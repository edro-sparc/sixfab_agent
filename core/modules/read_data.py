def read_data(api):
    return {
        "charge_status": api.getBatteryLevel(),
        "battery_health": api.getBatteryHealt(),
        "fanspeed": api.getFanSpeed(),
        "stats":{
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
            }
        }
    }