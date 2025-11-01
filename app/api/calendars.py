"""Calendars API module for hass-mcp.

This module provides functions for interacting with Home Assistant calendars.
Calendars are used for managing calendar events and integrations.
"""

import logging
from typing import Any, cast

from app.api.base import BaseAPI
from app.api.entities import get_entities
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class CalendarsAPI(BaseAPI):
    """API client for Home Assistant calendar operations."""

    pass


_calendars_api = CalendarsAPI()


@handle_api_errors
async def list_calendars() -> list[dict[str, Any]]:
    """
    Get list of all calendar entities.

    Returns:
        List of calendar dictionaries containing:
        - entity_id: The calendar entity ID
        - state: Current state of the calendar
        - friendly_name: Display name of the calendar
        - supported_features: Bitmask of supported features

    Example response:
        [
            {
                "entity_id": "calendar.google",
                "state": "idle",
                "friendly_name": "Google Calendar",
                "supported_features": 3
            }
        ]

    Note:
        Calendars are entities that support calendar functionality.
        Supported features indicate which operations are available
        (e.g., CREATE_EVENT, DELETE_EVENT).

    Best Practices:
        - Use this to discover available calendars
        - Check supported_features to see what operations are available
        - Use to find calendar entities before getting events
    """
    calendar_entities = await get_entities(domain="calendar", lean=True)

    calendars = []
    for entity in calendar_entities:
        calendars.append(
            {
                "entity_id": entity.get("entity_id"),
                "state": entity.get("state"),
                "friendly_name": entity.get("attributes", {}).get("friendly_name"),
                "supported_features": entity.get("attributes", {}).get("supported_features", 0),
            }
        )

    return calendars


@handle_api_errors
async def get_calendar_events(
    entity_id: str, start_date: str, end_date: str
) -> list[dict[str, Any]]:
    """
    Get calendar events for a date range.

    Args:
        entity_id: The calendar entity ID (e.g., 'calendar.google')
        start_date: Start date/time in ISO 8601 format (e.g., '2025-01-01T00:00:00' or '2025-01-01')
        end_date: End date/time in ISO 8601 format (e.g., '2025-01-07T23:59:59' or '2025-01-07')

    Returns:
        List of calendar event dictionaries containing:
        - summary: Event title/summary
        - start: Start date/time
        - end: End date/time
        - description: Event description (if available)
        - location: Event location (if available)
        - uid: Unique event identifier

    Example response:
        [
            {
                "summary": "Meeting",
                "start": {"dateTime": "2025-01-01T10:00:00"},
                "end": {"dateTime": "2025-01-01T11:00:00"},
                "description": "Team meeting",
                "location": "Conference Room A",
                "uid": "event_12345"
            }
        ]

    Note:
        Date formats are automatically handled. If only a date is provided,
        time is added automatically (start: 00:00:00, end: 23:59:59).
        ISO 8601 format is expected for dates.

    Best Practices:
        - Use ISO 8601 format for dates (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        - Keep date ranges reasonable (e.g., 1-4 weeks)
        - Check calendar exists before getting events
    """
    # Format dates (ISO 8601)
    # Ensure dates are properly formatted
    start_iso = start_date if "T" in start_date else f"{start_date}T00:00:00"
    end_iso = end_date if "T" in end_date else f"{end_date}T23:59:59"

    response = await _calendars_api.get(
        f"/api/calendars/{entity_id}",
        params={"start_date_time": start_iso, "end_date_time": end_iso},
    )

    return cast(list[dict[str, Any]], response)


@handle_api_errors
async def create_calendar_event(
    entity_id: str,
    summary: str,
    start: str,
    end: str,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a calendar event.

    Args:
        entity_id: The calendar entity ID (e.g., 'calendar.google')
        summary: Event title/summary (required)
        start: Start date/time in ISO 8601 format (e.g., '2025-01-01T10:00:00' or '2025-01-01')
        end: End date/time in ISO 8601 format (e.g., '2025-01-01T11:00:00' or '2025-01-01')
        description: Optional event description

    Returns:
        Response dictionary containing created event information

    Examples:
        entity_id="calendar.google", summary="Meeting", start="2025-01-01T10:00:00", end="2025-01-01T11:00:00"
        entity_id="calendar.google", summary="All Day Event", start="2025-01-01", end="2025-01-01", description="All day event"

    Note:
        Date formats are automatically handled. If only a date is provided,
        time is added automatically (start: 00:00:00, end: 23:59:59).
        The calendar must support event creation (check supported_features).

    Best Practices:
        - Use ISO 8601 format for dates
        - Check calendar supported_features before creating events
        - Use description to provide additional event details
        - Verify event was created successfully
    """
    # Format dates (ISO 8601)
    start_iso = start if "T" in start else f"{start}T00:00:00"
    end_iso = end if "T" in end else f"{end}T23:59:59"

    payload: dict[str, Any] = {
        "summary": summary,
        "dtstart": start_iso,
        "dtend": end_iso,
    }

    if description:
        payload["description"] = description

    return await _calendars_api.post(f"/api/calendars/{entity_id}/events", data=payload)
