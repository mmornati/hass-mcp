"""Entity description generation module for hass-mcp.

This module provides enhanced entity description generation with templates,
multi-language support, and context-aware descriptions for better semantic search.
"""

import logging
from typing import Any

from app.api.areas import get_areas
from app.api.devices import get_device_details

logger = logging.getLogger(__name__)

# Description templates for different entity domains
DESCRIPTION_TEMPLATES = {
    "light": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Supports {capabilities}. Currently {state}. "
        "Part of the {manufacturer} {model} system."
    ),
    "sensor": (
        "{friendly_name} - {domain} entity ({device_class}) in the {area_name} area. "
        "Measures {unit_of_measurement}. Currently {state}. "
        "Manufactured by {manufacturer}."
    ),
    "switch": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "climate": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Current temperature: {current_temperature}°C. "
        "Target temperature: {temperature}°C. Mode: {hvac_mode}."
    ),
    "cover": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "fan": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "lock": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "media_player": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "camera": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
    "default": (
        "{friendly_name} - {domain} entity in the {area_name} area. "
        "Currently {state}. Part of {device_name}."
    ),
}


async def get_area_name(area_id: str) -> str | None:
    """
    Get area name from area_id.

    Args:
        area_id: The area ID to get name for

    Returns:
        Area name if found, None otherwise
    """
    try:
        areas = await get_areas()
        if isinstance(areas, list):
            for area in areas:
                if area.get("area_id") == area_id:
                    return area.get("name")
    except Exception as e:
        logger.debug(f"Could not get area name for {area_id}: {e}")
    return None


async def get_device_info(device_id: str | None) -> dict[str, Any] | None:
    """
    Get device information from device_id.

    Args:
        device_id: The device ID to get information for

    Returns:
        Device information dictionary if found, None otherwise
    """
    if not device_id:
        return None

    try:
        device_info = await get_device_details(device_id)
        if isinstance(device_info, dict):
            return device_info
    except Exception as e:
        logger.debug(f"Could not get device info for {device_id}: {e}")
    return None


def extract_capabilities(entity: dict[str, Any]) -> str:
    """
    Extract entity capabilities as a string.

    Args:
        entity: Entity state dictionary

    Returns:
        String describing entity capabilities
    """
    capabilities = []
    attributes = entity.get("attributes", {})
    domain = entity.get("entity_id", "").split(".")[0] if entity.get("entity_id") else "unknown"

    if domain == "light":
        supported_color_modes = attributes.get("supported_color_modes", [])
        if supported_color_modes:
            capabilities.append(f"color modes: {', '.join(supported_color_modes)}")
        if attributes.get("brightness") is not None:
            capabilities.append("brightness control")
        if attributes.get("color_temp") is not None:
            capabilities.append("color temperature control")
        if attributes.get("rgb_color") is not None:
            capabilities.append("RGB color control")
    elif domain == "sensor":
        device_class = attributes.get("device_class", "")
        if device_class:
            capabilities.append(f"{device_class} sensor")
    elif domain == "climate":
        hvac_modes = attributes.get("hvac_modes", [])
        if hvac_modes:
            capabilities.append(f"HVAC modes: {', '.join(hvac_modes)}")
        if attributes.get("temperature") is not None:
            capabilities.append("temperature control")
    elif domain == "cover":
        supported_features = attributes.get("supported_features", 0)
        if supported_features:
            capabilities.append("cover control")

    return ", ".join(capabilities) if capabilities else "basic control"


