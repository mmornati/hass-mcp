"""Tools module for hass-mcp.

This module contains MCP tools organized by domain.
Tools are thin wrappers around API functions that expose
Home Assistant functionality via the Model Context Protocol.
"""

from app.tools import (
    areas,
    automations,
    blueprints,
    calendars,
    devices,
    diagnostics,
    entities,
    events,
    helpers,
    integrations,
    logbook,
    notifications,
    scenes,
    scripts,
    services,
    statistics,
    system,
    templates,
    zones,
)

__all__ = [
    "areas",
    "automations",
    "blueprints",
    "calendars",
    "devices",
    "diagnostics",
    "entities",
    "events",
    "helpers",
    "integrations",
    "logbook",
    "notifications",
    "scenes",
    "scripts",
    "services",
    "statistics",
    "system",
    "templates",
    "zones",
]
