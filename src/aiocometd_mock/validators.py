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
                return await handler(request, [{}])

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
                logger.error("Validation failed: %s", error_msg)
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

