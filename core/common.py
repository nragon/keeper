import sys
from os import environ, getpid
from os import devnull
from os.path import join
from subprocess import call

from yaml import load

KEEPER_HOME = environ["KEEPER_HOME"]
STATUS_RUNNING = "Running"
STATUS_NOT_RUNNING = "Not Running"

def load_config():
    with open(join(KEEPER_HOME, "config", "keeper-config.yaml")) as config:
        return load(config)


def exec_command(command):
    try:
        with open(devnull, "wb") as dev_null:
            code = call(command, stdout=dev_null, stderr=dev_null)

        return code == 0
    except:
        return False


def stop(signum=None, frame=None):
    sys.exit(0)
