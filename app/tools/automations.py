"""Automation MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant automations.
These tools are thin wrappers around the automations API layer.
"""

import logging
from typing import Any

from app.api.automations import (
    create_automation,
    delete_automation,
    disable_automation,
    enable_automation,
    get_automation_config,
    get_automation_execution_log,
    get_automations,
    trigger_automation,
    update_automation,
    validate_automation_config,
)

logger = logging.getLogger(__name__)


async def list_automations() -> list[dict[str, Any]]:
    """
    Get a list of all automations from Home Assistant.

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


async def get_automation_config_tool(automation_id: str) -> dict[str, Any]:
    """
    Get full automation configuration including triggers, conditions, actions.

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


async def create_automation_tool(config: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new automation from configuration dictionary.

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
    return await create_automation(config)


async def update_automation_tool(automation_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Update an existing automation with new configuration.

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


async def delete_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Delete an automation.

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


async def enable_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Enable an automation.

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


async def disable_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Disable an automation.

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


async def trigger_automation_tool(automation_id: str) -> dict[str, Any]:
    """
    Manually trigger an automation.

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


async def get_automation_execution_log_tool(automation_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get automation execution history from logbook.

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


async def validate_automation_config_tool(config: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an automation configuration.

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
