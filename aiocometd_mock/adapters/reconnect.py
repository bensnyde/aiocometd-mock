import logging
import time
from typing import Any, Dict, List

from aiohttp import web

from . import register_adapter

logger = logging.getLogger(__name__)


@register_adapter
async def force_reconnect(
    request: web.Request, payload: List[Dict[str, Any]]
) -> web.Response | None:
    """Force a client to reconnect based on connection count or time."""
    request_message = payload[0]
    client_id = request_message.get("clientId")
    channel = request_message.get("channel")
    client_ids = request.app.get("client_ids", {})

    if client_id in client_ids:
        client_info = client_ids[client_id]
        reconnection_interval = request.app.get("reconnection_interval")
        reconnection_interval_seconds = request.app.get(
            "reconnection_interval_seconds"
        )

        if (
            reconnection_interval is not None
            and client_info["connection_count"] > reconnection_interval
        ) or (
            reconnection_interval_seconds is not None
            and time.time() - client_info["creation_time"] > reconnection_interval_seconds
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
    return None
