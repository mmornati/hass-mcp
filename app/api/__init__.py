"""API layer module for hass-mcp.

This module provides the API layer that interfaces with Home Assistant's REST API.
It's organized by domain (entities, automations, scripts, etc.) for better maintainability.
"""

# Re-export main modules for easy importing
from app.api.automations import (
    create_automation,
    delete_automation,
    disable_automation,
    enable_automation,
    get_automation_config,
    get_automation_execution_log,
    get_automations,
    reload_automations,
    trigger_automation,
    update_automation,
    validate_automation_config,
)
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
    "get_automations",
    "reload_automations",
    "get_automation_config",
    "create_automation",
    "update_automation",
    "delete_automation",
    "enable_automation",
    "disable_automation",
    "trigger_automation",
    "get_automation_execution_log",
    "validate_automation_config",
]
