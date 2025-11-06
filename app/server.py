import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create an MCP server
from mcp.server.fastmcp import FastMCP

from app.api.entities import (
    get_entities,
    get_entity_state,
)
from app.core import async_handler

mcp = FastMCP("Hass-MCP")

# Import and register tools from tools modules
# Tools are registered manually to avoid circular imports
from app.tools import (
    areas,
    automations,
    backups,
    blueprints,
    calendars,
    devices,
    diagnostics,
    entities,
    entity_suggestions,
    events,
    helpers,
    integrations,
    logbook,
    notifications,
    query_processing,
    scenes,
    scripts,
    services,
    statistics,
    system,
    tags,
    templates,
    unified,
    webhooks,
    zones,
)  # noqa: E402

# Register entity tools with MCP instance
mcp.tool()(async_handler("get_entity")(entities.get_entity))
mcp.tool()(async_handler("entity_action")(entities.entity_action))
mcp.tool()(async_handler("search_entities")(unified.search_entities))
mcp.tool()(async_handler("get_entity_suggestions")(entity_suggestions.get_entity_suggestions_tool))

# Register query processing tools with MCP instance
mcp.tool()(
    async_handler("process_natural_language_query")(query_processing.process_natural_language_query)
)

# Register unified entity description tool (replaces generate_entity_description and generate_entity_descriptions_batch)
mcp.tool()(async_handler("generate_entity_description")(unified.generate_entity_description))

# Register unified tools (replaces multiple specialized tools)
mcp.tool()(async_handler("list_items")(unified.list_items))
mcp.tool()(async_handler("get_item")(unified.get_item))
mcp.tool()(async_handler("manage_item")(unified.manage_item))

# Register specialized automation tools (not replaced by unified tools)
mcp.tool()(
    async_handler("get_automation_execution_log")(automations.get_automation_execution_log_tool)
)
mcp.tool()(async_handler("validate_automation_config")(automations.validate_automation_config_tool))

# Register specialized script tools (run_script not replaced by unified tools)
mcp.tool()(async_handler("run_script")(scripts.run_script_tool))

# Register unified device/area tools (replaces get_device_entities, get_device_stats, get_area_entities, get_area_summary)
mcp.tool()(async_handler("get_item_entities")(unified.get_item_entities))
mcp.tool()(async_handler("get_item_summary")(unified.get_item_summary))

# Scene tools are now handled by unified tools (list_items, get_item, manage_item)

# Register specialized integration tools (reload not replaced by unified tools)
mcp.tool()(async_handler("reload_integration")(integrations.reload_integration_tool))

# Register unified system tools (replaces get_version, system_overview, system_health, core_config, get_error_log, get_cache_statistics, get_history, domain_summary)
mcp.tool()(async_handler("get_system_info")(unified.get_system_info))
mcp.tool()(async_handler("get_system_data")(unified.get_system_data))
# Keep restart_ha as separate tool (critical action)
mcp.tool()(async_handler("restart_ha")(system.restart_ha))

# Register service tools with MCP instance
mcp.tool()(async_handler("call_service")(services.call_service_tool))

# Register template tools with MCP instance
mcp.tool()(async_handler("test_template")(templates.test_template_tool))

# Register unified logbook tool (replaces get_logbook, get_entity_logbook, search_logbook)
mcp.tool()(async_handler("get_logbook")(unified.get_logbook))

# Register unified statistics tool (replaces get_entity_statistics, get_domain_statistics, analyze_usage_patterns)
mcp.tool()(async_handler("get_statistics")(unified.get_statistics))

# Register unified diagnostics tool (replaces diagnose_entity, check_entity_dependencies, analyze_automation_conflicts, get_integration_errors)
mcp.tool()(async_handler("diagnose")(unified.diagnose))

# Register specialized blueprint tools (not replaced by unified tools)
mcp.tool()(async_handler("import_blueprint")(blueprints.import_blueprint_tool))
mcp.tool()(
    async_handler("create_automation_from_blueprint")(
        blueprints.create_automation_from_blueprint_tool
    )
)

