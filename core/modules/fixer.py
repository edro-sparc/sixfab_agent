import os

if not os.path.exists("/opt/sixfab/.agent-fixes"):
    os.system("sudo touch /opt/sixfab/.agent-fixes")

fixes_list = open("/opt/sixfab/.agent-fixes").read().split(",")

def execute_fix(name, command):
    if name in fixes_list:
        return

    os.system(command)

    with open("/opt/sixfab/.agent-fixes", "a") as file:
        file.write(","+name)

# change old service file with new one
execute_fix("3004-service-file", 'echo -e "[Unit]\nDescription=Sixfab PMS Agent\nAfter=network.target network-online.target\nRequires=network-online.target\n\n[Service]\nExecStart=/usr/bin/python3 -u agent.py\nWorkingDirectory=/opt/sixfab/pms/agent\nStandardOutput=inherit\nStandardError=inherit\nRestart=always\nRestartSec=3\nUser=pi\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/pms_agent.service && sudo systemctl daemon-reload && sudo systemctl disable pms_agent & sudo systemctl enable pms_agent')
