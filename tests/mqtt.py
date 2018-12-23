# -*- coding: utf-8 -*-
"""
    Test mqtt
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from os import environ, getcwd, mkdir
from os.path import join

environ["KEEPER_HOME"] = join(getcwd(), "mqtt")
from shutil import rmtree, copy
from unittest import TestCase
from network import MqttClient

from core import common


class TestMqtt(TestCase):
    def setUp(self):
        mkdir(environ["KEEPER_HOME"])
        config_path = join(environ["KEEPER_HOME"], "config")
        mkdir(config_path)
        copy(join(environ["KEEPER_HOME"], "..", "..", "config", "keeper-config.yaml"), config_path)

    def tearDown(self):
        rmtree(environ["KEEPER_HOME"])

    def test_connected(self):
        config = common.load_config()
        with MqttClient("keepermqtttest", config) as mqtt_client:
            self.assertEqual(mqtt_client.connection_status(), 2)

    def test_not_connected(self):
        config = common.load_config()
        config["mqtt.broker"] = "1.1.1.1"
        try:
            with MqttClient("keepermqtttest", config, False):
                pass
        except:
            pass

    def test_wait(self):
        config = common.load_config()
        with MqttClient("keepermqtttest", config) as mqtt_client:
            mqtt_client.wait_connection()
            self.assertEqual(mqtt_client.connection_status(), 2)

    def test_is_connected(self):
        config = common.load_config()
        with MqttClient("keepermqtttest", config) as mqtt_client:
            self.assertEqual(mqtt_client.connection_status(), 2)

        self.assertEqual(mqtt_client.connection_status(), 0)
