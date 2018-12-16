# -*- coding: utf-8 -*-
"""
    Provides base logging functions
    :copyright: © 2018 by Nuno Gonçalves
    :license: MIT, see LICENSE for more details.
"""

from multiprocessing import current_process
from time import strftime

from core.constants import INFO, WARN, ERROR, TIME_FORMAT


class Logger(object):
    """
    logger class that prints to stdout
    """

    def __init__(self):
        """
        partially initializes format
        """
        self.format = "%s " + current_process().name + "-keeper[%s]: %s"

    def info(self, message):
        """
        prints an info message
        :param message: message
        """

        self.log(INFO, message)

    def warning(self, message):
        """
        prints a warning message
        :param message: message
        """

        self.log(WARN, message)

    def error(self, message):
        """
        prints an error message
        :param message: message
        """

        self.log(ERROR, message)

    def log(self, level, message):
        """
        prints a message
        :param level: log level
        :param message: message
        """

        print(self.format % (strftime(TIME_FORMAT), level, message))
