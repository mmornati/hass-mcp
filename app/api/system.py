"""System API module for hass-mcp.

This module provides functions for interacting with Home Assistant system information.
"""

import logging
import re
from typing import Any, cast

from app.api.entities import filter_fields
from app.config import HA_URL, get_ha_headers
from app.core import DOMAIN_IMPORTANT_ATTRIBUTES, get_client
from app.core.cache.config import get_cache_config
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

    Example response:
        {
            "log_text": "...",
            "error_count": 5,
            "warning_count": 10,
            "integration_mentions": {
                "hue": 3,
                "mqtt": 2
            }
        }

    Best Practices:
        - Use this tool when troubleshooting specific Home Assistant errors
        - Look for patterns in repeated errors
        - Pay attention to timestamps to correlate errors with events
        - Focus on integrations with many mentions in the log
    """
    try:
        client = await get_client()
        response = await client.get(
            f"{HA_URL}/api/error_log", headers=get_ha_headers(), timeout=30.0
        )
        response.raise_for_status()
        log_text = response.text

        # Parse log for errors and warnings
        error_count = len(re.findall(r"ERROR", log_text))
        warning_count = len(re.findall(r"WARNING", log_text))

        # Extract integration mentions
        integration_mentions = {}
        for line in log_text.split("\n"):
            # Look for patterns like [integration_name] or (integration_name)
            matches = re.findall(r"\[([^\]]+)\]|\(([^\)]+)\)", line)
            for match in matches:
                integration_name = match[0] if match[0] else match[1]
                if integration_name and integration_name not in ["INFO", "ERROR", "WARNING"]:
                    integration_mentions[integration_name] = (
                        integration_mentions.get(integration_name, 0) + 1
                    )

        return {
            "log_text": log_text,
            "error_count": error_count,
            "warning_count": warning_count,
            "integration_mentions": integration_mentions,
        }
    except Exception as e:
        return {
            "log_text": "",
            "error_count": 0,
            "warning_count": 0,
            "integration_mentions": {},
            "error": str(e),
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
        response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers(), timeout=30.0)
        response.raise_for_status()
        all_entities = cast(list[dict[str, Any]], response.json())

        # Organize by domain
        domains: dict[str, dict[str, Any]] = {}
        domain_samples: dict[str, list[dict[str, Any]]] = {}
        domain_attributes: dict[str, set[str]] = {}
        area_distribution: dict[str, dict[str, int]] = {}

        for entity in all_entities:
            entity_id = entity.get("entity_id", "")
            if "." not in entity_id:
                continue

            domain = entity_id.split(".")[0]
            state = entity.get("state", "unknown")
            attributes = entity.get("attributes", {})
            area_id = attributes.get("area_id")

            # Update domain counts
            if domain not in domains:
                domains[domain] = {"count": 0, "states": {}}
            domains[domain]["count"] += 1
            domains[domain]["states"][state] = domains[domain]["states"].get(state, 0) + 1

            # Collect samples (first 2-3 per domain)
            if domain not in domain_samples:
                domain_samples[domain] = []
            if len(domain_samples[domain]) < 3:
                # Filter to important fields only
                sample = filter_fields(entity, DOMAIN_IMPORTANT_ATTRIBUTES.get(domain, []))
                domain_samples[domain].append(sample)

            # Collect attributes
            if domain not in domain_attributes:
                domain_attributes[domain] = set()
            domain_attributes[domain].update(attributes.keys())

            # Track area distribution
            if area_id:
                if area_id not in area_distribution:
                    area_distribution[area_id] = {}
                area_distribution[area_id][domain] = area_distribution[area_id].get(domain, 0) + 1

        # Convert sets to lists for JSON serialization
        domain_attributes_serializable = {
            domain: list(attrs) for domain, attrs in domain_attributes.items()
        }

        # Calculate most common domains
        most_common_domains = sorted(
            [(domain, data["count"]) for domain, data in domains.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "total_entities": len(all_entities),
            "domains": domains,
            "domain_samples": domain_samples,
            "domain_attributes": domain_attributes_serializable,
            "area_distribution": area_distribution,
            "domain_count": len(domains),
            "most_common_domains": most_common_domains,
        }
    except Exception as e:
        logger.error(f"Error getting system overview: {e}", exc_info=True)
        return {
            "total_entities": 0,
            "domains": {},
            "domain_samples": {},
            "domain_attributes": {},
            "area_distribution": {},
            "domain_count": 0,
            "most_common_domains": [],
            "error": str(e),
        }


@handle_api_errors
async def get_system_health() -> dict[str, Any]:
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
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/system_health", headers=get_ha_headers())
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def get_core_config() -> dict[str, Any]:
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


@handle_api_errors
async def get_cache_configuration() -> dict[str, Any]:
    """
    Get the current cache configuration.

    Returns:
        A dictionary containing:
        - enabled: Whether caching is enabled
        - backend: The cache backend type (memory, redis, file)
        - default_ttl: Default TTL in seconds
        - max_size: Maximum cache size
        - redis_url: Redis URL if configured (None otherwise)
        - cache_dir: Cache directory path
        - endpoints: Dictionary of endpoint-specific TTL configurations

    Example response:
        {
            "enabled": true,
            "backend": "memory",
            "default_ttl": 300,
            "max_size": 1000,
            "redis_url": None,
            "cache_dir": ".cache",
            "endpoints": {
                "entities": {"ttl": 1800},
                "automations": {"ttl": 3600}
            }
        }

    Best Practices:
        - Use this to check current cache configuration
        - Verify endpoint-specific TTLs are set correctly
        - Check cache backend type before making assumptions about persistence
    """
    config = get_cache_config()
    return config.get_all_config()


@handle_api_errors
async def update_cache_endpoint_ttl(
    domain: str, ttl: int, operation: str | None = None
) -> dict[str, Any]:
    """
    Update the TTL for a specific cache endpoint at runtime.

    Args:
        domain: The API domain (e.g., 'entities', 'automations')
        ttl: TTL in seconds
        operation: Optional operation name (e.g., 'list', 'get_state')

    Returns:
        Dictionary with status and updated configuration

    Example response:
        {
            "status": "success",
            "message": "Updated TTL for entities.list: 1800s",
            "domain": "entities",
            "operation": "list",
            "ttl": 1800
        }

    Best Practices:
        - Use this to adjust TTLs at runtime without restarting
        - Set shorter TTLs for frequently changing data
        - Set longer TTLs for static data
        - Changes take effect immediately for new cache entries
    """
    config = get_cache_config()
    config.update_endpoint_ttl(domain, ttl, operation)
    return {
        "status": "success",
        "message": f"Updated TTL for {domain}{'.' + operation if operation else ''}: {ttl}s",
        "domain": domain,
        "operation": operation,
        "ttl": ttl,
    }


@handle_api_errors
async def reload_cache_config() -> dict[str, Any]:
    """
    Reload cache configuration from file and environment variables.

    Returns:
        Dictionary with status and reloaded configuration

    Example response:
        {
            "status": "success",
            "message": "Cache configuration reloaded",
            "config": {
                "enabled": true,
                "backend": "memory",
                ...
            }
        }

    Best Practices:
        - Use this after modifying the cache configuration file
        - Reload to pick up environment variable changes
        - Note: This resets any runtime TTL changes made via update_cache_endpoint_ttl
    """
    config = get_cache_config()
    config.reload()
    return {
        "status": "success",
        "message": "Cache configuration reloaded",
        "config": config.get_all_config(),
    }
