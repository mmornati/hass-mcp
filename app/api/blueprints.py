"""Blueprints API module for hass-mcp.

This module provides functions for interacting with Home Assistant blueprints.
Blueprints are reusable automation templates.
"""

import logging
import urllib.parse
import uuid
from typing import Any

from app.api.automations import create_automation
from app.api.base import BaseAPI
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_VERY_LONG
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class BlueprintsAPI(BaseAPI):
    """API client for Home Assistant blueprint operations."""

    pass


_blueprints_api = BlueprintsAPI()


@handle_api_errors
@cached(ttl=TTL_VERY_LONG, key_prefix="blueprints")
async def list_blueprints(domain: str | None = None) -> list[dict[str, Any]]:
    """
    Get list of available blueprints.

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

    Best Practices:
        - Use domain filter to find blueprints for specific use cases
        - Check blueprint metadata to understand what inputs are required
        - Use get_blueprint() to get full blueprint definition before using
    """
    url = f"/api/blueprint/domain/{domain}" if domain else "/api/blueprint/list"
    return await _blueprints_api.get(url)


@handle_api_errors
@cached(ttl=TTL_VERY_LONG, key_prefix="blueprints")
async def get_blueprint(blueprint_id: str, domain: str | None = None) -> dict[str, Any]:
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

    Best Practices:
        - Use this to inspect blueprint inputs before creating automation
        - Check metadata to understand what the blueprint does
        - Review definition to understand blueprint structure
    """
    # Blueprint ID typically includes domain and path
    if domain:
        url = f"/api/blueprint/metadata/{domain}/{blueprint_id}"
    else:
        # Try to extract domain from blueprint_id
        parts = blueprint_id.split("/")
        if len(parts) >= 2:
            domain = parts[0]
            path = "/".join(parts[1:])
            url = f"/api/blueprint/metadata/{domain}/{path}"
        else:
            return {
                "error": "Cannot determine domain for blueprint. Please provide domain parameter."
            }

    return await _blueprints_api.get(url)


@handle_api_errors
async def import_blueprint(url: str) -> dict[str, Any]:
    """
    Import blueprint from URL.

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

    Best Practices:
        - Use community blueprint URLs from Home Assistant documentation
        - Verify blueprint source before importing
        - Check blueprint definition after import before using
    """
    # URL encode the blueprint URL
    encoded_url = urllib.parse.quote(url, safe="")

    endpoint = f"/api/blueprint/import/{encoded_url}"
    return await _blueprints_api.get(endpoint)


@handle_api_errors
async def create_automation_from_blueprint(
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

    Example response:
        {
            "automation_id": "automation_12345",
            "status": "created"
        }

    Note:
        This creates a new automation using a blueprint as a template.
        The inputs dictionary must match the blueprint's input schema.
        An automation ID will be automatically generated if not provided in inputs.

    Best Practices:
        - Get blueprint definition first to see required inputs
        - Validate inputs match blueprint schema
        - Use descriptive automation_id in inputs for better organization
    """
    # Get blueprint definition first
    blueprint = await get_blueprint(blueprint_id, domain)

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
