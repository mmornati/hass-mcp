"""API layer module for hass-mcp.

This module provides the API layer that interfaces with Home Assistant's REST API.
It's organized by domain (entities, automations, scripts, etc.) for better maintainability.
"""

# Re-export main modules for easy importing
from app.api.areas import (
    create_area,
    delete_area,
    get_area_entities,
    get_area_summary,
    get_areas,
    update_area,
)
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
from app.api.devices import (
    get_device_details,
    get_device_entities,
    get_device_statistics,
    get_devices,
)
from app.api.entities import (
    filter_fields,
    get_all_entity_states,
    get_entities,
    get_entity_history,
    get_entity_state,
)
from app.api.integrations import (
    get_integration_config,
    get_integrations,
    reload_integration,
)
from app.api.scenes import (
    activate_scene,
    create_scene,
    get_scene_config,
    get_scenes,
    reload_scenes,
)
from app.api.scripts import (
    get_script_config,
    get_scripts,
    reload_scripts,
    run_script,
)
from app.api.services import call_service
from app.api.system import (
    get_core_config,
    get_hass_error_log,
    get_hass_version,
    get_system_health,
    get_system_overview,
    restart_home_assistant,
)
from app.api.templates import test_template

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
    "get_scripts",
    "get_script_config",
    "run_script",
    "reload_scripts",
    "get_devices",
    "get_device_details",
    "get_device_entities",
    "get_device_statistics",
    "get_areas",
    "get_area_entities",
    "create_area",
    "update_area",
    "delete_area",
    "get_area_summary",
    "get_scenes",
    "get_scene_config",
    "create_scene",
    "activate_scene",
    "reload_scenes",
    "get_integrations",
    "get_integration_config",
    "reload_integration",
    "get_hass_version",
    "get_system_overview",
    "get_system_health",
    "get_hass_error_log",
    "get_core_config",
    "restart_home_assistant",
    "call_service",
    "test_template",
]
