from os import environ, getcwd, mkdir
from os.path import join
from shutil import rmtree, copy
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "reporter")
from runtime.reporter import Reporter

from core.storage import Storage
from core.mqtt import MqttClient

from core import common


class TestReporter(TestCase):
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
        mqtt_client = MqttClient("keeperheartbeatertest", config)
        with Storage() as storage:
            reporter = Reporter(storage, mqtt_client)
            reporter.connect(wait=False)
            self.assertEqual(mqtt_client.connection_status(), 0)

    def test_connected(self):
        config = common.load_config()
        mqtt_client = MqttClient("keeperheartbeatertest", config)
        with Storage() as storage:
            reporter = Reporter(storage, mqtt_client)
            reporter.connect()
            self.assertEqual(mqtt_client.connection_status(), 2)
