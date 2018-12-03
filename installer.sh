#!/usr/bin/env bash

set -o posix

echo "Checking system"
command -v systemctl > /dev/null 2>&1 || { echo "[ERROR] systemd is required!"; exit 1; }

if [[ -z "$KEEPER_HOME" ]]; then
  export KEEPER_HOME="$(cd "`dirname "$0"`"; pwd)"
fi

finish() {
  pkill -9 -P $$
}

trap finish EXIT

echo "[INFO] Installing required software inside ${KEEPER_HOME}"
sudo apt-get install -y python3 python3-venv python3-pip
echo "[INFO] Creating virtual environment for Keeper"
python3 -m venv "${KEEPER_HOME}"
source "${KEEPER_HOME}/bin/activate"
echo "[INFO] Installing required components"
python3 -m pip install -r requirements.txt
deactivate
chmod 755 "${KEEPER_HOME}/bin/keeper.sh"
sudo cat > "${KEEPER_HOME}/config/keeper-config.yaml" <<- EOF
heartbeat.interval: 30
heartbeat.delay: 10
heartbeat.restart.delay: 180
heartbeat.topic: "homeassistant/binary_sensor/keeper/state"
restart.command: "sudo systemctl restart home-assistant@homeassistant"
mqtt.broker:
mqtt.port:
mqtt.user:
mqtt.pass:
mqtt.command: "sudo systemctl restart mosquitto.service"
EOF
echo "[INFO] Creating Keeper service"
cat > "/etc/systemd/system/keeper.service" <<- EOF
[Unit]
Description=keeper service
After=network.target

[Service]
Type=simple
ExecStart=${KEEPER_HOME}/bin/keeper.sh
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF
echo "[INFO] Enabling Keeper service"
sudo systemctl enable keeper
echo "[INFO] Installation completed. Please configure your Keeper in keeper-config.yaml inside config folder"
echo "[INFO] Execute \"sudo systemctl restart keeper\" to (re)start Keeper service"