async def generate_entity_description_enhanced(  # noqa: PLR0915
    entity: dict[str, Any],
    area_name: str | None = None,
    device_info: dict[str, Any] | None = None,
    use_template: bool = True,
    language: str = "en",
) -> str:
    """
    Generate rich, contextual description for entity embedding using templates.

    This enhanced version supports:
    - Template-based description generation
    - Multi-language support (currently English only)
    - Context-aware descriptions
    - Rich metadata extraction

    Args:
        entity: Entity state dictionary
        area_name: Optional area name (will be fetched if not provided)
        device_info: Optional device information (will be fetched if not provided)
        use_template: Whether to use template-based generation (default: True)
        language: Language for description (default: "en")

    Returns:
        Rich text description of the entity
    """
    entity_id = entity.get("entity_id", "")
    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
    attributes = entity.get("attributes", {})

    # Get area name if not provided
    if not area_name:
        area_id = attributes.get("area_id")
        if area_id:
            area_name = await get_area_name(area_id)

    # Get device info if not provided
    if not device_info:
        device_id = attributes.get("device_id")
        if device_id:
            device_info = await get_device_info(device_id)

    # Extract metadata
    friendly_name = attributes.get("friendly_name", "")
    if not friendly_name:
        # Fall back to entity_id if no friendly name
        friendly_name = entity_id.replace("_", " ").replace(".", " ").title()

    state = entity.get("state", "unknown")
    area_name = area_name or "unknown area"

    # Extract device information
    manufacturer = "unknown"
    model = "unknown"
    device_name = "unknown device"
    if device_info:
        manufacturer = (
            device_info.get("manufacturer_by", {}).get("manufacturer")
            or device_info.get("manufacturer")
            or "unknown"
        )
        model = (
            device_info.get("model_by", {}).get("model") or device_info.get("model") or "unknown"
        )
        device_name = device_info.get("name_by_user") or device_info.get("name") or "unknown device"

    # Extract capabilities
    capabilities = extract_capabilities(entity)

    # Build description using template or fallback
    if use_template and domain in DESCRIPTION_TEMPLATES:
        template = DESCRIPTION_TEMPLATES[domain]
    elif use_template:
        template = DESCRIPTION_TEMPLATES["default"]
    else:
        # Fallback to simple description
        return f"{friendly_name} - {domain} entity in the {area_name} area. Currently {state}."

    # Prepare template variables
    template_vars: dict[str, Any] = {
        "friendly_name": friendly_name,
        "domain": domain,
        "area_name": area_name,
        "state": state,
        "capabilities": capabilities,
        "manufacturer": manufacturer,
        "model": model,
        "device_name": device_name,
    }

    # Add domain-specific attributes
    if domain == "sensor":
        template_vars["device_class"] = attributes.get("device_class", "generic")
        template_vars["unit_of_measurement"] = attributes.get("unit_of_measurement", "")
    elif domain == "climate":
        template_vars["current_temperature"] = attributes.get("current_temperature", "unknown")
        template_vars["temperature"] = attributes.get("temperature", "unknown")
        template_vars["hvac_mode"] = attributes.get("hvac_mode", "unknown")

    # Format template
    try:
        description = template.format(**template_vars)
    except KeyError as e:
        logger.warning(f"Template variable missing: {e}, using fallback")
        # Fallback to simple description
        description = (
            f"{friendly_name} - {domain} entity in the {area_name} area. Currently {state}."
        )

    # Clean up description
    description = description.replace("unknown area", "an area")
    description = description.replace("unknown device", "a device")
    description = description.replace("unknown", "N/A")

    return description


async def generate_entity_description_batch(
    entities: list[dict[str, Any]],
    use_template: bool = True,
    language: str = "en",
) -> dict[str, str]:
    """
    Generate descriptions for multiple entities in batch.

    Args:
        entities: List of entity state dictionaries
        use_template: Whether to use template-based generation
        language: Language for descriptions

    Returns:
        Dictionary mapping entity_id to description
    """
    descriptions = {}

    # Get all areas and devices in batch
    area_ids = set()
    device_ids = set()

    for entity in entities:
        area_id = entity.get("attributes", {}).get("area_id")
        if area_id:
            area_ids.add(area_id)
        device_id = entity.get("attributes", {}).get("device_id")
        if device_id:
            device_ids.add(device_id)

    # Fetch all areas
    areas_map = {}
    try:
        areas = await get_areas()
        if isinstance(areas, list):
            for area in areas:
                area_id = area.get("area_id")
                if area_id:
                    areas_map[area_id] = area.get("name")
    except Exception as e:
        logger.warning(f"Failed to fetch areas: {e}")

    # Fetch all devices
    devices_map = {}
    for device_id in device_ids:
        try:
            device_info = await get_device_info(device_id)
            if device_info:
                devices_map[device_id] = device_info
        except Exception as e:
            logger.debug(f"Failed to fetch device {device_id}: {e}")

    # Generate descriptions
    for entity in entities:
        entity_id = entity.get("entity_id")
        if not entity_id:
            continue

        area_id = entity.get("attributes", {}).get("area_id")
        area_name = areas_map.get(area_id) if area_id else None

        device_id = entity.get("attributes", {}).get("device_id")
        device_info = devices_map.get(device_id) if device_id else None

        description = await generate_entity_description_enhanced(
            entity,
            area_name=area_name,
            device_info=device_info,
            use_template=use_template,
            language=language,
        )
        descriptions[entity_id] = description

    return descriptions
