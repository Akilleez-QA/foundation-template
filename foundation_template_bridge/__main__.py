import sys

sys.dont_write_bytecode = True


def run():
    from .server import main
    return main()


raise SystemExit(run())
