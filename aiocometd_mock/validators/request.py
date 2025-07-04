import logging
from typing import Any, Dict, List, Set

from aiohttp import web

from . import register_validator

logger = logging.getLogger(__name__)


def _create_error_response(
    error_message: str,
    channel: str | None = None,
    message_id: str | None = None,
    *,
    status_code: int = 400,
) -> web.Response:
    """
    Creates a standard CometD error response for a failed validation.

    Args:
        error_message: The description of the error.
        channel: The channel of the message that failed validation.
        message_id: The ID of the message that failed validation.
        status_code: The HTTP status code for the response.

    Returns:
        An aiohttp web.Response object containing the CometD error payload.
    """
    error_tag = error_message.lower().replace(" ", "_").replace("'", "")
    log_message = f"CometD validation failed: {error_message}. Channel: {channel or 'N/A'}, ID: {message_id or 'N/A'}"
    logger.error(log_message)

    # As per spec, the error response is a JSON array.
    response_payload = {
        "successful": False,
        "error": f"{status_code}::bad_request,{error_tag}",
        "advice": {"reconnect": "none"},
    }
    if channel:
        response_payload["channel"] = channel
    if message_id:
        response_payload["id"] = message_id

    # Even if the request has multiple messages, a single validation error
    # on the payload structure warrants a single error response that rejects the batch.
    return web.json_response([response_payload], status=status_code)


@register_validator
async def validate_request(request: web.Request, payload: List[Dict[str, Any]]) -> web.Response | None:
    """
    Validate incoming CometD requests against the CometD specification.

    This function checks for:
    - The payload is a non-empty list.
    - Each item in the payload is a JSON object (dict).
    - Each message object has a valid 'channel' field (string starting with '/').
    - The presence of a string 'clientId' for all non-handshake messages.
    - Correct types for channel-specific fields like 'subscription' and 'connectionType'.

    If any validation check fails, it returns a standard CometD error response,
    rejecting the entire batch of messages.

    Args:
        request: The incoming aiohttp web.Request.
        payload: The JSON-decoded request body, expected to be a list of messages.

    Returns:
        None if the payload is valid, otherwise an aiohttp web.Response with
        a CometD error message.
    """
    # Skip validation if the 'no_validation' flag is set in the app context
    if request.app.get("no_validation"):
        return None

    if not isinstance(payload, list) or not payload:
        return _create_error_response("Payload must be a non-empty list")

    for message in payload:
        if not isinstance(message, dict):
            # The payload must be a list of objects.
            return _create_error_response("Payload must contain only JSON objects")

        channel = message.get("channel")
        message_id = message.get("id")

        # 1. Validate 'channel' field
        if not isinstance(channel, str) or not channel.startswith("/"):
            return _create_error_response(
                "Message must have a 'channel' field starting with '/'",
                channel=channel,
                message_id=message_id,
            )

        # 2. Validate 'clientId' for all messages except the initial handshake
        if channel != "/meta/handshake":
            if not isinstance(message.get("clientId"), str):
                return _create_error_response(
                    "Message requires a string 'clientId' field",
                    channel=channel,
                    message_id=message_id,
                )

        # 3. Perform channel-specific field validation
        if channel in ("/meta/subscribe", "/meta/unsubscribe"):
            subscription = message.get("subscription")
            is_string = isinstance(subscription, str)
            is_list_of_strings = isinstance(subscription, list) and all(isinstance(s, str) for s in subscription)
            if not (is_string or is_list_of_strings):
                return _create_error_response(
                    "Message requires a 'subscription' field (string or array of strings)",
                    channel=channel,
                    message_id=message_id,
                )

        if channel == "/meta/connect":
            if not isinstance(message.get("connectionType"), str):
                return _create_error_response(
                    "Message requires a string 'connectionType' field",
                    channel=channel,
                    message_id=message_id,
                )

    # If we get here, all messages in the payload are valid.
    return None
