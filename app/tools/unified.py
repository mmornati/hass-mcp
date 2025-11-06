"""Unified MCP tools for hass-mcp.

This module provides consolidated, modular tools that replace multiple
specialized tools with unified interfaces. This reduces the total number
of tools while maintaining full functionality.

The unified tools use a type-based approach where a single tool handles
multiple item types (automations, scripts, scenes, etc.) through parameters.
"""

import logging
from typing import Any

from app.api import (
    areas,
    automations,
    backups,
    blueprints,
    calendars,
    devices,
    helpers,
    integrations,
    scenes,
    scripts,
    tags,
    zones,
)

logger = logging.getLogger(__name__)

# Mapping of item types to their API modules
ITEM_TYPE_MODULES = {
    "automation": automations,
    "script": scripts,
    "scene": scenes,
    "area": areas,
    "device": devices,
    "integration": integrations,
    "blueprint": blueprints,
    "zone": zones,
    "tag": tags,
    "helper": helpers,
    "calendar": calendars,
    "backup": backups,
}

# Mapping of item types to their list functions
LIST_FUNCTIONS = {
    "automation": automations.get_automations,
    "script": scripts.get_scripts,
    "scene": scenes.get_scenes,
    "area": areas.get_areas,
    "device": devices.get_devices,
    "integration": integrations.get_integrations,
    "blueprint": blueprints.list_blueprints,
    "zone": zones.list_zones,
    "tag": tags.list_tags,
    "helper": helpers.list_helpers,
    "calendar": calendars.list_calendars,
    "backup": backups.list_backups,
}

# Mapping of item types to their get functions
# Note: Some item types don't have individual get functions
# For those, we'll find the item from the list
GET_FUNCTIONS = {
    "automation": automations.get_automation_config,
    "script": scripts.get_script_config,
    "scene": scenes.get_scene_config,
    "area": None,  # No get_area function, will find from list
    "device": devices.get_device_details,
    "integration": integrations.get_integration_config,
    "blueprint": blueprints.get_blueprint,
    "zone": None,  # No get_zone function, will find from list
    "tag": None,  # No get_tag function, will find from list
    "helper": helpers.get_helper,
    "calendar": None,  # No get_calendar function, will find from list
    "backup": None,  # No get_backup function, will find from list
}


