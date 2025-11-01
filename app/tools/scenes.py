"""Scene MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant scenes.
These tools are thin wrappers around the scenes API layer.
"""

import logging
from typing import Any

from app.api.scenes import (
    activate_scene,
    create_scene,
    get_scene_config,
    get_scenes,
    reload_scenes,
)

logger = logging.getLogger(__name__)


async def list_scenes_tool() -> list[dict[str, Any]]:
    """
    Get a list of all scenes in Home Assistant.

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


async def get_scene_tool(scene_id: str) -> dict[str, Any]:
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


async def create_scene_tool(
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


async def activate_scene_tool(scene_id: str) -> dict[str, Any]:
    """
    Activate/restore a scene.

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


async def reload_scenes_tool() -> dict[str, Any]:
    """
    Reload scenes from configuration.

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
