"""Integration tests for entity indexing."""

import pytest

from app.core.vectordb.indexing import (
    get_indexing_status,
    index_entities,
    index_entity,
    remove_entity_from_index,
    update_entity_index,
)
from app.core.vectordb.manager import get_vectordb_manager


@pytest.mark.integration
@pytest.mark.asyncio
async def test_index_single_entity():
    """Test indexing a single entity."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Get a real entity
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    entity_id = entities[0]["entity_id"]

    # Index the entity
    result = await index_entity(entity_id)
    assert result["success"] is True
    assert result["entity_id"] == entity_id

    # Check indexing status
    status = await get_indexing_status()
    assert status["total_indexed"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_index_multiple_entities():
    """Test indexing multiple entities."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Get real entities
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities or len(entities) < 2:
        pytest.skip("Not enough entities available")

    entity_ids = [e["entity_id"] for e in entities[:5]]  # Index up to 5 entities

    # Index entities
    result = await index_entities(entity_ids)
    assert result["total"] == len(entity_ids)
    assert result["succeeded"] >= 1  # At least one should succeed

    # Check indexing status
    status = await get_indexing_status()
    assert status["total_indexed"] >= result["succeeded"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_index():
    """Test updating an indexed entity."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Get a real entity
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    entity_id = entities[0]["entity_id"]

    # First index the entity
    await index_entity(entity_id)

    # Update the index
    result = await update_entity_index(entity_id)
    assert result["success"] is True
    assert result["entity_id"] == entity_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_entity_from_index():
    """Test removing an entity from the index."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Get a real entity
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    entity_id = entities[0]["entity_id"]

    # First index the entity
    await index_entity(entity_id)

    # Get initial status
    status_before = await get_indexing_status()
    total_before = status_before["total_indexed"]

    # Remove from index
    result = await remove_entity_from_index(entity_id)
    assert result["success"] is True
    assert result["entity_id"] == entity_id

    # Check status decreased
    status_after = await get_indexing_status()
    assert status_after["total_indexed"] < total_before


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_indexing_status():
    """Test getting indexing status."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    status = await get_indexing_status()
    assert "total_indexed" in status
    assert "collection_name" in status
    assert isinstance(status["total_indexed"], int)
    assert status["total_indexed"] >= 0
