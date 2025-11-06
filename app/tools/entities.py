"""Entity MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant entities.
These tools are thin wrappers around the entities API layer.
"""

import logging
from typing import Any

from app.api.entities import get_entities, get_entity_state
from app.api.services import call_service
from app.core.cache.decorator import invalidate_cache
from app.core.vectordb.search import semantic_search  # noqa: PLC0415

logger = logging.getLogger(__name__)


async def get_entity(
    entity_id: str, fields: list[str] | None = None, detailed: bool = False
) -> dict:
    """
    Get the state of a Home Assistant entity with optional field filtering.

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


@invalidate_cache(pattern="entities:state:*")
async def entity_action(entity_id: str, action: str, params: dict[str, Any] | None = None) -> dict:
    """
    Perform an action on a Home Assistant entity (on, off, toggle).

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


async def list_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int = 100,
    fields: list[str] | None = None,
    detailed: bool = False,
) -> list[dict[str, Any]]:
    """
    Get a list of Home Assistant entities with optional filtering.

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


async def search_entities_tool(query: str, limit: int = 20) -> dict[str, Any]:
    """
    Search for entities matching a query string.

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
    }


async def semantic_search_entities_tool(  # noqa: PLR0915
    query: str,
    domain: str | None = None,
    area_id: str | None = None,
    limit: int = 10,
    similarity_threshold: float = 0.7,
    search_mode: str = "hybrid",
) -> dict[str, Any]:
    """
    Search for entities using semantic search with natural language queries.

    This tool combines semantic and keyword search to find entities more accurately
    using natural language. It supports three search modes:
    - "semantic": Pure semantic search using vector embeddings
    - "keyword": Pure keyword search (fallback)
    - "hybrid": Combines both semantic and keyword search (default)

    Args:
        query: Natural language search query (e.g., "living room lights", "temperature sensors")
        domain: Optional domain filter (e.g., "light", "sensor", "switch")
        area_id: Optional area/room filter (e.g., "living_room", "kitchen")
        limit: Maximum number of results to return (default: 10)
        similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.7)
        search_mode: Search mode - "semantic", "keyword", or "hybrid" (default: "hybrid")

    Returns:
        A dictionary containing search results and metadata:
        - query: The original search query
        - count: Total number of matching entities found
        - results: List of matching entities with similarity scores and explanations
        - search_mode: The search mode used
        - domains: Map of domains with counts (e.g. {"light": 3, "sensor": 2})

    Examples:
        query="living room lights" - Find lights in living room using natural language
        query="temperature sensors", domain="sensor" - Find temperature sensors
        query="lights", area_id="kitchen", search_mode="semantic" - Pure semantic search
        query="switches", similarity_threshold=0.8 - Higher similarity threshold
    """
    logger.info(
        f"Semantic search for entities: '{query}' (mode: {search_mode}, domain: {domain}, area: {area_id})"
    )

    # Validate search_mode
    if search_mode not in ["semantic", "keyword", "hybrid"]:
        return {
            "error": f"Invalid search_mode: {search_mode}. Must be 'semantic', 'keyword', or 'hybrid'",
            "query": query,
            "count": 0,
            "results": [],
            "search_mode": search_mode,
            "domains": {},
        }

    # Handle empty query
    if not query or not query.strip():
        logger.info("Empty query - falling back to keyword search")
        # Fall back to keyword search for empty queries
        entities = await get_entities(domain=domain, limit=limit, lean=True)
        if isinstance(entities, dict) and "error" in entities:
            return {
                "error": entities["error"],
                "query": query,
                "count": 0,
                "results": [],
                "search_mode": "keyword",
                "domains": {},
            }

        # Format results similar to search_entities_tool
        domains_count = {}
        simplified_entities = []

        for entity in entities:
            entity_domain = entity["entity_id"].split(".")[0]
            if domain and entity_domain != domain:
                continue

            if entity_domain not in domains_count:
                domains_count[entity_domain] = 0
            domains_count[entity_domain] += 1

            simplified_entity = {
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "domain": entity_domain,
                "friendly_name": entity.get("attributes", {}).get(
                    "friendly_name", entity["entity_id"]
                ),
                "similarity": 1.0,  # No similarity score for keyword-only
                "match_reason": "Keyword match (empty query)",
            }

            simplified_entities.append(simplified_entity)

        return {
            "query": query,
            "count": len(simplified_entities),
            "results": simplified_entities,
            "search_mode": "keyword",
            "domains": domains_count,
        }

    try:
        # Determine hybrid_search based on search_mode
        hybrid_search = search_mode == "hybrid"

        # Perform semantic search
        if search_mode == "keyword":
            # Use keyword search only
            entities = await get_entities(domain=domain, search_query=query, limit=limit, lean=True)

            if isinstance(entities, dict) and "error" in entities:
                return {
                    "error": entities["error"],
                    "query": query,
                    "count": 0,
                    "results": [],
                    "search_mode": "keyword",
                    "domains": {},
                }

            # Format results
            domains_count = {}
            simplified_entities = []

            for entity in entities:
                entity_domain = entity["entity_id"].split(".")[0]
                if entity_domain not in domains_count:
                    domains_count[entity_domain] = 0
                domains_count[entity_domain] += 1

                simplified_entity = {
                    "entity_id": entity["entity_id"],
                    "state": entity["state"],
                    "domain": entity_domain,
                    "friendly_name": entity.get("attributes", {}).get(
                        "friendly_name", entity["entity_id"]
                    ),
                    "similarity": 1.0,  # No similarity score for keyword-only
                    "match_reason": f"Keyword match: '{query}'",
                }

                simplified_entities.append(simplified_entity)

            return {
                "query": query,
                "count": len(simplified_entities),
                "results": simplified_entities,
                "search_mode": "keyword",
                "domains": domains_count,
            }

        # Use semantic search (semantic or hybrid mode)
        semantic_results = await semantic_search(
            query=query,
            domain=domain,
            area_id=area_id,
            limit=limit,
            similarity_threshold=similarity_threshold,
            hybrid_search=hybrid_search,
        )

        # Format results
        domains_count = {}
        simplified_entities = []

        for result in semantic_results:
            entity = result.get("entity", {})
            entity_id = result.get("entity_id")
            if not entity_id:
                continue

            entity_domain = entity_id.split(".")[0]
            if domain and entity_domain != domain:
                continue

            if entity_domain not in domains_count:
                domains_count[entity_domain] = 0
            domains_count[entity_domain] += 1

            # Build simplified entity
            simplified_entity = {
                "entity_id": entity_id,
                "state": entity.get("state"),
                "domain": entity_domain,
                "friendly_name": entity.get("attributes", {}).get("friendly_name", entity_id),
                "similarity": round(result.get("similarity_score", 0.0), 3),
                "match_reason": result.get("explanation", "Semantic match"),
            }

            # Add metadata if available
            metadata = result.get("metadata", {})
            if metadata:
                simplified_entity["metadata"] = metadata

            # Add key attributes based on domain
            attributes = entity.get("attributes", {})
            if entity_domain == "light" and "brightness" in attributes:
                simplified_entity["brightness"] = attributes["brightness"]
            elif entity_domain == "sensor" and "unit_of_measurement" in attributes:
                simplified_entity["unit"] = attributes["unit_of_measurement"]
            elif entity_domain == "climate" and "temperature" in attributes:
                simplified_entity["temperature"] = attributes["temperature"]
            elif entity_domain == "media_player" and "media_title" in attributes:
                simplified_entity["media_title"] = attributes["media_title"]

            simplified_entities.append(simplified_entity)

        return {
            "query": query,
            "count": len(simplified_entities),
            "results": simplified_entities,
            "search_mode": search_mode,
            "domains": domains_count,
        }

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        # Fall back to keyword search on error
        try:
            entities = await get_entities(domain=domain, search_query=query, limit=limit, lean=True)

            if isinstance(entities, dict) and "error" in entities:
                return {
                    "error": entities["error"],
                    "query": query,
                    "count": 0,
                    "results": [],
                    "search_mode": "keyword",
                    "domains": {},
                }

            # Format results
            domains_count = {}
            simplified_entities = []

            for entity in entities:
                entity_domain = entity["entity_id"].split(".")[0]
                if entity_domain not in domains_count:
                    domains_count[entity_domain] = 0
                domains_count[entity_domain] += 1

                simplified_entity = {
                    "entity_id": entity["entity_id"],
                    "state": entity["state"],
                    "domain": entity_domain,
                    "friendly_name": entity.get("attributes", {}).get(
                        "friendly_name", entity["entity_id"]
                    ),
                    "similarity": 1.0,
                    "match_reason": f"Keyword match (semantic search failed: {str(e)})",
                }

                simplified_entities.append(simplified_entity)

            return {
                "query": query,
                "count": len(simplified_entities),
                "results": simplified_entities,
                "search_mode": "keyword",
                "domains": domains_count,
            }
        except Exception as fallback_error:
            logger.error(f"Keyword search fallback also failed: {fallback_error}")
            return {
                "error": f"Search failed: {str(e)}",
                "query": query,
                "count": 0,
                "results": [],
                "search_mode": "keyword",
                "domains": {},
            }
