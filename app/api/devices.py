"""Devices API module for hass-mcp.

This module provides functions for interacting with Home Assistant devices.
"""

import logging
from typing import Any, cast

from app.api.entities import get_entity_state
from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def get_devices(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of all devices, optionally filtered by integration domain.

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
        - name_by_user: User-defined name (if set)
        - disabled_by: Reason device is disabled (if disabled)
        - entities: List of entity IDs belonging to this device
        - identifiers: List of identifier tuples (e.g., [["domain", "unique_id"]])
        - connections: List of connection tuples (e.g., [["mac", "aa:bb:cc:dd:ee:ff"]])

    Example response:
        [
            {
                "id": "device_id",
                "name": "Device Name",
                "manufacturer": "Manufacturer",
                "model": "Model Name",
                "via_device_id": null,
                "area_id": "living_room",
                "entities": ["entity_id_1", "entity_id_2"],
                "identifiers": [["domain", "unique_id"]],
                "connections": [["mac", "aa:bb:cc:dd:ee:ff"]]
            }
        ]

    Note:
        Devices represent physical hardware units.
        Filtering by domain matches the first identifier's domain.
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/devices",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    devices = cast(list[dict[str, Any]], response.json())

    # Filter by domain if specified
    if domain:
        filtered_devices = []
        for device in devices:
            identifiers = device.get("identifiers", [])
            if identifiers and len(identifiers) > 0:
                # First identifier contains [domain, unique_id]
                device_domain = identifiers[0][0] if len(identifiers[0]) > 0 else None
                if device_domain == domain:
                    filtered_devices.append(device)
        devices = filtered_devices

    return devices


@handle_api_errors
async def get_device_details(device_id: str) -> dict[str, Any]:
    """
    Get detailed device information.

    Args:
        device_id: The device ID to get details for

    Returns:
        Detailed device dictionary with:
        - id: Unique device identifier
        - name: Device name
        - manufacturer: Manufacturer name
        - model: Model name
        - via_device_id: Parent device ID if device is connected via another device
        - area_id: Area ID the device belongs to
        - name_by_user: User-defined name (if set)
        - disabled_by: Reason device is disabled (if disabled)
        - entities: List of entity IDs belonging to this device
        - identifiers: List of identifier tuples
        - connections: List of connection tuples (MAC addresses, etc.)

    Example response:
        {
            "id": "device_id",
            "name": "Device Name",
            "manufacturer": "Manufacturer",
            "model": "Model Name",
            "via_device_id": null,
            "area_id": "living_room",
            "entities": ["entity_id_1", "entity_id_2"],
            "identifiers": [["domain", "unique_id"]],
            "connections": [["mac", "aa:bb:cc:dd:ee:ff"]]
        }

    Note:
        This provides the same information as get_devices but for a single device.
        Useful when you already know the device_id.
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/devices/{device_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


@handle_api_errors
async def get_device_entities(device_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific device.

    Args:
        device_id: The device ID to get entities for

    Returns:
        List of entity dictionaries belonging to the device

    Example response:
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {...}
            },
            {
                "entity_id": "sensor.temperature",
                "state": "21.5",
                "attributes": {...}
            }
        ]

    Note:
        Entities are retrieved from the device's entity list.
        Returns empty list if device has no entities or device doesn't exist.
    """
    device = await get_device_details(device_id)

    # Check if we got an error response
    if isinstance(device, dict) and "error" in device:
        return [device]  # Return list with error dict for consistency

    entity_ids = device.get("entities", [])
    entities = []
    for entity_id in entity_ids:
        entity = await get_entity_state(entity_id, lean=True)
        entities.append(entity)

    return entities


@handle_api_errors
async def get_device_statistics() -> dict[str, Any]:
    """
    Get statistics about devices (counts by manufacturer, model, etc.).

    Returns:
        Dictionary containing:
        - total_devices: Total number of devices
        - by_manufacturer: Dictionary mapping manufacturer to count
        - by_model: Dictionary mapping model to count
        - by_integration: Dictionary mapping integration domain to count
        - disabled_devices: Number of disabled devices

    Example response:
        {
            "total_devices": 25,
            "by_manufacturer": {
                "Philips": 5,
                "Samsung": 3,
                "Unknown": 2
            },
            "by_model": {
                "Hue Bridge": 2,
                "Smart TV": 1
            },
            "by_integration": {
                "hue": 5,
                "zwave": 10,
                "mqtt": 5
            },
            "disabled_devices": 1
        }

    Best Practices:
        - Use this to understand device distribution
        - Identify common manufacturers and models
        - See which integrations have the most devices
        - Track disabled devices
    """
    devices = await get_devices()

    stats: dict[str, Any] = {
        "total_devices": len(devices),
        "by_manufacturer": {},
        "by_model": {},
        "by_integration": {},
        "disabled_devices": 0,
    }

    for device in devices:
        manufacturer = device.get("manufacturer") or "Unknown"
        model = device.get("model") or "Unknown"

        # Count by manufacturer
        stats["by_manufacturer"][manufacturer] = stats["by_manufacturer"].get(manufacturer, 0) + 1

        # Count by model
        stats["by_model"][model] = stats["by_model"].get(model, 0) + 1

        # Count by integration
        identifiers = device.get("identifiers", [])
        if identifiers and len(identifiers) > 0:
            integration = identifiers[0][0] if len(identifiers[0]) > 0 else "Unknown"
            stats["by_integration"][integration] = stats["by_integration"].get(integration, 0) + 1

        # Count disabled
        if device.get("disabled_by"):
            stats["disabled_devices"] += 1

    return stats
