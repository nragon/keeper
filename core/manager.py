from importlib import import_module
from multiprocessing import Process
from os import kill, getpid
from time import sleep
from setproctitle import setproctitle

from core import logger
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
running = {}
PID = getpid()


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
        logger.info("stopping process %s[pid=%s]" % (name, process.pid))
        process.terminate()
        process.join(3)
        if process.exitcode is None:
            logger.info("stopping process %s[pid=%s] with SIGKILL" % (name, process.pid))
            kill(process.pid, 9)
    except Exception:
        try:
            logger.info("stopping process %s[pid=%s] with SIGKILL" % (name, process.pid))
            kill(process.pid, 9)
        except Exception:
            logger.info("unable to stop process %s[pid=%s]" % (name, process.pid))


def is_running(process):
    try:
        if process.exitcode is not None:
            return 0

        kill(process.pid, 0)

        return 1
    except Exception:
        return 0


def start():
    logger.init()
    logger.info("starting manager[pid=%s]" % PID)
    with Storage() as storage:
        for name in PROCESSES:
            metric = "%sStatus" % name
            storage.put(metric, "Launching")
            running[name] = start_process(name)
            storage.put(metric, "Launched")

        try:
            loop(storage)
        finally:
            logger.info("manager[pid=%s] is stopping" % PID)


def loop(storage):
    put = storage.put
    sleep(30)
    while 1:
        for name in PROCESSES:
            metric = "%s.status" % name
            process = running.get(name)
            if process and is_running(process):
                put(metric, "Running")
                continue

            put(metric, "Not Running")
            logger.info("process %s is not running" % name)
            if process:
                close_process(name, process)

            put(metric, "Launching")
            process = start_process(name)
            put(metric, "Launched")
            running[name] = process

        sleep(30)


def close():
    logger.info("stopping all processes")
    for name, process in running.items():
        close_process(name, process)

    logger.info("manager[pid=%s] stopped" % PID)
