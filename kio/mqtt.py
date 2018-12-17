# -*- coding: utf-8 -*-
"""
    Provides base access to mqtt
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from time import sleep
from paho.mqtt.client import Client
from core import Logger, STATE_TOPIC, CONFIG_TOPIC, CONFIG_PAYLOAD


class MqttClient(object):
    """
    Holds connection and basic methods for accessing mqtt
    """

    def __init__(self, client_id, config, wait=True, manager=None):
        """
        initialize mqtt client
        :param client_id: client id
        :param config: keeper configuration
        :param wait: whether to wait for connection
        """

        user = config.get("mqtt.user")
        pwd = config.get("mqtt.pass")
        client = Client(client_id=client_id)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.disable_logger()
        if user and pwd:
            client.username_pw_set(user, pwd)

        client.connect_async(config["mqtt.broker"], config["mqtt.port"], 30)
        self.client = client
        self.connected = False
        if manager:
            manager.set_mqtt(self)

        self.manager = manager
        self.wait = wait
        self.logger = Logger()

    def __enter__(self):
        """
        create initial connection when entering context
        :return: MqttClient object
        """

        self.reconnect()

        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        """
        disconnects client when exiting context
        :param type:
        :param value:
        :param traceback:
        """

        try:
            self.client.disconnect()
        except Exception:
            pass

        self.client = None

    # noinspection PyProtectedMember
    def _on_disconnect(self, client, userdata, rc):
        """
        base on disconnect behaviour, can be extended wih custom
        methods from implementation
        :param client: mqtt client
        :param userdata: userdata dict
        :param rc: rc code
        """

        self.logger.info("disconnected from %s:%s" % (client._host, client._port))
        self.connected = False
        # call custom on disconnect methods if any defined
        manager = self.manager
        if manager and manager.on_disconnect:
            manager.on_disconnect(client, userdata, rc)

    # noinspection PyProtectedMember
    def _on_connect(self, client, userdata, flags, rc):
        """
        base on connect behaviour, can be extended wih custom
        methods from implementation
        :param client: mqtt client
        :param userdata: userdata dict
        :param flags: flags
        :param rc: rc code
        """

        self.logger.info("connected to %s:%s" % (client._host, client._port))
        self.connected = rc == 0
        # call custom on connect methods if any defined
        manager = self.manager
        if manager and manager.on_connect:
            manager.on_connect(client, userdata, flags, rc)

    def _on_message(self, client, userdata, message):
        """
        base on message behaviour, can be extended wih custom
        methods from implementation
        :param client: mqtt client
        :param userdata: userdata dict
        :param message: message received
        """

        # call custom on message methods if any defined
        manager = self.manager
        if manager and manager.on_message:
            manager.on_message(client, userdata, message)

    def connection_status(self):
        """
        Returns a connection status code.
        :return: connection status code. 0 is not connected, 1 is
        waiting for connection and 2 for connected
        """

        try:
            if self.client.loop() > 0:
                return 0

            if not self.connected:
                return 1

            return 2
        except Exception:
            return 0

    def wait_connection(self, timeout=-1):
        """
        blocks waiting for connection
        """

        connection_status = self.connection_status
        reconnect = self.client.reconnect
        status = connection_status()
        now = datetime.now
        limit = now() + timedelta(seconds=timeout)
        while status != 2 and (timeout == -1 or now() <= limit):
            # reconnects when not connected, status 0
            # status 1 should only wait for connection
            # instead of reconnecting
            if status == 0:
                try:
                    reconnect()
                except:
                    pass

            sleep(1)
            status = connection_status()

    # noinspection PyProtectedMember
    def reconnect(self, wait=True):
        """
        reconnects to mqtt client
        :param wait: whether we should wait for connection
        :return: connection status
        """

        client = self.client
        self.logger.info("connecting to %s:%s" % (client._host, client._port))
        connection_status = self.connection_status
        reconnect = client.reconnect
        status = connection_status()
        while status != 2:
            try:
                if status == 0:
                    try:
                        reconnect()
                    except:
                        pass

                status = connection_status()
                manager = self.manager
                if status == 0 and manager and manager.on_not_connect:
                    manager.on_not_connect()

                if not wait:
                    break
            except Exception:
                pass

            sleep(1)

        return status

    def register(self, metric, name, icon):
        """
        register a new metric using mqtt discovery
        :param metric: metric identification
        :param name: metric name
        :param icon: metric icon
        """

        try:
            self.client.publish(CONFIG_TOPIC % metric, CONFIG_PAYLOAD % (name, metric, icon), 1, True)
        except:
            pass

    def publish_state(self, metric, state):
        """
        publish state to mqtt
        :param metric: metric identification
        :param state: state value
        """

        try:
            self.client.publish(STATE_TOPIC % metric, state, 1, True)
        except:
            pass

    def loop(self):
        """
        calls mqtt client loop
        """
        self.client.loop()
