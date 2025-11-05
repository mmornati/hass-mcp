"""Unit tests for Redis cache backend (US-009)."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock redis module for testing - always use mocks to avoid requiring Redis
mock_redis = MagicMock()
mock_redis_async = MagicMock()
mock_redis_async.Redis = MagicMock
mock_redis_async.ConnectionPool = MagicMock
mock_redis.asyncio = mock_redis_async
# Set up Redis and ConnectionPool on mock_redis for compatibility checks
mock_redis.Redis = MagicMock
mock_redis.ConnectionPool = MagicMock

# Patch redis module before importing
with patch.dict("sys.modules", {"redis": mock_redis, "redis.asyncio": mock_redis_async}):
    from app.core.cache.redis import RedisCacheBackend


# Test class at module level for pickle serialization
class TestObject:
    """Test object for pickle serialization tests."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, TestObject) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


class TestRedisCacheBackend:
    """Test Redis cache backend implementation."""

    @pytest.fixture
    async def redis_backend(self):
        """Create a Redis backend instance."""
        # Import the module to get access to the redis variable
        import app.core.cache.redis as redis_module

        # Save original value
        original_redis = redis_module.redis

        try:
            # Replace redis with our mock (which is actually redis.asyncio)
            # The mock_redis_async is what gets imported as redis.asyncio
            redis_module.redis = mock_redis_async

            # Mock ConnectionPool.from_url
            mock_pool = MagicMock()
            mock_redis_async.ConnectionPool.from_url = MagicMock(return_value=mock_pool)
            # Mock Redis client
            mock_client = AsyncMock()
            mock_redis_async.Redis = MagicMock(return_value=mock_client)
            # Mock ping for connection test
            mock_client.ping = AsyncMock(return_value=True)

            backend = RedisCacheBackend(url="redis://localhost:6379/0")
            # Pre-initialize the client to avoid connection issues
            backend._client = mock_client
            backend._connection_pool = mock_pool
            yield backend
            # Cleanup - only close if client exists and is not None
            if backend._client is not None:
                from contextlib import suppress

                with suppress(Exception):
                    await backend.close()
        finally:
            # Restore original value
            redis_module.redis = original_redis

    @pytest.mark.asyncio
    async def test_get_set(self, redis_backend):
        """Test basic get and set operations."""
        # Mock Redis GET to return serialized value
        mock_data = b'{"test": "value"}'
        redis_backend._client.get = AsyncMock(return_value=mock_data)
        redis_backend._client.set = AsyncMock()

        # Set value without TTL (should use set, not setex)
        await redis_backend.set("test_key", {"test": "value"})
        redis_backend._client.set.assert_called_once()

        # Get value
        value = await redis_backend.get("test_key")
        assert value == {"test": "value"}

    @pytest.mark.asyncio
    async def test_get_with_ttl(self, redis_backend):
        """Test set with TTL."""
        redis_backend._client.setex = AsyncMock()
        await redis_backend.set("test_key", "test_value", ttl=300)
        redis_backend._client.setex.assert_called_once()
        # Verify TTL was passed
        call_args = redis_backend._client.setex.call_args
        assert call_args[0][1] == 300  # TTL parameter

    @pytest.mark.asyncio
    async def test_get_without_ttl(self, redis_backend):
        """Test set without TTL."""
        redis_backend._client.set = AsyncMock()
        await redis_backend.set("test_key", "test_value", ttl=None)
        redis_backend._client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_backend):
        """Test get for nonexistent key."""
        redis_backend._client.get = AsyncMock(return_value=None)
        value = await redis_backend.get("nonexistent_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, redis_backend):
        """Test delete operation."""
        redis_backend._client.delete = AsyncMock(return_value=1)
        await redis_backend.delete("test_key")
        redis_backend._client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_clear(self, redis_backend):
        """Test clear operation."""
        redis_backend._client.flushdb = AsyncMock(return_value=True)
        await redis_backend.clear()
        redis_backend._client.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists(self, redis_backend):
        """Test exists operation."""
        redis_backend._client.exists = AsyncMock(return_value=1)
        result = await redis_backend.exists("test_key")
        assert result is True

        redis_backend._client.exists = AsyncMock(return_value=0)
        result = await redis_backend.exists("nonexistent_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_keys_with_pattern(self, redis_backend):
        """Test keys with pattern matching."""

        # Mock SCAN_ITER to return keys (async iterator)
        async def mock_scan_iter(match=None):
            mock_keys = [b"entities:state:id=light.living_room", b"entities:state:id=light.kitchen"]
            for key in mock_keys:
                yield key

        redis_backend._client.scan_iter = mock_scan_iter

        keys = await redis_backend.keys("entities:state:*")
        assert len(keys) == 2
        assert "entities:state:id=light.living_room" in keys
        assert "entities:state:id=light.kitchen" in keys

    @pytest.mark.asyncio
    async def test_keys_without_pattern(self, redis_backend):
        """Test keys without pattern."""

        # Mock SCAN_ITER to return keys (async iterator)
        async def mock_scan_iter(match=None):
            mock_keys = [b"key1", b"key2"]
            for key in mock_keys:
                yield key

        redis_backend._client.scan_iter = mock_scan_iter

        keys = await redis_backend.keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    @pytest.mark.asyncio
    async def test_serialize_json(self, redis_backend):
        """Test serialization of JSON-compatible types."""
        # Test dict
        data = redis_backend._serialize({"test": "value"})
        assert isinstance(data, bytes)
        assert b'"test"' in data

        # Test list
        data = redis_backend._serialize([1, 2, 3])
        assert isinstance(data, bytes)

        # Test string
        data = redis_backend._serialize("test")
        assert isinstance(data, bytes)

        # Test int
        data = redis_backend._serialize(42)
        assert isinstance(data, bytes)

    @pytest.mark.asyncio
    async def test_serialize_complex_types(self, redis_backend):
        """Test serialization of complex types using pickle."""
        # Test with a complex object (set can't be JSON-serialized, will use pickle)
        obj = {1, 2, 3}  # Set requires pickle
        data = redis_backend._serialize(obj)
        assert isinstance(data, bytes)

        # Deserialize should work
        deserialized = redis_backend._deserialize(data)
        assert isinstance(deserialized, set)
        assert deserialized == {1, 2, 3}

        # Test with module-level class
        test_obj = TestObject("test")
        data = redis_backend._serialize(test_obj)
        assert isinstance(data, bytes)

        # Deserialize should work
        deserialized = redis_backend._deserialize(data)
        assert isinstance(deserialized, TestObject)
        assert deserialized.value == "test"

    @pytest.mark.asyncio
    async def test_deserialize_json(self, redis_backend):
        """Test deserialization of JSON data."""
        import json

        # Test dict
        data = json.dumps({"test": "value"}).encode("utf-8")
        value = redis_backend._deserialize(data)
        assert value == {"test": "value"}

        # Test list
        data = json.dumps([1, 2, 3]).encode("utf-8")
        value = redis_backend._deserialize(data)
        assert value == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_deserialize_pickle(self, redis_backend):
        """Test deserialization of pickle data."""
        import pickle

        # Test with module-level class
        obj = TestObject("test")
        data = pickle.dumps(obj)
        value = redis_backend._deserialize(data)
        assert isinstance(value, TestObject)
        assert value.value == "test"

        # Test with set (requires pickle)
        test_set = {1, 2, 3}
        data = pickle.dumps(test_set)
        value = redis_backend._deserialize(data)
        assert isinstance(value, set)
        assert value == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, redis_backend, caplog):
        """Test handling of connection errors."""

        # Use a generic Exception since we're mocking redis
        # The code catches redis.ConnectionError first, but since redis is mocked,
        # it will fall through to the generic Exception handler
        class MockConnectionError(Exception):
            pass

        # Mock connection error
        redis_backend._client.get = AsyncMock(side_effect=MockConnectionError("Connection failed"))

        # Should return None and log warning, not raise exception
        # The code will catch this as a generic Exception (not redis.ConnectionError)
        value = await redis_backend.get("test_key")
        assert value is None
        # Check that warning was logged
        assert "Redis get error" in caplog.text or "Redis connection error" in caplog.text

    @pytest.mark.asyncio
    async def test_size_async(self, redis_backend):
        """Test async_size method."""
        redis_backend._client.dbsize = AsyncMock(return_value=10)
        size = await redis_backend.async_size()
        assert size == 10

    @pytest.mark.asyncio
    async def test_size_sync(self, redis_backend):
        """Test sync size method returns -1."""
        size = redis_backend.size()
        assert size == -1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, redis_backend):
        """Test cleanup_expired method."""
        redis_backend._client.ping = AsyncMock(return_value=True)
        removed = await redis_backend.cleanup_expired()
        assert removed == 0  # Redis handles TTL automatically

    @pytest.mark.asyncio
    async def test_close(self, redis_backend):
        """Test close method."""
        # Ensure client exists before closing
        if redis_backend._client is None:
            redis_backend._client = AsyncMock()
        # Store reference before close (close() sets _client to None)
        client_ref = redis_backend._client
        client_ref.aclose = AsyncMock()
        await redis_backend.close()
        # Assert on the stored reference since _client is now None after close()
        client_ref.aclose.assert_called_once()
        assert redis_backend._client is None

    @pytest.mark.asyncio
    async def test_initialization_without_redis(self):
        """Test initialization without redis package."""
        import importlib

        # Save original state
        original_redis_module = sys.modules.get("app.core.cache.redis")
        original_redis = sys.modules.get("redis")
        original_redis_async = sys.modules.get("redis.asyncio")

        try:
            # Remove from sys.modules to simulate ImportError scenario
            if "redis" in sys.modules:
                del sys.modules["redis"]
            if "redis.asyncio" in sys.modules:
                del sys.modules["redis.asyncio"]
            if "app.core.cache.redis" in sys.modules:
                del sys.modules["app.core.cache.redis"]

            # Patch redis to None before importing
            with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
                # Import the module (will have redis=None)
                import app.core.cache.redis as redis_module

                # Now try to create an instance - should raise ImportError
                with pytest.raises(ImportError, match="Redis package is not installed"):
                    redis_module.RedisCacheBackend(url="redis://localhost:6379/0")
        finally:
            # Restore original state
            if original_redis is not None:
                sys.modules["redis"] = original_redis
            if original_redis_async is not None:
                sys.modules["redis.asyncio"] = original_redis_async
            if original_redis_module is not None:
                sys.modules["app.core.cache.redis"] = original_redis_module
            # Restore redis mock
            with patch.dict(
                "sys.modules", {"redis": mock_redis, "redis.asyncio": mock_redis_async}
            ):
                if "app.core.cache.redis" in sys.modules:
                    importlib.reload(sys.modules["app.core.cache.redis"])


