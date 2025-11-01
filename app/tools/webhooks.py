"""Webhooks MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant webhooks.
These tools are thin wrappers around the webhooks API layer.
"""

import logging
from typing import Any

from app.api.webhooks import list_webhooks, test_webhook

logger = logging.getLogger(__name__)


async def list_webhooks_tool() -> list[dict[str, Any]]:
    """
    Get a list of registered webhooks in Home Assistant.

    Returns:
        List of webhook information dictionaries containing:
        - note: Information about webhook configuration
        - common_webhook_id_pattern: Pattern for webhook IDs
        - usage: Usage instructions
        - webhook_url_format: Webhook URL format
        - authentication: Authentication requirements

    Examples:
        Returns webhook patterns and usage information

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
    logger.info("Getting list of webhooks")
    return await list_webhooks()


async def test_webhook_tool(
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
    logger.info(f"Testing webhook: {webhook_id}" + (f" with payload: {payload}" if payload else ""))
    return await test_webhook(webhook_id, payload)
