# -*- coding: utf-8 -*-
"""
    Provides base logging functions
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""
from logging import getLevelName, INFO, WARN, ERROR, DEBUG
from multiprocessing import current_process
from time import strftime

from core.common import load_config
from core.constants import TIME_FORMAT


class Logger(object):
    """
    logger class that prints to stdout
    """

    def __init__(self):
        """
        partially initializes format
        """

        self.format = "%s " + current_process().name + "-keeper[%s]: %s"
        self.debug = bool(load_config()["debug"])

    def info(self, message):
        """
        prints an info message
        :param message: message
        """

        self._log(INFO, message)

    def warning(self, message):
        """
        prints a warning message
        :param message: message
        """

        self._log(WARN, message)

    def error(self, message):
        """
        prints an error message
        :param message: message
        """

        self._log(ERROR, message)

    def log(self, level, message, *args):
        """
        prints an message with args
        :param level: log level
        :param message: message
        :param args: arguments
        """

        if level != DEBUG or self.debug:
            self._log(level, message % args)

    def _log(self, level, message):
        """
        prints a message
        :param level: log level
        :param message: message
        """

        print(self.format % (strftime(TIME_FORMAT), getLevelName(level), message))
