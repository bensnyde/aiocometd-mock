import logging
import uuid
from typing import Any, Dict, List

from aiohttp import web

from .validators import validate_client_id, validate_cometd_request

logger: logging.Logger = logging.getLogger(__name__)


async def process_request(request: web.Request) -> web.Response:
    """
    Processes an incoming CometD request and routes it to the correct handler.
    """
    try:
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
            return web.json_response(
                [{"successful": False, "error": "404::Unknown Channel"}],
                status=404,
            )
    except Exception as e:
        logger.exception("Error processing request: %s", e)
        return web.json_response(
            [{"successful": False, "error": f"500::Internal Server Error: {e}"}],
            status=500,
        )


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
