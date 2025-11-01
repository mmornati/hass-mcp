"""API layer module for hass-mcp.

This module provides the API layer that interfaces with Home Assistant's REST API.
It's organized by domain (entities, automations, scripts, etc.) for better maintainability.
"""

# Re-export main modules for easy importing
from app.api.base import BaseAPI
from app.api.entities import (
    filter_fields,
    get_all_entity_states,
    get_entities,
    get_entity_history,
    get_entity_state,
)

__all__ = [
    "BaseAPI",
    "filter_fields",
    "get_all_entity_states",
    "get_entities",
    "get_entity_history",
    "get_entity_state",
]
