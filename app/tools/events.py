"""Events MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant events.
These tools are thin wrappers around the events API layer.
"""

import logging
from typing import Any

from app.api.events import fire_event, get_events, list_event_types

logger = logging.getLogger(__name__)


async def fire_event_tool(
    event_type: str, event_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Fire a custom event.

    Args:
        event_type: The event type name (e.g., 'custom_event', 'state_changed')
        event_data: Optional dictionary of event data/payload

    Returns:
        Response dictionary from the event fire API

    Examples:
        event_type="custom_event", event_data={"message": "Hello"}
        event_type="automation_triggered", event_data={"entity_id": "light.living_room"}

    Note:
        Events are used for communication between different parts of Home Assistant.
        Custom events can trigger automations that listen for specific event types.
        Event data is optional but commonly used to pass information to event handlers.

    Best Practices:
        - Use descriptive event type names (e.g., 'custom_event', 'my_app_ready')
        - Include relevant data in event_data for event handlers
        - Use events to trigger automations based on custom conditions
        - Document custom event types for team members
        - Use events for inter-component communication
    """
    logger.info(f"Firing event: {event_type}" + (f" with data: {event_data}" if event_data else ""))
    return await fire_event(event_type, event_data)


async def list_event_types_tool() -> list[str]:
    """
    List common event types used in Home Assistant.

    Returns:
        List of common event type strings

    Examples:
        Returns common event types like "state_changed", "time_changed", etc.

    Note:
        Home Assistant API doesn't provide a comprehensive list of event types.
        This function returns common event types from documentation.
        Custom event types can be any string, but common ones are listed here.

    Best Practices:
        - Use this to discover common event types
        - Create custom event types for your own use cases
        - Check automations/logbook for other event types used in your setup
        - Use descriptive names for custom event types
    """
    logger.info("Getting list of common event types")
    return await list_event_types()


async def get_events_tool(entity_id: str | None = None, hours: int = 1) -> list[dict[str, Any]]:
    """
    Get recent events for an entity (via logbook).

    Args:
        entity_id: Optional entity ID to filter events for a specific entity
        hours: Number of hours of history to retrieve (default: 1)

    Returns:
        List of event dictionaries from logbook entries

    Examples:
        entity_id=None, hours=1 - get all recent events from last hour
        entity_id="light.living_room", hours=24 - get events for specific entity from last day

    Note:
        Events can be retrieved via logbook entries.
        This is a convenience function that uses get_logbook_entries.
        Useful for debugging and understanding what events occurred.

    Best Practices:
        - Keep hours reasonable (1-24) for token efficiency
        - Use entity_id to filter events for specific entities
        - Use to debug event-triggered automations
        - Use to understand event flow in your Home Assistant setup
    """
    logger.info(
        "Getting recent events"
        + (f" for entity: {entity_id}" if entity_id else "")
        + f" for last {hours} hours"
    )
    return await get_events(entity_id, hours)