class TestRedisCacheBackendIntegration:
    """Integration tests for Redis cache backend (requires Redis)."""

    @pytest.fixture
    async def redis_backend_real(self):
        """Create a real Redis backend instance if Redis is available."""
        # Skip if REDIS_URL not set
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        backend = RedisCacheBackend(url=redis_url)
        try:
            # Test connection
            await backend._get_client()
            yield backend
        except Exception:
            pytest.skip("Redis not available")
        finally:
            await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_integration_get_set(self, redis_backend_real):
        """Integration test for get and set operations."""
        await redis_backend_real.clear()

        # Set value
        await redis_backend_real.set("test_key", {"test": "value"}, ttl=60)
        # Get value
        value = await redis_backend_real.get("test_key")
        assert value == {"test": "value"}

        # Cleanup
        await redis_backend_real.delete("test_key")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_integration_ttl_expiration(self, redis_backend_real):
        """Integration test for TTL expiration."""
        await redis_backend_real.clear()

        # Set value with short TTL
        await redis_backend_real.set("test_key_ttl", "test_value", ttl=1)

        # Should exist immediately
        value = await redis_backend_real.get("test_key_ttl")
        assert value == "test_value"

        # Wait for expiration
        import asyncio

        await asyncio.sleep(1.1)

        # Should be None after expiration
        value = await redis_backend_real.get("test_key_ttl")
        assert value is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_integration_pattern_matching(self, redis_backend_real):
        """Integration test for pattern matching."""
        await redis_backend_real.clear()

        # Set multiple keys
        await redis_backend_real.set("entities:state:id=light.living_room", "value1")
        await redis_backend_real.set("entities:state:id=light.kitchen", "value2")
        await redis_backend_real.set("automations:list:", "value3")

        # Get keys matching pattern
        keys = await redis_backend_real.keys("entities:state:*")
        assert len(keys) == 2
        assert "entities:state:id=light.living_room" in keys
        assert "entities:state:id=light.kitchen" in keys

        # Cleanup
        await redis_backend_real.clear()
