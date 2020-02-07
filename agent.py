from core import Agent
from configparser import ConfigParser

if __name__ == "__main__":
    configs = ConfigParser()
    configs.read("/opt/sixfab/.env")
    configs = configs["pms"]
 
    agent = Agent(
        configs["TOKEN"],
        interval=configs["INTERVAL"],
    )
    agent.loop()
