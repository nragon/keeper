# Welcome to Keeper
[Keeper](https://github.com/nragon/keeper) is an open source service manager. Currently, monitors home assistant service and mqtt services.
MQTT service is monitored by checking connections to the service and home assistant is monitored using an heartbeating mechanism. Through MQTT we exchange heartbeat messages is home assistant in order to determine if its running.

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

# Contributing
Pull requests and issues on [github](https://github.com/nragon/keeper) are very grateful. Feel free to suggest any improvement.

# Licensing
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details