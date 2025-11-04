"""Helpers API module for hass-mcp.

This module provides functions for interacting with Home Assistant input helpers.
Helpers are virtual entities used for storing values and controlling automations.
"""

import logging
from typing import Any

from app.api.entities import get_entities, get_entity_state
from app.api.services import call_service
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


# Helper types supported by Home Assistant
HELPER_TYPES = [
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


@handle_api_errors
@cached(ttl=TTL_LONG, key_prefix="helpers")
async def list_helpers(helper_type: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of input helpers (input_boolean, input_number, etc.).

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
    all_helpers = []

    if helper_type:
        # Filter by specific type
        if helper_type in HELPER_TYPES:
            helpers = await get_entities(domain=helper_type, lean=True)
            all_helpers.extend(helpers)
    else:
        # Get all helpers
        for helper_domain in HELPER_TYPES:
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
async def get_helper(helper_id: str) -> dict[str, Any]:
    """
    Get helper state and configuration.

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
        all_helpers = await list_helpers()
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
async def update_helper(helper_id: str, value: Any) -> dict[str, Any]:
    """
    Update helper value.

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
