from signal import signal, SIGTERM

from core import manager, common


def main():
    signal(SIGTERM, common.stop)
    try:
        manager.start()
    except KeyboardInterrupt:
        pass
    except Exception:
        from traceback import print_exc
        print_exc()
    finally:
        manager.close()


if __name__ == "__main__":
    main()
