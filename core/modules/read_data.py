import time

def read_data(api):
    def fan_health():
        response = api.getFanHealth()
        responses = {0: None, 1: True, 2: False}

        return responses[response]

    def working_mode():
        response = api.getWorkingMode()
        responses = {
            0: "n/a",
            1: "Charging",
            2: "Fully Charged - Adapter Powered",
            3: "Battery Powered",
        }

        return responses[response]

    def watchdog_signal():
        response = api.askWatchdogAlarm()
        responses = {0: None, 1: True, 2: False}

        return responses[response]

    return {
        "timestamp": time.time(),
        "charge_status": api.getBatteryLevel(),
        "battery_health": api.getBatteryHealth(),
        "fanspeed": api.getFanSpeed(),
        "fan_health": fan_health(),
        "working_status": working_mode(),
        "watchdog_signal": watchdog_signal(),
        "stats": {
            "input": {
                "temperature": api.getInputTemp(),
                "voltage": api.getInputVoltage(),
                "current": api.getInputCurrent(),
                "power": api.getInputPower(),
            },
            "system": {
                "temperature": api.getSystemTemp(),
                "voltage": api.getSystemVoltage(),
                "current": api.getSystemCurrent(),
                "power": api.getSystemPower(),
            },
            "battery": {
                "temperature": api.getBatteryTemp(),
                "voltage": api.getBatteryVoltage(),
                "current": api.getBatteryCurrent(),
                "power": api.getBatteryPower(),
            },
        },
    }
