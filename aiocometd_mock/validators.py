import logging
from functools import wraps
from typing import Any, Dict, List, Set

from aiohttp import web

logger = logging.getLogger(__name__)


def validate_cometd_request(required_fields: Set[str] = None):
    """
    Decorator to validate incoming CometD requests.

    It checks for:
    - Valid JSON body.
    - Payload is a non-empty list of objects.
    - Presence of required fields for the specific CometD channel.

    If validation fails, it returns a standard CometD error response.
    """
    _required_fields = required_fields or set()

    def decorator(handler):
        @wraps(handler)
        async def wrapper(request: web.Request) -> web.Response:
            # Skip validation if the no_validation flag is set on the app
            if request.app.get("no_validation"):
                try:
                    payload = await request.json()
                except Exception:
                    payload = []
                return await handler(request, payload)

            # Parse the request body
            try:
                payload: List[Dict[str, Any]] = await request.json()
            except Exception:
                logger.error("Request body is not valid JSON.")
                return web.json_response(
                    [
                        {
                            "channel": "/meta/error",
                            "successful": False,
                            "error": "400::bad_request,JSON_parse_error",
                            "advice": {"reconnect": "none"},
                        }
                    ],
                    status=400,
                )

            if not isinstance(payload, list) or not payload:
                logger.error("Invalid payload: must be a non-empty list.")
                return web.json_response(
                    [
                        {
                            "channel": "/meta/error",
                            "successful": False,
                            "error": "400::bad_request,invalid_payload",
                            "advice": {"reconnect": "none"},
                        }
                    ],
                    status=400,
                )

            request_message = payload[0]
            channel = request_message.get("channel")

            # Validate the presence of required fields
            missing_fields = _required_fields - set(request_message.keys())
            if missing_fields:
                error_msg = (
                    f"401::{','.join(sorted(list(missing_fields)))}::missing_required_fields"
                )
                logger.error(f"Validation failed: {error_msg} {request_message}")
                return web.json_response(
                    [
                        {
                            "id": request_message.get("id"),
                            "channel": channel,
                            "successful": False,
                            "error": error_msg,
                            "advice": {"reconnect": "none"},
                        }
                    ],
                    status=400,
                )

            # If validation is successful, pass the parsed payload to the handler
            return await handler(request, payload)

        return wrapper

    return decorator


def validate_client_id(handler):
    """
    Decorator to validate the clientId in a CometD request.

    It checks if the clientId from the request payload is present in the
    `client_ids` dictionary of the web application.

    If the clientId is invalid, it returns a CometD error response
    with advice to perform a handshake.
    """

    @wraps(handler)
    async def wrapper(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response:
        if request.app.get("no_validation"):
            return await handler(request, payload)
        request_message = payload[0]
        client_id = request_message.get("clientId")
        channel = request_message.get("channel")
        client_ids = request.app.get("client_ids", {})

        # Pre-emptively check for expiration and remove if necessary
        if client_id in client_ids:
            client_info = client_ids[client_id]
            expire_after = request.app.get("expire_client_ids_after")
            if (
                expire_after is not None
                and client_info["connection_count"] >= expire_after
            ):
                del client_ids[client_id]
                logger.debug("Expired clientId: %s", client_id)

        # Single check for validity (covers unknown and just-expired)
        if client_id not in client_ids:
            logger.debug("Unknown or expired clientId in request: %s", client_id)
            return web.json_response(
                [
                    {
                        "id": request_message.get("id"),
                        "channel": channel,
                        "successful": False,
                        "error": f"401::{client_id}::unknown_client_id",
                        "advice": {"reconnect": "handshake"},
                    }
                ]
            )

        # If we're here, the client is valid.
        client_info = client_ids[client_id]
        client_info["connection_count"] += 1
        logger.debug(
            f"Connection count for client {client_id} is now: {client_info['connection_count']}"
        )

        reconnection_interval = request.app.get("reconnection_interval")
        if (
            reconnection_interval is not None
            and client_info["connection_count"] > reconnection_interval
        ):
            client_info["connection_count"] = 1
            logger.debug(
                "Reconnection interval exceeded for client %s, advising reconnect.",
                client_id,
            )
            return web.json_response(
                [
                    {
                        "id": request_message.get("id", "1"),
                        "channel": channel,
                        "clientId": client_id,
                        "successful": True,
                        "advice": {"reconnect": "retry"},
                    }
                ]
            )

        return await handler(request, payload)

    return wrapper