# Zone tools are now handled by unified tools (list_items, get_item, manage_item)

# Register unified events tool (replaces fire_event, list_event_types, get_events)
mcp.tool()(async_handler("manage_events")(unified.manage_events))

# Register unified notifications tool (replaces list_notification_services, send_notification, test_notification)
mcp.tool()(async_handler("manage_notifications")(unified.manage_notifications))

# Register specialized calendar tools (not replaced by unified tools)
mcp.tool()(async_handler("get_calendar_events")(calendars.get_calendar_events_tool))
mcp.tool()(async_handler("create_calendar_event")(calendars.create_calendar_event_tool))

# Register specialized helper tools (update_helper not replaced by unified tools)
mcp.tool()(async_handler("update_helper")(helpers.update_helper_tool))

# Register specialized tag tools (not replaced by unified tools)
mcp.tool()(async_handler("get_tag_automations")(tags.get_tag_automations_tool))

# Register unified webhooks tool (replaces list_webhooks, test_webhook)
mcp.tool()(async_handler("manage_webhooks")(unified.manage_webhooks))

# Register specialized backup tools (restore not replaced by unified tools)
mcp.tool()(async_handler("restore_backup")(backups.restore_backup_tool))

# Re-export all tools for backward compatibility
# This allows tests and other code to import them from app.server
get_entity = entities.get_entity
entity_action = entities.entity_action
list_entities = entities.list_entities
search_entities_tool = entities.search_entities_tool
list_automations = automations.list_automations
get_automation_config_tool = automations.get_automation_config_tool
create_automation_tool = automations.create_automation_tool
update_automation_tool = automations.update_automation_tool
delete_automation_tool = automations.delete_automation_tool
enable_automation_tool = automations.enable_automation_tool
disable_automation_tool = automations.disable_automation_tool
trigger_automation_tool = automations.trigger_automation_tool
get_automation_execution_log_tool = automations.get_automation_execution_log_tool
validate_automation_config_tool = automations.validate_automation_config_tool
list_scripts_tool = scripts.list_scripts_tool
get_script_tool = scripts.get_script_tool
run_script_tool = scripts.run_script_tool
reload_scripts_tool = scripts.reload_scripts_tool
list_devices_tool = devices.list_devices_tool
get_device_tool = devices.get_device_tool
get_device_entities_tool = devices.get_device_entities_tool
get_device_stats_tool = devices.get_device_stats_tool
list_areas_tool = areas.list_areas_tool
get_area_entities_tool = areas.get_area_entities_tool
create_area_tool = areas.create_area_tool
update_area_tool = areas.update_area_tool
delete_area_tool = areas.delete_area_tool
get_area_summary_tool = areas.get_area_summary_tool
list_scenes_tool = scenes.list_scenes_tool
get_scene_tool = scenes.get_scene_tool
create_scene_tool = scenes.create_scene_tool
activate_scene_tool = scenes.activate_scene_tool
reload_scenes_tool = scenes.reload_scenes_tool
list_integrations = integrations.list_integrations
get_integration_config_tool = integrations.get_integration_config_tool
reload_integration_tool = integrations.reload_integration_tool
get_version = system.get_version
system_overview = system.system_overview
get_error_log = system.get_error_log
system_health = system.system_health
core_config = system.core_config
restart_ha = system.restart_ha
get_history = system.get_history
domain_summary_tool = system.domain_summary_tool
get_cache_statistics_tool = system.get_cache_statistics_tool
call_service_tool = services.call_service_tool
test_template_tool = templates.test_template_tool
get_logbook_tool = logbook.get_logbook_tool
get_entity_logbook_tool = logbook.get_entity_logbook_tool
search_logbook_tool = logbook.search_logbook_tool
get_entity_statistics_tool = statistics.get_entity_statistics_tool
get_domain_statistics_tool = statistics.get_domain_statistics_tool
analyze_usage_patterns_tool = statistics.analyze_usage_patterns_tool
diagnose_entity_tool = diagnostics.diagnose_entity_tool
check_entity_dependencies_tool = diagnostics.check_entity_dependencies_tool
analyze_automation_conflicts_tool = diagnostics.analyze_automation_conflicts_tool
get_integration_errors_tool = diagnostics.get_integration_errors_tool
list_blueprints_tool = blueprints.list_blueprints_tool
get_blueprint_tool = blueprints.get_blueprint_tool
import_blueprint_tool = blueprints.import_blueprint_tool
create_automation_from_blueprint_tool = blueprints.create_automation_from_blueprint_tool
list_zones_tool = zones.list_zones_tool
create_zone_tool = zones.create_zone_tool
update_zone_tool = zones.update_zone_tool
delete_zone_tool = zones.delete_zone_tool
fire_event_tool = events.fire_event_tool
list_event_types_tool = events.list_event_types_tool
get_events_tool = events.get_events_tool
list_notification_services_tool = notifications.list_notification_services_tool
send_notification_tool = notifications.send_notification_tool
test_notification_tool = notifications.test_notification_tool
list_calendars_tool = calendars.list_calendars_tool
get_calendar_events_tool = calendars.get_calendar_events_tool
create_calendar_event_tool = calendars.create_calendar_event_tool
list_helpers_tool = helpers.list_helpers_tool
get_helper_tool = helpers.get_helper_tool
update_helper_tool = helpers.update_helper_tool
list_tags_tool = tags.list_tags_tool
create_tag_tool = tags.create_tag_tool
delete_tag_tool = tags.delete_tag_tool
get_tag_automations_tool = tags.get_tag_automations_tool
list_webhooks_tool = webhooks.list_webhooks_tool
test_webhook_tool = webhooks.test_webhook_tool
list_backups_tool = backups.list_backups_tool
create_backup_tool = backups.create_backup_tool
restore_backup_tool = backups.restore_backup_tool
delete_backup_tool = backups.delete_backup_tool


