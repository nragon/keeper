from multiprocessing import current_process

from time import strftime

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"


def info(message):
    log(INFO, message)


def warning(message):
    log(WARN, message)


def error(message):
    log(ERROR, message)


def log(level, message):
    print("%s %s-keeper[%s]: %s" % (strftime(TIME_FORMAT), current_process().name, level, message))
