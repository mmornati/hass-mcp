"""Service MCP tools for hass-mcp.

This module provides MCP tools for calling Home Assistant services.
These tools are thin wrappers around the services API layer.
"""

import logging
from typing import Any

from app.api.services import call_service, get_service_definitions

logger = logging.getLogger(__name__)


async def call_service_tool(
    domain: str,
    service: str,
    data: dict[str, Any] | None = None,
    return_response: bool = False,
) -> dict[str, Any]:
    """
    Call any Home Assistant service (low-level API access).

    Use this for services that accept parameters (data). For services like
    reload, restart, or refresh that accept NO data, use call_service_simple
    instead to avoid 400 errors from HA.

    Args:
        domain: The domain of the service (e.g., 'light', 'switch', 'automation')
        service: The service to call (e.g., 'turn_on', 'turn_off', 'toggle')
        data: Service parameters as a dict. Omit or set to null for services
            that don't accept data (reload, restart, refresh, etc.).
            Example: {'entity_id': 'light.living_room', 'brightness': 128}
            ⚠ Services like scene.reload, automation.reload, homeassistant.restart
            accept NO data — passing any will cause a 400 error.
        return_response: If True, request response data from services that support it.
            Use only for services known to return data (e.g., weather.get_forecasts).
            Using this on services that don't support responses will cause a 400 error.

    Returns:
        The response from Home Assistant. Without return_response: usually empty for
        successful calls. With return_response: includes changed_states and service_response.

    Examples:
        domain='light', service='turn_on', data={'entity_id': 'light.x', 'brightness': 255}
        domain='weather', service='get_forecasts', data={'entity_id': 'weather.home', 'type': 'daily'}, return_response=True

    Services that accept NO data (use call_service_simple instead):
        - domain='scene', service='reload'
        - domain='automation', service='reload'
        - domain='homeassistant', service='restart'
        - domain='homeassistant', service='reload_core_config'
        - domain='script', service='reload'
    """
    logger.info(f"Calling Home Assistant service: {domain}.{service} with data: {data}")
    return await call_service(domain, service, data or {}, return_response=return_response)


async def list_services_tool(
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    List available Home Assistant services with their parameter schemas.

    Use this to discover what services are available and what data fields
    they accept before calling them. Each service definition includes
    field names, types, and whether they are required.

    Args:
        domain: Optional domain to filter by (e.g., 'light', 'scene', 'automation').
            If omitted, returns all services across all domains.

    Returns:
        List of service definitions. Each entry contains:
            domain (str): The service domain
            services (list): Available services with name, description, fields

    Examples:
        domain='scene' -> returns all scene services with their field schemas
        domain='light' -> returns light services like turn_on, turn_off with field schemas
        (no filter)    -> returns all services across all domains

    Best Practices:
        - Call this first when you're unsure what data a service needs
        - Use the 'fields' in each service definition to build the data dict
        - Services with empty 'fields' accept no data (reload, restart, etc.)
    """
    logger.info(f"Listing services for domain: {domain or 'all'}")
    all_services = await get_service_definitions()
    if domain:
        domain_lower = domain.lower()
        return [s for s in all_services if s.get("domain") == domain_lower]
    return all_services


async def call_service_simple_tool(
    domain: str,
    service: str,
) -> dict[str, Any]:
    """
    Call a Home Assistant service that accepts NO data parameters.

    Use this for reload, restart, refresh operations that don't accept
    any service data. Passing data to these services via call_service
    would result in a 400 Bad Request error.

    Args:
        domain: The domain of the service (e.g., 'scene', 'automation', 'homeassistant')
        service: The service to call (e.g., 'reload', 'restart', 'refresh')

    Returns:
        The response from Home Assistant (typically an empty list for successful calls).

    Examples:
        domain='scene', service='reload'
        domain='automation', service='reload'
        domain='homeassistant', service='restart'
        domain='homeassistant', service='reload_core_config'
        domain='script', service='reload'
        domain='group', service='reload'
    """
    logger.info(f"Calling simple service (no data): {domain}.{service}")
    return await call_service(domain, service, data={})