# All tools are now in app.tools.* modules
# They are registered above after creating the mcp instance


# Entity tools are now in app.tools.entities module
# They are registered above after creating the mcp instance


@mcp.resource("hass://entities/{entity_id}")
@async_handler("get_entity_resource")
async def get_entity_resource(entity_id: str) -> str:
    """
    Get the state of a Home Assistant entity as a resource

    This endpoint provides a standard view with common entity information.
    For comprehensive attribute details, use the /detailed endpoint.

    Args:
        entity_id: The entity ID to get information for
    """
    logger.info(f"Getting entity resource: {entity_id}")

    # Get the entity state with caching (using lean format for token efficiency)
    state = await get_entity_state(entity_id, lean=True)

    # Check if there was an error
    if "error" in state:
        return f"# Entity: {entity_id}\n\nError retrieving entity: {state['error']}"

    # Format the entity as markdown
    result = f"# Entity: {entity_id}\n\n"

    # Get friendly name if available
    friendly_name = state.get("attributes", {}).get("friendly_name")
    if friendly_name and friendly_name != entity_id:
        result += f"**Name**: {friendly_name}\n\n"

    # Add state
    result += f"**State**: {state.get('state')}\n\n"

    # Add domain info
    domain = entity_id.split(".")[0]
    result += f"**Domain**: {domain}\n\n"

    # Add key attributes based on domain type
    attributes = state.get("attributes", {})

    # Add a curated list of important attributes
    important_attrs = []

    # Common attributes across many domains
    common_attrs = ["device_class", "unit_of_measurement", "friendly_name"]

    # Domain-specific important attributes
    if domain == "light":
        important_attrs = [
            "brightness",
            "color_temp",
            "rgb_color",
            "supported_features",
            "supported_color_modes",
        ]
    elif domain == "sensor":
        important_attrs = ["unit_of_measurement", "device_class", "state_class"]
    elif domain == "climate":
        important_attrs = [
            "hvac_mode",
            "hvac_action",
            "temperature",
            "current_temperature",
            "target_temp_*",
        ]
    elif domain == "media_player":
        important_attrs = [
            "media_title",
            "media_artist",
            "source",
            "volume_level",
            "media_content_type",
        ]
    elif domain == "switch" or domain == "binary_sensor":
        important_attrs = ["device_class", "is_on"]

    # Combine with common attributes
    important_attrs.extend(common_attrs)

    # Deduplicate the list while preserving order
    important_attrs = list(dict.fromkeys(important_attrs))

    # Create and add the important attributes section
    result += "## Key Attributes\n\n"

    # Display only the important attributes that exist
    displayed_attrs = 0
    for attr_name in important_attrs:
        # Handle wildcard attributes (e.g., target_temp_*)
        if attr_name.endswith("*"):
            prefix = attr_name[:-1]
            matching_attrs = [name for name in attributes if name.startswith(prefix)]
            for name in matching_attrs:
                result += f"- **{name}**: {attributes[name]}\n"
                displayed_attrs += 1
        # Regular attribute match
        elif attr_name in attributes:
            attr_value = attributes[attr_name]
            if isinstance(attr_value, (list, dict)) and len(str(attr_value)) > 100:
                result += f"- **{attr_name}**: *[Complex data]*\n"
            else:
                result += f"- **{attr_name}**: {attr_value}\n"
            displayed_attrs += 1

    # If no important attributes were found, show a message
    if displayed_attrs == 0:
        result += "No key attributes found for this entity type.\n\n"

    # Add attribute count and link to detailed view
    total_attr_count = len(attributes)
    if total_attr_count > displayed_attrs:
        hidden_count = total_attr_count - displayed_attrs
        result += f"\n**Note**: Showing {displayed_attrs} of {total_attr_count} total attributes. "
        result += f"{hidden_count} additional attributes are available in the [detailed view](/api/resource/hass://entities/{entity_id}/detailed).\n\n"

    # Add last updated time if available
    if "last_updated" in state:
        result += f"**Last Updated**: {state['last_updated']}\n"

    return result


