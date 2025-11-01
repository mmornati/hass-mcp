"""System API module for hass-mcp.

This module provides functions for interacting with Home Assistant system information.
"""

import logging
import re
from typing import Any, cast

import httpx

from app.api.entities import filter_fields
from app.config import HA_URL, get_ha_headers
from app.core import DOMAIN_IMPORTANT_ATTRIBUTES, get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def get_hass_version() -> str:
    """
    Get the Home Assistant version from the API.

    Returns:
        Home Assistant version string (e.g., "2025.3.0")

    Example response:
        "2025.3.0"

    Note:
        Returns "unknown" if version cannot be retrieved.
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/config", headers=get_ha_headers())
    response.raise_for_status()
    data = cast(dict[str, Any], response.json())
    return data.get("version", "unknown")


@handle_api_errors
async def get_hass_error_log() -> dict[str, Any]:
    """
    Get the Home Assistant error log for troubleshooting.

    Returns:
        A dictionary containing:
        - log_text: The full error log text
        - error_count: Number of ERROR entries found
        - warning_count: Number of WARNING entries found
        - integration_mentions: Map of integration names to mention counts
        - error: Error message if retrieval failed

    Example response:
        {
            "log_text": "...",
            "error_count": 5,
            "warning_count": 12,
            "integration_mentions": {"mqtt": 3, "zwave": 2},
        }

    Best Practices:
        - Use this tool when troubleshooting specific Home Assistant errors
        - Look for patterns in repeated errors
        - Pay attention to timestamps to correlate errors with events
        - Focus on integrations with many mentions in the log
    """
    try:
        # Call the Home Assistant API error_log endpoint
        url = f"{HA_URL}/api/error_log"
        headers = get_ha_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                log_text = response.text

                # Count errors and warnings
                error_count = log_text.count("ERROR")
                warning_count = log_text.count("WARNING")

                # Extract integration mentions
                integration_mentions = {}

                # Look for patterns like [mqtt], [zwave], etc.
                for match in re.finditer(r"\[([a-zA-Z0-9_]+)\]", log_text):
                    integration = match.group(1).lower()
                    if integration not in integration_mentions:
                        integration_mentions[integration] = 0
                    integration_mentions[integration] += 1

                return {
                    "log_text": log_text,
                    "error_count": error_count,
                    "warning_count": warning_count,
                    "integration_mentions": integration_mentions,
                }
            return {
                "error": f"Error retrieving error log: {response.status_code} {response.reason_phrase}",
                "details": response.text,
                "log_text": "",
                "error_count": 0,
                "warning_count": 0,
                "integration_mentions": {},
            }
    except Exception as e:
        logger.error(f"Error retrieving Home Assistant error log: {str(e)}")
        return {
            "error": f"Error retrieving error log: {str(e)}",
            "log_text": "",
            "error_count": 0,
            "warning_count": 0,
            "integration_mentions": {},
        }


@handle_api_errors
async def get_system_overview() -> dict[str, Any]:
    """
    Get a comprehensive overview of the entire Home Assistant system.

    Returns:
        A dictionary containing:
        - total_entities: Total count of all entities
        - domains: Dictionary of domains with their entity counts and state distributions
        - domain_samples: Representative sample entities for each domain (2-3 per domain)
        - domain_attributes: Common attributes for each domain
        - area_distribution: Entities grouped by area (if available)
        - domain_count: Number of unique domains
        - most_common_domains: Top 5 domains by entity count

    Example response:
        {
            "total_entities": 150,
            "domains": {
                "light": {"count": 20, "states": {"on": 10, "off": 10}},
                "sensor": {"count": 50, "states": {"unavailable": 2, "30": 48}}
            },
            "domain_samples": {
                "light": [
                    {"entity_id": "light.living_room", "state": "on", "friendly_name": "Living Room"}
                ]
            },
            "domain_attributes": {
                "light": ["brightness", "color_mode", "friendly_name"]
            },
            "area_distribution": {
                "Living Room": {"light": 3, "sensor": 5}
            },
            "domain_count": 10,
            "most_common_domains": [("sensor", 50), ("light", 20)]
        }

    Best Practices:
        - Use this as the first call when exploring an unfamiliar Home Assistant instance
        - Perfect for building context about the structure of the smart home
        - After getting an overview, use domain_summary_tool to dig deeper into specific domains
    """
    try:
        # Get ALL entities with minimal fields for efficiency
        # We retrieve all entities since API calls don't consume tokens, only responses do
        client = await get_client()
        response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
        response.raise_for_status()
        all_entities_raw = cast(list[dict[str, Any]], response.json())

        # Apply lean formatting to reduce token usage in the response
        all_entities = []
        for entity in all_entities_raw:
            domain = entity["entity_id"].split(".")[0]

            # Start with basic lean fields
            lean_fields = ["entity_id", "state", "attr.friendly_name"]

            # Add domain-specific important attributes
            if domain in DOMAIN_IMPORTANT_ATTRIBUTES:
                for attr in DOMAIN_IMPORTANT_ATTRIBUTES[domain]:
                    lean_fields.append(f"attr.{attr}")

            # Filter and add to result
            all_entities.append(filter_fields(entity, lean_fields))

        # Initialize overview structure
        overview: dict[str, Any] = {
            "total_entities": len(all_entities),
            "domains": {},
            "domain_samples": {},
            "domain_attributes": {},
            "area_distribution": {},
        }

        # Group entities by domain
        domain_entities: dict[str, list[dict[str, Any]]] = {}
        for entity in all_entities:
            domain = entity["entity_id"].split(".")[0]
            if domain not in domain_entities:
                domain_entities[domain] = []
            domain_entities[domain].append(entity)

        # Process each domain
        for domain, entities in domain_entities.items():
            # Count entities in this domain
            count = len(entities)

            # Collect state distribution
            state_distribution: dict[str, int] = {}
            for entity in entities:
                state = entity.get("state", "unknown")
                if state not in state_distribution:
                    state_distribution[state] = 0
                state_distribution[state] += 1

            # Store domain information
            overview["domains"][domain] = {"count": count, "states": state_distribution}

            # Select representative samples (2-3 per domain)
            sample_limit = min(3, count)
            samples = []
            for i in range(sample_limit):
                entity = entities[i]
                samples.append(
                    {
                        "entity_id": entity["entity_id"],
                        "state": entity.get("state", "unknown"),
                        "friendly_name": entity.get("attributes", {}).get(
                            "friendly_name", entity["entity_id"]
                        ),
                    }
                )
            overview["domain_samples"][domain] = samples

            # Collect common attributes for this domain
            attribute_counts: dict[str, int] = {}
            for entity in entities:
                for attr in entity.get("attributes", {}):
                    if attr not in attribute_counts:
                        attribute_counts[attr] = 0
                    attribute_counts[attr] += 1

            # Get top 5 most common attributes for this domain
            common_attributes = sorted(attribute_counts.items(), key=lambda x: x[1], reverse=True)[
                :5
            ]
            overview["domain_attributes"][domain] = [attr for attr, count in common_attributes]

            # Group by area if available
            for entity in entities:
                area_id = entity.get("attributes", {}).get("area_id", "Unknown")
                area_name = entity.get("attributes", {}).get("area_name", area_id)

                if area_name not in overview["area_distribution"]:
                    overview["area_distribution"][area_name] = {}

                if domain not in overview["area_distribution"][area_name]:
                    overview["area_distribution"][area_name][domain] = 0

                overview["area_distribution"][area_name][domain] += 1

        # Add summary information
        overview["domain_count"] = len(domain_entities)
        overview["most_common_domains"] = sorted(
            [(domain, len(entities)) for domain, entities in domain_entities.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return overview
    except Exception as e:
        logger.error(f"Error generating system overview: {str(e)}")
        return {"error": f"Error generating system overview: {str(e)}"}


@handle_api_errors
async def get_system_health() -> dict[str, Any]:
    """
    Get system health information from Home Assistant.

    Returns:
        A dictionary containing system health information for each component:
        - homeassistant: Core HA health and version
        - supervisor: Supervisor health and version (if available)
        - Other integrations with health information

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
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/system_health", headers=get_ha_headers())
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def get_core_config() -> dict[str, Any]:
    """
    Get core configuration from Home Assistant.

    Returns:
        A dictionary containing core configuration information:
        - location_name: Location name
        - time_zone: Configured timezone
        - unit_system: Unit system configuration
        - components: List of loaded components
        - version: Home Assistant version
        - config_dir: Configuration directory path
        - whitelist_external_dirs: Whitelisted directories
        - allowlist_external_dirs: Allowlisted directories
        - allowlist_external_urls: Allowlisted URLs
        - latitude/longitude: Location coordinates
        - elevation: Elevation above sea level
        - currency: Configured currency
        - country: Configured country
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
            "components": ["mqtt", "hue", ...]
        }

    Best Practices:
        - Use to understand the HA instance configuration
        - Check which components are loaded before using specific integrations
        - Verify timezone and unit system settings for automations
        - Use for debugging location-based automations
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/config", headers=get_ha_headers())
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def restart_home_assistant() -> dict[str, Any]:
    """
    Restart Home Assistant.

    Returns:
        Response from the restart operation

    Example response:
        []

    Warning:
        ⚠️ This will restart Home Assistant, causing temporary unavailability.
        All entities and services will be unavailable during restart.
        Use with caution!

    Best Practices:
        - Only restart when necessary (e.g., after configuration changes)
        - Warn users about temporary unavailability
        - Consider restarting during low-activity periods
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/homeassistant/restart",
        headers=get_ha_headers(),
        json={},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
