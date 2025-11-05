"""Error handling tests for cache components.

This module tests error handling scenarios including
cache backend failures, serialization errors, and edge cases.
"""

import pytest

from app.core.cache.manager import get_cache_manager
from tests.fixtures.cache_fixtures import MockCacheBackend


@pytest.mark.asyncio
class TestCacheErrorHandling:
    """Test cache error handling scenarios."""

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
    async def test_backend_unavailable_graceful_degradation(self, manager):
        """Test that cache gracefully degrades when backend is unavailable."""
        # Replace backend with a mock that raises errors
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        mock_backend.enable_errors()
        manager._backend = mock_backend

        try:
            # Should not raise exception, should return default
            value = await manager.get("test_key", default="default_value")
            assert value == "default_value"

            # Set should not raise exception
            await manager.set("test_key", "test_value")

            # Delete should not raise exception
            await manager.delete("test_key")
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_invalidation_error_graceful_degradation(self, manager):
        """Test that invalidation errors don't break execution."""
        # Replace backend with a mock that raises errors on keys()
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        mock_backend.enable_errors()
        manager._backend = mock_backend

        try:
            # Should not raise exception
            result = await manager.invalidate("entities:*")
            # Should return empty result on error
            assert result["total_invalidated"] == 0
            assert "error" in result or result["total_invalidated"] == 0
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_clear_error_graceful_degradation(self, manager):
        """Test that clear errors don't break execution."""
        # Replace backend with a mock that raises errors
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        mock_backend.enable_errors()
        manager._backend = mock_backend

        try:
            # Should not raise exception
            await manager.clear()
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_keys_error_graceful_degradation(self, manager):
        """Test that keys errors don't break execution."""
        # Replace backend with a mock that raises errors
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        mock_backend.enable_errors()
        manager._backend = mock_backend

        try:
            # Should not raise exception, should return empty list
            keys = await manager.keys("entities:*")
            assert isinstance(keys, list)
            assert len(keys) == 0
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_cleanup_error_graceful_degradation(self, manager):
        """Test that cleanup errors don't break execution."""
        # Replace backend with a mock that raises errors
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        mock_backend.enable_errors()
        manager._backend = mock_backend

        try:
            # Should not raise exception, should return 0
            removed = await manager.cleanup_expired()
            assert removed == 0
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_invalid_cache_key(self, manager):
        """Test that invalid cache keys don't cause errors."""
        # Empty key
        await manager.set("", "value")
        value = await manager.get("")
        assert value == "value"

        # Very long key
        long_key = "x" * 10000
        await manager.set(long_key, "value")
        value = await manager.get(long_key)
        assert value == "value"

        # Key with special characters
        special_key = "entities:state:id=light.living_room:field=state"
        await manager.set(special_key, "value")
        value = await manager.get(special_key)
        assert value == "value"

    @pytest.mark.asyncio
    async def test_ttl_edge_cases(self, manager):
        """Test TTL edge cases."""
        # Zero TTL (should expire immediately)
        await manager.set("key_zero", "value", ttl=0)
        # Should still be available immediately (TTL=0 means no expiration)
        value = await manager.get("key_zero")
        assert value == "value"

        # Negative TTL (should treat as no expiration)
        await manager.set("key_negative", "value", ttl=-1)
        value = await manager.get("key_negative")
        assert value == "value"

        # Very large TTL
        await manager.set("key_large", "value", ttl=999999999)
        value = await manager.get("key_large")
        assert value == "value"

        # None TTL (no expiration)
        await manager.set("key_none", "value", ttl=None)
        value = await manager.get("key_none")
        assert value == "value"

    @pytest.mark.asyncio
    async def test_large_value_handling(self, manager):
        """Test that large values are handled correctly."""
        # Large string value
        large_value = "x" * 1000000  # 1MB string
        await manager.set("key_large", large_value)
        value = await manager.get("key_large")
        assert value == large_value

        # Large dictionary
        large_dict = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
        await manager.set("key_large_dict", large_dict)
        value = await manager.get("key_large_dict")
        assert value == large_dict

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, manager):
        """Test error handling with concurrent operations."""
        import asyncio

        # Replace backend with a mock that sometimes raises errors
        original_backend = manager._backend
        mock_backend = MockCacheBackend()
        call_count = {"count": 0}

        async def mock_get(key: str):
            call_count["count"] += 1
            if call_count["count"] % 3 == 0:  # Every 3rd call fails
                raise Exception("Intermittent error")
            return mock_backend._cache.get(key)

        mock_backend.get = mock_get
        manager._backend = mock_backend

        try:
            # Perform concurrent operations
            async def operation(key: str):
                try:
                    await manager.set(key, f"value_{key}")
                    return await manager.get(key, default="default")
                except Exception:
                    return "default"

            # Run 30 concurrent operations
            tasks = [operation(f"key_{i}") for i in range(30)]
            results = await asyncio.gather(*tasks)

            # All operations should complete (return default on error)
            assert len(results) == 30
            assert all(r in ("default", f"value_key_{i}") for i, r in enumerate(results))
        finally:
            manager._backend = original_backend

    @pytest.mark.asyncio
    async def test_cache_disabled_operations(self):
        """Test that cache operations work when cache is disabled."""
        import os

        original_enabled = os.environ.get("HASS_MCP_CACHE_ENABLED")
        os.environ["HASS_MCP_CACHE_ENABLED"] = "false"

        try:
            import app.core.cache.config as config_module
            import app.core.cache.manager as manager_module

            # Clear all singleton instances
            manager_module._cache_manager = None
            config_module._cache_config = None

            # Reload config modules
            import importlib

            import app.config as config_module_base

            importlib.reload(config_module_base)
            importlib.reload(config_module)
            importlib.reload(manager_module)

            manager = await get_cache_manager()

            # All operations should work but not cache
            await manager.set("test_key", "test_value")
            value = await manager.get("test_key", default="default")
            assert value == "default"  # Should return default when disabled

            await manager.delete("test_key")
            await manager.clear()
            await manager.invalidate("entities:*")
            keys = await manager.keys()
            assert keys == []

            stats = manager.get_statistics()
            assert stats["enabled"] is False
        finally:
            if original_enabled is None:
                os.environ.pop("HASS_MCP_CACHE_ENABLED", None)
            else:
                os.environ["HASS_MCP_CACHE_ENABLED"] = original_enabled

            # Reload modules
            import importlib

            import app.config as config_module_base
            import app.core.cache.config as config_module
            import app.core.cache.manager as manager_module

            importlib.reload(config_module_base)
            importlib.reload(config_module)
            importlib.reload(manager_module)
            manager_module._cache_manager = None
            config_module._cache_config = None
