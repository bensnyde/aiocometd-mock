import argparse
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from aiocometd_mock.validators import validate_cometd_request, validate_client_id
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
    client_id = str(uuid.uuid4())
    request.app["client_ids"][client_id] = {"connection_count": 0}
    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "0"),
            "channel": "/meta/handshake",
            "successful": True,
            "version": "1.0",
            "supportedConnectionTypes": ["long-polling"],
            "clientId": client_id,
            "advice": {"reconnect": "retry", "interval": 0, "timeout": 45000},
        }
    ]
    logger.debug("Handshake response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "id"})
@validate_client_id
async def connect(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD connect requests."""
    request_message: Dict[str, Any] = payload[0]
    client_id = request_message.get("clientId")

    logger.debug("Connect request: %s", payload)

    advice = {"interval": request.app["connect_interval"], "timeout": request.app["connect_timeout"]}

    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "1"),
            "channel": "/meta/connect",
            "clientId": client_id,
            "successful": True,
            "advice": advice,
        }
    ]
    logger.debug("Connect response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "subscription"})
@validate_client_id
async def subscribe(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD subscribe requests."""
    logger.debug("Subscribe request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    client_id = request_message.get("clientId")

    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "2"),
            "channel": "/meta/subscribe",
            "clientId": client_id,
            "subscription": request_message.get("subscription", "mock-subscription"),
            "successful": True,
        }
    ]
    logger.debug("Subscribe response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId", "subscription"})
@validate_client_id
async def unsubscribe(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD unsubscribe requests."""
    logger.debug("Unsubscribe request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    client_id = request_message.get("clientId")

    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "3"),
            "channel": "/meta/unsubscribe",
            "clientId": client_id,
            "subscription": request_message.get("subscription", "mock-subscription"),
            "successful": True,
        }
    ]
    logger.debug("Unsubscribe response: %s", response_data)
    return web.json_response(response_data)


@validate_cometd_request({"clientId"})
@validate_client_id
async def disconnect(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
    """Handles CometD disconnect requests."""
    logger.debug("Disconnect request: %s", payload)
    request_message: Dict[str, Any] = payload[0]
    client_id = request_message.get("clientId")

    if client_id in request.app["client_ids"]:
        del request.app["client_ids"][client_id]

    response_data: List[Dict[str, Any]] = [
        {
            "id": request_message.get("id", "4"),
            "channel": "/meta/disconnect",
            "clientId": client_id,
            "successful": True,
        }
    ]
    logger.debug("Disconnect response: %s", response_data)
    return web.json_response(response_data)


def create_app() -> web.Application:
    """Creates and configures the aiohttp application."""
    logger.info("Creating application")
    app: web.Application = web.Application()
    app["client_ids"] = {}
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
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="aiocometd-mock server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--connect-interval", type=int, default=60, help="Connect interval returned by server")
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
    app["reconnection_interval"] = args.reconnection_interval
    app["expire_client_ids_after"] = args.expire_client_ids_after

    try:
        asyncio.run(start_server(app, args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server shutting down.")


if __name__ == "__main__":
    main()
