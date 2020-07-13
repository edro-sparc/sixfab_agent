import os
from subprocess import check_output, call

if not os.path.exists("/opt/sixfab/.agent-fixes"):
    os.system("sudo touch /opt/sixfab/.agent-fixes")

fixes_list = check_output(["sudo", "cat", "/opt/sixfab/.agent-fixes"]).decode().split("\n")

def execute_fix(name, command):
    if name in fixes_list:
        return
        
    os.system("echo {} | sudo tee -a /opt/sixfab/.agent-fixes".format(name))
    call(command, shell=True, executable='/bin/bash')

# change old service file with new one
execute_fix("3004-service-file", r'printf "[Unit]\nDescription=Sixfab PMS Agent\nAfter=network.target network-online.target\nRequires=network-online.target\n\n[Service]\nExecStart=/usr/bin/python3 -u agent.py\nWorkingDirectory=/opt/sixfab/pms/agent\nStandardOutput=inherit\nStandardError=inherit\nRestart=always\nRestartSec=3\nUser=pi\n\n[Install]\nWantedBy=multi-user.target" | sudo tee /etc/systemd/system/pms_agent.service && sudo systemctl daemon-reload && sudo systemctl restart pms_agent')
execute_fix("10.07.2020-distribution-service", r"""pip3 uninstall sixfab-power-python-api; sudo pip3 uninstall sixfab-power-python-api; pip3 install -U sixfab-power-python-api;API_LOCATION=$(cd /opt/sixfab/pms/api&&sudo git remote show origin);if [[ $API_LOCATION == *"sixfab.com/sixfab-power/api"* ]];then sudo rm -r /opt/sixfab/pms/api;sudo git clone https://github.com/sixfab/power_distribution-service.git /opt/sixfab/pms/api;pip3 install -r /opt/sixfab/pms/api/requirements.txt;sudo touch /etc/systemd/system/sixfab_power_api.service;echo "[Unit]
Description=Sixfab UPS HAT Distributed API

[Service]
User=pi
ExecStart=/usr/bin/python3 /opt/sixfab/pms/api/run_server.py

[Install]
WantedBy=multi-user.target"|sudo tee /etc/systemd/system/sixfab_power_api.service;sudo systemctl daemon-reload;sudo systemctl enable sixfab_power_api;sudo systemctl start sixfab_power_api;fi""")
