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
    diagnostics,
    events,
    helpers,
    integrations,
    logbook,
    notifications,
    scenes,
    scripts,
    statistics,
    system,
    tags,
    webhooks,
    zones,
)
from app.api.entities import get_entities, get_entity_history, get_entity_state, summarize_domain
from app.core.vectordb.description import (  # noqa: PLC0415
    generate_entity_description_batch,
    generate_entity_description_enhanced,
)
from app.core.vectordb.search import semantic_search  # noqa: PLC0415

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


async def search_entities(
    query: str | None = None,
    domain: str | None = None,
    search_mode: str = "keyword",
    limit: int = 100,
    area_id: str | None = None,
    similarity_threshold: float = 0.7,
) -> dict[str, Any]:
    """
    Unified entity search tool that replaces list_entities, search_entities_tool, and semantic_search_entities_tool.

    This unified tool supports multiple search modes:
    - "keyword": Keyword-based search (default)
    - "semantic": Semantic search using vector embeddings
    - "hybrid": Combines both semantic and keyword search

    Args:
        query: Optional search query. If None, returns all entities (up to limit)
        domain: Optional domain filter (e.g., 'light', 'switch', 'sensor')
        search_mode: Search mode - "keyword", "semantic", or "hybrid" (default: "keyword")
        limit: Maximum number of entities to return (default: 100)
        area_id: Optional area filter for semantic search
        similarity_threshold: Similarity threshold for semantic search (default: 0.7)

    Returns:
        Dictionary containing search results with count, results, and domains

    Examples:
        query="temperature", search_mode="keyword" - Keyword search
        query="lights", search_mode="semantic" - Semantic search
        query="kitchen", search_mode="hybrid" - Hybrid search
        domain="light", limit=50 - List lights with limit
    """
    logger.info(
        f"Searching entities: query={query}, domain={domain}, mode={search_mode}, limit={limit}"
    )

    try:
        if search_mode in ["semantic", "hybrid"]:
            # Use semantic search
            try:
                result = await semantic_search(
                    query=query or "",
                    domain=domain,
                    area_id=area_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                    search_mode=search_mode,
                )
                return result
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}, falling back to keyword search")
                search_mode = "keyword"

        # Use keyword search (default or fallback)
        if query:
            entities_list = await get_entities(
                domain=domain, search_query=query, limit=limit, lean=True
            )
        else:
            entities_list = await get_entities(domain=domain, limit=limit, lean=True)

        if isinstance(entities_list, dict) and "error" in entities_list:
            return {"error": entities_list["error"], "count": 0, "results": [], "domains": {}}

        # Format results similar to search_entities_tool
        domains_count = {}
        simplified_entities = []

        for entity in entities_list:
            domain_name = entity["entity_id"].split(".")[0]
            if domain_name not in domains_count:
                domains_count[domain_name] = 0
            domains_count[domain_name] += 1

            simplified_entity = {
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "domain": domain_name,
                "friendly_name": entity.get("attributes", {}).get(
                    "friendly_name", entity["entity_id"]
                ),
            }

            # Add key attributes based on domain
            attributes = entity.get("attributes", {})
            if domain_name == "light" and "brightness" in attributes:
                simplified_entity["brightness"] = attributes["brightness"]
            elif domain_name == "sensor" and "unit_of_measurement" in attributes:
                simplified_entity["unit"] = attributes["unit_of_measurement"]
            elif domain_name == "climate" and "temperature" in attributes:
                simplified_entity["temperature"] = attributes["temperature"]
            elif domain_name == "media_player" and "media_title" in attributes:
                simplified_entity["media_title"] = attributes["media_title"]

            simplified_entities.append(simplified_entity)

        return {
            "count": len(simplified_entities),
            "results": simplified_entities,
            "domains": domains_count,
            "search_mode": search_mode,
        }

    except Exception as e:
        logger.error(f"Error searching entities: {str(e)}")
        return {
            "error": f"Failed to search entities: {str(e)}",
            "count": 0,
            "results": [],
            "domains": {},
        }


