# -*- coding: utf-8 -*-
"""
    Test connector
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from datetime import datetime, timedelta
from os import environ, getcwd, mkdir
from os.path import join
from shutil import rmtree, copy
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "connector")
from kio import Storage
from network import MqttClient
from runtime.connector import Connector

from core import common, constants


class TestConnector(TestCase):
    def setUp(self):
        mkdir(environ["KEEPER_HOME"])
        config_path = join(environ["KEEPER_HOME"], "config")
        mkdir(config_path)
        copy(join(environ["KEEPER_HOME"], "..", "..", "config", "keeper.json"), config_path)

    def tearDown(self):
        rmtree(environ["KEEPER_HOME"])

    def test_on_not_connected(self):
        config = common.load_config()
        with Storage() as storage, MqttClient("keeperconnectortest", config) as mc, Connector(config, storage,
                                                                                              mc) as connector:
            connector.on_not_connect()
            self.assertEqual(connector.attempts, 1)
            self.assertEqual(storage.get_int(constants.CONNECTOR_FAILED_CONNECTIONS), 1)
            self.assertEqual(storage.get_int(constants.CONNECTOR_MQTT_RESTARTS), 0)
            connector.on_not_connect()
            self.assertEqual(connector.attempts, 2)
            self.assertEqual(storage.get_int(constants.CONNECTOR_FAILED_CONNECTIONS), 2)
            self.assertEqual(storage.get_int(constants.CONNECTOR_MQTT_RESTARTS), 0)
            connector.on_not_connect()
            self.assertEqual(connector.attempts, 3)
            self.assertEqual(storage.get_int(constants.CONNECTOR_FAILED_CONNECTIONS), 3)
            self.assertEqual(storage.get_int(constants.CONNECTOR_MQTT_RESTARTS), 0)
            connector.on_not_connect()
            self.assertEqual(storage.get_int(constants.CONNECTOR_MQTT_RESTARTS), 1)
            self.assertEqual(connector.attempts, 0)
            connector.on_not_connect()
            self.assertEqual(connector.attempts, 1)
            self.assertEqual(storage.get_int(constants.CONNECTOR_FAILED_CONNECTIONS), 4)
            self.assertEqual(storage.get_int(constants.CONNECTOR_MQTT_RESTARTS), 1)

    def test_stable(self):
        config = common.load_config()
        with Storage() as storage, MqttClient("keeperconnectortest", config) as mc, Connector(config, storage,
                                                                                              mc) as connector:
            now = datetime.now()
            connector.started_at = now - timedelta(seconds=10)
            connector.connected_at = now - timedelta(seconds=9)
            self.assertTrue(connector.is_stable())

    def test_not_stable(self):
        config = common.load_config()
        with Storage() as storage, MqttClient("keeperconnectortest", config) as mc, Connector(config, storage,
                                                                                              mc) as connector:
            now = datetime.now()
            connector.started_at = now - timedelta(seconds=10)
            connector.connected_at = now - timedelta(seconds=8)
            self.assertFalse(connector.is_stable())
