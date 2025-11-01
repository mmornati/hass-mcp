"""Device MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant devices.
These tools are thin wrappers around the devices API layer.
"""

import logging
from typing import Any

from app.api.devices import (
    get_device_details,
    get_device_entities,
    get_device_statistics,
    get_devices,
)

logger = logging.getLogger(__name__)


async def list_devices_tool(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all devices in Home Assistant, optionally filtered by integration domain.

    Args:
        domain: Optional integration domain to filter devices by (e.g., 'hue', 'zwave')

    Returns:
        List of device dictionaries containing:
        - id: Unique device identifier
        - name: Device name
        - manufacturer: Manufacturer name
        - model: Model name
        - via_device_id: Parent device ID if device is connected via another device
        - area_id: Area ID the device belongs to

    Examples:
        domain=None - get all devices
        domain="hue" - get only Hue devices

    Best Practices:
        - Use domain filtering to reduce response size
        - Check device area_id to organize devices by location
    """
    logger.info("Getting list of devices" + (f" for domain: {domain}" if domain else ""))
    return await get_devices(domain=domain)


async def get_device_tool(device_id: str) -> dict[str, Any]:
    """
    Get detailed device information.

    Args:
        device_id: The device ID to get details for

    Returns:
        Device dictionary with complete information including:
        - id: Device identifier
        - name: Device name
        - manufacturer: Manufacturer name
        - model: Model name
        - sw_version: Software version
        - hw_version: Hardware version
        - area_id: Area ID
        - name_by_user: Custom name
        - disabled_by: Whether device is disabled
        - entities: List of entity IDs belonging to the device
        - entry_type: Configuration entry type

    Examples:
        device_id="abc123" - get details for device with ID abc123

    Best Practices:
        - Use this to understand device capabilities
        - Check entities list to see what the device controls
        - Review area_id to see device location
    """
    logger.info(f"Getting device details for: {device_id}")
    return await get_device_details(device_id)


async def get_device_entities_tool(device_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific device.

    Args:
        device_id: The device ID to get entities for

    Returns:
        List of entity dictionaries belonging to the device

    Examples:
        device_id="abc123" - get all entities for device with ID abc123

    Note:
        Entities are retrieved from the device's entity list.
        Returns empty list if device has no entities or device doesn't exist.

    Best Practices:
        - Use this to understand what a device controls
        - Check entities to see device capabilities
        - Use before removing or disabling a device
    """
    logger.info(f"Getting entities for device: {device_id}")
    return await get_device_entities(device_id)


async def get_device_stats_tool() -> dict[str, Any]:
    """
    Get statistics about devices (counts by manufacturer, model, etc.).

    Returns:
        Dictionary containing:
        - total_devices: Total number of devices
        - manufacturers: Dictionary of manufacturer counts
        - models: Dictionary of model counts
        - domains: Dictionary of domain counts
        - areas: Dictionary of area distribution

    Examples:
        Returns device statistics and distribution information

    Best Practices:
        - Use this to understand device distribution
        - Check manufacturer and model counts for insights
        - Analyze area distribution to see device placement
    """
    logger.info("Getting device statistics")
    return await get_device_statistics()
