from os import environ

KEEPER_HOME = environ["KEEPER_HOME"]
STATUS_RUNNING = "Running"
STATUS_NOT_RUNNING = "Not Running"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
CONNECTOR_STATUS = "connectorStatus"
CONNECTOR_CONNECTION_STATUS = "connectorConnectionStatus"
CONNECTOR_FAILED_CONNECTIONS = "connectorFailedConnections"
CONNECTOR_MQTT_RESTARTS = "connectorMQTTRestarts"
CONNECTOR_CONNECTION_OK = "Stable"
CONNECTOR_CONNECTION_NOK = "Not Stable"
HEARTBEATER_STATUS = "heartbeaterStatus"
HEARTBEATER_MISSED_HEARTBEAT = "heartbeaterMissedHeartbeat"
HEARTBEATER_HA_RESTARTS = "heartbeaterHARestarts"
HEARTBEATER_SYSTEM_RESTARTS = "heartbeaterSystemRestarts"
REPORTER_CONFIG_TOPIC = "homeassistant/sensor/keeperReporter-%s/config"
REPORTER_CONFIG_PAYLOAD = "{\"name\": \"keeperReport-%(s)s\", \"state_topic\": " \
                          "\"homeassistant/sensor/keeperReporter/state\", \"value_template\": \"{{ value_json.%(s)s " \
                          "}}\"} "
REPORTER_TOPIC = "homeassistant/sensor/keeperReporter/state"
REPORTER_STATUS = "reporterStatus"
