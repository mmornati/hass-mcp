"""Services API module for hass-mcp.

This module provides functions for calling Home Assistant services.
"""

import logging
from typing import Any, cast

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def call_service(
    domain: str, service: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Call a Home Assistant service.

    Args:
        domain: The service domain (e.g., 'light', 'switch', 'automation')
        service: The service name (e.g., 'turn_on', 'turn_off', 'toggle')
        data: Optional dictionary of service data/parameters

    Returns:
        Response from the service call (usually empty list for successful calls)

    Example response:
        []

    Examples:
        # Turn on a light
        await call_service("light", "turn_on", {"entity_id": "light.living_room"})

        # Turn off with brightness
        await call_service("light", "turn_on", {"entity_id": "light.bedroom", "brightness": 128})

        # Toggle a switch
        await call_service("switch", "toggle", {"entity_id": "switch.garden_lights"})

    Note:
        Services are used by many other domains and are generic and reusable patterns.
        Common domains include light, switch, fan, cover, climate, etc.
        Service data varies by domain and service type.

    Best Practices:
        - Check service availability before calling
        - Use appropriate service data for the domain
        - Handle empty responses (success usually returns [])
        - Use entity_id in data for entity-specific services
    """
    if data is None:
        data = {}

    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/{domain}/{service}", headers=get_ha_headers(), json=data
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
