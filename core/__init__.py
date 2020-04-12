import time
import json
import logging
from threading import Thread

import paho.mqtt.client as mqtt
from pms_api import SixfabPMS

from .modules import *
from .modules.set_configurations import update_timezone

MQTT_HOST = "power.sixfab.com"
MQTT_PORT = 1883

COMMANDS = {"healthcheck": health_check, "configurations": set_configurations}


class Agent(object):
    def __init__(
        self,
        token: str,
        configs: dict,
        lwt: bool = True,
        enable_feeder: bool = True,
    ):
        client = mqtt.Client()
        self.client = client
        self.token = token
        self.configs = configs
        self.PMSAPI = SixfabPMS()

        self.lock_feeder = False
        self.feeder_working = False

        client.username_pw_set(token, token)
        client.user_data_set(token)

        if lwt:
            client.will_set(
                "/device/{}/status".format(token),
                json.dumps({"connected": False}),
                retain=True
            )

        client.connect(MQTT_HOST, MQTT_PORT, 50)
        client.on_connect = self.__on_connect
        client.on_message = self.__on_message
        client.on_disconnect = self.__on_disconnect
        client.on_log = self.__on_log

    def reinit_api(self):
        self.PMSAPI = SixfabPMS()

    def loop(self):
        listener = Thread(target=self.client.loop_forever)
        feeder = Thread(target=self.feeder)

        listener.start()
        feeder.start()

    def feeder(self):

        while True:
            if self.lock_feeder:
                time.sleep(.5)
                continue

            try:
                self.feeder_working = True
                logging.debug("[FEEDER] Starting, locking setters")
                self.client.publish(
                    "/device/{token}/feed".format(token=self.token),
                    json.dumps(read_data(self.PMSAPI, agent_version=self.configs["version"])),
                )
                logging.debug("[FEEDER] Done, releasing setters")
                self.feeder_working = False
                time.sleep(self.configs["feeder_interval"])
            except:
                time.sleep(1)

    def _lock_feeder_for_firmware_update(self):
        self.lock_feeder = not self.lock_feeder

        update_firmware(
            api=self.PMSAPI,
            repository= self.configs["firmware_update_repository"],
            mqtt_client=self.client,
            lock_feeder=self.lock_feeder,
            token=self.token
        )

        self.lock_feeder = False
        

    def __on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())
        command = message.get("command", None)
        commandID = message.get("commandID", None)
        command_data = message.get("data", {})

        if COMMANDS.get(command, False):
            while self.feeder_working:
                    time.sleep(.3)
            
            executed_command_output = COMMANDS[command](self.PMSAPI, command_data)

            response = json.dumps(
                {
                    "command": command,
                    "commandID": commandID,
                    "response": executed_command_output,
                }
            )

            self.client.publish(
                "/device/{userdata}/hive".format(userdata=userdata), response
            )

            return

        if command.startswith('update_'):
            update_type = command.split("_")[1]

            if update_type == "firmware":
                firmware_update_thread = Thread(target=self._lock_feeder_for_firmware_update)
                firmware_update_thread.start()
                return

            elif update_type == "agent":
                agent_update_thread = Thread(target=update_agent, kwargs=dict(
                    mqtt_client = self.client,
                    token = self.token
                ))
                agent_update_thread.start()
                return

            elif update_type == "rtc":

                def update_timezone_thread():
                    while self.feeder_working:
                        time.sleep(.3)

                    time.sleep(1)

                    self.lock_feeder = True
                    logging.debug("Setting RTC time to "+command_data["timezone"])
                    update_timezone(self.PMSAPI, command_data["timezone"])
                    self.lock_feeder = False

                Thread(target=update_timezone_thread).start()

        else:
            response = json.dumps(
                {
                    "command": command,
                    "commandID": commandID,
                    "response": "Invalid command",
                }
            )
            client.publish(
                "/device/{userdata}/hive".format(userdata=userdata), response
            )

    def __on_connect(self, client, userdata, flags, rc):
        print("Connected to the server")
        self.client.subscribe("/device/{userdata}/directives".format(userdata=userdata))
        self.client.publish(
            "/device/{userdata}/status".format(userdata=userdata),
            json.dumps({"connected": True}),
            retain=True,
        )

    def __on_disconnect(self, client, userdata, rc):
        print("Disconnected. Result Code: {rc}".format(rc=rc))

    def __on_log(self, mqttc, obj, level, string):
        print(string)
