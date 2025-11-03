"""Additional tests for memory cache backend to improve coverage."""

import asyncio

import pytest

from app.core.cache.memory import MemoryCacheBackend


class TestMemoryCacheBackendCoverage:
    """Additional tests to improve coverage for edge cases."""

    @pytest.fixture
    async def cache(self):
        """Create a memory cache backend instance."""
        return MemoryCacheBackend(max_size=100)

    @pytest.mark.asyncio
    async def test_exists_expired_entry(self, cache):
        """Test exists() with expired entry."""
        # Set entry with very short TTL
        await cache.set("expired_key", "value", ttl=0.1)
        await asyncio.sleep(0.2)

        # Should return False and remove expired entry
        assert await cache.exists("expired_key") is False

    @pytest.mark.asyncio
    async def test_keys_pattern_middle(self, cache):
        """Test pattern matching with *middle* pattern."""
        await cache.set("entities:list:domain=light", "value1")
        await cache.set("entities:state:id=light1", "value2")
        await cache.set("automations:list:", "value3")

        # Pattern with * in middle
        keys = await cache.keys("*list*")
        assert "entities:list:domain=light" in keys
        assert "automations:list:" in keys

    @pytest.mark.asyncio
    async def test_keys_pattern_complex_wildcard(self, cache):
        """Test pattern matching with complex wildcard pattern."""
        await cache.set("entities:list:domain=light", "value1")
        await cache.set("entities:state:id=light1", "value2")

        # Pattern with multiple wildcards
        keys = await cache.keys("*:list:*")
        assert "entities:list:domain=light" in keys