async def list_items(
    item_type: str,
    domain: str | None = None,
    search_query: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List items of a specific type (automations, scripts, scenes, areas, etc.).

    This unified tool replaces multiple specialized list tools:
    - list_automations, list_scripts, list_scenes, list_areas, etc.

    Args:
        item_type: Type of items to list. Options:
            - "automation": List all automations
            - "script": List all scripts
            - "scene": List all scenes
            - "area": List all areas
            - "device": List all devices (optionally filtered by domain)
            - "integration": List all integrations (optionally filtered by domain)
            - "blueprint": List all blueprints (optionally filtered by domain)
            - "zone": List all zones
            - "tag": List all tags
            - "helper": List all helpers (optionally filtered by helper_type)
            - "calendar": List all calendars
            - "backup": List all backups
        domain: Optional domain filter (for devices, integrations, blueprints)
        search_query: Optional search query to filter results
        limit: Maximum number of items to return (default: 100)

    Returns:
        List of item dictionaries

    Examples:
        item_type="automation" - List all automations
        item_type="script" - List all scripts
        item_type="device", domain="hue" - List Hue devices
        item_type="helper", search_query="temperature" - Search helpers
    """
    logger.info(
        f"Listing {item_type} items with filters: domain={domain}, search={search_query}, limit={limit}"
    )

    if item_type not in LIST_FUNCTIONS:
        return {
            "error": f"Invalid item_type: {item_type}. Valid types: {', '.join(LIST_FUNCTIONS.keys())}"
        }

    try:
        list_func = LIST_FUNCTIONS[item_type]

        # Handle different function signatures
        if item_type in ["device", "integration", "blueprint"]:
            result = await list_func(domain=domain)
        elif item_type == "helper":
            result = await list_func(helper_type=domain)  # domain is used as helper_type
        elif item_type == "backup":
            # backups.list_backups returns a dict with 'backups' key
            backup_result = await list_func()
            result = backup_result.get("backups", []) if isinstance(backup_result, dict) else []
        else:
            result = await list_func()

        # Apply search filter if provided
        if search_query and isinstance(result, list):
            search_lower = search_query.lower()
            result = [
                item
                for item in result
                if search_lower in str(item.get("entity_id", "")).lower()
                or search_lower in str(item.get("id", "")).lower()
                or search_lower in str(item.get("name", "")).lower()
                or search_lower in str(item.get("alias", "")).lower()
                or search_lower in str(item.get("friendly_name", "")).lower()
            ]

        # Apply limit
        if isinstance(result, list) and limit > 0:
            result = result[:limit]

        return result if isinstance(result, list) else [result] if result else []

    except Exception as e:
        logger.error(f"Error listing {item_type} items: {str(e)}")
        return {"error": f"Failed to list {item_type} items: {str(e)}"}


async def get_item(item_type: str, item_id: str) -> dict[str, Any]:
    """
    Get a specific item by type and ID.

    This unified tool replaces multiple specialized get tools:
    - get_automation_config, get_script, get_scene, get_area, etc.

    Args:
        item_type: Type of item. Options:
            - "automation": Get automation configuration
            - "script": Get script configuration
            - "scene": Get scene configuration
            - "area": Get area details
            - "device": Get device details
            - "integration": Get integration configuration
            - "blueprint": Get blueprint definition
            - "zone": Get zone details
            - "tag": Get tag details
            - "helper": Get helper state and configuration
            - "calendar": Get calendar details
            - "backup": Get backup details
        item_id: The item ID (without type prefix, e.g., "turn_on_lights" not "automation.turn_on_lights")

    Returns:
        Item configuration dictionary

    Examples:
        item_type="automation", item_id="turn_on_lights" - Get automation config
        item_type="script", item_id="notify" - Get script config
        item_type="scene", item_id="living_room_dim" - Get scene config
    """
    logger.info(f"Getting {item_type} item: {item_id}")

    if item_type not in GET_FUNCTIONS:
        return {
            "error": f"Invalid item_type: {item_type}. Valid types: {', '.join(GET_FUNCTIONS.keys())}"
        }

    try:
        get_func = GET_FUNCTIONS[item_type]

        # If no get function exists, find the item from the list
        if get_func is None:
            list_func = LIST_FUNCTIONS[item_type]

            # Handle different function signatures
            if item_type in ["device", "integration", "blueprint"]:
                items = await list_func(domain=None)
            elif item_type == "helper":
                items = await list_func(helper_type=None)
            elif item_type == "backup":
                backup_result = await list_func()
                items = backup_result.get("backups", []) if isinstance(backup_result, dict) else []
            else:
                items = await list_func()

            # Find the item by ID
            if isinstance(items, list):
                for item in items:
                    # Check various ID fields
                    if (
                        item.get("id") == item_id
                        or item.get("entity_id", "").replace(f"{item_type}.", "") == item_id
                        or item.get("entry_id") == item_id
                        or item.get("tag_id") == item_id
                        or item.get("slug") == item_id
                        or item.get("area_id") == item_id
                        or item.get("zone_id") == item_id
                    ):
                        return item
                return {"error": f"{item_type} item '{item_id}' not found"}
            return {"error": f"Failed to list {item_type} items"}
        return await get_func(item_id)
    except Exception as e:
        logger.error(f"Error getting {item_type} item {item_id}: {str(e)}")
        return {"error": f"Failed to get {item_type} item {item_id}: {str(e)}"}


async def manage_item(
    action: str,
    item_type: str,
    item_id: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Manage items (create, update, delete, enable, disable, etc.).

    This unified tool replaces multiple specialized management tools:
    - create_automation, update_automation, delete_automation, etc.
    - create_scene, update_scene, delete_scene, etc.
    - create_area, update_area, delete_area, etc.

    Args:
        action: Action to perform. Options:
            - "create": Create a new item (requires config)
            - "update": Update an existing item (requires item_id and config)
            - "delete": Delete an item (requires item_id)
            - "enable": Enable an item (requires item_id)
            - "disable": Disable an item (requires item_id)
            - "trigger": Trigger an item (requires item_id)
            - "activate": Activate an item (requires item_id)
            - "reload": Reload items (item_id optional)
        item_type: Type of item. Options:
            - "automation", "script", "scene", "area", "zone", "tag", "helper", "calendar", "backup"
        item_id: Item ID (required for most actions except create and reload)
        config: Configuration dictionary (required for create/update)

    Returns:
        Result dictionary

    Examples:
        action="create", item_type="automation", config={...} - Create automation
        action="update", item_type="automation", item_id="turn_on_lights", config={...} - Update automation
        action="delete", item_type="automation", item_id="turn_on_lights" - Delete automation
        action="enable", item_type="automation", item_id="turn_on_lights" - Enable automation
        action="trigger", item_type="automation", item_id="turn_on_lights" - Trigger automation
        action="activate", item_type="scene", item_id="living_room_dim" - Activate scene
    """
    logger.info(f"Managing {item_type} item: action={action}, item_id={item_id}")

    if item_type not in ITEM_TYPE_MODULES:
        return {
            "error": f"Invalid item_type: {item_type}. Valid types: {', '.join(ITEM_TYPE_MODULES.keys())}"
        }

    module = ITEM_TYPE_MODULES[item_type]

    try:
        if action == "create":
            if not config:
                return {"error": "config is required for create action"}
            if item_type == "automation":
                return await automations.create_automation(config)
            if item_type == "scene":
                return await scenes.create_scene(
                    config.get("name", ""), config.get("entity_ids", []), config.get("states")
                )
            if item_type == "area":
                return await areas.create_area(
                    config.get("name", ""), config.get("aliases"), config.get("picture")
                )
            if item_type == "zone":
                return await zones.create_zone(
                    config.get("name", ""),
                    config.get("latitude"),
                    config.get("longitude"),
                    config.get("radius"),
                    config.get("icon"),
                    config.get("passive", False),
                )
            if item_type == "tag":
                return await tags.create_tag(config.get("tag_id", ""), config.get("name", ""))
            if item_type == "backup":
                return await backups.create_backup(
                    config.get("name", ""), config.get("password"), config.get("full", True)
                )
            return {"error": f"Create action not supported for {item_type}"}

        if action == "update":
            if not item_id:
                return {"error": "item_id is required for update action"}
            if not config:
                return {"error": "config is required for update action"}
            if item_type == "automation":
                return await automations.update_automation(item_id, config)
            if item_type == "scene":
                return {"error": "Scene update not directly supported - use create/delete pattern"}
            if item_type == "area":
                return await areas.update_area(
                    item_id, config.get("name"), config.get("aliases"), config.get("picture")
                )
            if item_type == "zone":
                return await zones.update_zone(
                    item_id,
                    config.get("name"),
                    config.get("latitude"),
                    config.get("longitude"),
                    config.get("radius"),
                    config.get("icon"),
                )
            return {"error": f"Update action not supported for {item_type}"}

        if action == "delete":
            if not item_id:
                return {"error": "item_id is required for delete action"}
            if item_type == "automation":
                return await automations.delete_automation(item_id)
            if item_type == "scene":
                return {"error": "Scene deletion not directly supported via API"}
            if item_type == "area":
                return await areas.delete_area(item_id)
            if item_type == "zone":
                return await zones.delete_zone(item_id)
            if item_type == "tag":
                return await tags.delete_tag(item_id)
            if item_type == "backup":
                return await backups.delete_backup(item_id)
            return {"error": f"Delete action not supported for {item_type}"}

        if action == "enable":
            if not item_id:
                return {"error": "item_id is required for enable action"}
            if item_type == "automation":
                return await automations.enable_automation(item_id)
            return {"error": f"Enable action not supported for {item_type}"}

        if action == "disable":
            if not item_id:
                return {"error": "item_id is required for disable action"}
            if item_type == "automation":
                return await automations.disable_automation(item_id)
            return {"error": f"Disable action not supported for {item_type}"}

        if action == "trigger":
            if not item_id:
                return {"error": "item_id is required for trigger action"}
            if item_type == "automation":
                return await automations.trigger_automation(item_id)
            return {"error": f"Trigger action not supported for {item_type}"}

        if action == "activate":
            if not item_id:
                return {"error": "item_id is required for activate action"}
            if item_type == "scene":
                return await scenes.activate_scene(item_id)
            return {"error": f"Activate action not supported for {item_type}"}

        if action == "reload":
            if item_type == "script":
                return await scripts.reload_scripts()
            if item_type == "scene":
                return await scenes.reload_scenes()
            return {"error": f"Reload action not supported for {item_type}"}

        return {
            "error": f"Invalid action: {action}. Valid actions: create, update, delete, enable, disable, trigger, activate, reload"
        }

    except Exception as e:
        logger.error(f"Error managing {item_type} item: {str(e)}")
        return {"error": f"Failed to {action} {item_type} item: {str(e)}"}