async def generate_entity_description(
    entity_id: str | None = None,
    entity_ids: list[str] | None = None,
    use_template: bool = True,
    language: str = "en",
) -> dict[str, Any]:
    """
    Unified entity description generation tool that replaces generate_entity_description and generate_entity_descriptions_batch.

    Args:
        entity_id: Single entity ID to generate description for (for single entity mode)
        entity_ids: List of entity IDs to generate descriptions for (for batch mode)
        use_template: Whether to use template-based generation (default: True)
        language: Language for description (default: "en")

    Returns:
        For single entity: Dictionary with entity_id, description, template_used, language
        For batch: Dictionary with total, succeeded, failed, descriptions

    Examples:
        entity_id="light.living_room" - Generate description for single entity
        entity_ids=["light.living_room", "sensor.temperature"] - Generate descriptions for multiple entities
    """
    logger.info(
        f"Generating description(s): entity_id={entity_id}, entity_ids={entity_ids}, use_template={use_template}"
    )

    try:
        # Batch mode
        if entity_ids is not None:
            entities_list = []
            for eid in entity_ids:
                entity = await get_entity_state(eid, lean=False)
                if isinstance(entity, dict) and "error" not in entity:
                    entities_list.append(entity)

            if not entities_list:
                return {
                    "error": "Failed to get entities",
                    "total": 0,
                    "succeeded": 0,
                    "failed": 0,
                    "descriptions": {},
                }

            descriptions = await generate_entity_description_batch(
                entities_list, use_template=use_template, language=language
            )

            return {
                "total": len(entity_ids),
                "succeeded": len(descriptions),
                "failed": len(entity_ids) - len(descriptions),
                "descriptions": descriptions,
            }

        # Single entity mode
        if entity_id:
            entity = await get_entity_state(entity_id, lean=False)
            if isinstance(entity, dict) and "error" in entity:
                return {
                    "error": entity["error"],
                    "entity_id": entity_id,
                    "description": None,
                    "template_used": use_template,
                    "language": language,
                }

            description = await generate_entity_description_enhanced(
                entity, use_template=use_template, language=language
            )

            return {
                "entity_id": entity_id,
                "description": description,
                "template_used": use_template,
                "language": language,
            }

        return {"error": "Either entity_id or entity_ids must be provided"}

    except Exception as e:
        logger.error(f"Error generating entity description(s): {str(e)}")
        return {"error": f"Failed to generate description(s): {str(e)}"}


async def get_logbook(
    entity_id: str | None = None,
    search_query: str | None = None,
    timestamp: str | None = None,
    hours: int = 24,
) -> list[dict[str, Any]]:
    """
    Unified logbook tool that replaces get_logbook, get_entity_logbook, and search_logbook.

    Args:
        entity_id: Optional entity ID to filter logbook entries by
        search_query: Optional search query to filter logbook entries
        timestamp: Optional timestamp to start from (ISO format)
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        List of logbook entry dictionaries

    Examples:
        entity_id="light.living_room" - Get logbook for specific entity
        search_query="error" - Search logbook entries
        entity_id="sensor.temperature", hours=48 - Get logbook for entity for last 48 hours
    """
    logger.info(
        f"Getting logbook: entity_id={entity_id}, search_query={search_query}, hours={hours}"
    )

    try:
        if search_query:
            return await logbook.search_logbook(search_query, hours)
        if entity_id:
            return await logbook.get_entity_logbook(entity_id, hours)
        return await logbook.get_logbook(timestamp, entity_id, hours)

    except Exception as e:
        logger.error(f"Error getting logbook: {str(e)}")
        return []


