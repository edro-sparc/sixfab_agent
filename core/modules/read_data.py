import os
import re
import time
import logging

from subprocess import check_output
from requests import get
from .consts import DISTRIBUTION_SERVICE
from .proxy import get_metric_by_sensor, run_signal, get_metric

def read_data(**kwargs):
    def fan_health():
        response = get_metric_by_sensor("fan", "health", default=0)

        return {0: None, 1: True, 2: False}[response]

    def watchdog_signal():
        response = run_signal("watchdog_alarm", default=None)
        return response

    def firmware_version():
        return get_metric("version", "0.0.0")

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
                        .replace("\"", "")
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

        working_status={
            "charging": 1,
            "fully_charged": 2,
            "battery_powered": 3 
        }[get_metric("working_mode")],
        charge_status=get_metric_by_sensor("battery", "level"),
        battery_health=get_metric_by_sensor("battery", "health"),
        fanspeed=get_metric_by_sensor("fan", "speed"),

        input_temperature=get_metric_by_sensor("input", "temperature"),
        input_voltage=get_metric_by_sensor("input", "voltage"),
        input_current=get_metric_by_sensor("input", "current"),
        input_power=get_metric_by_sensor("input", "power"),

        system_temperature=get_metric_by_sensor("system", "temperature"),
        system_voltage=get_metric_by_sensor("system", "voltage"),
        system_current=get_metric_by_sensor("system", "current"),
        system_power=get_metric_by_sensor("system", "power"),

        battery_temperature=get_metric_by_sensor("battery", "temperature"),
        battery_voltage=get_metric_by_sensor("battery", "voltage"),
        battery_current=get_metric_by_sensor("battery", "current"),
        battery_power=get_metric_by_sensor("battery", "power"),
        )
    }