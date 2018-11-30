from json import dumps
from os import getpid

import paho.mqtt.client as mqtt
from signal import signal, SIGTERM, SIGINT
from time import sleep

from core import common, logger, storage

REPORTER_CONFIG_TOPIC = "homeassistant/sensor/keeperReporter-%s/config"
REPORTER_CONFIG_PAYLOAD = "{\"name\": \"keeperReport-%(s)s\", \"state_topic\": \"homeassistant/sensor/keeperReporter/state\", \"value_template\": \"{{ value_json.%(s)s }}\"}"
REPORTER_TOPIC = "homeassistant/sensor/keeperReporter/state"
REPORTER_STATUS = "reporterStatus"
PID = getpid()
running = False


def start():
    logger.info("starting reported[pid=%s]" % PID)
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config.get("mqtt.user")
    pwd = config.get("mqtt.pass")
    del config
    with storage.get_connection() as conn:
        storage.put(conn, REPORTER_STATUS, common.STATUS_RUNNING)
        try:
            loop(conn, broker, port, user, pwd)
        finally:
            storage.put(conn, REPORTER_STATUS, common.STATUS_NOT_RUNNING)
            logger.info("stopping watcher[pid=%s]" % PID)


def loop(conn, broker, port, user, pwd):
    global running
    running = True
    client = connect(broker, port, user, pwd)
    registered = register(client, conn)
    while running:
        if client.loop() > 0 and running:
            client = connect(broker, port, user, pwd)
        else:
            try:
                send_report(registered, client, conn)
                sleep(30)
            except Exception as e:
                logger.error("failed to send report: %s" % e)


def register(client, conn):
    try:
        keys = storage.get_keys(conn)
        if not keys:
            return

        for key in keys:
            client.publish(REPORTER_CONFIG_TOPIC % key, REPORTER_CONFIG_PAYLOAD % {"s": key}, 1,
                           True).wait_for_publish()

        return list(keys)
    except Exception as e:
        logger.error("failed to register auto discover: %s" % e)


def send_report(registered, client, conn):
    result = storage.get_all(conn)
    if not result:
        return

    report = {}
    for record in result:
        key = record[0]
        report[key] = record[1]
        if key not in registered:
            client.publish(REPORTER_CONFIG_TOPIC % key, REPORTER_CONFIG_PAYLOAD % {"s": key}, 1,
                           True).wait_for_publish()
            registered.append(key)

    client.publish(REPORTER_TOPIC, dumps(report), 1, True)


def connect(broker, port, user, pwd):
    while running:
        try:
            logger.info("connecting to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="visionreporter")
            if user and pwd:
                client.username_pw_set(user, pwd)

            client.connect(broker, port, 60)

            return client
        except Exception as e:
            logger.warning("unable to connect %s:%s: %s" % (broker, port, e))
            logger.warning("retrying in 10 seconds")
            sleep(10)


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
        logger.error("An error occurred during watcher execution: %s" % e)
