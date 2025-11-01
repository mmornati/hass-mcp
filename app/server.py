import json
import logging
from typing import Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create an MCP server
from mcp.server.fastmcp import FastMCP

from app.core import async_handler
from app.hass import (
    create_backup,
    create_calendar_event,
    create_tag,
    create_zone,
    delete_backup,
    delete_tag,
    delete_zone,
    fire_event,
    get_backups,
    get_calendar_events,
    get_calendars,
    get_entities,
    get_entity_state,
    get_event_types,
    get_helper_details,
    get_helpers,
    get_notification_services,
    get_recent_events,
    get_tag_automations,
    get_tags,
    get_webhooks,
    get_zones,
    restore_backup,
    send_notification,
    test_notification_delivery,
    test_webhook_endpoint,
    update_helper_value,
    update_zone,
)

mcp = FastMCP("Hass-MCP")

# Import and register tools from tools modules
# Tools are registered manually to avoid circular imports
from app.tools import (
    areas,
    automations,
    blueprints,
    devices,
    diagnostics,
    entities,
    integrations,
    logbook,
    scenes,
    scripts,
    services,
    statistics,
    system,
    templates,
)  # noqa: E402

# Register entity tools with MCP instance
mcp.tool()(async_handler("get_entity")(entities.get_entity))
mcp.tool()(async_handler("entity_action")(entities.entity_action))
mcp.tool()(async_handler("list_entities")(entities.list_entities))
mcp.tool()(async_handler("search_entities_tool")(entities.search_entities_tool))

# Register automation tools with MCP instance
mcp.tool()(async_handler("list_automations")(automations.list_automations))
mcp.tool()(async_handler("get_automation_config")(automations.get_automation_config_tool))
mcp.tool()(async_handler("create_automation")(automations.create_automation_tool))
mcp.tool()(async_handler("update_automation")(automations.update_automation_tool))
mcp.tool()(async_handler("delete_automation")(automations.delete_automation_tool))
mcp.tool()(async_handler("enable_automation")(automations.enable_automation_tool))
mcp.tool()(async_handler("disable_automation")(automations.disable_automation_tool))
mcp.tool()(async_handler("trigger_automation")(automations.trigger_automation_tool))
mcp.tool()(
    async_handler("get_automation_execution_log")(automations.get_automation_execution_log_tool)
)
mcp.tool()(async_handler("validate_automation_config")(automations.validate_automation_config_tool))

# Register script tools with MCP instance
mcp.tool()(async_handler("list_scripts")(scripts.list_scripts_tool))
mcp.tool()(async_handler("get_script")(scripts.get_script_tool))
mcp.tool()(async_handler("run_script")(scripts.run_script_tool))
mcp.tool()(async_handler("reload_scripts")(scripts.reload_scripts_tool))

# Register device tools with MCP instance
mcp.tool()(async_handler("list_devices")(devices.list_devices_tool))
mcp.tool()(async_handler("get_device")(devices.get_device_tool))
mcp.tool()(async_handler("get_device_entities")(devices.get_device_entities_tool))
mcp.tool()(async_handler("get_device_stats")(devices.get_device_stats_tool))

# Register area tools with MCP instance
mcp.tool()(async_handler("list_areas")(areas.list_areas_tool))
mcp.tool()(async_handler("get_area_entities")(areas.get_area_entities_tool))
mcp.tool()(async_handler("create_area")(areas.create_area_tool))
mcp.tool()(async_handler("update_area")(areas.update_area_tool))
mcp.tool()(async_handler("delete_area")(areas.delete_area_tool))
mcp.tool()(async_handler("get_area_summary")(areas.get_area_summary_tool))

# Register scene tools with MCP instance
mcp.tool()(async_handler("list_scenes")(scenes.list_scenes_tool))
mcp.tool()(async_handler("get_scene")(scenes.get_scene_tool))
mcp.tool()(async_handler("create_scene")(scenes.create_scene_tool))
mcp.tool()(async_handler("activate_scene")(scenes.activate_scene_tool))
mcp.tool()(async_handler("reload_scenes")(scenes.reload_scenes_tool))

# Register integration tools with MCP instance
mcp.tool()(async_handler("list_integrations")(integrations.list_integrations))
mcp.tool()(async_handler("get_integration_config")(integrations.get_integration_config_tool))
mcp.tool()(async_handler("reload_integration")(integrations.reload_integration_tool))

