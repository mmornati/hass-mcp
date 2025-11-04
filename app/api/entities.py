"""Entities API module for hass-mcp.

This module provides functions for interacting with Home Assistant entities.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.config import HA_URL, get_ha_headers
from app.core import DEFAULT_LEAN_FIELDS, DOMAIN_IMPORTANT_ATTRIBUTES, get_client
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG, TTL_SHORT
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


def filter_fields(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """
    Filter entity data to only include requested fields.

    This function helps reduce token usage by returning only requested fields.

    Args:
        data: The complete entity data dictionary
        fields: List of fields to include in the result
               - "state": Include the entity state
               - "attributes": Include all attributes
               - "attr.X": Include only attribute X (e.g. "attr.brightness")
               - "context": Include context data
               - "last_updated"/"last_changed": Include timestamp fields

    Returns:
        A filtered dictionary with only the requested fields
    """
    if not fields:
        return data

    result = {"entity_id": data["entity_id"]}

    for field in fields:
        if field == "state":
            result["state"] = data.get("state")
        elif field == "attributes":
            result["attributes"] = data.get("attributes", {})
        elif field.startswith("attr.") and len(field) > 5:
            attr_name = field[5:]
            attributes = data.get("attributes", {})
            if attr_name in attributes:
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"][attr_name] = attributes[attr_name]
        elif field == "context":
            if "context" in data:
                result["context"] = data["context"]
        elif field in ["last_updated", "last_changed"]:
            if field in data:
                result[field] = data[field]

    return result


async def get_all_entity_states() -> dict[str, dict[str, Any]]:
    """
    Fetch all entity states from Home Assistant.

    Returns:
        Dictionary mapping entity_id to entity state dictionary
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
    response.raise_for_status()
    entities = response.json()

    # Create a mapping for easier access
    return cast(dict[str, dict[str, Any]], {entity["entity_id"]: entity for entity in entities})


