from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from core import common, logger, storage

HEARTBEATER_STATUS = "heartbeaterStatus"
HEARTBEATER_MISSED_HEARTBEAT = "heartbeaterMissedHeartbeat"
HEARTBEATER_HA_RESTARTS = "heartbeaterHARestarts"
HEARTBEATER_SYSTEM_RESTARTS = "heartbeaterSystemRestarts"
PID = getpid()
last_message = None
running = False


def start():
    logger.info("starting heartbeater[pid=%s]" % PID)
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config.get("mqtt.user")
    pwd = config.get("mqtt.pass")
    command = config["restart.command"].split(" ")
    topic = config["heartbeat.topic"]
    interval = config["heartbeat.interval"]
    delay = config["heartbeat.delay"]
    restart_delay = config["heartbeat.restart.delay"]
    del config
    with storage.get_connection() as conn:
        storage.put(conn, HEARTBEATER_STATUS, common.STATUS_RUNNING)
        try:
            loop(conn, broker, port, user, pwd, topic, interval, delay, restart_delay, command)
        finally:
            storage.put(conn, HEARTBEATER_STATUS, common.STATUS_NOT_RUNNING)
            logger.info("heartbeater[pid=%s] is stopping" % PID)


def loop(conn, broker, port, user, pwd, topic, interval, delay, restart_delay, command):
    inc = storage.inc
    get_int = storage.get_int
    missed_heartbeats = get_int(conn, HEARTBEATER_MISSED_HEARTBEAT)
    if not missed_heartbeats:
        missed_heartbeats = 0

    ha_restarts = get_int(conn, HEARTBEATER_HA_RESTARTS)
    if not ha_restarts:
        ha_restarts = 0

    system_restarts = get_int(conn, HEARTBEATER_SYSTEM_RESTARTS)
    if not system_restarts:
        system_restarts = 0

    attempts = 0
    misses = 0
    now = datetime.now
    global last_message
    last_message = now() + timedelta(seconds=restart_delay)
    last_known_message = last_message
    client = connect(broker, port, user, pwd, topic)
    global running
    running = True
    while running:
        if client.loop() > 0 and running:
            client = connect(broker, port, user, pwd, topic)
        else:
            current = now()
            diff = (current - last_message).total_seconds()
            if diff > interval + delay:
                logger.warning("heartbeat threshold reached")
                if misses < 3:
                    misses += 1
                    last_message += timedelta(seconds=interval)
                    missed_heartbeats = inc(conn, HEARTBEATER_MISSED_HEARTBEAT, missed_heartbeats)
                    logger.info("tolerating missed heartbeat (%s of 3)" % misses)
                elif attempts < 3:
                    attempts += 1
                    misses = 0
                    logger.warning("max of misses reached")
                    logger.info("restarting ha service (%s of 3) with command %s" % (attempts, command))
                    if common.exec_command(command):
                        ha_restarts = inc(conn, HEARTBEATER_HA_RESTARTS, ha_restarts)
                        logger.info("waiting %s seconds for ha service to start" % restart_delay)
                        last_message = now() + timedelta(seconds=restart_delay)
                else:
                    logger.warning("heartbeat still failing after 3 restarts")
                    logger.info("rebooting")
                    system_restarts = inc(conn, HEARTBEATER_SYSTEM_RESTARTS, system_restarts)
                    common.exec_command(["sudo", "reboot", "-f"])

                last_known_message = last_message

            if last_known_message != last_message:
                misses = 0
                attempts = 0

            sleep(1)


def connect(broker, port, user, pwd, topic):
    while 1:
        try:
            logger.info("connecting to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="keeper_heartbeater",
                                 userdata={"topic": topic, "broker": broker, "port": port})
            client.on_connect = on_connect
            client.on_message = on_message
            if user and pwd:
                client.username_pw_set(user, pwd)

            client.connect(broker, port, 60)
            logger.info("listening for heartbeat messages")

            return client
        except:
            logger.warning("unable to connect %s:%s" % (broker, port))
            logger.warning("retrying in 10 seconds")
            sleep(10)


def on_connect(client, userdata, flags, rc):
    logger.info("connected to %s:%s" % (userdata["broker"], userdata["port"]))
    client.subscribe(userdata["topic"])


def on_message(client, userdata, msg):
    global last_message
    last_message = datetime.now()


def stop():
    global running
    running = False


def handle_signal(signum=None, frame=None):
    stop()
    common.stop()


def main():
    signal(SIGTERM, handle_signal)
    signal(SIGINT, handle_signal)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during connector execution: %s" % e)
