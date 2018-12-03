from os import environ

KEEPER_HOME = environ["KEEPER_HOME"]
STATUS_RUNNING = "Running"
STATUS_NOT_RUNNING = "Not Running"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
CONNECTOR_CONNECTION_OK = "Stable"
CONNECTOR_CONNECTION_NOK = "Not Stable"
CONNECTOR_STATUS = "connectorStatus"
CONNECTOR_CONNECTION_STATUS = "mqttConnectionStatus"
CONNECTOR_FAILED_CONNECTIONS = "mqttFailedConnections"
CONNECTOR_MQTT_RESTARTS = "mqttRestarts"
CONNECTOR_LAST_MQTT_RESTART = "lastMqttRestart"
HEARTBEATER_STATUS = "heartbeaterStatus"
HEARTBEATER_MISSED_HEARTBEAT = "missedHeartbeat"
HEARTBEATER_HA_RESTARTS = "HARestarts"
HEARTBEATER_LAST_HA_RESTARTS = "lastHARestart"
HEARTBEATER_SYSTEM_RESTARTS = "systemRestarts"
HEARTBEATER_LAST_SYSTEM_RESTART = "lastSystemRestart"
HEARTBEATER_LAST_HEARTBEAT = "lastHeartbeat"
REPORTER_CONFIG_TOPIC = "homeassistant/sensor/k-%s/config"
REPORTER_CONFIG_PAYLOAD = "{\"name\": \"k-%(s)s\", \"state_topic\": " \
                          "\"homeassistant/sensor/keeper/state\", \"value_template\": \"{{ value_json.%(s)s " \
                          "}}\"} "
REPORTER_TOPIC = "homeassistant/sensor/keeper/state"
REPORTER_STATUS = "reporterStatus"
