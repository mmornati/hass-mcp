"""File-based cache backend for hass-mcp.

This module provides a file-based cache backend implementation for persistent caching.
File backend allows cache to persist across server restarts without requiring external
dependencies like Redis.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle  # nosec B403 - Used for serializing complex types in trusted cache
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

try:
    import aiofiles
    import aiofiles.os
except ImportError:
    aiofiles = None  # type: ignore[assignment]
    aiofiles_os = None  # type: ignore[assignment]

from app.core.cache.backend import CacheBackend

logger = logging.getLogger(__name__)


class FileCacheBackend(CacheBackend):
    """
    File-based cache backend using filesystem storage.

    This backend stores cache entries as files on disk with TTL support.
    It uses a directory structure for organization and async file I/O for performance.
    """

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize the file cache backend.

        Args:
            cache_dir: Directory path for cache files (default: ".cache")

        Raises:
            ImportError: If aiofiles package is not installed
            ValueError: If cache directory cannot be created
        """
        # Check if aiofiles is available
        if aiofiles is None:
            raise ImportError(
                "aiofiles package is not installed. Install it with: pip install aiofiles"
            )

        self.cache_dir = Path(cache_dir)
        self._lock = None  # Will be initialized in async context

        # Create cache directory if it doesn't exist
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized file cache backend at {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to create cache directory {self.cache_dir}: {e}", exc_info=True)
            raise ValueError(f"Failed to create cache directory: {e}") from e

    def _get_key_hash(self, key: str) -> str:
        """
        Generate a hash for a cache key.

        Args:
            key: The cache key

        Returns:
            Hash string for the key
        """
        # Use MD5 for hashing (not for security, just for cache key)
        return hashlib.md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()

    def _get_file_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            key: The cache key

        Returns:
            Path to the cache file
        """
        # Extract prefix from key (e.g., "entities:state:id=light" -> "entities")
        prefix = "default"
        if ":" in key:
            prefix = key.split(":")[0]

        # Create directory structure: cache_dir/prefix/
        key_hash = self._get_key_hash(key)
        dir_path = self.cache_dir / prefix
        return dir_path / f"{key_hash}.json"

    def _get_metadata_path(self, key: str) -> Path:
        """
        Get the metadata file path for a cache key.

        Args:
            key: The cache key

        Returns:
            Path to the metadata file
        """
        file_path = self._get_file_path(key)
        # Replace .json with .meta.json
        return file_path.parent / f"{file_path.stem}.meta.json"

    async def _ensure_directory(self, file_path: Path) -> None:
        """
        Ensure the directory for a file path exists.

        Args:
            file_path: The file path
        """
        try:
            await aiofiles.os.makedirs(file_path.parent, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create directory {file_path.parent}: {e}", exc_info=True)

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize a value for storage.

        Args:
            value: The value to serialize

        Returns:
            Serialized bytes

        Raises:
            ValueError: If serialization fails
        """
        try:
            # Try JSON for simple types (dict, list, str, int, float, bool, None)
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                json_str = json.dumps(value, default=str)
                return json_str.encode("utf-8")
            # Use pickle for complex types
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except (TypeError, ValueError) as e:
            # If JSON fails, try pickle
            try:
                return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as pickle_error:
                logger.error(
                    f"Failed to serialize value: {e} (pickle also failed: {pickle_error})",
                    exc_info=True,
                )
                raise ValueError(f"Failed to serialize value: {e}") from pickle_error

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize a value from storage.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized value

        Raises:
            ValueError: If deserialization fails
        """
        try:
            # Try JSON first (faster for simple types)
            try:
                json_str = data.decode("utf-8")
                return json.loads(json_str)
            except (UnicodeDecodeError, json.JSONDecodeError):
                # If JSON fails, try pickle
                # nosec B301 - Cache data is trusted (from our own cache directory)
                return pickle.loads(data)  # nosec B301
        except Exception as e:
            logger.error(f"Failed to deserialize value: {e}", exc_info=True)
            raise ValueError(f"Failed to deserialize value: {e}") from e

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found and not expired, None otherwise
        """
        try:
            file_path = self._get_file_path(key)

            # Check if file exists
            if not await aiofiles.os.path.exists(file_path):
                return None

            # Read cache file
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()

            if not data:
                return None

            # Check metadata for expiration
            metadata_path = self._get_metadata_path(key)
            if await aiofiles.os.path.exists(metadata_path):
                async with aiofiles.open(metadata_path, "r") as f:
                    metadata_str = await f.read()
                    metadata = json.loads(metadata_str)

                    # Check expiration
                    expires_at = metadata.get("expires_at")
                    if expires_at is not None:
                        if time.time() > expires_at:
                            # Expired, delete files
                            await self.delete(key)
                            return None

            # Deserialize and return value
            return self._deserialize(data)
        except Exception as e:
            logger.warning(f"File cache get error for key '{key}': {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional Time-To-Live in seconds. If None, entry doesn't expire
        """
        try:
            file_path = self._get_file_path(key)
            metadata_path = self._get_metadata_path(key)

            # Ensure directory exists
            await self._ensure_directory(file_path)

            # Serialize value
            data = self._serialize(value)

            # Write cache file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            # Write metadata (store original key for pattern matching)
            metadata = {
                "key": key,  # Store original key for pattern matching
                "created_at": time.time(),
                "expires_at": time.time() + ttl if ttl and ttl > 0 else None,
                "ttl": ttl,
            }
            async with aiofiles.open(metadata_path, "w") as f:
                await f.write(json.dumps(metadata))

        except Exception as e:
            logger.warning(f"File cache set error for key '{key}': {e}", exc_info=True)

    async def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
        """
        try:
            file_path = self._get_file_path(key)
            metadata_path = self._get_metadata_path(key)

            # Delete cache file
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)

            # Delete metadata file
            if await aiofiles.os.path.exists(metadata_path):
                await aiofiles.os.remove(metadata_path)

            # Try to remove empty directory
            with suppress(Exception):
                if file_path.parent.exists() and not any(file_path.parent.iterdir()):
                    await aiofiles.os.rmdir(file_path.parent)
        except Exception as e:
            logger.warning(f"File cache delete error for key '{key}': {e}", exc_info=True)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        try:
            # Remove all files in cache directory
            if self.cache_dir.exists():
                for item in self.cache_dir.iterdir():
                    if item.is_file():
                        await aiofiles.os.remove(item)
                    elif item.is_dir():
                        # Recursively remove directory contents
                        for subitem in item.rglob("*"):
                            if subitem.is_file():
                                await aiofiles.os.remove(subitem)
                        # Remove empty directories
                        for subitem in item.rglob("*"):
                            if subitem.is_dir():
                                with suppress(Exception):
                                    await aiofiles.os.rmdir(subitem)
                        with suppress(Exception):
                            await aiofiles.os.rmdir(item)

            logger.info("File cache cleared")
        except Exception as e:
            logger.warning(f"File cache clear error: {e}", exc_info=True)

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists and is not expired, False otherwise
        """
        try:
            file_path = self._get_file_path(key)

            if not await aiofiles.os.path.exists(file_path):
                return False

            # Check expiration
            metadata_path = self._get_metadata_path(key)
            if await aiofiles.os.path.exists(metadata_path):
                async with aiofiles.open(metadata_path, "r") as f:
                    metadata_str = await f.read()
                    metadata = json.loads(metadata_str)

                    expires_at = metadata.get("expires_at")
                    if expires_at is not None:
                        if time.time() > expires_at:
                            # Expired, delete files
                            await self.delete(key)
                            return False

            return True
        except Exception as e:
            logger.warning(f"File cache exists error for key '{key}': {e}", exc_info=True)
            return False

    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        Get all cache keys, optionally filtered by pattern.

        Args:
            pattern: Optional pattern to match keys (supports wildcards like '*')

        Returns:
            List of matching cache keys
        """
        try:
            keys: list[str] = []

            if not self.cache_dir.exists():
                return []

            # Walk through cache directory
            for prefix_dir in self.cache_dir.iterdir():
                if not prefix_dir.is_dir():
                    continue

                # Scan files in prefix directory
                for file_path in prefix_dir.glob("*.json"):
                    # Skip metadata files
                    if file_path.name.endswith(".meta.json"):
                        continue

                    # Read metadata to get original key
                    metadata_path = file_path.with_suffix(".meta.json")
                    original_key = None
                    if metadata_path.exists():
                        try:
                            async with aiofiles.open(metadata_path, "r") as f:
                                metadata_str = await f.read()
                                metadata = json.loads(metadata_str)

                                # Get original key from metadata
                                original_key = metadata.get("key")

                                # Check expiration
                                expires_at = metadata.get("expires_at")
                                if expires_at is not None and time.time() > expires_at:
                                    # Expired, skip
                                    continue
                        except Exception as e:  # noqa: B112 - Intentional continue on error
                            # If metadata read fails, skip this file
                            logger.debug(f"Error reading metadata for {file_path}: {e}")
                            continue

                    # If no original key found, skip this file
                    if original_key is None:
                        continue

                    # Match pattern if provided
                    if pattern:
                        if "*" in pattern:
                            # Simple wildcard matching
                            pattern_parts = pattern.split("*")
                            if len(pattern_parts) == 2:
                                # Pattern like "prefix*" or "*suffix" or "*middle*"
                                if pattern.startswith("*") and pattern.endswith("*"):
                                    # *middle*
                                    middle = pattern_parts[1]
                                    if middle in original_key:
                                        keys.append(original_key)
                                elif pattern.startswith("*"):
                                    # *suffix
                                    suffix = pattern_parts[1]
                                    if original_key.endswith(suffix):
                                        keys.append(original_key)
                                elif pattern.endswith("*"):
                                    # prefix*
                                    prefix = pattern_parts[0]
                                    if original_key.startswith(prefix):
                                        keys.append(original_key)
                            # More complex pattern, use simple substring match
                            elif pattern.replace("*", "") in original_key:
                                keys.append(original_key)
                        # Exact match
                        elif original_key == pattern:
                            keys.append(original_key)
                    else:
                        keys.append(original_key)

            return keys
        except Exception as e:
            logger.warning(f"File cache keys error for pattern '{pattern}': {e}", exc_info=True)
            return []

    def size(self) -> int:
        """
        Get the current number of cache entries.

        Returns:
            Number of entries in the cache, or -1 if not available synchronously
        """
        # For synchronous access, we can't easily get the size
        # Return -1 to indicate it's not available synchronously
        # Size can be queried via async_size() if needed
        return -1

    async def async_size(self) -> int:
        """
        Get the current number of cache entries asynchronously.

        Returns:
            Number of entries in the cache
        """
        try:
            keys = await self.keys()
            return len(keys)
        except Exception as e:
            logger.warning(f"File cache size error: {e}", exc_info=True)
            return -1

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        try:
            removed = 0

            if not self.cache_dir.exists():
                return 0

            # Walk through cache directory
            for prefix_dir in self.cache_dir.iterdir():
                if not prefix_dir.is_dir():
                    continue

                # Scan files in prefix directory
                for file_path in prefix_dir.glob("*.json"):
                    # Skip metadata files
                    if file_path.name.endswith(".meta.json"):
                        continue

                    # Check expiration from metadata
                    metadata_path = file_path.with_suffix(".meta.json")
                    if metadata_path.exists():
                        try:
                            async with aiofiles.open(metadata_path, "r") as f:
                                metadata_str = await f.read()
                                metadata = json.loads(metadata_str)
                                expires_at = metadata.get("expires_at")

                                if expires_at is not None and time.time() > expires_at:
                                    # Expired, delete files
                                    original_key = metadata.get("key")
                                    if original_key:
                                        await self.delete(original_key)
                                        removed += 1
                        except Exception as e:
                            logger.debug(f"Error checking expiration for {file_path}: {e}")

            if removed > 0:
                logger.info(f"Cleaned up {removed} expired cache entries")
            return removed
        except Exception as e:
            logger.warning(f"File cache cleanup error: {e}", exc_info=True)
            return 0
