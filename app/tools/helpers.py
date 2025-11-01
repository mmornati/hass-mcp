"""Helpers MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant input helpers.
These tools are thin wrappers around the helpers API layer.
"""

import logging
from typing import Any

from app.api.helpers import get_helper, list_helpers, update_helper

logger = logging.getLogger(__name__)


async def list_helpers_tool(helper_type: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all input helpers in Home Assistant.

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

    Examples:
        helper_type=None - get all helpers
        helper_type="input_boolean" - get only input_boolean helpers
        helper_type="input_number" - get only input_number helpers

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
    logger.info("Getting list of helpers" + (f" of type: {helper_type}" if helper_type else ""))
    return await list_helpers(helper_type)


async def get_helper_tool(helper_id: str) -> dict[str, Any]:
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
    logger.info(f"Getting helper details: {helper_id}")
    return await get_helper(helper_id)


async def update_helper_tool(helper_id: str, value: Any) -> dict[str, Any]:
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
        - Use timers with "start", "pause", or "cancel"
    """
    logger.info(f"Updating helper: {helper_id} with value: {value}")
    return await update_helper(helper_id, value)
