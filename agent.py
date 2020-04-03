from core import Agent
from configparser import ConfigParser

__version__ = "0.1.0"

if __name__ == "__main__":
    configs = ConfigParser()
    configs.read("/opt/sixfab/.env")
    configs = configs["pms"]
 
    agent = Agent(
        configs["TOKEN"],
        version=__version__,
        interval=int(configs["INTERVAL"]),
    )
    agent.loop()
