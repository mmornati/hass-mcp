"""Notifications MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant notifications.
These tools are thin wrappers around the notifications API layer.
"""

import logging
from typing import Any

from app.api.notifications import (
    list_notification_services,
    send_notification,
    test_notification_delivery,
)

logger = logging.getLogger(__name__)


async def list_notification_services_tool() -> list[dict[str, Any]]:
    """
    Get a list of all available notification platforms in Home Assistant.

    Returns:
        List of notification service dictionaries containing:
        - service: The service name (e.g., 'notify.mobile_app_iphone')
        - name: Display name of the service
        - description: Service description (if available)
        - entity_id: Entity ID if available from fallback

    Examples:
        Returns all notification services with their configuration

    Note:
        Notification services are platforms that can send notifications.
        Common platforms include mobile_app, telegram, email, etc.

    Best Practices:
        - Use this to discover available notification platforms
        - Check service names before sending notifications
        - Use to test which notification services are configured
        - Use to verify notification services are working
    """
    logger.info("Getting list of notification services")
    return await list_notification_services()


async def send_notification_tool(
    message: str, target: str | None = None, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Send a notification.

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
        - Use to send alerts about system status, errors, or important events
    """
    logger.info(f"Sending notification: '{message}'" + (f" to {target}" if target else ""))
    return await send_notification(message, target, data)


async def test_notification_tool(platform: str, message: str) -> dict[str, Any]:
    """
    Test notification delivery to a specific platform.

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
        - Use to test notification delivery after setup or configuration
    """
    logger.info(f"Testing notification delivery to {platform} with message: '{message}'")
    return await test_notification_delivery(platform, message)
