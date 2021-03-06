import os
import time
import json
import logging
import logging.handlers
import subprocess
import paho.mqtt.client as mqtt

from uuid import uuid4
from typing import List
from threading import Thread, Lock

from .modules import *
from .modules.set_configurations import update_timezone
from .modules.proxy import run_signal
from .modules import cloud_api

from .helpers.configs import config_object_to_string
from .helpers import network
from .helpers.logger import initialize_logger

MQTT_HOST = "power.sixfab.com"
MQTT_PORT = 1883

logger = initialize_logger()

class Agent(object):
    def __init__(
        self, token: str, configs: dict, lwt: bool = True, enable_feeder: bool = True,
    ):
        client = mqtt.Client(protocol=mqtt.MQTTv31,
                             client_id=f"device/{uuid4().hex}")
        self.client = client
        self.token = token
        self.configs = configs
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

        client.on_connect = self.__on_connect
        client.on_message = self.__on_message
        client.on_disconnect = self.__on_disconnect
        client.on_log = self.__on_log

    def loop(self):
        ping_addr = "power.sixfab.com"
        ping_host = None

        Thread(target=self.routine_worker).start()
        Thread(target=self.feeder_worker).start()

        while True:
            if network.is_network_available(ping_host or ping_addr):

                if not ping_host:
                    ping_host = network.get_host_by_addr(ping_addr)

                if not self.is_connected:
                    logger.debug("[LOOP] Network online, starting mqtt agent")
                    self.client.connect(
                        self.configs["environments"].get("MQTT_HOST", MQTT_HOST),
                        MQTT_PORT,
                        keepalive=30
                    )
                    self.client.loop_start()
                    self.is_connected = True

                time.sleep(30)
            else:
                if ping_host:
                    ping_host = None
                    continue

                if self.is_connected:
                    logger.debug("[LOOP] Network ofline, blocking mqtt agent")
                    self.is_connected = False
                    self.client.loop_stop()
                    self.client.disconnect()

                time.sleep(10)

    def feeder_worker(self):
        """ Feeds cloud with sensor datas """
        while True:
            if not self.is_connected:
                time.sleep(1)
                continue

            try:
                logger.debug("[FEEDER] Starting, locking")
                with self.lock_thread:
                    self.client.publish(
                        "/device/{token}/feed".format(token=self.token),
                        json.dumps(
                            read_data(agent_version=self.configs["version"])
                        ),
                    )
                logger.debug("[FEEDER] Done, releasing setters")

                time.sleep(self.configs["feeder_interval"])
            except:
                time.sleep(1)

    def routine_worker(self):
        while True:
            with self.lock_thread:
                try:
                    run_signal("soft_shutdown")
                    run_signal("soft_reboot")
                    run_signal("system_temperature")
                except Exception as e:
                    logger.debug("[ROUTINE WORKER] Error occured, trying again in 15secs")
                else:
                    logger.debug("[ROUTINE WORKER] Metrics sent to hat")

            time.sleep(15)

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

    def _wait_ntp_and_update_rtc(self, timezone):
        while True:
            is_ntp_synchronized = subprocess.check_output(
                ["timedatectl"]).decode()
            is_ntp_synchronized = is_ntp_synchronized[is_ntp_synchronized.find(
                "synchronized: ")+14:]
            is_ntp_synchronized = is_ntp_synchronized[:is_ntp_synchronized.find(
                "\n")]

            if is_ntp_synchronized == 'yes':
                logger.debug("NTP synchronized, updating timezone")

                with self.lock_thread:
                    logger.debug("Setting RTC timezone to " + timezone)
                    update_timezone(timezone)

                return True
            logger.debug("Waiting for NTP synchronization")
            time.sleep(15)

    def _lock_feeder_for_firmware_update(self):
        with self.lock_thread:
            update_firmware(
                repository=self.configs["firmware_update_repository"],
                mqtt_client=self.client,
                token=self.token,
                experimental_enabled=self.configs["experimental_enabled"],
            )

            time.sleep(15)

    def __on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())
        command = message.get("command", None)
        command_id = message.get("id", None)
        command_data = message.get("data", {})

        if "connected" in message:
            logger.info(
                "[CONNECTION] status message recieved from broker")
            if not message["connected"]:
                logger.warning(
                    "[CONNECTION] looks like broker thinks we are disconnected, sending status message again")
                self.client.publish(
                    "/device/{}/status".format(self.token),
                    json.dumps({"connected": True}),
                    retain=True,
                )
                logger.info(
                    "[CONNECTION] status changed to true")

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
                        command_data, configs=self.configs
                    )

                    if is_configured:
                        response = json.dumps({
                            "id": command_id,
                            "command": "update_status_configurations",
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
                Thread(target=self._wait_ntp_and_update_rtc,
                       args=(command_data["timezone"],)).start()

        elif command == "rpc":
            response = cloud_api.handler(command_data)

            response = json.dumps({
                            "id": command_id,
                            "command": "rpc",
                            "response": {
                                "data": response
                            },
                        })

            self.client.publish(
                            "/device/{userdata}/hive".format(
                                userdata=userdata), response
                        )

        else:
            response = json.dumps(
                {
                    "id": command_id,
                    "command": command,
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
        print(string.replace(obj, "...censored_uuid..."))
