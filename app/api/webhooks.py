"""Webhooks API module for hass-mcp.

This module provides functions for interacting with Home Assistant webhooks.
Webhooks allow external systems to trigger Home Assistant actions via HTTP POST requests.
"""

import logging
from typing import Any

from app.config import HA_URL
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def list_webhooks() -> list[dict[str, Any]]:
    """
    List registered webhooks (might need to parse configuration).

    Returns:
        List of webhook information dictionaries containing:
        - note: Information about webhook configuration
        - common_webhook_id_pattern: Pattern for webhook IDs
        - usage: Usage instructions
        - webhook_url_format: Webhook URL format
        - authentication: Authentication requirements

    Example response:
        [
            {
                "note": "Webhooks are typically defined in configuration.yaml or automation/script triggers",
                "common_webhook_id_pattern": "webhook_id defined in automations/scripts",
                "usage": "Use test_webhook to test webhook endpoints",
                "webhook_url_format": "/api/webhook/{webhook_id}",
                "authentication": "Webhooks don't require authentication token"
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
async def test_webhook(  # noqa: PT001
    webhook_id: str,
    payload: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test webhook endpoint.

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
        - Check webhook response to verify it's working correctly
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
