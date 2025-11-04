"""Unit tests for cache statistics API endpoint (US-007)."""

from unittest.mock import patch

import pytest

from app.api.system import get_cache_statistics
from app.core.cache.manager import get_cache_manager
from app.core.cache.metrics import get_cache_metrics


@pytest.fixture(autouse=True)
async def clear_cache_and_metrics():
    """Clear cache and reset metrics before each test."""
    cache = await get_cache_manager()
    metrics = get_cache_metrics()
    await cache.clear()
    metrics.reset()
    yield
    await cache.clear()
    metrics.reset()


@pytest.mark.skip(
    reason="Temporarily skipping all tests in this class due to hanging issue with async fixtures in pytest-asyncio"
)
class TestGetCacheStatistics:
    """Test get_cache_statistics API endpoint."""

    @pytest.mark.asyncio
    async def test_get_cache_statistics_basic(self):
        """Test basic cache statistics retrieval."""
        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            assert isinstance(result, dict)
            assert "cache_enabled" in result
            assert "backend" in result
            assert "statistics" in result
            assert "per_endpoint" in result
            assert "top_endpoints" in result
            assert "health" in result

    @pytest.mark.asyncio
    async def test_get_cache_statistics_structure(self):
        """Test cache statistics structure."""
        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            # Check statistics structure
            stats = result["statistics"]
            assert "total_hits" in stats
            assert "total_misses" in stats
            assert "total_sets" in stats
            assert "total_deletes" in stats
            assert "total_invalidations" in stats
            assert "total_requests" in stats
            assert "hit_rate" in stats
            assert "uptime_seconds" in stats
            assert "performance" in stats
            assert "endpoint_count" in stats

            # Check performance structure
            performance = stats["performance"]
            assert "avg_api_time_ms" in performance
            assert "avg_cache_time_ms" in performance
            assert "time_saved_ms" in performance
            assert "total_api_calls" in performance
            assert "total_cache_calls" in performance

            # Check health structure
            health = result["health"]
            assert "status" in health
            assert "backend_available" in health

    @pytest.mark.asyncio
    async def test_get_cache_statistics_with_data(self):
        """Test cache statistics with actual cache operations."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Perform some cache operations
        await cache.set("test_key", "test_value", endpoint="entities:get_entities")
        await cache.get("test_key", endpoint="entities:get_entities")
        await cache.get("nonexistent_key", endpoint="entities:get_entities")
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            assert result["statistics"]["total_hits"] == 1
            assert result["statistics"]["total_misses"] == 1
            assert result["statistics"]["total_sets"] == 1
            assert result["statistics"]["total_requests"] == 2
            assert result["statistics"]["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_cache_statistics_per_endpoint(self):
        """Test per-endpoint statistics."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Perform operations for different endpoints
        await cache.set("key1", "value1", endpoint="entities:get_entities")
        await cache.set("key2", "value2", endpoint="automations:get_automations")
        await cache.get("key1", endpoint="entities:get_entities")
        await cache.get("key2", endpoint="automations:get_automations")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            per_endpoint = result["per_endpoint"]
            assert "entities:get_entities" in per_endpoint
            assert "automations:get_automations" in per_endpoint

            entities_stats = per_endpoint["entities:get_entities"]
            assert entities_stats["hits"] == 1
            assert entities_stats["sets"] == 1

    @pytest.mark.asyncio
    async def test_get_cache_statistics_top_endpoints(self):
        """Test top endpoints statistics."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Create multiple endpoints with different hit counts
        for i in range(5):
            await cache.set(f"key{i}", f"value{i}", endpoint="entities:get_entities")
            await cache.get(f"key{i}", endpoint="entities:get_entities")

        for i in range(3):
            await cache.set(f"key{i}", f"value{i}", endpoint="automations:get_automations")
            await cache.get(f"key{i}", endpoint="automations:get_automations")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            top_endpoints = result["top_endpoints"]
            assert "by_hits" in top_endpoints
            assert "by_time_saved" in top_endpoints
            assert "by_hit_rate" in top_endpoints

            # Check that entities:get_entities has more hits
            top_by_hits = top_endpoints["by_hits"]
            assert len(top_by_hits) > 0
            assert top_by_hits[0][0] == "entities:get_entities"  # 5 hits

    @pytest.mark.asyncio
    async def test_get_cache_statistics_health(self):
        """Test cache health information."""
        cache = await get_cache_manager()

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            health = result["health"]
            assert health["status"] in ["healthy", "warning", "critical"]
            assert isinstance(health["backend_available"], bool)

            # If backend has size method, check size info
            if cache._backend and hasattr(cache._backend, "size"):
                assert "size_limit" in health
                assert "current_size" in health
                assert "size_usage_percent" in health

    @pytest.mark.asyncio
    async def test_get_cache_statistics_health_warning_near_full(self):
        """Test cache health warning when cache is nearly full."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Fill cache to near capacity (if max_size is available)
        if cache._backend and hasattr(cache._backend, "size"):
            max_size = cache._config.get_max_size()
            # Fill to 91% capacity
            for i in range(int(max_size * 0.91)):
                await cache.set(f"key{i}", f"value{i}")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            health = result["health"]
            if cache._backend and hasattr(cache._backend, "size"):
                current_size = cache._backend.size()
                max_size = cache._config.get_max_size()
                if current_size >= max_size * 0.9:
                    assert health["status"] in ["warning", "critical"]
                    assert "warning" in health

    @pytest.mark.asyncio
    async def test_get_cache_statistics_health_warning_low_hit_rate(self):
        """Test cache health warning when hit rate is low."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Create many misses and few hits
        for _ in range(10):
            await cache.get("nonexistent_key", endpoint="test:endpoint")
        for _ in range(2):
            await cache.set("key", "value", endpoint="test:endpoint")
            await cache.get("key", endpoint="test:endpoint")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            # Check that hit rate is low
            hit_rate = result["statistics"]["hit_rate"]
            if hit_rate < 0.5:
                health = result["health"]
                assert health["status"] in ["warning", "critical"]
                assert "warning" in health

    @pytest.mark.asyncio
    async def test_get_cache_statistics_performance_metrics(self):
        """Test performance metrics in statistics."""
        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Record some API calls and cache operations
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)
        metrics.record_api_call("entities:get_entities", api_time_ms=60.0)
        metrics.record_hit("entities:get_entities", cache_time_ms=1.0)
        metrics.record_hit("entities:get_entities", cache_time_ms=1.5)

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await get_cache_statistics()

            performance = result["statistics"]["performance"]
            assert performance["total_api_calls"] == 2
            assert performance["total_cache_calls"] == 2
            assert performance["avg_api_time_ms"] == 55.0  # (50 + 60) / 2
            assert performance["avg_cache_time_ms"] == 1.25  # (1.0 + 1.5) / 2
            assert performance["time_saved_ms"] > 0  # Should be positive
