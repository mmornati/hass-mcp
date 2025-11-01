import json
import logging
import re
import urllib.parse
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.api.automations import (
    create_automation,
    get_automation_config,
    get_automations,
)
from app.api.entities import (
    filter_fields,
    get_entities,
    get_entity_history,
    get_entity_state,
)
from app.config import HA_URL, get_ha_headers
from app.core import (
    DOMAIN_IMPORTANT_ATTRIBUTES,
    get_client,
    handle_api_errors,
)

# Set up logging
logger = logging.getLogger(__name__)


# API Functions
@handle_api_errors
async def get_hass_version() -> str:
    """Get the Home Assistant version from the API"""
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/config", headers=get_ha_headers())
    response.raise_for_status()
    data = response.json()
    return data.get("version", "unknown")


@handle_api_errors
async def call_service(
    domain: str, service: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Call a Home Assistant service"""
    if data is None:
        data = {}

    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/{domain}/{service}", headers=get_ha_headers(), json=data
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def summarize_domain(domain: str, example_limit: int = 3) -> dict[str, Any]:
    """
    Generate a summary of entities in a domain

    Args:
        domain: The domain to summarize (e.g., 'light', 'switch')
        example_limit: Maximum number of examples to include for each state

    Returns:
        Dictionary with summary information
    """
    entities = await get_entities(domain=domain)

    # Check if we got an error response
    if isinstance(entities, dict) and "error" in entities:
        return entities  # Just pass through the error

    try:
        # Initialize summary data
        total_count = len(entities)
        state_counts = {}
        state_examples = {}
        attributes_summary = {}

        # Process entities to build the summary
        for entity in entities:
            state = entity.get("state", "unknown")

            # Count states
            if state not in state_counts:
                state_counts[state] = 0
                state_examples[state] = []
            state_counts[state] += 1

            # Add examples (up to the limit)
            if len(state_examples[state]) < example_limit:
                example = {
                    "entity_id": entity["entity_id"],
                    "friendly_name": entity.get("attributes", {}).get(
                        "friendly_name", entity["entity_id"]
                    ),
                }
                state_examples[state].append(example)

            # Collect attribute keys for summary
            for attr_key in entity.get("attributes", {}):
                if attr_key not in attributes_summary:
                    attributes_summary[attr_key] = 0
                attributes_summary[attr_key] += 1

        # Create the summary
        summary = {
            "domain": domain,
            "total_count": total_count,
            "state_distribution": state_counts,
            "examples": state_examples,
            "common_attributes": sorted(
                [(k, v) for k, v in attributes_summary.items()], key=lambda x: x[1], reverse=True
            )[:10],  # Top 10 most common attributes
        }

        return summary
    except Exception as e:
        return {"error": f"Error generating domain summary: {str(e)}"}


# Re-export automation functions from api/automations for backwards compatibility
# All automation functions have been moved to app/api/automations.py


@handle_api_errors
async def restart_home_assistant() -> dict[str, Any]:
    """Restart Home Assistant"""
    return await call_service("homeassistant", "restart", {})


@handle_api_errors
async def get_scripts() -> list[dict[str, Any]]:
    """
    Get list of all scripts

    Returns:
        List of script dictionaries containing:
        - entity_id: The script entity ID (e.g., 'script.turn_on_lights')
        - state: Current state of the script
        - friendly_name: Display name of the script
        - last_triggered: Timestamp of last execution (if available)
        - alias: Script alias/name
    """
    # Scripts can be retrieved via states API
    script_entities = await get_entities(domain="script")

    # Extract script information
    scripts = []
    for entity in script_entities:
        script_info = {
            "entity_id": entity.get("entity_id"),
            "state": entity.get("state"),
        }

        # Add attributes if available
        attributes = entity.get("attributes", {})
        if "friendly_name" in attributes:
            script_info["friendly_name"] = attributes["friendly_name"]
        if "alias" in attributes:
            script_info["alias"] = attributes["alias"]
        if "last_triggered" in attributes:
            script_info["last_triggered"] = attributes["last_triggered"]

        scripts.append(script_info)

    return scripts


@handle_api_errors
async def get_script_config(script_id: str) -> dict[str, Any]:
    """
    Get script configuration (sequence of actions)

    Args:
        script_id: The script ID to get (without 'script.' prefix)

    Returns:
        Script configuration dictionary with:
        - entity_id: The script entity ID
        - state: Current state
        - attributes: Script attributes including configuration
        - config: Script configuration if available via config API

    Note:
        Script configuration might be available via config API or
        only through entity state depending on Home Assistant version.
        This function tries the config API first, then falls back to entity state.
    """
    entity_id = f"script.{script_id}"

    # Try to get config via config API if available
    try:
        client = await get_client()
        response = await client.get(
            f"{HA_URL}/api/config/scripts/{script_id}",
            headers=get_ha_headers(),
        )
        if response.status_code == 200:
            config_data = response.json()
            # Merge with entity state for complete information
            entity = await get_entity_state(entity_id, lean=False)
            config_data["entity"] = entity
            return config_data
    except Exception:  # nosec B110
        # Config API not available, fall through to entity state
        pass

    # Fallback to entity state
    return await get_entity_state(entity_id, lean=False)


@handle_api_errors
async def run_script(script_id: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Execute a script with optional variables

    Args:
        script_id: The script ID to execute (without 'script.' prefix)
        variables: Optional dictionary of variables to pass to the script

    Returns:
        Response from the script execution

    Examples:
        # Run script without variables
        result = await run_script("turn_on_lights")

        # Run script with variables
        result = await run_script("notify", {"message": "Hello", "target": "user1"})

    Note:
        Scripts execute asynchronously. The response indicates the script was started,
        not necessarily that it completed.
    """
    data: dict[str, Any] = {}
    if variables:
        data["variables"] = variables

    return await call_service("script", script_id, data)


@handle_api_errors
async def reload_scripts() -> dict[str, Any]:
    """
    Reload all scripts from configuration

    Returns:
        Response from the reload operation

    Note:
        Reloading scripts reloads all script configurations from YAML files.
        This is useful after modifying script configuration files.
    """
    return await call_service("script", "reload", {})


@handle_api_errors
async def test_template(
    template_string: str,
    entity_context: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test Jinja2 template rendering

    Args:
        template_string: The Jinja2 template string to test
        entity_context: Optional dictionary of entity IDs to provide as context
                         (e.g., {"entity_id": "light.living_room"})

    Returns:
        Dictionary containing:
        - result: The rendered template result
        - listeners: Entity listeners (if applicable)
        - error: Error message if template rendering failed

    Examples:
        # Test a simple template
        result = await test_template("{{ states('sensor.temperature') }}")

        # Test with entity context
        result = await test_template(
            "{{ states('light.living_room') }}",
            {"entity_id": "light.living_room"}
        )

    Note:
        Template testing API might not be available in all Home Assistant versions.
        If unavailable, returns a helpful error message.
    """
    client = await get_client()

    payload: dict[str, Any] = {"template": template_string}
    if entity_context:
        payload["entity_id"] = entity_context

    response = await client.post(
        f"{HA_URL}/api/template",
        headers=get_ha_headers(),
        json=payload,
    )

    if response.status_code == 404:
        # Template API might not be available
        return {
            "error": "Template testing API not available in this Home Assistant version",
            "note": "Try using the script developer tools in Home Assistant UI",
            "template": template_string,
        }

    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_areas() -> list[dict[str, Any]]:
    """
    Get list of all areas

    Returns:
        List of area dictionaries containing:
        - area_id: Unique identifier for the area
        - name: Display name of the area
        - aliases: List of aliases for the area
        - picture: Path to area picture (if available)

    Example response:
        [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": [],
                "picture": null
            }
        ]
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/area_registry",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_area_entities(area_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific area

    Args:
        area_id: The area ID to get entities for

    Returns:
        List of entities in the specified area

    Note:
        Entities are filtered by their area_id attribute.
        Returns empty list if area has no entities or area doesn't exist.
    """
    # Get all entities and filter by area_id
    all_entities = await get_entities(lean=True)

    area_entities = []
    for entity in all_entities:
        entity_area_id = entity.get("attributes", {}).get("area_id")
        if entity_area_id == area_id:
            area_entities.append(entity)

    return area_entities


@handle_api_errors
async def create_area(
    name: str,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Create a new area

    Args:
        name: Display name for the area (required)
        aliases: Optional list of aliases for the area
        picture: Optional path to area picture

    Returns:
        Created area dictionary with area_id and configuration

    Examples:
        # Create area with just name
        area = await create_area("Living Room")

        # Create area with aliases
        area = await create_area("Living Room", aliases=["lounge", "salon"])

        # Create area with picture
        area = await create_area("Living Room", picture="/config/www/living_room.jpg")

    Note:
        Area IDs are automatically generated by Home Assistant.
        Duplicate names are allowed but may cause confusion.
    """
    client = await get_client()

    payload: dict[str, Any] = {"name": name}
    if aliases:
        payload["aliases"] = aliases
    if picture:
        payload["picture"] = picture

    response = await client.post(
        f"{HA_URL}/api/config/area_registry/create",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def update_area(
    area_id: str,
    name: str | None = None,
    aliases: list[str] | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing area

    Args:
        area_id: The area ID to update
        name: Optional new name for the area
        aliases: Optional new list of aliases (replaces existing)
        picture: Optional new picture path

    Returns:
        Updated area dictionary

    Examples:
        # Update area name
        area = await update_area("living_room", name="Family Room")

        # Update aliases
        area = await update_area("living_room", aliases=["lounge", "salon"])

        # Update multiple fields
        area = await update_area("living_room", name="Family Room", aliases=["lounge"])

    Note:
        Only provided fields will be updated. Fields not provided remain unchanged.
        If aliases is provided, it replaces all existing aliases.
    """
    client = await get_client()

    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if aliases is not None:
        payload["aliases"] = aliases
    if picture is not None:
        payload["picture"] = picture

    if not payload:
        return {"error": "At least one field (name, aliases, picture) must be provided"}

    response = await client.post(
        f"{HA_URL}/api/config/area_registry/{area_id}",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def delete_area(area_id: str) -> dict[str, Any]:
    """
    Delete an area

    Args:
        area_id: The area ID to delete

    Returns:
        Response from the delete operation

    Note:
        ⚠️ This permanently deletes the area. There is no undo.
        Entities associated with this area will have their area_id removed.
        Make sure to check for entities before deleting, or use get_area_entities first.
    """
    client = await get_client()
    response = await client.delete(
        f"{HA_URL}/api/config/area_registry/{area_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return {"status": "deleted", "area_id": area_id}


@handle_api_errors
async def get_area_summary() -> dict[str, Any]:
    """
    Get summary of all areas with device/entity distribution

    Returns:
        Dictionary containing:
        - total_areas: Total number of areas
        - areas: Dictionary mapping area_id to area summary with:
            - name: Area name
            - entity_count: Number of entities in the area
            - domain_counts: Dictionary of domain counts (e.g., {"light": 3, "switch": 2})

    Example response:
        {
            "total_areas": 5,
            "areas": {
                "living_room": {
                    "name": "Living Room",
                    "entity_count": 10,
                    "domain_counts": {"light": 3, "switch": 2, "sensor": 5}
                }
            }
        }

    Best Practices:
        - Use this to understand entity distribution across areas
        - Identify areas with no entities
        - Analyze domain distribution by area
    """
    areas = await get_areas()
    all_entities = await get_entities(lean=True)

    summary: dict[str, Any] = {
        "total_areas": len(areas),
        "areas": {},
    }

    for area in areas:
        area_id = area.get("area_id")
        area_entities = [
            e for e in all_entities if e.get("attributes", {}).get("area_id") == area_id
        ]

        # Group entities by domain
        domain_counts: dict[str, int] = {}
        for entity in area_entities:
            entity_id = entity.get("entity_id", "")
            if "." in entity_id:
                domain = entity_id.split(".")[0]
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        summary["areas"][area_id] = {
            "name": area.get("name"),
            "entity_count": len(area_entities),
            "domain_counts": domain_counts,
        }

    return summary


@handle_api_errors
async def get_devices(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of all devices, optionally filtered by integration domain

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
    devices = response.json()

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
    Get detailed device information

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
    return response.json()


@handle_api_errors
async def get_device_entities(device_id: str) -> list[dict[str, Any]]:
    """
    Get all entities belonging to a specific device

    Args:
        device_id: The device ID to get entities for

    Returns:
        List of entity dictionaries belonging to the device

    Note:
        Entities are retrieved from the device's entity list.
        Returns empty list if device has no entities or device doesn't exist.
    """
    device = await get_device_details(device_id)

    entity_ids = device.get("entities", [])
    entities = []
    for entity_id in entity_ids:
        entity = await get_entity_state(entity_id, lean=True)
        entities.append(entity)

    return entities


@handle_api_errors
async def get_device_statistics() -> dict[str, Any]:
    """
    Get statistics about devices (counts by manufacturer, model, etc.)

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


@handle_api_errors
async def get_scenes() -> list[dict[str, Any]]:
    """
    Get list of all scenes

    Returns:
        List of scene dictionaries containing:
        - entity_id: The scene entity ID (e.g., 'scene.living_room_dim')
        - state: Current state of the scene
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene

    Example response:
        [
            {
                "entity_id": "scene.living_room_dim",
                "state": "scening",
                "friendly_name": "Living Room Dim",
                "entity_id_list": ["light.living_room", "light.kitchen"]
            }
        ]

    Note:
        Scenes capture the state of multiple entities at a point in time.
        Useful for creating lighting presets and room configurations.
    """
    scene_entities = await get_entities(domain="scene")

    scenes = []
    for entity in scene_entities:
        scene_info = {
            "entity_id": entity.get("entity_id"),
            "state": entity.get("state"),
        }

        # Add attributes if available
        attributes = entity.get("attributes", {})
        if "friendly_name" in attributes:
            scene_info["friendly_name"] = attributes["friendly_name"]
        if "entity_id" in attributes:
            scene_info["entity_id_list"] = attributes["entity_id"]
        if "snapshot" in attributes:
            scene_info["snapshot"] = attributes["snapshot"]

        scenes.append(scene_info)

    return scenes


@handle_api_errors
async def get_scene_config(scene_id: str) -> dict[str, Any]:
    """
    Get scene configuration (what entities/values it saves)

    Args:
        scene_id: The scene ID to get (with or without 'scene.' prefix)

    Returns:
        Scene configuration dictionary with:
        - entity_id: The scene entity ID
        - friendly_name: Display name of the scene
        - entity_id_list: List of entity IDs included in the scene
        - snapshot: Snapshot of entity states when scene was created

    Note:
        Scene configuration shows what entities are included in the scene
        and what states they were in when the scene was created.
    """
    entity_id = f"scene.{scene_id}" if not scene_id.startswith("scene.") else scene_id

    entity = await get_entity_state(entity_id, lean=False)

    # Extract scene data
    attributes = entity.get("attributes", {})
    scene_config = {
        "entity_id": entity.get("entity_id"),
        "friendly_name": attributes.get("friendly_name"),
        "entity_id_list": attributes.get("entity_id", []),
        "snapshot": attributes.get("snapshot", []),
    }

    return scene_config


@handle_api_errors
async def create_scene(
    name: str,
    entity_ids: list[str],
    states: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new scene

    Args:
        name: Display name for the scene
        entity_ids: List of entity IDs to include in the scene
        states: Optional dictionary of entity states to capture (if None, captures current states)

    Returns:
        Response from the create operation, or error message if creation fails

    Note:
        ⚠️ Scene creation via API may not be available in all Home Assistant versions.
        The create service is deprecated. If it fails, a helpful YAML configuration example
        is returned to guide manual scene creation.

    Examples:
        # Create scene capturing current states
        scene = await create_scene("Living Room Dim", ["light.living_room", "light.kitchen"])

        # Create scene with specific states
        scene = await create_scene(
            "Living Room Dim",
            ["light.living_room", "light.kitchen"],
            {"light.living_room": {"state": "on", "brightness": 128}}
        )
    """
    data: dict[str, Any] = {
        "name": name,
        "entities": entity_ids,
    }

    if states:
        data["states"] = states

    try:
        return await call_service("scene", "create", data)
    except Exception as e:
        # If create service doesn't work, provide helpful message
        example_config = f"\nscene:\n  - name: {name}\n    entities:"

        for eid in entity_ids:
            if states and eid in states:
                example_config += f"\n      {eid}: {json.dumps(states[eid])}"
            else:
                example_config += f"\n      {eid}:"
        return {
            "error": "Scene creation via API is not available",
            "note": "Scenes should be created in configuration.yaml or via UI",
            "example_config": example_config,
            "exception": str(e),
        }


@handle_api_errors
async def activate_scene(scene_id: str) -> dict[str, Any]:
    """
    Activate/restore a scene

    Args:
        scene_id: The scene ID to activate (with or without 'scene.' prefix)

    Returns:
        Response from the activate operation

    Examples:
        # Activate scene
        result = await activate_scene("living_room_dim")
        result = await activate_scene("scene.living_room_dim")

    Note:
        Activating a scene restores all entities to their saved states.
        The scene entity_id can be provided with or without the 'scene.' prefix.
    """
    entity_id = f"scene.{scene_id}" if not scene_id.startswith("scene.") else scene_id

    return await call_service("scene", "turn_on", {"entity_id": entity_id})


@handle_api_errors
async def reload_scenes() -> dict[str, Any]:
    """
    Reload scenes from configuration

    Returns:
        Response from the reload operation

    Note:
        Reloading scenes reloads all scene configurations from YAML files.
        This is useful after modifying scene configuration files.
    """
    return await call_service("scene", "reload", {})


@handle_api_errors
async def diagnose_entity(entity_id: str) -> dict[str, Any]:
    """
    Comprehensive entity diagnostics

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
    for integration in integrations:
        integration_state = integration.get("state")
        if integration_state != "loaded":
            diagnosis["issues"].append(f"Integration {domain} is in state: {integration_state}")
            diagnosis["recommendations"].append(
                f"Check integration {domain} configuration and reload if needed"
            )

    # Get recent history to check for errors
    try:
        history = await get_entity_history(entity_id, hours=24)
        if isinstance(history, list):
            # Check for error states in recent history
            error_states = [
                s for s in history if s.get("state", "").lower() in ["error", "unavailable"]
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
async def find_entity_dependencies(entity_id: str) -> dict[str, Any]:
    """
    Find what depends on this entity (automations, scripts, etc.)

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
    for script in scripts:
        script_id = script.get("entity_id")
        if not script_id:
            continue
        try:
            script_id_clean = (
                script_id.replace("script.", "") if "script." in script_id else script_id
            )
            config = await get_script_config(script_id_clean)
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
async def find_automation_conflicts() -> dict[str, Any]:
    """
    Detect conflicting automations (opposing actions, redundant triggers, etc.)

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
        if "turn_on" in services and "turn_off" in services:
            conflicting_automations = [
                a["automation"] for a in actions if a["service"] in ["turn_on", "turn_off"]
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
async def find_integration_errors(domain: str | None = None) -> dict[str, Any]:
    """
    Get errors specific to integrations

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

    integration_errors: dict[str, list[str]] = {}
    log_text = error_log.get("log_text", "")

    # Parse log for integration-specific errors
    lines = log_text.split("\n")

    for line in lines:
        if "ERROR" in line.upper() or "Exception" in line:
            # Extract integration name from [integration] pattern
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


@handle_api_errors
async def get_integrations(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of all configuration entries (integrations)

    Args:
        domain: Optional domain to filter integrations by (e.g., 'mqtt', 'zwave')

    Returns:
        List of integration entries with their status and configuration

    Example response:
        [
            {
                "entry_id": "abc123",
                "domain": "mqtt",
                "title": "MQTT",
                "source": "user",
                "state": "loaded",
                "supports_options": true,
                "pref_disable_new_entities": false,
                "pref_disable_polling": false
            }
        ]
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/config_entries/entry",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    entries = response.json()

    # Filter by domain if specified
    if domain:
        entries = [e for e in entries if e.get("domain") == domain]

    return entries


@handle_api_errors
async def get_integration_config(entry_id: str) -> dict[str, Any]:
    """
    Get detailed configuration for a specific integration entry

    Args:
        entry_id: The entry ID of the integration to get

    Returns:
        Detailed configuration dictionary for the integration entry

    Example response:
        {
            "entry_id": "abc123",
            "domain": "mqtt",
            "title": "MQTT",
            "source": "user",
            "state": "loaded",
            "options": {...},
            "pref_disable_new_entities": false,
            "pref_disable_polling": false
        }
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/config_entries/entry/{entry_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def reload_integration(entry_id: str) -> dict[str, Any]:
    """
    Reload a specific integration

    Args:
        entry_id: The entry ID of the integration to reload

    Returns:
        Response from the reload service call

    Note:
        Reloading an integration may cause temporary unavailability of its entities.
        Use with caution.
    """
    return await call_service("config", "reload_entry", {"entry_id": entry_id})


@handle_api_errors
async def get_hass_error_log() -> dict[str, Any]:
    """
    Get the Home Assistant error log for troubleshooting

    Returns:
        A dictionary containing:
        - log_text: The full error log text
        - error_count: Number of ERROR entries found
        - warning_count: Number of WARNING entries found
        - integration_mentions: Map of integration names to mention counts
        - error: Error message if retrieval failed
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
    Get a comprehensive overview of the entire Home Assistant system

    Returns:
        A dictionary containing:
        - total_entities: Total count of all entities
        - domains: Dictionary of domains with their entity counts and state distributions
        - domain_samples: Representative sample entities for each domain (2-3 per domain)
        - domain_attributes: Common attributes for each domain
        - area_distribution: Entities grouped by area (if available)
    """
    try:
        # Get ALL entities with minimal fields for efficiency
        # We retrieve all entities since API calls don't consume tokens, only responses do
        client = await get_client()
        response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
        response.raise_for_status()
        all_entities_raw = response.json()

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
        overview = {
            "total_entities": len(all_entities),
            "domains": {},
            "domain_samples": {},
            "domain_attributes": {},
            "area_distribution": {},
        }

        # Group entities by domain
        domain_entities = {}
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
            state_distribution = {}
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
            attribute_counts = {}
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
    Get system health information from Home Assistant

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
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/system_health", headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_core_config() -> dict[str, Any]:
    """
    Get core configuration from Home Assistant

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
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/config", headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_blueprints(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of available blueprints

    Args:
        domain: Optional domain to filter blueprints by (e.g., 'automation')

    Returns:
        List of blueprint dictionaries containing:
        - path: Blueprint path
        - domain: Blueprint domain
        - name: Blueprint name
        - metadata: Blueprint metadata

    Example response:
        [
            {
                "path": "blueprint_path",
                "domain": "automation",
                "name": "Blueprint Name",
                "metadata": {...}
            }
        ]

    Note:
        Blueprints are reusable automation templates.
        If domain is provided, returns blueprints for that domain only.
    """
    client = await get_client()

    url = f"{HA_URL}/api/blueprint/domain/{domain}" if domain else f"{HA_URL}/api/blueprint/list"

    response = await client.get(url, headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_blueprint_definition(blueprint_id: str, domain: str | None = None) -> dict[str, Any]:
    """
    Get blueprint definition and metadata

    Args:
        blueprint_id: The blueprint ID to get (may include domain and path)
        domain: Optional domain for the blueprint (e.g., 'automation')

    Returns:
        Blueprint definition dictionary with:
        - path: Blueprint path
        - domain: Blueprint domain
        - name: Blueprint name
        - metadata: Blueprint metadata including inputs, description
        - definition: Blueprint YAML definition

    Example response:
        {
            "path": "blueprint_path",
            "domain": "automation",
            "name": "Blueprint Name",
            "metadata": {
                "input": {...},
                "description": "..."
            },
            "definition": "..."
        }

    Note:
        Blueprint ID typically includes domain and path.
        If domain is not provided, attempts to extract it from blueprint_id.
    """
    client = await get_client()

    # Blueprint ID typically includes domain and path
    if domain:
        url = f"{HA_URL}/api/blueprint/metadata/{domain}/{blueprint_id}"
    else:
        # Try to extract domain from blueprint_id
        parts = blueprint_id.split("/")
        if len(parts) >= 2:
            domain = parts[0]
            path = "/".join(parts[1:])
            url = f"{HA_URL}/api/blueprint/metadata/{domain}/{path}"
        else:
            return {
                "error": "Cannot determine domain for blueprint. Please provide domain parameter."
            }

    response = await client.get(url, headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def import_blueprint_from_url(url: str) -> dict[str, Any]:
    """
    Import blueprint from URL

    Args:
        url: The URL to import the blueprint from

    Returns:
        Response dictionary containing imported blueprint information

    Example response:
        {
            "status": "imported",
            "blueprint": {...}
        }

    Note:
        This imports a blueprint from a community URL or external source.
        The URL is URL-encoded when making the API request.
    """
    client = await get_client()

    # URL encode the blueprint URL
    encoded_url = urllib.parse.quote(url, safe="")

    response = await client.get(
        f"{HA_URL}/api/blueprint/import/{encoded_url}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def create_automation_from_blueprint(
    blueprint_id: str, inputs: dict[str, Any], domain: str | None = None
) -> dict[str, Any]:
    """
    Create automation from blueprint with specified inputs

    Args:
        blueprint_id: The blueprint ID to use (may include domain and path)
        inputs: Dictionary of input values for the blueprint
        domain: Optional domain for the blueprint (e.g., 'automation')

    Returns:
        Response from the automation creation operation

    Example response:
        {
            "automation_id": "automation_12345",
            "status": "created"
        }

    Note:
        This creates a new automation using a blueprint as a template.
        The inputs dictionary must match the blueprint's input schema.
        An automation ID will be generated if not provided in the inputs.
    """
    # Get blueprint definition first
    blueprint = await get_blueprint_definition(blueprint_id, domain)

    # Check for errors
    if isinstance(blueprint, dict) and "error" in blueprint:
        return blueprint

    # Construct automation config from blueprint
    # Extract domain from blueprint if not provided
    if not domain:
        domain = blueprint.get("domain", "automation")

    # Construct automation config with blueprint reference
    automation_config: dict[str, Any] = {
        "use_blueprint": {
            "path": blueprint.get("path", blueprint_id),
            "input": inputs,
        }
    }

    # Generate automation_id if not provided in inputs
    automation_id = inputs.get("automation_id")
    if not automation_id:
        automation_id = f"automation_{uuid.uuid4().hex[:8]}"
        automation_config["id"] = automation_id

    # Use the create_automation function
    return await create_automation(automation_config)


@handle_api_errors
async def get_zones() -> list[dict[str, Any]]:
    """
    Get list of all zones (GPS coordinates)

    Returns:
        List of zone dictionaries containing:
        - id: Unique identifier for the zone
        - name: Display name of the zone
        - latitude: Latitude coordinate (-90 to 90)
        - longitude: Longitude coordinate (-180 to 180)
        - radius: Zone radius in meters
        - icon: Zone icon (if available)
        - passive: Whether the zone is passive

    Example response:
        [
            {
                "id": "home",
                "name": "Home",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius": 100,
                "icon": "mdi:home",
                "passive": false
            }
        ]

    Note:
        Zones are geographic areas defined by GPS coordinates.
        Used for location-based automations and device tracking.
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/config/zone_registry", headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def create_zone(
    name: str,
    latitude: float,
    longitude: float,
    radius: float,
    icon: str | None = None,
    passive: bool = False,
) -> dict[str, Any]:
    """
    Create a new zone

    Args:
        name: Display name for the zone (required)
        latitude: Latitude coordinate (-90 to 90) (required)
        longitude: Longitude coordinate (-180 to 180) (required)
        radius: Zone radius in meters (required, must be positive)
        icon: Optional zone icon (e.g., 'mdi:home')
        passive: Whether the zone is passive (default: False)

    Returns:
        Created zone dictionary with zone_id and configuration

    Examples:
        # Create a home zone
        zone = await create_zone("Home", 37.7749, -122.4194, 100, "mdi:home")

        # Create a work zone
        zone = await create_zone("Work", 37.7849, -122.4094, 200)

        # Create a passive zone
        zone = await create_zone("School", 37.7949, -122.3994, 150, passive=True)

    Note:
        Zone IDs are automatically generated by Home Assistant.
        GPS coordinates are validated to be within valid ranges.
        Radius must be positive.

    Error Handling:
        - Validates latitude is between -90 and 90
        - Validates longitude is between -180 and 180
        - Validates radius is positive
        - Handles duplicate zone names
    """
    # Validate GPS coordinates
    if not -90 <= latitude <= 90:
        return {"error": f"Latitude must be between -90 and 90, got: {latitude}"}

    if not -180 <= longitude <= 180:
        return {"error": f"Longitude must be between -180 and 180, got: {longitude}"}

    if radius <= 0:
        return {"error": f"Radius must be positive, got: {radius}"}

    client = await get_client()

    payload: dict[str, Any] = {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "passive": passive,
    }

    if icon:
        payload["icon"] = icon

    response = await client.post(
        f"{HA_URL}/api/config/zone_registry", headers=get_ha_headers(), json=payload
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def update_zone(
    zone_id: str,
    name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius: float | None = None,
    icon: str | None = None,
) -> dict[str, Any]:
    """
    Update an existing zone

    Args:
        zone_id: The zone ID to update
        name: Optional new name for the zone
        latitude: Optional new latitude coordinate (-90 to 90)
        longitude: Optional new longitude coordinate (-180 to 180)
        radius: Optional new radius in meters (must be positive)
        icon: Optional new icon

    Returns:
        Updated zone dictionary

    Examples:
        # Update zone name
        zone = await update_zone("home", name="My Home")

        # Update zone location
        zone = await update_zone("work", latitude=37.7849, longitude=-122.4094)

        # Update zone radius
        zone = await update_zone("home", radius=150)

        # Update multiple fields
        zone = await update_zone("work", name="Office", radius=200, icon="mdi:office")

    Note:
        Only provided fields will be updated. Fields not provided remain unchanged.
        GPS coordinates and radius are validated if provided.

    Error Handling:
        - Validates latitude is between -90 and 90 (if provided)
        - Validates longitude is between -180 and 180 (if provided)
        - Validates radius is positive (if provided)
    """
    # Validate GPS coordinates if provided
    if latitude is not None and not -90 <= latitude <= 90:
        return {"error": f"Latitude must be between -90 and 90, got: {latitude}"}

    if longitude is not None and not -180 <= longitude <= 180:
        return {"error": f"Longitude must be between -180 and 180, got: {longitude}"}

    if radius is not None and radius <= 0:
        return {"error": f"Radius must be positive, got: {radius}"}

    client = await get_client()

    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude
    if radius is not None:
        payload["radius"] = radius
    if icon is not None:
        payload["icon"] = icon

    if not payload:
        return {
            "error": "At least one field (name, latitude, longitude, radius, icon) must be provided"
        }

    response = await client.post(
        f"{HA_URL}/api/config/zone_registry/{zone_id}",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def delete_zone(zone_id: str) -> dict[str, Any]:
    """
    Delete a zone

    Args:
        zone_id: The zone ID to delete

    Returns:
        Response from the delete operation

    Examples:
        zone_id="work" - delete zone with ID work

    Note:
        ⚠️ This permanently deletes the zone. There is no undo.
        System zones (like 'home') may not be deletable.
        Make sure no automations or device tracking depend on this zone.

    Best Practices:
        - Check for dependencies before deleting
        - Verify zone_id is correct before deletion
        - Consider updating zone instead of deleting if possible
    """
    client = await get_client()
    response = await client.delete(
        f"{HA_URL}/api/config/zone_registry/{zone_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return {"status": "deleted", "zone_id": zone_id}


@handle_api_errors
async def get_logbook_entries(
    timestamp: str | None = None,
    entity_id: str | None = None,
    hours: int = 24,
) -> list[dict[str, Any]]:
    """
    Get logbook entries

    Args:
        timestamp: Optional timestamp to start from (ISO format, e.g., "2025-01-01T00:00:00Z")
                   If not provided, calculated from hours parameter
        entity_id: Optional entity ID to filter logbook entries by
        hours: Number of hours of history to retrieve (default: 24, only used if timestamp is not provided)

    Returns:
        List of logbook entry dictionaries containing:
        - when: Timestamp of the event
        - name: Display name of the entity
        - entity_id: The entity ID
        - state: State change value
        - domain: Entity domain
        - message: Description of what happened
        - icon: Icon associated with the event (if available)

    Example response:
        [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
                "icon": null
            }
        ]

    Note:
        The logbook records all state changes and events in Home Assistant.
        Useful for debugging and auditing system behavior.
        If timestamp is provided, hours parameter is ignored.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use entity_id filter to focus on specific entities
        - Use timestamp for precise time ranges
    """
    # Calculate timestamp if not provided
    if not timestamp:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)
        timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    # Ensure timestamp doesn't have timezone info for API format
    elif timestamp.endswith("Z"):
        timestamp = timestamp[:-1]

    client = await get_client()

    # Build URL and params
    url = f"{HA_URL}/api/logbook/{timestamp}"
    params: dict[str, Any] = {}
    if entity_id:
        params["entity"] = entity_id

    response = await client.get(url, headers=get_ha_headers(), params=params)
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_entity_logbook_entries(entity_id: str, hours: int = 24) -> list[dict[str, Any]]:
    """
    Get logbook entries for a specific entity

    Args:
        entity_id: The entity ID to get logbook entries for
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        List of logbook entry dictionaries for the specified entity

    Examples:
        entity_id="light.living_room", hours=24 - get last 24 hours of logbook for light
        entity_id="sensor.temperature", hours=168 - get last 7 days of logbook for sensor

    Note:
        This is a convenience wrapper around get_logbook_entries with entity_id filter.
        Returns only logbook entries for the specified entity.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use this to debug specific entity behavior
        - Check logbook to understand entity state changes over time
    """
    return await get_logbook_entries(entity_id=entity_id, hours=hours)


@handle_api_errors
async def search_logbook_entries(query: str, hours: int = 24) -> list[dict[str, Any]]:
    """
    Search logbook entries by query string

    Args:
        query: Search query to match against entity_id, name, or message
        hours: Number of hours of history to search (default: 24)

    Returns:
        List of logbook entry dictionaries matching the query

    Examples:
        query="error" - find logbook entries containing "error"
        query="sensor" - find logbook entries related to sensors
        query="light.living_room" - find entries for specific entity

    Note:
        This searches through logbook entries using case-insensitive matching.
        Searches in entity_id, name, and message fields.
        Returns entries that contain the query string in any of these fields.

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use specific queries to find relevant entries
        - Search for error messages, entity IDs, or specific events
    """
    # Get all logbook entries
    entries = await get_logbook_entries(hours=hours)

    # Filter entries matching query
    query_lower = query.lower()
    matching_entries = []

    for entry in entries:
        # Search in entity_id, name, message, etc.
        entry_entity_id = entry.get("entity_id", "").lower()
        entry_name = entry.get("name", "").lower()
        entry_message = entry.get("message", "").lower()

        if (
            query_lower in entry_entity_id
            or query_lower in entry_name
            or query_lower in entry_message
        ):
            matching_entries.append(entry)

    return matching_entries


@handle_api_errors
async def get_entity_statistics(entity_id: str, period_days: int = 7) -> dict[str, Any]:
    """
    Get statistics for an entity (min, max, mean, median)

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

    Example response:
        {
            "entity_id": "sensor.temperature",
            "period_days": 7,
            "data_points": 1680,
            "statistics": {
                "min": 18.5,
                "max": 24.3,
                "mean": 21.4,
                "median": 21.2
            }
        }

    Note:
        This calculates statistics from entity history data.
        Only numeric entities can provide meaningful statistics.
        Returns empty statistics if entity is not numeric or has no data.

    Best Practices:
        - Use for sensors with numeric values (temperature, humidity, etc.)
        - Keep period_days reasonable (7-30) for performance
        - Check for empty statistics if entity is not numeric
    """
    # Get history for the period
    history = await get_entity_history(entity_id, hours=period_days * 24)

    # Check for errors
    if isinstance(history, dict) and "error" in history:
        return {
            "entity_id": entity_id,
            "period_days": period_days,
            "error": history["error"],
            "statistics": {},
        }

    # Flatten history list (history is a list of lists)
    states = []
    if isinstance(history, list):
        for state_list in history:
            if isinstance(state_list, list):
                states.extend(state_list)

    if not states:
        return {
            "entity_id": entity_id,
            "period_days": period_days,
            "note": "No data available for the specified period",
            "statistics": {},
        }

    # Extract numeric values
    numeric_values = []
    for state in states:
        state_value = state.get("state")
        try:
            numeric_value = float(state_value)
            numeric_values.append(numeric_value)
        except (ValueError, TypeError):
            continue

    if not numeric_values:
        return {
            "entity_id": entity_id,
            "period_days": period_days,
            "note": "Entity state is not numeric, cannot calculate statistics",
            "statistics": {},
        }

    # Calculate statistics
    sorted_values = sorted(numeric_values)
    n = len(numeric_values)
    median = (
        sorted_values[n // 2]
        if n % 2 == 1
        else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    )

    stats = {
        "entity_id": entity_id,
        "period_days": period_days,
        "data_points": len(numeric_values),
        "statistics": {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": sum(numeric_values) / len(numeric_values),
            "median": median,
        },
    }

    return stats


@handle_api_errors
async def get_domain_statistics(domain: str, period_days: int = 7) -> dict[str, Any]:
    """
    Get aggregate statistics for all entities in a domain

    Args:
        domain: The domain to get statistics for (e.g., 'sensor', 'light')
        period_days: Number of days to analyze (default: 7)

    Returns:
        Dictionary containing:
        - domain: The domain analyzed
        - period_days: Number of days analyzed
        - total_entities: Total number of entities in the domain
        - entity_statistics: Dictionary mapping entity_id to statistics

    Example response:
        {
            "domain": "sensor",
            "period_days": 7,
            "total_entities": 25,
            "entity_statistics": {
                "sensor.temperature": {
                    "min": 18.5,
                    "max": 24.3,
                    "mean": 21.4,
                    "median": 21.2
                }
            }
        }

    Note:
        This aggregates statistics for entities in a domain.
        Limited to first 10 entities for performance.
        Only numeric entities are included in entity_statistics.

    Best Practices:
        - Use for domains with numeric entities (sensor, energy, etc.)
        - Keep period_days reasonable (7-30) for performance
        - Consider using get_entity_statistics for individual entities
    """
    # Get all entities in domain
    entities = await get_entities(domain=domain, lean=True)

    stats: dict[str, Any] = {
        "domain": domain,
        "period_days": period_days,
        "total_entities": len(entities),
        "entity_statistics": {},
    }

    # Get statistics for each entity (limited to first 10 for performance)
    for entity in entities[:10]:
        entity_id = entity.get("entity_id")
        if not entity_id:
            continue
        try:
            entity_stats = await get_entity_statistics(entity_id, period_days)
            # Only include entities with valid statistics
            if entity_stats.get("statistics"):
                stats["entity_statistics"][entity_id] = entity_stats.get("statistics", {})
        except Exception:  # nosec B112
            continue

    return stats


@handle_api_errors
async def analyze_usage_patterns(entity_id: str, days: int = 30) -> dict[str, Any]:
    """
    Analyze usage patterns (when device is used most)

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

    Example response:
        {
            "entity_id": "light.living_room",
            "period_days": 30,
            "total_events": 150,
            "hourly_distribution": {18: 30, 19: 25, 20: 20, ...},
            "daily_distribution": {"Monday": 25, "Tuesday": 22, ...},
            "peak_hour": 18,
            "peak_day": "Monday"
        }

    Note:
        This analyzes logbook entries to find usage patterns.
        Useful for understanding when devices are used most.
        Helps optimize automations based on actual usage.

    Best Practices:
        - Use for devices with frequent state changes (lights, switches, etc.)
        - Keep days reasonable (7-30) for performance
        - Use results to optimize automation schedules
    """
    # Get logbook entries
    logbook = await get_entity_logbook_entries(entity_id, hours=days * 24)

    # Analyze by hour of day
    hourly_usage: dict[int, int] = {}
    daily_usage: dict[str, int] = {}

    for entry in logbook:
        when = entry.get("when")
        if when:
            try:
                # Parse timestamp (handle both with and without timezone)
                if when.endswith("Z"):
                    dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(when)

                hour = dt.hour
                hourly_usage[hour] = hourly_usage.get(hour, 0) + 1

                # Analyze by day of week
                day = dt.strftime("%A")
                daily_usage[day] = daily_usage.get(day, 0) + 1
            except (ValueError, AttributeError):  # nosec B110
                continue

    # Find peak hour and day
    peak_hour = max(hourly_usage.items(), key=lambda x: x[1])[0] if hourly_usage else None
    peak_day = max(daily_usage.items(), key=lambda x: x[1])[0] if daily_usage else None

    return {
        "entity_id": entity_id,
        "period_days": days,
        "total_events": len(logbook),
        "hourly_distribution": hourly_usage,
        "daily_distribution": daily_usage,
        "peak_hour": peak_hour,
        "peak_day": peak_day,
    }


@handle_api_errors
async def get_calendars() -> list[dict[str, Any]]:
    """
    Get list of all calendar entities

    Returns:
        List of calendar dictionaries containing:
        - entity_id: The calendar entity ID
        - state: Current state of the calendar
        - friendly_name: Display name of the calendar
        - supported_features: Bitmask of supported features

    Example response:
        [
            {
                "entity_id": "calendar.google",
                "state": "idle",
                "friendly_name": "Google Calendar",
                "supported_features": 3
            }
        ]

    Note:
        Calendars are entities that support calendar functionality.
        Supported features indicate which operations are available
        (e.g., CREATE_EVENT, DELETE_EVENT).

    Best Practices:
        - Use this to discover available calendars
        - Check supported_features to see what operations are available
        - Use to find calendar entities before getting events
    """
    calendar_entities = await get_entities(domain="calendar", lean=True)

    calendars = []
    for entity in calendar_entities:
        calendars.append(
            {
                "entity_id": entity.get("entity_id"),
                "state": entity.get("state"),
                "friendly_name": entity.get("attributes", {}).get("friendly_name"),
                "supported_features": entity.get("attributes", {}).get("supported_features", 0),
            }
        )

    return calendars


@handle_api_errors
async def get_calendar_events(
    entity_id: str, start_date: str, end_date: str
) -> list[dict[str, Any]]:
    """
    Get calendar events for a date range

    Args:
        entity_id: The calendar entity ID (e.g., 'calendar.google')
        start_date: Start date/time in ISO 8601 format (e.g., '2025-01-01T00:00:00' or '2025-01-01')
        end_date: End date/time in ISO 8601 format (e.g., '2025-01-07T23:59:59' or '2025-01-07')

    Returns:
        List of calendar event dictionaries containing:
        - summary: Event title/summary
        - start: Start date/time
        - end: End date/time
        - description: Event description (if available)
        - location: Event location (if available)
        - uid: Unique event identifier

    Example response:
        [
            {
                "summary": "Meeting",
                "start": {"dateTime": "2025-01-01T10:00:00"},
                "end": {"dateTime": "2025-01-01T11:00:00"},
                "description": "Team meeting",
                "location": "Conference Room A",
                "uid": "event_12345"
            }
        ]

    Note:
        Date formats are automatically handled. If only a date is provided,
        time is added automatically (start: 00:00:00, end: 23:59:59).
        ISO 8601 format is expected for dates.

    Best Practices:
        - Use ISO 8601 format for dates (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        - Keep date ranges reasonable (e.g., 1-4 weeks)
        - Check calendar exists before getting events
    """
    client = await get_client()

    # Format dates (ISO 8601)
    # Ensure dates are properly formatted
    start_iso = start_date if "T" in start_date else f"{start_date}T00:00:00"
    end_iso = end_date if "T" in end_date else f"{end_date}T23:59:59"

    response = await client.get(
        f"{HA_URL}/api/calendars/{entity_id}",
        headers=get_ha_headers(),
        params={
            "start_date_time": start_iso,
            "end_date_time": end_iso,
        },
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def create_calendar_event(
    entity_id: str,
    summary: str,
    start: str,
    end: str,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a calendar event

    Args:
        entity_id: The calendar entity ID (e.g., 'calendar.google')
        summary: Event title/summary (required)
        start: Start date/time in ISO 8601 format (e.g., '2025-01-01T10:00:00' or '2025-01-01')
        end: End date/time in ISO 8601 format (e.g., '2025-01-01T11:00:00' or '2025-01-01')
        description: Optional event description

    Returns:
        Response dictionary containing created event information

    Examples:
        entity_id="calendar.google", summary="Meeting", start="2025-01-01T10:00:00", end="2025-01-01T11:00:00"
        entity_id="calendar.google", summary="All Day Event", start="2025-01-01", end="2025-01-01", description="All day event"

    Note:
        Date formats are automatically handled. If only a date is provided,
        time is added automatically (start: 00:00:00, end: 23:59:59).
        The calendar must support event creation (check supported_features).

    Best Practices:
        - Use ISO 8601 format for dates
        - Check calendar supported_features before creating events
        - Use description to provide additional event details
        - Verify event was created successfully
    """
    client = await get_client()

    # Format dates (ISO 8601)
    start_iso = start if "T" in start else f"{start}T00:00:00"
    end_iso = end if "T" in end else f"{end}T23:59:59"

    payload: dict[str, Any] = {
        "summary": summary,
        "dtstart": start_iso,
        "dtend": end_iso,
    }

    if description:
        payload["description"] = description

    response = await client.post(
        f"{HA_URL}/api/calendars/{entity_id}/events",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_notification_services() -> list[dict[str, Any]]:
    """
    Get list of available notification platforms

    Returns:
        List of notification service dictionaries containing:
        - service: The service name (e.g., 'notify.mobile_app_iphone')
        - name: Display name of the service
        - description: Service description (if available)
        - entity_id: Entity ID if available from fallback

    Example response:
        [
            {
                "service": "notify.mobile_app_iphone",
                "name": "mobile_app_iphone",
                "description": "Send notifications to iPhone"
            }
        ]

    Note:
        Notification services are platforms that can send notifications.
        Common platforms include mobile_app, telegram, email, etc.
        This function tries the services API first, then falls back to entity states.

    Best Practices:
        - Use this to discover available notification platforms
        - Check service names before sending notifications
        - Use to test which notification services are configured
    """
    client = await get_client()

    try:
        # Try to get services via services API
        response = await client.get(f"{HA_URL}/api/services", headers=get_ha_headers())
        response.raise_for_status()
        services = response.json()

        # Filter notify services
        notify_services = []
        for service in services.get("notify", []):
            notify_services.append(
                {
                    "service": service.get("service"),
                    "name": service.get("name"),
                    "description": service.get("description"),
                }
            )

        return notify_services
    except Exception:  # nosec B110
        # Fallback: try to get from entity states
        notify_entities = await get_entities(domain="notify", lean=True)
        return [{"entity_id": e.get("entity_id")} for e in notify_entities]


@handle_api_errors
async def send_notification(
    message: str,
    target: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Send a notification

    Args:
        message: The notification message (required)
        target: Optional target notification service/platform
                 Can be 'notify.service_name' or just 'service_name'
                 If not provided, uses persistent_notification
        data: Optional dictionary of additional notification data
              (e.g., title, data for platform-specific options)

    Returns:
        Response dictionary from the notification service

    Examples:
        message="Alert: Temperature too high" - send to default notification
        message="Alert", target="notify.mobile_app_iphone" - send to iPhone
        message="Alert", target="mobile_app_iphone", data={"title": "System Alert"} - send with title

    Note:
        If target is provided, it will be parsed to determine domain and service.
        If target is 'notify.service_name', domain is 'notify' and service is 'service_name'.
        If target is just 'service_name', domain is 'notify' and service is 'service_name'.
        Additional data can include platform-specific options like title, url, etc.

    Best Practices:
        - Use list_notification_services to discover available targets
        - Include a clear message describing what the notification is about
        - Use data parameter for platform-specific options (title, image, etc.)
        - Test notifications before using in production automations
    """
    # Determine notification service
    if target:
        # Use specific service
        service_parts = target.split(".")
        if len(service_parts) == 2:
            domain, service = service_parts
        else:
            domain = "notify"
            service = service_parts[0]
    else:
        # Use default notify service (persistent_notification)
        domain = "notify"
        service = "persistent_notification"

    # Prepare notification data
    notification_data: dict[str, Any] = {"message": message}
    if data:
        notification_data.update(data)

    return await call_service(domain, service, notification_data)


@handle_api_errors
async def test_notification_delivery(platform: str, message: str) -> dict[str, Any]:
    """
    Test notification delivery to a specific platform

    Args:
        platform: The notification platform/service name
                  Can be 'notify.service_name' or just 'service_name'
        message: The test message to send

    Returns:
        Response dictionary from the notification service

    Examples:
        platform="notify.mobile_app_iphone", message="Test notification"
        platform="mobile_app_iphone", message="Test notification"

    Note:
        This sends a test notification prefixed with "[TEST]".
        Useful for verifying notification delivery works before using in automations.
        The platform parameter follows the same format as send_notification target.

    Best Practices:
        - Use to verify notification services are working
        - Test each notification platform before using in production
        - Check notification delivery after configuration changes
    """
    test_message = f"[TEST] {message}"
    return await send_notification(test_message, target=platform)


@handle_api_errors
async def fire_event(event_type: str, event_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Fire a custom event

    Args:
        event_type: The event type name (e.g., 'custom_event', 'state_changed')
        event_data: Optional dictionary of event data/payload

    Returns:
        Response dictionary from the event fire API

    Examples:
        event_type="custom_event", event_data={"message": "Hello"}
        event_type="automation_triggered", event_data={"entity_id": "light.living_room"}

    Note:
        Events are used for communication between different parts of Home Assistant.
        Custom events can trigger automations that listen for specific event types.
        Event data is optional but commonly used to pass information to event handlers.

    Best Practices:
        - Use descriptive event type names (e.g., 'custom_event', 'my_app_ready')
        - Include relevant data in event_data for event handlers
        - Use events to trigger automations based on custom conditions
        - Document custom event types for team members
    """
    client = await get_client()

    payload = event_data or {}

    response = await client.post(
        f"{HA_URL}/api/events/{event_type}",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_event_types() -> list[str]:
    """
    List common event types used in Home Assistant

    Returns:
        List of common event type strings

    Example response:
        [
            "state_changed",
            "time_changed",
            "service_registered",
            "call_service",
            "homeassistant_start",
            "homeassistant_stop",
            "automation_triggered",
            "script_started",
            "scene_on"
        ]

    Note:
        Home Assistant API doesn't provide a comprehensive list of event types.
        This function returns common event types from documentation.
        Custom event types can be any string, but common ones are listed here.
        Events are documented in Home Assistant's event documentation.

    Best Practices:
        - Use this to discover common event types
        - Create custom event types for your own use cases
        - Check automations/logbook for other event types used in your setup
        - Use descriptive names for custom event types
    """
    # Note: Home Assistant API doesn't provide a list of event types
    # This returns common event types from documentation
    common_event_types = [
        "state_changed",
        "time_changed",
        "service_registered",
        "call_service",
        "homeassistant_start",
        "homeassistant_stop",
        "automation_triggered",
        "script_started",
        "scene_on",
        "custom_event",
    ]

    # Try to extract event types from logbook or automations if possible
    # This is a simplified implementation that returns common event types
    return common_event_types


@handle_api_errors
async def get_recent_events(entity_id: str | None = None, hours: int = 1) -> list[dict[str, Any]]:
    """
    Get recent events for an entity (via logbook)

    Args:
        entity_id: Optional entity ID to filter events for a specific entity
        hours: Number of hours of history to retrieve (default: 1)

    Returns:
        List of event dictionaries from logbook entries

    Examples:
        entity_id=None, hours=1 - get all recent events from last hour
        entity_id="light.living_room", hours=24 - get events for specific entity from last day

    Note:
        Events can be retrieved via logbook entries.
        This is a convenience function that uses get_logbook_entries.
        Useful for debugging and understanding what events occurred.

    Best Practices:
        - Keep hours reasonable (1-24) for token efficiency
        - Use entity_id to filter events for specific entities
        - Use to debug event-triggered automations
        - Use to understand event flow in your Home Assistant setup
    """
    # Events can be retrieved via logbook
    return await get_logbook_entries(entity_id=entity_id, hours=hours)


@handle_api_errors
async def get_tags() -> list[dict[str, Any]]:
    """
    Get list of all RFID/NFC tags

    Returns:
        List of tag dictionaries containing:
        - tag_id: The tag ID (unique identifier)
        - name: Display name of the tag
        - last_scanned: Last scan timestamp (if available)
        - device_id: Device ID associated with the tag (if available)

    Example response:
        [
            {
                "tag_id": "ABC123",
                "name": "Front Door Key",
                "last_scanned": "2025-01-01T10:00:00",
                "device_id": "device_123"
            }
        ]

    Note:
        Tags are RFID/NFC tags used for NFC-based automations.
        Tags can trigger automations when scanned.
        Each tag has a unique tag_id and optional name.

    Best Practices:
        - Use this to discover configured tags
        - Check tag IDs before creating new tags
        - Use to manage tags for NFC-based automations
    """
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/tag", headers=get_ha_headers())
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def create_tag(tag_id: str, name: str) -> dict[str, Any]:
    """
    Create a new tag

    Args:
        tag_id: The tag ID (unique identifier, e.g., 'ABC123')
        name: Display name for the tag (e.g., 'Front Door Key')

    Returns:
        Response dictionary containing created tag information

    Examples:
        tag_id="ABC123", name="Front Door Key"
        tag_id="XYZ789", name="Office Access Card"

    Note:
        Tag IDs must be unique.
        Tags are used to trigger automations when scanned.
        After creating a tag, you can create automations triggered by tag scans.

    Best Practices:
        - Use descriptive names for tags
        - Choose unique tag IDs
        - Use tag names to identify physical tags/cards
        - Create automations after creating tags
    """
    client = await get_client()

    payload = {"tag_id": tag_id, "name": name}

    response = await client.post(
        f"{HA_URL}/api/tag",
        headers=get_ha_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def delete_tag(tag_id: str) -> dict[str, Any]:
    """
    Delete a tag

    Args:
        tag_id: The tag ID to delete

    Returns:
        Response dictionary from the delete API

    Examples:
        tag_id="ABC123" - delete a specific tag

    Note:
        Deleting a tag removes it from Home Assistant.
        Automations that use this tag may stop working.
        Tag deletion is permanent and cannot be undone.

    Best Practices:
        - Check for automations using the tag before deleting
        - Use get_tag_automations to find dependent automations
        - Remove or update automations before deleting tags
        - Verify tag_id exists before deleting
    """
    client = await get_client()
    response = await client.delete(
        f"{HA_URL}/api/tag/{tag_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def get_tag_automations(tag_id: str) -> list[dict[str, Any]]:
    """
    Get automations triggered by a tag

    Args:
        tag_id: The tag ID to find automations for

    Returns:
        List of automation dictionaries containing:
        - automation_id: The automation entity ID
        - alias: Display name of the automation
        - enabled: Whether the automation is enabled

    Example response:
        [
            {
                "automation_id": "automation.front_door_unlock",
                "alias": "Front Door Unlock",
                "enabled": true
            }
        ]

    Note:
        This searches through all automations to find those with tag triggers.
        Tag triggers use platform "tag" with matching tag_id.
        Useful for understanding tag dependencies before deletion.

    Best Practices:
        - Use before deleting tags to check dependencies
        - Review automations that depend on the tag
        - Update or remove dependent automations if needed
        - Use to document tag usage in your setup
    """
    # Get all automations
    automations = await get_automations()

    tag_automations = []
    for automation in automations:
        automation_id = automation.get("entity_id")
        if not automation_id:
            continue
        try:
            automation_entity_id = automation_id.replace("automation.", "")
            config = await get_automation_config(automation_entity_id)

            # Check if automation has tag trigger
            triggers = config.get("trigger", [])
            if not isinstance(triggers, list):
                triggers = []

            for trigger in triggers:
                if (
                    isinstance(trigger, dict)
                    and trigger.get("platform") == "tag"
                    and trigger.get("tag_id") == tag_id
                ):
                    tag_automations.append(
                        {
                            "automation_id": automation_id,
                            "alias": automation.get("attributes", {}).get("friendly_name")
                            or config.get("alias"),
                            "enabled": automation.get("state") == "on",
                        }
                    )
                    break
        except Exception:  # nosec B112
            continue

    return tag_automations


@handle_api_errors
async def get_helpers(helper_type: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of input helpers (input_boolean, input_number, etc.)

    Args:
        helper_type: Optional helper type to filter by
                     (e.g., 'input_boolean', 'input_number', 'input_text', etc.)
                     If not provided, returns all helpers

    Returns:
        List of helper dictionaries containing:
        - entity_id: The helper entity ID
        - domain: The helper domain (e.g., 'input_boolean')
        - state: Current state of the helper
        - friendly_name: Display name of the helper
        - attributes: Helper attributes

    Example response:
        [
            {
                "entity_id": "input_boolean.work_from_home",
                "domain": "input_boolean",
                "state": "on",
                "friendly_name": "Work From Home",
                "attributes": {...}
            }
        ]

    Note:
        Helper types include:
        - input_boolean, input_number, input_text, input_select
        - input_datetime, input_button, counter, timer, schedule
        Helpers are virtual entities used for storing values and controlling automations.

    Best Practices:
        - Use helper_type to filter specific helper types
        - Use to discover configured helpers
        - Use to manage virtual entities for automations
        - Check helper types before updating values
    """
    helper_types = [
        "input_boolean",
        "input_number",
        "input_text",
        "input_select",
        "input_datetime",
        "input_button",
        "counter",
        "timer",
        "schedule",
    ]

    all_helpers = []

    if helper_type:
        # Filter by specific type
        if helper_type in helper_types:
            helpers = await get_entities(domain=helper_type, lean=True)
            all_helpers.extend(helpers)
    else:
        # Get all helpers
        for helper_domain in helper_types:
            helpers = await get_entities(domain=helper_domain, lean=True)
            all_helpers.extend(helpers)

    # Format helper information
    formatted_helpers = []
    for helper in all_helpers:
        entity_id = helper.get("entity_id")
        if not entity_id:
            continue
        domain = entity_id.split(".")[0]
        formatted_helpers.append(
            {
                "entity_id": entity_id,
                "domain": domain,
                "state": helper.get("state"),
                "friendly_name": helper.get("attributes", {}).get("friendly_name"),
                "attributes": helper.get("attributes", {}),
            }
        )

    return formatted_helpers


@handle_api_errors
async def get_helper_details(helper_id: str) -> dict[str, Any]:
    """
    Get helper state and configuration

    Args:
        helper_id: The helper entity ID or name
                   (e.g., 'input_boolean.work_from_home' or 'work_from_home')

    Returns:
        Dictionary containing helper state and configuration

    Examples:
        helper_id="input_boolean.work_from_home"
        helper_id="work_from_home" - will search for matching helper

    Note:
        If helper_id doesn't include domain, the function searches for matching helpers.
        Returns full entity state with all attributes.
        Useful for getting current value and configuration of helpers.

    Best Practices:
        - Use full entity_id (with domain) when possible
        - Check helper exists before updating
        - Use to inspect helper configuration and current value
    """
    # Ensure helper_id includes domain
    if (
        not helper_id.startswith("input_")
        and not helper_id.startswith("counter")
        and not helper_id.startswith("timer")
        and not helper_id.startswith("schedule")
    ):
        # Try to find the helper
        all_helpers = await get_helpers()
        matching = [
            h
            for h in all_helpers
            if h["entity_id"] == helper_id or h["entity_id"].endswith(f".{helper_id}")
        ]
        if matching:
            helper_id = matching[0]["entity_id"]
        else:
            return {"error": f"Helper {helper_id} not found"}

    return await get_entity_state(helper_id, lean=False)


@handle_api_errors
async def update_helper_value(helper_id: str, value: Any) -> dict[str, Any]:
    """
    Update helper value

    Args:
        helper_id: The helper entity ID (e.g., 'input_boolean.work_from_home')
        value: The value to set, depends on helper type:
               - input_boolean: True/False or "on"/"off"
               - input_number: Numeric value (float)
               - input_text: String value
               - input_select: Option string (must match available options)
               - counter: Integer value, or "+" to increment, "-" to decrement
               - timer: "start", "pause", or "cancel"
               - input_button: Any value (triggers press action)

    Returns:
        Response dictionary from the service call

    Examples:
        helper_id="input_boolean.work_from_home", value=True
        helper_id="input_number.temperature", value=22.5
        helper_id="input_text.name", value="John"
        helper_id="counter.steps", value="+"
        helper_id="timer.countdown", value="start"

    Note:
        Different helper types require different service calls:
        - input_boolean: turn_on/turn_off
        - input_number: set_value
        - input_text: set_value
        - input_select: select_option
        - counter: increment/decrement/set_value
        - timer: start/pause/cancel
        - input_button: press

    Best Practices:
        - Use appropriate value types for each helper type
        - Check helper type before updating
        - Verify value is valid for the helper type
        - Use counters with "+" or "-" for increment/decrement
    """
    # Extract domain from helper_id
    domain = helper_id.split(".")[0]

    # Determine service based on domain
    if domain == "input_boolean":
        # Convert value to boolean
        if isinstance(value, str):
            service = "turn_on" if value.lower() in ("on", "true", "1") else "turn_off"
        else:
            service = "turn_on" if value else "turn_off"
        return await call_service(domain, service, {"entity_id": helper_id})
    if domain == "input_number":
        return await call_service(
            domain, "set_value", {"entity_id": helper_id, "value": float(value)}
        )
    if domain == "input_text":
        return await call_service(
            domain, "set_value", {"entity_id": helper_id, "value": str(value)}
        )
    if domain == "input_select":
        return await call_service(
            domain, "select_option", {"entity_id": helper_id, "option": str(value)}
        )
    if domain == "counter":
        if isinstance(value, str) and value.startswith("+"):
            return await call_service(domain, "increment", {"entity_id": helper_id})
        if isinstance(value, str) and value.startswith("-"):
            return await call_service(domain, "decrement", {"entity_id": helper_id})
        return await call_service(
            domain, "set_value", {"entity_id": helper_id, "value": int(value)}
        )
    if domain == "timer":
        if value == "start":
            return await call_service(domain, "start", {"entity_id": helper_id})
        if value == "pause":
            return await call_service(domain, "pause", {"entity_id": helper_id})
        if value == "cancel":
            return await call_service(domain, "cancel", {"entity_id": helper_id})
        return {"error": f"Unknown timer action: {value}. Use 'start', 'pause', or 'cancel'"}
    if domain == "input_button":
        return await call_service(domain, "press", {"entity_id": helper_id})
    return {
        "error": f"Cannot update helper of type {domain}. Supported types: input_boolean, input_number, input_text, input_select, counter, timer, input_button"
    }


@handle_api_errors
async def get_webhooks() -> list[dict[str, Any]]:
    """
    List registered webhooks (might need to parse configuration)

    Returns:
        List of webhook information dictionaries containing:
        - note: Information about webhook configuration
        - common_webhook_id_pattern: Pattern for webhook IDs
        - usage: Usage instructions

    Example response:
        [
            {
                "note": "Webhooks are typically defined in configuration.yaml",
                "common_webhook_id_pattern": "webhook_id defined in automations/scripts",
                "usage": "Use test_webhook to test webhook endpoints"
            }
        ]

    Note:
        Webhooks are typically defined in configuration.yaml or through automations/scripts.
        They might not have entities, so they need to be parsed from configuration.
        In a real implementation, this might need to:
        - Parse configuration.yaml
        - Use a config API if available
        - Document webhooks from automations/scripts
        For now, this returns common webhook patterns and usage information.

    Best Practices:
        - Webhooks are typically created via configuration files
        - Use test_webhook to test webhook endpoints
        - Webhook IDs are defined in automations/scripts
        - Check configuration.yaml for webhook definitions
    """
    # Note: Webhooks are typically defined in configuration
    # They might not have entities, so we need to parse config or document them
    # For now, return common webhook patterns
    # In a real implementation, this might need to:
    # 1. Parse configuration.yaml
    # 2. Use a config API if available
    # 3. Document webhooks from automations/scripts

    return [
        {
            "note": "Webhooks are typically defined in configuration.yaml or automation/script triggers",
            "common_webhook_id_pattern": "webhook_id defined in automations/scripts",
            "usage": "Use test_webhook to test webhook endpoints",
            "webhook_url_format": "/api/webhook/{webhook_id}",
            "authentication": "Webhooks don't require authentication token",
        }
    ]


@handle_api_errors
async def test_webhook_endpoint(
    webhook_id: str,
    payload: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test webhook endpoint

    Args:
        webhook_id: The webhook ID to test
        payload: Optional payload to send with the webhook request

    Returns:
        Dictionary containing webhook response:
        - status: Response status ("success" or "error")
        - status_code: HTTP status code
        - response_text: Response text (limited to 500 characters)
        - response_json: Response JSON if available

    Examples:
        webhook_id="my_webhook", payload=None
        webhook_id="automation_trigger", payload={"entity_id": "light.living_room"}

    Note:
        Webhooks allow external systems to trigger Home Assistant actions via HTTP POST requests.
        Webhook URL format: /api/webhook/{webhook_id}
        Webhooks don't require authentication token.
        Webhooks return 200 on success, but might not return JSON.

    Best Practices:
        - Use to test webhook endpoints
        - Test with various payloads
        - Verify webhook triggers correct actions
        - Use to debug webhook configurations
    """
    client = await get_client()

    # Webhook URL format: /api/webhook/{webhook_id}
    webhook_url = f"{HA_URL}/api/webhook/{webhook_id}"

    # Webhooks don't require authentication token
    response = await client.post(webhook_url, json=payload or {})

    # Webhooks return 200 on success, but might not return JSON
    if response.status_code == 200:
        try:
            response_json = response.json()
            return {
                "status": "success",
                "status_code": response.status_code,
                "response_json": response_json,
            }
        except Exception:  # nosec B110
            return {
                "status": "success",
                "status_code": response.status_code,
                "response_text": response.text[:500],  # Limit response text
            }
    else:
        response_text = response.text[:500] if response.text else ""
        return {
            "error": "Webhook request failed",
            "status": "error",
            "status_code": response.status_code,
            "response_text": response_text,
        }


@handle_api_errors
async def get_backups() -> dict[str, Any]:
    """
    List available backups (if Supervisor API available)

    Returns:
        Dictionary containing:
        - available: Boolean indicating if Supervisor API is available
        - backups: List of backup dictionaries (if available)
        - error: Error message (if Supervisor API not available)

    Example response:
        {
            "available": True,
            "backups": [
                {
                    "slug": "20250101_120000",
                    "name": "Full Backup 2025-01-01",
                    "date": "2025-01-01T12:00:00",
                    "size": 1024000,
                    "type": "full"
                }
            ]
        }

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        If Supervisor API is not available (404), returns available: False.
        This feature requires Home Assistant OS installation.

    Best Practices:
        - Check available flag before attempting operations
        - Use to list existing backups before creating new ones
        - Use to verify backup creation succeeded
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    try:
        response = await client.get(
            f"{HA_URL}/api/hassio/backups",
            headers=get_ha_headers(),
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "available": True,
            "backups": data.get("backups", []),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def create_backup(
    name: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Create a backup (if Supervisor API available)

    Args:
        name: Backup name (e.g., 'Full Backup 2025-01-01')
        password: Optional password for encrypted backup
        full: If True, creates full backup; if False, creates partial backup

    Returns:
        Dictionary containing backup creation response:
        - available: Boolean indicating if Supervisor API is available
        - slug: Backup slug identifier (if successful)
        - error: Error message (if Supervisor API not available or creation failed)

    Examples:
        name="Full Backup 2025-01-01", password=None, full=True
        name="Partial Backup", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full backups include all data, partial backups allow selective restoration.
        Password-protected backups require password for restoration.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Use descriptive backup names with dates
        - Create full backups before major changes
        - Use partial backups for specific components
        - Store passwords securely for encrypted backups
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    endpoint = "new/full" if full else "new/partial"

    payload = {"name": name}
    if password:
        payload["password"] = password

    try:
        response = await client.post(
            f"{HA_URL}/api/hassio/backups/{endpoint}",
            headers=get_ha_headers(),
            json=payload,
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "available": True,
            "slug": data.get("slug"),
            "message": "Backup created successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def restore_backup(
    backup_slug: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Restore a backup (if Supervisor API available)

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')
        password: Optional password for encrypted backup
        full: If True, restores full backup; if False, restores partial backup

    Returns:
        Dictionary containing restore response:
        - available: Boolean indicating if Supervisor API is available
        - message: Restore status message
        - error: Error message (if Supervisor API not available or restore failed)

    Examples:
        backup_slug="20250101_120000", password=None, full=True
        backup_slug="backup_2025", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full restore restores entire system, partial restore allows selective restoration.
        Password-protected backups require password for restoration.
        Restoring will restart Home Assistant and may take several minutes.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup exists before restoring
        - Use full restore for complete system recovery
        - Use partial restore for specific components
        - Provide password for encrypted backups
        - Only available on Home Assistant OS installations
        - System will restart after restore
    """
    client = await get_client()

    endpoint = "restore/full" if full else "restore/partial"

    payload = {}
    if password:
        payload["password"] = password

    try:
        response = await client.post(
            f"{HA_URL}/api/hassio/backups/{backup_slug}/{endpoint}",
            headers=get_ha_headers(),
            json=payload,
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        return {
            "available": True,
            "message": "Backup restore initiated successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def delete_backup(backup_slug: str) -> dict[str, Any]:
    """
    Delete a backup (if Supervisor API available)

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')

    Returns:
        Dictionary containing delete response:
        - available: Boolean indicating if Supervisor API is available
        - message: Delete status message
        - error: Error message (if Supervisor API not available or delete failed)

    Examples:
        backup_slug="20250101_120000"

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Deleting a backup is permanent and cannot be undone.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup slug exists before deleting
        - Use with caution as deletion is permanent
        - Only delete backups you no longer need
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    try:
        response = await client.delete(
            f"{HA_URL}/api/hassio/backups/{backup_slug}",
            headers=get_ha_headers(),
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        return {
            "available": True,
            "message": "Backup deleted successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }
