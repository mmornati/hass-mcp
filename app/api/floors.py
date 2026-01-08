"""Floors API module for hass-mcp.

This module provides functions for interacting with Home Assistant floors.
Floors are used to organize areas into vertical levels of a building.
"""

import ast
import logging
from typing import Any

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_VERY_LONG
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
@cached(ttl=TTL_VERY_LONG, key_prefix="floors")
async def get_floors() -> list[dict[str, Any]]:
    """
    Get list of all floors.

    Returns:
        List of floor dictionaries containing:
        - floor_id: Unique identifier for the floor
        - name: Display name of the floor
        - level: Optional numeric level (e.g., 0 for ground, 1 for first floor)
        - icon: Optional icon for the floor
        - aliases: Optional list of aliases

    Example response:
        [
            {
                "floor_id": "ground_floor",
                "name": "Ground Floor",
                "level": 0,
                "icon": "mdi:home-floor-0",
                "aliases": ["first floor", "main level"]
            },
            {
                "floor_id": "upstairs",
                "name": "Upstairs",
                "level": 1,
                "icon": "mdi:home-floor-1",
                "aliases": ["second floor"]
            }
        ]

    Note:
        Home Assistant does not provide a REST endpoint for floors.
        This implementation uses the template API as a workaround.
        Floors are used to group areas by vertical level.
    """
    client = await get_client()

    # Use template API to access floors (similar to areas workaround)
    template = """
    {% set result = [] %}
    {% for floor in floors() %}{
        "floor_id": "{{ floor.floor_id }}",
        "name": "{{ floor.name }}",
        "level": {{ floor.level | default(0) }},
        "icon": "{{ floor.icon or '' }}",
        "aliases": {{ floor.aliases | list | to_json }}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
    """

    response = await client.post(
        f"{HA_URL}/api/template",
        headers=get_ha_headers(),
        json={"template": f"[{template}]"},
    )
    response.raise_for_status()

    # Parse the template response
    result_text = response.text.strip()
    if result_text:
        try:
            # Use ast.literal_eval for safer parsing
            floors = ast.literal_eval(result_text)
            return floors
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse floors template response: {e}")
            return []
    return []


@handle_api_errors
@cached(ttl=TTL_VERY_LONG, key_prefix="floors")
async def get_floor(floor_id: str) -> dict[str, Any] | None:
    """
    Get a specific floor by ID.

    Args:
        floor_id: The floor ID to retrieve

    Returns:
        Floor dictionary or None if not found

    Example response:
        {
            "floor_id": "ground_floor",
            "name": "Ground Floor",
            "level": 0,
            "icon": "mdi:home-floor-0",
            "aliases": ["first floor", "main level"]
        }
    """
    floors = await get_floors()
    for floor in floors:
        if floor.get("floor_id") == floor_id:
            return floor
    return None


@handle_api_errors
async def get_areas_on_floor(floor_id: str) -> list[dict[str, Any]]:
    """
    Get all areas on a specific floor.

    Args:
        floor_id: The floor ID to get areas for

    Returns:
        List of area dictionaries on the specified floor

    Example response:
        [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "floor_id": "ground_floor"
            }
        ]

    Note:
        This uses the template API to filter areas by floor.
    """
    client = await get_client()

    template = f"""
    {{% for area in areas() %}}
      {{% if area.floor_id == '{floor_id}' %}}{{
          "area_id": "{{{{ area.area_id }}}}",
          "name": "{{{{ area.name }}}}",
          "floor_id": "{{{{ area.floor_id or '' }}}}"
      }}{{% if not loop.last %}},{{% endif %}}
      {{% endif %}}
    {{% endfor %}}
    """

    response = await client.post(
        f"{HA_URL}/api/template",
        headers=get_ha_headers(),
        json={"template": f"[{template}]"},
    )
    response.raise_for_status()

    result_text = response.text.strip()
    if result_text:
        try:
            areas = ast.literal_eval(result_text)
            # Filter out empty entries
            return [a for a in areas if a]
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse floor areas template response: {e}")
            return []
    return []
