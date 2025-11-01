"""Templates API module for hass-mcp.

This module provides functions for testing Jinja2 templates.
"""

import logging
from typing import Any, cast

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def test_template(  # noqa: PT001 (function name not matching pytest naming convention)
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

    Example response:
        {
            "result": "on",
            "listeners": {"all": True, "domains": [], "entities": ["light.living_room"]}
        }

    Examples:
        # Test a simple template
        result = await test_template("{{ states('sensor.temperature') }}")

        # Test with entity context
        result = await test_template(
            "{{ states('light.living_room') }}",
            {"entity_id": "light.living_room"}
        )

    Note:
        Template testing API might not be available in all Home Assistant versions.
        If unavailable, returns a helpful error message with status code 404.
        Templates are used for automation conditions and dynamic values.

    Best Practices:
        - Use templates to test dynamic values before using in automations
        - Test templates with entity context for entity-specific operations
        - Handle 404 errors gracefully (template API might not be available)
        - Use for debugging automation conditions
    """
    client = await get_client()

    payload: dict[str, Any] = {"template": template_string}
    if entity_context:
        payload["entity_id"] = entity_context

    response = await client.post(
        f"{HA_URL}/api/template",
        headers=get_ha_headers(),
        json=payload,
    )

    if response.status_code == 404:
        # Template API might not be available
        return {
            "error": "Template testing API not available in this Home Assistant version",
            "note": "Try using the script developer tools in Home Assistant UI",
            "template": template_string,
        }

    response.raise_for_status()
    return cast(dict[str, Any], response.json())
