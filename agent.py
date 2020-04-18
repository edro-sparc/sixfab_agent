import os
import logging

from core import Agent
from configparser import ConfigParser

__version__ = "0.1.1"


# is_debugger_true = os.getenv('ENABLE_PMS_AGENT_DEBUG')
# is_debugger_true = True if is_debugger_true == "True" else False
is_debugger_true = True # debug is always enabled for now.

logging.basicConfig(level=logging.DEBUG if is_debugger_true else logging.CRITICAL)

environments = ConfigParser()
environments.read("/opt/sixfab/.env")
environments = environments["pms"]

configs = {
    "version": __version__,
    "feeder_interval": int(environments.get("INTERVAL", 10)),
    "firmware_update_repository": "https://git.sixfab.com/sixfab-power/firmwares.git",
}

if __name__ == "__main__":
 
    agent = Agent(
        environments["TOKEN"],
        configs=configs
    )
    agent.loop()
