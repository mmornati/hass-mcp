"""Integration MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant integrations.
These tools are thin wrappers around the integrations API layer.
"""

import logging
from typing import Any

from app.api.integrations import (
    get_integration_config,
    get_integrations,
    reload_integration,
)

logger = logging.getLogger(__name__)


async def list_integrations(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all configuration entries (integrations) from Home Assistant.

    Args:
        domain: Optional domain to filter integrations by (e.g., 'mqtt', 'zwave')

    Returns:
        List of integration entries with their status and configuration.
        Each entry contains:
        - entry_id: Unique identifier for the integration entry
        - domain: The integration domain (e.g., 'mqtt', 'zwave')
        - title: Display name of the integration
        - source: Where the integration was configured (user, discovery, etc.)
        - state: Current state (loaded, setup_error, etc.)
        - supports_options: Whether the integration supports configuration options
        - pref_disable_new_entities: Preference to disable new entities
        - pref_disable_polling: Preference to disable polling

    Examples:
        domain=None - get all integrations
        domain="mqtt" - get only MQTT integrations

    Best Practices:
        - Use domain filter to find specific integration types
        - Check state field to identify integrations with errors
        - Use get_integration_config for detailed information
    """
    logger.info("Getting integrations" + (f" for domain: {domain}" if domain else ""))
    return await get_integrations(domain)


async def get_integration_config_tool(entry_id: str) -> dict[str, Any]:
    """
    Get detailed configuration for a specific integration entry.

    Args:
        entry_id: The entry ID of the integration to get

    Returns:
        Detailed configuration dictionary for the integration entry, including:
        - entry_id: Unique identifier
        - domain: Integration domain
        - title: Display name
        - source: Configuration source
        - state: Current state (loaded, setup_error, etc.)
        - options: Integration-specific configuration options
        - pref_disable_new_entities: Preference setting
        - pref_disable_polling: Preference setting

    Examples:
        entry_id="abc123" - get configuration for entry with ID abc123

    Error Handling:
        - Returns error dict if entry_id doesn't exist (404)
        - Error handling is managed by handle_api_errors decorator
    """
    logger.info(f"Getting integration config for entry: {entry_id}")
    return await get_integration_config(entry_id)


async def reload_integration_tool(entry_id: str) -> dict[str, Any]:
    """
    Reload a specific integration.

    Args:
        entry_id: The entry ID of the integration to reload

    Returns:
        Response from the reload service call

    Examples:
        entry_id="abc123" - reload integration with ID abc123

    Note:
        ⚠️ Reloading an integration may cause temporary unavailability of its entities.
        Use with caution, especially for critical integrations like MQTT or Z-Wave.

    Best Practices:
        - Check integration state before reloading
        - Reload integrations that are showing setup errors
        - Avoid reloading during active automation execution
    """
    logger.info(f"Reloading integration: {entry_id}")
    return await reload_integration(entry_id)
