"""Services API module for hass-mcp.

This module provides functions for calling Home Assistant services.
"""

import logging
from typing import Any, cast

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.cache.decorator import invalidate_cache
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


def should_invalidate_entity_cache(
    args: tuple[Any, ...], kwargs: dict[str, Any], result: Any
) -> bool:
    """Determine if entity cache should be invalidated based on service call."""
    # Check if this service call affects an entity
    data = kwargs.get("data") or (args[2] if len(args) > 2 else None)
    return isinstance(data, dict) and "entity_id" in data


@handle_api_errors
@invalidate_cache(
    pattern="entities:state:*",
    condition=should_invalidate_entity_cache,
)
async def call_service(
    domain: str,
    service: str,
    data: dict[str, Any] | None = None,
    return_response: bool = False,
) -> dict[str, Any]:
    """
    Call a Home Assistant service.

    Args:
        domain: The service domain (e.g., 'light', 'switch', 'automation')
        service: The service name (e.g., 'turn_on', 'turn_off', 'toggle')
        data: Optional dictionary of service data/parameters
        return_response: If True, request response data from services that support it.
            Some services return structured data (e.g., weather.get_forecasts).
            If the service doesn't support responses, this may cause an error.

    Returns:
        Response from the service call. Without return_response, usually returns
        a list of changed states. With return_response, returns a dict containing:
        - changed_states: List of states that changed during the service call
        - service_response: Response data from the service (if supported)

    Example response (with return_response=True):
        {
            "changed_states": [...],
            "service_response": {
                "weather.home": {
                    "forecast": [{"condition": "sunny", "temperature": 20}, ...]
                }
            }
        }

    Examples:
        # Turn on a light
        await call_service("light", "turn_on", {"entity_id": "light.living_room"})

        # Get weather forecast (with response data)
        await call_service("weather", "get_forecasts",
            {"entity_id": "weather.home", "type": "daily"}, return_response=True)

        # Toggle a switch
        await call_service("switch", "toggle", {"entity_id": "switch.garden_lights"})

    Note:
        Services are used by many other domains and are generic and reusable patterns.
        Common domains include light, switch, fan, cover, climate, etc.
        Service data varies by domain and service type.
        Use return_response=True only for services that support response data.

    Best Practices:
        - Check service availability before calling
        - Use appropriate service data for the domain
        - Handle empty responses (success usually returns [])
        - Use entity_id in data for entity-specific services
        - Use return_response=True for services like weather.get_forecasts
    """
    if data is None:
        data = {}

    client = await get_client()
    url = f"{HA_URL}/api/services/{domain}/{service}"
    if return_response:
        url += "?return_response"

    response = await client.post(url, headers=get_ha_headers(), json=data)
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
