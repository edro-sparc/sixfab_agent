from core import Agent
from configparser import ConfigParser

__version__ = "0.1.1"

environments = ConfigParser()
environments.read("/opt/sixfab/.env")
environments = environments["pms"]

configs = {
    "version": __version__,
    "feeder_interval": int(environments.get("INTERVAL", 10)),
    "firmware_update_repository": "https://git.ray.kim/sixfab-power/temp-fota-repo.git",
}

if __name__ == "__main__":
 
    agent = Agent(
        environments["TOKEN"],
        configs=configs
    )
    agent.loop()
