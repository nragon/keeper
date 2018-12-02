from importlib import import_module
from json import dumps
from multiprocessing import Process
from os import kill, getpid
from setproctitle import setproctitle
from threading import Event
from time import sleep

from core import logger, constants, common
from core.mqtt import MqttClient
from core.storage import Storage

PROCESSES = [
    "heartbeater",
    "connector",
    "reporter"
]
MODULES = {
    "heartbeater": "runtime.heartbeater",
    "connector": "runtime.connector",
    "reporter": "runtime.reporter"
}
running_processes = {}
running = False
wait_loop = Event()


def launcher(process, name):
    try:
        mod = import_module(process)
        setproctitle("keeper:" + name)
        mod.main()
    except Exception as e:
        logger.warning("process %s[%s] failed to launch %s" % (name, process, e))
        pass


def start_process(name):
    attempts = 0
    module = MODULES[name]
    while 1:
        try:
            logger.info("launching process %s[module=%s]" % (name, module))
            process = Process(name=name, target=launcher, args=(module, name))
            process.start()
            logger.info("launched process %s[pid=%s]" % (name, process.pid))

            return process
        except Exception as e:
            if attempts >= 3:
                logger.error("max of 3 launching attempts was reached when  launching process %s[module=%s]: %s" % (
                    name, module, e))
                raise

            logger.warning("error launching process %s[module=%s]: %s" % (name, module, e))
            attempts += 1
            logger.warning("reattempting launch of %s (%s of 3)" % (name, attempts))


def close_process(name, process):
    try:
        logger.info("stopping %s[pid=%s]" % (name, process.pid))
        process.terminate()
        process.join(3)
        if process.exitcode is None:
            logger.info("stopping %s[pid=%s] with SIGKILL" % (name, process.pid))
            kill(process.pid, 9)
    except Exception:
        try:
            logger.info("stopping %s[pid=%s] with SIGKILL" % (name, process.pid))
            kill(process.pid, 9)
        except Exception:
            logger.info("unable to stop %s[pid=%s]" % (name, process.pid))


def wait_children():
    while 1:
        finished = True
        for name, process in running_processes.items():
            if process.exitcode is None:
                finished = False

        sleep(1)
        if finished:
            return


def is_running(process):
    try:
        if process.exitcode is not None:
            return 0

        kill(process.pid, 0)

        return 1
    except Exception:
        return 0


def start():
    pid = getpid()
    logger.init("manager")
    logger.info("starting manager[pid=%s]" % pid)
    with Storage() as storage:
        for name in PROCESSES:
            metric = "%sStatus" % name
            storage.put(metric, "Launching")
            running_processes[name] = start_process(name)
            storage.put(metric, "Launched")

        try:
            loop(storage)
        finally:
            logger.info("waiting for all processes to finish")
            wait_children()
            logger.info("stopping manager[pid=%s]" % pid)
            try:
                for name in PROCESSES:
                    metric = "%sStatus" % name
                    storage.put_no_lock(metric, constants.STATUS_NOT_RUNNING)

                result = storage.get_all()
                if result:
                    report = {}
                    for record in result:
                        report[record[0]] = record[1]

                    mqtt_client = MqttClient("keepermanager", common.load_config())
                    mqtt_client.connect()
                    mqtt_client.publish(constants.REPORTER_TOPIC, dumps(report))
            except Exception:
                pass


def loop(storage):
    put = storage.put
    global running
    running = True
    wait_loop.wait(30)
    while running:
        for name in PROCESSES:
            metric = "%sStatus" % name
            process = running_processes.get(name)
            if process and is_running(process):
                put(metric, constants.STATUS_RUNNING)
                continue

            put(metric, constants.STATUS_NOT_RUNNING)
            logger.info("process %s is not running" % name)
            if process:
                close_process(name, process)

            put(metric, "Launching")
            process = start_process(name)
            put(metric, "Launched")
            running_processes[name] = process

        wait_loop.wait(30)


def handle_signal(signum=None, frame=None):
    global running
    running = False
    wait_loop.set()
