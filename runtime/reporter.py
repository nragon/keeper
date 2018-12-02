from json import dumps
from os import getpid
from signal import signal, SIGTERM, SIGINT
from threading import Event

from core import common, logger, constants
from core.mqtt import MqttClient
from core.storage import Storage
from runtime import heartbeater, connector

running = False
wait_loop = Event()


class Reporter(object):
    def __init__(self, storage, mqtt_client):
        mqtt_client.on_connect = self.register
        self.mqtt_client = mqtt_client
        self.get_all = storage.get_all

    def register(self, client, userdata, flags, rc):
        try:
            for key in heartbeater.get_metrics_defaults():
                self.mqtt_client.publish(constants.REPORTER_CONFIG_TOPIC % key,
                                         constants.REPORTER_CONFIG_PAYLOAD % {"s": key})

            for key in connector.get_metrics_defaults():
                self.mqtt_client.publish(constants.REPORTER_CONFIG_TOPIC % key,
                                         constants.REPORTER_CONFIG_PAYLOAD % {"s": key})

        except Exception as e:
            logger.error("failed to register auto discover: %s" % e)

    def send_report(self):
        result = self.get_all()
        if not result:
            return

        report = {}
        for record in result:
            report[record[0]] = record[1]

        self.mqtt_client.publish(constants.REPORTER_TOPIC, dumps(report))

    def connect(self, wait=True):
        self.mqtt_client.reconnect(wait)


def start():
    pid = getpid()
    logger.info("starting reported[pid=%s]" % pid)
    mqtt_client = MqttClient("keeperreporter", common.load_config())
    with Storage() as storage:
        reporter = Reporter(storage, mqtt_client)
        storage.put(constants.REPORTER_STATUS, constants.STATUS_RUNNING)
        try:
            loop(reporter, mqtt_client)
        except Exception as e:
            if running:
                raise e
        finally:
            logger.info("stopping reporter[pid=%s]" % pid)
            try:
                storage.put(constants.REPORTER_STATUS, constants.STATUS_NOT_RUNNING)
                mqtt_client.disconnect()
            except Exception:
                pass


def loop(reporter, mqtt_client):
    global running
    running = True
    reporter.connect()
    while running:
        if mqtt_client.connection_status() != 2 and running:
            mqtt_client.wait_connection()

        reporter.send_report()
        wait_loop.wait(15)


def handle_signal(signum=None, frame=None):
    global running
    running = False
    wait_loop.set()


def main():
    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    logger.init()
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during reporter execution: %s" % e)
