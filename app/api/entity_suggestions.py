"""Entity suggestions API module for hass-mcp.

This module provides context-aware entity suggestions based on relationships
and usage patterns.
"""

import logging
from typing import Any

from app.api.devices import get_device_details
from app.api.entities import get_entities, get_entity_state
from app.core.decorators import handle_api_errors
from app.core.vectordb.config import get_vectordb_config
from app.core.vectordb.indexing import ENTITY_COLLECTION
from app.core.vectordb.manager import get_vectordb_manager

logger = logging.getLogger(__name__)

# Relationship types
RELATIONSHIP_TYPES = {
    "same_area": "Entities in the same area/room",
    "same_device": "Entities from the same device",
    "same_domain": "Entities of the same type",
    "similar_name": "Entities with similar names",
    "similar_capabilities": "Entities with similar capabilities",
    # TODO: Future relationship types to implement:
    # "frequently_used_together": "Entities often used together",
    # "same_manufacturer": "Entities from the same manufacturer",
}


async def _find_entities_by_area(
    area_id: str | None, exclude_entity_id: str
) -> list[dict[str, Any]]:
    """
    Find entities in the same area.

    Args:
        area_id: The area ID to search in
        exclude_entity_id: Entity ID to exclude from results

    Returns:
        List of entities in the same area with relationship metadata
    """
    if not area_id:
        return []

    try:
        # Get all entities
        entities = await get_entities(lean=True)
        if isinstance(entities, dict) and "error" in entities:
            return []

        results = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue

            entity_id = entity.get("entity_id", "")
            if entity_id == exclude_entity_id:
                continue

            # Check if entity is in the same area
            entity_area_id = entity.get("attributes", {}).get("area_id")
            if entity_area_id == area_id:
                results.append(
                    {
                        "entity_id": entity_id,
                        "entity": entity,
                        "relationship_type": "same_area",
                        "relationship_score": 1.0,
                        "metadata": {"area_id": area_id},
                    }
                )

        return results
    except Exception as e:
        logger.error(f"Failed to find entities by area: {e}")
        return []


async def _find_entities_by_device(
    device_id: str | None, exclude_entity_id: str
) -> list[dict[str, Any]]:
    """
    Find entities from the same device.

    Args:
        device_id: The device ID to search for
        exclude_entity_id: Entity ID to exclude from results

    Returns:
        List of entities from the same device with relationship metadata
    """
    if not device_id:
        return []

    try:
        # Get device details to find all entities
        device = await get_device_details(device_id)
        if isinstance(device, dict) and "error" in device:
            return []

        device_entities = device.get("entities", [])
        if not device_entities:
            return []

        results = []
        for entity_id in device_entities:
            if entity_id == exclude_entity_id:
                continue

            try:
                entity = await get_entity_state(entity_id, lean=True)
                if isinstance(entity, dict) and "error" not in entity:
                    results.append(
                        {
                            "entity_id": entity_id,
                            "entity": entity,
                            "relationship_type": "same_device",
                            "relationship_score": 1.0,
                            "metadata": {"device_id": device_id},
                        }
                    )
            except Exception as e:
                logger.debug(f"Failed to get entity {entity_id}: {e}")
                continue

        return results
    except Exception as e:
        logger.error(f"Failed to find entities by device: {e}")
        return []


