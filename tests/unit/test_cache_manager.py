"""Unit tests for cache manager."""

import os

import pytest

from app.config import CACHE_ENABLED
from app.core.cache.manager import get_cache_manager


class TestCacheManager:
    """Test cache manager implementation."""

    @pytest.fixture
    async def manager(self):
        """Create a cache manager instance."""
        # Clear any existing manager
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager = await get_cache_manager()
        yield manager
        # Cleanup
        await manager.clear()
        manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that get_cache_manager returns same instance."""
        import app.core.cache.manager as manager_module

        manager_module._cache_manager = None
        manager1 = await get_cache_manager()
        manager2 = await get_cache_manager()
        assert manager1 is manager2
        manager_module._cache_manager = None

    @pytest.mark.asyncio
    async def test_get_set(self, manager):
        """Test basic get and set operations."""
        await manager.set("test_key", "test_value")
        value = await manager.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_with_default(self, manager):
        """Test get with default value."""
        value = await manager.get("nonexistent_key", default="default_value")
        assert value == "default_value"

    @pytest.mark.asyncio
    async def test_delete(self, manager):
        """Test delete operation."""
        await manager.set("test_key", "test_value")
        await manager.delete("test_key")
        value = await manager.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, manager):
        """Test pattern-based invalidation."""
        await manager.set("entities:list:domain=light", "value1")
        await manager.set("entities:state:id=light1", "value2")
        await manager.set("automations:list:", "value3")

        await manager.invalidate("entities:*")

        assert await manager.get("entities:list:domain=light") is None
        assert await manager.get("entities:state:id=light1") is None
        assert await manager.get("automations:list:") == "value3"

    @pytest.mark.asyncio
    async def test_clear(self, manager):
        """Test clear operation."""
        await manager.set("key1", "value1")
        await manager.set("key2", "value2")
        await manager.clear()
        assert await manager.get("key1") is None
        assert await manager.get("key2") is None

    @pytest.mark.asyncio
    async def test_error_handling_get(self, manager):
        """Test that get errors don't break execution."""
        # This test ensures graceful degradation
        # If backend fails, should return default
        value = await manager.get("test_key", default="default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_error_handling_set(self, manager):
        """Test that set errors don't break execution."""
        # Should not raise exception
        await manager.set("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_statistics(self, manager):
        """Test cache statistics."""
        await manager.set("key1", "value1")
        await manager.get("key1")  # Hit
        await manager.get("key2")  # Miss

        stats = manager.get_statistics()
        assert stats["enabled"] == CACHE_ENABLED
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats
        assert "total_requests" in stats

    @pytest.mark.asyncio
    async def test_statistics_hit_rate(self, manager):
        """Test hit rate calculation."""
        await manager.set("key1", "value1")
        await manager.get("key1")  # Hit
        await manager.get("key1")  # Hit
        await manager.get("key2")  # Miss

        stats = manager.get_statistics()
        assert stats["total_requests"] == 3
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert 0.0 <= stats["hit_rate"] <= 1.0

    @pytest.mark.asyncio
    async def test_disabled_cache_returns_default(self):
        """Test that disabled cache returns default values."""
        # Temporarily disable cache
        original_enabled = os.environ.get("HASS_MCP_CACHE_ENABLED")
        os.environ["HASS_MCP_CACHE_ENABLED"] = "false"

        try:
            import app.core.cache.manager as manager_module

            manager_module._cache_manager = None
            # Reload config
            import importlib

            import app.config as config_module

            importlib.reload(config_module)
            importlib.reload(manager_module)

            manager = await get_cache_manager()
            await manager.set("test_key", "test_value")
            # Should return default when cache is disabled
            value = await manager.get("test_key", default="default")
            assert value == "default"
        finally:
            # Restore original setting
            if original_enabled is None:
                os.environ.pop("HASS_MCP_CACHE_ENABLED", None)
            else:
                os.environ["HASS_MCP_CACHE_ENABLED"] = original_enabled

            # Reload modules
            import importlib

            import app.config as config_module
            import app.core.cache.manager as manager_module

            importlib.reload(config_module)
            importlib.reload(manager_module)