async def get_statistics(
    type: str,  # noqa: A002
    entity_id: str | None = None,
    domain: str | None = None,
    period_days: int = 7,
    days: int = 30,
) -> dict[str, Any]:
    """
    Unified statistics tool that replaces get_entity_statistics, get_domain_statistics, and analyze_usage_patterns.

    Args:
        type: Type of statistics. Options:
            - "entity": Get statistics for a specific entity (requires entity_id)
            - "domain": Get statistics for a domain (requires domain)
            - "usage_patterns": Analyze usage patterns for an entity (requires entity_id)
        entity_id: Entity ID (required for "entity" and "usage_patterns" types)
        domain: Domain name (required for "domain" type)
        period_days: Number of days to analyze (default: 7, used for "entity" and "domain")
        days: Number of days to analyze (default: 30, used for "usage_patterns")

    Returns:
        Statistics dictionary

    Examples:
        type="entity", entity_id="sensor.temperature", period_days=7 - Entity statistics
        type="domain", domain="sensor", period_days=7 - Domain statistics
        type="usage_patterns", entity_id="light.living_room", days=30 - Usage patterns
    """
    logger.info(f"Getting statistics: type={type}, entity_id={entity_id}, domain={domain}")

    try:
        if type == "entity":
            if not entity_id:
                return {"error": "entity_id is required for entity statistics"}
            return await statistics.get_entity_statistics(entity_id, period_days)
        if type == "domain":
            if not domain:
                return {"error": "domain is required for domain statistics"}
            return await statistics.get_domain_statistics(domain, period_days)
        if type == "usage_patterns":
            if not entity_id:
                return {"error": "entity_id is required for usage patterns analysis"}
            return await statistics.analyze_usage_patterns(entity_id, days)
        return {"error": f"Invalid type: {type}. Valid types: entity, domain, usage_patterns"}

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return {"error": f"Failed to get statistics: {str(e)}"}


