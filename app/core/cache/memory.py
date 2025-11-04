"""In-memory cache backend for hass-mcp.

This module provides an in-memory cache backend using Python dictionaries.
"""

import asyncio
import logging
import time
from typing import Any

from app.core.cache.backend import CacheBackend

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cache entry with value and expiration timestamp."""

    def __init__(self, value: Any, expires_at: float | None = None):
        """
        Initialize a cache entry.

        Args:
            value: The cached value
            expires_at: Optional expiration timestamp (Unix time)
        """
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class MemoryCacheBackend(CacheBackend):
    """
    In-memory cache backend using Python dictionaries.

    This backend stores cache entries in memory with TTL support.
    It uses OrderedDict for LRU-like behavior when max_size is reached.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the memory cache backend.

        Args:
            max_size: Maximum number of entries to store (default: 1000)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.max_size = max_size

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found and not expired, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check if expired
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                return None

            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional Time-To-Live in seconds. If None, entry doesn't expire
        """
        async with self._lock:
            # Calculate expiration timestamp
            expires_at = None
            if ttl and ttl > 0:
                expires_at = time.time() + ttl

            # Create cache entry
            entry = CacheEntry(value, expires_at)

            # Check if we need to evict entries (LRU-like behavior)
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Remove oldest entry (first in dict)
                if self._cache:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"Evicted cache entry: {oldest_key}")

            # Store the entry
            self._cache[key] = entry

    async def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists and is not expired, False otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return False

            # Check if expired
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                return False

            return True

    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        Get all cache keys, optionally filtered by pattern.

        Args:
            pattern: Optional pattern to match keys (supports wildcards like '*')

        Returns:
            List of matching cache keys (excluding expired entries)
        """
        async with self._lock:
            # Clean up expired entries first
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]

            # Get all keys
            all_keys = list(self._cache.keys())

            # Filter by pattern if provided
            if pattern:
                if "*" in pattern:
                    # Simple wildcard matching
                    pattern_parts = pattern.split("*")
                    if len(pattern_parts) == 2:
                        # Pattern like "prefix*" or "*suffix" or "*middle*"
                        if pattern.startswith("*") and pattern.endswith("*"):
                            # *middle*
                            middle = pattern_parts[1]
                            all_keys = [k for k in all_keys if middle in k]
                        elif pattern.startswith("*"):
                            # *suffix
                            suffix = pattern_parts[1]
                            all_keys = [k for k in all_keys if k.endswith(suffix)]
                        elif pattern.endswith("*"):
                            # prefix*
                            prefix = pattern_parts[0]
                            all_keys = [k for k in all_keys if k.startswith(prefix)]
                    else:
                        # More complex pattern, use simple substring match
                        all_keys = [k for k in all_keys if pattern.replace("*", "") in k]
                else:
                    # Exact match
                    all_keys = [k for k in all_keys if k == pattern]

            return all_keys

    def size(self) -> int:
        """
        Get the current number of cache entries.

        Returns:
            Number of entries in the cache
        """
        return len(self._cache)

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        async with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
