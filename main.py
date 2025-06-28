import sys

from aiocometd_mock.cli import parse_args
from aiocometd_mock.server import run


def main() -> int:
    """
    The main entry point for the application.
    It parses command-line arguments and starts the server.
    """
    args = parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
