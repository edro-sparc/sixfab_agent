import paho.mqtt.client as mqtt
import json
from .modules import *

MQTT_HOST = "beta.sixfab.com"
MQTT_PORT = 1883

COMMANDS = {"healthcheck": health_check}


class Agent(object):
    def __init__(self, token: str, interval: int = 10, lwt: bool = True):
        client = mqtt.Client()
        self.client = client

        client.username_pw_set(token, token)
        client.user_data_set(token)

        if lwt:
           client.will_set("/device/{}/status".format(token), "offline", retain=True)
    
        client.connect(MQTT_HOST, MQTT_PORT, 50)
        client.on_connect = self.__on_connect
        client.on_message = self.__on_message
        client.on_disconnect = self.__on_disconnect
        client.on_log = self.__on_log

    def loop(self):
        self.client.loop_forever()

    def __on_message(self, client, userdata, msg):
        """
        Triggering on mqtt message
    
        Request Format:
            {
                "command": "",
                "commandID": "", !!! OPTIONAL
                "data": {}, !!! OPTIONAL
            }


        Response Format:
            {
                "command": "",
                "commandID": "", !!! OPTIONAL
                "response": {}, !!! OPTIONAL
            }
        """
        message = json.loads(msg.payload.decode())
        command = message.get("command", None)
        commandID = message.get("commandID", None)

        if COMMANDS[command]:
            response = json.dumps(
                {
                    "command": command,
                    "commandID": commandID,
                    "response": COMMANDS[command](),
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
            "online",
            retain=True,
        )

    def __on_disconnect(self, client, userdata, rc):
        print("Disconnected. Result Code: {rc}".format(rc=rc))

    def __on_log(self, mqttc, obj, level, string):
        print(string)
