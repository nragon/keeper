from signal import signal, SIGTERM, SIGINT
from time import sleep

import paho.mqtt.client as mqtt

from core import common, logger

stopping = False


def start():
    logger.info("starting connector manager[pid=%s]" % common.PID)
    client = None
    config = common.load_config()
    broker = config["mqtt.broker"]
    port = config["mqtt.port"]
    user = config.get("mqtt.user")
    pwd = config.get("mqtt.pass")
    command = config["mqtt.command"].split(" ")
    del config
    try:
        client = connect(broker, port, user, pwd, command)
        while not stopping:
            if client.loop() > 0 and not stopping:
                client = connect(broker, port, user, pwd, command)
            else:
                sleep(1)
    finally:
        logger.info("connector[pid=%s] is stopping" % common.PID)
        try:
            client.close()
        except:
            pass

        logger.info("connector[pid=%s] stopped" % common.PID)


def connect(broker, port, user, pwd, command):
    attempts = 0
    while not stopping:
        try:
            logger.info("checking connection to %s:%s" % (broker, port))
            client = mqtt.Client(client_id="keeper_connector")
            if user and pwd:
                client.username_pw_set(user, pwd)

            client.connect(broker, port, 30)
            if client.loop() == 0:
                logger.info("connection to %s:%s is ok" % (broker, port))
                return client
        except:
            if attempts >= 3:
                logger.warning("max of 3 connection attempts was reached")
                logger.warning("restarting mqtt service")
                if common.exec_command(command):
                    sleep(30)
                else:
                    logger.error("unable to restart mqtt service with command %s" % command)

                attempts = 0
            else:
                attempts += 1
                logger.warning("broker is not responding (%s of 3)" % attempts)
                logger.warning("retrying in 5 seconds")
                sleep(5)


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
