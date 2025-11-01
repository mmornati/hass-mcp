"""Logbook MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant logbook.
These tools are thin wrappers around the logbook API layer.
"""

import logging
from typing import Any

from app.api.logbook import get_entity_logbook, get_logbook, search_logbook

logger = logging.getLogger(__name__)


async def get_logbook_tool(
    timestamp: str | None = None,
    entity_id: str | None = None,
    hours: int = 24,
) -> list[dict[str, Any]]:
    """
    Get logbook entries for a time range, optionally filtered by entity.

    Args:
        timestamp: Optional timestamp to start from (ISO format, e.g., "2025-01-01T00:00:00Z")
                   If not provided, calculated from hours parameter
        entity_id: Optional entity ID to filter logbook entries by
        hours: Number of hours of history to retrieve (default: 24, only used if timestamp is not provided)

    Returns:
        List of logbook entry dictionaries containing:
        - when: Timestamp of the event
        - name: Display name of the entity
        - entity_id: The entity ID
        - state: State change value
        - domain: Entity domain
        - message: Description of what happened
        - icon: Icon associated with the event (if available)

    Examples:
        timestamp=None, entity_id=None, hours=24 - get last 24 hours of all logbook entries
        timestamp=None, entity_id="light.living_room", hours=48 - get last 48 hours for specific entity
        timestamp="2025-01-01T00:00:00Z", entity_id=None - get entries from specific timestamp

    Note:
        The logbook records all state changes and events in Home Assistant.
        Useful for debugging and auditing system behavior.
        If timestamp is provided, hours parameter is ignored.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use entity_id filter to focus on specific entities
        - Use timestamp for precise time ranges
        - Use to debug state changes and events
    """
    logger.info(
        "Getting logbook entries"
        + (f" for entity: {entity_id}" if entity_id else "")
        + (f" from timestamp: {timestamp}" if timestamp else f" for last {hours} hours")
    )
    return await get_logbook(timestamp, entity_id, hours)


async def get_entity_logbook_tool(entity_id: str, hours: int = 24) -> list[dict[str, Any]]:
    """
    Get logbook entries for a specific entity.

    Args:
        entity_id: The entity ID to get logbook entries for
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        List of logbook entry dictionaries for the specified entity

    Examples:
        entity_id="light.living_room", hours=24 - get last 24 hours of logbook for light
        entity_id="sensor.temperature", hours=168 - get last 7 days of logbook for sensor

    Note:
        This is a convenience wrapper around get_logbook with entity_id filter.
        Returns only logbook entries for the specified entity.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use this to debug specific entity behavior
        - Check logbook to understand entity state changes over time
    """
    logger.info(f"Getting logbook entries for entity: {entity_id}, hours: {hours}")
    return await get_entity_logbook(entity_id, hours)


async def search_logbook_tool(query: str, hours: int = 24) -> list[dict[str, Any]]:
    """
    Search logbook entries by query string.

    Args:
        query: Search query to match against entity_id, name, or message
        hours: Number of hours of history to search (default: 24)

    Returns:
        List of logbook entry dictionaries matching the query

    Examples:
        query="error" - find logbook entries containing "error"
        query="sensor" - find logbook entries related to sensors
        query="light.living_room" - find entries for specific entity

    Note:
        This searches through logbook entries using case-insensitive matching.
        Searches in entity_id, name, and message fields.
        Returns entries that contain the query string in any of these fields.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use specific queries to find relevant entries
        - Search for error messages, entity IDs, or specific events
    """
    logger.info(f"Searching logbook for query: {query}, hours: {hours}")
    return await search_logbook(query, hours)
