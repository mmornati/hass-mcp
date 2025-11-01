"""Script MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant scripts.
These tools are thin wrappers around the scripts API layer.
"""

import logging
from typing import Any

from app.api.scripts import get_script_config, get_scripts, reload_scripts, run_script

logger = logging.getLogger(__name__)


async def list_scripts_tool() -> list[dict[str, Any]]:
    """
    Get a list of all scripts in Home Assistant.

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


async def get_script_tool(script_id: str) -> dict[str, Any]:
    """
    Get script configuration and details.

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


async def run_script_tool(
    script_id: str, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Execute a script with optional variables.

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


async def reload_scripts_tool() -> dict[str, Any]:
    """
    Reload all scripts from configuration.

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
