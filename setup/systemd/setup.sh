#!/usr/bin/env bash

set -o posix
datetime=`date '+%d/%m/%Y %H:%M:%S'`
echo "[$datetime - INFO] checking system"
# checking if systemd is installed
if [[ ! -x "$(command -v systemctl)" ]]; then
    echo "[$datetime - ERROR] systemd is required!";
    exit 1;
fi
# kill all processes launched by this setup
finish() {
  pkill -9 -P $$
}

trap finish EXIT
# install required software
if [[ ! -x "$(command -v python3)" ] || [ ! -x "$(command -v git)" ]]; then
    echo "[$datetime - INFO] installing required software"
    apt-get install -y python3 python3-venv python3-pip git
    if [[ $? -ne 0 ]]; then
        echo "[$datetime - ERROR] unable to install required software"
        exit 1
    fi
fi

export KEEPER_HOME="$(cd "`dirname "$0"`"/../..; pwd)"
# creating a venv to execute keeper
if [[ ! -x "$(command -v source \"${KEEPER_HOME}/bin/activate\")" ]]; then
    echo "[$datetime - INFO] creating virtual environment"
    python3 -m venv "${KEEPER_HOME}" && \
    source "${KEEPER_HOME}/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "[$datetime - ERROR] unable to create virtual environment"
        exit 1
    fi
    # install requirements
    echo "[$datetime - INFO] installing required components"
    python3 -m pip install -r "${KEEPER_HOME}/requirements.txt" && \
    deactivate
    if [[ $? -ne 0 ]]; then
        echo "[$datetime - ERROR] unable to install required components"
        exit 1
    fi
fi
# clone repo
if [[ ! -d "${KEEPER_HOME}/runtime" ]]; then
    echo "[$datetime - INFO] getting latest keeper"
    git clone --depth 1 -b master https://github.com/nragon/keeper.git "${KEEPER_HOME}"
    if [[ $? -ne 0 ]]; then
        echo "[$datetime - ERROR] unable get keeper"
        exit 1
    fi
fi
# create a config properties
echo "[$datetime - INFO] creating configuration properties"
echo -n "Heartbeat Interval: "
read hi
echo -n "Heartbeat Delay: "
read hd
echo -n "Heartbeat Topic: "
read ht
echo -n "HA Restart Command: "
read hrc
echo -n "System Restart Command: "
read src
echo -n "MQTT Broker: "
read mb
echo -n "MQTT Port: "
read mp
echo -n "MQTT User: "
read mu
echo -n "MQTT Password: "
read mpw
echo -n "MQTT Restart Command: "
read mrc
cat > "${KEEPER_HOME}/config/keeper.json" <<- EOF
{
    "heartbeat.interval": "${hi}",
    "heartbeat.delay": "${hd}",
    "heartbeat.topic": "${ht}",
    "ha.restart.command": "${hrc}",
    "system.restart.command": "${src}",
    "mqtt.broker": "${mb}",
    "mqtt.port": "${mp}",
    "mqtt.user": "${mu}",
    "mqtt.pass": "${mpw}",
    "mqtt.restart.command": "${mrc}",
    "debug": false
}
EOF
if [[ $? -ne 0 ]]; then
    echo "[$datetime - ERROR] unable create configuration properties"
    exit 1
fi
# create systemd service
echo "[$datetime - INFO] creating service"
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
if [[ $? -ne 0 ]]; then
    echo "[$datetime - ERROR] unable create servicee"
    exit 1
fi
# enable service
echo "[$datetime - INFO] enabling and starting keeper"
chmod a+x "${KEEPER_HOME}/bin/keeper.sh" && \
systemctl daemon-reload && \
systemctl enable keeper && \
systemctl restart keeper
if [[ $? -ne 0 ]]; then
    echo "[$datetime - ERROR] unable enable or start keeper"
    exit 1
fi

echo "[$datetime - INFO] setup completed"
exit 0