# list_entities tool is now in app.tools.entities module
# Registered above after creating the mcp instance


@mcp.resource("hass://entities")
@async_handler("get_all_entities_resource")
async def get_all_entities_resource() -> str:
    """
    Get a list of all Home Assistant entities as a resource

    This endpoint returns a complete list of all entities in Home Assistant,
    organized by domain. For token efficiency with large installations,
    consider using domain-specific endpoints or the domain summary instead.

    Returns:
        A markdown formatted string listing all entities grouped by domain

    Examples:
        ```
        # Get all entities
        entities = mcp.get_resource("hass://entities")
        ```

    Best Practices:
        - WARNING: This endpoint can return large amounts of data with many entities
        - Prefer domain-filtered endpoints: hass://entities/domain/{domain}
        - For overview information, use domain summaries instead of full entity lists
        - Consider starting with a search if looking for specific entities
    """
    logger.info("Getting all entities as a resource")
    entities = await get_entities(lean=True)

    # Check if there was an error
    if isinstance(entities, dict) and "error" in entities:
        return f"Error retrieving entities: {entities['error']}"
    if len(entities) == 1 and isinstance(entities[0], dict) and "error" in entities[0]:
        return f"Error retrieving entities: {entities[0]['error']}"

    # Format the entities as a string
    result = "# Home Assistant Entities\n\n"
    result += f"Total entities: {len(entities)}\n\n"
    result += "⚠️ **Note**: For better performance and token efficiency, consider using:\n"
    result += "- Domain filtering: `hass://entities/domain/{domain}`\n"
    result += "- Domain summaries: `hass://entities/domain/{domain}/summary`\n"
    result += "- Entity search: `hass://search/{query}`\n\n"

    # Group entities by domain for better organization
    domains = {}
    for entity in entities:
        domain = entity["entity_id"].split(".")[0]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(entity)

    # Build the string with entities grouped by domain
    for domain in sorted(domains.keys()):
        domain_count = len(domains[domain])
        result += f"## {domain.capitalize()} ({domain_count})\n\n"
        for entity in sorted(domains[domain], key=lambda e: e["entity_id"]):
            # Get a friendly name if available
            friendly_name = entity.get("attributes", {}).get("friendly_name", "")
            result += f"- **{entity['entity_id']}**: {entity['state']}"
            if friendly_name and friendly_name != entity["entity_id"]:
                result += f" ({friendly_name})"
            result += "\n"
        result += "\n"

    return result