def should_cache_entity_state(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> bool:
    """Only cache if result is successful and entity is available."""
    if isinstance(result, dict):
        # Don't cache error responses
        if "error" in result:
            return False
        # Don't cache if entity state is "unknown" or "unavailable"
        state = result.get("state", "").lower()
        if state in ("unknown", "unavailable"):
            return False
    return True


@handle_api_errors
@cached(
    ttl=TTL_SHORT,
    key_prefix="entities:state",
    condition=should_cache_entity_state,
)
async def get_entity_state(
    entity_id: str, fields: list[str] | None = None, lean: bool = False
) -> dict[str, Any]:
    """
    Get the state of a Home Assistant entity.

    Args:
        entity_id: The entity ID to get
        fields: Optional list of specific fields to include in the response
        lean: If True, returns a token-efficient version with minimal fields
              (overridden by fields parameter if provided)

    Returns:
        Entity state dictionary, optionally filtered to include only specified fields
    """
    # Fetch directly
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states/{entity_id}", headers=get_ha_headers())
    response.raise_for_status()
    entity_data = response.json()

    # Apply field filtering if requested
    if fields:
        # User-specified fields take precedence
        return filter_fields(entity_data, fields)
    if lean:
        # Build domain-specific lean fields
        lean_fields = DEFAULT_LEAN_FIELDS.copy()

        # Add domain-specific important attributes
        domain = entity_id.split(".")[0]
        if domain in DOMAIN_IMPORTANT_ATTRIBUTES:
            for attr in DOMAIN_IMPORTANT_ATTRIBUTES[domain]:
                lean_fields.append(f"attr.{attr}")

        return filter_fields(entity_data, lean_fields)
    # Return full entity data
    return cast(dict[str, Any], entity_data)


def should_cache_entities(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> bool:
    """Only cache if result is successful."""
    if isinstance(result, dict) and "error" in result:
        return False
    if isinstance(result, list) and len(result) == 1:
        if isinstance(result[0], dict) and "error" in result[0]:
            return False
    return True


def get_entities_ttl(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> int:
    """Determine TTL based on whether lean mode is used or fields are specified."""
    # If lean=False or fields are specified, we're including state info, use TTL_SHORT
    # If lean=True and no fields, we're getting metadata only, use TTL_LONG
    lean = kwargs.get("lean", True)
    fields = kwargs.get("fields")

    # If fields are specified, we're including state info
    if fields:
        return TTL_SHORT
    # If lean=False, we're including state info
    if not lean:
        return TTL_SHORT
    # Otherwise, metadata only, use TTL_LONG
    return TTL_LONG


@handle_api_errors
@cached(ttl=get_entities_ttl, key_prefix="entities", condition=should_cache_entities)
async def get_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int = 100,
    fields: list[str] | None = None,
    lean: bool = True,
) -> list[dict[str, Any]]:
    """
    Get a list of all entities from Home Assistant with optional filtering and search.

    Args:
        domain: Optional domain to filter entities by (e.g., 'light', 'switch')
        search_query: Optional case-insensitive search term to filter by entity_id,
                     friendly_name or other attributes
        limit: Maximum number of entities to return (default: 100)
        fields: Optional list of specific fields to include in each entity
        lean: If True (default), returns token-efficient versions with minimal fields

    Returns:
        List of entity dictionaries, optionally filtered by domain and search terms,
        and optionally limited to specific fields
    """
    # Get all entities directly
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
    response.raise_for_status()
    entities = response.json()

    # Filter by domain if specified
    if domain:
        entities = [entity for entity in entities if entity["entity_id"].startswith(f"{domain}.")]

    # Search if query is provided
    if search_query and search_query.strip():
        search_term = search_query.lower().strip()
        filtered_entities = []

        for entity in entities:
            # Search in entity_id
            if search_term in entity["entity_id"].lower():
                filtered_entities.append(entity)
                continue

            # Search in friendly_name
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            if friendly_name and search_term in friendly_name:
                filtered_entities.append(entity)
                continue

            # Search in other common attributes (state, area_id, etc.)
            if search_term in entity.get("state", "").lower():
                filtered_entities.append(entity)
                continue

            # Search in other attributes
            for _attr_name, attr_value in entity.get("attributes", {}).items():
                # Check if attribute value can be converted to string
                if isinstance(attr_value, (str, int, float, bool)):
                    if search_term in str(attr_value).lower():
                        filtered_entities.append(entity)
                        break

        entities = filtered_entities

    # Apply the limit
    if limit > 0 and len(entities) > limit:
        entities = entities[:limit]

    # Apply field filtering if requested
    if fields:
        # Use explicit field list when provided
        return [filter_fields(entity, fields) for entity in entities]
    if lean:
        # Apply domain-specific lean fields to each entity
        result = []
        for entity in entities:
            # Get the entity's domain
            entity_domain = entity["entity_id"].split(".")[0]

            # Start with basic lean fields
            lean_fields = DEFAULT_LEAN_FIELDS.copy()

            # Add domain-specific important attributes
            if entity_domain in DOMAIN_IMPORTANT_ATTRIBUTES:
                for attr in DOMAIN_IMPORTANT_ATTRIBUTES[entity_domain]:
                    lean_fields.append(f"attr.{attr}")

            # Filter and add to result
            result.append(filter_fields(entity, lean_fields))

        return result
    # Return full entities
    return cast(list[dict[str, Any]], entities)


# NOTE: This function is explicitly excluded from caching (US-006)
# History data is highly dynamic and time-sensitive, so it should not be cached
@handle_api_errors
async def get_entity_history(entity_id: str, hours: int) -> list[dict[str, Any]]:
    """
    Get the history of an entity's state changes from Home Assistant.

    Args:
        entity_id: The entity ID to get history for.
        hours: Number of hours of history to retrieve.

    Returns:
        A list of state change objects, or an error dictionary.
    """
    client = await get_client()

    # Calculate the end time for the history lookup
    end_time = datetime.now(UTC)
    end_time_iso = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Calculate the start time for the history lookup based on end_time
    start_time = end_time - timedelta(hours=hours)
    start_time_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the API URL
    url = f"{HA_URL}/api/history/period/{start_time_iso}"

    # Set query parameters
    params = {
        "filter_entity_id": entity_id,
        "minimal_response": "true",
        "end_time": end_time_iso,
    }

    # Make the API call
    response = await client.get(url, headers=get_ha_headers(), params=params)
    response.raise_for_status()

    # Return the JSON response
    return response.json()


@handle_api_errors
@cached(ttl=TTL_SHORT, key_prefix="entities")
async def summarize_domain(domain: str, example_limit: int = 3) -> dict[str, Any]:
    """
    Generate a summary of entities in a domain.

    Args:
        domain: The domain to summarize (e.g., 'light', 'switch')
        example_limit: Maximum number of examples to include for each state

    Returns:
        Dictionary with summary information containing:
        - domain: The domain name
        - total_count: Total number of entities in the domain
        - state_distribution: Count of entities in each state
        - examples: Sample entities for each state
        - common_attributes: Most common attributes across entities

    Examples:
        domain="light", example_limit=3 - summarize light entities

    Note:
        This function aggregates entity data to provide a summary view.
        Useful for understanding the state distribution and common patterns
        within a domain.

    Best Practices:
        - Use to get an overview of entities in a domain
        - Check state_distribution to understand entity states
        - Review common_attributes to see important attributes
        - Use example_limit to control detail level
    """
    entities = await get_entities(domain=domain)

    # Check if we got an error response
    if isinstance(entities, dict) and "error" in entities:
        return entities  # Just pass through the error

    try:
        # Initialize summary data
        total_count = len(entities)
        state_counts = {}
        state_examples = {}
        attributes_summary = {}

        # Process entities to build the summary
        for entity in entities:
            state = entity.get("state", "unknown")

            # Count states
            if state not in state_counts:
                state_counts[state] = 0
                state_examples[state] = []
            state_counts[state] += 1

            # Add examples (up to the limit)
            if len(state_examples[state]) < example_limit:
                example = {
                    "entity_id": entity["entity_id"],
                    "friendly_name": entity.get("attributes", {}).get(
                        "friendly_name", entity["entity_id"]
                    ),
                }
                state_examples[state].append(example)

            # Collect attribute keys for summary
            for attr_key in entity.get("attributes", {}):
                if attr_key not in attributes_summary:
                    attributes_summary[attr_key] = 0
                attributes_summary[attr_key] += 1

        # Create the summary
        summary = {
            "domain": domain,
            "total_count": total_count,
            "state_distribution": state_counts,
            "examples": state_examples,
            "common_attributes": sorted(
                [(k, v) for k, v in attributes_summary.items()], key=lambda x: x[1], reverse=True
            )[:10],  # Top 10 most common attributes
        }

        return summary
    except Exception as e:
        return {"error": f"Error generating domain summary: {str(e)}"}
