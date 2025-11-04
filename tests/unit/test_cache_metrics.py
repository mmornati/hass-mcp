"""Unit tests for cache metrics (US-007)."""

import pytest

from app.core.cache.manager import get_cache_manager
from app.core.cache.metrics import CacheMetrics, EndpointStats, get_cache_metrics


class TestEndpointStats:
    """Test EndpointStats class."""

    def test_endpoint_stats_initialization(self):
        """Test that EndpointStats initializes with default values."""
        stats = EndpointStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.total_api_time_ms == 0.0
        assert stats.total_cache_time_ms == 0.0
        assert stats.api_call_count == 0
        assert stats.cache_call_count == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = EndpointStats()
        assert stats.hit_rate() == 0.0  # No requests

        stats.hits = 10
        stats.misses = 5
        assert stats.hit_rate() == 10 / 15  # 0.667

        stats.hits = 100
        stats.misses = 0
        assert stats.hit_rate() == 1.0  # 100%

    def test_avg_api_time_calculation(self):
        """Test average API time calculation."""
        stats = EndpointStats()
        assert stats.avg_api_time_ms() == 0.0  # No calls

        stats.api_call_count = 2
        stats.total_api_time_ms = 100.0
        assert stats.avg_api_time_ms() == 50.0

    def test_avg_cache_time_calculation(self):
        """Test average cache time calculation."""
        stats = EndpointStats()
        assert stats.avg_cache_time_ms() == 0.0  # No calls

        stats.cache_call_count = 3
        stats.total_cache_time_ms = 6.0
        assert stats.avg_cache_time_ms() == 2.0

    def test_time_saved_calculation(self):
        """Test time saved calculation."""
        stats = EndpointStats()
        assert stats.time_saved_ms() == 0.0  # No calls

        stats.api_call_count = 10
        stats.total_api_time_ms = 500.0  # 50ms avg
        stats.cache_call_count = 5
        stats.total_cache_time_ms = 5.0  # 1ms avg
        assert stats.time_saved_ms() == 49.0  # 50 - 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = EndpointStats()
        stats.hits = 10
        stats.misses = 5
        stats.sets = 3
        stats.deletes = 1
        stats.api_call_count = 5
        stats.total_api_time_ms = 250.0
        stats.cache_call_count = 10
        stats.total_cache_time_ms = 10.0

        result = stats.to_dict()
        assert result["hits"] == 10
        assert result["misses"] == 5
        assert result["sets"] == 3
        assert result["deletes"] == 1
        assert result["hit_rate"] == round(10 / 15, 3)
        assert result["avg_api_time_ms"] == 50.0
        assert result["avg_cache_time_ms"] == 1.0
        assert result["time_saved_ms"] == 49.0
        assert result["api_call_count"] == 5
        assert result["cache_call_count"] == 10


