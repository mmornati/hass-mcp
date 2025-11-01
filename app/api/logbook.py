"""Logbook API module for hass-mcp.

This module provides functions for interacting with Home Assistant logbook.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.api.base import BaseAPI
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class LogbookAPI(BaseAPI):
    """API client for Home Assistant logbook operations."""

    pass


_logbook_api = LogbookAPI()


@handle_api_errors
async def get_logbook(
    timestamp: str | None = None,
    entity_id: str | None = None,
    hours: int = 24,
) -> list[dict[str, Any]]:
    """
    Get logbook entries.

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

    Example response:
        [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
                "icon": null
            }
        ]

    Note:
        The logbook records all state changes and events in Home Assistant.
        Useful for debugging and auditing system behavior.
        If timestamp is provided, hours parameter is ignored.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use entity_id filter to focus on specific entities
        - Use timestamp for precise time ranges
    """
    # Calculate timestamp if not provided
    if not timestamp:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)
        timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    # Ensure timestamp doesn't have timezone info for API format
    elif timestamp.endswith("Z"):
        timestamp = timestamp[:-1]

    # Build URL and params
    endpoint = f"/api/logbook/{timestamp}"
    params: dict[str, Any] = {}
    if entity_id:
        params["entity"] = entity_id

    response = await _logbook_api.get(endpoint, params=params)
    return cast(list[dict[str, Any]], response)


@handle_api_errors
async def get_entity_logbook(entity_id: str, hours: int = 24) -> list[dict[str, Any]]:
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
    return await get_logbook(entity_id=entity_id, hours=hours)


@handle_api_errors
async def search_logbook(query: str, hours: int = 24) -> list[dict[str, Any]]:
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
    # Get all logbook entries
    entries = await get_logbook(hours=hours)

    # Filter entries matching query
    query_lower = query.lower()
    matching_entries = []

    for entry in entries:
        # Search in entity_id, name, message, etc.
        entry_entity_id = entry.get("entity_id", "").lower()
        entry_name = entry.get("name", "").lower()
        entry_message = entry.get("message", "").lower()

        if (
            query_lower in entry_entity_id
            or query_lower in entry_name
            or query_lower in entry_message
        ):
            matching_entries.append(entry)

    return matching_entries
