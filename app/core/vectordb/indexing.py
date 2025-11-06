"""Entity indexing module for hass-mcp.

This module provides functionality for generating entity embeddings and indexing
them in the vector database for semantic search.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.api.areas import get_areas
from app.api.devices import get_device_details
from app.api.entities import get_entities, get_entity_state
from app.core.vectordb.description import (
    generate_entity_description_enhanced,
)
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

logger = logging.getLogger(__name__)

# Collection name for entity embeddings
ENTITY_COLLECTION = "entities"


async def get_area_name(area_id: str) -> str | None:
    """
    Get area name from area_id.

    Args:
        area_id: The area ID to get name for

    Returns:
        Area name if found, None otherwise
    """
    try:
        areas = await get_areas()
        if isinstance(areas, list):
            for area in areas:
                if area.get("area_id") == area_id:
                    return area.get("name")
    except Exception as e:
        logger.debug(f"Could not get area name for {area_id}: {e}")
    return None


def generate_entity_description(  # noqa: PLR0915
    entity: dict[str, Any], area_name: str | None = None, device_info: dict[str, Any] | None = None
) -> str:
    """
    Generate rich description for entity embedding.

    Args:
        entity: Entity state dictionary
        area_name: Optional area name
        device_info: Optional device information dictionary

    Returns:
        Rich text description of the entity
    """
    parts = []

    # Friendly name
    friendly_name = entity.get("attributes", {}).get("friendly_name", "")
    if friendly_name:
        parts.append(friendly_name)
    else:
        # Fall back to entity_id if no friendly name
        entity_id = entity.get("entity_id", "")
        parts.append(entity_id.replace("_", " ").replace(".", " ").title())

    # Domain type
    entity_id = entity.get("entity_id", "")
    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
    parts.append(f"{domain} entity")

    # Area/room
    if area_name:
        parts.append(f"in the {area_name} area")
    else:
        # Try to get area from attributes
        area_id = entity.get("attributes", {}).get("area_id")
        if area_id:
            parts.append(f"in area {area_id}")

    # Device information
    if device_info:
        manufacturer = device_info.get("manufacturer")
        model = device_info.get("model")
        if manufacturer and model:
            parts.append(f"({manufacturer} {model})")
        elif manufacturer:
            parts.append(f"({manufacturer})")
        elif model:
            parts.append(f"({model})")

    # Domain-specific capabilities
    attributes = entity.get("attributes", {})
    if domain == "light":
        supported_color_modes = attributes.get("supported_color_modes", [])
        if supported_color_modes:
            modes_str = ", ".join(supported_color_modes)
            parts.append(f"Supports {modes_str}")
        brightness = attributes.get("brightness")
        if brightness is not None:
            parts.append("brightness control")
        color_temp = attributes.get("color_temp")
        if color_temp is not None:
            parts.append("color temperature control")
    elif domain == "sensor":
        device_class = attributes.get("device_class", "")
        unit = attributes.get("unit_of_measurement", "")
        if device_class:
            parts.append(f"{device_class} sensor")
        if unit:
            parts.append(f"measured in {unit}")
    elif domain == "switch" or domain == "input_boolean":
        parts.append("switch entity")
    elif domain == "climate":
        current_temp = attributes.get("current_temperature")
        target_temp = attributes.get("temperature")
        hvac_mode = attributes.get("hvac_mode", "")
        if current_temp is not None:
            parts.append(f"current temperature {current_temp}")
        if target_temp is not None:
            parts.append(f"target temperature {target_temp}")
        if hvac_mode:
            parts.append(f"mode {hvac_mode}")

    # Current state
    state = entity.get("state", "unknown")
    if state not in ("unknown", "unavailable"):
        parts.append(f"Currently {state}")

    # Join parts
    description = ". ".join(parts)
    if not description.endswith("."):
        description += "."

    return description


async def generate_entity_metadata(entity: dict[str, Any]) -> dict[str, Any]:
    """
    Generate metadata dictionary for entity vector.

    Args:
        entity: Entity state dictionary

    Returns:
        Metadata dictionary for vector storage
    """
    entity_id = entity.get("entity_id", "")
    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
    attributes = entity.get("attributes", {})

    metadata = {
        "entity_id": entity_id,
        "domain": domain,
        "friendly_name": attributes.get("friendly_name", ""),
        "area_id": attributes.get("area_id"),
        "device_id": attributes.get("device_id"),
        "device_class": attributes.get("device_class"),
        "last_updated": entity.get("last_updated", datetime.now(UTC).isoformat()),
        "indexed_at": datetime.now(UTC).isoformat(),
    }

    # Add device information if available
    if attributes.get("device_id"):
        try:
            device_info = await get_device_details(attributes["device_id"])
            if device_info and (not isinstance(device_info, dict) or "error" not in device_info):
                metadata["manufacturer"] = device_info.get("manufacturer")
                metadata["model"] = device_info.get("model")
        except Exception as e:
            logger.debug(f"Could not get device info for {attributes['device_id']}: {e}")

    return metadata


async def index_entity(entity_id: str, manager: VectorDBManager | None = None) -> dict[str, Any]:
    """
    Index a single entity in the vector database.

    Args:
        entity_id: The entity ID to index
        manager: Optional VectorDBManager instance. If None, uses global manager.

    Returns:
        Dictionary with indexing result:
        - entity_id: The entity ID indexed
        - success: Boolean indicating if indexing succeeded
        - description: Generated description
        - error: Error message if indexing failed
    """
    manager = manager or get_vectordb_manager()

    if not manager.config.is_enabled():
        return {
            "entity_id": entity_id,
            "success": False,
            "error": "Vector DB is disabled",
        }

    try:
        # Get entity state
        entity = await get_entity_state(entity_id, lean=False)
        if isinstance(entity, dict) and "error" in entity:
            return {
                "entity_id": entity_id,
                "success": False,
                "error": entity.get("error", "Unknown error"),
            }

        # Get area name if available
        area_name = None
        area_id = entity.get("attributes", {}).get("area_id")
        if area_id:
            try:
                area_name = await get_area_name(area_id)
            except Exception as e:
                logger.debug(f"Could not get area name for {area_id}: {e}")

        # Get device info if available
        device_info = None
        device_id = entity.get("attributes", {}).get("device_id")
        if device_id:
            try:
                device_info = await get_device_details(device_id)
                if isinstance(device_info, dict) and "error" in device_info:
                    device_info = None
            except Exception as e:
                logger.debug(f"Could not get device info for {device_id}: {e}")

        # Generate description using enhanced version
        description = await generate_entity_description_enhanced(
            entity, area_name=area_name, device_info=device_info, use_template=True
        )

        # Generate metadata
        metadata = await generate_entity_metadata(entity)

        # Ensure collection exists
        if not await manager.collection_exists(ENTITY_COLLECTION):
            await manager.create_collection(ENTITY_COLLECTION)

        # Add vector to collection
        await manager.add_vectors(
            collection_name=ENTITY_COLLECTION,
            texts=[description],
            ids=[entity_id],
            metadata=[metadata],
        )

        logger.debug(f"Indexed entity: {entity_id}")
        return {
            "entity_id": entity_id,
            "success": True,
            "description": description,
        }
    except Exception as e:
        logger.error(f"Failed to index entity {entity_id}: {e}")
        return {
            "entity_id": entity_id,
            "success": False,
            "error": str(e),
        }


async def index_entities(
    entity_ids: list[str] | None = None,
    batch_size: int = 100,
    manager: VectorDBManager | None = None,
) -> dict[str, Any]:
    """
    Index multiple entities in batches.

    Args:
        entity_ids: Optional list of entity IDs to index. If None, indexes all entities.
        batch_size: Number of entities to process in each batch
        manager: Optional VectorDBManager instance. If None, uses global manager.

    Returns:
        Dictionary with indexing results:
        - total: Total number of entities processed
        - succeeded: Number of successfully indexed entities
        - failed: Number of failed entities
        - results: List of individual indexing results
    """
    manager = manager or get_vectordb_manager()

    if not manager.config.is_enabled():
        return {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "results": [],
            "error": "Vector DB is disabled",
        }

    # Get entity IDs if not provided
    if entity_ids is None:
        entities = await get_entities()
        if isinstance(entities, list):
            entity_ids = [entity["entity_id"] for entity in entities]
        else:
            return {
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "results": [],
                "error": "Failed to get entities",
            }

    total = len(entity_ids)
    succeeded = 0
    failed = 0
    results = []

    # Process in batches
    for i in range(0, total, batch_size):
        batch = entity_ids[i : i + batch_size]
        logger.info(f"Indexing batch {i // batch_size + 1} ({len(batch)} entities)")

        for entity_id in batch:
            result = await index_entity(entity_id, manager)
            results.append(result)
            if result.get("success"):
                succeeded += 1
            else:
                failed += 1

    logger.info(f"Indexing complete: {succeeded} succeeded, {failed} failed out of {total} total")
    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


async def update_entity_index(
    entity_id: str, manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Update an existing entity in the index.

    Args:
        entity_id: The entity ID to update
        manager: Optional VectorDBManager instance. If None, uses global manager.

    Returns:
        Dictionary with update result
    """
    # For now, we just re-index the entity
    # This will upsert the vector in Chroma
    return await index_entity(entity_id, manager)


