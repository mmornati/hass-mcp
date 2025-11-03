"""Abstract cache backend interface for hass-mcp.

This module defines the abstract interface that all cache backends must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """
    Abstract base class for cache backends.

    All cache backends must implement this interface to ensure consistent
    behavior across different storage mechanisms (memory, Redis, file, etc.).
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional Time-To-Live in seconds. If None, entry doesn't expire
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists, False otherwise
        """
        pass

    @abstractmethod
    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        Get all cache keys, optionally filtered by pattern.

        Args:
            pattern: Optional pattern to match keys (supports wildcards like '*')

        Returns:
            List of matching cache keys
        """
        pass
