from os import getpid
from signal import signal, SIGTERM, SIGINT
from time import sleep
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from core import common, logger

PID = getpid()
last_message = None
stopping = False


def start():
    logger.info("starting heartbeater[pid=%s]" % PID)
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config["mqtt.user"]
    pwd = config["mqtt.pass"]
    command = config["restart.command"].split(" ")
    topic = config["heartbeat.topic"]
    interval = config["heartbeat.interval"]
    delay = config["heartbeat.delay"]
    restart_delay = config["heartbeat.restart.delay"]
    del config
    now = datetime.now
    global last_message
    last_message = now() + timedelta(seconds=restart_delay)
    attempts = 0
    misses = 0
    last_known_message = last_message
    client = None
    try:
        client = connect(broker, port, user, pwd, topic)
        while not stopping:
            if client.loop() > 0 and not stopping:
                client = connect(broker, port, user, pwd, topic)
            else:
                current = now()
                diff = (current - last_message).total_seconds()
                if diff > interval + delay:
                    logger.warning("heartbeat threshold reached")
                    if misses < 3:
                        misses += 1
                        last_message += timedelta(seconds=interval)
                        logger.info("tolerating missed heartbeat (%s of 3)" % misses)
                    elif attempts < 3:
                        attempts += 1
                        misses = 0
                        logger.warning("max of misses reached")
                        logger.info("restarting ha service (%s of 3) with command %s" % (attempts, command))
                        common.exec_command(command)
                        logger.info("waiting %s seconds for ha service to start" % restart_delay)
                        last_message = now() + timedelta(seconds=restart_delay)
                    else:
                        logger.warning("heartbeat still failing after 3 restarts")
                        logger.info("rebooting")
                        common.exec_command(["sudo", "reboot", "-f"])

                    last_known_message = last_message

                if last_known_message != last_message:
                    misses = 0
                    attempts = 0

                sleep(1)
    finally:
        logger.info("heartbeater[pid=%s] is stopping" % PID)
        try:
            client.close()
        except:
            pass

        logger.info("heartbeater[pid=%s] stopped" % PID)


def connect(broker, port, user, pwd, topic):
    while 1:
        try:
            logger.info("connecting to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="keeper_heartbeater",
                                 userdata={"topic": topic, "broker": broker, "port": port})
            client.on_connect = on_connect
            client.on_message = on_message
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


def stop(signum=None, frame=None):
    global stopping
    stopping = True
    common.stop()


def main():
    signal(SIGTERM, stop)
    signal(SIGINT, stop)
    try:
        start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error occurred during connector execution: %s" % e)
