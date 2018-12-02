from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep
from datetime import datetime, timedelta
from core import common, logger, constants
from core.mqtt import MqttClient
from core.storage import Storage

running = False


class Heartbeater(object):
    def __init__(self, interval, delay, topic, command, storage, mqtt_client):
        self.attempts = 0
        self.misses = 0
        self.missed_heartbeats = storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT)
        self.ha_restarts = storage.get_int(constants.HEARTBEATER_HA_RESTARTS)
        self.system_restarts = storage.get_int(constants.HEARTBEATER_SYSTEM_RESTARTS)
        self.command = command
        mqtt_client.on_message = self.recv
        mqtt_client.on_connect = self.subscribe
        mqtt_client.on_not_connect = Heartbeater.on_not_connect
        self.mqtt_client = mqtt_client
        self.inc = storage.inc
        self.last_status = False
        self.put = storage.put
        self.put(constants.CONNECTOR_CONNECTION_STATUS, constants.CONNECTOR_CONNECTION_NOK)
        self.now = datetime.now
        self.last_message = None
        self.last_known_message = None
        self.interval = interval
        self.topic = topic
        self.delay = delay
        self.inc = storage.inc

    def subscribe(self, client):
        client.subscribe(self.topic)

    @staticmethod
    def on_not_connect(client):
        logger.warning("unable to connect %s:%s" % (client._host, client._port))
        logger.warning("retrying in 10 seconds")
        sleep(10)

    def reconnect(self, wait=True):
        self.mqtt_client.reconnect(wait)

    def connect(self, wait=True):
        self.mqtt_client.reconnect(wait)

    def recv(self):
        self.last_message = self.now()

    def wait_ha_connection(self):
        self.last_message = self.now()

    def monitor(self):
        diff = (self.now() - self.last_message).total_seconds()
        if diff > self.interval + self.delay:
            logger.warning("heartbeat threshold reached")
            if self.misses < 3:
                self.misses += 1
                self.last_message += timedelta(seconds=self.interval)
                self.missed_heartbeats = self.inc(constants.HEARTBEATER_MISSED_HEARTBEAT, self.missed_heartbeats)
                logger.info("tolerating missed heartbeat (%s of 3)" % self.misses)
            elif self.attempts < 3:
                self.attempts += 1
                self.misses = 0
                logger.warning("max of misses reached")
                logger.info("restarting ha service (%s of 3) with command %s" % (self.attempts, " ".join(self.command)))
                if common.exec_command(self.command):
                    self.ha_restarts = self.inc(constants.HEARTBEATER_HA_RESTARTS, self.ha_restarts)
                    self.wait_ha_connection()
            else:
                logger.warning("heartbeat still failing after 3 restarts")
                logger.info("rebooting")
                self.system_restarts = self.inc(constants.HEARTBEATER_SYSTEM_RESTARTS, self.system_restarts)
                common.exec_command(["sudo", "reboot", "-f"])

            self.last_known_message = self.last_message

        if self.last_known_message != self.last_message:
            self.misses = 0
            self.attempts = 0


def start():
    pid = getpid()
    logger.info("starting heartbeater[pid=%s]" % pid)
    config = common.load_config()
    mqtt_client = MqttClient("keeperheartbeater", config)
    with Storage() as storage:
        heartbeater = Heartbeater(config["heartbeat.interval"], config["heartbeat.delay"], config["heartbeat.topic"],
                                  config["mqtt.command"].split(" "), storage, mqtt_client)
        del config
        storage.put(constants.HEARTBEATER_STATUS, constants.STATUS_RUNNING)
        try:
            loop(mqtt_client, heartbeater)
        finally:
            logger.info("heartbeater[pid=%s] is stopping" % pid)
            storage.put(constants.HEARTBEATER_STATUS, constants.STATUS_NOT_RUNNING)
            mqtt_client.disconnect()


def loop(mqtt_client, heartbeater):
    global running
    running = True
    heartbeater.wait_ha_connection()
    while running:
        if mqtt_client.connection_status() != 2 and running:
            heartbeater.reconnect()

        mqtt_client.loop()
        heartbeater.monitor()
        sleep(1)


def get_metrics_defaults():
    return [constants.HEARTBEATER_STATUS, constants.HEARTBEATER_MISSED_HEARTBEAT, constants.HEARTBEATER_HA_RESTARTS,
            constants.HEARTBEATER_SYSTEM_RESTARTS]


def stop():
    global running
    running = False


def handle_signal(signum=None, frame=None):
    stop()
    common.stop(signum, frame)


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
