from os import environ, getcwd, mkdir
from os.path import join
from shutil import rmtree, copy
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "connector")
from kio import Storage, MqttClient
from runtime.connector import Connector

from core import common, constants, CONNECTOR_CONNECTION_STATUS, CONNECTOR_CONNECTION_NOK


class TestConnector(TestCase):
    def setUp(self):
        mkdir(environ["KEEPER_HOME"])
        config_path = join(environ["KEEPER_HOME"], "config")
        mkdir(config_path)
        copy(join(environ["KEEPER_HOME"], "..", "..", "config", "keeper-config.yaml"), config_path)

    def tearDown(self):
        rmtree(environ["KEEPER_HOME"])

    def test_not_connected(self):
        config = common.load_config()
        config["mqtt.broker"] = "1.1.1.1"
        with Storage() as storage:
            try:
                with Connector(config, storage) as connector, MqttClient("keeperconnectortest", config, manager=connector):
                    pass
            except Exception as e:
                pass

            self.assertEqual(storage.get(CONNECTOR_CONNECTION_STATUS), CONNECTOR_CONNECTION_NOK)

    def test_connected(self):
        config = common.load_config()
        with Storage() as storage, Connector(config, storage) as connector, MqttClient("keeperconnectortest", config,
                                                                                       manager=connector) as mqtt_client:
            self.assertEqual(mqtt_client.connection_status(), 2)
            self.assertEqual(storage.get(constants.CONNECTOR_CONNECTION_STATUS),
                             constants.CONNECTOR_CONNECTION_OK)

    def test_on_not_connected(self):
        config = common.load_config()
        with Storage() as storage, Connector(config, storage) as connector, MqttClient("keeperconnectortest", config,
                                                                                       manager=connector) as mqtt_client:
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