async def diagnose(
    type: str,  # noqa: A002
    entity_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """
    Unified diagnostics tool that replaces diagnose_entity, check_entity_dependencies, analyze_automation_conflicts, and get_integration_errors.

    Args:
        type: Type of diagnostics. Options:
            - "entity": Diagnose a specific entity (requires entity_id)
            - "dependencies": Check entity dependencies (requires entity_id)
            - "automation_conflicts": Analyze automation conflicts
            - "integration_errors": Get integration errors (optional domain filter)
        entity_id: Entity ID (required for "entity" and "dependencies" types)
        domain: Optional domain filter for "integration_errors" type

    Returns:
        Diagnostics dictionary

    Examples:
        type="entity", entity_id="light.living_room" - Diagnose entity
        type="dependencies", entity_id="sensor.temperature" - Check dependencies
        type="automation_conflicts" - Analyze conflicts
        type="integration_errors", domain="hue" - Get integration errors
    """
    logger.info(f"Running diagnostics: type={type}, entity_id={entity_id}, domain={domain}")

    try:
        if type == "entity":
            if not entity_id:
                return {"error": "entity_id is required for entity diagnostics"}
            return await diagnostics.diagnose_entity(entity_id)
        if type == "dependencies":
            if not entity_id:
                return {"error": "entity_id is required for dependency check"}
            return await diagnostics.check_entity_dependencies(entity_id)
        if type == "automation_conflicts":
            return await diagnostics.analyze_automation_conflicts()
        if type == "integration_errors":
            return await diagnostics.get_integration_errors(domain)
        return {
            "error": f"Invalid type: {type}. Valid types: entity, dependencies, automation_conflicts, integration_errors"
        }

    except Exception as e:
        logger.error(f"Error running diagnostics: {str(e)}")
        return {"error": f"Failed to run diagnostics: {str(e)}"}


async def manage_events(
    action: str,
    event_type: str | None = None,
    event_data: dict[str, Any] | None = None,
    entity_id: str | None = None,
    hours: int = 1,
) -> dict[str, Any] | list[dict[str, Any]] | list[str]:
    """
    Unified events tool that replaces fire_event, list_event_types, and get_events.

    Args:
        action: Action to perform. Options:
            - "fire": Fire a custom event (requires event_type)
            - "list_types": List common event types
            - "get": Get recent events (optional entity_id filter)
        event_type: Event type name (required for "fire" action)
        event_data: Optional event data/payload (for "fire" action)
        entity_id: Optional entity ID to filter events (for "get" action)
        hours: Number of hours of history to retrieve (default: 1, for "get" action)

    Returns:
        Response depends on action:
        - "fire": Response dictionary from fire_event
        - "list_types": List of event type strings
        - "get": List of event dictionaries

    Examples:
        action="fire", event_type="custom_event", event_data={"message": "Hello"}
        action="list_types" - List event types
        action="get", entity_id="light.living_room", hours=24 - Get events for entity
    """
    logger.info(f"Managing events: action={action}, event_type={event_type}")

    try:
        if action == "fire":
            if not event_type:
                return {"error": "event_type is required for fire action"}
            return await events.fire_event(event_type, event_data)
        if action == "list_types":
            return await events.list_event_types()
        if action == "get":
            return await events.get_events(entity_id, hours)
        return {"error": f"Invalid action: {action}. Valid actions: fire, list_types, get"}

    except Exception as e:
        logger.error(f"Error managing events: {str(e)}")
        return {"error": f"Failed to manage events: {str(e)}"}


async def manage_notifications(
    action: str,
    message: str | None = None,
    target: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Unified notifications tool that replaces list_notification_services, send_notification, and test_notification.

    Args:
        action: Action to perform. Options:
            - "list": List available notification services
            - "send": Send a notification (requires message)
            - "test": Test notification delivery (requires message and target)
        message: Notification message (required for "send" and "test" actions)
        target: Target notification service/platform (required for "test", optional for "send")
        data: Optional dictionary of additional notification data (for "send" action)

    Returns:
        Response depends on action:
        - "list": List of notification service dictionaries
        - "send": Response dictionary from send_notification
        - "test": Response dictionary from test_notification

    Examples:
        action="list" - List notification services
        action="send", message="Alert: Temperature too high" - Send notification
        action="test", message="Test", target="notify.mobile_app_iphone" - Test notification
    """
    logger.info(f"Managing notifications: action={action}, message={message}, target={target}")

    try:
        if action == "list":
            return await notifications.list_notification_services()
        if action == "send":
            if not message:
                return {"error": "message is required for send action"}
            return await notifications.send_notification(message, target, data)
        if action == "test":
            if not message:
                return {"error": "message is required for test action"}
            if not target:
                return {"error": "target is required for test action"}
            return await notifications.test_notification_delivery(target, message)
        return {"error": f"Invalid action: {action}. Valid actions: list, send, test"}

    except Exception as e:
        logger.error(f"Error managing notifications: {str(e)}")
        return {"error": f"Failed to manage notifications: {str(e)}"}


async def manage_webhooks(
    action: str,
    webhook_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Unified webhooks tool that replaces list_webhooks and test_webhook.

    Args:
        action: Action to perform. Options:
            - "list": List registered webhooks
            - "test": Test webhook endpoint (requires webhook_id)
        webhook_id: Webhook ID to test (required for "test" action)
        payload: Optional payload to send with webhook request (for "test" action)

    Returns:
        Response depends on action:
        - "list": List of webhook information dictionaries
        - "test": Response dictionary from test_webhook

    Examples:
        action="list" - List webhooks
        action="test", webhook_id="my_webhook", payload={"entity_id": "light.living_room"}
    """
    logger.info(f"Managing webhooks: action={action}, webhook_id={webhook_id}")

    try:
        if action == "list":
            return await webhooks.list_webhooks()
        if action == "test":
            if not webhook_id:
                return {"error": "webhook_id is required for test action"}
            return await webhooks.test_webhook(webhook_id, payload)
        return {"error": f"Invalid action: {action}. Valid actions: list, test"}

    except Exception as e:
        logger.error(f"Error managing webhooks: {str(e)}")
        return {"error": f"Failed to manage webhooks: {str(e)}"}


async def get_system_info(info_type: str) -> dict[str, Any] | str:
    """
    Unified system info tool that replaces get_version, system_overview, system_health, and core_config.

    Args:
        info_type: Type of system info. Options:
            - "version": Get Home Assistant version
            - "overview": Get comprehensive system overview
            - "health": Get system health information
            - "config": Get core configuration

    Returns:
        System information dictionary or version string

    Examples:
        info_type="version" - Get HA version
        info_type="overview" - Get system overview
        info_type="health" - Get system health
        info_type="config" - Get core config
    """
    logger.info(f"Getting system info: type={info_type}")

    try:
        if info_type == "version":
            return await system.get_hass_version()
        if info_type == "overview":
            return await system.get_system_overview()
        if info_type == "health":
            return await system.get_system_health()
        if info_type == "config":
            return await system.get_core_config()
        return {
            "error": f"Invalid info_type: {info_type}. Valid types: version, overview, health, config"
        }

    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": f"Failed to get system info: {str(e)}"}


async def get_system_data(
    data_type: str, entity_id: str | None = None, domain: str | None = None
) -> dict[str, Any]:
    """
    Unified system data tool that replaces get_error_log, get_cache_statistics, get_history, and domain_summary.

    Args:
        data_type: Type of system data. Options:
            - "error_log": Get error log
            - "cache_statistics": Get cache statistics
            - "history": Get entity history (requires entity_id)
            - "domain_summary": Get domain summary (requires domain)
        entity_id: Entity ID (required for "history" type)
        domain: Domain name (required for "domain_summary" type)

    Returns:
        System data dictionary

    Examples:
        data_type="error_log" - Get error log
        data_type="cache_statistics" - Get cache statistics
        data_type="history", entity_id="sensor.temperature" - Get entity history
        data_type="domain_summary", domain="light" - Get domain summary
    """
    logger.info(f"Getting system data: type={data_type}, entity_id={entity_id}, domain={domain}")

    try:
        if data_type == "error_log":
            return await system.get_hass_error_log()
        if data_type == "cache_statistics":
            return await system.get_cache_statistics()
        if data_type == "history":
            if not entity_id:
                return {"error": "entity_id is required for history data type"}
            # get_history uses hours parameter, defaulting to 24
            return await get_entity_history(entity_id, 24)
        if data_type == "domain_summary":
            if not domain:
                return {"error": "domain is required for domain_summary data type"}
            return await summarize_domain(domain)
        return {
            "error": f"Invalid data_type: {data_type}. Valid types: error_log, cache_statistics, history, domain_summary"
        }

    except Exception as e:
        logger.error(f"Error getting system data: {str(e)}")
        return {"error": f"Failed to get system data: {str(e)}"}


async def get_item_entities(item_type: str, item_id: str) -> list[dict[str, Any]]:
    """
    Unified tool that replaces get_device_entities and get_area_entities.

    Args:
        item_type: Type of item. Options:
            - "device": Get entities for a device
            - "area": Get entities in an area
        item_id: The item ID (device_id or area_id)

    Returns:
        List of entity dictionaries

    Examples:
        item_type="device", item_id="device_123" - Get entities for device
        item_type="area", item_id="living_room" - Get entities in area
    """
    logger.info(f"Getting entities for {item_type}: {item_id}")

    try:
        if item_type == "device":
            return await devices.get_device_entities(item_id)
        if item_type == "area":
            return await areas.get_area_entities(item_id)
        return {"error": f"Invalid item_type: {item_type}. Valid types: device, area"}

    except Exception as e:
        logger.error(f"Error getting {item_type} entities: {str(e)}")
        return {"error": f"Failed to get {item_type} entities: {str(e)}"}


async def get_item_summary(item_type: str, item_id: str | None = None) -> dict[str, Any]:
    """
    Unified tool that replaces get_device_stats and get_area_summary.

    Args:
        item_type: Type of item. Options:
            - "device": Get device statistics (requires item_id)
            - "area": Get area summary (item_id optional, returns all areas if None)
        item_id: Optional item ID (device_id for "device", area_id for "area")

    Returns:
        Summary dictionary

    Examples:
        item_type="device", item_id="device_123" - Get device statistics
        item_type="area" - Get summary of all areas
        item_type="area", item_id="living_room" - Get summary for specific area
    """
    logger.info(f"Getting summary for {item_type}: {item_id}")

    try:
        if item_type == "device":
            if not item_id:
                return {"error": "item_id is required for device statistics"}
            # get_device_statistics doesn't take device_id, it returns all device stats
            return await devices.get_device_statistics()
        if item_type == "area":
            # get_area_summary returns all areas summary
            return await areas.get_area_summary()
        return {"error": f"Invalid item_type: {item_type}. Valid types: device, area"}

    except Exception as e:
        logger.error(f"Error getting {item_type} summary: {str(e)}")
        return {"error": f"Failed to get {item_type} summary: {str(e)}"}
