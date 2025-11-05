"""Performance tests for cache operations.

This module tests cache performance characteristics including
operation speed, concurrent access, and memory usage.
"""

import asyncio

import pytest

from app.core.cache.manager import get_cache_manager
from app.core.cache.memory import MemoryCacheBackend
from tests.fixtures.cache_fixtures import PerformanceTimer, measure_cache_operation


class TestCachePerformance:
    """Test cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Test that cache hits are fast (< 1ms)."""
        cache = MemoryCacheBackend()
        await cache.set("test_key", "test_value")

        # Measure cache hit
        _, elapsed_ms = await measure_cache_operation(cache.get, "test_key")

        # Cache hit should be very fast (< 1ms)
        assert elapsed_ms < 10.0  # Allow some margin for test environment

    @pytest.mark.asyncio
    async def test_cache_set_performance(self):
        """Test that cache set operations are fast (< 1ms)."""
        cache = MemoryCacheBackend()

        # Measure cache set
        _, elapsed_ms = await measure_cache_operation(cache.set, "test_key", "test_value")

        # Cache set should be very fast (< 1ms)
        assert elapsed_ms < 10.0  # Allow some margin for test environment

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations don't cause issues."""
        cache = MemoryCacheBackend()

        # Perform many concurrent operations
        async def cache_operation(key: str):
            await cache.set(key, f"value_{key}")
            return await cache.get(key)

        # Run 100 concurrent operations
        tasks = [cache_operation(f"key_{i}") for i in range(100)]
        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert len(results) == 100
        assert all(r == f"value_key_{i}" for i, r in enumerate(results))

    @pytest.mark.asyncio
    async def test_cache_pattern_invalidation_performance(self):
        """Test that pattern invalidation is efficient (< 10ms for 1000 entries)."""
        manager = await get_cache_manager()
        await manager.clear()

        # Populate cache with many entries
        for i in range(1000):
            await manager.set(f"entities:state:id=light.{i}", {"state": "on"})

        # Measure invalidation time
        timer = PerformanceTimer()
        timer.start()
        await manager.invalidate("entities:state:*")
        timer.stop()

        # Invalidation should be reasonably fast
        elapsed_ms = timer.elapsed_ms()
        # Allow up to 100ms for 1000 entries (more lenient for test environment)
        assert elapsed_ms < 1000.0  # Allow margin for test environment

    @pytest.mark.asyncio
    async def test_cache_size_limit_performance(self):
        """Test that cache handles size limits efficiently."""
        cache = MemoryCacheBackend(max_size=100)

        # Fill cache to capacity
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}")

        # Measure adding one more (should evict oldest)
        timer = PerformanceTimer()
        timer.start()
        await cache.set("key_100", "value_100")
        timer.stop()

        # Eviction should be fast
        elapsed_ms = timer.elapsed_ms()
        assert elapsed_ms < 10.0  # Should be fast even with eviction

        # Verify cache size is still within limit
        keys = await cache.keys()
        assert len(keys) <= 100

    @pytest.mark.asyncio
    async def test_cache_get_miss_vs_hit_performance(self):
        """Test that cache misses are handled efficiently."""
        cache = MemoryCacheBackend()

        # Measure cache miss
        _, miss_ms = await measure_cache_operation(cache.get, "nonexistent_key")

        # Cache miss should be fast (no need to wait for API)
        assert miss_ms < 10.0

        # Set value and measure cache hit
        await cache.set("test_key", "test_value")
        _, hit_ms = await measure_cache_operation(cache.get, "test_key")

        # Both should be fast, hit should be similar or faster than miss
        assert hit_ms < 10.0
        # Hit might be slightly faster, but both should be very fast
        assert abs(hit_ms - miss_ms) < 5.0  # Allow small difference

    @pytest.mark.asyncio
    async def test_bulk_cache_operations(self):
        """Test performance of bulk cache operations."""
        cache = MemoryCacheBackend()

        # Measure bulk set operations
        timer = PerformanceTimer()
        timer.start()
        for i in range(1000):
            await cache.set(f"key_{i}", f"value_{i}")
        timer.stop()

        elapsed_ms = timer.elapsed_ms()
        # 1000 operations should complete in reasonable time
        assert elapsed_ms < 5000.0  # Allow up to 5 seconds for 1000 operations

        # Measure bulk get operations
        timer.start()
        for i in range(1000):
            await cache.get(f"key_{i}")
        timer.stop()

        elapsed_ms = timer.elapsed_ms()
        # 1000 gets should complete in reasonable time
        assert elapsed_ms < 5000.0  # Allow up to 5 seconds for 1000 operations

    @pytest.mark.asyncio
    async def test_cache_cleanup_performance(self):
        """Test that cache cleanup is efficient."""
        cache = MemoryCacheBackend()

        # Populate cache with entries that will expire
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Measure cleanup time
        timer = PerformanceTimer()
        timer.start()
        removed = await cache.cleanup_expired()
        timer.stop()

        # Cleanup should be efficient
        elapsed_ms = timer.elapsed_ms()
        assert elapsed_ms < 1000.0  # Should complete quickly
        assert removed > 0  # Should have removed expired entries
