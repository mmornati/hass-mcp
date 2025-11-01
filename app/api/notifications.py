"""Notifications API module for hass-mcp.

This module provides functions for interacting with Home Assistant notifications.
Notifications can be sent across various platforms (mobile apps, email, Telegram, etc.).
"""

import logging
from typing import Any, cast

from app.api.base import BaseAPI
from app.api.entities import get_entities
from app.api.services import call_service
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


class NotificationsAPI(BaseAPI):
    """API client for Home Assistant notification operations."""

    pass


_notifications_api = NotificationsAPI()


@handle_api_errors
async def list_notification_services() -> list[dict[str, Any]]:
    """
    Get list of available notification platforms.

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
    try:
        # Try to get services via services API
        response = await _notifications_api.get("/api/services")
        services = cast(dict[str, Any], response)

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
async def test_notification_delivery(platform: str, message: str) -> dict[str, Any]:  # noqa: PT001
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
    """
    test_message = f"[TEST] {message}"
    return await send_notification(test_message, target=platform)
