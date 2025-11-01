"""Diagnostics API module for hass-mcp.

This module provides functions for advanced debugging and diagnostics.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Any

from app.api.automations import (
    get_automation_config,
    get_automations,
)
from app.api.entities import (
    get_entity_history,
    get_entity_state,
)
from app.api.integrations import get_integrations
from app.api.scenes import get_scenes
from app.api.scripts import (
    get_script_config,
    get_scripts,
)
from app.api.system import get_hass_error_log
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def diagnose_entity(entity_id: str) -> dict[str, Any]:
    """
    Comprehensive entity diagnostics.

    Args:
        entity_id: The entity ID to diagnose

    Returns:
        Dictionary containing:
        - entity_id: The entity ID being diagnosed
        - status: Dictionary with status information (state, domain, last_updated_age_seconds)
        - issues: List of issues found
        - recommendations: List of recommendations to fix issues

    Example response:
        {
            "entity_id": "light.living_room",
            "status": {
                "entity_state": "unavailable",
                "domain": "light",
                "last_updated_age_seconds": 7200
            },
            "issues": [
                "Entity is unavailable",
                "Entity hasn't updated in 2.0 hours"
            ],
            "recommendations": [
                "Check device connectivity and integration status"
            ]
        }

    Best Practices:
        - Use this to diagnose why an entity isn't working
        - Check issues and recommendations for actionable steps
        - Review integration status if entity is unavailable
    """
    diagnosis: dict[str, Any] = {
        "entity_id": entity_id,
        "status": {},
        "issues": [],
        "recommendations": [],
    }

    # Get entity state
    entity = await get_entity_state(entity_id, lean=False)

    # Check for errors
    if isinstance(entity, dict) and "error" in entity:
        diagnosis["issues"].append(f"Entity not found: {entity.get('error')}")
        diagnosis["recommendations"].append("Verify entity_id is correct")
        return diagnosis

    # Check availability
    state = entity.get("state")
    if state == "unavailable":
        diagnosis["issues"].append("Entity is unavailable")
        diagnosis["recommendations"].append("Check device connectivity and integration status")

    # Check last update time
    last_updated = entity.get("last_updated")
    if last_updated:
        last_update_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        age = (now - last_update_dt).total_seconds()

        diagnosis["status"]["last_updated_age_seconds"] = age
        if age > 3600:  # 1 hour
            diagnosis["issues"].append(f"Entity hasn't updated in {age / 3600:.1f} hours")
            diagnosis["recommendations"].append("Check if device is powered on and connected")

    # Check for errors in related integrations
    domain = entity_id.split(".")[0]
    integrations = await get_integrations(domain=domain)

    # Check for errors in integrations list response
    if isinstance(integrations, dict) and "error" in integrations:
        diagnosis["issues"].append(f"Error getting integrations: {integrations.get('error')}")
    elif isinstance(integrations, list):
        for integration in integrations:
            integration_state = integration.get("state")
            if integration_state and integration_state != "loaded":
                diagnosis["issues"].append(f"Integration {domain} is in state: {integration_state}")
                diagnosis["recommendations"].append(
                    f"Check integration {domain} configuration and reload if needed"
                )

    # Get recent history to check for errors
    try:
        history = await get_entity_history(entity_id, hours=24)
        if isinstance(history, list):
            # Flatten history list (history is a list of lists)
            states = []
            for state_list in history:
                if isinstance(state_list, list):
                    states.extend(state_list)
                else:
                    states.append(state_list)

            # Check for error states in recent history
            error_states = [
                s
                for s in states
                if isinstance(s, dict) and s.get("state", "").lower() in ["error", "unavailable"]
            ]
            if error_states:
                diagnosis["issues"].append(
                    f"Found {len(error_states)} error/unavailable states in recent history"
                )
    except Exception:  # nosec B110
        pass

    diagnosis["status"]["entity_state"] = state
    diagnosis["status"]["domain"] = domain

    return diagnosis


@handle_api_errors
async def check_entity_dependencies(entity_id: str) -> dict[str, Any]:
    """
    Find what depends on this entity (automations, scripts, etc.).

    Args:
        entity_id: The entity ID to check dependencies for

    Returns:
        Dictionary containing:
        - entity_id: The entity ID being checked
        - automations: List of automations that use this entity
        - scripts: List of scripts that use this entity
        - scenes: List of scenes that use this entity

    Example response:
        {
            "entity_id": "light.living_room",
            "automations": [
                {"entity_id": "automation.turn_on_lights", "alias": "Turn on lights"}
            ],
            "scripts": [
                {"entity_id": "script.lights_on", "friendly_name": "Lights On"}
            ],
            "scenes": [
                {"entity_id": "scene.living_room_dim", "friendly_name": "Living Room Dim"}
            ]
        }

    Best Practices:
        - Use this before deleting or disabling an entity
        - Check dependencies to understand entity impact
        - Review automations and scripts that depend on the entity
    """
    dependencies: dict[str, Any] = {
        "entity_id": entity_id,
        "automations": [],
        "scripts": [],
        "scenes": [],
    }

    # Get all automations
    automations = await get_automations()

    # Check for errors in automations response
    if isinstance(automations, dict) and "error" in automations:
        return dependencies

    for automation in automations:
        automation_id = automation.get("entity_id")
        if not automation_id:
            continue
        try:
            automation_id_clean = (
                automation_id.replace("automation.", "")
                if "automation." in automation_id
                else automation_id
            )
            config = await get_automation_config(automation_id_clean)
            # Check for errors in config
            if isinstance(config, dict) and "error" in config:
                continue
            # Search config for entity_id
            config_str = str(config)
            if entity_id in config_str:
                dependencies["automations"].append(
                    {
                        "entity_id": automation_id,
                        "alias": automation.get("alias", automation_id),
                    }
                )
        except Exception:  # nosec B110
            pass

    # Get all scripts
    scripts = await get_scripts()

    # Check for errors in scripts response
    if isinstance(scripts, dict) and "error" in scripts:
        return dependencies

    for script in scripts:
        script_id = script.get("entity_id")
        if not script_id:
            continue
        try:
            script_id_clean = (
                script_id.replace("script.", "") if "script." in script_id else script_id
            )
            config = await get_script_config(script_id_clean)
            # Check for errors in config
            if isinstance(config, dict) and "error" in config:
                continue
            config_str = str(config)
            if entity_id in config_str:
                dependencies["scripts"].append(
                    {
                        "entity_id": script_id,
                        "friendly_name": script.get("friendly_name", script_id),
                    }
                )
        except Exception:  # nosec B110
            pass

    # Check scenes
    scenes = await get_scenes()

    # Check for errors in scenes response
    if isinstance(scenes, dict) and "error" in scenes:
        return dependencies

    for scene in scenes:
        entity_ids = scene.get("entity_id_list", [])
        if entity_id in entity_ids:
            dependencies["scenes"].append(
                {
                    "entity_id": scene.get("entity_id"),
                    "friendly_name": scene.get("friendly_name", scene.get("entity_id")),
                }
            )

    return dependencies


@handle_api_errors
async def analyze_automation_conflicts() -> dict[str, Any]:
    """
    Detect conflicting automations (opposing actions, redundant triggers, etc.).

    Returns:
        Dictionary containing:
        - total_automations: Total number of automations checked
        - conflicts: List of conflicts found
        - warnings: List of warnings

    Example response:
        {
            "total_automations": 10,
            "conflicts": [
                {
                    "entity_id": "light.living_room",
                    "type": "opposing_actions",
                    "automations": ["automation.turn_on", "automation.turn_off"],
                    "description": "Multiple automations control light.living_room with opposing actions"
                }
            ],
            "warnings": []
        }

    Best Practices:
        - Use this to identify potential automation conflicts
        - Review conflicts to ensure automations work as intended
        - Consider automation modes (single, restart, queued, parallel) when reviewing
    """
    automations = await get_automations()

    # Check for errors in automations response
    if isinstance(automations, dict) and "error" in automations:
        return {
            "total_automations": 0,
            "conflicts": [],
            "warnings": [],
            "error": automations.get("error"),
        }

    conflicts: dict[str, Any] = {
        "total_automations": len(automations),
        "conflicts": [],
        "warnings": [],
    }

    automation_configs = {}
    for automation in automations:
        automation_id = automation.get("entity_id")
        if not automation_id:
            continue
        try:
            automation_id_clean = (
                automation_id.replace("automation.", "")
                if "automation." in automation_id
                else automation_id
            )
            config = await get_automation_config(automation_id_clean)
            # Check for errors in config
            if isinstance(config, dict) and "error" in config:
                continue
            automation_configs[automation_id] = config
        except Exception:  # nosec B112
            continue

    # Check for opposing actions on same entities
    entity_actions: dict[str, list[dict[str, Any]]] = {}
    for automation_id, config in automation_configs.items():
        actions = config.get("action", [])
        for action in actions:
            if not isinstance(action, dict):
                continue
            service = action.get("service", "")
            action_entity_id = action.get("entity_id")

            if not action_entity_id:
                continue

            if isinstance(action_entity_id, list):
                entity_ids = action_entity_id
            else:
                entity_ids = [action_entity_id]

            for eid in entity_ids:
                if eid not in entity_actions:
                    entity_actions[eid] = []
                entity_actions[eid].append(
                    {
                        "automation": automation_id,
                        "service": service,
                    }
                )

    # Check for conflicts (turn_on vs turn_off, etc.)
    for eid, actions in entity_actions.items():
        services = [a["service"] for a in actions]
        # Check for opposing actions (handle both "turn_on" and "domain.turn_on" formats)
        has_turn_on = any("turn_on" in service for service in services)
        has_turn_off = any("turn_off" in service for service in services)
        if has_turn_on and has_turn_off:
            conflicting_automations = [
                a["automation"]
                for a in actions
                if "turn_on" in a["service"] or "turn_off" in a["service"]
            ]
            conflicts["conflicts"].append(
                {
                    "entity_id": eid,
                    "type": "opposing_actions",
                    "automations": conflicting_automations,
                    "description": f"Multiple automations control {eid} with opposing actions",
                }
            )

    return conflicts


@handle_api_errors
async def get_integration_errors(domain: str | None = None) -> dict[str, Any]:
    """
    Get errors specific to integrations.

    Args:
        domain: Optional integration domain to filter errors by

    Returns:
        Dictionary containing:
        - integration_errors: Dictionary mapping integration name to list of errors
        - total_integrations_with_errors: Number of integrations with errors
        - note: Note about error source

    Example response:
        {
            "integration_errors": {
                "hue": [
                    "2024-01-01 12:00:00 ERROR (MainThread) [homeassistant.components.hue] Connection failed"
                ],
                "mqtt": [
                    "2024-01-01 12:00:01 ERROR (MainThread) [homeassistant.components.mqtt] Failed to connect"
                ]
            },
            "total_integrations_with_errors": 2,
            "note": "These are errors found in the error log"
        }

    Best Practices:
        - Use this to identify integration-specific issues
        - Filter by domain to focus on specific integration
        - Review errors to understand integration problems
    """
    # Get error log
    error_log = await get_hass_error_log()

    # Check for errors in error log response
    if isinstance(error_log, dict) and "error" in error_log:
        return {
            "integration_errors": {},
            "total_integrations_with_errors": 0,
            "error": error_log.get("error"),
            "note": "Could not retrieve error log",
        }

    integration_errors: dict[str, list[str]] = {}
    log_text = error_log.get("log_text", "")

    # Parse log for integration-specific errors
    lines = log_text.split("\n")

    for line in lines:
        if "ERROR" in line.upper() or "Exception" in line:
            # Extract integration name from [homeassistant.components.integration] pattern
            # Try to match components.integration first, then fall back to any [name] pattern
            integration_match = re.search(r"\[homeassistant\.components\.([a-zA-Z0-9_]+)\]", line)
            if not integration_match:
                # Fall back to matching any [integration] pattern
                integration_match = re.search(r"\[([a-zA-Z0-9_]+)\]", line)
            if integration_match:
                integration = integration_match.group(1)

                if domain and integration != domain:
                    continue

                if integration not in integration_errors:
                    integration_errors[integration] = []

                integration_errors[integration].append(line.strip())

    return {
        "integration_errors": integration_errors,
        "total_integrations_with_errors": len(integration_errors),
        "note": "These are errors found in the error log",
    }
