"""Tags MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant RFID/NFC tags.
These tools are thin wrappers around the tags API layer.
"""

import logging
from typing import Any

from app.api.tags import (
    create_tag,
    delete_tag,
    get_tag_automations,
    list_tags,
)

logger = logging.getLogger(__name__)


async def list_tags_tool() -> list[dict[str, Any]]:
    """
    Get a list of all RFID/NFC tags in Home Assistant.

    Returns:
        List of tag dictionaries containing:
        - tag_id: The tag ID (unique identifier)
        - name: Display name of the tag
        - last_scanned: Last scan timestamp (if available)
        - device_id: Device ID associated with the tag (if available)

    Examples:
        Returns all tags with their configuration and metadata

    Note:
        Tags are RFID/NFC tags used for NFC-based automations.
        Tags can trigger automations when scanned.
        Each tag has a unique tag_id and optional name.

    Best Practices:
        - Use this to discover configured tags
        - Check tag IDs before creating new tags
        - Use to manage tags for NFC-based automations
        - Use to document all tags in your setup
    """
    logger.info("Getting list of tags")
    return await list_tags()


async def create_tag_tool(tag_id: str, name: str) -> dict[str, Any]:
    """
    Create a new tag.

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
        - Use consistent naming conventions for tags
    """
    logger.info(f"Creating tag: {tag_id} with name: {name}")
    return await create_tag(tag_id, name)


async def delete_tag_tool(tag_id: str) -> dict[str, Any]:
    """
    Delete a tag.

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
    logger.info(f"Deleting tag: {tag_id}")
    return await delete_tag(tag_id)


async def get_tag_automations_tool(tag_id: str) -> list[dict[str, Any]]:
    """
    Get automations triggered by a tag.

    Args:
        tag_id: The tag ID to find automations for

    Returns:
        List of automation dictionaries containing:
        - automation_id: The automation entity ID
        - alias: Display name of the automation
        - enabled: Whether the automation is enabled

    Examples:
        tag_id="ABC123" - find all automations triggered by this tag

    Note:
        This searches through all automations to find those with tag triggers.
        Tag triggers use platform "tag" with matching tag_id.
        Useful for understanding tag dependencies before deletion.

    Best Practices:
        - Use before deleting tags to check dependencies
        - Review automations that depend on the tag
        - Update or remove dependent automations if needed
        - Use to document tag usage in your setup
        - Use to troubleshoot tag-triggered automations
    """
    logger.info(f"Getting automations for tag: {tag_id}")
    return await get_tag_automations(tag_id)
