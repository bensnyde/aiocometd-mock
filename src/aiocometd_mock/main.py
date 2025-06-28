import argparse
import asyncio
import logging
from typing import Any, Dict, List, Optional
from validators import validate_cometd_request
from aiohttp import web

logger: logging.Logger = logging.getLogger(__name__)


async def process_request(request: web.Request) -> web.Response:
    """Processes an incoming CometD request."""
    request_data: List[Dict[str, Any]] = await request.json()
    channel = request_data[0].get("channel")
    logger.debug("Processing request for channel: %s", channel)

    if channel == "/meta/handshake":
        return await handshake(request)
    elif channel == "/meta/connect":
        return await connect(request)
    elif channel == "/meta/subscribe":
        return await subscribe(request)
    elif channel == "/meta/unsubscribe":
        return await unsubscribe(request)
    elif channel == "/meta/disconnect":
        return await disconnect(request)
    else:
        logger.error("Unknown channel: %s", channel)


@validate_cometd_request({"id", "channel"})
async def handshake(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD handshake requests."""
    logger.debug("Handshake request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/handshake",
            "successful": True,
            "version": "1.0",
            "supportedConnectionTypes": ["long-polling"],
            "clientId": "mock-client-id",
            "advice": {"reconnect": "retry", "interval": 0, "timeout": 45000},
        }
    ]
    logger.debug("Handshake response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "id"})
async def connect(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD connect requests."""
    logger.debug("Connect request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/connect",
            "clientId": request_message.get("clientId", "mock-client-id"),
            "successful": True,
            "advice": {
                "interval": request.app.get("connection-interval"),
                "timeout": request.app.get("connection-timeout")
            },
        }
    ]
    logger.debug("Connect response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "subscription"})
async def subscribe(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD subscribe requests."""
    logger.debug("Subscribe request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/subscribe",
            "clientId": request_message.get("clientId", "mock-client-id"),
            "subscription": request_message.get("subscription", "mock-subscription"),
            "successful": True,
        }
    ]
    logger.debug("Subscribe response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "subscription"})
async def unsubscribe(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD unsubscribe requests."""
    logger.debug("Unsubscribe request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/unsubscribe",
            "clientId": request_message.get("clientId", "mock-client-id"),
            "subscription": request_message.get("subscription", "mock-subscription"),
            "successful": True,
        }
    ]
    logger.debug("Unsubscribe response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId"})
async def disconnect(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD disconnect requests."""
    logger.debug("Disconnect request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/disconnect",
            "clientId": request_message.get("clientId", "mock-client-id"),
            "successful": True,
        }
    ]
    logger.debug("Disconnect response: %s", response_data)
    return web.json_response(response_data)


def create_app() -> web.Application:
    """Creates and configures the aiohttp application."""
    logger.info("Creating application")
    app: web.Application = web.Application()
    app.router.add_post("/cometd", process_request)
    return app


async def start_server(app: web.Application, host: str, port: int) -> None:
    """Sets up and starts the web server."""
    runner: web.AppRunner = web.AppRunner(app)
    await runner.setup()
    site: web.TCPSite = web.TCPSite(runner, host, port)
    await site.start()

    logger.info("======== Running on http://%s:%s ========", host, port)
    # Wait forever
    await asyncio.Event().wait()


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="aiocometd-mock server"
    )
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--connect-interval", type=int, default=60, help="Connect interval")
    parser.add_argument("--connect-timeout", type=int, default=45000, help="Connect timeout")
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Disable CometD request validation",
    )
    parser.add_argument("--debug", default=False, action="store_true", help="Debug mode")
    return parser.parse_args(args)


def main() -> None:
    """Main entry point for the application."""


    args: argparse.Namespace = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.debug("Parsed arguments: %s", args)
    app: web.Application = create_app()
    app["no_validation"] = args.no_validation
    app["connect_interval"] = args.connect_interval
    app["connect_timeout"] = args.connect_timeout

    try:
        asyncio.run(start_server(app, args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server shutting down.")


if __name__ == "__main__":
    main()
