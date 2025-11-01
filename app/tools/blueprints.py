"""Blueprints MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant blueprints.
These tools are thin wrappers around the blueprints API layer.
"""

import logging
from typing import Any

from app.api.blueprints import (
    create_automation_from_blueprint,
    get_blueprint,
    import_blueprint,
    list_blueprints,
)

logger = logging.getLogger(__name__)


async def list_blueprints_tool(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get a list of all available blueprints, optionally filtered by domain.

    Args:
        domain: Optional domain to filter blueprints by (e.g., 'automation')

    Returns:
        List of blueprint dictionaries containing:
        - path: Blueprint path
        - domain: Blueprint domain
        - name: Blueprint name
        - metadata: Blueprint metadata

    Examples:
        domain=None - get all blueprints
        domain="automation" - get only automation blueprints

    Note:
        Blueprints are reusable automation templates.
        Use domain filter to find blueprints for specific use cases.

    Best Practices:
        - Use domain filter to find blueprints for specific use cases
        - Check blueprint metadata to understand what inputs are required
        - Use get_blueprint to get full blueprint definition before using
        - Verify blueprint source before using in production
    """
    logger.info("Getting blueprints" + (f" for domain: {domain}" if domain else ""))
    return await list_blueprints(domain)


async def get_blueprint_tool(blueprint_id: str, domain: str | None = None) -> dict[str, Any]:
    """
    Get blueprint definition and metadata.

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

    Examples:
        blueprint_id="motion_light", domain="automation" - get automation blueprint
        blueprint_id="automation/motion_light" - get blueprint with full path

    Note:
        Blueprint ID typically includes domain and path.
        If domain is not provided, attempts to extract it from blueprint_id.

    Best Practices:
        - Use this to inspect blueprint inputs before creating automation
        - Check metadata to understand what the blueprint does
        - Review definition to understand blueprint structure
        - Validate inputs match blueprint schema before using
    """
    logger.info(f"Getting blueprint: {blueprint_id}" + (f" for domain: {domain}" if domain else ""))
    return await get_blueprint(blueprint_id, domain)


async def import_blueprint_tool(url: str) -> dict[str, Any]:
    """
    Import blueprint from URL.

    Args:
        url: The URL to import the blueprint from

    Returns:
        Response dictionary containing imported blueprint information

    Examples:
        url="https://www.home-assistant.io/blueprints/..." - import from community
        url="https://github.com/user/repo/blob/main/blueprint.yaml" - import from GitHub

    Note:
        This imports a blueprint from a community URL or external source.
        The URL is automatically URL-encoded when making the API request.

    Best Practices:
        - Use community blueprint URLs from Home Assistant documentation
        - Verify blueprint source before importing
        - Check blueprint definition after import before using
        - Review blueprint inputs and requirements before creating automations
    """
    logger.info(f"Importing blueprint from URL: {url}")
    return await import_blueprint(url)


async def create_automation_from_blueprint_tool(
    blueprint_id: str, inputs: dict[str, Any], domain: str | None = None
) -> dict[str, Any]:
    """
    Create automation from blueprint with specified inputs.

    Args:
        blueprint_id: The blueprint ID to use (may include domain and path)
        inputs: Dictionary of input values for the blueprint (must match blueprint input schema)
        domain: Optional domain for the blueprint (e.g., 'automation')

    Returns:
        Response from the automation creation operation

    Examples:
        blueprint_id="motion_light", domain="automation", inputs={
            "motion_entity": "binary_sensor.motion",
            "light_entity": "light.living_room",
            "delay": "00:00:05"
        }

    Note:
        This creates a new automation using a blueprint as a template.
        The inputs dictionary must match the blueprint's input schema.
        An automation ID will be automatically generated if not provided in inputs.

    Best Practices:
        - Get blueprint definition first to see required inputs
        - Validate inputs match blueprint schema
        - Use descriptive automation_id in inputs for better organization
        - Test blueprint automation before using in production
    """
    logger.info(f"Creating automation from blueprint: {blueprint_id}")
    return await create_automation_from_blueprint(blueprint_id, inputs, domain)
