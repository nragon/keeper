# -*- coding: utf-8 -*-
"""
    Heartbeater manager handles heartbeat exchanges with ha
    restarts ha service or even the system if too many heartbeat
    messages are lost
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep, strftime
from datetime import datetime, timedelta
from core import exec_command, load_config, constants, Logger, HEARTBEATER_STATUS, STATUS_RUNNING, STATUS_NOT_RUNNING
from kio import MqttClient, Storage

running = False


class Heartbeater(object):
    def __init__(self, config, storage):
        self.attempts = 0
        self.misses = 0
        self.ha_command = config["ha.restart.command"].split(" ")
        self.sys_command = config["system.restart.command"].split(" ")
        self.inc = storage.inc
        put = storage.put
        get_int = storage.get_int
        self.missed_heartbeats = put(constants.HEARTBEATER_MISSED_HEARTBEAT,
                                     get_int(constants.HEARTBEATER_MISSED_HEARTBEAT))
        self.ha_restarts = put(constants.HEARTBEATER_HA_RESTARTS, get_int(constants.HEARTBEATER_HA_RESTARTS))
        self.system_restarts = put(constants.HEARTBEATER_SYSTEM_RESTARTS,
                                   get_int(constants.HEARTBEATER_SYSTEM_RESTARTS))
        self.put = put
        self.now = datetime.now
        self.mqtt_client = None
        self.last_message = None
        self.last_known_message = None
        self.interval = config["heartbeat.interval"]
        self.topic = config["heartbeat.topic"]
        self.delay = config["heartbeat.delay"]
        self.logger = Logger()

    def __enter__(self):
        """
        updates manager status when entering context
        :return: Heartbeater object
        """

        self.logger.info("starting heartbeater manager[pid=%s]" % getpid())
        self.put(HEARTBEATER_STATUS, STATUS_RUNNING)

        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        """
        updates manager status when exiting context
        :param type:
        :param value:
        :param traceback:
        """

        self.logger.info("stopping heartbeater[pid=%s]" % getpid())
        self.put(HEARTBEATER_STATUS, STATUS_NOT_RUNNING)

    def set_mqtt(self, mqtt_client):
        """
        sets mqtt client
        :param mqtt_client: mqtt client
        """
        self.mqtt_client = mqtt_client

    # noinspection PyUnusedLocal
    def on_connect(self, client, userdata, flags, rc):
        """
        subscribes to heartbeat topic
        :param client: mqtt client
        :param userdata: userdata dict
        :param flags: flags
        :param rc: rc code
        """
        self.logger.info("subscribing topic %s" % self.topic)
        client.subscribe(self.topic)

    # noinspection PyUnusedLocal
    def on_message(self, client, userdata, message):
        """
        updates heartbeat message timestamp
        :param client: mqtt client
        :param userdata: userdata dict
        :param message: message received
        """
        self.last_message = self.now()
        self.put(constants.HEARTBEATER_LAST_HEARTBEAT, strftime(constants.TIME_FORMAT))

    def wait_ha_connection(self):
        """
        waits for a heartbeat message or timeout of 120 seconds
        """
        self.last_message = None
        self.last_known_message = None
        now = self.now
        limit = now() + timedelta(seconds=120)
        self.logger.info("waiting for ha service")
        while running and not self.last_message and now() < limit:
            self.mqtt_client.loop()
            sleep(1)

        if self.last_message:
            self.logger.info("ha is reachable")
        else:
            self.last_message = self.now()
            self.last_known_message = self.last_message
            self.logger.warning("ha service still not reachable")

    def monitor(self):
        """
        monitors heartbeat messages and restarts ha if 3 messages are missed
        also restarts system after 3 ha restarts
        """

        if (self.now() - self.last_message).total_seconds() > self.interval + self.delay:
            self.logger.warning("heartbeat threshold reached")
            if self.misses < 3:
                self.misses += 1
                self.last_message += timedelta(seconds=self.interval)
                self.missed_heartbeats = self.inc(constants.HEARTBEATER_MISSED_HEARTBEAT, self.missed_heartbeats)
                self.logger.warning("tolerating missed heartbeat (%s of 3)" % self.misses)
            elif self.attempts < 3:
                self.attempts += 1
                self.misses = 0
                self.logger.warning("max of misses reached")
                self.logger.warning(
                    "restarting ha service (%s of 3) with command %s" % (self.attempts, " ".join(self.ha_command)))
                if exec_command(self.ha_command):
                    self.ha_restarts = self.inc(constants.HEARTBEATER_HA_RESTARTS, self.ha_restarts)
                    self.put(constants.HEARTBEATER_LAST_HA_RESTARTS, strftime(constants.TIME_FORMAT))
                    self.wait_ha_connection()
            else:
                self.logger.warning("heartbeat still failing after 3 restarts")
                self.logger.warning("rebooting")
                self.system_restarts = self.inc(constants.HEARTBEATER_SYSTEM_RESTARTS, self.system_restarts)
                self.put(constants.HEARTBEATER_LAST_SYSTEM_RESTART, strftime(constants.TIME_FORMAT))
                exec_command(self.sys_command)

            self.last_known_message = self.last_message

        if self.last_known_message != self.last_message:
            self.misses = 0
            self.attempts = 0


def start():
    """
    starts this manager and calls it's routine
    loop which monitors heartbeat messages
    """

    config = load_config()
    with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperheartbeater", config,
                                                                                       manager=heartbeater) as mqtt_client:
        del config
        try:
            loop(mqtt_client, heartbeater)
        except Exception as e:
            if running:
                raise e


def loop(mqtt_client, heartbeater):
    """
    continuously receives heartbeat message
    :param mqtt_client: mqtt client
    :param heartbeater: manager
    """

    global running
    running = True
    heartbeater.wait_ha_connection()
    while running:
        if mqtt_client.connection_status() != 2 and running:
            mqtt_client.wait_connection()
            heartbeater.wait_ha_connection()

        mqtt_client.loop()
        heartbeater.monitor()
        sleep(1)


# noinspection PyUnusedLocal
def handle_signal(signum=None, frame=None):
    """
    interrupts main loop
    :param signum:
    :param frame:
    """

    global running
    running = False


def main():
    """
    main method which starts the manager
    """

    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    try:
        start()
    except KeyboardInterrupt:
        pass
