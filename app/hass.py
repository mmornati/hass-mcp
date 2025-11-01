import functools
import inspect
import json
import logging
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast

import httpx

from app.config import HA_TOKEN, HA_URL, get_ha_headers

# Set up logging
logger = logging.getLogger(__name__)

# Define a generic type for our API function return values
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# HTTP client
_client: httpx.AsyncClient | None = None

# Default field sets for different verbosity levels
# Lean fields for standard requests (optimized for token efficiency)
DEFAULT_LEAN_FIELDS = ["entity_id", "state", "attr.friendly_name"]

# Common fields that are typically needed for entity operations
DEFAULT_STANDARD_FIELDS = ["entity_id", "state", "attributes", "last_updated"]

# Domain-specific important attributes to include in lean responses
DOMAIN_IMPORTANT_ATTRIBUTES = {
    "light": ["brightness", "color_temp", "rgb_color", "supported_color_modes"],
    "switch": ["device_class"],
    "binary_sensor": ["device_class"],
    "sensor": ["device_class", "unit_of_measurement", "state_class"],
    "climate": ["hvac_mode", "current_temperature", "temperature", "hvac_action"],
    "media_player": ["media_title", "media_artist", "source", "volume_level"],
    "cover": ["current_position", "current_tilt_position"],
    "fan": ["percentage", "preset_mode"],
    "camera": ["entity_picture"],
    "automation": ["last_triggered"],
    "scene": [],
    "script": ["last_triggered"],
}


