#!/usr/bin/env bash

set -o posix

echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] checking system"
# checking if systemd is installed
if [[ ! -x "$(command -v systemctl)" ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] systemd is required!";
    exit 1;
fi
# kill all processes launched by this setup
finish() {
  pkill -9 -P $$
}

trap finish EXIT
# install required software
if [[ ! -x "$(command -v python3)" ]] || [[ ! -x "$(command -v git)" ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] installing required software"
    sudo apt-get install -y python3 python3-venv python3-pip git
    if [[ $? -ne 0 ]]; then
        echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable to install required software"
        exit 1
    fi
fi
export KEEPER_HOME="$(cd "`dirname "$0"`"; pwd)"
# clone repo
if [[ ! -d "${KEEPER_HOME}/runtime" ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] getting latest keeper"
    git clone --depth 1 -b master https://github.com/nragon/keeper.git "${KEEPER_HOME}/tmp" && \
    mv ${KEEPER_HOME}/tmp/* "${KEEPER_HOME}" && \
    rm -rf "${KEEPER_HOME}/tmp" && \
    rm -rf "${KEEPER_HOME}/tests" && \
    rm -rf "${KEEPER_HOME}/setup"
    if [[ $? -ne 0 ]]; then
        echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable get keeper"
        exit 1
    fi
fi
# creating a venv to execute keeper
if [[ ! -x "$(command -v ${KEEPER_HOME}/bin/python3)" ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] creating virtual environment"
    python3 -m venv "${KEEPER_HOME}" && \
    source "${KEEPER_HOME}/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable to create virtual environment"
        exit 1
    fi
    # install requirements
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] installing required components"
    python3 -m pip install -r "${KEEPER_HOME}/requirements.txt" && \
    deactivate
    if [[ $? -ne 0 ]]; then
        echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable to install required components"
        exit 1
    fi
fi
# create a config properties
echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] creating configuration properties"
read -p "Heartbeat Interval: " hi
read -p "Heartbeat Delay: " hd
read -p "Heartbeat Topic: " ht
read -p "HA Restart Command: " hrc
read -p "System Restart Command: " src
read -p "MQTT Broker: " mb
read -p "MQTT Port: " mp
read -p "MQTT User: " mu
read -p "MQTT Password: " mpw
read -p "MQTT Restart Command: " mrc
cat > "${KEEPER_HOME}/config/keeper.json" <<- EOF
{
    "heartbeat.interval": ${hi},
    "heartbeat.delay": ${hd},
    "heartbeat.topic": "${ht}",
    "ha.restart.command": "${hrc}",
    "system.restart.command": "${src}",
    "mqtt.broker": "${mb}",
    "mqtt.port": ${mp},
    "mqtt.user": "${mu}",
    "mqtt.pass": "${mpw}",
    "mqtt.restart.command": "${mrc}",
    "debug": false
}
EOF
if [[ $? -ne 0 ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable create configuration properties"
    exit 1
fi
# create systemd service
echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] creating service"
sudo cat > "${KEEPER_HOME}/config/keeper.service" <<- EOF
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
if [[ $? -ne 0 ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable create servicee"
    exit 1
fi

sudo mv "${KEEPER_HOME}/config/keeper.service" "/etc/systemd/system"
if [[ $? -ne 0 ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable create servicee"
    exit 1
fi
# enable service
echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] enabling and starting keeper"
chmod a+x "${KEEPER_HOME}/bin/keeper.sh" && \
sudo systemctl daemon-reload && \
sudo systemctl enable keeper && \
sudo systemctl restart keeper
if [[ $? -ne 0 ]]; then
    echo "[$(date '+%d/%m/%Y %H:%M:%S') - ERROR] unable enable or start keeper"
    exit 1
fi

echo "[$(date '+%d/%m/%Y %H:%M:%S') - INFO] setup completed"
exit 0