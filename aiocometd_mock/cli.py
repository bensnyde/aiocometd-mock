import argparse
from typing import List, Optional


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="aiocometd-mock server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--connect-interval", type=int, default=0, help="Connect interval returned by server")
    parser.add_argument("--connect-timeout", type=int, default=45000, help="Connect timeout returned by server")
    parser.add_argument(
        "--reconnection-interval", type=int, default=5, help="Advise reconnect after a certain number of connections"
    )
    parser.add_argument(
        "--expire-client-ids-after",
        type=int,
        default=None,
        help="Expire clientIds after a certain number of connections",
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Disable CometD request validation",
    )
    parser.add_argument("--debug", default=False, action="store_true", help="Debug mode")
    return parser.parse_args(args)
