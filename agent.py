import os
import logging

from core import Agent
from core.modules import fixer
from configparser import ConfigParser

__version__ = "0.1.8"


# is_debugger_true = os.getenv('ENABLE_PMS_AGENT_DEBUG')
# is_debugger_true = True if is_debugger_true == "True" else False
is_debugger_true = True # debug is always enabled for now.

logging.basicConfig(level=logging.DEBUG if is_debugger_true else logging.CRITICAL)
environments_object = ConfigParser()
environments_object.read("/opt/sixfab/.env")
pms_environments = environments_object["pms"]

configs = {
    "version": __version__,
    "feeder_interval": int(pms_environments.get("INTERVAL", 10)),
    "experimental_enabled": True if pms_environments.get("EXPERIMENTAL", False) == "True" else False,
    "environments": pms_environments,
    "environments_object": environments_object,
    "firmware_update_repository": "https://git.sixfab.com/sixfab-power/firmwares.git"
}

if __name__ == "__main__":
 
    agent = Agent(
        pms_environments["TOKEN"],
        configs=configs
    )
    agent.loop()
