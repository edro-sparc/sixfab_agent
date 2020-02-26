import json
from threading import Thread

import paho.mqtt.client as mqtt
from pms_api import SixfabPMS

from .modules import *

MQTT_HOST = "power.sixfab.com"
MQTT_PORT = 1883

COMMANDS = {"healthcheck": health_check, "configurations": set_configurations}


class Agent(object):
    def __init__(
        self,
        token: str,
        interval: int = 10,
        lwt: bool = True,
        enable_feeder: bool = True,
    ):
        client = mqtt.Client()
        self.client = client
        self.token = token
        self.interval = interval
        self.PMSAPI = SixfabPMS()

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

    def loop(self):
        listener = Thread(target=self.client.loop_forever)
        feeder = Thread(target=self.feeder)

        listener.start()
        feeder.start()

    def feeder(self):
        import time
        import random

        while True:
            try:
                self.client.publish(
                    "/device/{token}/feed".format(token=self.token),
                    json.dumps(read_data(self.PMSAPI)),
                )
                time.sleep(self.interval)
            except:
                time.sleep(1)

    def __on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())
        command = message.get("command", None)
        commandID = message.get("commandID", None)
        command_data = message.get("data", {})

        if COMMANDS[command]:
            response = json.dumps(
                {
                    "command": command,
                    "commandID": commandID,
                    "response": COMMANDS[command](self.PMSAPI, command_data),
                }
            )

            client.publish(
                "/device/{userdata}/hive".format(userdata=userdata), response
            )

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