# search_entities_tool is now in app.tools.entities module
# Registered above after creating the mcp instance


@mcp.resource("hass://search/{query}/{limit}")
@async_handler("search_entities_resource_with_limit")
async def search_entities_resource_with_limit(query: str, limit: str) -> str:
    """
    Search for entities matching a query string with a specified result limit

    This endpoint extends the basic search functionality by allowing you to specify
    a custom limit on the number of results returned. It's useful for both broader
    searches (larger limit) and more focused searches (smaller limit).

    Args:
        query: The search query to match against entity IDs, names, and attributes
        limit: Maximum number of entities to return (as a string, will be converted to int)

    Returns:
        A markdown formatted string with search results and a JSON summary

    Examples:
        ```
        # Search with a larger limit (up to 50 results)
        results = mcp.get_resource("hass://search/sensor/50")

        # Search with a smaller limit for focused results
        results = mcp.get_resource("hass://search/kitchen/5")
        ```

    Best Practices:
        - Use smaller limits (5-10) for focused searches where you need just a few matches
        - Use larger limits (30-50) for broader searches when you need more comprehensive results
        - Balance larger limits against token usage - more results means more tokens
        - Consider domain-specific searches for better precision: "light kitchen" instead of just "kitchen"
    """
    try:
        limit_int = int(limit)
        if limit_int <= 0:
            limit_int = 20
    except ValueError:
        limit_int = 20

    logger.info(f"Searching for entities matching: '{query}' with custom limit: {limit_int}")

    if not query or not query.strip():
        return "# Entity Search\n\nError: No search query provided"

    entities = await get_entities(search_query=query, limit=limit_int, lean=True)

    # Check if there was an error
    if isinstance(entities, dict) and "error" in entities:
        return f"# Entity Search\n\nError retrieving entities: {entities['error']}"

    # Format the search results
    result = f"# Entity Search Results for '{query}' (Limit: {limit_int})\n\n"

    if not entities:
        result += "No entities found matching your search query.\n"
        return result

    result += f"Found {len(entities)} matching entities:\n\n"

    # Group entities by domain for better organization
    domains = {}
    for entity in entities:
        domain = entity["entity_id"].split(".")[0]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(entity)

    # Build the string with entities grouped by domain
    for domain in sorted(domains.keys()):
        result += f"## {domain.capitalize()}\n\n"
        for entity in sorted(domains[domain], key=lambda e: e["entity_id"]):
            # Get a friendly name if available
            friendly_name = entity.get("attributes", {}).get("friendly_name", entity["entity_id"])
            result += f"- **{entity['entity_id']}**: {entity['state']}"
            if friendly_name != entity["entity_id"]:
                result += f" ({friendly_name})"
            result += "\n"
        result += "\n"

    # Add a more structured summary section for easy LLM processing
    result += "## Summary in JSON format\n\n"
    result += "```json\n"

    # Create a simplified JSON representation with only essential fields
    simplified_entities = []
    for entity in entities:
        simplified_entity = {
            "entity_id": entity["entity_id"],
            "state": entity["state"],
            "domain": entity["entity_id"].split(".")[0],
            "friendly_name": entity.get("attributes", {}).get("friendly_name", entity["entity_id"]),
        }

        # Add key attributes based on domain type if they exist
        domain = entity["entity_id"].split(".")[0]
        attributes = entity.get("attributes", {})

        # Include domain-specific important attributes
        if domain == "light" and "brightness" in attributes:
            simplified_entity["brightness"] = attributes["brightness"]
        elif domain == "sensor" and "unit_of_measurement" in attributes:
            simplified_entity["unit"] = attributes["unit_of_measurement"]
        elif domain == "climate" and "temperature" in attributes:
            simplified_entity["temperature"] = attributes["temperature"]
        elif domain == "media_player" and "media_title" in attributes:
            simplified_entity["media_title"] = attributes["media_title"]

        simplified_entities.append(simplified_entity)

    result += json.dumps(simplified_entities, indent=2)
    result += "\n```\n"

    return result


