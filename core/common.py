import sys
from os import devnull
from os.path import join
from subprocess import call

from yaml import load

from core import constants, logger


def load_config():
    with open(join(constants.KEEPER_HOME, "config", "keeper-config.yaml")) as config:
        return load(config)


def exec_command(command):
    try:
        with open(devnull, "wb") as dev_null:
            code = call(command, stdout=dev_null, stderr=dev_null)

        return code == 0
    except Exception as e:
        logger.error("unable to execute command \"%s\": %s" % (" ".join(command), e))
        return False


def stop(signum=None, frame=None):
    sys.exit(0)
