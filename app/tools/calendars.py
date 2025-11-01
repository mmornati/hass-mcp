"""Calendars MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant calendars.
These tools are thin wrappers around the calendars API layer.
"""

import logging
from typing import Any

from app.api.calendars import (
    create_calendar_event,
    get_calendar_events,
    list_calendars,
)

logger = logging.getLogger(__name__)


async def list_calendars_tool() -> list[dict[str, Any]]:
    """
    Get a list of all calendar entities in Home Assistant.

    Returns:
        List of calendar dictionaries containing:
        - entity_id: The calendar entity ID
        - state: Current state of the calendar
        - friendly_name: Display name of the calendar
        - supported_features: Bitmask of supported features

    Examples:
        Returns all calendars with their configuration and supported features

    Note:
        Calendars are entities that support calendar functionality.
        Supported features indicate which operations are available.

    Best Practices:
        - Use this to discover available calendars
        - Check supported_features to see what operations are available
        - Use to find calendar entities before getting events
        - Check supported_features before creating events
    """
    logger.info("Getting list of calendars")
    return await list_calendars()


async def get_calendar_events_tool(
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

    Examples:
        entity_id="calendar.google", start_date="2025-01-01", end_date="2025-01-07"
        entity_id="calendar.google", start_date="2025-01-01T00:00:00", end_date="2025-01-07T23:59:59"

    Note:
        Date formats are automatically handled. If only a date is provided,
        time is added automatically (start: 00:00:00, end: 23:59:59).
        ISO 8601 format is expected for dates.

    Best Practices:
        - Use ISO 8601 format for dates (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        - Keep date ranges reasonable (e.g., 1-4 weeks)
        - Check calendar exists before getting events
    """
    logger.info(f"Getting calendar events for {entity_id} from {start_date} to {end_date}")
    return await get_calendar_events(entity_id, start_date, end_date)


async def create_calendar_event_tool(
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
        - Use to create reminders and appointments from automations
    """
    logger.info(f"Creating calendar event: {summary} on {entity_id} from {start} to {end}")
    return await create_calendar_event(entity_id, summary, start, end, description)
