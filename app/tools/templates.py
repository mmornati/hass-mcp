"""Template MCP tools for hass-mcp.

This module provides MCP tools for testing Jinja2 templates.
These tools are thin wrappers around the templates API layer.
"""

import logging
from typing import Any

from app.api.templates import test_template

logger = logging.getLogger(__name__)


async def test_template_tool(
    template_string: str,
    entity_context: dict[str, Any] | None = None,  # noqa: PT028
) -> dict[str, Any]:
    """
    Test Jinja2 template rendering.

    Args:
        template_string: The Jinja2 template string to test
        entity_context: Optional dictionary of entity IDs to provide as context
                         (e.g., {"entity_id": "light.living_room"})

    Returns:
        Dictionary containing:
        - result: The rendered template result
        - listeners: Entity listeners (if applicable)
        - error: Error message if template rendering failed

    Examples:
        template_string="{{ states('sensor.temperature') }}" - test simple template
        template_string="{{ states('light.living_room') }}", entity_context={"entity_id": "light.living_room"}

    Note:
        Template testing API might not be available in all Home Assistant versions.
        If unavailable, returns a helpful error message.

    Best Practices:
        - Test templates before using them in automations or scripts
        - Use entity_context to test templates with specific entity context
        - Check for errors in the response
    """
    logger.info(
        f"Testing template: {template_string[:50]}..."
        + (f" with context: {entity_context}" if entity_context else "")
    )
    return await test_template(template_string, entity_context)
