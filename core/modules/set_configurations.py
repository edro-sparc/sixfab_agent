MAP_BOOL = {
    True: 1,
    False: 2
}

MAP_ANIMATIONS = {
    "Disabled": 1,
    "Heartbeat": 2,
    "Temperature Map": 3
}

MAP_COLORS = {
        "Red": 1,
        "Green": 2,
        "Blue": 3,
        "Yellow": 4,
        "Cyan": 5,
        "Magenta": 6,
        "White": 7
}

MAP_SPEEDS = {
    "Slow": 1,
    "Normal": 2,
    "Fast": 3
}

import time

def try_until_done(function, *args):
    resp = function(*args)
    while resp != 1:
        if resp == 1:
            break
        else:
            time.sleep(.5)
            resp = function(*args)

def set_configurations(pms, data):
    try_until_done(pms.setWatchdogStatus, MAP_BOOL[data["watchdog_enabled"]])

    smart_cooling = data["smart_cooling"].split(",")
    smart_cooling = [int(value) for value in smart_cooling]
    try_until_done(pms.setFanAutomation, smart_cooling[0], smart_cooling[1])

    battery_percentage = data["battery_percentage"].split(",")
    battery_percentage = [int(value) for value in battery_percentage]
    try_until_done(pms.setSafeShutdownBatteryLevel, battery_percentage[0])
    try_until_done(pms.setBatteryMaxChargeLevel, battery_percentage[1])

    try_until_done(pms.setRgbAnimation,
            MAP_ANIMATIONS[data["led_animation"]],
            MAP_COLORS[data.get("led_color", "Red")],
            MAP_SPEEDS[data.get("led_speed", "Normal")]
        )

    return True


