"""Entity description generation MCP tool for hass-mcp.

This module provides a tool for generating rich, contextual entity descriptions
for better semantic search.
"""

import logging
from typing import Any

from app.api.entities import get_entities, get_entity_state
from app.core.vectordb.description import (  # noqa: PLC0415
    generate_entity_description_batch,
    generate_entity_description_enhanced,
)

logger = logging.getLogger(__name__)


async def generate_entity_description_tool(
    entity_id: str,
    use_template: bool = True,
    language: str = "en",
) -> dict[str, Any]:
    """
    Generate rich, contextual description for an entity.

    This tool generates rich descriptions for entities using templates,
    multi-language support, and context-aware information for better semantic search.

    Args:
        entity_id: The entity ID to generate description for
        use_template: Whether to use template-based generation (default: True)
        language: Language for description (default: "en")

    Returns:
        A dictionary containing:
        - entity_id: The entity ID
        - description: The generated description
        - template_used: Whether template was used
        - language: The language used

    Examples:
        entity_id="light.living_room"
        Returns:
        {
            "entity_id": "light.living_room",
            "description": "Living Room Light - light entity in the Living Room area. Supports color modes: brightness, brightness control. Currently on. Part of the Philips Hue system.",
            "template_used": true,
            "language": "en"
        }
    """
    logger.info(f"Generating description for entity: {entity_id}")

    if not entity_id or not entity_id.strip():
        return {
            "error": "Empty entity_id provided",
            "entity_id": entity_id,
            "description": None,
            "template_used": use_template,
            "language": language,
        }

    try:
        # Get entity state
        entity = await get_entity_state(entity_id, lean=False)

        if isinstance(entity, dict) and "error" in entity:
            return {
                "error": entity["error"],
                "entity_id": entity_id,
                "description": None,
                "template_used": use_template,
                "language": language,
            }

        # Generate description
        description = await generate_entity_description_enhanced(
            entity, use_template=use_template, language=language
        )

        return {
            "entity_id": entity_id,
            "description": description,
            "template_used": use_template,
            "language": language,
        }

    except Exception as e:
        logger.error(f"Failed to generate description for {entity_id}: {e}")
        return {
            "error": f"Failed to generate description: {str(e)}",
            "entity_id": entity_id,
            "description": None,
            "template_used": use_template,
            "language": language,
        }


async def generate_entity_descriptions_batch_tool(
    entity_ids: list[str] | None = None,
    use_template: bool = True,
    language: str = "en",
) -> dict[str, Any]:
    """
    Generate rich descriptions for multiple entities in batch.

    This tool generates descriptions for multiple entities efficiently using
    batch processing for better performance.

    Args:
        entity_ids: Optional list of entity IDs to generate descriptions for.
                   If None, generates descriptions for all entities.
        use_template: Whether to use template-based generation (default: True)
        language: Language for descriptions (default: "en")

    Returns:
        A dictionary containing:
        - total: Total number of entities processed
        - succeeded: Number of successfully generated descriptions
        - failed: Number of failed descriptions
        - descriptions: Dictionary mapping entity_id to description

    Examples:
        entity_ids=["light.living_room", "sensor.temperature"]
        Returns:
        {
            "total": 2,
            "succeeded": 2,
            "failed": 0,
            "descriptions": {
                "light.living_room": "Living Room Light - light entity...",
                "sensor.temperature": "Temperature Sensor - sensor entity..."
            }
        }
    """
    logger.info(f"Generating descriptions for {len(entity_ids) if entity_ids else 'all'} entities")

    try:
        # Get entities
        if entity_ids is None:
            entities = await get_entities(lean=False)
        else:
            entities = []
            for entity_id in entity_ids:
                entity = await get_entity_state(entity_id, lean=False)
                if isinstance(entity, dict) and "error" not in entity:
                    entities.append(entity)

        if not isinstance(entities, list):
            return {
                "error": "Failed to get entities",
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "descriptions": {},
            }

        # Generate descriptions in batch
        descriptions = await generate_entity_description_batch(
            entities, use_template=use_template, language=language
        )

        return {
            "total": len(entities),
            "succeeded": len(descriptions),
            "failed": len(entities) - len(descriptions),
            "descriptions": descriptions,
        }

    except Exception as e:
        logger.error(f"Failed to generate descriptions in batch: {e}")
        return {
            "error": f"Failed to generate descriptions: {str(e)}",
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "descriptions": {},
        }
