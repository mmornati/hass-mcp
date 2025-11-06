"""Performance tests for vector DB operations."""

import time

import pytest

from app.core.vectordb.indexing import index_entities
from app.core.vectordb.manager import get_vectordb_manager
from app.core.vectordb.search import semantic_search


@pytest.mark.performance
@pytest.mark.asyncio
async def test_indexing_performance():
    """Benchmark entity indexing performance."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities or len(entities) < 10:
        pytest.skip("Not enough entities available for performance test")

    # Test with different batch sizes
    batch_sizes = [10, 50, 100]
    entity_ids = [e["entity_id"] for e in entities[:100]]

    for batch_size in batch_sizes:
        batch = entity_ids[:batch_size]

        start_time = time.time()
        result = await index_entities(batch)
        elapsed_time = time.time() - start_time

        assert result["succeeded"] > 0
        # Log performance metrics
        entities_per_second = result["succeeded"] / elapsed_time if elapsed_time > 0 else 0
        print(f"\nBatch size: {batch_size}, Entities indexed: {result['succeeded']}")
        print(f"Time: {elapsed_time:.2f}s, Rate: {entities_per_second:.2f} entities/s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_search_performance():
    """Benchmark search performance."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index some entities
    entity_ids = [e["entity_id"] for e in entities[:50]]
    await index_entities(entity_ids)

    # Test search performance with different queries
    queries = ["light", "sensor", "temperature", "switch", "climate"]

    for query in queries:
        start_time = time.time()
        results = await semantic_search(query, limit=10)
        elapsed_time = time.time() - start_time

        assert isinstance(results, list)
        # Log performance metrics
        print(f"\nQuery: '{query}', Results: {len(results)}")
        print(f"Time: {elapsed_time:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_embedding_generation_performance():
    """Benchmark embedding generation performance."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Test with different text lengths
    texts = [
        "light",
        "Living room light",
        "Living room light in the main area",
        "Living room light in the main area with dimming capability",
    ]

    for text in texts:
        start_time = time.time()
        embeddings = await manager.embed_texts([text])
        elapsed_time = time.time() - start_time

        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0
        # Log performance metrics
        print(f"\nText length: {len(text)} chars")
        print(f"Time: {elapsed_time:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent vector DB operations."""
    import asyncio

    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    # Ensure we have some entities indexed
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Index some entities
    entity_ids = [e["entity_id"] for e in entities[:20]]
    await index_entities(entity_ids)

    # Perform concurrent searches
    queries = ["light", "sensor", "temperature", "switch", "climate"]

    start_time = time.time()
    tasks = [semantic_search(query, limit=5) for query in queries]
    results = await asyncio.gather(*tasks)
    elapsed_time = time.time() - start_time

    assert len(results) == len(queries)
    # Log performance metrics
    print(f"\nConcurrent searches: {len(queries)}")
    print(f"Time: {elapsed_time:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_large_entity_set():
    """Test with large entity sets (1000+ entities)."""
    manager = get_vectordb_manager()
    if not manager.config.is_enabled():
        pytest.skip("Vector DB is not enabled")

    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities or len(entities) < 100:
        pytest.skip("Not enough entities available for large set test")

    # Use up to 1000 entities
    entity_ids = [e["entity_id"] for e in entities[:1000]]

    start_time = time.time()
    result = await index_entities(entity_ids)
    elapsed_time = time.time() - start_time

    assert result["succeeded"] > 0
    # Log performance metrics
    entities_per_second = result["succeeded"] / elapsed_time if elapsed_time > 0 else 0
    print(f"\nLarge entity set: {len(entity_ids)} entities")
    print(f"Indexed: {result['succeeded']}, Failed: {result['failed']}")
    print(f"Time: {elapsed_time:.2f}s, Rate: {entities_per_second:.2f} entities/s")
