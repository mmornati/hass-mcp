"""Integrations API module for hass-mcp.

This module provides functions for interacting with Home Assistant integrations.
"""

import logging
from typing import Any, cast

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.ttl import TTL_MEDIUM
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
@cached(ttl=TTL_MEDIUM, key_prefix="integrations")
async def get_integrations(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of all configuration entries (integrations).

    Args:
        domain: Optional domain to filter integrations by (e.g., 'mqtt', 'zwave')

    Returns:
        List of integration entries with their status and configuration

    Example response:
        [
            {
                "entry_id": "abc123",
                "domain": "mqtt",
                "title": "MQTT",
                "source": "user",
                "state": "loaded",
                "supports_options": true,
                "pref_disable_new_entities": false,
                "pref_disable_polling": false
            }
        ]

    Best Practices:
        - Use domain filter to find specific integration types
        - Check state field to identify integrations with errors
        - Use get_integration_config for detailed information
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/config_entries/entry",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    entries = cast(list[dict[str, Any]], response.json())

    # Filter by domain if specified
    if domain:
        entries = [e for e in entries if e.get("domain") == domain]

    return entries


@handle_api_errors
@cached(ttl=TTL_MEDIUM, key_prefix="integrations")
async def get_integration_config(entry_id: str) -> dict[str, Any]:
    """
    Get detailed configuration for a specific integration entry.

    Args:
        entry_id: The entry ID of the integration to get

    Returns:
        Detailed configuration dictionary for the integration entry

    Example response:
        {
            "entry_id": "abc123",
            "domain": "mqtt",
            "title": "MQTT",
            "source": "user",
            "state": "loaded",
            "options": {...},
            "pref_disable_new_entities": false,
            "pref_disable_polling": false
        }

    Error Handling:
        - Returns error dict if entry_id doesn't exist (404)
        - Error handling is managed by handle_api_errors decorator
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/config_entries/entry/{entry_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
@invalidate_cache(pattern="integrations:*")
async def reload_integration(entry_id: str) -> dict[str, Any]:
    """
    Reload a specific integration.

    Args:
        entry_id: The entry ID of the integration to reload

    Returns:
        Response from the reload service call

    Example response:
        []

    Note:
        ⚠️ Reloading an integration may cause temporary unavailability of its entities.
        Use with caution, especially for critical integrations like MQTT or Z-Wave.

    Best Practices:
        - Check integration state before reloading
        - Reload integrations that are showing setup errors
        - Avoid reloading during active automation execution
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/config/reload_entry",
        headers=get_ha_headers(),
        json={"entry_id": entry_id},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
