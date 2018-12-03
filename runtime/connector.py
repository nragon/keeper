from json import dumps
from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep, strftime

from core import common, logger, constants
from core.mqtt import MqttClient
from core.storage import Storage

running = False


class Connector(object):
    def __init__(self, command, storage, mqtt_client):
        self.attempts = 0
        self.command = command
        mqtt_client.on_not_connect = self.on_not_connect
        self.mqtt_client = mqtt_client
        self.last_status = False
        self.put = storage.put
        self.put(constants.CONNECTOR_CONNECTION_STATUS, constants.CONNECTOR_CONNECTION_NOK)
        self.mqtt_restarts = storage.get_int(constants.CONNECTOR_MQTT_RESTARTS)
        self.put(constants.CONNECTOR_MQTT_RESTARTS, self.mqtt_restarts)
        self.failed_connections = storage.get_int(constants.CONNECTOR_FAILED_CONNECTIONS)
        self.put(constants.CONNECTOR_FAILED_CONNECTIONS, self.failed_connections)
        self.inc = storage.inc

    def on_not_connect(self):
        if self.attempts >= 3:
            logger.warning("max of 3 connection attempts was reached")
            logger.warning("restarting mqtt service")
            if common.exec_command(self.command):
                self.mqtt_restarts = self.inc(constants.CONNECTOR_MQTT_RESTARTS, self.mqtt_restarts)
                self.put(constants.CONNECTOR_LAST_MQTT_RESTART, strftime(constants.TIME_FORMAT))
                self.mqtt_client.wait_connection()
                self.attempts = 0
        else:
            self.attempts += 1
            self.failed_connections = self.inc(constants.CONNECTOR_FAILED_CONNECTIONS, self.failed_connections)
            logger.warning("broker is not responding (%s of 3)" % self.attempts)
            sleep(5)

    def reconnect(self, wait=True):
        self.put(constants.CONNECTOR_CONNECTION_STATUS, constants.CONNECTOR_CONNECTION_NOK)
        self.connect(wait)

    def connect(self, wait=True):
        if self.mqtt_client.reconnect(wait) == 2:
            self.put(constants.CONNECTOR_CONNECTION_STATUS, constants.CONNECTOR_CONNECTION_OK)


def start():
    pid = getpid()
    logger.info("starting connector manager[pid=%s]" % pid)
    config = common.load_config()
    mqtt_client = MqttClient("keeperconnector", config)
    with Storage() as storage:
        connector = Connector(config["mqtt.restart.command"].split(" "), storage, mqtt_client)
        del config
        storage.put(constants.CONNECTOR_STATUS, constants.STATUS_RUNNING)
        try:
            loop(mqtt_client, connector)
        except Exception as e:
            if running:
                raise e
        finally:
            logger.info("stopping connector[pid=%s]" % pid)
            try:
                storage.put(constants.CONNECTOR_STATUS, constants.STATUS_NOT_RUNNING)
                mqtt_client.disconnect()
            except Exception:
                pass


def loop(mqtt_client, connector):
    global running
    running = True
    connector.connect()
    while running:
        if mqtt_client.connection_status() != 2 and running:
            connector.reconnect()

        sleep(1)


def get_metrics_defaults():
    return [constants.CONNECTOR_STATUS, constants.CONNECTOR_MQTT_RESTARTS, constants.CONNECTOR_FAILED_CONNECTIONS,
            constants.CONNECTOR_CONNECTION_STATUS, constants.CONNECTOR_LAST_MQTT_RESTART]


def handle_signal(signum=None, frame=None):
    global running
    running = False


def main():
    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    logger.init()
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during connector execution: %s" % e)
