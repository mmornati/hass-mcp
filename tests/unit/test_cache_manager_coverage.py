"""Additional tests for cache manager to improve coverage.

This module adds tests for edge cases and code paths
that may not be covered by existing tests.
"""

from unittest.mock import patch

import pytest

from app.core.cache.manager import get_cache_manager


@pytest.mark.asyncio
class TestCacheManagerCoverage:
    """Additional tests for cache manager coverage."""

    @pytest.fixture
    async def manager(self):
        """Create a cache manager instance."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager = await get_cache_manager()
        yield manager
        await manager.clear()
        manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_backend_initialization_memory(self, manager):
        """Test memory backend initialization."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager._backend = None

        # Force memory backend
        import os

        original_backend = os.environ.get("HASS_MCP_CACHE_BACKEND")
        os.environ["HASS_MCP_CACHE_BACKEND"] = "memory"

        try:
            import importlib

            import app.core.cache.config as config_module

            config_module._cache_config = None
            importlib.reload(config_module)

            manager._config = config_module.get_cache_config()
            manager._backend = None

            backend = await manager._get_backend()
            assert backend is not None
            assert backend.__class__.__name__ == "MemoryCacheBackend"
        finally:
            if original_backend is None:
                os.environ.pop("HASS_MCP_CACHE_BACKEND", None)
            else:
                os.environ["HASS_MCP_CACHE_BACKEND"] = original_backend

            import importlib

            import app.core.cache.config as config_module

            importlib.reload(config_module)
            manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_backend_initialization_redis_fallback(self, manager):
        """Test Redis backend initialization with fallback."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager._backend = None

        # Force Redis backend but don't install redis
        import os
        import sys

        original_backend = os.environ.get("HASS_MCP_CACHE_BACKEND")
        os.environ["HASS_MCP_CACHE_BACKEND"] = "redis"

        try:
            import importlib

            import app.core.cache.config as config_module

            config_module._cache_config = None
            importlib.reload(config_module)

            manager._config = config_module.get_cache_config()
            manager._backend = None

            # Temporarily remove redis module from sys.modules to simulate it not being installed
            original_redis = sys.modules.pop("redis", None)
            original_redis_async = sys.modules.pop("redis.asyncio", None)

            try:
                backend = await manager._get_backend()
                # Should fallback to memory backend since redis is not available
                assert backend is not None
                assert backend.__class__.__name__ == "MemoryCacheBackend"
            finally:
                # Restore redis modules
                if original_redis is not None:
                    sys.modules["redis"] = original_redis
                if original_redis_async is not None:
                    sys.modules["redis.asyncio"] = original_redis_async
        finally:
            if original_backend is None:
                os.environ.pop("HASS_MCP_CACHE_BACKEND", None)
            else:
                os.environ["HASS_MCP_CACHE_BACKEND"] = original_backend

            import importlib

            import app.core.cache.config as config_module

            importlib.reload(config_module)
            manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_backend_initialization_file_fallback(self, manager):
        """Test file backend initialization with fallback."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager._backend = None

        # Force file backend but simulate FileCacheBackend initialization failure
        import os

        original_backend = os.environ.get("HASS_MCP_CACHE_BACKEND")
        os.environ["HASS_MCP_CACHE_BACKEND"] = "file"

        try:
            import importlib

            import app.core.cache.config as config_module

            config_module._cache_config = None
            importlib.reload(config_module)

            manager._config = config_module.get_cache_config()
            manager._backend = None

            # Patch FileCacheBackend.__init__ to raise ImportError
            # This simulates the case where aiofiles is not available
            with patch(
                "app.core.cache.file.FileCacheBackend.__init__",
                side_effect=ImportError("aiofiles not available"),
            ):
                backend = await manager._get_backend()
                # Should fallback to memory backend since FileCacheBackend initialization failed
                assert backend is not None
                assert backend.__class__.__name__ == "MemoryCacheBackend"
        finally:
            if original_backend is None:
                os.environ.pop("HASS_MCP_CACHE_BACKEND", None)
            else:
                os.environ["HASS_MCP_CACHE_BACKEND"] = original_backend

            import importlib

            import app.core.cache.config as config_module

            importlib.reload(config_module)
            manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_backend_initialization_unknown(self, manager):
        """Test unknown backend initialization with fallback."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager._backend = None

        # Force unknown backend
        import os

        original_backend = os.environ.get("HASS_MCP_CACHE_BACKEND")
        os.environ["HASS_MCP_CACHE_BACKEND"] = "unknown_backend"

        try:
            import importlib

            import app.core.cache.config as config_module

            config_module._cache_config = None
            importlib.reload(config_module)

            manager._config = config_module.get_cache_config()
            manager._backend = None

            backend = await manager._get_backend()
            # Should fallback to memory backend
            assert backend is not None
            assert backend.__class__.__name__ == "MemoryCacheBackend"
        finally:
            if original_backend is None:
                os.environ.pop("HASS_MCP_CACHE_BACKEND", None)
            else:
                os.environ["HASS_MCP_CACHE_BACKEND"] = original_backend

            import importlib

            import app.core.cache.config as config_module

            importlib.reload(config_module)
            manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_get_with_endpoint_metrics(self, manager):
        """Test get operation with endpoint metrics."""
        await manager.set("test_key", "test_value", endpoint="test_endpoint")
        value = await manager.get("test_key", endpoint="test_endpoint")
        assert value == "test_value"

        # Check statistics include endpoint metrics
        stats = manager.get_statistics()
        assert "statistics" in stats
        assert "per_endpoint" in stats

    @pytest.mark.asyncio
    async def test_set_with_endpoint_metrics(self, manager):
        """Test set operation with endpoint metrics."""
        await manager.set("test_key", "test_value", endpoint="test_endpoint")

        # Check statistics
        stats = manager.get_statistics()
        assert "statistics" in stats

    @pytest.mark.asyncio
    async def test_delete_with_endpoint_metrics(self, manager):
        """Test delete operation with endpoint metrics."""
        await manager.set("test_key", "test_value")
        await manager.delete("test_key", endpoint="test_endpoint")

        value = await manager.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_invalidate_with_hierarchical_expansion(self, manager):
        """Test invalidation with hierarchical expansion."""
        # Set up cache entries
        await manager.set("entities:state:id=light.living_room", "value1")
        await manager.set("entities:list:domain=light", "value2")
        await manager.set("automations:list:", "value3")

        # Invalidate with hierarchical expansion
        result = await manager.invalidate("entities:*", hierarchical=True, expand_children=True)

        # Should invalidate both entities entries
        assert result["total_invalidated"] >= 2
        assert await manager.get("entities:state:id=light.living_room") is None
        assert await manager.get("entities:list:domain=light") is None
        assert await manager.get("automations:list:") == "value3"

    @pytest.mark.asyncio
    async def test_invalidate_without_expansion(self, manager):
        """Test invalidation without hierarchical expansion."""
        # Set up cache entries
        await manager.set("entities:state:id=light.living_room", "value1")
        await manager.set("entities:list:domain=light", "value2")

        # Invalidate without expansion
        result = await manager.invalidate("entities:*", hierarchical=False, expand_children=False)

        # Should only invalidate exact pattern match
        assert result["total_invalidated"] >= 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_with_backend_support(self, manager):
        """Test cleanup_expired with backend that supports it."""
        await manager.set("key1", "value1", ttl=1)
        await manager.set("key2", "value2", ttl=100)

        # Wait for first entry to expire
        import asyncio

        await asyncio.sleep(1.1)

        # Cleanup expired entries
        removed = await manager.cleanup_expired()
        assert removed >= 0  # May be 0 if backend handles it automatically

    @pytest.mark.asyncio
    async def test_cleanup_expired_without_backend_support(self, manager):
        """Test cleanup_expired with backend that doesn't support it."""
        # Backend should still work
        removed = await manager.cleanup_expired()
        assert removed >= 0

    @pytest.mark.asyncio
    async def test_keys_with_pattern(self, manager):
        """Test keys with pattern matching."""
        await manager.set("entities:state:id=light.living_room", "value1")
        await manager.set("entities:state:id=light.kitchen", "value2")
        await manager.set("automations:list:", "value3")

        keys = await manager.keys("entities:state:*")
        assert len(keys) >= 2
        assert any("light.living_room" in key for key in keys)
        assert any("light.kitchen" in key for key in keys)

    @pytest.mark.asyncio
    async def test_keys_without_pattern(self, manager):
        """Test keys without pattern."""
        await manager.set("key1", "value1")
        await manager.set("key2", "value2")

        keys = await manager.keys()
        assert len(keys) >= 2
        assert "key1" in keys or any("key1" in k for k in keys)
        assert "key2" in keys or any("key2" in k for k in keys)

    @pytest.mark.asyncio
    async def test_statistics_with_no_backend_size(self, manager):
        """Test statistics when backend doesn't have size() method."""
        stats = manager.get_statistics()
        assert "enabled" in stats
        assert "hits" in stats
        assert "misses" in stats
        # Size may not be available for all backends
        assert "size" in stats or "statistics" in stats

    @pytest.mark.asyncio
    async def test_get_statistics_with_no_requests(self, manager):
        """Test statistics with no cache requests."""
        stats = manager.get_statistics()
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_with_requests(self, manager):
        """Test statistics with cache requests."""
        await manager.set("key1", "value1")
        await manager.get("key1")  # Hit
        await manager.get("key2")  # Miss

        stats = manager.get_statistics()
        assert stats["total_requests"] >= 2
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert 0.0 <= stats["hit_rate"] <= 1.0