# Register system tools with MCP instance
mcp.tool()(async_handler("get_version")(system.get_version))
mcp.tool()(async_handler("system_overview")(system.system_overview))
mcp.tool()(async_handler("get_error_log")(system.get_error_log))
mcp.tool()(async_handler("system_health")(system.system_health))
mcp.tool()(async_handler("core_config")(system.core_config))
mcp.tool()(async_handler("restart_ha")(system.restart_ha))
mcp.tool()(async_handler("get_history")(system.get_history))
mcp.tool()(async_handler("domain_summary")(system.domain_summary_tool))

# Register service tools with MCP instance
mcp.tool()(async_handler("call_service")(services.call_service_tool))

# Register template tools with MCP instance
mcp.tool()(async_handler("test_template")(templates.test_template_tool))

# Register logbook tools with MCP instance
mcp.tool()(async_handler("get_logbook")(logbook.get_logbook_tool))
mcp.tool()(async_handler("get_entity_logbook")(logbook.get_entity_logbook_tool))
mcp.tool()(async_handler("search_logbook")(logbook.search_logbook_tool))

# Register statistics tools with MCP instance
mcp.tool()(async_handler("get_entity_statistics")(statistics.get_entity_statistics_tool))
mcp.tool()(async_handler("get_domain_statistics")(statistics.get_domain_statistics_tool))
mcp.tool()(async_handler("analyze_usage_patterns")(statistics.analyze_usage_patterns_tool))

# Register diagnostics tools with MCP instance
mcp.tool()(async_handler("diagnose_entity")(diagnostics.diagnose_entity_tool))
mcp.tool()(async_handler("check_entity_dependencies")(diagnostics.check_entity_dependencies_tool))
mcp.tool()(
    async_handler("analyze_automation_conflicts")(diagnostics.analyze_automation_conflicts_tool)
)
mcp.tool()(async_handler("get_integration_errors")(diagnostics.get_integration_errors_tool))

# Register blueprints tools with MCP instance
mcp.tool()(async_handler("list_blueprints")(blueprints.list_blueprints_tool))
mcp.tool()(async_handler("get_blueprint")(blueprints.get_blueprint_tool))
mcp.tool()(async_handler("import_blueprint")(blueprints.import_blueprint_tool))
mcp.tool()(
    async_handler("create_automation_from_blueprint")(
        blueprints.create_automation_from_blueprint_tool
    )
)

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


@mcp.tool()
@async_handler("list_zones")
async def list_zones_tool() -> list[dict[str, Any]]:
    """
    Get a list of all zones (GPS coordinates) in Home Assistant

    Returns:
        List of zone dictionaries containing:
        - id: Unique identifier for the zone
        - name: Display name of the zone
        - latitude: Latitude coordinate (-90 to 90)
        - longitude: Longitude coordinate (-180 to 180)
        - radius: Zone radius in meters
        - icon: Zone icon (if available)
        - passive: Whether the zone is passive

    Examples:
        Returns all zones with their GPS coordinates and configuration

    Best Practices:
        - Use this to discover available zones before operations
        - Check zone coordinates and radius for location-based automations
        - Use zones for location-based device tracking and automations
    """
    logger.info("Getting list of zones")
    return await get_zones()


@mcp.tool()
@async_handler("create_zone")
async def create_zone_tool(
    name: str,
    latitude: float,
    longitude: float,
    radius: float,
    icon: str | None = None,
    passive: bool = False,
) -> dict[str, Any]:
    """
    Create a new zone

    Args:
        name: Display name for the zone (required)
        latitude: Latitude coordinate (-90 to 90) (required)
        longitude: Longitude coordinate (-180 to 180) (required)
        radius: Zone radius in meters (required, must be positive)
        icon: Optional zone icon (e.g., 'mdi:home')
        passive: Whether the zone is passive (default: False)

    Returns:
        Created zone dictionary with zone_id and configuration

    Examples:
        name="Home", latitude=37.7749, longitude=-122.4194, radius=100, icon="mdi:home"
        name="Work", latitude=37.7849, longitude=-122.4094, radius=200
        name="School", latitude=37.7949, longitude=-122.3994, radius=150, passive=True

    Note:
        Zone IDs are automatically generated by Home Assistant.
        GPS coordinates are validated to be within valid ranges.
        Radius must be positive.

    Best Practices:
        - Use descriptive names for zones
        - Set appropriate radius based on location size
        - Use icons for visual identification in dashboards
        - Set passive=True for zones that should not trigger automations
    """
    logger.info(f"Creating zone: {name} at ({latitude}, {longitude}) with radius {radius}")
    return await create_zone(name, latitude, longitude, radius, icon, passive)


