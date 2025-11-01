"""Diagnostics MCP tools for hass-mcp.

This module provides MCP tools for advanced debugging and diagnostics.
These tools are thin wrappers around the diagnostics API layer.
"""

import logging
from typing import Any

from app.api.diagnostics import (
    analyze_automation_conflicts,
    check_entity_dependencies,
    diagnose_entity,
    get_integration_errors,
)

logger = logging.getLogger(__name__)


async def diagnose_entity_tool(entity_id: str) -> dict[str, Any]:
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

    Examples:
        entity_id="light.living_room" - diagnose light entity
        entity_id="sensor.temperature" - diagnose sensor entity

    Note:
        This provides comprehensive diagnostics including:
        - Entity availability status
        - Last update time
        - Integration status
        - Recent error history
        - Actionable recommendations

    Best Practices:
        - Use this to diagnose why an entity isn't working
        - Check issues and recommendations for actionable steps
        - Review integration status if entity is unavailable
        - Use to troubleshoot entity connectivity issues
    """
    logger.info(f"Diagnosing entity: {entity_id}")
    return await diagnose_entity(entity_id)


async def check_entity_dependencies_tool(entity_id: str) -> dict[str, Any]:
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

    Examples:
        entity_id="light.living_room" - find dependencies for light entity
        entity_id="sensor.temperature" - find dependencies for sensor entity

    Note:
        This searches through automations, scripts, and scenes to find
        references to the specified entity. Useful for understanding
        the impact of disabling or deleting an entity.

    Best Practices:
        - Use this before deleting or disabling an entity
        - Check dependencies to understand entity impact
        - Review automations and scripts that depend on the entity
        - Use to prevent breaking automations when making changes
    """
    logger.info(f"Checking dependencies for entity: {entity_id}")
    return await check_entity_dependencies(entity_id)


async def analyze_automation_conflicts_tool() -> dict[str, Any]:
    """
    Detect conflicting automations (opposing actions, redundant triggers, etc.).

    Returns:
        Dictionary containing:
        - total_automations: Total number of automations checked
        - conflicts: List of conflicts found
        - warnings: List of warnings

    Examples:
        Returns analysis of all automations for conflicts

    Note:
        This analyzes all automations to find potential conflicts, such as:
        - Opposing actions (turn_on vs turn_off) on the same entity
        - Redundant triggers
        - Race conditions

    Best Practices:
        - Use this to identify potential automation conflicts
        - Review conflicts to ensure automations work as intended
        - Consider automation modes (single, restart, queued, parallel) when reviewing
        - Use to prevent unintended automation behavior
    """
    logger.info("Analyzing automation conflicts")
    return await analyze_automation_conflicts()


async def get_integration_errors_tool(domain: str | None = None) -> dict[str, Any]:
    """
    Get errors specific to integrations.

    Args:
        domain: Optional integration domain to filter errors by

    Returns:
        Dictionary containing:
        - integration_errors: Dictionary mapping integration name to list of errors
        - total_integrations_with_errors: Number of integrations with errors
        - note: Note about error source

    Examples:
        domain=None - get errors for all integrations
        domain="hue" - get errors for hue integration only
        domain="mqtt" - get errors for mqtt integration only

    Note:
        This parses the Home Assistant error log to extract integration-specific errors.
        Errors are extracted from log entries matching [integration_name] patterns.

    Best Practices:
        - Use this to identify integration-specific issues
        - Filter by domain to focus on specific integration
        - Review errors to understand integration problems
        - Use to troubleshoot integration connectivity and configuration issues
    """
    logger.info("Getting integration errors" + (f" for domain: {domain}" if domain else ""))
    return await get_integration_errors(domain)
