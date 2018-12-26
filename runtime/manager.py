# -*- coding: utf-8 -*-
"""
    Manager that launches runtime processes and monitors
    their execution
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from importlib import import_module
from multiprocessing import Process
from os import kill, getpid
from setproctitle import setproctitle
from threading import Event
from time import sleep

from core import Logger, STATUS_RUNNING, STATUS_NOT_RUNNING
from kio import Storage

running = False
wait_loop = Event()
MODULES = {
    "heartbeater": "runtime.heartbeater",
    "connector": "runtime.connector"
}


class Manager(object):
    """
    Manager responsible for deploying other managers
    """

    def __init__(self, storage):
        """
        initializes manager
        """

        self.running_processes = {}
        self.put = storage.put
        self.logger = Logger()

    def __enter__(self):
        """
        launches initial processes when entering context
        :return: Manager object
        """

        self.logger.info("starting manager[pid=%s]" % getpid())
        put = self.put
        for process in MODULES.items():
            name, module = process
            metric = "%sStatus" % name
            put(metric, "Launching")
            self.running_processes[name] = self.start_process(name, module)
            put(metric, "Launched")

        return self

    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback):
        """
        waits for all processes when exiting context
        :param type:
        :param value:
        :param traceback:
        """

        self.logger.info("stopping manager[pid=%s]" % getpid())
        running_processes = self.running_processes.items()
        while 1:
            finished = True
            for name, process in running_processes:
                if process.exitcode is None:
                    finished = False
                    break

            sleep(1)
            if finished:
                return

    def launcher(self, process, name):
        """
        used by process to start a new manager by
        calling its main methods
        :param process: process implementation
        :param name: process name
        """

        try:
            mod = import_module(process)
            setproctitle("keeper:" + name)
            mod.main()
        except Exception as ex:
            self.logger.warning("process %s[%s] failed: %s" % (name, process, ex))
            pass

    def start_process(self, name, module):
        """
        start a new process with a manager
        this will retry 3 times until it fails
        :param name: manager name
        :param module: manager module
        :return: process where manager is running
        """

        attempts = 0
        while 1:
            try:
                self.logger.info("launching process %s[module=%s]" % (name, module))
                process = Process(name=name, target=self.launcher, args=(module, name))
                process.start()
                self.logger.info("launched process %s[pid=%s]" % (name, process.pid))

                return process
            except Exception as ex:
                if attempts >= 3:
                    self.logger.error(
                        "max of 3 launching attempts was reached when  launching process %s[module=%s]: %s" % (
                            name, module, ex))
                    raise ex

                self.logger.warning("error launching process %s[module=%s]: %s" % (name, module, ex))
                attempts += 1
                self.logger.warning("reattempting launch of %s (%s of 3)" % (name, attempts))

    def close_process(self, name, process):
        """
        close a process. uses kill signal when process
        fails to end peacefully
        :param name: process name
        :param process: process
        """

        try:
            self.logger.info("stopping %s[pid=%s]" % (name, process.pid))
            process.terminate()
            process.join(3)
            if process.exitcode is None:
                self.logger.info("stopping %s[pid=%s] with SIGKILL" % (name, process.pid))
                kill(process.pid, 9)
        except Exception:
            try:
                self.logger.info("stopping %s[pid=%s] with SIGKILL" % (name, process.pid))
                kill(process.pid, 9)
            except Exception:
                self.logger.info("unable to stop %s[pid=%s]" % (name, process.pid))

    def check_processes(self):
        """
        check if all processes are running and
        launches those who are not
        """

        put = self.put
        for process in MODULES.items():
            name, module = process
            metric = "%sStatus" % name
            process = self.running_processes.get(name)
            if process and is_running(process):
                put(metric, STATUS_RUNNING)
                continue

            put(metric, STATUS_NOT_RUNNING)
            self.logger.info("process %s is not running" % name)
            if process:
                self.close_process(name, process)

            put(metric, "Launching")
            process = self.start_process(name, module)
            put(metric, "Launched")
            self.running_processes[name] = process


def start():
    """
    starts this manager and calls it's routine
    loop which launches other managers
    """

    with Storage() as storage, Manager(storage) as manager:
        try:
            loop(manager)
        except Exception as ex:
            if running:
                raise ex


def loop(manager):
    """
    continuously check launched processes
    :param manager: manager
    """

    global running
    running = True
    while running:
        wait_loop.wait(30)
        manager.check_processes()


def is_running(process):
    """
    check whether a process is running
    :param process: process to be checked
    :return: True if running, False not running
    """

    try:
        if process.exitcode is not None:
            return False

        kill(process.pid, 0)

        return True
    except Exception:
        return False


# noinspection PyUnusedLocal
def handle_signal(signum=None, frame=None):
    """
    interrupts main loop
    :param signum:
    :param frame:
    """

    global running
    running = False
    wait_loop.set()
