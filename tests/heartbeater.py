from datetime import datetime, timedelta
from os import environ, getcwd, mkdir
from os.path import join
from shutil import rmtree, copy
from unittest import TestCase

environ["KEEPER_HOME"] = join(getcwd(), "heartbeater")
from runtime.heartbeater import Heartbeater
from kio import Storage, MqttClient
from core import common, constants


class TestHeartbeater(TestCase):
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
                with Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest", config,
                                                                             False, manager=heartbeater):
                    pass
            except Exception as e:
                pass

    def test_connected(self):
        config = common.load_config()
        with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest",
                                                                                           config,
                                                                                           manager=heartbeater) as mqtt_client:
            self.assertEqual(mqtt_client.connection_status(), 2)

    def test_monitor_in_time_no_delay(self):
        config = common.load_config()
        with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest",
                                                                                           config,
                                                                                           manager=heartbeater):
            heartbeater.last_message = datetime.now() - timedelta(seconds=config["heartbeat.interval"])
            heartbeater.monitor()
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 0)

    def test_monitor_in_time_delay(self):
        config = common.load_config()
        with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest",
                                                                                           config,
                                                                                           manager=heartbeater):
            heartbeater.last_message = datetime.now() - timedelta(
                seconds=config["heartbeat.interval"] + config["heartbeat.delay"])
            heartbeater.monitor()
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 0)

    def test_monitor_not_in_time(self):
        config = common.load_config()
        with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest",
                                                                                           config,
                                                                                           manager=heartbeater):
            heartbeater.last_message = datetime.now() - timedelta(
                seconds=config["heartbeat.interval"] + config["heartbeat.delay"] + 1)
            heartbeater.monitor()
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 1)

    def test_monitor_restart_ha(self):
        config = common.load_config()
        with Storage() as storage, Heartbeater(config, storage) as heartbeater, MqttClient("keeperconnectortest",
                                                                                           config,
                                                                                           manager=heartbeater):
            diff = config["heartbeat.interval"] + config["heartbeat.delay"] + 1
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 1)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 1)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 0)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 2)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 2)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 0)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 3)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 3)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 0)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 0)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 3)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 1)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 1)
            self.assertEqual(heartbeater.attempts, 1)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 4)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 1)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 2)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 5)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 1)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 3)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 6)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 1)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 0)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 6)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 2)
            heartbeater.last_message = datetime.now() - timedelta(seconds=diff)
            heartbeater.monitor()
            self.assertEqual(heartbeater.misses, 1)
            self.assertEqual(heartbeater.attempts, 2)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_MISSED_HEARTBEAT), 7)
            self.assertEqual(storage.get_int(constants.HEARTBEATER_HA_RESTARTS), 2)
