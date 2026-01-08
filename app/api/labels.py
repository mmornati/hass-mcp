"""Labels API module for hass-mcp.

This module provides functions for interacting with Home Assistant labels.
Labels are organizational tags that can be applied to entities, devices, and areas.
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
@cached(ttl=TTL_VERY_LONG, key_prefix="labels")
async def get_labels() -> list[dict[str, Any]]:
    """
    Get list of all labels.

    Returns:
        List of label dictionaries containing:
        - label_id: Unique identifier for the label
        - name: Display name of the label
        - icon: Optional icon for the label
        - color: Optional color for the label
        - description: Optional description of the label

    Example response:
        [
            {
                "label_id": "smart_lights",
                "name": "Smart Lights",
                "icon": "mdi:lightbulb",
                "color": "blue",
                "description": "All smart lighting devices"
            }
        ]

    Note:
        Home Assistant does not provide a REST endpoint for labels.
        This implementation uses the template API as a workaround.
        Labels are used to organize and group entities, devices, and areas.
    """
    client = await get_client()

    # Use template API to access labels (similar to areas workaround)
    template = """
    {% set labels = [] %}
    {% for label in labels_all %}{
        "label_id": "{{ label.label_id }}",
        "name": "{{ label.name }}",
        "icon": "{{ label.icon or '' }}",
        "color": "{{ label.color or '' }}",
        "description": "{{ label.description or '' }}"
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
            labels = ast.literal_eval(result_text)
            return labels
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse labels template response: {e}")
            return []
    return []


@handle_api_errors
@cached(ttl=TTL_VERY_LONG, key_prefix="labels")
async def get_label(label_id: str) -> dict[str, Any] | None:
    """
    Get a specific label by ID.

    Args:
        label_id: The label ID to retrieve

    Returns:
        Label dictionary or None if not found

    Example response:
        {
            "label_id": "smart_lights",
            "name": "Smart Lights",
            "icon": "mdi:lightbulb",
            "color": "blue",
            "description": "All smart lighting devices"
        }
    """
    labels = await get_labels()
    for label in labels:
        if label.get("label_id") == label_id:
            return label
    return None


@handle_api_errors
async def get_entities_with_label(label_id: str) -> list[dict[str, Any]]:
    """
    Get all entities with a specific label.

    Args:
        label_id: The label ID to filter entities by

    Returns:
        List of entity dictionaries that have the specified label

    Example response:
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "labels": ["smart_lights", "living_room"]
            }
        ]

    Note:
        This uses the template API to filter entities by label.
        Not all entities may have labels assigned.
    """
    client = await get_client()

    template = f"""
    {{% set entities = [] %}}
    {{% for state in states %}}
      {{% if '{label_id}' in labels_for(state.entity_id) %}}{{
          "entity_id": "{{{{ state.entity_id }}}}",
          "state": "{{{{ state.state }}}}",
          "friendly_name": "{{{{ state.attributes.friendly_name or state.entity_id }}}}"
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
            entities = ast.literal_eval(result_text)
            # Filter out empty entries
            return [e for e in entities if e]
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse labeled entities template response: {e}")
            return []
    return []
