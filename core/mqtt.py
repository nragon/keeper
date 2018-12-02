from time import sleep

import paho.mqtt.client as mqtt

from core import logger


class MqttClient(object):

    def __init__(self, client_id, config):
        user = config.get("mqtt.user")
        pwd = config.get("mqtt.pass")
        client = mqtt.Client(client_id=client_id)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.disable_logger()
        if user and pwd:
            client.username_pw_set(user, pwd)

        client.connect_async(config["mqtt.broker"], config["mqtt.port"], 30)
        self.client = client
        self.connected = False
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_not_connect = None

    def _on_disconnect(self, client, userdata, rc):
        logger.info("disconnected from %s:%s" % (client._host, client._port))
        self.connected = False
        on_disconnect = self.on_disconnect
        if on_disconnect:
            on_disconnect(client, userdata, rc)

    def _on_connect(self, client, userdata, flags, rc):
        logger.info("connected to %s:%s" % (client._host, client._port))
        self.connected = rc == 0
        on_connect = self.on_connect
        if on_connect:
            on_connect(client, userdata, flags, rc)

    def _on_message(self, client, userdata, message):
        on_message = self.on_message
        if on_message:
            on_message(client, userdata, message)

    def connection_status(self):
        try:
            if self.client.loop() > 0:
                return 0

            if not self.connected:
                return 1

            return 2
        except Exception:
            return 0

    def wait_connection(self):
        connection_status = self.connection_status
        reconnect = self.client.reconnect
        status = connection_status()
        while status != 2:
            if status == 0:
                try:
                    reconnect()
                except Exception:
                    pass

            sleep(1)
            status = connection_status()

    def connect(self):
        self.client.reconnect()

    def reconnect(self, wait=True):
        client = self.client
        logger.info("connecting to %s:%s" % (client._host, client._port))
        connection_status = self.connection_status
        reconnect = client.reconnect
        status = connection_status()
        while status != 2:
            try:
                if status == 0:
                    reconnect()

                status = connection_status()
            except Exception as e:
                pass

            on_not_connect = self.on_not_connect
            if status == 0 and on_not_connect:
                on_not_connect()

            if not wait:
                break

            sleep(1)

        return status

    def publish(self, topic, payload):
        self.client.publish(topic, payload, 1, True)

    def loop(self):
        self.client.loop()

    def disconnect(self):
        self.client.disconnect()
