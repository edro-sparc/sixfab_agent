import time
import json
import logging
import subprocess
import paho.mqtt.client as mqtt

from uuid import uuid4
from pms_api import SixfabPMS
from typing import List
from threading import Thread, Lock

from .modules import *
from .modules.set_configurations import update_timezone

from .helpers.configs import config_object_to_string
from .helpers import ntp

MQTT_HOST = "power.sixfab.com"
MQTT_PORT = 1883


class Agent(object):
    def __init__(
        self, token: str, configs: dict, lwt: bool = True, enable_feeder: bool = True,
    ):
        client = mqtt.Client(protocol=mqtt.MQTTv31,
                             client_id=f"device/{uuid4().hex}")
        self.client = client
        self.token = token
        self.configs = configs
        self.PMSAPI = SixfabPMS()
        self.is_connected = False

        self.lock_thread = Lock()

        client.username_pw_set(token, token)
        client.user_data_set(token)

        if lwt:
            client.will_set(
                "/device/{}/status".format(token),
                json.dumps({"connected": False}),
                retain=True,
            )

        client.connect(
            configs["environments"].get("MQTT_HOST", MQTT_HOST),
            MQTT_PORT,
            keepalive=120
        )
        client.on_connect = self.__on_connect
        client.on_message = self.__on_message
        client.on_disconnect = self.__on_disconnect
        client.on_log = self.__on_log

    def reinit_api(self):
        self.PMSAPI = SixfabPMS()

    def loop(self):
        self.client.loop_start()

        while True:
            if not self.is_connected:
                time.sleep(1)
                continue

            try:
                logging.debug("[FEEDER] Starting, locking")
                with self.lock_thread:
                    self.client.publish(
                        "/device/{token}/feed".format(token=self.token),
                        json.dumps(
                            read_data(
                                self.PMSAPI, agent_version=self.configs["version"]
                            )
                        ),
                    )
                logging.debug("[FEEDER] Done, releasing setters")

                time.sleep(self.configs["feeder_interval"])
                print(self.configs["feeder_interval"])
            except:
                time.sleep(1)

    def _upsert_environments(self, items: List[tuple]):
        """
            Update environments for Power Management System
            Params:
                items: list, contains (key, value) pairs for every configurations to upsert 
        """
        environments = self.configs["environments_object"]

        for key, value in items:
            environments.set("pms", str(key), str(value))

        subprocess.call(f"echo \"{config_object_to_string(environments)}\" | sudo tee /opt/sixfab/.env",
                        shell=True, stdout=subprocess.DEVNULL)
        return True

    def _lock_feeder_for_firmware_update(self):
        with self.lock_thread:
            update_firmware(
                api=self.PMSAPI,
                repository=self.configs["firmware_update_repository"],
                mqtt_client=self.client,
                token=self.token,
                experimental_enabled=self.configs["experimental_enabled"],
            )

            time.sleep(15)

    def __on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())
        command = message.get("command", None)
        commandID = message.get("commandID", None)
        command_data = message.get("data", {})

        if "connected" in message:
            logging.error(
                "\033[33m[CONNECTION] \033[0m status message recieved from broker")
            if not message["connected"]:
                logging.error(
                    "\033[33m[CONNECTION] \033[0m looks like broker thinks we are disconnected, sending status message again")
                self.client.publish(
                    "/device/{}/status".format(self.token),
                    json.dumps({"connected": True}),
                    retain=True,
                )
                logging.error(
                    "\033[33m[CONNECTION] \033[0m status changed to true")

            return

        if command == "configurations":
            def _lock_and_execute_command():
                if "interval" in command_data:
                    new_feeder_interval = command_data["interval"]
                    self.configs["feeder_interval"] = new_feeder_interval
                    self._upsert_environments(
                        [('interval', new_feeder_interval)])

                with self.lock_thread:
                    is_configured = set_configurations(
                        self.PMSAPI, command_data, configs=self.configs
                    )

                    if is_configured:
                        response = json.dumps({
                            "command": "update_status_configurations",
                            "commandID": commandID,
                            "response": {"updated": True},
                        })

                        self.client.publish(
                            "/device/{userdata}/hive".format(
                                userdata=userdata), response
                        )

            Thread(target=_lock_and_execute_command).start()
            return

        elif command and command.startswith("update_"):
            update_type = command.split("_")[1]

            if update_type == "firmware":
                firmware_update_thread = Thread(
                    target=self._lock_feeder_for_firmware_update
                )
                firmware_update_thread.start()
                return

            elif update_type == "agent":

                def _lock_and_update_agent(**kwargs):
                    with self.lock_thread:
                        update_agent(
                            mqtt_client=self.client,
                            token=self.token,
                            experimental_enabled=self.configs["experimental_enabled"]
                        )

                agent_update_thread = Thread(target=_lock_and_update_agent,)
                agent_update_thread.start()
                return

            elif update_type == "rtc":
                
                while True:
                    try:
                        ntp_utc0 = ntp.get_utc0()
                        if ntp_utc0:
                            break
                    except:
                        pass
                
                subprocess.call(f"sudo date -s '{time.ctime(ntp_utc0)}'", shell=True, stdout=subprocess.DEVNULL)

                def update_timezone_thread():
                    with self.lock_thread:
                        logging.debug("Setting RTC time to " +
                                      command_data["timezone"])
                        update_timezone(self.PMSAPI, command_data["timezone"], unix_time=ntp_utc0)

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
        self.is_connected = True

        self.client.subscribe(f"/device/{self.token}/directives")
        self.client.subscribe(f"/device/{self.token}/status")
        self.client.publish(
            f"/device/{self.token}/status",
            json.dumps({"connected": True}),
            retain=True,
        )

    def __on_disconnect(self, client, userdata, rc):
        print("Disconnected. Result Code: {rc}".format(rc=rc))
        self.is_connected = False

    def __on_log(self, mqttc, obj, level, string):
        print(string)
