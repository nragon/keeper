from importlib import import_module
from multiprocessing import Process
from os import kill
from time import sleep
from setproctitle import setproctitle

from core import logger, common

PROCESSES = [
    "heartbeater",
    "connector"
]
MODULES = {
    "heartbeater": "runtime.heartbeater",
    "connector": "runtime.connector"
}
running = {}


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
    except:
        try:
            logger.info("stopping process %s[pid=%s] with SIGKILL" % (name, process.pid))
            kill(process.pid, 9)
        except:
            logger.info("unable to stop process %s[pid=%s]" % (name, process.pid))


def is_running(process):
    try:
        if process.exitcode is not None:
            return 0

        kill(process.pid, 0)

        return 1
    except:
        return 0


def start():
    logger.info("starting manager[pid=%s]" % common.PID)
    for name in PROCESSES:
        running[name] = start_process(name)

    try:
        sleep(30)
        while 1:
            for name in PROCESSES:
                process = running.get(name)
                if process and is_running(process):
                    continue

                logger.info("process %s is not running" % name)
                if process:
                    close_process(name, process)

                process = start_process(name)
                running[name] = process

            sleep(30)
    finally:
        logger.info("manager[pid=%s] is stopping" % common.PID)


def close():
    logger.info("stopping all processes")
    for name, process in running.items():
        close_process(name, process)

    logger.info("manager[pid=%s] stopped" % common.PID)
