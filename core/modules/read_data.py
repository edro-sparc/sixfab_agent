import os
import re
import time
import logging

from subprocess import check_output
from pms_api import SixfabPMS

from .recovery import try_until_get

def read_data(api, **kwargs):
    def fan_health():
        response = try_until_get(api, "getFanHealth")
        responses = {0: None, 1: True, 2: False}

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
<<<<<<< Updated upstream
=======
                        .replace("\"", "")
                        .replace(")", "")
>>>>>>> Stashed changes
                    )

        return '0.0.0'

    return {
    "ts": time.time(),
    "data": "{firmware_version},{agent_version},{api_version}|{fan_health},{watchdog}|{working_status},{charge_status},{battery_health},{fanspeed},{input_temperature},{input_voltage},{input_current},{input_power},{system_temperature},{system_voltage},{system_current},{system_power},{battery_temperature},{battery_voltage},{battery_current},{battery_power}".format(
        firmware_version=firmware_version(),
        agent_version=kwargs.get("agent_version", "0.0.0"),
        api_version=get_api_version(),

        fan_health="T" if fan_health() else "F",
        watchdog="T" if watchdog_signal() else "F",

        working_status=try_until_get(api, "getWorkingMode"),
        charge_status=try_until_get(api, "getBatteryLevel"),
        battery_health=try_until_get(api, "getBatteryHealth"),
        fanspeed=try_until_get(api, "getFanSpeed"),

        input_temperature=try_until_get(api, "getInputTemp"),
        input_voltage=try_until_get(api, "getInputVoltage"),
        input_current=try_until_get(api, "getInputCurrent"),
        input_power=try_until_get(api, "getInputPower"),

        system_temperature=try_until_get(api, "getSystemTemp"),
        system_voltage=try_until_get(api, "getSystemVoltage"),
        system_current=try_until_get(api, "getSystemCurrent"),
        system_power=try_until_get(api, "getSystemPower"),

        battery_temperature=try_until_get(api, "getBatteryTemp"),
        battery_voltage=try_until_get(api, "getBatteryVoltage"),
        battery_current=try_until_get(api, "getBatteryCurrent"),
        battery_power=try_until_get(api, "getBatteryPower"),
        )
    }