async def remove_entity_from_index(
    entity_id: str, manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Remove an entity from the index.

    Args:
        entity_id: The entity ID to remove
        manager: Optional VectorDBManager instance. If None, uses global manager.

    Returns:
        Dictionary with removal result
    """
    manager = manager or get_vectordb_manager()

    if not manager.config.is_enabled():
        return {
            "entity_id": entity_id,
            "success": False,
            "error": "Vector DB is disabled",
        }

    try:
        await manager.delete_vectors(ENTITY_COLLECTION, [entity_id])
        logger.debug(f"Removed entity from index: {entity_id}")
        return {
            "entity_id": entity_id,
            "success": True,
        }
    except Exception as e:
        logger.error(f"Failed to remove entity {entity_id} from index: {e}")
        return {
            "entity_id": entity_id,
            "success": False,
            "error": str(e),
        }


async def get_indexing_status(manager: VectorDBManager | None = None) -> dict[str, Any]:
    """
    Get indexing status for the entity collection.

    Args:
        manager: Optional VectorDBManager instance. If None, uses global manager.

    Returns:
        Dictionary with indexing status:
        - collection_exists: Whether the collection exists
        - total_entities: Total number of indexed entities
        - dimensions: Vector dimensions
        - metadata: Collection metadata
    """
    manager = manager or get_vectordb_manager()

    if not manager.config.is_enabled():
        return {
            "collection_exists": False,
            "total_entities": 0,
            "dimensions": 0,
            "metadata": {},
            "error": "Vector DB is disabled",
        }

    try:
        if not await manager.collection_exists(ENTITY_COLLECTION):
            return {
                "collection_exists": False,
                "total_entities": 0,
                "dimensions": 0,
                "metadata": {},
            }

        stats = await manager.get_collection_stats(ENTITY_COLLECTION)
        return {
            "collection_exists": True,
            "total_entities": stats.get("count", 0),
            "dimensions": stats.get("dimensions", 0),
            "metadata": stats.get("metadata", {}),
        }
    except Exception as e:
        logger.error(f"Failed to get indexing status: {e}")
        return {
            "collection_exists": False,
            "total_entities": 0,
            "dimensions": 0,
            "metadata": {},
            "error": str(e),
        }
