# -*- coding: utf-8 -*-
"""
    Constants
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from os import environ, name

IS_NT = name == "nt"
KEEPER_HOME = environ["KEEPER_HOME"]
STATUS_RUNNING = "Running"
STATUS_NOT_RUNNING = "Not Running"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
CONNECTOR_CONNECTION_OK = "Stable"
CONNECTOR_CONNECTION_NOK = "Not Stable"
CONNECTOR_STATUS = "kpConnectorStatus"
CONNECTOR_STATUS_ICON = "mdi:access-point"
CONNECTOR_CONNECTION_STATUS = "kpMQTTConnectionStatus"
CONNECTOR_CONNECTION_STATUS_ICON = "mdi:network"
CONNECTOR_FAILED_CONNECTIONS = "kpMQTTFailedConnections"
CONNECTOR_FAILED_CONNECTIONS_ICON = "mdi:sync-alert"
CONNECTOR_MQTT_RESTARTS = "kpMQTTRestarts"
CONNECTOR_MQTT_RESTARTS_ICON = "mdi:restart"
CONNECTOR_LAST_MQTT_RESTART = "kpLastMqttRestart"
CONNECTOR_LAST_MQTT_RESTART_ICON = "mdi:calendar-clock"
HEARTBEATER_STATUS = "kpHeartbeaterStatus"
HEARTBEATER_STATUS_ICON = "mdi:heart-pulse"
HEARTBEATER_MISSED_HEARTBEAT = "kpMissedHeartbeats"
HEARTBEATER_MISSED_HEARTBEAT_ICON = "mdi:pipe-leak"
HEARTBEATER_HA_RESTARTS = "kpHARestarts"
HEARTBEATER_HA_RESTARTS_ICON = "mdi:restart"
HEARTBEATER_LAST_HA_RESTART = "kpLastHARestart"
HEARTBEATER_LAST_HA_RESTART_ICON = "mdi:calendar-clock"
HEARTBEATER_SYSTEM_RESTARTS = "kpSystemRestarts"
HEARTBEATER_SYSTEM_RESTARTS_ICON = "mdi:server"
HEARTBEATER_LAST_SYSTEM_RESTART = "kpLastSystemRestart"
HEARTBEATER_LAST_SYSTEM_RESTART_ICON = "mdi:calendar-clock"
HEARTBEATER_LAST_HEARTBEAT = "kpLastHeartbeat"
HEARTBEATER_LAST_HEARTBEAT_ICON = "mdi:calendar-clock"
STATE_TOPIC = "homeassistant/sensor/%s/state"
CONFIG_TOPIC = "homeassistant/sensor/%s/config"
CONFIG_PAYLOAD = "{\"name\": \"%s\", \"state_topic\": \"" + STATE_TOPIC + "\", \"icon\": \"%s\"}"
