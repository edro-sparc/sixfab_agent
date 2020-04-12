import logging
import time
import re

from pms_api import SixfabPMS
from pms_api.exceptions import CRCCheckFailed

def try_until_get(api, function):
    while True:
        try:
            resp = getattr(api, function)()
        except CRCCheckFailed:
            logging.error("\033[33m[{}] \033[0m crc check failed, reinitializing api".format(function))
            del api
            api = SixfabPMS()
        except TypeError:
            logging.error("\033[33m[{}] \033[0m TypeError raised, clearing pipe".format(function))
            api.clearPipe()
        except Exception as e:
            logging.error("\033[33m[{}] \033[0m unknown exception raised".format(function))
        else:
            logging.debug("\033[94m[{}] \033[0m done".format(function))
            return resp
            
        logging.error("[{}] trying again".format(function))
        time.sleep(0.5)

def read_data(api, **kwargs):

    # TODO api.softPowerOff()
    # TODO api.softReboot()

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
            "agent": kwargs.get("agent_version", "0.0.0")
        }
    }