# Domain and system overview tools are now in app.tools.system module
# They are registered above after creating the mcp instance


@mcp.resource("hass://entities/{entity_id}/detailed")
@async_handler("get_entity_resource_detailed")
async def get_entity_resource_detailed(entity_id: str) -> str:
    """
    Get detailed information about a Home Assistant entity as a resource

    Use this detailed view selectively when you need to:
    - Understand all available attributes of an entity
    - Debug entity behavior or capabilities
    - See comprehensive state information

    For routine operations where you only need basic state information,
    prefer the standard entity endpoint or specify fields in the get_entity tool.

    Args:
        entity_id: The entity ID to get information for
    """
    logger.info(f"Getting detailed entity resource: {entity_id}")

    # Get all fields, no filtering (detailed view explicitly requests all data)
    state = await get_entity_state(entity_id, lean=False)

    # Check if there was an error
    if "error" in state:
        return f"# Entity: {entity_id}\n\nError retrieving entity: {state['error']}"

    # Format the entity as markdown
    result = f"# Entity: {entity_id} (Detailed View)\n\n"

    # Get friendly name if available
    friendly_name = state.get("attributes", {}).get("friendly_name")
    if friendly_name and friendly_name != entity_id:
        result += f"**Name**: {friendly_name}\n\n"

    # Add state
    result += f"**State**: {state.get('state')}\n\n"

    # Add domain and entity type information
    domain = entity_id.split(".")[0]
    result += f"**Domain**: {domain}\n\n"

    # Add usage guidance
    result += "## Usage Note\n"
    result += "This is the detailed view showing all entity attributes. For token-efficient interactions, "
    result += "consider using the standard entity endpoint or the get_entity tool with field filtering.\n\n"

    # Add all attributes with full details
    attributes = state.get("attributes", {})
    if attributes:
        result += "## Attributes\n\n"

        # Sort attributes for better organization
        sorted_attrs = sorted(attributes.items())

        # Format each attribute with complete information
        for attr_name, attr_value in sorted_attrs:
            # Format the attribute value
            if isinstance(attr_value, (list, dict)):
                attr_str = json.dumps(attr_value, indent=2)
                result += f"- **{attr_name}**:\n```json\n{attr_str}\n```\n"
            else:
                result += f"- **{attr_name}**: {attr_value}\n"

    # Add context data section
    result += "\n## Context Data\n\n"

    # Add last updated time if available
    if "last_updated" in state:
        result += f"**Last Updated**: {state['last_updated']}\n"

    # Add last changed time if available
    if "last_changed" in state:
        result += f"**Last Changed**: {state['last_changed']}\n"

    # Add entity ID and context information
    if "context" in state:
        context = state["context"]
        result += f"**Context ID**: {context.get('id', 'N/A')}\n"
        if "parent_id" in context:
            result += f"**Parent Context**: {context['parent_id']}\n"
        if "user_id" in context:
            result += f"**User ID**: {context['user_id']}\n"

    # Add related entities suggestions
    related_domains = []
    if domain == "light":
        related_domains = ["switch", "scene", "automation"]
    elif domain == "sensor":
        related_domains = ["binary_sensor", "input_number", "utility_meter"]
    elif domain == "climate":
        related_domains = ["sensor", "switch", "fan"]
    elif domain == "media_player":
        related_domains = ["remote", "switch", "sensor"]

    if related_domains:
        result += "\n## Related Entity Types\n\n"
        result += "You may want to check entities in these related domains:\n"
        for related in related_domains:
            result += f"- {related}\n"

    return result


