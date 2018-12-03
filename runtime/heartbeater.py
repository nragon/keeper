from json import dumps
from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep, strftime
from datetime import datetime, timedelta
from core import common, logger, constants
from core.mqtt import MqttClient
from core.storage import Storage

running = False


class Heartbeater(object):
    def __init__(self, interval, delay, topic, command, storage, mqtt_client):
        self.attempts = 0
        self.misses = 0
        self.command = command
        mqtt_client.on_message = self.recv
        mqtt_client.on_connect = self.subscribe
        self.mqtt_client = mqtt_client
        self.inc = storage.inc
        self.last_status = False
        self.put = storage.put
        self.missed_heartbeats = storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT)
        self.put(constants.HEARTBEATER_MISSED_HEARTBEAT, self.missed_heartbeats)
        self.ha_restarts = storage.get_int(constants.HEARTBEATER_HA_RESTARTS)
        self.put(constants.HEARTBEATER_HA_RESTARTS, self.ha_restarts)
        self.system_restarts = storage.get_int(constants.HEARTBEATER_SYSTEM_RESTARTS)
        self.put(constants.HEARTBEATER_SYSTEM_RESTARTS, self.system_restarts)
        self.now = datetime.now
        self.last_message = None
        self.last_known_message = None
        self.interval = interval
        self.topic = topic
        self.delay = delay

    def subscribe(self, client, userdata, flags, rc):
        logger.info("subscribing topic %s" % self.topic)
        client.subscribe(self.topic)

    def connect(self, wait=True):
        self.mqtt_client.reconnect(wait)

    def recv(self, client, userdata, message):
        self.last_message = self.now()
        self.put(constants.HEARTBEATER_LAST_HEARTBEAT, strftime(constants.TIME_FORMAT))

    def wait_ha_connection(self):
        self.last_message = None
        self.last_known_message = None
        since = self.now()
        logger.info("waiting for ha service")
        while running and not self.last_message and (self.now() - since).total_seconds() <= 120:
            self.mqtt_client.loop()
            sleep(1)

        if self.last_message:
            logger.info("ha is reachable")
        else:
            self.last_message = self.now()
            self.last_known_message = self.last_message
            logger.warning("ha service still not reachable")

    def monitor(self):
        diff = (self.now() - self.last_message).total_seconds()
        if diff > self.interval + self.delay:
            logger.warning("heartbeat threshold reached")
            if self.misses < 3:
                self.misses += 1
                self.last_message += timedelta(seconds=self.interval)
                self.missed_heartbeats = self.inc(constants.HEARTBEATER_MISSED_HEARTBEAT, self.missed_heartbeats)
                logger.warning("tolerating missed heartbeat (%s of 3)" % self.misses)
            elif self.attempts < 3:
                self.attempts += 1
                self.misses = 0
                logger.warning("max of misses reached")
                logger.warning(
                    "restarting ha service (%s of 3) with command %s" % (self.attempts, " ".join(self.command)))
                if common.exec_command(self.command):
                    self.ha_restarts = self.inc(constants.HEARTBEATER_HA_RESTARTS, self.ha_restarts)
                    self.put(constants.HEARTBEATER_LAST_HA_RESTARTS, strftime(constants.TIME_FORMAT))
                    self.wait_ha_connection()
            else:
                logger.warning("heartbeat still failing after 3 restarts")
                logger.warning("rebooting")
                self.system_restarts = self.inc(constants.HEARTBEATER_SYSTEM_RESTARTS, self.system_restarts)
                self.put(constants.HEARTBEATER_LAST_SYSTEM_RESTART, strftime(constants.TIME_FORMAT))
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
                                  config["restart.command"].split(" "), storage, mqtt_client)
        del config
        storage.put(constants.HEARTBEATER_STATUS, constants.STATUS_RUNNING)
        try:
            loop(mqtt_client, heartbeater)
        except Exception as e:
            if running:
                raise e
        finally:
            logger.info("stopping heartbeater[pid=%s]" % pid)
            try:
                storage.put(constants.HEARTBEATER_STATUS, constants.STATUS_NOT_RUNNING)
                mqtt_client.disconnect()
            except Exception:
                pass


def loop(mqtt_client, heartbeater):
    global running
    running = True
    heartbeater.connect()
    heartbeater.wait_ha_connection()
    while running:
        if mqtt_client.connection_status() != 2 and running:
            mqtt_client.wait_connection()
            heartbeater.wait_ha_connection()

        mqtt_client.loop()
        heartbeater.monitor()
        sleep(1)


def get_metrics_defaults():
    return [constants.HEARTBEATER_STATUS, constants.HEARTBEATER_MISSED_HEARTBEAT, constants.HEARTBEATER_HA_RESTARTS,
            constants.HEARTBEATER_SYSTEM_RESTARTS, constants.HEARTBEATER_LAST_HEARTBEAT,
            constants.HEARTBEATER_LAST_HA_RESTARTS, constants.HEARTBEATER_LAST_SYSTEM_RESTART]


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
        logger.error("An error occurred during heartbeater execution: %s" % e)
