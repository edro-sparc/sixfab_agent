














import os
from subprocess import check_output

if not os.path.exists("/opt/sixfab/.agent-fixes"):
    os.system("sudo touch /opt/sixfab/.agent-fixes")

fixes_list = check_output(["sudo", "cat", "/opt/sixfab/.agent-fixes"]).decode().split("\n")

def execute_fix(name, command):
    if name in fixes_list:
        return

    os.system(command)
    os.system("echo {} | sudo tee -a /opt/sixfab/.agent-fixes".format(name))

# change old service file with new one
execute_fix("3004-service-file", r'printf "[Unit]\nDescription=Sixfab PMS Agent\nAfter=network.target network-online.target\nRequires=network-online.target\n\n[Service]\nExecStart=/usr/bin/python3 -u agent.py\nWorkingDirectory=/opt/sixfab/pms/agent\nStandardOutput=inherit\nStandardError=inherit\nRestart=always\nRestartSec=3\nUser=pi\n\n[Install]\nWantedBy=multi-user.target" | sudo tee /etc/systemd/system/pms_agent.service && sudo systemctl daemon-reload && sudo systemctl disable pms_agent && sudo systemctl enable pms_agent && sudo systemctl restart pms_agent')