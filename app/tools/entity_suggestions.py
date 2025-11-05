"""Entity suggestions tools for hass-mcp.

This module provides MCP tools for context-aware entity suggestions.
"""

from typing import Annotated, Any

from app.api.entity_suggestions import get_entity_suggestions


async def get_entity_suggestions_tool(
    entity_id: Annotated[str, "The entity ID to get suggestions for"],
    relationship_types: Annotated[
        list[str] | None,
        "Types of relationships to consider (same_area, same_device, same_domain, similar_name, similar_capabilities). If not specified, all types are used.",
    ] = None,
    limit: Annotated[int, "Maximum number of suggestions to return"] = 10,
) -> list[dict[str, Any]]:
    """
    Get context-aware entity suggestions based on relationships and usage patterns.

    This tool helps discover related entities by analyzing various relationships:
    - same_area: Entities in the same area/room
    - same_device: Entities from the same physical device
    - same_domain: Entities of the same type (e.g., all lights)
    - similar_name: Entities with similar friendly names
    - similar_capabilities: Entities with similar functionality (uses vector embeddings)

    Each suggestion includes:
    - entity_id: The suggested entity ID
    - entity: Full entity state information
    - relationship_type: Why this entity was suggested
    - relationship_score: Confidence score (0.0-1.0)
    - explanation: Human-readable explanation of the relationship

    Examples:
        # Get all types of suggestions for a light
        suggestions = await get_entity_suggestions_tool("light.living_room")

        # Get only same-area and same-device suggestions
        suggestions = await get_entity_suggestions_tool(
            "light.living_room",
            relationship_types=["same_area", "same_device"],
            limit=5
        )

        # Get entities with similar capabilities
        suggestions = await get_entity_suggestions_tool(
            "sensor.temperature",
            relationship_types=["similar_capabilities"],
            limit=10
        )

    Args:
        entity_id: The entity ID to get suggestions for
        relationship_types: Types of relationships to consider. Defaults to all types.
        limit: Maximum number of suggestions to return (default: 10)

    Returns:
        List of entity suggestions with relationship information and explanations.
    """
    return await get_entity_suggestions(
        entity_id=entity_id,
        relationship_types=relationship_types,
        limit=limit,
    )
