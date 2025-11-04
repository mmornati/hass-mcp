"""Scenes API module for hass-mcp.

This module provides functions for interacting with Home Assistant scenes.
"""

import json
import logging
from typing import Any, cast

from app.api.entities import get_entities, get_entity_state
from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.ttl import TTL_LONG
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
@cached(ttl=TTL_LONG, key_prefix="scenes")
async def get_scenes() -> list[dict[str, Any]]:
    """
    Get list of all scenes.

    Returns:
        List of scene dictionaries containing:
        - entity_id: The scene entity ID (e.g., 'scene.living_room_dim')
        - state: Current state of the scene
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene

    Example response:
        [
            {
                "entity_id": "scene.living_room_dim",
                "state": "scening",
                "friendly_name": "Living Room Dim",
                "entity_id_list": ["light.living_room", "light.kitchen"]
            }
        ]

    Note:
        Scenes capture the state of multiple entities at a point in time.
        Useful for creating lighting presets and room configurations.
    """
    scene_entities = await get_entities(domain="scene")

    # Check if we got an error response
    if isinstance(scene_entities, dict) and "error" in scene_entities:
        return [scene_entities]  # Return list with error dict for consistency

    scenes = []
    for entity in scene_entities:
        scene_info = {
            "entity_id": entity.get("entity_id"),
            "state": entity.get("state"),
        }

        # Add attributes if available
        attributes = entity.get("attributes", {})
        if "friendly_name" in attributes:
            scene_info["friendly_name"] = attributes["friendly_name"]
        if "entity_id" in attributes:
            scene_info["entity_id_list"] = attributes["entity_id"]
        if "snapshot" in attributes:
            scene_info["snapshot"] = attributes["snapshot"]

        scenes.append(scene_info)

    return scenes


@handle_api_errors
@cached(ttl=TTL_LONG, key_prefix="scenes")
async def get_scene_config(scene_id: str) -> dict[str, Any]:
    """
    Get scene configuration (what entities/values it saves).

    Args:
        scene_id: The scene ID to get (with or without 'scene.' prefix)

    Returns:
        Scene configuration dictionary with:
        - entity_id: The scene entity ID
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene
        - snapshot: Snapshot of entity states when scene was created

    Example response:
        {
            "entity_id": "scene.living_room_dim",
            "friendly_name": "Living Room Dim",
            "entity_id_list": ["light.living_room", "light.kitchen"],
            "snapshot": [...]
        }

    Note:
        Scene configuration shows what entities are included in the scene
        and what states they were in when the scene was created.
    """
    entity_id = f"scene.{scene_id}" if not scene_id.startswith("scene.") else scene_id

    entity = await get_entity_state(entity_id, lean=False)

    # Check if we got an error response
    if isinstance(entity, dict) and "error" in entity:
        return entity

    # Extract scene data
    attributes = entity.get("attributes", {})
    scene_config = {
        "entity_id": entity.get("entity_id"),
        "friendly_name": attributes.get("friendly_name"),
        "entity_id_list": attributes.get("entity_id", []),
        "snapshot": attributes.get("snapshot", []),
    }

    return scene_config


@handle_api_errors
@invalidate_cache(pattern="scenes:*")
async def create_scene(
    name: str,
    entity_ids: list[str],
    states: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new scene.

    Args:
        name: Display name for the scene
        entity_ids: List of entity IDs to include in the scene
        states: Optional dictionary of entity states to capture (if None, captures current states)

    Returns:
        Response from the create operation, or error message if creation fails

    Example response:
        {
            "entity_id": "scene.living_room_dim",
            "name": "Living Room Dim"
        }

    Examples:
        # Create scene capturing current states
        scene = await create_scene("Living Room Dim", ["light.living_room", "light.kitchen"])

        # Create scene with specific states
        scene = await create_scene(
            "Living Room Dim",
            ["light.living_room", "light.kitchen"],
            {"light.living_room": {"state": "on", "brightness": 128}}
        )

    Note:
        ⚠️ Scene creation via API may not be available in all Home Assistant versions.
        The create service is deprecated. If it fails, a helpful YAML configuration example
        is returned to guide manual scene creation.
    """
    client = await get_client()

    data: dict[str, Any] = {
        "name": name,
        "entities": entity_ids,
    }

    if states:
        data["states"] = states

    try:
        response = await client.post(
            f"{HA_URL}/api/services/scene/create",
            headers=get_ha_headers(),
            json=data,
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
    except Exception as e:
        # If create service doesn't work, provide helpful message
        example_config = f"\nscene:\n  - name: {name}\n    entities:"

        for eid in entity_ids:
            if states and eid in states:
                example_config += f"\n      {eid}: {json.dumps(states[eid])}"
            else:
                example_config += f"\n      {eid}:"
        return {
            "error": "Scene creation via API is not available",
            "note": "Scenes should be created in configuration.yaml or via UI",
            "example_config": example_config,
            "exception": str(e),
        }


@handle_api_errors
async def activate_scene(scene_id: str) -> dict[str, Any]:
    """
    Activate/restore a scene.

    Args:
        scene_id: The scene ID to activate (with or without 'scene.' prefix)

    Returns:
        Response from the activate operation

    Example response:
        []

    Examples:
        # Activate scene
        result = await activate_scene("living_room_dim")
        result = await activate_scene("scene.living_room_dim")

    Note:
        Activating a scene restores all entities to their saved states.
        The scene entity_id can be provided with or without the 'scene.' prefix.
    """
    entity_id = f"scene.{scene_id}" if not scene_id.startswith("scene.") else scene_id

    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/scene/turn_on",
        headers=get_ha_headers(),
        json={"entity_id": entity_id},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def reload_scenes() -> dict[str, Any]:
    """
    Reload scenes from configuration.

    Returns:
        Response from the reload operation

    Example response:
        []

    Note:
        Reloading scenes reloads all scene configurations from YAML files.
        This is useful after modifying scene configuration files.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/scene/reload",
        headers=get_ha_headers(),
        json={},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
