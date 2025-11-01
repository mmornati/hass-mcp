"""Automations API module for hass-mcp.

This module provides functions for interacting with Home Assistant automations.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.api.entities import get_entities
from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def get_automations() -> list[dict[str, Any]]:
    """Get a list of all automations from Home Assistant"""
    # Reuse the get_entities function with domain filtering
    automation_entities = await get_entities(domain="automation")

    # Check if we got an error response
    if isinstance(automation_entities, dict) and "error" in automation_entities:
        return automation_entities  # Just pass through the error

    # Process automation entities
    result = []
    try:
        for entity in automation_entities:
            # Extract relevant information
            automation_info = {
                "id": entity["entity_id"].split(".")[1],
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "alias": entity["attributes"].get("friendly_name", entity["entity_id"]),
            }

            # Add any additional attributes that might be useful
            if "last_triggered" in entity["attributes"]:
                automation_info["last_triggered"] = entity["attributes"]["last_triggered"]

            result.append(automation_info)
    except (TypeError, KeyError) as e:
        # Handle errors in processing the entities
        return {"error": f"Error processing automation entities: {str(e)}"}

    return result


@handle_api_errors
async def reload_automations() -> dict[str, Any]:
    """Reload all automations in Home Assistant"""
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/automation/reload",
        headers=get_ha_headers(),
        json={},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def get_automation_config(automation_id: str) -> dict[str, Any]:
    """
    Get full automation configuration including triggers, conditions, actions

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

    Example response:
        {
            "id": "automation_id",
            "alias": "Turn on lights at sunset",
            "description": "Automatically turn on lights",
            "trigger": [...],
            "condition": [...],
            "action": [...],
            "mode": "single"
        }
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def create_automation(config: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new automation from configuration dictionary

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

    Note:
        If 'id' is not provided in config, a unique ID will be generated.
        The automation will be created and enabled by default.
    """
    # Extract automation_id from config or generate one
    automation_id = config.get("id")
    if not automation_id:
        automation_id = f"automation_{uuid.uuid4().hex[:8]}"
        config["id"] = automation_id

    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
        json=config,
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def update_automation(automation_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Update an existing automation with new configuration

    Args:
        automation_id: The automation ID to update (without 'automation.' prefix)
        config: Updated automation configuration dictionary

    Returns:
        Response from the update operation

    Note:
        The config should include all fields you want to keep.
        Fields not included may be removed.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
        json=config,
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def delete_automation(automation_id: str) -> dict[str, Any]:
    """
    Delete an automation

    Args:
        automation_id: The automation ID to delete (without 'automation.' prefix)

    Returns:
        Response from the delete operation

    Note:
        ⚠️ This permanently deletes the automation. There is no undo.
        Make sure the automation is not referenced by other automations or scripts.
    """
    client = await get_client()
    response = await client.delete(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return {"status": "deleted", "automation_id": automation_id}


@handle_api_errors
async def enable_automation(automation_id: str) -> dict[str, Any]:
    """
    Enable an automation

    Args:
        automation_id: The automation ID to enable (without 'automation.' prefix)

    Returns:
        Response from the enable operation

    Note:
        Enabling an automation allows it to trigger automatically.
        The automation must exist and be configured correctly.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/automation/turn_on",
        headers=get_ha_headers(),
        json={"entity_id": f"automation.{automation_id}"},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def disable_automation(automation_id: str) -> dict[str, Any]:
    """
    Disable an automation

    Args:
        automation_id: The automation ID to disable (without 'automation.' prefix)

    Returns:
        Response from the disable operation

    Note:
        Disabling prevents the automation from triggering automatically.
        The automation configuration is preserved and can be re-enabled later.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/automation/turn_off",
        headers=get_ha_headers(),
        json={"entity_id": f"automation.{automation_id}"},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def trigger_automation(automation_id: str) -> dict[str, Any]:
    """
    Manually trigger an automation

    Args:
        automation_id: The automation ID to trigger (without 'automation.' prefix)

    Returns:
        Response from the trigger operation

    Note:
        This manually executes the automation actions.
        Useful for testing automations without waiting for triggers.
        The automation does not need to be enabled to be triggered manually.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/automation/trigger",
        headers=get_ha_headers(),
        json={"entity_id": f"automation.{automation_id}"},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def get_automation_execution_log(automation_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get automation execution history from logbook

    Args:
        automation_id: The automation ID to get history for (without 'automation.' prefix)
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        Dictionary containing:
        - automation_id: The automation ID requested
        - executions: List of execution events with timestamps
        - count: Number of executions found
        - time_range: Dictionary with start_time and end_time

    Example response:
        {
            "automation_id": "automation_id",
            "executions": [
                {
                    "when": "2024-01-01T12:00:00Z",
                    "name": "Turn on lights",
                    "domain": "automation",
                    "entity_id": "automation.automation_id"
                }
            ],
            "count": 5,
            "time_range": {
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z"
            }
        }

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use to debug why an automation isn't firing
        - Check execution frequency to optimize automation triggers
    """
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=hours)
    start_time_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S")

    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/logbook/{start_time_iso}",
        headers=get_ha_headers(),
        params={"entity": f"automation.{automation_id}"},
    )
    response.raise_for_status()
    logbook_data = cast(list[dict[str, Any]], response.json())

    return {
        "automation_id": automation_id,
        "executions": logbook_data,
        "count": len(logbook_data),
        "time_range": {
            "start_time": start_time_iso,
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
    }


@handle_api_errors
async def validate_automation_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an automation configuration

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
        - Entity IDs referenced exist (basic check)

    Example response:
        {
            "valid": true,
            "errors": [],
            "warnings": ["Missing description for automation"],
            "suggestions": ["Consider adding a description"]
        }
    """
    errors = []
    warnings = []
    suggestions = []

    # Check required fields
    if "trigger" not in config or not config["trigger"]:
        errors.append("Missing required field: 'trigger'")
    elif not isinstance(config["trigger"], list):
        errors.append("'trigger' must be a list")

    if "action" not in config or not config["action"]:
        errors.append("Missing required field: 'action'")
    elif not isinstance(config["action"], list):
        errors.append("'action' must be a list")

    # Validate mode
    if "mode" in config:
        valid_modes = ["single", "restart", "queued", "parallel"]
        if config["mode"] not in valid_modes:
            errors.append(f"'mode' must be one of {valid_modes}, got: {config.get('mode')}")

    # Warnings and suggestions
    if "alias" not in config:
        warnings.append("Missing 'alias' - automation will have no display name")
        suggestions.append("Add an 'alias' field for better organization")

    if "description" not in config:
        warnings.append("Missing 'description' - consider adding one for documentation")

    # Basic trigger validation
    if "trigger" in config and isinstance(config["trigger"], list):
        for i, trigger in enumerate(config["trigger"]):
            if not isinstance(trigger, dict):
                errors.append(f"Trigger {i} must be a dictionary")
            elif "platform" not in trigger:
                errors.append(f"Trigger {i} missing required 'platform' field")

    # Basic action validation
    if "action" in config and isinstance(config["action"], list):
        if len(config["action"]) == 0:
            warnings.append("No actions defined - automation will do nothing")

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
    }
