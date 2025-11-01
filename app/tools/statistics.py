"""Statistics MCP tools for hass-mcp.

This module provides MCP tools for statistics and analytics.
These tools are thin wrappers around the statistics API layer.
"""

import logging
from typing import Any

from app.api.statistics import (
    analyze_usage_patterns,
    get_domain_statistics,
    get_entity_statistics,
)

logger = logging.getLogger(__name__)


async def get_entity_statistics_tool(entity_id: str, period_days: int = 7) -> dict[str, Any]:
    """
    Get statistics for an entity (min, max, mean, median).

    Args:
        entity_id: The entity ID to get statistics for
        period_days: Number of days to analyze (default: 7)

    Returns:
        Dictionary containing:
        - entity_id: The entity ID analyzed
        - period_days: Number of days analyzed
        - data_points: Number of numeric data points found
        - statistics: Dictionary with min, max, mean, median values
        - note: Note if no data or entity is not numeric

    Examples:
        entity_id="sensor.temperature", period_days=7 - get temperature statistics for last week
        entity_id="sensor.humidity", period_days=30 - get humidity statistics for last month

    Note:
        This calculates statistics from entity history data.
        Only numeric entities can provide meaningful statistics.
        Returns empty statistics if entity is not numeric or has no data.

    Best Practices:
        - Use for sensors with numeric values (temperature, humidity, etc.)
        - Keep period_days reasonable (7-30) for performance
        - Check for empty statistics if entity is not numeric
        - Use to analyze energy consumption, temperature trends, etc.
    """
    logger.info(f"Getting statistics for entity: {entity_id}, period_days: {period_days}")
    return await get_entity_statistics(entity_id, period_days)


async def get_domain_statistics_tool(domain: str, period_days: int = 7) -> dict[str, Any]:
    """
    Get aggregate statistics for all entities in a domain.

    Args:
        domain: The domain to get statistics for (e.g., 'sensor', 'light')
        period_days: Number of days to analyze (default: 7)

    Returns:
        Dictionary containing:
        - domain: The domain analyzed
        - period_days: Number of days analyzed
        - total_entities: Total number of entities in the domain
        - entity_statistics: Dictionary mapping entity_id to statistics

    Examples:
        domain="sensor", period_days=7 - get statistics for all sensors over last week
        domain="energy", period_days=30 - get statistics for all energy entities over last month

    Note:
        This aggregates statistics for entities in a domain.
        Limited to first 10 entities for performance.
        Only numeric entities are included in entity_statistics.

    Best Practices:
        - Use for domains with numeric entities (sensor, energy, etc.)
        - Keep period_days reasonable (7-30) for performance
        - Consider using get_entity_statistics for individual entities
        - Use to analyze trends across multiple entities in a domain
    """
    logger.info(f"Getting statistics for domain: {domain}, period_days: {period_days}")
    return await get_domain_statistics(domain, period_days)


async def analyze_usage_patterns_tool(entity_id: str, days: int = 30) -> dict[str, Any]:
    """
    Analyze usage patterns (when device is used most).

    Args:
        entity_id: The entity ID to analyze
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary containing:
        - entity_id: The entity ID analyzed
        - period_days: Number of days analyzed
        - total_events: Total number of logbook events
        - hourly_distribution: Dictionary mapping hour (0-23) to event count
        - daily_distribution: Dictionary mapping day name to event count
        - peak_hour: Hour with most events (0-23)
        - peak_day: Day of week with most events

    Examples:
        entity_id="light.living_room", days=30 - analyze light usage patterns over last month
        entity_id="switch.kitchen", days=7 - analyze switch usage patterns over last week

    Note:
        This analyzes logbook entries to find usage patterns.
        Useful for understanding when devices are used most.
        Helps optimize automations based on actual usage.

    Best Practices:
        - Use for devices with frequent state changes (lights, switches, etc.)
        - Keep days reasonable (7-30) for performance
        - Use results to optimize automation schedules
        - Use to identify peak usage times for energy optimization
    """
    logger.info(f"Analyzing usage patterns for entity: {entity_id}, days: {days}")
    return await analyze_usage_patterns(entity_id, days)
