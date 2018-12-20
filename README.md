# Welcome to Keeper
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Keeper](https://github.com/nragon/keeper) is an open source service manager. Currently, monitors home assistant service and mqtt services.
MQTT service is monitored by checking connections to the service and home assistant is monitored using an heartbeating mechanism. Through MQTT we exchange heartbeat messages with home assistant in order to determine if its running.
Every 3 missed messages between [Keeper](https://github.com/nragon/keeper) and home assistant, [Keeper](https://github.com/nragon/keeper) will attempt to restart home assistant. Then, if after 3 restarts home assistant still not responding, the system is rebooted.
In MQTT case, it's only performed a service restart every 3 missed connections

# Table of Contents
- [Installation](#installation)
- [Configuration](#installation)
- [Home Assistant](#homeassistant)
- [Contributing](#contributing)
- [Licensing](#licensing)
# Installation
Download Keeper release (replace <version> with pretended version)
```` 
wget -q --show-progress --no-use-server-timestamps https://github.com/nragon/keeper/archive/<version>.tar.gz
````
Unpack package and change to unpacked directory
````` 
tar xvf <version>.tar.gz
cd keeper-<versions>
`````
Execute installer script
````
chmod 755 installer.sh
sudo ./installer.sh
````
Follow instructions

# Configuration
You can find a set of properties in a yaml file inside [config](config) directory that can be tuned and configured according with you own settings

Configuration | Definition
--------------| ----------
heartbeat.interval | Interval between heartbeat message. This should match number of seconds in home assistant automation
heartbeat.delay | Number of seconds we should wait before considering a miss heartbeat message
heartbeat.topic | Heartbeat topic
ha.restart.command | Command to restart home assistant service
system.restart.command | Command to restart system
mqtt.broker | MQTT broker ip
mqtt.port | MQTT broker port
mqtt.user | MQTT user used
mqtt.pass | MQTT user password
mqtt.restart.command | Command to restart MQTT service

# Home Assistant
In home assistant side we should configure an automation capable o sending heartbeat messages to [Keeper](https://github.com/nragon/keeper).
The number of seconds and topic are different depending on [Keeper](https://github.com/nragon/keeper) configurations
````
- id: keeperheartbeat
  initial_state: "on"
  trigger:
    platform: time
    seconds: "/<numberofseconds>"
  action:
    service: mqtt.publish
    data:
      topic: "<heartbeattopic>"
      payload: "1"
````
# Contributing
Pull requests and issues on [github](https://github.com/nragon/keeper) are welcome. Feel free to suggest any improvement.

# Licensing
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
