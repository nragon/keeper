# Welcome to Keeper
[Keeper](https://github.com/nragon/keeper) is an open source service manager. Currently, monitors home assistant service and mqtt services.
MQTT service is monitored by checking connections to the service and home assistant is monitored using an heartbeating mechanism. Through MQTT we exchange heartbeat messages is home assistant in order to determine if its running.

# Table of Contents
- [Installation](#installation)
- [Configuration](#installation)
- [Home Assistant](#homeassistant)
- [Contributing](#contributing)
- [Licensing](#licensing)
# Installation
Install the requirements
````
python3 -m pip install -r requirements.txt
```` 

Create a system service to initialize keeper at boot
Note that the following service depends on home assistant and mosquitto(MQTT) service
````
[Unit]
Description=keeper service
After=network.target home-assistant@homeassistant.service mosquitto.service

[Service]
Type=simple
ExecStart=<pathtobin>/keeper.sh
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
````
# Configuration
You can find a set of properties in a yaml file inside [config](config) directory that can be tuned and configured according with you own settings

Configuration | Definition
--------------| ----------
heartbeat.interval | Interval between heartbeat message. This should match number of seconds in home assistant automation
heartbeat.delay | Number of seconds we should wait before considering a miss heartbeat message
heartbeat.restart.delay | Seconds to wait between home assistant restarts
heartbeat.topic | Heartbeat topic
restart.command | Command to restart home assistant service
mqtt.broker | MQTT broker ip
mqtt.port | MQTT broker port
mqtt.user | MQTT user used
mqtt.pass | MQTT user password
mqtt.command | Command to restart MQTT service

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
Pull requests and issues on [github](https://github.com/nragon/keeper) are very grateful. Feel free to suggest any improvement.

# Licensing
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details