"""Scripts API module for hass-mcp.

This module provides functions for interacting with Home Assistant scripts.
"""

import logging
from typing import Any, cast

from app.api.entities import get_entities, get_entity_state
from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def get_scripts() -> list[dict[str, Any]]:
    """
    Get list of all scripts from Home Assistant.

    Returns:
        List of script dictionaries containing:
        - entity_id: The script entity ID (e.g., 'script.turn_on_lights')
        - state: Current state of the script
        - friendly_name: Display name of the script
        - last_triggered: Timestamp of last execution (if available)
        - alias: Script alias/name

    Example response:
        [
            {
                "entity_id": "script.turn_on_lights",
                "state": "idle",
                "friendly_name": "Turn on lights",
                "alias": "Turn on lights",
                "last_triggered": "2025-01-01T12:00:00Z"
            }
        ]
    """
    # Scripts can be retrieved via states API
    script_entities = await get_entities(domain="script")

    # Check if we got an error response
    if isinstance(script_entities, dict) and "error" in script_entities:
        return cast(list[dict[str, Any]], script_entities)  # Just pass through the error

    # Extract script information
    scripts = []
    try:
        for entity in script_entities:
            script_info = {
                "entity_id": entity.get("entity_id"),
                "state": entity.get("state"),
            }

            # Add attributes if available
            attributes = entity.get("attributes", {})
            if "friendly_name" in attributes:
                script_info["friendly_name"] = attributes["friendly_name"]
            if "alias" in attributes:
                script_info["alias"] = attributes["alias"]
            if "last_triggered" in attributes:
                script_info["last_triggered"] = attributes["last_triggered"]

            scripts.append(script_info)
    except (TypeError, KeyError) as e:
        # Handle errors in processing the entities
        return {"error": f"Error processing script entities: {str(e)}"}

    return scripts


@handle_api_errors
async def get_script_config(script_id: str) -> dict[str, Any]:
    """
    Get script configuration (sequence of actions).

    Args:
        script_id: The script ID to get (without 'script.' prefix)

    Returns:
        Script configuration dictionary with:
        - entity_id: The script entity ID
        - state: Current state
        - attributes: Script attributes including configuration
        - config: Script configuration if available via config API

    Example response:
        {
            "entity_id": "script.turn_on_lights",
            "state": "idle",
            "attributes": {...},
            "sequence": [
                {"service": "light.turn_on", "entity_id": "light.living_room"}
            ]
        }

    Note:
        Script configuration might be available via config API or
        only through entity state depending on Home Assistant version.
        This function tries the config API first, then falls back to entity state.
    """
    entity_id = f"script.{script_id}"

    # Try to get config via config API if available
    try:
        client = await get_client()
        response = await client.get(
            f"{HA_URL}/api/config/scripts/{script_id}",
            headers=get_ha_headers(),
        )
        if response.status_code == 200:
            config_data = response.json()
            # Merge with entity state for complete information
            entity = await get_entity_state(entity_id, lean=False)
            config_data["entity"] = entity
            return cast(dict[str, Any], config_data)
    except Exception:  # nosec B110
        # Config API not available, fall through to entity state
        pass

    # Fallback to entity state
    return await get_entity_state(entity_id, lean=False)


@handle_api_errors
async def run_script(script_id: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Execute a script with optional variables.

    Args:
        script_id: The script ID to execute (without 'script.' prefix)
        variables: Optional dictionary of variables to pass to the script

    Returns:
        Response from the script execution (usually empty for successful calls)

    Examples:
        # Run script without variables
        result = await run_script("turn_on_lights")

        # Run script with variables
        result = await run_script("notify", {"message": "Hello", "target": "user1"})

    Note:
        Scripts execute asynchronously. The response indicates the script was started,
        not necessarily that it completed.
    """
    data: dict[str, Any] = {}
    if variables:
        data["variables"] = variables

    # Call script service directly via httpx
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/script/{script_id}",
        headers=get_ha_headers(),
        json=data,
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def reload_scripts() -> dict[str, Any]:
    """
    Reload all scripts from configuration.

    Returns:
        Response from the reload operation (usually empty for successful calls)

    Note:
        Reloading scripts reloads all script configurations from YAML files.
        This is useful after modifying script configuration files.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/script/reload",
        headers=get_ha_headers(),
        json={},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
