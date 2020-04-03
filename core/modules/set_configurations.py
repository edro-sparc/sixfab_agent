from pms_api.definitions import Definition
from pms_api.event import Event

MAP_BOOL = {True: 1, False: 2}

MAP_ANIMATIONS = {"Disabled": 1, "Heartbeat": 2, "Temperature Map": 3}

MAP_COLORS = {
    "Green": 1,
    "Blue": 2,
    "Red": 3,
    "Yellow": 4,
    "Cyan": 5,
    "Magenta": 6,
    "White": 7,
}

MAP_SPEEDS = {"Slow": 1, "Normal": 2, "Fast": 3}

MAP_DAYS = {
    "mon": Definition.MONDAY,
    "tue": Definition.TUESDAY,
    "wed": Definition.WEDNESDAY,
    "thu": Definition.THURSDAY,
    "fri": Definition.FRIDAY,
    "sat": Definition.SATURDAY,
    "sun": Definition.SUNDAY,
}

MAP_ACTIONS = {
    "start": 1,
    "shutdown_hard": 2,
    "shutdown_soft": 3,
    "reboot_hard": 4,
    "reboot_soft": 5,
}

MAP_INTERVAL_TYPE = {"seconds": 1, "minutes": 2, "hours": 3}

import time


def get_until_done(function):
    while True:
        try:
            return function()
        except:
            pass
    time.sleep(0.5)


def try_until_done(function, *args):
    while True:
        try:
            resp = function(*args)
        except:
            resp = 0

        if resp == 1:
            return resp

        time.sleep(0.5)


def set_configurations(pms, data):
    try_until_done(pms.setWatchdogStatus, MAP_BOOL[data["watchdog_enabled"]])

    smart_cooling = data["smart_cooling"].split(",")
    smart_cooling = [int(value) for value in smart_cooling]
    try_until_done(pms.setFanAutomation, smart_cooling[0], smart_cooling[1])

    battery_percentage = data["battery_percentage"].split(",")
    battery_percentage = [int(value) for value in battery_percentage]
    try_until_done(pms.setSafeShutdownBatteryLevel, battery_percentage[0])
    try_until_done(pms.setBatteryMaxChargeLevel, battery_percentage[1])

    try_until_done(
        pms.setRgbAnimation,
        MAP_ANIMATIONS[data["led_animation"]],
        MAP_COLORS[data.get("led_color", "Red")],
        MAP_SPEEDS[data.get("led_speed", "Normal")],
    )

    # set scheduled events
    for ignored_field in data["ignored_fields"]:  # clear ignored events
        for event in data["scheduled"]:
            if f"event_{event['_id']}" == ignored_field:
                data["scheduled"].remove(event)

    cloud_event_ids = [event["_id"] for event in data["scheduled"]]
    local_event_ids = get_until_done(pms.getScheduledEventIds)

    s = set(cloud_event_ids)
    ids_to_delete = [x for x in local_event_ids if x not in s]

    s = set(local_event_ids)
    ids_to_add = [x for x in cloud_event_ids if x not in s]

    for _id in ids_to_delete:
        try_until_done(pms.removeScheduledEvent, _id)

    for _id in ids_to_add:
        if f"event_{_id}" in data["ignored_fields"]:
            continue

        for _event in data["scheduled"]:
            if _event["_id"] == _id:
                event = _event
                break

        event_to_save = Event()

        if event["event_type"] == "time":
            epoch_time = event["time"].split(":")
            epoch_time = int(epoch_time[0]) * 60 * 60 + int(epoch_time[1]) * 60

            days = 0
            if event["time_frequency"] == "daily":
                days = Definition.EVERYDAY
            else:
                for day in event["days"].split(","):
                    days = days | MAP_DAYS[day]

            event_to_save.id = _id
            event_to_save.schedule_type = Definition.EVENT_TIME
            event_to_save.repeat = (
                Definition.EVENT_ONE_SHOT
                if event["time_frequency"] == "once"
                else Definition.EVENT_REPEATED
            )
            event_to_save.time_interval = epoch_time
            event_to_save.day = days
            event_to_save.action = MAP_ACTIONS[event["action"]]

            try_until_done(pms.createScheduledEventWithEvent, event_to_save)

        elif event["event_type"] == "interval":
            event_to_save.id = _id
            event_to_save.schedule_type = Definition.EVENT_INTERVAL
            event_to_save.time_interval = event["interval_value"]
            event_to_save.interval_type = MAP_INTERVAL_TYPE[event["interval_frequency"]]
            event_to_save.action = MAP_ACTIONS[event["action"]]
            event_to_save.repeat = (
                Definition.EVENT_ONE_SHOT
                if event["interval_type"] == "once"
                else Definition.EVENT_REPEATED
            )

            try_until_done(pms.createScheduledEventWithEvent, event_to_save)

    return True
