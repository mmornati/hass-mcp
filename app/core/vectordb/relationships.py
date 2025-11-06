"""Entity relationship graph module for hass-mcp.

This module provides entity relationship graph construction, storage, and querying
for intelligent entity discovery and context-aware suggestions.
"""

import logging
from typing import Any

from app.api.areas import get_areas
from app.api.automations import get_automations
from app.api.devices import get_device_details, get_devices
from app.api.entities import get_entities
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

logger = logging.getLogger(__name__)

# Collection name for entity relationships
RELATIONSHIPS_COLLECTION = "entity_relationships"

# Relationship types
RELATIONSHIP_TYPES = {
    "in_area": "Entity is in an area",
    "from_device": "Entity is from a device",
    "same_device": "Entities from same device",
    "same_area": "Entities in same area",
    "same_domain": "Entities of same domain",
    "in_automation": "Entity used in automation",
    "device_parent": "Device parent relationship",
    "device_child": "Device child relationship",
}


async def build_relationship_graph(  # noqa: PLR0915
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Build entity relationship graph.

    Args:
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with relationship graph statistics:
        - total_relationships: Total number of relationships
        - relationships_by_type: Count of relationships by type
        - entities_count: Number of entities with relationships
        - areas_count: Number of areas
        - devices_count: Number of devices
        - automations_count: Number of automations
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        logger.debug("Vector DB is disabled, skipping relationship graph construction")
        return {
            "total_relationships": 0,
            "relationships_by_type": {},
            "entities_count": 0,
            "areas_count": 0,
            "devices_count": 0,
            "automations_count": 0,
            "success": False,
            "reason": "Vector DB disabled",
        }

    try:
        # Initialize if needed
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            raise RuntimeError("Vector DB backend not initialized")

        if not manager.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        # Get all entities, areas, devices, and automations
        entities = await get_entities(lean=True)
        areas = await get_areas()
        devices = await get_devices()
        automations = await get_automations()

        # Build relationships
        relationships: list[dict[str, Any]] = []
        relationships_by_type: dict[str, int] = {}

        # Entity → Area relationships
        for entity in entities:
            if not isinstance(entity, dict):
                continue

            entity_id = entity.get("entity_id")
            if not entity_id:
                continue

            area_id = entity.get("attributes", {}).get("area_id")
            if area_id:
                relationship = {
                    "source": entity_id,
                    "target": area_id,
                    "relationship_type": "in_area",
                    "source_type": "entity",
                    "target_type": "area",
                }
                relationships.append(relationship)
                relationships_by_type["in_area"] = relationships_by_type.get("in_area", 0) + 1

        # Entity → Device relationships
        for device in devices:
            if not isinstance(device, dict):
                continue

            device_id = device.get("id")
            if not device_id:
                continue

            device_entities = device.get("entities", [])
            for entity_id in device_entities:
                relationship = {
                    "source": entity_id,
                    "target": device_id,
                    "relationship_type": "from_device",
                    "source_type": "entity",
                    "target_type": "device",
                }
                relationships.append(relationship)
                relationships_by_type["from_device"] = (
                    relationships_by_type.get("from_device", 0) + 1
                )

        # Device → Device relationships (parent/child)
        for device in devices:
            if not isinstance(device, dict):
                continue

            device_id = device.get("id")
            via_device_id = device.get("via_device_id")

            if device_id and via_device_id:
                relationship = {
                    "source": device_id,
                    "target": via_device_id,
                    "relationship_type": "device_parent",
                    "source_type": "device",
                    "target_type": "device",
                }
                relationships.append(relationship)
                relationships_by_type["device_parent"] = (
                    relationships_by_type.get("device_parent", 0) + 1
                )

        # Entity → Automation relationships
        for automation in automations:
            if not isinstance(automation, dict):
                continue

            automation_id = automation.get("entity_id")
            if not automation_id:
                continue

            # Get automation details to find entities used
            try:
                automation_details = await get_device_details(automation_id)
                if isinstance(automation_details, dict):
                    # Extract entities from automation (simplified - would need full automation parsing)
                    # For now, we'll use a placeholder approach
                    pass
            except Exception as e:
                logger.debug(f"Could not get automation details for {automation_id}: {e}")

        # Store relationships in vector DB
        if relationships:
            await _store_relationships(relationships, manager, config)

        return {
            "total_relationships": len(relationships),
            "relationships_by_type": relationships_by_type,
            "entities_count": len(entities) if isinstance(entities, list) else 0,
            "areas_count": len(areas) if isinstance(areas, list) else 0,
            "devices_count": len(devices) if isinstance(devices, list) else 0,
            "automations_count": len(automations) if isinstance(automations, list) else 0,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to build relationship graph: {e}")
        return {
            "total_relationships": 0,
            "relationships_by_type": {},
            "entities_count": 0,
            "areas_count": 0,
            "devices_count": 0,
            "automations_count": 0,
            "success": False,
            "error": str(e),
        }


async def _store_relationships(
    relationships: list[dict[str, Any]],
    manager: VectorDBManager,
    config: VectorDBConfig,
) -> None:
    """
    Store relationships in vector database.

    Args:
        relationships: List of relationship dictionaries
        manager: VectorDBManager instance
        config: VectorDBConfig instance
    """
    try:
        if not manager.backend:
            return

        # Ensure collection exists
        if not await manager.backend.collection_exists(RELATIONSHIPS_COLLECTION):
            await manager.backend.create_collection(RELATIONSHIPS_COLLECTION)

        # Generate embeddings for relationships
        relationship_texts = []
        relationship_ids = []
        relationship_metadata = []

        for relationship in relationships:
            # Create text representation for embedding
            relationship_text = f"{relationship['source']} {relationship['relationship_type']} {relationship['target']}"
            relationship_texts.append(relationship_text)

            # Create unique ID
            relationship_id = f"{relationship['source']}_{relationship['relationship_type']}_{relationship['target']}"
            relationship_ids.append(relationship_id)

            # Store metadata
            relationship_metadata.append(relationship)

        # Generate embeddings
        embeddings = await manager.embed_texts(relationship_texts)

        # Store in vector DB
        await manager.backend.add_vectors(
            collection_name=RELATIONSHIPS_COLLECTION,
            vectors=embeddings,
            ids=relationship_ids,
            metadata=relationship_metadata,
        )

    except Exception as e:
        logger.error(f"Failed to store relationships: {e}")


async def find_entities_by_relationship(
    entity_id: str | None = None,
    relationship_type: str | None = None,
    target: str | None = None,
    limit: int = 50,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Find entities by relationship type.

    Args:
        entity_id: Optional source entity ID
        relationship_type: Optional relationship type filter
        target: Optional target ID filter
        limit: Maximum number of results
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of relationships matching the criteria
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return []

    try:
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            return []

        if not await manager.backend.collection_exists(RELATIONSHIPS_COLLECTION):
            return []

        # Build search query
        search_text = ""
        if entity_id:
            search_text += f"{entity_id} "
        if relationship_type:
            search_text += f"{relationship_type} "
        if target:
            search_text += f"{target}"

        if not search_text:
            search_text = "entity relationship"

        # Generate embedding for search
        search_embedding = await manager.embed_texts([search_text])
        search_vector = search_embedding[0]

        # Build metadata filter
        filter_metadata: dict[str, Any] = {}
        if entity_id:
            filter_metadata["source"] = entity_id
        if relationship_type:
            filter_metadata["relationship_type"] = relationship_type
        if target:
            filter_metadata["target"] = target

        # Search relationships
        results = await manager.backend.search_vectors(
            collection_name=RELATIONSHIPS_COLLECTION,
            query_vector=search_vector,
            limit=limit,
            filter_metadata=filter_metadata if filter_metadata else None,
        )

        # Extract relationships from results
        relationships = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata:
                relationships.append(metadata)

        return relationships[:limit]

    except Exception as e:
        logger.error(f"Failed to find entities by relationship: {e}")
        return []


async def get_entities_in_area(
    area_id: str,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[str]:
    """
    Get all entities in an area.

    Args:
        area_id: Area ID
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of entity IDs in the area
    """
    relationships = await find_entities_by_relationship(
        relationship_type="in_area",
        target=area_id,
        manager=manager,
        config=config,
    )

    entity_ids = [rel.get("source") for rel in relationships if rel.get("source")]
    return [eid for eid in entity_ids if eid]


async def get_entities_from_device(
    device_id: str,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[str]:
    """
    Get all entities from a device.

    Args:
        device_id: Device ID
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of entity IDs from the device
    """
    relationships = await find_entities_by_relationship(
        relationship_type="from_device",
        target=device_id,
        manager=manager,
        config=config,
    )

    entity_ids = [rel.get("source") for rel in relationships if rel.get("source")]
    return [eid for eid in entity_ids if eid]


async def get_related_entities(
    entity_id: str,
    relationship_types: list[str] | None = None,
    limit: int = 50,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Get entities related to a given entity.

    Args:
        entity_id: Entity ID to find related entities for
        relationship_types: Optional list of relationship types to filter by
        limit: Maximum number of results
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of related entities with relationship information
    """
    if relationship_types is None:
        relationship_types = ["same_area", "same_device", "same_domain"]

    all_relationships = []

    for relationship_type in relationship_types:
        relationships = await find_entities_by_relationship(
            entity_id=entity_id,
            relationship_type=relationship_type,
            limit=limit,
            manager=manager,
            config=config,
        )
        all_relationships.extend(relationships)

    # Also find relationships where entity is the target
    for relationship_type in relationship_types:
        relationships = await find_entities_by_relationship(
            target=entity_id,
            relationship_type=relationship_type,
            limit=limit,
            manager=manager,
            config=config,
        )
        all_relationships.extend(relationships)

    # Deduplicate and format results
    seen_entities: set[str] = set()
    related_entities = []

    for relationship in all_relationships:
        source = relationship.get("source")
        target = relationship.get("target")

        # Find the related entity (not the original entity_id)
        related_entity_id = None
        if source == entity_id and target != entity_id:
            related_entity_id = target
        elif target == entity_id and source != entity_id:
            related_entity_id = source

        if related_entity_id and related_entity_id not in seen_entities:
            seen_entities.add(related_entity_id)
            related_entities.append(
                {
                    "entity_id": related_entity_id,
                    "relationship_type": relationship.get("relationship_type"),
                    "relationship": relationship,
                }
            )

    return related_entities[:limit]


async def get_relationship_statistics(
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Get relationship graph statistics.

    Args:
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with relationship statistics:
        - total_relationships: Total number of relationships
        - relationships_by_type: Count of relationships by type
        - entities_with_relationships: Number of entities with relationships
        - areas_with_entities: Number of areas with entities
        - devices_with_entities: Number of devices with entities
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return {
            "total_relationships": 0,
            "relationships_by_type": {},
            "entities_with_relationships": 0,
            "areas_with_entities": 0,
            "devices_with_entities": 0,
        }

    try:
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            return {
                "total_relationships": 0,
                "relationships_by_type": {},
                "entities_with_relationships": 0,
                "areas_with_entities": 0,
                "devices_with_entities": 0,
            }

        if not await manager.backend.collection_exists(RELATIONSHIPS_COLLECTION):
            return {
                "total_relationships": 0,
                "relationships_by_type": {},
                "entities_with_relationships": 0,
                "areas_with_entities": 0,
                "devices_with_entities": 0,
            }

        # Get all relationships (simplified - in production, you'd want better querying)
        search_embedding = await manager.embed_texts(["entity relationship"])
        results = await manager.backend.search_vectors(
            collection_name=RELATIONSHIPS_COLLECTION,
            query_vector=search_embedding[0],
            limit=10000,  # Get a large number
        )

        # Calculate statistics
        relationships_by_type: dict[str, int] = {}
        entities_with_relationships: set[str] = set()
        areas_with_entities: set[str] = set()
        devices_with_entities: set[str] = set()

        for result in results:
            metadata = result.get("metadata", {})
            if not metadata:
                continue

            relationship_type = metadata.get("relationship_type")
            if relationship_type:
                relationships_by_type[relationship_type] = (
                    relationships_by_type.get(relationship_type, 0) + 1
                )

            source = metadata.get("source")
            target = metadata.get("target")
            source_type = metadata.get("source_type")
            target_type = metadata.get("target_type")

            if source_type == "entity":
                entities_with_relationships.add(source)
            if target_type == "entity":
                entities_with_relationships.add(target)

            if target_type == "area":
                areas_with_entities.add(target)
            if target_type == "device":
                devices_with_entities.add(target)

        return {
            "total_relationships": len(results),
            "relationships_by_type": relationships_by_type,
            "entities_with_relationships": len(entities_with_relationships),
            "areas_with_entities": len(areas_with_entities),
            "devices_with_entities": len(devices_with_entities),
        }

    except Exception as e:
        logger.error(f"Failed to get relationship statistics: {e}")
        return {
            "total_relationships": 0,
            "relationships_by_type": {},
            "entities_with_relationships": 0,
            "areas_with_entities": 0,
            "devices_with_entities": 0,
        }
