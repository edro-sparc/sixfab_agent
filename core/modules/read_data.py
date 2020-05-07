import os
import re
import time
import logging

from subprocess import check_output
from pms_api import SixfabPMS

from .recovery import try_until_get

def read_data(api, **kwargs):

    api.softPowerOff()
    api.softReboot()
    api.sendSystemTemp()

    def fan_health():
        response = try_until_get(api, "getFanHealth")
        responses = {0: None, 1: True, 2: False}

        return responses[response]

    def working_mode():
        response = try_until_get(api, "getWorkingMode")
        responses = {
            0: "n/a",
            1: "Charging",
            2: "Fully Charged - Adapter Powered",
            3: "Battery Powered",
        }

        return responses[response]

    def watchdog_signal():
        response = try_until_get(api, "askWatchdogAlarm")
        responses = {0: None, 1: True, 2: False}

        return responses[response]

    def firmware_version():
        get_from_hat = try_until_get(api, "getFirmwareVer")

        if isinstance(get_from_hat, str):
            return re.search("v([0-9]*.[0-9]*.[0-9]*)", get_from_hat)[1]
        elif isinstance(get_from_hat, bytearray) or isinstance(get_from_hat, bytes):
            return get_from_hat.decode().replace("v", "")
        else:
            return '0.0.0'

    def get_api_version():
        api_version_file_path = "/opt/sixfab/pms/api/setup.py"

        if not os.path.exists(api_version_file_path):
            return "0.0.0"

        file_content = check_output(["sudo", "cat", api_version_file_path]).decode()

        for line in file_content.split("\n"):
            if "version" in line:
                return (
                        line.split("=")[1]
                        .replace(",", "")
                        .replace("'", "")
                    )

        return '0.0.0'

    return {
        "timestamp": time.time(),
        "charge_status": try_until_get(api, "getBatteryLevel"),
        "battery_healt": try_until_get(api, "getBatteryHealth"),
        "fanspeed": try_until_get(api, "getFanSpeed"),
        "fan_health": fan_health(),
        "working_status": working_mode(),
        "watchdog_signal": watchdog_signal(),
        "stats": {
            "input": {
                "temperature": try_until_get(api, "getInputTemp"),
                "voltage": try_until_get(api, "getInputVoltage"),
                "current": try_until_get(api, "getInputCurrent"),
                "power": try_until_get(api, "getInputPower"),
            },
            "system": {
                "temperature": try_until_get(api, "getSystemTemp"),
                "voltage": try_until_get(api, "getSystemVoltage"),
                "current": try_until_get(api, "getSystemCurrent"),
                "power": try_until_get(api, "getSystemPower"),
            },
            "battery": {
                "temperature": try_until_get(api, "getBatteryTemp"),
                "voltage": try_until_get(api, "getBatteryVoltage"),
                "current": try_until_get(api, "getBatteryCurrent"),
                "power": try_until_get(api, "getBatteryPower"),
            },
        },
        "versions": {
            "firmware": firmware_version(),
            "agent": kwargs.get("agent_version", "0.0.0"),
            "api": get_api_version()
        }
    }