async def _find_entities_by_domain(
    domain: str | None, exclude_entity_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    """
    Find entities of the same domain/type.

    Args:
        domain: The domain to search for
        exclude_entity_id: Entity ID to exclude from results
        limit: Maximum number of results

    Returns:
        List of entities in the same domain with relationship metadata
    """
    if not domain:
        return []

    try:
        # Get entities of the same domain
        entities = await get_entities(domain=domain, lean=True, limit=limit + 10)
        if isinstance(entities, dict) and "error" in entities:
            return []

        results = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue

            entity_id = entity.get("entity_id", "")
            if entity_id == exclude_entity_id:
                continue

            results.append(
                {
                    "entity_id": entity_id,
                    "entity": entity,
                    "relationship_type": "same_domain",
                    "relationship_score": 0.8,
                    "metadata": {"domain": domain},
                }
            )

            if len(results) >= limit:
                break

        return results
    except Exception as e:
        logger.error(f"Failed to find entities by domain: {e}")
        return []


async def _find_entities_by_similar_name(
    entity_id: str, friendly_name: str | None, limit: int = 10
) -> list[dict[str, Any]]:
    """
    Find entities with similar names.

    Args:
        entity_id: The entity ID to find similar entities for
        friendly_name: The friendly name to search for
        limit: Maximum number of results

    Returns:
        List of entities with similar names with relationship metadata
    """
    if not friendly_name:
        return []

    try:
        # Split friendly name into words and search
        name_words = friendly_name.lower().split()
        if not name_words:
            return []

        # Get all entities
        entities = await get_entities(lean=True)
        if isinstance(entities, dict) and "error" in entities:
            return []

        results = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue

            current_entity_id = entity.get("entity_id", "")
            if current_entity_id == entity_id:
                continue

            entity_friendly_name = entity.get("attributes", {}).get("friendly_name", "")
            if not entity_friendly_name:
                continue

            # Calculate name similarity
            entity_name_words = set(entity_friendly_name.lower().split())
            common_words = set(name_words).intersection(entity_name_words)

            if common_words:
                # Calculate similarity score
                similarity_score = len(common_words) / max(len(name_words), len(entity_name_words))

                results.append(
                    {
                        "entity_id": current_entity_id,
                        "entity": entity,
                        "relationship_type": "similar_name",
                        "relationship_score": similarity_score,
                        "metadata": {
                            "common_words": list(common_words),
                            "similarity": similarity_score,
                        },
                    }
                )

        # Sort by similarity score
        results.sort(key=lambda x: x["relationship_score"], reverse=True)

        return results[:limit]
    except Exception as e:
        logger.error(f"Failed to find entities by similar name: {e}")
        return []


async def _find_entities_by_vector_similarity(
    entity_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """
    Find entities with similar capabilities using vector embeddings.

    Args:
        entity_id: The entity ID to find similar entities for
        limit: Maximum number of results

    Returns:
        List of similar entities with relationship metadata
    """
    config = get_vectordb_config()
    if not config.is_enabled():
        logger.debug("Vector DB is disabled, skipping vector similarity search")
        return []

    try:
        manager = get_vectordb_manager()
        if not manager._initialized:
            await manager.initialize()

        # Get entity embedding from vector DB
        # We'll use the entity_id as the document ID in the collection
        try:
            # Search for similar entities
            entity = await get_entity_state(entity_id, lean=True)
            if isinstance(entity, dict) and "error" in entity:
                return []

            # Generate search text from entity
            friendly_name = entity.get("attributes", {}).get("friendly_name", "")
            domain = entity_id.split(".")[0] if "." in entity_id else ""
            search_text = f"{friendly_name} {domain}"

            # Search vectors
            similar_results = await manager.search_vectors(
                collection_name=ENTITY_COLLECTION,
                query_text=search_text,
                limit=limit + 1,  # Get one extra to exclude self
                filter_metadata=None,
            )

            results = []
            for result in similar_results:
                result_entity_id = result.get("id") or result.get("entity_id")
                if not result_entity_id or result_entity_id == entity_id:
                    continue

                # Convert distance to similarity score
                distance = result.get("distance", 0.0)
                similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

                try:
                    similar_entity = await get_entity_state(result_entity_id, lean=True)
                    if isinstance(similar_entity, dict) and "error" not in similar_entity:
                        results.append(
                            {
                                "entity_id": result_entity_id,
                                "entity": similar_entity,
                                "relationship_type": "similar_capabilities",
                                "relationship_score": similarity_score,
                                "metadata": {
                                    "vector_similarity": similarity_score,
                                    "distance": distance,
                                },
                            }
                        )
                except Exception as e:
                    logger.debug(f"Failed to get entity {result_entity_id}: {e}")
                    continue

                if len(results) >= limit:
                    break

            return results
        except Exception as e:
            logger.debug(f"Vector search failed: {e}")
            return []
    except Exception as e:
        logger.error(f"Failed to find entities by vector similarity: {e}")
        return []


def _rank_and_deduplicate(
    all_suggestions: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    """
    Rank suggestions and remove duplicates.

    Args:
        all_suggestions: List of all suggestions from different sources
        limit: Maximum number of suggestions to return

    Returns:
        Ranked and deduplicated list of suggestions
    """
    # Use a dictionary to deduplicate by entity_id
    suggestion_map: dict[str, dict[str, Any]] = {}

    for suggestion in all_suggestions:
        entity_id = suggestion.get("entity_id")
        if not entity_id:
            continue

        if entity_id in suggestion_map:
            # Keep the one with higher score
            existing_score = suggestion_map[entity_id].get("relationship_score", 0.0)
            new_score = suggestion.get("relationship_score", 0.0)
            if new_score > existing_score:
                suggestion_map[entity_id] = suggestion
        else:
            suggestion_map[entity_id] = suggestion

    # Convert to list and sort by score
    ranked_suggestions = list(suggestion_map.values())
    ranked_suggestions.sort(key=lambda x: x.get("relationship_score", 0.0), reverse=True)

    return ranked_suggestions[:limit]


def _build_suggestion_explanation(suggestion: dict[str, Any]) -> str:
    """
    Build explanation for a suggestion.

    Args:
        suggestion: Suggestion dictionary

    Returns:
        Human-readable explanation
    """
    entity = suggestion.get("entity", {})
    relationship_type = suggestion.get("relationship_type", "")
    relationship_score = suggestion.get("relationship_score", 0.0)

    friendly_name = entity.get("attributes", {}).get("friendly_name", "")
    entity_id = suggestion.get("entity_id", "")
    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

    parts = []
    if friendly_name:
        parts.append(f'"{friendly_name}"')
    else:
        parts.append(f'"{entity_id}"')

    parts.append(f"({domain})")

    # Add relationship-specific explanation
    if relationship_type == "same_area":
        area_id = suggestion.get("metadata", {}).get("area_id", "")
        parts.append(f'in the same area "{area_id}"')
    elif relationship_type == "same_device":
        parts.append("from the same device")
    elif relationship_type == "same_domain":
        parts.append("of the same type")
    elif relationship_type == "similar_name":
        common_words = suggestion.get("metadata", {}).get("common_words", [])
        if common_words:
            parts.append(f"with similar name (common: {', '.join(common_words)})")
        else:
            parts.append("with similar name")
    elif relationship_type == "similar_capabilities":
        similarity = suggestion.get("metadata", {}).get("vector_similarity", 0.0)
        parts.append(f"with similar capabilities ({similarity:.1%} similarity)")

    # Add score
    parts.append(f"(score: {relationship_score:.2f})")

    return " ".join(parts)


@handle_api_errors
async def get_entity_suggestions(
    entity_id: str,
    relationship_types: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Get context-aware suggestions for an entity.

    Args:
        entity_id: The entity to get suggestions for
        relationship_types: Types of relationships to consider. If None, uses all types.
                          Supported types: same_area, same_device, same_domain,
                          similar_name, similar_capabilities
        limit: Maximum number of suggestions to return

    Returns:
        List of suggested entities with relationship information:
        - entity_id: The entity ID
        - entity: Entity state dictionary
        - relationship_type: Type of relationship (e.g., "same_area")
        - relationship_score: Score indicating strength of relationship (0.0-1.0)
        - explanation: Human-readable explanation
        - metadata: Additional relationship metadata

    Example:
        >>> suggestions = await get_entity_suggestions("light.living_room")
        >>> for suggestion in suggestions:
        ...     print(suggestion["explanation"])
    """
    # Get entity metadata
    try:
        entity = await get_entity_state(entity_id, lean=True)
        if isinstance(entity, dict) and "error" in entity:
            return [{"error": f"Entity {entity_id} not found"}]
    except Exception as e:
        logger.error(f"Failed to get entity {entity_id}: {e}")
        return [{"error": f"Failed to get entity {entity_id}: {e}"}]

    # Default to all relationship types if not specified
    if relationship_types is None:
        relationship_types = [
            "same_area",
            "same_device",
            "same_domain",
            "similar_name",
            "similar_capabilities",
        ]

    # Extract entity metadata
    attributes = entity.get("attributes", {})
    area_id = attributes.get("area_id")
    device_id = attributes.get("device_id")
    domain = entity_id.split(".")[0] if "." in entity_id else None
    friendly_name = attributes.get("friendly_name")

    # Collect suggestions from different sources
    all_suggestions = []

    # Same area
    if "same_area" in relationship_types:
        area_suggestions = await _find_entities_by_area(area_id, entity_id)
        all_suggestions.extend(area_suggestions)

    # Same device
    if "same_device" in relationship_types:
        device_suggestions = await _find_entities_by_device(device_id, entity_id)
        all_suggestions.extend(device_suggestions)

    # Same domain
    if "same_domain" in relationship_types:
        domain_suggestions = await _find_entities_by_domain(domain, entity_id, limit)
        all_suggestions.extend(domain_suggestions)

    # Similar name
    if "similar_name" in relationship_types:
        name_suggestions = await _find_entities_by_similar_name(
            entity_id, friendly_name, limit
        )
        all_suggestions.extend(name_suggestions)

    # Similar capabilities (vector similarity)
    if "similar_capabilities" in relationship_types:
        vector_suggestions = await _find_entities_by_vector_similarity(entity_id, limit)
        all_suggestions.extend(vector_suggestions)

    # Rank and deduplicate
    ranked_suggestions = _rank_and_deduplicate(all_suggestions, limit)

    # Add explanations
    for suggestion in ranked_suggestions:
        suggestion["explanation"] = _build_suggestion_explanation(suggestion)

    return ranked_suggestions
