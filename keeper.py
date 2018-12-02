import sys
from signal import signal, SIGTERM

from core import manager, common


def main():
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
    sys.exit(0)