@mcp.tool()
@async_handler("update_zone")
async def update_zone_tool(
    zone_id: str,
    name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius: float | None = None,
    icon: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing zone

    Args:
        zone_id: The zone ID to update
        name: Optional new name for the zone
        latitude: Optional new latitude coordinate (-90 to 90)
        longitude: Optional new longitude coordinate (-180 to 180)
        radius: Optional new radius in meters (must be positive)
        icon: Optional new icon

    Returns:
        Updated zone dictionary

    Examples:
        zone_id="home", name="My Home" - update zone name
        zone_id="work", latitude=37.7849, longitude=-122.4094 - update zone location
        zone_id="home", radius=150 - update zone radius
        zone_id="work", name="Office", radius=200, icon="mdi:office" - update multiple fields

    Note:
        Only provided fields will be updated. Fields not provided remain unchanged.
        GPS coordinates and radius are validated if provided.

    Best Practices:
        - Get zone first with list_zones to verify zone_id
        - Update one field at a time or all together
        - Verify GPS coordinates are correct before updating
    """
    logger.info(f"Updating zone: {zone_id}")
    return await update_zone(zone_id, name, latitude, longitude, radius, icon)


@mcp.tool()
@async_handler("delete_zone")
async def delete_zone_tool(zone_id: str) -> dict[str, Any]:
    """
    Delete a zone

    Args:
        zone_id: The zone ID to delete

    Returns:
        Response from the delete operation

    Examples:
        zone_id="work" - delete zone with ID work

    Note:
        ⚠️ This permanently deletes the zone. There is no undo.
        System zones (like 'home') may not be deletable.
        Make sure no automations or device tracking depend on this zone.

    Best Practices:
        - Check for dependencies before deleting
        - Verify zone_id is correct before deletion
        - Consider updating zone instead of deleting if possible
        - List zones first to ensure correct zone_id
    """
    logger.info(f"Deleting zone: {zone_id}")
    return await delete_zone(zone_id)


@mcp.tool()
@async_handler("list_calendars")
async def list_calendars_tool() -> list[dict[str, Any]]:
    """
    Get a list of all calendar entities in Home Assistant

    Returns:
        List of calendar dictionaries containing:
        - entity_id: The calendar entity ID
        - state: Current state of the calendar
        - friendly_name: Display name of the calendar
        - supported_features: Bitmask of supported features

    Examples:
        Returns all calendars with their configuration and supported features

    Best Practices:
        - Use this to discover available calendars
        - Check supported_features to see what operations are available
        - Use to find calendar entities before getting events
        - Check supported_features before creating events
    """
    logger.info("Getting list of calendars")
    return await get_calendars()


@mcp.tool()
@async_handler("get_calendar_events")
async def get_calendar_events_tool(
    entity_id: str, start_date: str, end_date: str
) -> list[dict[str, Any]]:
    """
    Get calendar events for a date range

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
        - Use to check upcoming events for automations
    """
    logger.info(f"Getting calendar events for {entity_id} from {start_date} to {end_date}")
    return await get_calendar_events(entity_id, start_date, end_date)


@mcp.tool()
@async_handler("create_calendar_event")
async def create_calendar_event_tool(
    entity_id: str,
    summary: str,
    start: str,
    end: str,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a calendar event

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


@mcp.tool()
@async_handler("list_notification_services")
async def list_notification_services_tool() -> list[dict[str, Any]]:
    """
    Get a list of all available notification platforms in Home Assistant

    Returns:
        List of notification service dictionaries containing:
        - service: The service name (e.g., 'notify.mobile_app_iphone')
        - name: Display name of the service
        - description: Service description (if available)
        - entity_id: Entity ID if available from fallback

    Examples:
        Returns all notification services with their configuration

    Best Practices:
        - Use this to discover available notification platforms
        - Check service names before sending notifications
        - Use to test which notification services are configured
        - Use to verify notification services are working
    """
    logger.info("Getting list of notification services")
    return await get_notification_services()


@mcp.tool()
@async_handler("send_notification")
async def send_notification_tool(
    message: str, target: str | None = None, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Send a notification

    Args:
        message: The notification message (required)
        target: Optional target notification service/platform
                 Can be 'notify.service_name' or just 'service_name'
                 If not provided, uses persistent_notification
        data: Optional dictionary of additional notification data
              (e.g., title, data for platform-specific options)

    Returns:
        Response dictionary from the notification service

    Examples:
        message="Alert: Temperature too high" - send to default notification
        message="Alert", target="notify.mobile_app_iphone" - send to iPhone
        message="Alert", target="mobile_app_iphone", data={"title": "System Alert"} - send with title

    Note:
        If target is provided, it will be parsed to determine domain and service.
        If target is 'notify.service_name', domain is 'notify' and service is 'service_name'.
        If target is just 'service_name', domain is 'notify' and service is 'service_name'.
        Additional data can include platform-specific options like title, url, etc.

    Best Practices:
        - Use list_notification_services to discover available targets
        - Include a clear message describing what the notification is about
        - Use data parameter for platform-specific options (title, image, etc.)
        - Test notifications before using in production automations
        - Use to send alerts about system status, errors, or important events
    """
    logger.info(f"Sending notification: '{message}'" + (f" to {target}" if target else ""))
    return await send_notification(message, target, data)


@mcp.tool()
@async_handler("test_notification")
async def test_notification_tool(platform: str, message: str) -> dict[str, Any]:
    """
    Test notification delivery to a specific platform

    Args:
        platform: The notification platform/service name
                  Can be 'notify.service_name' or just 'service_name'
        message: The test message to send

    Returns:
        Response dictionary from the notification service

    Examples:
        platform="notify.mobile_app_iphone", message="Test notification"
        platform="mobile_app_iphone", message="Test notification"

    Note:
        This sends a test notification prefixed with "[TEST]".
        Useful for verifying notification delivery works before using in automations.
        The platform parameter follows the same format as send_notification target.

    Best Practices:
        - Use to verify notification services are working
        - Test each notification platform before using in production
        - Check notification delivery after configuration changes
        - Use to test notification delivery after setup or configuration
    """
    logger.info(f"Testing notification delivery to {platform} with message: '{message}'")
    return await test_notification_delivery(platform, message)


@mcp.tool()
@async_handler("fire_event")
async def fire_event_tool(
    event_type: str, event_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Fire a custom event

    Args:
        event_type: The event type name (e.g., 'custom_event', 'state_changed')
        event_data: Optional dictionary of event data/payload

    Returns:
        Response dictionary from the event fire API

    Examples:
        event_type="custom_event", event_data={"message": "Hello"}
        event_type="automation_triggered", event_data={"entity_id": "light.living_room"}

    Note:
        Events are used for communication between different parts of Home Assistant.
        Custom events can trigger automations that listen for specific event types.
        Event data is optional but commonly used to pass information to event handlers.

    Best Practices:
        - Use descriptive event type names (e.g., 'custom_event', 'my_app_ready')
        - Include relevant data in event_data for event handlers
        - Use events to trigger automations based on custom conditions
        - Document custom event types for team members
        - Use events for inter-component communication
    """
    logger.info(f"Firing event: {event_type}" + (f" with data: {event_data}" if event_data else ""))
    return await fire_event(event_type, event_data)


@mcp.tool()
@async_handler("list_event_types")
async def list_event_types_tool() -> list[str]:
    """
    List common event types used in Home Assistant

    Returns:
        List of common event type strings

    Examples:
        Returns common event types like "state_changed", "time_changed", etc.

    Note:
        Home Assistant API doesn't provide a comprehensive list of event types.
        This function returns common event types from documentation.
        Custom event types can be any string, but common ones are listed here.

    Best Practices:
        - Use this to discover common event types
        - Create custom event types for your own use cases
        - Check automations/logbook for other event types used in your setup
        - Use descriptive names for custom event types
    """
    logger.info("Getting list of common event types")
    return await get_event_types()


@mcp.tool()
@async_handler("get_events")
async def get_events_tool(entity_id: str | None = None, hours: int = 1) -> list[dict[str, Any]]:
    """
    Get recent events for an entity (via logbook)

    Args:
        entity_id: Optional entity ID to filter events for a specific entity
        hours: Number of hours of history to retrieve (default: 1)

    Returns:
        List of event dictionaries from logbook entries

    Examples:
        entity_id=None, hours=1 - get all recent events from last hour
        entity_id="light.living_room", hours=24 - get events for specific entity from last day

    Note:
        Events can be retrieved via logbook entries.
        This is a convenience function that uses get_logbook_entries.
        Useful for debugging and understanding what events occurred.

    Best Practices:
        - Keep hours reasonable (1-24) for token efficiency
        - Use entity_id to filter events for specific entities
        - Use to debug event-triggered automations
        - Use to understand event flow in your Home Assistant setup
    """
    logger.info(
        "Getting recent events"
        + (f" for entity: {entity_id}" if entity_id else "")
        + f" for last {hours} hours"
    )
    return await get_recent_events(entity_id, hours)


@mcp.tool()
@async_handler("list_tags")
async def list_tags_tool() -> list[dict[str, Any]]:
    """
    Get a list of all RFID/NFC tags in Home Assistant

    Returns:
        List of tag dictionaries containing:
        - tag_id: The tag ID (unique identifier)
        - name: Display name of the tag
        - last_scanned: Last scan timestamp (if available)
        - device_id: Device ID associated with the tag (if available)

    Examples:
        Returns all tags with their configuration and metadata

    Best Practices:
        - Use this to discover configured tags
        - Check tag IDs before creating new tags
        - Use to manage tags for NFC-based automations
        - Use to document all tags in your setup
    """
    logger.info("Getting list of tags")
    return await get_tags()


@mcp.tool()
@async_handler("create_tag")
async def create_tag_tool(tag_id: str, name: str) -> dict[str, Any]:
    """
    Create a new tag

    Args:
        tag_id: The tag ID (unique identifier, e.g., 'ABC123')
        name: Display name for the tag (e.g., 'Front Door Key')

    Returns:
        Response dictionary containing created tag information

    Examples:
        tag_id="ABC123", name="Front Door Key"
        tag_id="XYZ789", name="Office Access Card"

    Note:
        Tag IDs must be unique.
        Tags are used to trigger automations when scanned.
        After creating a tag, you can create automations triggered by tag scans.

    Best Practices:
        - Use descriptive names for tags
        - Choose unique tag IDs
        - Use tag names to identify physical tags/cards
        - Create automations after creating tags
        - Use consistent naming conventions for tags
    """
    logger.info(f"Creating tag: {tag_id} with name: {name}")
    return await create_tag(tag_id, name)


@mcp.tool()
@async_handler("delete_tag")
async def delete_tag_tool(tag_id: str) -> dict[str, Any]:
    """
    Delete a tag

    Args:
        tag_id: The tag ID to delete

    Returns:
        Response dictionary from the delete API

    Examples:
        tag_id="ABC123" - delete a specific tag

    Note:
        Deleting a tag removes it from Home Assistant.
        Automations that use this tag may stop working.
        Tag deletion is permanent and cannot be undone.

    Best Practices:
        - Check for automations using the tag before deleting
        - Use get_tag_automations to find dependent automations
        - Remove or update automations before deleting tags
        - Verify tag_id exists before deleting
    """
    logger.info(f"Deleting tag: {tag_id}")
    return await delete_tag(tag_id)


@mcp.tool()
@async_handler("get_tag_automations")
async def get_tag_automations_tool(tag_id: str) -> list[dict[str, Any]]:
    """
    Get automations triggered by a tag

    Args:
        tag_id: The tag ID to find automations for

    Returns:
        List of automation dictionaries containing:
        - automation_id: The automation entity ID
        - alias: Display name of the automation
        - enabled: Whether the automation is enabled

    Examples:
        tag_id="ABC123" - find all automations triggered by this tag

    Note:
        This searches through all automations to find those with tag triggers.
        Tag triggers use platform "tag" with matching tag_id.
        Useful for understanding tag dependencies before deletion.

    Best Practices:
        - Use before deleting tags to check dependencies
        - Review automations that depend on the tag
        - Update or remove dependent automations if needed
        - Use to document tag usage in your setup
        - Use to troubleshoot tag-triggered automations
    """
    logger.info(f"Getting automations for tag: {tag_id}")
    return await get_tag_automations(tag_id)


@mcp.tool()
@async_handler("list_helpers")
async def list_helpers_tool(helper_type: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all input helpers in Home Assistant

    Args:
        helper_type: Optional helper type to filter by
                     (e.g., 'input_boolean', 'input_number', 'input_text', etc.)
                     If not provided, returns all helpers

    Returns:
        List of helper dictionaries containing:
        - entity_id: The helper entity ID
        - domain: The helper domain (e.g., 'input_boolean')
        - state: Current state of the helper
        - friendly_name: Display name of the helper
        - attributes: Helper attributes

    Examples:
        helper_type=None - get all helpers
        helper_type="input_boolean" - get only input_boolean helpers
        helper_type="input_number" - get only input_number helpers

    Note:
        Helper types include:
        - input_boolean, input_number, input_text, input_select
        - input_datetime, input_button, counter, timer, schedule
        Helpers are virtual entities used for storing values and controlling automations.

    Best Practices:
        - Use helper_type to filter specific helper types
        - Use to discover configured helpers
        - Use to manage virtual entities for automations
        - Check helper types before updating values
    """
    logger.info("Getting list of helpers" + (f" of type: {helper_type}" if helper_type else ""))
    return await get_helpers(helper_type)


@mcp.tool()
@async_handler("get_helper")
async def get_helper_tool(helper_id: str) -> dict[str, Any]:
    """
    Get helper state and configuration

    Args:
        helper_id: The helper entity ID or name
                   (e.g., 'input_boolean.work_from_home' or 'work_from_home')

    Returns:
        Dictionary containing helper state and configuration

    Examples:
        helper_id="input_boolean.work_from_home"
        helper_id="work_from_home" - will search for matching helper

    Note:
        If helper_id doesn't include domain, the function searches for matching helpers.
        Returns full entity state with all attributes.
        Useful for getting current value and configuration of helpers.

    Best Practices:
        - Use full entity_id (with domain) when possible
        - Check helper exists before updating
        - Use to inspect helper configuration and current value
    """
    logger.info(f"Getting helper details: {helper_id}")
    return await get_helper_details(helper_id)


@mcp.tool()
@async_handler("update_helper")
async def update_helper_tool(helper_id: str, value: Any) -> dict[str, Any]:
    """
    Update helper value

    Args:
        helper_id: The helper entity ID (e.g., 'input_boolean.work_from_home')
        value: The value to set, depends on helper type:
               - input_boolean: True/False or "on"/"off"
               - input_number: Numeric value (float)
               - input_text: String value
               - input_select: Option string (must match available options)
               - counter: Integer value, or "+" to increment, "-" to decrement
               - timer: "start", "pause", or "cancel"
               - input_button: Any value (triggers press action)

    Returns:
        Response dictionary from the service call

    Examples:
        helper_id="input_boolean.work_from_home", value=True
        helper_id="input_number.temperature", value=22.5
        helper_id="input_text.name", value="John"
        helper_id="counter.steps", value="+"
        helper_id="timer.countdown", value="start"

    Note:
        Different helper types require different service calls:
        - input_boolean: turn_on/turn_off
        - input_number: set_value
        - input_text: set_value
        - input_select: select_option
        - counter: increment/decrement/set_value
        - timer: start/pause/cancel
        - input_button: press

    Best Practices:
        - Use appropriate value types for each helper type
        - Check helper type before updating
        - Verify value is valid for the helper type
        - Use counters with "+" or "-" for increment/decrement
        - Use timers with "start", "pause", or "cancel"
    """
    logger.info(f"Updating helper: {helper_id} with value: {value}")
    return await update_helper_value(helper_id, value)


@mcp.tool()
@async_handler("list_webhooks")
async def list_webhooks_tool() -> list[dict[str, Any]]:
    """
    Get a list of registered webhooks in Home Assistant

    Returns:
        List of webhook information dictionaries containing:
        - note: Information about webhook configuration
        - common_webhook_id_pattern: Pattern for webhook IDs
        - usage: Usage instructions
        - webhook_url_format: Webhook URL format
        - authentication: Authentication requirements

    Examples:
        Returns webhook patterns and usage information

    Note:
        Webhooks are typically defined in configuration.yaml or through automations/scripts.
        They might not have entities, so they need to be parsed from configuration.
        In a real implementation, this might need to:
        - Parse configuration.yaml
        - Use a config API if available
        - Document webhooks from automations/scripts
        For now, this returns common webhook patterns and usage information.

    Best Practices:
        - Webhooks are typically created via configuration files
        - Use test_webhook to test webhook endpoints
        - Webhook IDs are defined in automations/scripts
        - Check configuration.yaml for webhook definitions
    """
    logger.info("Getting list of webhooks")
    return await get_webhooks()


@mcp.tool()
@async_handler("test_webhook")
async def test_webhook_tool(
    webhook_id: str,
    payload: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test webhook endpoint

    Args:
        webhook_id: The webhook ID to test
        payload: Optional payload to send with the webhook request

    Returns:
        Dictionary containing webhook response:
        - status: Response status ("success" or "error")
        - status_code: HTTP status code
        - response_text: Response text (limited to 500 characters)
        - response_json: Response JSON if available

    Examples:
        webhook_id="my_webhook", payload=None
        webhook_id="automation_trigger", payload={"entity_id": "light.living_room"}

    Note:
        Webhooks allow external systems to trigger Home Assistant actions via HTTP POST requests.
        Webhook URL format: /api/webhook/{webhook_id}
        Webhooks don't require authentication token.
        Webhooks return 200 on success, but might not return JSON.

    Best Practices:
        - Use to test webhook endpoints
        - Test with various payloads
        - Verify webhook triggers correct actions
        - Use to debug webhook configurations
        - Check webhook response to verify it's working correctly
    """
    logger.info(f"Testing webhook: {webhook_id}" + (f" with payload: {payload}" if payload else ""))
    return await test_webhook_endpoint(webhook_id, payload)


@mcp.tool()
@async_handler("list_backups")
async def list_backups_tool() -> dict[str, Any]:
    """
    List available backups (if Supervisor API available)

    Returns:
        Dictionary containing:
        - available: Boolean indicating if Supervisor API is available
        - backups: List of backup dictionaries (if available)
        - error: Error message (if Supervisor API not available)

    Examples:
        Returns list of backups or error if Supervisor API not available

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        If Supervisor API is not available (404), returns available: False.
        This feature requires Home Assistant OS installation.

    Best Practices:
        - Check available flag before attempting operations
        - Use to list existing backups before creating new ones
        - Use to verify backup creation succeeded
        - Only available on Home Assistant OS installations
    """
    logger.info("Getting list of backups")
    return await get_backups()


@mcp.tool()
@async_handler("create_backup")
async def create_backup_tool(
    name: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Create a backup (if Supervisor API available)

    Args:
        name: Backup name (e.g., 'Full Backup 2025-01-01')
        password: Optional password for encrypted backup
        full: If True, creates full backup; if False, creates partial backup

    Returns:
        Dictionary containing backup creation response:
        - available: Boolean indicating if Supervisor API is available
        - slug: Backup slug identifier (if successful)
        - error: Error message (if Supervisor API not available or creation failed)

    Examples:
        name="Full Backup 2025-01-01", password=None, full=True
        name="Partial Backup", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full backups include all data, partial backups allow selective restoration.
        Password-protected backups require password for restoration.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Use descriptive backup names with dates
        - Create full backups before major changes
        - Use partial backups for specific components
        - Store passwords securely for encrypted backups
        - Only available on Home Assistant OS installations
    """
    logger.info(f"Creating {'full' if full else 'partial'} backup: {name}")
    return await create_backup(name, password, full)


@mcp.tool()
@async_handler("restore_backup")
async def restore_backup_tool(
    backup_slug: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Restore a backup (if Supervisor API available)

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')
        password: Optional password for encrypted backup
        full: If True, restores full backup; if False, restores partial backup

    Returns:
        Dictionary containing restore response:
        - available: Boolean indicating if Supervisor API is available
        - message: Restore status message
        - error: Error message (if Supervisor API not available or restore failed)

    Examples:
        backup_slug="20250101_120000", password=None, full=True
        backup_slug="backup_2025", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full restore restores entire system, partial restore allows selective restoration.
        Password-protected backups require password for restoration.
        Restoring will restart Home Assistant and may take several minutes.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup exists before restoring
        - Use full restore for complete system recovery
        - Use partial restore for specific components
        - Provide password for encrypted backups
        - Only available on Home Assistant OS installations
        - System will restart after restore
    """
    logger.info(
        f"Restoring {'full' if full else 'partial'} backup: {backup_slug}"
        + (" with password" if password else "")
    )
    return await restore_backup(backup_slug, password, full)


@mcp.tool()
@async_handler("delete_backup")
async def delete_backup_tool(backup_slug: str) -> dict[str, Any]:
    """
    Delete a backup (if Supervisor API available)

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')

    Returns:
        Dictionary containing delete response:
        - available: Boolean indicating if Supervisor API is available
        - message: Delete status message
        - error: Error message (if Supervisor API not available or delete failed)

    Examples:
        backup_slug="20250101_120000"

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Deleting a backup is permanent and cannot be undone.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup slug exists before deleting
        - Use with caution as deletion is permanent
        - Only delete backups you no longer need
        - Only available on Home Assistant OS installations
    """
    logger.info(f"Deleting backup: {backup_slug}")
    return await delete_backup(backup_slug)


# Prompt functionality
@mcp.prompt()
def create_automation(trigger_type: str, entity_id: str = None):
    """
    Guide a user through creating a Home Assistant automation

    This prompt provides a step-by-step guided conversation for creating
    a new automation in Home Assistant based on the specified trigger type.

    Args:
        trigger_type: The type of trigger for the automation (state, time, etc.)
        entity_id: Optional entity to use as the trigger source

    Returns:
        A list of messages for the interactive conversation
    """
    # Define the initial system message
    system_message = """You are an automation creation assistant for Home Assistant.
You'll guide the user through creating an automation with the following steps:
1. Define the trigger conditions based on their specified trigger type
2. Specify the actions to perform
3. Add any conditions (optional)
4. Review and confirm the automation"""

    # Define the first user message based on parameters
    trigger_description = {
        "state": "an entity changing state",
        "time": "a specific time of day",
        "numeric_state": "a numeric value crossing a threshold",
        "zone": "entering or leaving a zone",
        "sun": "sun events (sunrise/sunset)",
        "template": "a template condition becoming true",
    }

    description = trigger_description.get(trigger_type, trigger_type)

    if entity_id:
        user_message = f"I want to create an automation triggered by {description} for {entity_id}."
    else:
        user_message = f"I want to create an automation triggered by {description}."

    # Return the conversation starter messages
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def debug_automation(automation_id: str):
    """
    Help a user troubleshoot an automation that isn't working

    This prompt guides the user through the process of diagnosing and fixing
    issues with an existing Home Assistant automation.

    Args:
        automation_id: The entity ID of the automation to troubleshoot

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant automation troubleshooting expert.
You'll help the user diagnose problems with their automation by checking:
1. Trigger conditions and whether they're being met
2. Conditions that might be preventing execution
3. Action configuration issues
4. Entity availability and connectivity
5. Permissions and scope issues"""

    user_message = (
        f"My automation {automation_id} isn't working properly. Can you help me troubleshoot it?"
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def troubleshoot_entity(entity_id: str):
    """
    Guide a user through troubleshooting issues with an entity

    This prompt helps diagnose and resolve problems with a specific
    Home Assistant entity that isn't functioning correctly.

    Args:
        entity_id: The entity ID having issues

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant entity troubleshooting expert.
You'll help the user diagnose problems with their entity by checking:
1. Entity status and availability
2. Integration status
3. Device connectivity
4. Recent state changes and error patterns
5. Configuration issues
6. Common problems with this entity type"""

    user_message = f"My entity {entity_id} isn't working properly. Can you help me troubleshoot it?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def routine_optimizer():
    """
    Analyze usage patterns and suggest optimized routines based on actual behavior

    This prompt helps users analyze their Home Assistant usage patterns and create
    more efficient routines, automations, and schedules based on real usage data.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant optimization expert specializing in routine analysis.
You'll help the user analyze their usage patterns and create optimized routines by:
1. Reviewing entity state histories to identify patterns
2. Analyzing when lights, climate controls, and other devices are used
3. Finding correlations between different device usages
4. Suggesting automations based on detected routines
5. Optimizing existing automations to better match actual usage
6. Creating schedules that adapt to the user's lifestyle
7. Identifying energy-saving opportunities based on usage patterns"""

    user_message = "I'd like to optimize my home automations based on my actual usage patterns. Can you help analyze how I use my smart home and suggest better routines?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def automation_health_check():
    """
    Review all automations, find conflicts, redundancies, or improvement opportunities

    This prompt helps users perform a comprehensive review of their Home Assistant
    automations to identify issues, optimize performance, and improve reliability.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant automation expert specializing in system optimization.
You'll help the user perform a comprehensive audit of their automations by:
1. Reviewing all automations for potential conflicts (e.g., opposing actions)
2. Identifying redundant automations that could be consolidated
3. Finding inefficient trigger patterns that might cause unnecessary processing
4. Detecting missing conditions that could improve reliability
5. Suggesting template optimizations for more efficient processing
6. Uncovering potential race conditions between automations
7. Recommending structural improvements to the automation organization
8. Highlighting best practices and suggesting implementation changes"""

    user_message = "I'd like to do a health check on all my Home Assistant automations. Can you help me review them for conflicts, redundancies, and potential improvements?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def entity_naming_consistency():
    """
    Audit entity names and suggest standardization improvements

    This prompt helps users analyze their entity naming conventions and create
    a more consistent, organized naming system across their Home Assistant instance.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant organization expert specializing in entity naming conventions.
You'll help the user audit and improve their entity naming by:
1. Analyzing current entity IDs and friendly names for inconsistencies
2. Identifying patterns in existing naming conventions
3. Suggesting standardized naming schemes based on entity types and locations
4. Creating clear guidelines for future entity naming
5. Proposing specific name changes for entities that don't follow conventions
6. Showing how to implement these changes without breaking automations
7. Explaining benefits of consistent naming for automation and UI organization"""

    user_message = "I'd like to make my Home Assistant entity names more consistent and organized. Can you help me audit my current naming conventions and suggest improvements?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


@mcp.prompt()
def dashboard_layout_generator():
    """
    Create optimized dashboards based on user preferences and usage patterns

    This prompt helps users design effective, user-friendly dashboards
    for their Home Assistant instance based on their specific needs.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant UI design expert specializing in dashboard creation.
You'll help the user create optimized dashboards by:
1. Analyzing which entities they interact with most frequently
2. Identifying logical groupings of entities (by room, function, or use case)
3. Suggesting dashboard layouts with the most important controls prominently placed
4. Creating specialized views for different contexts (mobile, tablet, wall-mounted)
5. Designing intuitive card arrangements that minimize scrolling/clicking
6. Recommending specialized cards and custom components that enhance usability
7. Balancing information density with visual clarity
8. Creating consistent visual patterns that aid in quick recognition"""

    user_message = "I'd like to redesign my Home Assistant dashboards to be more functional and user-friendly. Can you help me create optimized layouts based on how I actually use my system?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


# System tools (get_history, get_error_log, system_health, core_config) are now in app.tools.system module
# They are registered above after creating the mcp instance
