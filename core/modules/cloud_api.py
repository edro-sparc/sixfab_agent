from .proxy import get_metric_by_sensor, get_metric

def handler(command):
    print(command)
    if command.startswith("get_"):
        command = command.split("_")[1:]

        if len(command) == 1:
            return get_metric(command[0])
            
        return get_metric_by_sensor(command[0], command[1])