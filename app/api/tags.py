"""Tags API module for hass-mcp.

This module provides functions for interacting with Home Assistant RFID/NFC tags.
Tags are used with NFC/RFID readers to trigger automations.
"""

import logging
from typing import Any, cast

from app.api.automations import get_automation_config, get_automations
from app.api.base import BaseAPI
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class TagsAPI(BaseAPI):
    """API client for Home Assistant tag operations."""

    pass


_tags_api = TagsAPI()


@handle_api_errors
async def list_tags() -> list[dict[str, Any]]:
    """
    Get list of all RFID/NFC tags.

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
    response = await _tags_api.get("/api/tag")
    return cast(list[dict[str, Any]], response)


@handle_api_errors
async def create_tag(tag_id: str, name: str) -> dict[str, Any]:
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
    """
    payload = {"tag_id": tag_id, "name": name}
    return await _tags_api.post("/api/tag", data=payload)


@handle_api_errors
async def delete_tag(tag_id: str) -> dict[str, Any]:
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
    return await _tags_api.delete(f"/api/tag/{tag_id}")


@handle_api_errors
async def get_tag_automations(tag_id: str) -> list[dict[str, Any]]:
    """
    Get automations triggered by a tag.

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
