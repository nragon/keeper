#!/usr/bin/env bash

set -o posix
datetime=`date '+%d/%m/%Y %H:%M:%S'`
# install required software
if [[ ! -x "$(command -v python3)" ] || [ ! -x "$(command -v git)" ]]; then
    echo "[$datetime - INFO] installing required software"
    apt-get install -y python3 python3-venv python3-pip git
    if [[ $? -ne 0 ]]; then
        echo "[$datetime - ERROR] unable to install required software"
        exit 1
    fi
fi

export KEEPER_HOME="$(cd "`dirname "$0"`"; pwd)"
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

echo "[$datetime - INFO] running keeper"
cp /data/options.json ${KEEPER_HOME}/keeper.json && \
chmod a+x ${KEEPER_HOME}/bin/keeper.sh && \
. ${KEEPER_HOME}/bin/keeper.sh

exit 0