@mcp.resource("hass://entities/domain/{domain}")
@async_handler("list_states_by_domain_resource")
async def list_states_by_domain_resource(domain: str) -> str:
    """
    Get a list of entities for a specific domain as a resource

    This endpoint provides all entities of a specific type (domain). It's much more
    token-efficient than retrieving all entities when you only need entities of a
    specific type.

    Args:
        domain: The domain to filter by (e.g., 'light', 'switch', 'sensor')

    Returns:
        A markdown formatted string with all entities in the specified domain

    Examples:
        ```
        # Get all lights
        lights = mcp.get_resource("hass://entities/domain/light")

        # Get all climate devices
        climate = mcp.get_resource("hass://entities/domain/climate")

        # Get all sensors
        sensors = mcp.get_resource("hass://entities/domain/sensor")
        ```

    Best Practices:
        - Use this endpoint when you need detailed information about all entities of a specific type
        - For a more concise overview, use the domain summary endpoint: hass://entities/domain/{domain}/summary
        - For sensors and other high-count domains, consider using a search to further filter results
    """
    logger.info(f"Getting entities for domain: {domain}")

    # Get all entities for the specified domain (using lean format for token efficiency)
    entities = await get_entities(domain=domain, lean=True)

    # Check if there was an error
    if isinstance(entities, dict) and "error" in entities:
        return f"Error retrieving entities: {entities['error']}"

    # Format the entities as a string
    result = f"# {domain.capitalize()} Entities\n\n"

    # Pagination info (fixed for now due to MCP limitations)
    total_entities = len(entities)

    # List the entities
    for entity in sorted(entities, key=lambda e: e["entity_id"]):
        # Get a friendly name if available
        friendly_name = entity.get("attributes", {}).get("friendly_name", entity["entity_id"])
        result += f"- **{entity['entity_id']}**: {entity['state']}"
        if friendly_name != entity["entity_id"]:
            result += f" ({friendly_name})"
        result += "\n"

    # Add link to summary
    result += "\n## Related Resources\n\n"
    result += f"- [View domain summary](/api/resource/hass://entities/domain/{domain}/summary)\n"

    return result


# Automation tools are now in app.tools.automations module
# They are registered above after creating the mcp instance

# Script tools are now in app.tools.scripts module
# They are registered above after creating the mcp instance

# Area tools are now in app.tools.areas module
# They are registered above after creating the mcp instance

# Device tools are now in app.tools.devices module
# Template tools are now in app.tools.templates module
# Scene tools are now in app.tools.scenes module
# They are registered above after creating the mcp instance


# Integration tools are now in app.tools.integrations module
# They are registered above after creating the mcp instance

# Tag tools are now in app.tools.tags module
# They are registered above after creating the mcp instance

# Webhook tools are now in app.tools.webhooks module
# They are registered above after creating the mcp instance

# Backup tools are now in app.tools.backups module
# They are registered above after creating the mcp instance

# Prompt functionality is now in app.prompts module
from app.prompts import (
    automation_health_check,
    create_automation,
    dashboard_layout_generator,
    debug_automation,
    entity_naming_consistency,
    routine_optimizer,
    troubleshoot_entity,
)

# Register prompts with MCP instance
mcp.prompt()(create_automation)
mcp.prompt()(debug_automation)
mcp.prompt()(troubleshoot_entity)
mcp.prompt()(routine_optimizer)
mcp.prompt()(automation_health_check)
mcp.prompt()(entity_naming_consistency)
mcp.prompt()(dashboard_layout_generator)


# Legacy prompt definitions removed - now in app.prompts module
# All prompt functionality moved to app/prompts.py for better organization

# System tools (get_history, get_error_log, system_health, core_config) are now in app.tools.system module
# They are registered above after creating the mcp instance
