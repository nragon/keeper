import sys
from os import environ, getpid
from os import devnull
from subprocess import call

from yaml import load

PID = getpid()


def load_config():
    return load(open("%s/config/keeper-config.yaml" % environ["KEEPER_HOME"]))


def exec_command(command):
    try:
        with open(devnull, "wb") as dev_null:
            code = call(command, stdout=dev_null, stderr=dev_null)

        return code == 0
    except:
        return False


def stop(signum=None, frame=None):
    sys.exit(0)
