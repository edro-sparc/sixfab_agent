import os
import time
import logging
from subprocess import Popen
from .proxy import update_configurations, get_scheduled_event_ids, delete_scheduled_events, create_scheduled_event


def update_experimental_status(**kwargs):
    ENVIRONMENT_FILE = "/opt/sixfab/.env"
    REPOSITORIES = ("/opt/sixfab/pms/api",
                    "/opt/sixfab/pms/agent", "/opt/sixfab/pms/firmwares")

    if kwargs["current_status"] == kwargs["to_set"]:
        return

    if kwargs["to_set"] == True:  # enable experimental version using
        os.system(
            """
            if grep -q "EXPERIMENTAL" {ENVIRONMENT_FILE};
            then
                sudo sed -i 's/EXPERIMENTAL=False/EXPERIMENTAL=True/' {ENVIRONMENT_FILE}
            else
                echo 'EXPERIMENTAL=True' | sudo tee -a {ENVIRONMENT_FILE}
            fi
            """.format(ENVIRONMENT_FILE=ENVIRONMENT_FILE))

        for repo in REPOSITORIES:
            os.system(
                """
                cd {repo} &&
                sudo git reset --hard &&
                sudo git fetch &&
                sudo git checkout dev &&
                sudo git pull
                """.format(repo=repo)
            )
    else:
        os.system(
            "sudo sed -i 's/EXPERIMENTAL=True/EXPERIMENTAL=False/' /opt/sixfab/.env")
        os.system(
            """
            if grep -q "EXPERIMENTAL" {ENVIRONMENT_FILE};
            then
                sudo sed -i 's/EXPERIMENTAL=True/EXPERIMENTAL=False/' {ENVIRONMENT_FILE}
            else
                echo 'EXPERIMENTAL=True' | sudo tee -a {ENVIRONMENT_FILE}
            fi
            """.format(ENVIRONMENT_FILE=ENVIRONMENT_FILE))

        for repo in REPOSITORIES:
            os.system(
                """
                cd {repo} &&
                sudo git reset --hard &&
                sudo git checkout master &&
                sudo git pull
                """.format(repo=repo)
            )

    Popen("sleep 2 && sudo systemctl restart power_agent", shell=True)


def update_timezone(timezone):
    """
        timezone format: UTC[operator][offset]
        example: UTC+9, UTC-3, UTC+6:45
    """
    operator, offset = timezone[3:4], timezone[4:]

    if timezone == "default":
        update_configurations({
            "rtc": {
                "timestamp": int(time.time() - time.timezone)
            }
        })
        return

    if ":" not in offset and offset == "0":
        update_configurations({
            "rtc": {
                "timestamp": int(time.time())
            }
        })
        return

    offset_to_calculate = 0

    if ":" in offset:
        hours, minutes = offset.split(":")

        offset_to_calculate += int(hours) * 60 * 60
        offset_to_calculate += int(minutes) * 60

    else:
        offset_to_calculate += int(offset) * 60 * 60

    if operator == "+":
        epoch_to_set = int(time.time()) + offset_to_calculate
    else:
        epoch_to_set = int(time.time()) - offset_to_calculate

    update_configurations({
        "rtc": {
            "timestamp": int(epoch_to_set)
        }
    })


def set_configurations(data, **kwargs):
    configurations = {}

    update_timezone(data["timezone"])

    battery_percentage = data["battery_percentage"].split(",")
    battery_percentage = [int(value) for value in battery_percentage]
    configurations["battery"] = {
        "design_capacity": data["battery_capacity"],
        "safe_shutdown_level": battery_percentage[0],
        "max_charge_level": battery_percentage[1]
    }

    configurations["watchdog"] = {
        "is_enabled": data["watchdog_enabled"]
    }

    smart_cooling = data["smart_cooling"].split(",")
    smart_cooling = [int(value) for value in smart_cooling]

    configurations["fan"] = {
        "slow_threshold": smart_cooling[0],
        "fast_threshold": smart_cooling[1]
    }

    configurations["rgb"] = {
        "type": "temperature_map" if data["led_animation"] == "Temperature Map" else data["led_animation"].lower(),
        "color": data.get("led_color", "Green").lower(),
        "speed": data.get("led_speed", "Normal").lower()
    }

    update_configurations(configurations)

    # set scheduled events
    for ignored_field in data["ignored_fields"]:  # clear ignored events
        for event in data["scheduled"]:
            if f"event_{event['_id']}" == ignored_field:
                data["scheduled"].remove(event)

    cloud_event_ids = [event["_id"] for event in data["scheduled"]]
    local_event_ids = get_scheduled_event_ids()

    s = set(cloud_event_ids)
    ids_to_delete = [x for x in local_event_ids if x not in s]

    s = set(local_event_ids)
    ids_to_add = [x for x in cloud_event_ids if x not in s]

    delete_scheduled_events(ids_to_delete)

    events_to_create = []

    for _id in ids_to_add:
        if f"event_{_id}" in data["ignored_fields"]:
            continue

        for _event in data["scheduled"]:
            if _event["_id"] == _id:
                event = _event
                break

        if event["event_type"] == "time":
            events_to_create.append({
                "id": _id,
                "type": "time",
                "time": event["time"],
                "frequency": event["time_frequency"],
                "days": event["days"],
                "action": event["action"]
            })

        elif event["event_type"] == "interval":

            events_to_create.append({
                "id": _id,
                "type": "interval",
                "value": event["interval_value"],
                "frequency": event["interval_frequency"],
                "is_one_shot": event["interval_type"] == "once",
                "action": event["action"]
            })

    create_scheduled_event(events_to_create)

    if "experimental" in data:
        update_experimental_status(
            to_set=data.get("experimental"),
            current_status=kwargs["configs"].get("experimental_enabled")
        )

    return True
