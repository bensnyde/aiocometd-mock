import logging
from typing import Any, Dict, List

from aiohttp import web

from . import register_validator
from .. import adapters

logger = logging.getLogger(__name__)


@register_validator
async def validate_client_id(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response | None:
    """
    Validate the clientId in a CometD request.

    It checks if the clientId from the request payload is present in the
    `client_ids` dictionary of the web application.

    If the clientId is invalid, it returns a CometD error response
    with advice to perform a handshake.
    """
    request_message = payload[0]
    client_id = request_message.get("clientId")
    channel = request_message.get("channel")
    client_ids = request.app.get("client_ids", {})

    if channel != "/meta/handshake":
        if not client_id or client_id not in client_ids:
            logger.debug("Unknown clientId in request: %s", client_id)
            return web.json_response(
                [
                    {
                        "id": request_message.get("id"),
                        "channel": channel,
                        "successful": False,
                        "error": f"401::{client_id}::unknown_client_id",
                        "advice": {"reconnect": "handshake"},
                    }
                ],
                status=400
            )

        if client_id in client_ids:
            client_info = client_ids[client_id]
            client_info["connection_count"] += 1
            logger.debug(
                f"Connection count for client {client_id} is now: {client_info['connection_count']}"
            )
    return None