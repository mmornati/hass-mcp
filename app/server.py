import functools
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

from app.hass import (
    activate_scene,
    call_service,
    create_area,
    create_scene,
    delete_area,
    delete_automation,
    diagnose_entity,
    disable_automation,
    enable_automation,
    find_automation_conflicts,
    find_entity_dependencies,
    find_integration_errors,
    get_area_entities,
    get_area_summary,
    get_areas,
    get_automation_config,
    get_automation_execution_log,
    get_automations,
    get_core_config,
    get_device_details,
    get_device_entities,
    get_device_statistics,
    get_devices,
    get_entities,
    get_entity_history,
    get_entity_state,
    get_hass_error_log,
    get_hass_version,
    get_integration_config,
    get_integrations,
    get_scene_config,
    get_scenes,
    get_script_config,
    get_scripts,
    get_system_health,
    get_system_overview,
    reload_integration,
    reload_scenes,
    reload_scripts,
    restart_home_assistant,
    run_script,
    summarize_domain,
    test_template,
    trigger_automation,
    update_area,
    update_automation,
    validate_automation_config,
)
from app.hass import (
    create_automation as create_automation_api,
)

# Type variable for generic functions
T = TypeVar("T")

# Create an MCP server
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Hass-MCP")


def async_handler(command_type: str):
    """
    Simple decorator that logs the command

    Args:
        command_type: The type of command (for logging)
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            logger.info(f"Executing command: {command_type}")
            return await func(*args, **kwargs)

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator


@mcp.tool()
@async_handler("get_version")
async def get_version() -> str:
    """
    Get the Home Assistant version

    Returns:
        A string with the Home Assistant version (e.g., "2025.3.0")
    """
    logger.info("Getting Home Assistant version")
    return await get_hass_version()


@mcp.tool()
@async_handler("get_entity")
async def get_entity(
    entity_id: str, fields: list[str] | None = None, detailed: bool = False
) -> dict:
    """
    Get the state of a Home Assistant entity with optional field filtering

    Args:
        entity_id: The entity ID to get (e.g. 'light.living_room')
        fields: Optional list of fields to include (e.g. ['state', 'attr.brightness'])
        detailed: If True, returns all entity fields without filtering

    Examples:
        entity_id="light.living_room" - basic state check
        entity_id="light.living_room", fields=["state", "attr.brightness"] - specific fields
        entity_id="light.living_room", detailed=True - all details
    """
    logger.info(f"Getting entity state: {entity_id}")
    if detailed:
        # Return all fields
        return await get_entity_state(entity_id, lean=False)
    if fields:
        # Return only the specified fields
        return await get_entity_state(entity_id, fields=fields)
    # Return lean format with essential fields
    return await get_entity_state(entity_id, lean=True)


@mcp.tool()
@async_handler("entity_action")
async def entity_action(entity_id: str, action: str, params: dict[str, Any] | None = None) -> dict:
    """
    Perform an action on a Home Assistant entity (on, off, toggle)

    Args:
        entity_id: The entity ID to control (e.g. 'light.living_room')
        action: The action to perform ('on', 'off', 'toggle')
        params: Optional dictionary of additional parameters for the service call

    Returns:
        The response from Home Assistant

    Examples:
        entity_id="light.living_room", action="on", params={"brightness": 255}
        entity_id="switch.garden_lights", action="off"
        entity_id="climate.living_room", action="on", params={"temperature": 22.5}

    Domain-Specific Parameters:
        - Lights: brightness (0-255), color_temp, rgb_color, transition, effect
        - Covers: position (0-100), tilt_position
        - Climate: temperature, target_temp_high, target_temp_low, hvac_mode
        - Media players: source, volume_level (0-1)
    """
    if action not in ["on", "off", "toggle"]:
        return {"error": f"Invalid action: {action}. Valid actions are 'on', 'off', 'toggle'"}

    # Map action to service name
    service = action if action == "toggle" else f"turn_{action}"

    # Extract the domain from the entity_id
    domain = entity_id.split(".")[0]

    # Prepare service data
    data = {"entity_id": entity_id, **(params or {})}

    logger.info(f"Performing action '{action}' on entity: {entity_id} with params: {params}")
    return await call_service(domain, service, data)


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
    state = await get_entity_state(entity_id, use_cache=True, lean=True)

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


@mcp.tool()
@async_handler("list_entities")
async def list_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int = 100,
    fields: list[str] | None = None,
    detailed: bool = False,
) -> list[dict[str, Any]]:
    """
    Get a list of Home Assistant entities with optional filtering

    Args:
        domain: Optional domain to filter by (e.g., 'light', 'switch', 'sensor')
        search_query: Optional search term to filter entities by name, id, or attributes
                     (Note: Does not support wildcards. To get all entities, leave this empty)
        limit: Maximum number of entities to return (default: 100)
        fields: Optional list of specific fields to include in each entity
        detailed: If True, returns all entity fields without filtering

    Returns:
        A list of entity dictionaries with lean formatting by default

    Examples:
        domain="light" - get all lights
        search_query="kitchen", limit=20 - search entities
        domain="sensor", detailed=True - full sensor details

    Best Practices:
        - Use lean format (default) for most operations
        - Prefer domain filtering over no filtering
        - For domain overviews, use domain_summary_tool instead of list_entities
        - Only request detailed=True when necessary for full attribute inspection
        - To get all entity types/domains, use list_entities without a domain filter,
          then extract domains from entity_ids
    """
    log_message = "Getting entities"
    if domain:
        log_message += f" for domain: {domain}"
    if search_query:
        log_message += f" matching: '{search_query}'"
    if limit != 100:
        log_message += f" (limit: {limit})"
    if detailed:
        log_message += " (detailed format)"
    elif fields:
        log_message += f" (custom fields: {fields})"
    else:
        log_message += " (lean format)"

    logger.info(log_message)

    # Handle special case where search_query is a wildcard/asterisk - just ignore it
    if search_query == "*":
        search_query = None
        logger.info("Converting '*' search query to None (retrieving all entities)")

    # Use the updated get_entities function with field filtering
    return await get_entities(
        domain=domain,
        search_query=search_query,
        limit=limit,
        fields=fields,
        lean=not detailed,  # Use lean format unless detailed is requested
    )


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


@mcp.tool()
@async_handler("search_entities_tool")
async def search_entities_tool(query: str, limit: int = 20) -> dict[str, Any]:
    """
    Search for entities matching a query string

    Args:
        query: The search query to match against entity IDs, names, and attributes.
              (Note: Does not support wildcards. To get all entities, leave this blank or use list_entities tool)
        limit: Maximum number of results to return (default: 20)

    Returns:
        A dictionary containing search results and metadata:
        - count: Total number of matching entities found
        - results: List of matching entities with essential information
        - domains: Map of domains with counts (e.g. {"light": 3, "sensor": 2})

    Examples:
        query="temperature" - find temperature entities
        query="living room", limit=10 - find living room entities
        query="", limit=500 - list all entity types

    """
    logger.info(f"Searching for entities matching: '{query}' with limit: {limit}")

    # Special case - treat "*" as empty query to just return entities without filtering
    if query == "*":
        query = ""
        logger.info("Converting '*' to empty query (retrieving all entities up to limit)")

    # Handle empty query as a special case to just return entities up to the limit
    if not query or not query.strip():
        logger.info(f"Empty query - retrieving up to {limit} entities without filtering")
        entities = await get_entities(limit=limit, lean=True)

        # Check if there was an error
        if isinstance(entities, dict) and "error" in entities:
            return {"error": entities["error"], "count": 0, "results": [], "domains": {}}

        # No query, but we'll return a structured result anyway
        domains_count = {}
        simplified_entities = []

        for entity in entities:
            domain = entity["entity_id"].split(".")[0]

            # Count domains
            if domain not in domains_count:
                domains_count[domain] = 0
            domains_count[domain] += 1

            # Create simplified entity representation
            simplified_entity = {
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "domain": domain,
                "friendly_name": entity.get("attributes", {}).get(
                    "friendly_name", entity["entity_id"]
                ),
            }

            # Add key attributes based on domain
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

        # Return structured response for empty query
        return {
            "count": len(simplified_entities),
            "results": simplified_entities,
            "domains": domains_count,
            "query": "all entities (no filtering)",
        }

    # Normal search with non-empty query
    entities = await get_entities(search_query=query, limit=limit, lean=True)

    # Check if there was an error
    if isinstance(entities, dict) and "error" in entities:
        return {"error": entities["error"], "count": 0, "results": [], "domains": {}}

    # Prepare the results
    domains_count = {}
    simplified_entities = []

    for entity in entities:
        domain = entity["entity_id"].split(".")[0]

        # Count domains
        if domain not in domains_count:
            domains_count[domain] = 0
        domains_count[domain] += 1

        # Create simplified entity representation
        simplified_entity = {
            "entity_id": entity["entity_id"],
            "state": entity["state"],
            "domain": domain,
            "friendly_name": entity.get("attributes", {}).get("friendly_name", entity["entity_id"]),
        }

        # Add key attributes based on domain
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

    # Return structured response
    return {
        "count": len(simplified_entities),
        "results": simplified_entities,
        "domains": domains_count,
        "query": query,
    }


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


# The domain_summary_tool is already implemented, no need to duplicate it


@mcp.tool()
@async_handler("domain_summary")
async def domain_summary_tool(domain: str, example_limit: int = 3) -> dict[str, Any]:
    """
    Get a summary of entities in a specific domain

    Args:
        domain: The domain to summarize (e.g., 'light', 'switch', 'sensor')
        example_limit: Maximum number of examples to include for each state

    Returns:
        A dictionary containing:
        - total_count: Number of entities in the domain
        - state_distribution: Count of entities in each state
        - examples: Sample entities for each state
        - common_attributes: Most frequently occurring attributes

    Examples:
        domain="light" - get light summary
        domain="climate", example_limit=5 - climate summary with more examples
    Best Practices:
        - Use this before retrieving all entities in a domain to understand what's available"""
    logger.info(f"Getting domain summary for: {domain}")
    return await summarize_domain(domain, example_limit)