def handle_api_errors(func: F) -> F:
    """
    Decorator to handle common error cases for Home Assistant API calls

    Args:
        func: The async function to decorate

    Returns:
        Wrapped function that handles errors
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Determine return type from function annotation
        return_type = inspect.signature(func).return_annotation
        is_dict_return = "Dict" in str(return_type)
        is_list_return = "List" in str(return_type)

        # Prepare error formatters based on return type
        def format_error(msg: str) -> Any:
            if is_dict_return:
                return {"error": msg}
            if is_list_return:
                return [{"error": msg}]
            return msg

        try:
            # Check if token is available
            if not HA_TOKEN:
                return format_error(
                    "No Home Assistant token provided. Please set HA_TOKEN in .env file."
                )

            # Call the original function
            return await func(*args, **kwargs)
        except httpx.ConnectError:
            return format_error(f"Connection error: Cannot connect to Home Assistant at {HA_URL}")
        except httpx.TimeoutException:
            return format_error(
                f"Timeout error: Home Assistant at {HA_URL} did not respond in time"
            )
        except httpx.HTTPStatusError as e:
            return format_error(
                f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}"
            )
        except httpx.RequestError as e:
            return format_error(f"Error connecting to Home Assistant: {str(e)}")
        except Exception as e:
            return format_error(f"Unexpected error: {str(e)}")

    return cast(F, wrapper)


# Persistent HTTP client
async def get_client() -> httpx.AsyncClient:
    """Get a persistent httpx client for Home Assistant API calls"""
    global _client
    if _client is None:
        logger.debug("Creating new HTTP client")
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def cleanup_client() -> None:
    """Close the HTTP client when shutting down"""
    global _client
    if _client:
        logger.debug("Closing HTTP client")
        await _client.aclose()
        _client = None


# Direct entity retrieval function
async def get_all_entity_states() -> dict[str, dict[str, Any]]:
    """Fetch all entity states from Home Assistant"""
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
    response.raise_for_status()
    entities = response.json()

    # Create a mapping for easier access
    return {entity["entity_id"]: entity for entity in entities}


def filter_fields(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """
    Filter entity data to only include requested fields

    This function helps reduce token usage by returning only requested fields.

    Args:
        data: The complete entity data dictionary
        fields: List of fields to include in the result
               - "state": Include the entity state
               - "attributes": Include all attributes
               - "attr.X": Include only attribute X (e.g. "attr.brightness")
               - "context": Include context data
               - "last_updated"/"last_changed": Include timestamp fields

    Returns:
        A filtered dictionary with only the requested fields
    """
    if not fields:
        return data

    result = {"entity_id": data["entity_id"]}

    for field in fields:
        if field == "state":
            result["state"] = data.get("state")
        elif field == "attributes":
            result["attributes"] = data.get("attributes", {})
        elif field.startswith("attr.") and len(field) > 5:
            attr_name = field[5:]
            attributes = data.get("attributes", {})
            if attr_name in attributes:
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"][attr_name] = attributes[attr_name]
        elif field == "context":
            if "context" in data:
                result["context"] = data["context"]
        elif field in ["last_updated", "last_changed"]:
            if field in data:
                result[field] = data[field]

    return result


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
async def get_entity_state(
    entity_id: str, fields: list[str] | None = None, lean: bool = False
) -> dict[str, Any]:
    """
    Get the state of a Home Assistant entity

    Args:
        entity_id: The entity ID to get
        fields: Optional list of specific fields to include in the response
        lean: If True, returns a token-efficient version with minimal fields
              (overridden by fields parameter if provided)

    Returns:
        Entity state dictionary, optionally filtered to include only specified fields
    """
    # Fetch directly
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states/{entity_id}", headers=get_ha_headers())
    response.raise_for_status()
    entity_data = response.json()

    # Apply field filtering if requested
    if fields:
        # User-specified fields take precedence
        return filter_fields(entity_data, fields)
    if lean:
        # Build domain-specific lean fields
        lean_fields = DEFAULT_LEAN_FIELDS.copy()

        # Add domain-specific important attributes
        domain = entity_id.split(".")[0]
        if domain in DOMAIN_IMPORTANT_ATTRIBUTES:
            for attr in DOMAIN_IMPORTANT_ATTRIBUTES[domain]:
                lean_fields.append(f"attr.{attr}")

        return filter_fields(entity_data, lean_fields)
    # Return full entity data
    return entity_data


@handle_api_errors
async def get_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int = 100,
    fields: list[str] | None = None,
    lean: bool = True,
) -> list[dict[str, Any]]:
    """
    Get a list of all entities from Home Assistant with optional filtering and search

    Args:
        domain: Optional domain to filter entities by (e.g., 'light', 'switch')
        search_query: Optional case-insensitive search term to filter by entity_id, friendly_name or other attributes
        limit: Maximum number of entities to return (default: 100)
        fields: Optional list of specific fields to include in each entity
        lean: If True (default), returns token-efficient versions with minimal fields

    Returns:
        List of entity dictionaries, optionally filtered by domain and search terms,
        and optionally limited to specific fields
    """
    # Get all entities directly
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
    response.raise_for_status()
    entities = response.json()

    # Filter by domain if specified
    if domain:
        entities = [entity for entity in entities if entity["entity_id"].startswith(f"{domain}.")]

    # Search if query is provided
    if search_query and search_query.strip():
        search_term = search_query.lower().strip()
        filtered_entities = []

        for entity in entities:
            # Search in entity_id
            if search_term in entity["entity_id"].lower():
                filtered_entities.append(entity)
                continue

            # Search in friendly_name
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            if friendly_name and search_term in friendly_name:
                filtered_entities.append(entity)
                continue

            # Search in other common attributes (state, area_id, etc.)
            if search_term in entity.get("state", "").lower():
                filtered_entities.append(entity)
                continue

            # Search in other attributes
            for _attr_name, attr_value in entity.get("attributes", {}).items():
                # Check if attribute value can be converted to string
                if isinstance(attr_value, (str, int, float, bool)):
                    if search_term in str(attr_value).lower():
                        filtered_entities.append(entity)
                        break

        entities = filtered_entities

    # Apply the limit
    if limit > 0 and len(entities) > limit:
        entities = entities[:limit]

    # Apply field filtering if requested
    if fields:
        # Use explicit field list when provided
        return [filter_fields(entity, fields) for entity in entities]
    if lean:
        # Apply domain-specific lean fields to each entity
        result = []
        for entity in entities:
            # Get the entity's domain
            entity_domain = entity["entity_id"].split(".")[0]

            # Start with basic lean fields
            lean_fields = DEFAULT_LEAN_FIELDS.copy()

            # Add domain-specific important attributes
            if entity_domain in DOMAIN_IMPORTANT_ATTRIBUTES:
                for attr in DOMAIN_IMPORTANT_ATTRIBUTES[entity_domain]:
                    lean_fields.append(f"attr.{attr}")

            # Filter and add to result
            result.append(filter_fields(entity, lean_fields))

        return result
    # Return full entities
    return entities


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

    # Invalidate cache after service calls as they might change entity states
    global _entities_timestamp
    _entities_timestamp = 0

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


@handle_api_errors
async def get_automations() -> list[dict[str, Any]]:
    """Get a list of all automations from Home Assistant"""
    # Reuse the get_entities function with domain filtering
    automation_entities = await get_entities(domain="automation")

    # Check if we got an error response
    if isinstance(automation_entities, dict) and "error" in automation_entities:
        return automation_entities  # Just pass through the error

    # Process automation entities
    result = []
    try:
        for entity in automation_entities:
            # Extract relevant information
            automation_info = {
                "id": entity["entity_id"].split(".")[1],
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "alias": entity["attributes"].get("friendly_name", entity["entity_id"]),
            }

            # Add any additional attributes that might be useful
            if "last_triggered" in entity["attributes"]:
                automation_info["last_triggered"] = entity["attributes"]["last_triggered"]

            result.append(automation_info)
    except (TypeError, KeyError) as e:
        # Handle errors in processing the entities
        return {"error": f"Error processing automation entities: {str(e)}"}

    return result


@handle_api_errors
async def reload_automations() -> dict[str, Any]:
    """Reload all automations in Home Assistant"""
    return await call_service("automation", "reload", {})


@handle_api_errors
async def get_automation_config(automation_id: str) -> dict[str, Any]:
    """
    Get full automation configuration including triggers, conditions, actions

    Args:
        automation_id: The automation ID to get (without 'automation.' prefix)

    Returns:
        Complete automation configuration dictionary with:
        - id: Automation identifier
        - alias: Display name
        - description: Automation description
        - trigger: List of trigger configurations
        - condition: List of condition configurations
        - action: List of action configurations
        - mode: Automation mode (single, restart, queued, parallel)

    Example response:
        {
            "id": "automation_id",
            "alias": "Turn on lights at sunset",
            "description": "Automatically turn on lights",
            "trigger": [...],
            "condition": [...],
            "action": [...],
            "mode": "single"
        }
    """
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def create_automation(config: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new automation from configuration dictionary

    Args:
        config: Automation configuration dictionary with:
            - id: Automation identifier (optional, will be generated if missing)
            - alias: Display name
            - description: Automation description (optional)
            - trigger: List of trigger configurations (required)
            - condition: List of condition configurations (optional)
            - action: List of action configurations (required)
            - mode: Automation mode (optional, default: "single")

    Returns:
        Response from the create operation

    Note:
        If 'id' is not provided in config, a unique ID will be generated.
        The automation will be created and enabled by default.
    """
    # Extract automation_id from config or generate one
    automation_id = config.get("id")
    if not automation_id:
        automation_id = f"automation_{uuid.uuid4().hex[:8]}"
        config["id"] = automation_id

    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
        json=config,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def update_automation(automation_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Update an existing automation with new configuration

    Args:
        automation_id: The automation ID to update (without 'automation.' prefix)
        config: Updated automation configuration dictionary

    Returns:
        Response from the update operation

    Note:
        The config should include all fields you want to keep.
        Fields not included may be removed.
    """
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
        json=config,
    )
    response.raise_for_status()
    return response.json()


@handle_api_errors
async def delete_automation(automation_id: str) -> dict[str, Any]:
    """
    Delete an automation

    Args:
        automation_id: The automation ID to delete (without 'automation.' prefix)

    Returns:
        Response from the delete operation

    Note:
        ⚠️ This permanently deletes the automation. There is no undo.
        Make sure the automation is not referenced by other automations or scripts.
    """
    client = await get_client()
    response = await client.delete(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        headers=get_ha_headers(),
    )
    response.raise_for_status()
    return {"status": "deleted", "automation_id": automation_id}


@handle_api_errors
async def enable_automation(automation_id: str) -> dict[str, Any]:
    """
    Enable an automation

    Args:
        automation_id: The automation ID to enable (without 'automation.' prefix)

    Returns:
        Response from the enable operation

    Note:
        Enabling an automation allows it to trigger automatically.
        The automation must exist and be configured correctly.
    """
    return await call_service("automation", "turn_on", {"entity_id": f"automation.{automation_id}"})


@handle_api_errors
async def disable_automation(automation_id: str) -> dict[str, Any]:
    """
    Disable an automation

    Args:
        automation_id: The automation ID to disable (without 'automation.' prefix)

    Returns:
        Response from the disable operation

    Note:
        Disabling prevents the automation from triggering automatically.
        The automation configuration is preserved and can be re-enabled later.
    """
    return await call_service(
        "automation", "turn_off", {"entity_id": f"automation.{automation_id}"}
    )


@handle_api_errors
async def trigger_automation(automation_id: str) -> dict[str, Any]:
    """
    Manually trigger an automation

    Args:
        automation_id: The automation ID to trigger (without 'automation.' prefix)

    Returns:
        Response from the trigger operation

    Note:
        This manually executes the automation actions.
        Useful for testing automations without waiting for triggers.
        The automation does not need to be enabled to be triggered manually.
    """
    return await call_service("automation", "trigger", {"entity_id": f"automation.{automation_id}"})


@handle_api_errors
async def get_automation_execution_log(automation_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get automation execution history from logbook

    Args:
        automation_id: The automation ID to get history for (without 'automation.' prefix)
        hours: Number of hours of history to retrieve (default: 24)

    Returns:
        Dictionary containing:
        - automation_id: The automation ID requested
        - executions: List of execution events with timestamps
        - count: Number of executions found
        - time_range: Dictionary with start_time and end_time

    Example response:
        {
            "automation_id": "automation_id",
            "executions": [
                {
                    "when": "2024-01-01T12:00:00Z",
                    "name": "Turn on lights",
                    "domain": "automation",
                    "entity_id": "automation.automation_id"
                }
            ],
            "count": 5,
            "time_range": {
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z"
            }
        }

    Best Practices:
        - Keep hours reasonable (24-72) for token efficiency
        - Use to debug why an automation isn't firing
        - Check execution frequency to optimize automation triggers
    """
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=hours)
    start_time_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S")

    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/logbook/{start_time_iso}",
        headers=get_ha_headers(),
        params={"entity": f"automation.{automation_id}"},
    )
    response.raise_for_status()
    logbook_data = response.json()

    return {
        "automation_id": automation_id,
        "executions": logbook_data,
        "count": len(logbook_data),
        "time_range": {
            "start_time": start_time_iso,
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
    }


@handle_api_errors
async def validate_automation_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an automation configuration

    Args:
        config: Automation configuration dictionary to validate

    Returns:
        Dictionary with validation results:
        - valid: Boolean indicating if config is valid
        - errors: List of validation errors (empty if valid)
        - warnings: List of validation warnings
        - suggestions: List of improvement suggestions

    Validation checks:
        - Required fields present (trigger, action)
        - Trigger structure is valid
        - Action structure is valid
        - Condition structure is valid (if provided)
        - Mode value is valid
        - Entity IDs referenced exist (basic check)

    Example response:
        {
            "valid": true,
            "errors": [],
            "warnings": ["Missing description for automation"],
            "suggestions": ["Consider adding a description"]
        }
    """
    errors = []
    warnings = []
    suggestions = []

    # Check required fields
    if "trigger" not in config or not config["trigger"]:
        errors.append("Missing required field: 'trigger'")
    elif not isinstance(config["trigger"], list):
        errors.append("'trigger' must be a list")

    if "action" not in config or not config["action"]:
        errors.append("Missing required field: 'action'")
    elif not isinstance(config["action"], list):
        errors.append("'action' must be a list")

    # Validate mode
    if "mode" in config:
        valid_modes = ["single", "restart", "queued", "parallel"]
        if config["mode"] not in valid_modes:
            errors.append(f"'mode' must be one of {valid_modes}, got: {config.get('mode')}")

    # Warnings and suggestions
    if "alias" not in config:
        warnings.append("Missing 'alias' - automation will have no display name")
        suggestions.append("Add an 'alias' field for better organization")

    if "description" not in config:
        warnings.append("Missing 'description' - consider adding one for documentation")

    # Basic trigger validation
    if "trigger" in config and isinstance(config["trigger"], list):
        for i, trigger in enumerate(config["trigger"]):
            if not isinstance(trigger, dict):
                errors.append(f"Trigger {i} must be a dictionary")
            elif "platform" not in trigger:
                errors.append(f"Trigger {i} missing required 'platform' field")

    # Basic action validation
    if "action" in config and isinstance(config["action"], list):
        if len(config["action"]) == 0:
            warnings.append("No actions defined - automation will do nothing")

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
    }


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
            entity = await get_entity_state(entity_id, detailed=True)
            config_data["entity"] = entity
            return config_data
    except Exception:  # nosec B110
        # Config API not available, fall through to entity state
        pass

    # Fallback to entity state
    return await get_entity_state(entity_id, detailed=True)


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

    entity = await get_entity_state(entity_id, detailed=True)

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
async def get_entity_history(entity_id: str, hours: int) -> list[dict[str, Any]]:
    """
    Get the history of an entity's state changes from Home Assistant.

    Args:
        entity_id: The entity ID to get history for.
        hours: Number of hours of history to retrieve.

    Returns:
        A list of state change objects, or an error dictionary.
    """
    client = await get_client()

    # Calculate the end time for the history lookup
    end_time = datetime.now(UTC)
    end_time_iso = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Calculate the start time for the history lookup based on end_time
    start_time = end_time - timedelta(hours=hours)
    start_time_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the API URL
    url = f"{HA_URL}/api/history/period/{start_time_iso}"

    # Set query parameters
    params = {
        "filter_entity_id": entity_id,
        "minimal_response": "true",
        "end_time": end_time_iso,
    }

    # Make the API call
    response = await client.get(url, headers=get_ha_headers(), params=params)
    response.raise_for_status()

    # Return the JSON response
    return response.json()


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
