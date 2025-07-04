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
        "--reconnection-interval-seconds",
        type=int,
        default=None,
        help="Advise reconnect after a certain number of seconds",
    )
    parser.add_argument(
        "--expire-client-ids-after",
        type=int,
        default=None,
        help="Expire clientIds after a certain number of connections",
    )
    parser.add_argument(
        "--expire-client-ids-after-seconds",
        type=int,
        default=None,
        help="Expire clientIds after a certain number of seconds",
    )
    parser.add_argument(
        "--no-validation",
        default=False,
        action="store_true",
        help="Disable CometD request validation",
    )
    parser.add_argument("--debug", default=False, action="store_true", help="Debug mode")
    parsed_args = parser.parse_args(args)

    # Automatically determine which adapters to load
    adapters_to_load = []
    if parsed_args.reconnection_interval is not None or parsed_args.reconnection_interval_seconds is not None:
        adapters_to_load.append("reconnect")
    if parsed_args.expire_client_ids_after is not None or parsed_args.expire_client_ids_after_seconds is not None:
        adapters_to_load.append("expire")
    parsed_args.adapters = adapters_to_load

    # Default validators to load
    parsed_args.validators = ["request", "client_id"] if not parsed_args.no_validation else []

    return parsed_args