"""Events API module for hass-mcp.

This module provides functions for interacting with Home Assistant events.
Events are used for inter-component communication and triggering automations.
"""

import logging
from typing import Any

from app.api.base import BaseAPI
from app.api.logbook import get_logbook
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class EventsAPI(BaseAPI):
    """API client for Home Assistant event operations."""

    pass


_events_api = EventsAPI()


@handle_api_errors
async def fire_event(event_type: str, event_data: dict[str, Any] | None = None) -> dict[str, Any]:
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
    payload = event_data or {}
    return await _events_api.post(f"/api/events/{event_type}", data=payload)


@handle_api_errors
async def list_event_types() -> list[str]:
    """
    List common event types used in Home Assistant.

    Returns:
        List of common event type strings

    Example response:
        [
            "state_changed",
            "time_changed",
            "service_registered",
            "call_service",
            "homeassistant_start",
            "homeassistant_stop",
            "automation_triggered",
            "script_started",
            "scene_on",
            "custom_event"
        ]

    Note:
        Home Assistant API doesn't provide a comprehensive list of event types.
        This function returns common event types from documentation.
        Custom event types can be any string, but common ones are listed here.
        Events are documented in Home Assistant's event documentation.

    Best Practices:
        - Use this to discover common event types
        - Create custom event types for your own use cases
        - Check automations/logbook for other event types used in your setup
        - Use descriptive names for custom event types
    """
    # Note: Home Assistant API doesn't provide a list of event types
    # This returns common event types from documentation
    common_event_types = [
        "state_changed",
        "time_changed",
        "service_registered",
        "call_service",
        "homeassistant_start",
        "homeassistant_stop",
        "automation_triggered",
        "script_started",
        "scene_on",
        "custom_event",
    ]

    return common_event_types


@handle_api_errors
async def get_events(entity_id: str | None = None, hours: int = 1) -> list[dict[str, Any]]:
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
    # Events can be retrieved via logbook
    return await get_logbook(entity_id=entity_id, hours=hours)
