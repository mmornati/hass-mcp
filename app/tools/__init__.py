"""Tools module for hass-mcp.

This module contains MCP tools organized by domain.
Tools are thin wrappers around API functions that expose
Home Assistant functionality via the Model Context Protocol.
"""

from app.tools import (
    areas,
    automations,
    devices,
    entities,
    integrations,
    logbook,
    scenes,
    scripts,
    services,
    statistics,
    system,
    templates,
)

__all__ = [
    "areas",
    "automations",
    "devices",
    "entities",
    "integrations",
    "logbook",
    "scenes",
    "scripts",
    "services",
    "statistics",
    "system",
    "templates",
]
