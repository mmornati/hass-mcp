"""Integration tests for semantic search."""

import pytest

from app.core.vectordb.search import semantic_search


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search_basic():
    """Test basic semantic search."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities
    from app.core.vectordb.indexing import index_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index a few entities
    entity_ids = [e["entity_id"] for e in entities[:5]]
    await index_entities(entity_ids)

    # Perform semantic search
    results = await semantic_search("light", limit=10)
    assert isinstance(results, list)
    assert len(results) > 0

    # Check result structure
    result = results[0]
    assert "entity_id" in result
    assert "similarity" in result
    assert "match_reason" in result
    assert 0.0 <= result["similarity"] <= 1.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search_with_domain_filter():
    """Test semantic search with domain filter."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities
    from app.core.vectordb.indexing import index_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index a few entities
    entity_ids = [e["entity_id"] for e in entities[:10]]
    await index_entities(entity_ids)

    # Perform semantic search with domain filter
    results = await semantic_search("light", domain="light", limit=10)
    assert isinstance(results, list)

    # All results should be light entities
    for result in results:
        assert result["domain"] == "light"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search_with_area_filter():
    """Test semantic search with area filter."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities
    from app.core.vectordb.indexing import index_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Get entities with areas
    entities_with_areas = [e for e in entities if e.get("area_id")]
    if not entities_with_areas:
        pytest.skip("No entities with areas available")

    # Index entities
    entity_ids = [e["entity_id"] for e in entities_with_areas[:10]]
    await index_entities(entity_ids)

    # Get an area_id
    area_id = entities_with_areas[0]["area_id"]

    # Perform semantic search with area filter
    results = await semantic_search("sensor", area_id=area_id, limit=10)
    assert isinstance(results, list)

    # All results should be in the specified area
    for result in results:
        assert result.get("area_id") == area_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search_with_similarity_threshold():
    """Test semantic search with similarity threshold."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities
    from app.core.vectordb.indexing import index_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index a few entities
    entity_ids = [e["entity_id"] for e in entities[:10]]
    await index_entities(entity_ids)

    # Perform semantic search with high similarity threshold
    results = await semantic_search("light", similarity_threshold=0.8, limit=10)
    assert isinstance(results, list)

    # All results should meet the similarity threshold
    for result in results:
        assert result["similarity"] >= 0.8


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hybrid_search():
    """Test hybrid search combining semantic and keyword search."""
    from app.core.vectordb.manager import get_vectordb_manager

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities
    from app.core.vectordb.indexing import index_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index a few entities
    entity_ids = [e["entity_id"] for e in entities[:10]]
    await index_entities(entity_ids)

    # Perform hybrid search (default behavior)
    results = await semantic_search("light", limit=10)
    assert isinstance(results, list)
    assert len(results) > 0
