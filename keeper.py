from sys import exit
from signal import signal, SIGTERM

from runtime import manager


def main():
    """
    main
    """

    signal(SIGTERM, manager.handle_signal)
    try:
        manager.start()
    except KeyboardInterrupt:
        pass
    except Exception:
        from traceback import print_exc
        print_exc()


if __name__ == "__main__":
    main()
    exit(0)
