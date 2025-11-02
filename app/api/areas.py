"""Areas API module for hass-mcp.

This module provides functions for interacting with Home Assistant areas.
"""

import ast
import logging
from typing import Any

from app.api.entities import get_entities
from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def get_areas() -> list[dict[str, Any]]:
    """
    Get list of all areas.

    Returns:
        List of area dictionaries containing:
        - area_id: Unique identifier for the area
        - name: Display name of the area
        - aliases: List of aliases for the area
        - picture: Path to area picture (if available)

    Example response:
        [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": [],
                "picture": null
            }
        ]

    Note:
        Home Assistant does not provide a REST endpoint for areas.
        This implementation uses the template API as a workaround.
    """
    client = await get_client()

    # Get area IDs using template API
    response = await client.post(
        f"{HA_URL}/api/template",
        headers=get_ha_headers(),
        json={"template": "{{ areas() }}"},
    )
    response.raise_for_status()

    # Parse the list of area IDs from the response
    area_ids = ast.literal_eval(response.text.strip())

    # Get name for each area
    areas = []
    for area_id in area_ids:
        response_name = await client.post(
            f"{HA_URL}/api/template",
            headers=get_ha_headers(),
            json={"template": f'{{{{ area_name("{area_id}") }}}}'},
        )
        response_name.raise_for_status()
        name = response_name.text.strip().strip('"')

        areas.append(
            {
                "area_id": area_id,
                "name": name,
                "aliases": [],  # Template API doesn't provide aliases
                "picture": None,  # Template API doesn't provide picture
            }
        )

    return areas


@handle_api_errors
async def get_area_entities(area_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific area.

    Args:
        area_id: The area ID to get entities for

    Returns:
        List of entities in the specified area

    Example response:
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {...}
            }
        ]

    Note:
        Entities are filtered by their area_id attribute.
        Returns empty list if area has no entities or area doesn't exist.
    """
    # Get all entities and filter by area_id
    all_entities = await get_entities(lean=True)

    # Check if we got an error response
    if isinstance(all_entities, dict) and "error" in all_entities:
        return [all_entities]  # Return list with error dict for consistency

    area_entities = []
    for entity in all_entities:
        entity_area_id = entity.get("attributes", {}).get("area_id")
        if entity_area_id == area_id:
            area_entities.append(entity)

    return area_entities


@handle_api_errors
async def create_area(
    name: str,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Create a new area.

    Args:
        name: Display name for the area (required)
        aliases: Optional list of aliases for the area
        picture: Optional path to area picture

    Returns:
        Created area dictionary with area_id and configuration

    Example response:
        {
            "area_id": "living_room",
            "name": "Living Room",
            "aliases": ["lounge", "salon"],
            "picture": null
        }

    Examples:
        # Create area with just name
        area = await create_area("Living Room")

        # Create area with aliases
        area = await create_area("Living Room", aliases=["lounge", "salon"])

        # Create area with picture
        area = await create_area("Living Room", picture="/config/www/living_room.jpg")

    Note:
        ⚠️ This operation is not supported via REST API.
        Home Assistant only provides area management through the WebSocket API or UI.
        Please use the Home Assistant frontend or WebSocket API to create areas.
    """
    return {
        "error": "Area creation is not supported via REST API. Please use the Home Assistant frontend or WebSocket API."
    }


@handle_api_errors
async def update_area(
    area_id: str,
    name: str | None = None,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing area.

    Args:
        area_id: The area ID to update
        name: Optional new name for the area
        aliases: Optional new list of aliases (replaces existing)
        picture: Optional new picture path

    Returns:
        Updated area dictionary

    Example response:
        {
            "area_id": "living_room",
            "name": "Family Room",
            "aliases": ["lounge"],
            "picture": null
        }

    Examples:
        # Update area name
        area = await update_area("living_room", name="Family Room")

        # Update aliases
        area = await update_area("living_room", aliases=["lounge", "salon"])

        # Update multiple fields
        area = await update_area("living_room", name="Family Room", aliases=["lounge"])

    Note:
        ⚠️ This operation is not supported via REST API.
        Home Assistant only provides area management through the WebSocket API or UI.
        Please use the Home Assistant frontend or WebSocket API to update areas.
    """
    if not name and not aliases and not picture:
        return {"error": "At least one field (name, aliases, picture) must be provided"}

    return {
        "error": "Area update is not supported via REST API. Please use the Home Assistant frontend or WebSocket API."
    }


@handle_api_errors
async def delete_area(area_id: str) -> dict[str, Any]:
    """
    Delete an area.

    Args:
        area_id: The area ID to delete

    Returns:
        Response from the delete operation

    Example response:
        {
            "status": "deleted",
            "area_id": "living_room"
        }

    Note:
        ⚠️ This operation is not supported via REST API.
        Home Assistant only provides area management through the WebSocket API or UI.
        Please use the Home Assistant frontend or WebSocket API to delete areas.
    """
    return {
        "error": "Area deletion is not supported via REST API. Please use the Home Assistant frontend or WebSocket API."
    }


@handle_api_errors
async def get_area_summary() -> dict[str, Any]:
    """
    Get summary of all areas with device/entity distribution.

    Returns:
        Dictionary containing:
        - total_areas: Total number of areas
        - areas: Dictionary mapping area_id to area summary with:
            - name: Area name
            - entity_count: Number of entities in the area
            - domain_counts: Dictionary of domain counts (e.g., {"light": 3, "switch": 2})

    Example response:
        {
            "total_areas": 5,
            "areas": {
                "living_room": {
                    "name": "Living Room",
                    "entity_count": 10,
                    "domain_counts": {"light": 3, "switch": 2, "sensor": 5}
                }
            }
        }

    Best Practices:
        - Use this to understand entity distribution across areas
        - Identify areas with no entities
        - Analyze domain distribution by area
    """
    areas = await get_areas()
    all_entities = await get_entities(lean=True)

    # Check if we got error responses
    if isinstance(areas, dict) and "error" in areas:
        return areas
    if isinstance(all_entities, dict) and "error" in all_entities:
        return all_entities

    summary: dict[str, Any] = {
        "total_areas": len(areas),
        "areas": {},
    }

    for area in areas:
        area_id = area.get("area_id")
        area_entities = [
            e for e in all_entities if e.get("attributes", {}).get("area_id") == area_id
        ]

        # Group entities by domain
        domain_counts: dict[str, int] = {}
        for entity in area_entities:
            entity_id = entity.get("entity_id", "")
            if "." in entity_id:
                domain = entity_id.split(".")[0]
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        summary["areas"][area_id] = {
            "name": area.get("name"),
            "entity_count": len(area_entities),
            "domain_counts": domain_counts,
        }

    return summary
