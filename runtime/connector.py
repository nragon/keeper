from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep

import paho.mqtt.client as mqtt

from core import common, logger, storage

CONNECTOR_STATUS = "connectorStatus"
CONNECTOR_CONNECTION_STATUS = "connectorConnectionStatus"
CONNECTOR_FAILED_CONNECTIONS = "connectorFailedConnections"
CONNECTOR_MQTT_RESTARTS = "connectorMQTTRestarts"
CONNECTOR_CONNECTION_OK = "Stable"
CONNECTOR_CONNECTION_NOK = "Not Stable"
PID = getpid()
running = False


def start():
    logger.info("starting connector manager[pid=%s]" % PID)
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config.get("mqtt.user")
    pwd = config.get("mqtt.pass")
    command = config["mqtt.command"].split(" ")
    del config
    with storage.get_connection() as conn:
        storage.put(conn, CONNECTOR_STATUS, common.STATUS_RUNNING)
        try:
            loop(conn, broker, port, user, pwd, command)
        finally:
            storage.put(conn, CONNECTOR_STATUS, common.STATUS_NOT_RUNNING)
            logger.info("connector[pid=%s] is stopping" % PID)


def loop(conn, broker, port, user, pwd, command):
    inc = storage.inc
    put = storage.put
    get_int = storage.get_int
    failed_connections = get_int(conn, CONNECTOR_FAILED_CONNECTIONS)
    if not failed_connections:
        failed_connections = 0

    client = connect(conn, broker, port, user, pwd, command)
    last_status = False
    put(conn, CONNECTOR_CONNECTION_STATUS, CONNECTOR_CONNECTION_NOK)
    global running
    running = True
    while running:
        if client.loop() > 0 and running:
            failed_connections = inc(conn, CONNECTOR_FAILED_CONNECTIONS, failed_connections)
            if last_status:
                put(conn, CONNECTOR_CONNECTION_STATUS, CONNECTOR_CONNECTION_NOK)
                last_status = 0

            client = connect(conn, broker, port, user, pwd, command)
        else:
            if not last_status:
                put(conn, CONNECTOR_CONNECTION_STATUS, CONNECTOR_CONNECTION_OK)
                last_status = 1

            sleep(1)


def connect(conn, broker, port, user, pwd, command):
    attempts = 0
    while running:
        try:
            logger.info("checking connection to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="keeper_connector")
            if user and pwd:
                client.username_pw_set(user, pwd)

            client.connect(broker, port, 30)
            if client.loop() == 0:
                logger.info("connection to %s:%s is ok" % (broker, port))
                return client
        except:
            if attempts >= 3:
                logger.warning("max of 3 connection attempts was reached")
                logger.warning("restarting mqtt service")
                if common.exec_command(command):
                    mqtt_restarts = storage.get_int(conn, CONNECTOR_FAILED_CONNECTIONS)
                    if not mqtt_restarts:
                        mqtt_restarts = 0

                    storage.inc(conn, CONNECTOR_MQTT_RESTARTS, mqtt_restarts)
                    sleep(30)
                else:
                    logger.error("unable to restart mqtt service with command %s" % command)

                attempts = 0
            else:
                attempts += 1
                logger.warning("broker is not responding (%s of 3)" % attempts)
                logger.warning("retrying in 5 seconds")
                sleep(5)


def stop():
    global running
    running = False


def handle_signal(signum=None, frame=None):
    stop()
    common.stop()


def main():
    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during connector execution: %s" % e)