class TestCacheMetrics:
    """Test CacheMetrics class."""

    @pytest.fixture(autouse=True)
    def reset_metrics(self):
        """Reset metrics before each test in this class."""
        from app.core.cache.metrics import get_cache_metrics

        metrics = get_cache_metrics()
        metrics.reset()
        yield
        metrics.reset()

    def test_initialization(self):
        """Test that CacheMetrics initializes correctly."""
        metrics = CacheMetrics()
        assert metrics.get_total_hits() == 0
        assert metrics.get_total_misses() == 0
        assert metrics.get_total_sets() == 0
        assert metrics.get_total_deletes() == 0
        assert metrics.get_total_invalidations() == 0
        assert metrics.hit_rate() == 0.0

    def test_record_hit(self):
        """Test recording a cache hit."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities", cache_time_ms=1.5)
        assert metrics.get_total_hits() == 1
        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.hits == 1
        assert stats.misses == 0
        assert stats.cache_call_count == 1
        assert stats.total_cache_time_ms == 1.5

    def test_record_miss(self):
        """Test recording a cache miss."""
        metrics = CacheMetrics()
        metrics.record_miss("entities:get_entities")
        assert metrics.get_total_misses() == 1
        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.hits == 0
        assert stats.misses == 1

    def test_record_set(self):
        """Test recording a cache set."""
        metrics = CacheMetrics()
        metrics.record_set("entities:get_entities")
        assert metrics.get_total_sets() == 1
        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.sets == 1

    def test_record_delete(self):
        """Test recording a cache delete."""
        metrics = CacheMetrics()
        metrics.record_delete("entities:get_entities")
        assert metrics.get_total_deletes() == 1
        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.deletes == 1

    def test_record_invalidation(self):
        """Test recording a cache invalidation."""
        metrics = CacheMetrics()
        metrics.record_invalidation("entities:*")
        assert metrics.get_total_invalidations() == 1

    def test_record_api_call(self):
        """Test recording an API call."""
        metrics = CacheMetrics()
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)
        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.api_call_count == 1
        assert stats.total_api_time_ms == 50.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        metrics = CacheMetrics()
        assert metrics.hit_rate() == 0.0  # No requests

        metrics.record_hit("test:endpoint")
        metrics.record_hit("test:endpoint")
        metrics.record_miss("test:endpoint")
        assert metrics.hit_rate() == 2 / 3  # 0.667

    def test_get_endpoint_stats(self):
        """Test getting endpoint statistics."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities", cache_time_ms=1.0)
        metrics.record_miss("entities:get_entities")
        metrics.record_set("entities:get_entities")
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)

        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert isinstance(stats, EndpointStats)
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.sets == 1
        assert stats.total_api_time_ms == 50.0
        assert stats.total_cache_time_ms == 1.0

    def test_get_all_endpoint_stats(self):
        """Test getting all endpoint statistics."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities")
        metrics.record_hit("automations:get_automations")

        all_stats = metrics.get_all_endpoint_stats()
        assert "entities:get_entities" in all_stats
        assert "automations:get_automations" in all_stats
        assert all_stats["entities:get_entities"]["hits"] == 1
        assert all_stats["automations:get_automations"]["hits"] == 1

    def test_get_top_endpoints(self):
        """Test getting top endpoints."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities")
        metrics.record_hit("entities:get_entities")
        metrics.record_hit("automations:get_automations")
        metrics.record_api_call("entities:get_entities", api_time_ms=100.0)
        metrics.record_api_call("automations:get_automations", api_time_ms=50.0)

        # Top by hits
        top = metrics.get_top_endpoints(limit=2, sort_by="hits")
        assert len(top) == 2
        assert top[0][0] == "entities:get_entities"  # 2 hits
        assert top[0][1]["hits"] == 2
        assert top[1][0] == "automations:get_automations"  # 1 hit

        # Top by time saved
        top = metrics.get_top_endpoints(limit=2, sort_by="time_saved_ms")
        assert len(top) == 2

    @pytest.mark.skip(
        reason="Temporarily skipping due to hanging issue with async fixtures in pytest-asyncio"
    )
    def test_get_statistics(self):
        """Test getting complete statistics."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities", cache_time_ms=1.0)
        metrics.record_miss("entities:get_entities")
        metrics.record_set("entities:get_entities")
        metrics.record_delete("entities:get_entities")
        metrics.record_invalidation("entities:*")
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)

        stats = metrics.get_statistics()
        assert stats["total_hits"] == 1
        assert stats["total_misses"] == 1
        assert stats["total_sets"] == 1
        assert stats["total_deletes"] == 1
        assert stats["total_invalidations"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["endpoint_count"] == 1
        assert "uptime_seconds" in stats
        assert "performance" in stats

    def test_reset(self):
        """Test resetting statistics."""
        metrics = CacheMetrics()
        metrics.record_hit("entities:get_entities")
        metrics.record_miss("entities:get_entities")

        assert metrics.get_total_hits() == 1
        assert metrics.get_total_misses() == 1

        metrics.reset()
        assert metrics.get_total_hits() == 0
        assert metrics.get_total_misses() == 0
        assert len(metrics.get_all_endpoint_stats()) == 0


class TestGetCacheMetrics:
    """Test get_cache_metrics function."""

    def test_get_cache_metrics_singleton(self):
        """Test that get_cache_metrics returns a singleton."""
        metrics1 = get_cache_metrics()
        metrics2 = get_cache_metrics()
        assert metrics1 is metrics2

    def test_get_cache_metrics_independent(self):
        """Test that metrics are independent across different instances."""
        # Note: This test might not work as expected if metrics is truly a singleton
        # But it's good to verify the behavior
        metrics1 = get_cache_metrics()
        metrics1.record_hit("test:endpoint")
        assert metrics1.get_total_hits() == 1

        metrics2 = get_cache_metrics()
        assert metrics2.get_total_hits() == 1  # Same instance


class TestCacheMetricsIntegration:
    """Test cache metrics integration with cache manager."""

    @pytest.mark.asyncio
    async def test_cache_manager_records_metrics(self):
        """Test that cache manager records metrics."""
        from app.core.cache.metrics import get_cache_metrics

        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Reset metrics
        metrics.reset()
        await cache.clear()

        # Set a value
        await cache.set("test_key", "test_value", endpoint="test:endpoint")
        assert metrics.get_total_sets() == 1

        # Get the value (hit)
        value = await cache.get("test_key", endpoint="test:endpoint")
        assert value == "test_value"
        assert metrics.get_total_hits() == 1

        # Get a non-existent key (miss)
        value = await cache.get("nonexistent_key", endpoint="test:endpoint")
        assert value is None
        assert metrics.get_total_misses() == 1

        # Delete a key
        await cache.delete("test_key", endpoint="test:endpoint")
        assert metrics.get_total_deletes() == 1

    @pytest.mark.asyncio
    async def test_cache_manager_per_endpoint_metrics(self):
        """Test that cache manager tracks per-endpoint metrics."""
        from app.core.cache.metrics import get_cache_metrics

        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Reset metrics
        metrics.reset()
        await cache.clear()

        # Set values for different endpoints
        await cache.set("key1", "value1", endpoint="entities:get_entities")
        await cache.set("key2", "value2", endpoint="automations:get_automations")

        # Get values
        await cache.get("key1", endpoint="entities:get_entities")
        await cache.get("key2", endpoint="automations:get_automations")

        # Check per-endpoint stats
        stats1 = metrics.get_endpoint_stats("entities:get_entities")
        stats2 = metrics.get_endpoint_stats("automations:get_automations")

        assert stats1.hits == 1
        assert stats1.sets == 1
        assert stats2.hits == 1
        assert stats2.sets == 1

    @pytest.mark.asyncio
    async def test_cache_manager_performance_metrics(self):
        """Test that cache manager tracks performance metrics."""
        from app.core.cache.metrics import get_cache_metrics

        cache = await get_cache_manager()
        metrics = get_cache_metrics()

        # Reset metrics
        metrics.reset()
        await cache.clear()

        # Simulate API call
        metrics.record_api_call("entities:get_entities", api_time_ms=50.0)

        # Simulate cache hit
        metrics.record_hit("entities:get_entities", cache_time_ms=1.0)

        stats = metrics.get_endpoint_stats("entities:get_entities")
        assert stats.avg_api_time_ms() == 50.0
        assert stats.avg_cache_time_ms() == 1.0
        assert stats.time_saved_ms() == 49.0
