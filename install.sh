cat << "EOF"
 _____ _       __      _      _________  ___ _____ 
/  ___(_)     / _|    | |     | ___ \  \/  |/  ___|
\ `--. ___  _| |_ __ _| |__   | |_/ / .  . |\ `--. 
 `--. \ \ \/ /  _/ _` | '_ \  |  __/| |\/| | `--. \
/\__/ / |>  <| || (_| | |_) | | |   | |  | |/\__/ /
\____/|_/_/\_\_| \__,_|_.__/  \_|   \_|  |_/\____/ 
EOF

TOKEN="asd"
INTERVAL="10"
AGENT_REPOSITORY="asd"

echo "Creating Sixfab root directory on /opt..."
sudo mkdir -p /opt/sixfab
echo "Root directory created."


echo "Looking for dependencies..."

# Check if git installed
if ! [ -x "$(command -v git)" ]; then
  echo 'Git is not installed, installing...'
  sudo apt-get install git >/dev/null
fi

# Check if python installed
if ! [ -x "$(command -v python3)" ]; then
  echo 'Python3 is not installed, installing...'
  sudo apt-get install python3 >/dev/null
fi

# Check if python installed
if ! [ -x "$(command -v pip3)" ]; then
  echo 'Pip for python3 is not installed, installing...'
  sudo apt-get install python3-pip >/dev/null
fi

echo "Cloning agent source..."
sudo git clone $AGENT_REPOSITORY /opt/sixfab/pms-agent >/dev/null
echo "Agent source cloned."

echo "Installing agent dependencies from PyPI..."
sudo pip3 install -r /opt/sixfab/pms-agent/requirements.txt

echo "Creating environment file..."
sudo touch /opt/sixfab/.env

echo "[pms]
TOKEN=$TOKEN
INTERVAL=$INTERVAL
" > /opt/sixfab/.env

echo "Environment file created."

echo "Initializing systemd service..."

sudo echo "[Unit]
Description=Sixfab PMS Agent
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u agent.py
WorkingDirectory=/opt/sixfab/pms-agent
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/pms_agent.service

echo "Enabling and starting systemd service..."

sudo systemctl enable pms_agent
sudo systemctl start pms_agent

echo "Service initialized successfully."