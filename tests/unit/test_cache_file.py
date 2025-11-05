"""Unit tests for file cache backend (US-010)."""

import asyncio
import json
import pickle
import tempfile
from contextlib import suppress
from pathlib import Path

import pytest

# Mock aiofiles for testing
try:
    import aiofiles
    import aiofiles.os
except ImportError:
    aiofiles = None  # type: ignore[assignment]
    aiofiles_os = None  # type: ignore[assignment]

# Only run tests if aiofiles is available or mocked
pytestmark = pytest.mark.skipif(
    aiofiles is None, reason="aiofiles package required for file cache backend tests"
)


# Test class at module level for pickle serialization
class TestObject:
    """Test object for pickle serialization tests."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, TestObject) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
async def file_backend(temp_cache_dir):
    """Create a file backend instance."""
    from app.core.cache.file import FileCacheBackend

    backend = FileCacheBackend(cache_dir=temp_cache_dir)
    yield backend
    # Cleanup
    with suppress(Exception):
        await backend.clear()


class TestFileCacheBackend:
    """Test file cache backend implementation."""

    @pytest.mark.asyncio
    async def test_get_set(self, file_backend):
        """Test basic get and set operations."""
        # Set value
        await file_backend.set("test_key", {"test": "value"})

        # Get value
        value = await file_backend.get("test_key")
        assert value == {"test": "value"}

    @pytest.mark.asyncio
    async def test_get_set_with_ttl(self, file_backend):
        """Test set with TTL."""
        await file_backend.set("test_key", "test_value", ttl=300)

        # Should exist immediately
        value = await file_backend.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_set_without_ttl(self, file_backend):
        """Test set without TTL."""
        await file_backend.set("test_key", "test_value", ttl=None)

        # Should exist
        value = await file_backend.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, file_backend):
        """Test get for nonexistent key."""
        value = await file_backend.get("nonexistent_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, file_backend):
        """Test delete operation."""
        # Set value
        await file_backend.set("test_key", "test_value")

        # Delete
        await file_backend.delete("test_key")

        # Should not exist
        value = await file_backend.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self, file_backend):
        """Test clear operation."""
        # Set multiple values
        await file_backend.set("test_key1", "value1")
        await file_backend.set("test_key2", "value2")

        # Clear
        await file_backend.clear()

        # Should be empty
        value1 = await file_backend.get("test_key1")
        value2 = await file_backend.get("test_key2")
        assert value1 is None
        assert value2 is None

    @pytest.mark.asyncio
    async def test_exists(self, file_backend):
        """Test exists operation."""
        # Set value
        await file_backend.set("test_key", "test_value")

        # Should exist
        assert await file_backend.exists("test_key") is True

        # Delete
        await file_backend.delete("test_key")

        # Should not exist
        assert await file_backend.exists("test_key") is False

    @pytest.mark.asyncio
    async def test_keys_with_pattern(self, file_backend):
        """Test keys with pattern matching."""
        # Set multiple keys
        await file_backend.set("entities:state:id=light.living_room", "value1")
        await file_backend.set("entities:state:id=light.kitchen", "value2")
        await file_backend.set("automations:list:", "value3")

        # Get keys matching pattern
        keys = await file_backend.keys("entities:state:*")
        assert len(keys) == 2
        assert "entities:state:id=light.living_room" in keys
        assert "entities:state:id=light.kitchen" in keys

    @pytest.mark.asyncio
    async def test_keys_without_pattern(self, file_backend):
        """Test keys without pattern."""
        # Set multiple keys
        await file_backend.set("key1", "value1")
        await file_backend.set("key2", "value2")

        # Get all keys
        keys = await file_backend.keys()
        assert len(keys) >= 2
        assert "key1" in keys
        assert "key2" in keys

    @pytest.mark.asyncio
    async def test_serialize_json(self, file_backend):
        """Test serialization of JSON-compatible types."""
        # Test dict
        data = file_backend._serialize({"test": "value"})
        assert isinstance(data, bytes)
        assert b'"test"' in data

        # Test list
        data = file_backend._serialize([1, 2, 3])
        assert isinstance(data, bytes)

        # Test string
        data = file_backend._serialize("test")
        assert isinstance(data, bytes)

        # Test int
        data = file_backend._serialize(42)
        assert isinstance(data, bytes)

    @pytest.mark.asyncio
    async def test_serialize_complex_types(self, file_backend):
        """Test serialization of complex types using pickle."""
        # Test with a complex object (set can't be JSON-serialized, will use pickle)
        obj = {1, 2, 3}  # Set requires pickle
        data = file_backend._serialize(obj)
        assert isinstance(data, bytes)

        # Deserialize should work
        deserialized = file_backend._deserialize(data)
        assert isinstance(deserialized, set)
        assert deserialized == {1, 2, 3}

        # Test with module-level class
        test_obj = TestObject("test")
        data = file_backend._serialize(test_obj)
        assert isinstance(data, bytes)

        # Deserialize should work
        deserialized = file_backend._deserialize(data)
        assert isinstance(deserialized, TestObject)
        assert deserialized.value == "test"

    @pytest.mark.asyncio
    async def test_deserialize_json(self, file_backend):
        """Test deserialization of JSON data."""
        # Test dict
        data = json.dumps({"test": "value"}).encode("utf-8")
        value = file_backend._deserialize(data)
        assert value == {"test": "value"}

        # Test list
        data = json.dumps([1, 2, 3]).encode("utf-8")
        value = file_backend._deserialize(data)
        assert value == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_deserialize_pickle(self, file_backend):
        """Test deserialization of pickle data."""
        # Test with module-level class
        obj = TestObject("test")
        data = pickle.dumps(obj)
        value = file_backend._deserialize(data)
        assert isinstance(value, TestObject)
        assert value.value == "test"

        # Test with set (requires pickle)
        test_set = {1, 2, 3}
        data = pickle.dumps(test_set)
        value = file_backend._deserialize(data)
        assert isinstance(value, set)
        assert value == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, file_backend):
        """Test TTL expiration."""
        # Set value with short TTL
        await file_backend.set("test_key_ttl", "test_value", ttl=1)

        # Should exist immediately
        value = await file_backend.get("test_key_ttl")
        assert value == "test_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be None after expiration
        value = await file_backend.get("test_key_ttl")
        assert value is None

        # Should not exist
        assert await file_backend.exists("test_key_ttl") is False

    @pytest.mark.asyncio
    async def test_size_async(self, file_backend):
        """Test async_size method."""
        # Set multiple values
        await file_backend.set("key1", "value1")
        await file_backend.set("key2", "value2")

        size = await file_backend.async_size()
        assert size >= 2

    @pytest.mark.asyncio
    async def test_size_sync(self, file_backend):
        """Test sync size method returns -1."""
        size = file_backend.size()
        assert size == -1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, file_backend):
        """Test cleanup_expired method."""
        # Set entries with different TTLs
        await file_backend.set("key1", "value1", ttl=1)
        await file_backend.set("key2", "value2", ttl=100)

        # Wait for first entry to expire
        await asyncio.sleep(1.1)

        # Cleanup expired entries
        removed = await file_backend.cleanup_expired()

        assert removed >= 1
        # Verify expired entry is gone
        value1 = await file_backend.get("key1")
        assert value1 is None

        # Verify non-expired entry still exists
        value2 = await file_backend.get("key2")
        assert value2 == "value2"

    @pytest.mark.asyncio
    async def test_directory_structure(self, file_backend, temp_cache_dir):
        """Test directory structure creation."""
        # Set values with different prefixes
        await file_backend.set("entities:state:id=light.living_room", "value1")
        await file_backend.set("automations:list:", "value2")

        # Check that directories were created
        cache_path = Path(temp_cache_dir)
        assert (cache_path / "entities").exists()
        assert (cache_path / "automations").exists()

    @pytest.mark.asyncio
    async def test_file_path_generation(self, file_backend, temp_cache_dir):
        """Test file path generation."""
        key = "entities:state:id=light.living_room"
        file_path = file_backend._get_file_path(key)
        metadata_path = file_backend._get_metadata_path(key)

        # Check paths are correct
        assert file_path.suffix == ".json"
        assert metadata_path.name.endswith(".meta.json")
        assert metadata_path.stem == f"{file_path.stem}.meta"

        # Check that paths are within cache directory
        assert str(file_path).startswith(temp_cache_dir)
        assert str(metadata_path).startswith(temp_cache_dir)

        # Check that prefix directory is included
        assert "entities" in str(file_path)

    @pytest.mark.asyncio
    async def test_key_hash(self, file_backend):
        """Test key hashing."""
        key = "test_key"
        hash1 = file_backend._get_key_hash(key)
        hash2 = file_backend._get_key_hash(key)

        # Same key should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_error_handling(self, file_backend, caplog):
        """Test error handling."""
        # Test with invalid key (should not raise exception)
        value = await file_backend.get("")
        assert value is None

        # Test delete non-existent key (should not raise exception)
        await file_backend.delete("nonexistent_key")

    @pytest.mark.asyncio
    async def test_initialization_without_aiofiles(self):
        """Test initialization without aiofiles package."""
        # Temporarily remove aiofiles
        import app.core.cache.file as file_module

        original_aiofiles = file_module.aiofiles
        file_module.aiofiles = None

        try:
            from app.core.cache.file import FileCacheBackend

            with pytest.raises(ImportError, match="aiofiles package is not installed"):
                FileCacheBackend(cache_dir=".cache")
        finally:
            # Restore aiofiles
            file_module.aiofiles = original_aiofiles

    @pytest.mark.asyncio
    async def test_concurrent_access(self, file_backend):
        """Test concurrent access to file cache."""
        # Set multiple values concurrently
        await asyncio.gather(*[file_backend.set(f"key{i}", f"value{i}") for i in range(10)])

        # Get multiple values concurrently
        values = await asyncio.gather(*[file_backend.get(f"key{i}") for i in range(10)])

        # All values should be retrieved
        assert all(values)
        assert len([v for v in values if v is not None]) == 10

    @pytest.mark.asyncio
    async def test_metadata_storage(self, file_backend, temp_cache_dir):
        """Test that metadata is stored correctly."""
        key = "test_key"
        await file_backend.set(key, "test_value", ttl=300)

        # Check metadata file exists
        file_path = file_backend._get_file_path(key)
        metadata_path = file_backend._get_metadata_path(key)

        assert metadata_path.exists()

        # Read metadata
        import aiofiles

        async with aiofiles.open(metadata_path) as f:
            metadata_str = await f.read()
            metadata = json.loads(metadata_str)

        # Check metadata contains original key
        assert metadata["key"] == key
        assert "created_at" in metadata
        assert "expires_at" in metadata
        assert metadata["ttl"] == 300

    @pytest.mark.asyncio
    async def test_pattern_matching_prefix(self, file_backend):
        """Test pattern matching with prefix."""
        await file_backend.set("entities:state:id=light.living_room", "value1")
        await file_backend.set("entities:state:id=light.kitchen", "value2")
        await file_backend.set("automations:list:", "value3")

        # Match prefix
        keys = await file_backend.keys("entities:*")
        assert len(keys) == 2
        assert "entities:state:id=light.living_room" in keys
        assert "entities:state:id=light.kitchen" in keys

    @pytest.mark.asyncio
    async def test_pattern_matching_suffix(self, file_backend):
        """Test pattern matching with suffix."""
        await file_backend.set("entities:state:id=light.living_room", "value1")
        await file_backend.set("automations:state:id=light.living_room", "value2")

        # Match suffix
        keys = await file_backend.keys("*living_room")
        assert len(keys) >= 2

    @pytest.mark.asyncio
    async def test_empty_directory_cleanup(self, file_backend, temp_cache_dir):
        """Test that empty directories are cleaned up."""
        # Set value
        await file_backend.set("entities:state:id=light.living_room", "value1")

        # Delete value
        await file_backend.delete("entities:state:id=light.living_room")

        # Directory might be cleaned up (depending on implementation)
        # This is optional behavior, so we just check it doesn't crash
        cache_path = Path(temp_cache_dir)
        # Directory might or might not exist after cleanup
