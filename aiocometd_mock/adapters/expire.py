import logging
import time
from typing import Any, Dict, List

from aiohttp import web

from . import register_adapter

logger = logging.getLogger(__name__)


@register_adapter
async def expire_client_id(
    request: web.Request, payload: List[Dict[str, Any]]
) -> web.Response | None:
    """Expire client IDs based on connection count or time."""
    request_message = payload[0]
    client_id = request_message.get("clientId")
    client_ids = request.app.get("client_ids", {})

    if client_id in client_ids:
        client_info = client_ids[client_id]
        expire_after = request.app.get("expire_client_ids_after")
        expire_after_seconds = request.app.get("expire_client_ids_after_seconds")

        if (
            expire_after is not None
            and client_info["connection_count"] >= expire_after
        ) or (
            expire_after_seconds is not None
            and time.time() - client_info["creation_time"] >= expire_after_seconds
        ):
            del client_ids[client_id]
            logger.debug("Expired clientId: %s", client_id)
    return None
