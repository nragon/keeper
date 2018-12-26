#!/usr/bin/env bash

set -o posix
export KEEPER_HOME="$(cd "`dirname "$0"`"/..; pwd)"
finish() {
  pkill -9 -P $$
}

trap finish EXIT

if [[ ! -e "${KEEPER_HOME}/log/keeper.log" ]]; then
    mkdir "${KEEPER_HOME}/log"
    touch "${KEEPER_HOME}/log/keeper.log"
fi

sudo -E "${KEEPER_HOME}/bin/python3" -u "${KEEPER_HOME}/keeper.py" >> "${KEEPER_HOME}/log/keeper.log" 2>&1
wait $!