@mcp.tool()
@async_handler("system_overview")
async def system_overview() -> dict[str, Any]:
    """
    Get a comprehensive overview of the entire Home Assistant system

    Returns:
        A dictionary containing:
        - total_entities: Total count of all entities
        - domains: Dictionary of domains with their entity counts and state distributions
        - domain_samples: Representative sample entities for each domain (2-3 per domain)
        - domain_attributes: Common attributes for each domain
        - area_distribution: Entities grouped by area (if available)

    Examples:
        Returns domain counts, sample entities, and common attributes
    Best Practices:
        - Use this as the first call when exploring an unfamiliar Home Assistant instance
        - Perfect for building context about the structure of the smart home
        - After getting an overview, use domain_summary_tool to dig deeper into specific domains
    """
    logger.info("Generating complete system overview")
    return await get_system_overview()


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
    state = await get_entity_state(entity_id, use_cache=True, lean=False)

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


# Automation management MCP tools
@mcp.tool()
@async_handler("list_automations")
async def list_automations() -> list[dict[str, Any]]:
    """
    Get a list of all automations from Home Assistant

    This function retrieves all automations configured in Home Assistant,
    including their IDs, entity IDs, state, and display names.

    Returns:
        A list of automation dictionaries, each containing id, entity_id,
        state, and alias (friendly name) fields.

    Examples:
        Returns all automation objects with state and friendly names

    """
    logger.info("Getting all automations")
    try:
        # Get automations will now return data from states API, which is more reliable
        automations = await get_automations()

        # Handle error responses that might still occur
        if isinstance(automations, dict) and "error" in automations:
            logger.warning(f"Error getting automations: {automations['error']}")
            return []

        # Handle case where response is a list with error
        if (
            isinstance(automations, list)
            and len(automations) == 1
            and isinstance(automations[0], dict)
            and "error" in automations[0]
        ):
            logger.warning(f"Error getting automations: {automations[0]['error']}")
            return []

        return automations
    except Exception as e:
        logger.error(f"Error in list_automations: {str(e)}")
        return []


