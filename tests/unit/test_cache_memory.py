"""Unit tests for memory cache backend."""

import asyncio

import pytest

from app.core.cache.memory import MemoryCacheBackend


class TestMemoryCacheBackend:
    """Test memory cache backend implementation."""

    @pytest.fixture
    async def cache(self):
        """Create a memory cache backend instance."""
        return MemoryCacheBackend(max_size=100)

    @pytest.mark.asyncio
    async def test_get_set(self, cache):
        """Test basic get and set operations."""
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting non-existent key returns None."""
        value = await cache.get("nonexistent_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("test_key", "test_value")
        await cache.delete("test_key")
        value = await cache.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clear operation."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists operation."""
        await cache.set("test_key", "test_value")
        assert await cache.exists("test_key") is True
        assert await cache.exists("nonexistent_key") is False

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test TTL expiration."""
        # Use a very short TTL for testing (0.2 seconds) instead of TTL_SHORT (60s)
        test_ttl = 0.2

        await cache.set("test_key", "test_value", ttl=test_ttl)
        # Should still exist immediately
        assert await cache.get("test_key") == "test_value"

        # Wait for expiration
        await asyncio.sleep(test_ttl + 0.1)

        # Should be expired now
        assert await cache.get("test_key") is None
        assert await cache.exists("test_key") is False

    @pytest.mark.asyncio
    async def test_no_ttl_never_expires(self, cache):
        """Test that entries without TTL never expire."""
        await cache.set("test_key", "test_value", ttl=None)
        # Wait a bit
        await asyncio.sleep(0.1)
        # Should still exist
        assert await cache.get("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_keys_all(self, cache):
        """Test getting all keys."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        keys = await cache.keys()
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) == 2

    @pytest.mark.asyncio
    async def test_keys_pattern_prefix(self, cache):
        """Test pattern matching with prefix."""
        await cache.set("entities:list:domain=light", "value1")
        await cache.set("entities:state:id=light1", "value2")
        await cache.set("automations:list:", "value3")

        keys = await cache.keys("entities:*")
        assert len(keys) == 2
        assert "entities:list:domain=light" in keys
        assert "entities:state:id=light1" in keys
        assert "automations:list:" not in keys

    @pytest.mark.asyncio
    async def test_keys_pattern_suffix(self, cache):
        """Test pattern matching with suffix."""
        await cache.set("entities:list:domain=light", "value1")
        await cache.set("automations:list:", "value2")

        keys = await cache.keys("*:list:")
        assert "automations:list:" in keys
        assert "entities:list:domain=light" not in keys

    @pytest.mark.asyncio
    async def test_keys_pattern_exact(self, cache):
        """Test exact pattern matching."""
        await cache.set("test_key", "value1")
        await cache.set("test_key2", "value2")

        keys = await cache.keys("test_key")
        assert len(keys) == 1
        assert "test_key" in keys

    @pytest.mark.asyncio
    async def test_max_size_limit(self, cache):
        """Test max size limit enforcement."""
        # Fill cache to max size
        for i in range(100):
            await cache.set(f"key{i}", f"value{i}")

        assert cache.size() == 100

        # Add one more, should evict oldest
        await cache.set("new_key", "new_value")
        assert cache.size() == 100
        # First key should be evicted
        assert await cache.get("key0") is None
        # New key should exist
        assert await cache.get("new_key") == "new_value"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache):
        """Test concurrent cache operations."""
        # Set multiple keys concurrently
        await asyncio.gather(*[cache.set(f"key{i}", f"value{i}") for i in range(10)])

        # Get multiple keys concurrently
        values = await asyncio.gather(*[cache.get(f"key{i}") for i in range(10)])

        assert all(v == f"value{i}" for i, v in enumerate(values))

    @pytest.mark.asyncio
    async def test_expired_entries_removed_on_get(self, cache):
        """Test that expired entries are removed when accessed."""
        await cache.set("expired_key", "value", ttl=0.1)
        await asyncio.sleep(0.2)
        # Getting expired key should remove it
        assert await cache.get("expired_key") is None
        # Should not appear in keys list
        keys = await cache.keys()
        assert "expired_key" not in keys

    @pytest.mark.asyncio
    async def test_expired_entries_removed_on_keys(self, cache):
        """Test that expired entries are cleaned up when listing keys."""
        await cache.set("expired_key", "value", ttl=0.1)
        await cache.set("valid_key", "value", ttl=None)
        await asyncio.sleep(0.2)

        keys = await cache.keys()
        assert "expired_key" not in keys
        assert "valid_key" in keys

    def test_size(self, cache):
        """Test size method."""
        assert cache.size() == 0
        # Note: size() is synchronous, but we need async context for set
        # This is a synchronous test of the size method itself
