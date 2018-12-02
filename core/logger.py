from multiprocessing import current_process

from time import strftime

from core import constants

PROCESS_NAME = None


def init(process_name=None):
    global PROCESS_NAME
    PROCESS_NAME = process_name if process_name else current_process().name


def info(message):
    log(constants.INFO, message)


def warning(message):
    log(constants.WARN, message)


def error(message):
    log(constants.ERROR, message)


def log(level, message):
    print("%s %s-keeper[%s]: %s" % (strftime(constants.TIME_FORMAT), PROCESS_NAME, level, message))
