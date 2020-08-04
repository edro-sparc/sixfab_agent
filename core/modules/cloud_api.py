from .proxy import get_metric_by_sensor, get_metric

def handler(command):
    if command.startswith("get_"):
        command = command.split("_")[1:]

        if len(command) == 1:
            return get_metric(command[0])
        elif len(command) == 2 and command == ["working", "mode"]:
            return get_metric("working_mode")
        elif len(command) == 2:
            return get_metric_by_sensor(command[0], command[1])