"""System MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant system information.
These tools are thin wrappers around the system API layer.
"""

import logging
from typing import Any

from app.api.entities import get_entity_history, summarize_domain
from app.api.system import (
    get_core_config,
    get_hass_error_log,
    get_hass_version,
    get_system_health,
    get_system_overview,
    restart_home_assistant,
)

logger = logging.getLogger(__name__)


async def get_version() -> str:
    """
    Get the Home Assistant version.

    Returns:
        A string with the Home Assistant version (e.g., "2025.3.0")
    """
    logger.info("Getting Home Assistant version")
    return await get_hass_version()


async def system_overview() -> dict[str, Any]:
    """
    Get a comprehensive overview of the entire Home Assistant system.

    Returns:
        A dictionary containing:
        - total_entities: Total count of all entities
        - domains: Dictionary of domains with their entity counts and state distributions
        - domain_samples: Representative sample entities for each domain (2-3 per domain)
        - domain_attributes: Common attributes for each domain
        - area_distribution: Entities grouped by area (if available)

    Examples:
        Returns domain counts, sample entities, and common attributes

    Best Practices:
        - Use this as the first call when exploring an unfamiliar Home Assistant instance
        - Perfect for building context about the structure of the smart home
        - After getting an overview, use domain_summary_tool to dig deeper into specific domains
    """
    logger.info("Generating complete system overview")
    return await get_system_overview()


async def get_error_log() -> dict[str, Any]:
    """
    Get the Home Assistant error log for troubleshooting.

    Returns:
        A dictionary containing:
        - log_text: The full error log text
        - error_count: Number of ERROR entries found
        - warning_count: Number of WARNING entries found
        - integration_mentions: Map of integration names to mention counts
        - error: Error message if retrieval failed

    Examples:
        Returns errors, warnings count and integration mentions

    Best Practices:
        - Use this tool when troubleshooting specific Home Assistant errors
        - Look for patterns in repeated errors
        - Pay attention to timestamps to correlate errors with events
        - Focus on integrations with many mentions in the log
    """
    logger.info("Getting Home Assistant error log")
    return await get_hass_error_log()


async def system_health() -> dict[str, Any]:
    """
    Get system health information from Home Assistant.

    Returns:
        A dictionary containing system health information for each component.
        Each component includes health status and version information.

        Example response:
        {
            "homeassistant": {
                "healthy": true,
                "version": "2025.3.0"
            },
            "supervisor": {
                "healthy": true,
                "version": "2025.03.1"
            }
        }

    Examples:
        Check overall system health and component status

    Best Practices:
        - Use this tool to monitor system resources and health
        - Check after updates or when experiencing issues
        - Review all component health statuses, not just overall health
        - Note that some components may not be available in all HA installations
          (e.g., supervisor is only available on Home Assistant OS)

    Error Handling:
        - Returns error if endpoint is not available (some HA versions/configurations)
        - Gracefully handles missing components
        - Returns helpful error messages for permission issues
    """
    logger.info("Getting Home Assistant system health")
    return await get_system_health()


async def core_config() -> dict[str, Any]:
    """
    Get core configuration from Home Assistant.

    Returns:
        A dictionary containing core configuration information including:
        - location_name: The name of the location
        - time_zone: Configured timezone
        - unit_system: Unit system configuration (temperature, length, mass, volume)
        - components: List of all loaded components/integrations
        - version: Home Assistant version
        - latitude/longitude: Location coordinates
        - elevation: Elevation above sea level
        - currency: Configured currency
        - country: Configured country code
        - language: Configured language

        Example response:
        {
            "location_name": "Home",
            "time_zone": "America/New_York",
            "unit_system": {
                "length": "km",
                "mass": "g",
                "temperature": "°C",
                "volume": "L"
            },
            "version": "2025.3.0",
            "components": ["mqtt", "hue", "automation", ...]
        }

    Examples:
        Get timezone, unit system, and location information
        List all loaded components/integrations
        Check Home Assistant version and configuration details

    Best Practices:
        - Use to understand the HA instance configuration
        - Check which components are loaded before using specific integrations
        - Verify timezone and unit system settings for automations
        - Use for debugging location-based automations
    """
    logger.info("Getting Home Assistant core configuration")
    return await get_core_config()


async def restart_ha() -> dict[str, Any]:
    """
    Restart Home Assistant.

    ⚠️ WARNING: Temporarily disrupts all Home Assistant operations

    Returns:
        Result of restart operation

    Warning:
        ⚠️ This will restart Home Assistant, causing temporary unavailability.
        All entities and services will be unavailable during restart.
        Use with caution!

    Best Practices:
        - Only restart when necessary (e.g., after configuration changes)
        - Warn users about temporary unavailability
        - Consider restarting during low-activity periods
    """
    logger.info("Restarting Home Assistant")
    return await restart_home_assistant()


async def get_history(entity_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get the history of an entity's state changes.

    Args:
        entity_id: The entity ID to get history for
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        A dictionary containing:
        - entity_id: The entity ID requested
        - states: List of state objects with timestamps
        - count: Number of state changes found
        - first_changed: Timestamp of earliest state change
        - last_changed: Timestamp of most recent state change

    Examples:
        entity_id="light.living_room" - get 24h history
        entity_id="sensor.temperature", hours=168 - get 7 day history

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use for entities with discrete state changes rather than continuously changing sensors
        - Consider the state distribution rather than every individual state
    """
    logger.info(f"Getting history for entity: {entity_id}, hours: {hours}")

    try:
        # Call the API function to get history
        history_data = await get_entity_history(entity_id, hours)

        # Check for errors from the API call
        if isinstance(history_data, dict) and "error" in history_data:
            return {
                "entity_id": entity_id,
                "error": history_data["error"],
                "states": [],
                "count": 0,
            }

        # The result from the API is a list of lists of state changes
        # We need to flatten it and process it
        states = []
        if history_data and isinstance(history_data, list):
            for state_list in history_data:
                states.extend(state_list)

        if not states:
            return {
                "entity_id": entity_id,
                "states": [],
                "count": 0,
                "first_changed": None,
                "last_changed": None,
                "note": "No state changes found in the specified timeframe.",
            }

        # Sort states by last_changed timestamp
        states.sort(key=lambda x: x.get("last_changed", ""))

        # Extract first and last changed timestamps
        first_changed = states[0].get("last_changed")
        last_changed = states[-1].get("last_changed")

        return {
            "entity_id": entity_id,
            "states": states,
            "count": len(states),
            "first_changed": first_changed,
            "last_changed": last_changed,
        }
    except Exception as e:
        logger.error(f"Error processing history for {entity_id}: {str(e)}")
        return {
            "entity_id": entity_id,
            "error": f"Error processing history: {str(e)}",
            "states": [],
            "count": 0,
        }


async def domain_summary_tool(domain: str, example_limit: int = 3) -> dict[str, Any]:
    """
    Get a summary of entities in a specific domain.

    Args:
        domain: The domain to summarize (e.g., 'light', 'switch', 'sensor')
        example_limit: Maximum number of examples to include for each state

    Returns:
        A dictionary containing:
        - total_count: Number of entities in the domain
        - state_distribution: Count of entities in each state
        - examples: Sample entities for each state
        - common_attributes: Most frequently occurring attributes

    Examples:
        domain="light" - get light summary
        domain="climate", example_limit=5 - climate summary with more examples

    Best Practices:
        - Use this before retrieving all entities in a domain to understand what's available
    """
    logger.info(f"Getting domain summary for: {domain}")
    return await summarize_domain(domain, example_limit)