# We already have a list_automations tool, so no need to duplicate functionality


@mcp.tool()
@async_handler("restart_ha")
async def restart_ha() -> dict[str, Any]:
    """
    Restart Home Assistant

    ⚠️ WARNING: Temporarily disrupts all Home Assistant operations

    Returns:
        Result of restart operation
    """
    logger.info("Restarting Home Assistant")
    return await restart_home_assistant()


@mcp.tool()
@async_handler("call_service")
async def call_service_tool(
    domain: str, service: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Call any Home Assistant service (low-level API access)

    Args:
        domain: The domain of the service (e.g., 'light', 'switch', 'automation')
        service: The service to call (e.g., 'turn_on', 'turn_off', 'toggle')
        data: Optional data to pass to the service (e.g., {'entity_id': 'light.living_room'})

    Returns:
        The response from Home Assistant (usually empty for successful calls)

    Examples:
        domain='light', service='turn_on', data={'entity_id': 'light.x', 'brightness': 255}
        domain='automation', service='reload'
        domain='fan', service='set_percentage', data={'entity_id': 'fan.x', 'percentage': 50}

    """
    logger.info(f"Calling Home Assistant service: {domain}.{service} with data: {data}")
    return await call_service(domain, service, data or {})


@mcp.tool()
@async_handler("get_automation_config")
async def get_automation_config_tool(automation_id: str) -> dict[str, Any]:
    """
    Get full automation configuration including triggers, conditions, actions

    Args:
        automation_id: The automation ID to get (without 'automation.' prefix)

    Returns:
        Complete automation configuration dictionary with:
        - id: Automation identifier
        - alias: Display name
        - description: Automation description
        - trigger: List of trigger configurations
        - condition: List of condition configurations
        - action: List of action configurations
        - mode: Automation mode (single, restart, queued, parallel)

    Examples:
        automation_id="turn_on_lights" - get config for automation with ID turn_on_lights

    Best Practices:
        - Use this to inspect automation configuration before updating
        - Check triggers and actions to understand automation behavior
    """
    logger.info(f"Getting automation config for: {automation_id}")
    return await get_automation_config(automation_id)


@mcp.tool()
@async_handler("create_automation")
async def create_automation_tool(config: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new automation from configuration dictionary

    Args:
        config: Automation configuration dictionary with:
            - id: Automation identifier (optional, will be generated if missing)
            - alias: Display name
            - description: Automation description (optional)
            - trigger: List of trigger configurations (required)
            - condition: List of condition configurations (optional)
            - action: List of action configurations (required)
            - mode: Automation mode (optional, default: "single")

    Returns:
        Response from the create operation

    Examples:
        config={
            "alias": "Turn on lights at sunset",
            "trigger": [{"platform": "sun", "event": "sunset"}],
            "action": [{"service": "light.turn_on", "entity_id": "light.living_room"}]
        }

    Best Practices:
        - Validate config with validate_automation_config before creating
        - Include alias and description for better organization
        - Test automation after creation using trigger_automation
    """
    logger.info(f"Creating automation: {config.get('alias', config.get('id', 'new'))}")
    return await create_automation_api(config)


@mcp.tool()
@async_handler("update_automation")
async def update_automation_tool(automation_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Update an existing automation with new configuration

    Args:
        automation_id: The automation ID to update (without 'automation.' prefix)
        config: Updated automation configuration dictionary

    Returns:
        Response from the update operation

    Examples:
        automation_id="turn_on_lights"
        config={"alias": "Updated name", "trigger": [...], "action": [...]}

    Note:
        The config should include all fields you want to keep.
        Fields not included may be removed.

    Best Practices:
        - Get existing config first with get_automation_config
        - Validate config with validate_automation_config before updating
        - Test automation after update using trigger_automation
    """
    logger.info(f"Updating automation: {automation_id}")
    return await update_automation(automation_id, config)


@mcp.tool()
@async_handler("delete_automation")
async def delete_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Delete an automation

    Args:
        automation_id: The automation ID to delete (without 'automation.' prefix)

    Returns:
        Response from the delete operation

    Examples:
        automation_id="turn_on_lights" - delete automation with ID turn_on_lights

    Note:
        ⚠️ This permanently deletes the automation. There is no undo.
        Make sure the automation is not referenced by other automations or scripts.

    Best Practices:
        - Get automation config first to ensure correct ID
        - Check for dependencies before deleting
    """
    logger.info(f"Deleting automation: {automation_id}")
    return await delete_automation(automation_id)


@mcp.tool()
@async_handler("enable_automation")
async def enable_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Enable an automation

    Args:
        automation_id: The automation ID to enable (without 'automation.' prefix)

    Returns:
        Response from the enable operation

    Examples:
        automation_id="turn_on_lights" - enable automation with ID turn_on_lights

    Note:
        Enabling an automation allows it to trigger automatically.
        The automation must exist and be configured correctly.
    """
    logger.info(f"Enabling automation: {automation_id}")
    return await enable_automation(automation_id)


@mcp.tool()
@async_handler("disable_automation")
async def disable_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Disable an automation

    Args:
        automation_id: The automation ID to disable (without 'automation.' prefix)

    Returns:
        Response from the disable operation

    Examples:
        automation_id="turn_on_lights" - disable automation with ID turn_on_lights

    Note:
        Disabling prevents the automation from triggering automatically.
        The automation configuration is preserved and can be re-enabled later.

    Best Practices:
        - Disable automations temporarily for debugging
        - Re-enable when troubleshooting is complete
    """
    logger.info(f"Disabling automation: {automation_id}")
    return await disable_automation(automation_id)


@mcp.tool()
@async_handler("trigger_automation")
async def trigger_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Manually trigger an automation

    Args:
        automation_id: The automation ID to trigger (without 'automation.' prefix)

    Returns:
        Response from the trigger operation

    Examples:
        automation_id="turn_on_lights" - manually trigger automation with ID turn_on_lights

    Note:
        This manually executes the automation actions.
        Useful for testing automations without waiting for triggers.
        The automation does not need to be enabled to be triggered manually.

    Best Practices:
        - Use for testing new or updated automations
        - Check execution log after triggering to verify behavior
    """
    logger.info(f"Triggering automation: {automation_id}")
    return await trigger_automation(automation_id)


@mcp.tool()
@async_handler("get_automation_execution_log")
async def get_automation_execution_log_tool(automation_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get automation execution history from logbook

    Args:
        automation_id: The automation ID to get history for (without 'automation.' prefix)
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        Dictionary containing:
        - automation_id: The automation ID requested
        - executions: List of execution events with timestamps
        - count: Number of executions found
        - time_range: Dictionary with start_time and end_time

    Examples:
        automation_id="turn_on_lights", hours=24 - get last 24 hours of execution history

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use to debug why an automation isn't firing
        - Check execution frequency to optimize automation triggers
    """
    logger.info(f"Getting execution log for automation: {automation_id}, hours: {hours}")
    return await get_automation_execution_log(automation_id, hours)


@mcp.tool()
@async_handler("validate_automation_config")
async def validate_automation_config_tool(config: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an automation configuration

    Args:
        config: Automation configuration dictionary to validate

    Returns:
        Dictionary with validation results:
        - valid: Boolean indicating if config is valid
        - errors: List of validation errors (empty if valid)
        - warnings: List of validation warnings
        - suggestions: List of improvement suggestions

    Validation checks:
        - Required fields present (trigger, action)
        - Trigger structure is valid
        - Action structure is valid
        - Condition structure is valid (if provided)
        - Mode value is valid

    Examples:
        config={
            "trigger": [{"platform": "sun", "event": "sunset"}],
            "action": [{"service": "light.turn_on", "entity_id": "light.living_room"}]
        }

    Best Practices:
        - Always validate config before creating or updating
        - Review warnings and suggestions for improvements
        - Fix errors before attempting to create automation
    """
    logger.info("Validating automation config")
    return await validate_automation_config(config)


@mcp.tool()
@async_handler("list_scripts")
async def list_scripts_tool() -> list[dict[str, Any]]:
    """
    Get a list of all scripts in Home Assistant

    Returns:
        List of script dictionaries containing:
        - entity_id: The script entity ID (e.g., 'script.turn_on_lights')
        - state: Current state of the script
        - friendly_name: Display name of the script
        - alias: Script alias/name
        - last_triggered: Timestamp of last execution (if available)

    Examples:
        Returns all scripts with their current state and metadata

    Best Practices:
        - Use this to discover available scripts before executing
        - Check state to see if script is currently running
        - Use last_triggered to see when script was last executed
    """
    logger.info("Getting list of scripts")
    return await get_scripts()


@mcp.tool()
@async_handler("get_script")
async def get_script_tool(script_id: str) -> dict[str, Any]:
    """
    Get script configuration and details

    Args:
        script_id: The script ID to get (without 'script.' prefix)

    Returns:
        Script configuration dictionary with:
        - entity_id: The script entity ID
        - state: Current state
        - attributes: Script attributes including configuration
        - config: Script configuration if available via config API

    Examples:
        script_id="turn_on_lights" - get config for script with ID turn_on_lights

    Note:
        Script configuration might be available via config API or
        only through entity state depending on Home Assistant version.

    Best Practices:
        - Use this to inspect what actions a script performs
        - Check configuration before executing scripts
    """
    logger.info(f"Getting script config for: {script_id}")
    return await get_script_config(script_id)


@mcp.tool()
@async_handler("run_script")
async def run_script_tool(
    script_id: str, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Execute a script with optional variables

    Args:
        script_id: The script ID to execute (without 'script.' prefix)
        variables: Optional dictionary of variables to pass to the script

    Returns:
        Response from the script execution

    Examples:
        script_id="turn_on_lights" - execute script with ID turn_on_lights
        script_id="notify", variables={"message": "Hello", "target": "user1"} - execute with variables

    Note:
        Scripts execute asynchronously. The response indicates the script was started,
        not necessarily that it completed.

    Best Practices:
        - Get script config first to understand what variables are needed
        - Check script state before executing
        - Use variables to customize script behavior
    """
    logger.info(
        f"Running script: {script_id}" + (f" with variables: {variables}" if variables else "")
    )
    return await run_script(script_id, variables)


@mcp.tool()
@async_handler("reload_scripts")
async def reload_scripts_tool() -> dict[str, Any]:
    """
    Reload all scripts from configuration

    Returns:
        Response from the reload operation

    Examples:
        Reloads all script configurations after modifying YAML files

    Note:
        Reloading scripts reloads all script configurations from YAML files.
        This is useful after modifying script configuration files.

    Best Practices:
        - Reload scripts after making configuration changes
        - Use this after updating script YAML files
    """
    logger.info("Reloading scripts")
    return await reload_scripts()


@mcp.tool()
@async_handler("test_template")
async def test_template_tool(
    template_string: str,
    entity_context: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test Jinja2 template rendering

    Args:
        template_string: The Jinja2 template string to test
        entity_context: Optional dictionary of entity IDs to provide as context
                         (e.g., {"entity_id": "light.living_room"})

    Returns:
        Dictionary containing:
        - result: The rendered template result
        - listeners: Entity listeners (if applicable)
        - error: Error message if template rendering failed

    Examples:
        template_string="{{ states('sensor.temperature') }}" - test simple template
        template_string="{{ states('light.living_room') }}", entity_context={"entity_id": "light.living_room"}

    Note:
        Template testing API might not be available in all Home Assistant versions.
        If unavailable, returns a helpful error message.

    Best Practices:
        - Test templates before using them in automations or scripts
        - Use entity_context to test templates with specific entity context
        - Check for errors in the response
    """
    logger.info(
        f"Testing template: {template_string[:50]}..."
        + (f" with context: {entity_context}" if entity_context else "")
    )
    return await test_template(template_string, entity_context)


@mcp.tool()
@async_handler("list_areas")
async def list_areas_tool() -> list[dict[str, Any]]:
    """
    Get a list of all areas in Home Assistant

    Returns:
        List of area dictionaries containing:
        - area_id: Unique identifier for the area
        - name: Display name of the area
        - aliases: List of aliases for the area
        - picture: Path to area picture (if available)

    Examples:
        Returns all areas with their configuration

    Best Practices:
        - Use this to discover available areas before operations
        - Check area names and aliases to find specific areas
    """
    logger.info("Getting list of areas")
    return await get_areas()


@mcp.tool()
@async_handler("get_area_entities")
async def get_area_entities_tool(area_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific area

    Args:
        area_id: The area ID to get entities for

    Returns:
        List of entities in the specified area

    Examples:
        area_id="living_room" - get all entities in the living room area

    Note:
        Entities are filtered by their area_id attribute.
        Returns empty list if area has no entities or area doesn't exist.

    Best Practices:
        - Use this to see what entities are in an area before deleting it
        - Use to organize entities by location
    """
    logger.info(f"Getting entities for area: {area_id}")
    return await get_area_entities(area_id)


@mcp.tool()
@async_handler("create_area")
async def create_area_tool(
    name: str,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Create a new area

    Args:
        name: Display name for the area (required)
        aliases: Optional list of aliases for the area
        picture: Optional path to area picture

    Returns:
        Created area dictionary with area_id and configuration

    Examples:
        name="Living Room" - create area with just name
        name="Living Room", aliases=["lounge", "salon"] - create area with aliases

    Note:
        Area IDs are automatically generated by Home Assistant.
        Duplicate names are allowed but may cause confusion.

    Best Practices:
        - Use descriptive names for areas
        - Add aliases for common alternative names
        - Use pictures to visually identify areas in dashboards
    """
    logger.info(f"Creating area: {name}")
    return await create_area(name, aliases, picture)


@mcp.tool()
@async_handler("update_area")
async def update_area_tool(
    area_id: str,
    name: str | None = None,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing area

    Args:
        area_id: The area ID to update
        name: Optional new name for the area
        aliases: Optional new list of aliases (replaces existing)
        picture: Optional new picture path

    Returns:
        Updated area dictionary

    Examples:
        area_id="living_room", name="Family Room" - update area name
        area_id="living_room", aliases=["lounge", "salon"] - update aliases

    Note:
        Only provided fields will be updated. Fields not provided remain unchanged.
        If aliases is provided, it replaces all existing aliases.

    Best Practices:
        - Get area first with list_areas to verify area_id
        - Update one field at a time or all together
        - Remember that aliases replace existing ones
    """
    logger.info(f"Updating area: {area_id}")
    return await update_area(area_id, name, aliases, picture)


@mcp.tool()
@async_handler("delete_area")
async def delete_area_tool(area_id: str) -> dict[str, Any]:
    """
    Delete an area

    Args:
        area_id: The area ID to delete

    Returns:
        Response from the delete operation

    Examples:
        area_id="living_room" - delete area with ID living_room

    Note:
        ⚠️ This permanently deletes the area. There is no undo.
        Entities associated with this area will have their area_id removed.
        Make sure to check for entities before deleting, or use get_area_entities first.

    Best Practices:
        - Check for entities with get_area_entities before deleting
        - Verify area_id is correct before deletion
        - Consider updating entities to a new area instead of deleting
    """
    logger.info(f"Deleting area: {area_id}")
    return await delete_area(area_id)


@mcp.tool()
@async_handler("get_area_summary")
async def get_area_summary_tool() -> dict[str, Any]:
    """
    Get summary of all areas with device/entity distribution

    Returns:
        Dictionary containing:
        - total_areas: Total number of areas
        - areas: Dictionary mapping area_id to area summary with:
            - name: Area name
            - entity_count: Number of entities in the area
            - domain_counts: Dictionary of domain counts (e.g., {"light": 3, "switch": 2})

    Examples:
        Returns summary of all areas with entity distribution

    Best Practices:
        - Use this to understand entity distribution across areas
        - Identify areas with no entities
        - Analyze domain distribution by area
    """
    logger.info("Getting area summary")
    return await get_area_summary()


@mcp.tool()
@async_handler("list_devices")
async def list_devices_tool(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all devices in Home Assistant, optionally filtered by integration domain

    Args:
        domain: Optional integration domain to filter devices by (e.g., 'hue', 'zwave')

    Returns:
        List of device dictionaries containing:
        - id: Unique device identifier
        - name: Device name
        - manufacturer: Manufacturer name
        - model: Model name
        - via_device_id: Parent device ID if device is connected via another device
        - area_id: Area ID the device belongs to
        - entities: List of entity IDs belonging to this device
        - identifiers: List of identifier tuples
        - connections: List of connection tuples (MAC addresses, etc.)

    Examples:
        domain=None - get all devices
        domain="hue" - get all Philips Hue devices

    Best Practices:
        - Use this to discover available devices
        - Filter by domain to find devices from specific integrations
        - Check device identifiers to understand device topology
    """
    logger.info("Getting list of devices" + (f" for domain: {domain}" if domain else ""))
    return await get_devices(domain)


@mcp.tool()
@async_handler("get_device")
async def get_device_tool(device_id: str) -> dict[str, Any]:
    """
    Get detailed device information

    Args:
        device_id: The device ID to get details for

    Returns:
        Detailed device dictionary with:
        - id: Unique device identifier
        - name: Device name
        - manufacturer: Manufacturer name
        - model: Model name
        - via_device_id: Parent device ID if device is connected via another device
        - area_id: Area ID the device belongs to
        - name_by_user: User-defined name (if set)
        - disabled_by: Reason device is disabled (if disabled)
        - entities: List of entity IDs belonging to this device
        - identifiers: List of identifier tuples
        - connections: List of connection tuples (MAC addresses, etc.)

    Examples:
        device_id="abc123" - get details for device with ID abc123

    Note:
        This provides the same information as list_devices but for a single device.
        Useful when you already know the device_id.

    Best Practices:
        - Use this to inspect device details
        - Check manufacturer and model for device identification
        - Review connections to understand device topology
    """
    logger.info(f"Getting device details for: {device_id}")
    return await get_device_details(device_id)


@mcp.tool()
@async_handler("get_device_entities")
async def get_device_entities_tool(device_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific device

    Args:
        device_id: The device ID to get entities for

    Returns:
        List of entity dictionaries belonging to the device

    Examples:
        device_id="abc123" - get all entities for device with ID abc123

    Note:
        Entities are retrieved from the device's entity list.
        Returns empty list if device has no entities or device doesn't exist.

    Best Practices:
        - Use this to understand what a device controls
        - Check entities to see device capabilities
        - Use before removing or disabling a device
    """
    logger.info(f"Getting entities for device: {device_id}")
    return await get_device_entities(device_id)


@mcp.tool()
@async_handler("get_device_stats")
async def get_device_stats_tool() -> dict[str, Any]:
    """
    Get statistics about devices (counts by manufacturer, model, etc.)

    Returns:
        Dictionary containing:
        - total_devices: Total number of devices
        - by_manufacturer: Dictionary mapping manufacturer to count
        - by_model: Dictionary mapping model to count
        - by_integration: Dictionary mapping integration domain to count
        - disabled_devices: Number of disabled devices

    Examples:
        Returns statistics about all devices in the system

    Best Practices:
        - Use this to understand device distribution
        - Identify common manufacturers and models
        - See which integrations have the most devices
        - Track disabled devices
    """
    logger.info("Getting device statistics")
    return await get_device_statistics()


@mcp.tool()
@async_handler("list_scenes")
async def list_scenes_tool() -> list[dict[str, Any]]:
    """
    Get a list of all scenes in Home Assistant

    Returns:
        List of scene dictionaries containing:
        - entity_id: The scene entity ID (e.g., 'scene.living_room_dim')
        - state: Current state of the scene
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene
        - snapshot: Snapshot of entity states when scene was created

    Examples:
        Returns all scenes with their configuration

    Best Practices:
        - Use this to discover available scenes
        - Check entity_id_list to see what entities a scene affects
        - Review snapshots to understand scene states
    """
    logger.info("Getting list of scenes")
    return await get_scenes()


@mcp.tool()
@async_handler("get_scene")
async def get_scene_tool(scene_id: str) -> dict[str, Any]:
    """
    Get scene configuration (what entities/values it saves)

    Args:
        scene_id: The scene ID to get (with or without 'scene.' prefix)

    Returns:
        Scene configuration dictionary with:
        - entity_id: The scene entity ID
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene
        - snapshot: Snapshot of entity states when scene was created

    Examples:
        scene_id="living_room_dim" - get config for scene with ID living_room_dim
        scene_id="scene.living_room_dim" - also works with full entity ID

    Note:
        Scene configuration shows what entities are included in the scene
        and what states they were in when the scene was created.

    Best Practices:
        - Use this to inspect what entities a scene affects
        - Check snapshot to see what states will be restored
    """
    logger.info(f"Getting scene config for: {scene_id}")
    return await get_scene_config(scene_id)


@mcp.tool()
@async_handler("create_scene")
async def create_scene_tool(
    name: str,
    entity_ids: list[str],
    states: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new scene

    Args:
        name: Display name for the scene
        entity_ids: List of entity IDs to include in the scene
        states: Optional dictionary of entity states to capture (if None, captures current states)

    Returns:
        Response from the create operation, or error message with YAML example if creation fails

    Examples:
        name="Living Room Dim", entity_ids=["light.living_room", "light.kitchen"]
        name="Movie Mode", entity_ids=["light.living_room"], states={"light.living_room": {"state": "on", "brightness": 50}}

    Note:
        ⚠️ Scene creation via API may not be available in all Home Assistant versions.
        If it fails, a helpful YAML configuration example is returned.

    Best Practices:
        - Try creating via API first
        - If it fails, use the provided YAML example for manual creation
        - Include states parameter to specify exact entity states
    """
    logger.info(f"Creating scene: {name} with entities: {entity_ids}")
    return await create_scene(name, entity_ids, states)


@mcp.tool()
@async_handler("activate_scene")
async def activate_scene_tool(scene_id: str) -> dict[str, Any]:
    """
    Activate/restore a scene

    Args:
        scene_id: The scene ID to activate (with or without 'scene.' prefix)

    Returns:
        Response from the activate operation

    Examples:
        scene_id="living_room_dim" - activate scene with ID living_room_dim
        scene_id="scene.living_room_dim" - also works with full entity ID

    Note:
        Activating a scene restores all entities to their saved states.
        The scene entity_id can be provided with or without the 'scene.' prefix.

    Best Practices:
        - Use this to restore lighting presets and room configurations
        - Get scene config first to see what will be restored
    """
    logger.info(f"Activating scene: {scene_id}")
    return await activate_scene(scene_id)


@mcp.tool()
@async_handler("reload_scenes")
async def reload_scenes_tool() -> dict[str, Any]:
    """
    Reload scenes from configuration

    Returns:
        Response from the reload operation

    Examples:
        Reloads all scene configurations after modifying YAML files

    Note:
        Reloading scenes reloads all scene configurations from YAML files.
        This is useful after modifying scene configuration files.

    Best Practices:
        - Reload scenes after making configuration changes
        - Use this after updating scene YAML files
    """
    logger.info("Reloading scenes")
    return await reload_scenes()


@mcp.tool()
@async_handler("diagnose_entity")
async def diagnose_entity_tool(entity_id: str) -> dict[str, Any]:
    """
    Comprehensive entity diagnostics

    Args:
        entity_id: The entity ID to diagnose

    Returns:
        Dictionary containing:
        - entity_id: The entity ID being diagnosed
        - status: Dictionary with status information (state, domain, last_updated_age_seconds)
        - issues: List of issues found
        - recommendations: List of recommendations to fix issues

    Examples:
        entity_id="light.living_room" - diagnose light entity
        entity_id="sensor.temperature" - diagnose sensor entity

    Best Practices:
        - Use this to diagnose why an entity isn't working
        - Check issues and recommendations for actionable steps
        - Review integration status if entity is unavailable
    """
    logger.info(f"Diagnosing entity: {entity_id}")
    return await diagnose_entity(entity_id)


@mcp.tool()
@async_handler("check_entity_dependencies")
async def check_entity_dependencies_tool(entity_id: str) -> dict[str, Any]:
    """
    Find what depends on this entity (automations, scripts, etc.)

    Args:
        entity_id: The entity ID to check dependencies for

    Returns:
        Dictionary containing:
        - entity_id: The entity ID being checked
        - automations: List of automations that use this entity
        - scripts: List of scripts that use this entity
        - scenes: List of scenes that use this entity

    Examples:
        entity_id="light.living_room" - find dependencies for light entity

    Best Practices:
        - Use this before deleting or disabling an entity
        - Check dependencies to understand entity impact
        - Review automations and scripts that depend on the entity
    """
    logger.info(f"Checking dependencies for entity: {entity_id}")
    return await find_entity_dependencies(entity_id)


@mcp.tool()
@async_handler("analyze_automation_conflicts")
async def analyze_automation_conflicts_tool() -> dict[str, Any]:
    """
    Detect conflicting automations (opposing actions, redundant triggers, etc.)

    Returns:
        Dictionary containing:
        - total_automations: Total number of automations checked
        - conflicts: List of conflicts found
        - warnings: List of warnings

    Examples:
        Returns analysis of all automations for conflicts

    Best Practices:
        - Use this to identify potential automation conflicts
        - Review conflicts to ensure automations work as intended
        - Consider automation modes (single, restart, queued, parallel) when reviewing
    """
    logger.info("Analyzing automation conflicts")
    return await find_automation_conflicts()


@mcp.tool()
@async_handler("get_integration_errors")
async def get_integration_errors_tool(domain: str | None = None) -> dict[str, Any]:
    """
    Get errors specific to integrations

    Args:
        domain: Optional integration domain to filter errors by

    Returns:
        Dictionary containing:
        - integration_errors: Dictionary mapping integration name to list of errors
        - total_integrations_with_errors: Number of integrations with errors
        - note: Note about error source

    Examples:
        domain=None - get errors for all integrations
        domain="hue" - get errors for hue integration only

    Best Practices:
        - Use this to identify integration-specific issues
        - Filter by domain to focus on specific integration
        - Review errors to understand integration problems
    """
    logger.info("Getting integration errors" + (f" for domain: {domain}" if domain else ""))
    return await find_integration_errors(domain)


@mcp.tool()
@async_handler("list_integrations")
async def list_integrations(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all configuration entries (integrations) from Home Assistant

    Args:
        domain: Optional domain to filter integrations by (e.g., 'mqtt', 'zwave')

    Returns:
        List of integration entries with their status and configuration.
        Each entry contains:
        - entry_id: Unique identifier for the integration entry
        - domain: The integration domain (e.g., 'mqtt', 'zwave')
        - title: Display name of the integration
        - source: Where the integration was configured (user, discovery, etc.)
        - state: Current state (loaded, setup_error, etc.)
        - supports_options: Whether the integration supports configuration options
        - pref_disable_new_entities: Preference to disable new entities
        - pref_disable_polling: Preference to disable polling

    Examples:
        domain=None - get all integrations
        domain="mqtt" - get only MQTT integrations

    Best Practices:
        - Use domain filter to find specific integration types
        - Check state field to identify integrations with errors
        - Use get_integration_config for detailed information
    """
    logger.info("Getting integrations" + (f" for domain: {domain}" if domain else ""))
    return await get_integrations(domain)


@mcp.tool()
@async_handler("get_integration_config")
async def get_integration_config_tool(entry_id: str) -> dict[str, Any]:
    """
    Get detailed configuration for a specific integration entry

    Args:
        entry_id: The entry ID of the integration to get

    Returns:
        Detailed configuration dictionary for the integration entry, including:
        - entry_id: Unique identifier
        - domain: Integration domain
        - title: Display name
        - source: Configuration source
        - state: Current state (loaded, setup_error, etc.)
        - options: Integration-specific configuration options
        - pref_disable_new_entities: Preference setting
        - pref_disable_polling: Preference setting

    Examples:
        entry_id="abc123" - get configuration for entry with ID abc123

    Error Handling:
        - Returns error dict if entry_id doesn't exist (404)
        - Error handling is managed by handle_api_errors decorator
    """
    logger.info(f"Getting integration config for entry: {entry_id}")
    return await get_integration_config(entry_id)


@mcp.tool()
@async_handler("reload_integration")
async def reload_integration_tool(entry_id: str) -> dict[str, Any]:
    """
    Reload a specific integration

    Args:
        entry_id: The entry ID of the integration to reload

    Returns:
        Response from the reload service call

    Examples:
        entry_id="abc123" - reload integration with ID abc123

    Note:
        ⚠️ Reloading an integration may cause temporary unavailability of its entities.
        Use with caution, especially for critical integrations like MQTT or Z-Wave.

    Best Practices:
        - Check integration state before reloading
        - Reload integrations that are showing setup errors
        - Avoid reloading during active automation execution
    """
    logger.info(f"Reloading integration: {entry_id}")
    return await reload_integration(entry_id)


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


# Documentation endpoint
@mcp.tool()
@async_handler("get_history")
async def get_history(entity_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get the history of an entity's state changes

    Args:
        entity_id: The entity ID to get history for
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        A dictionary containing:
        - entity_id: The entity ID requested
        - states: List of state objects with timestamps
        - count: Number of state changes found
        - first_changed: Timestamp of earliest state change
        - last_changed: Timestamp of most recent state change

    Examples:
        entity_id="light.living_room" - get 24h history
        entity_id="sensor.temperature", hours=168 - get 7 day history
    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use for entities with discrete state changes rather than continuously changing sensors
        - Consider the state distribution rather than every individual state
    """
    logger.info(f"Getting history for entity: {entity_id}, hours: {hours}")

    try:
        # Call the new hass function to get history
        history_data = await get_entity_history(entity_id, hours)

        # Check for errors from the API call
        if isinstance(history_data, dict) and "error" in history_data:
            return {
                "entity_id": entity_id,
                "error": history_data["error"],
                "states": [],
                "count": 0,
            }

        # The result from the API is a list of lists of state changes
        # We need to flatten it and process it
        states = []
        if history_data and isinstance(history_data, list):
            for state_list in history_data:
                states.extend(state_list)

        if not states:
            return {
                "entity_id": entity_id,
                "states": [],
                "count": 0,
                "first_changed": None,
                "last_changed": None,
                "note": "No state changes found in the specified timeframe.",
            }

        # Sort states by last_changed timestamp
        states.sort(key=lambda x: x.get("last_changed", ""))

        # Extract first and last changed timestamps
        first_changed = states[0].get("last_changed")
        last_changed = states[-1].get("last_changed")

        return {
            "entity_id": entity_id,
            "states": states,
            "count": len(states),
            "first_changed": first_changed,
            "last_changed": last_changed,
        }
    except Exception as e:
        logger.error(f"Error processing history for {entity_id}: {str(e)}")
        return {
            "entity_id": entity_id,
            "error": f"Error processing history: {str(e)}",
            "states": [],
            "count": 0,
        }


@mcp.tool()
@async_handler("get_error_log")
async def get_error_log() -> dict[str, Any]:
    """
    Get the Home Assistant error log for troubleshooting

    Returns:
        A dictionary containing:
        - log_text: The full error log text
        - error_count: Number of ERROR entries found
        - warning_count: Number of WARNING entries found
        - integration_mentions: Map of integration names to mention counts
        - error: Error message if retrieval failed

    Examples:
        Returns errors, warnings count and integration mentions
    Best Practices:
        - Use this tool when troubleshooting specific Home Assistant errors
        - Look for patterns in repeated errors
        - Pay attention to timestamps to correlate errors with events
        - Focus on integrations with many mentions in the log
    """
    logger.info("Getting Home Assistant error log")
    return await get_hass_error_log()


@mcp.tool()
@async_handler("get_system_health")
async def system_health() -> dict[str, Any]:
    """
    Get system health information from Home Assistant

    Returns:
        A dictionary containing system health information for each component.
        Each component includes health status and version information.

        Example response:
        {
            "homeassistant": {
                "healthy": true,
                "version": "2025.3.0"
            },
            "supervisor": {
                "healthy": true,
                "version": "2025.03.1"
            }
        }

    Examples:
        Check overall system health and component status

    Best Practices:
        - Use this tool to monitor system resources and health
        - Check after updates or when experiencing issues
        - Review all component health statuses, not just overall health
        - Note that some components may not be available in all HA installations
          (e.g., supervisor is only available on Home Assistant OS)

    Error Handling:
        - Returns error if endpoint is not available (some HA versions/configurations)
        - Gracefully handles missing components
        - Returns helpful error messages for permission issues
    """
    logger.info("Getting Home Assistant system health")
    return await get_system_health()


@mcp.tool()
@async_handler("get_core_config")
async def core_config() -> dict[str, Any]:
    """
    Get core configuration from Home Assistant

    Returns:
        A dictionary containing core configuration information including:
        - location_name: The name of the location
        - time_zone: Configured timezone
        - unit_system: Unit system configuration (temperature, length, mass, volume)
        - components: List of all loaded components/integrations
        - version: Home Assistant version
        - latitude/longitude: Location coordinates
        - elevation: Elevation above sea level
        - currency: Configured currency
        - country: Configured country code
        - language: Configured language

        Example response:
        {
            "location_name": "Home",
            "time_zone": "America/New_York",
            "unit_system": {
                "length": "km",
                "mass": "g",
                "temperature": "°C",
                "volume": "L"
            },
            "version": "2025.3.0",
            "components": ["mqtt", "hue", "automation", ...]
        }

    Examples:
        Get timezone, unit system, and location information
        List all loaded components/integrations
        Check Home Assistant version and configuration details

    Best Practices:
        - Use to understand the HA instance configuration
        - Check which components are loaded before using specific integrations
        - Verify timezone and unit system settings for automations
        - Use for debugging location-based automations
    """
    logger.info("Getting Home Assistant core configuration")
    return await get_core_config()
