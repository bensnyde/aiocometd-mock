import logging
import random
from typing import Any, Dict, List

from aiohttp import web

from . import register_adapter

logger = logging.getLogger(__name__)

# A list of possible HTTP responses (status_code, message) to be chosen from.
# You can customize this list to add or remove status codes as needed.
CHAOS_RESPONSES = [
    (200, "OK"),
    (400, "Bad Request"),
    (401, "Unauthorized"),
    (403, "Forbidden"),
    (404, "Not Found"),
    (429, "Too Many Requests"),
    (500, "Internal Server Error"),
    (502, "Bad Gateway"),
    (503, "Service Unavailable"),
    (504, "Gateway Timeout"),
]


@register_adapter
async def chaos(
    request: web.Request, payload: List[Dict[str, Any]]
) -> web.Response:
    """
    Randomly replies with a variety of HTTP status codes to simulate chaos.

    This adapter always triggers and does not pass the request to other adapters.
    """
    # Randomly select a status code and message from the list.
    status_code, message = random.choice(CHAOS_RESPONSES)

    # Safely get details from the payload for logging and a potential success response.
    request_message = payload[0] if payload else {}
    client_id = request_message.get("clientId", "unknown")
    channel = request_message.get("channel")
    message_id = request_message.get("id")

    logger.info(
        "Chaos Adapter Activated! Client '%s' will receive a %d %s response.",
        client_id,
        status_code,
        message,
    )

    # If the chosen code is 200 OK, we return a successful-looking response.
    if status_code == 200:
        return web.json_response(
            [
                {
                    "id": message_id,
                    "channel": channel,
                    "clientId": client_id,
                    "successful": True,
                }
            ]
        )

    # For all other codes, return a simple text response with the error.
    return web.Response(status=status_code, text=message)