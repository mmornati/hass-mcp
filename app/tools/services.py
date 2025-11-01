"""Service MCP tools for hass-mcp.

This module provides MCP tools for calling Home Assistant services.
These tools are thin wrappers around the services API layer.
"""

import logging
from typing import Any

from app.api.services import call_service

logger = logging.getLogger(__name__)


async def call_service_tool(
    domain: str, service: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Call any Home Assistant service (low-level API access).

    Args:
        domain: The domain of the service (e.g., 'light', 'switch', 'automation')
        service: The service to call (e.g., 'turn_on', 'turn_off', 'toggle')
        data: Optional data to pass to the service (e.g., {'entity_id': 'light.living_room'})

    Returns:
        The response from Home Assistant (usually empty for successful calls)

    Examples:
        domain='light', service='turn_on', data={'entity_id': 'light.x', 'brightness': 255}
        domain='automation', service='reload'
        domain='fan', service='set_percentage', data={'entity_id': 'fan.x', 'percentage': 50}

    Best Practices:
        - Use domain and service to identify the service to call
        - Pass service data in the data parameter
        - Check response for errors or status
    """
    logger.info(f"Calling Home Assistant service: {domain}.{service} with data: {data}")
    return await call_service(domain, service, data or {})
