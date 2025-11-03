"""Cache manager for hass-mcp.

This module provides a singleton cache manager that initializes and manages
the appropriate cache backend based on configuration.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import CACHE_BACKEND, CACHE_ENABLED, CACHE_MAX_SIZE
from app.core.cache.backend import CacheBackend
from app.core.cache.memory import MemoryCacheBackend

logger = logging.getLogger(__name__)

# Global cache manager instance
_cache_manager: CacheManager | None = None


class CacheManager:
    """
    Singleton cache manager for global cache access.

    This class manages the cache backend and provides convenience methods
    for cache operations. It automatically initializes the appropriate
    backend based on configuration.
    """

    def __init__(self):
        """Initialize the cache manager with the configured backend."""
        self._backend: CacheBackend | None = None
        self._enabled = CACHE_ENABLED
        self._hits = 0
        self._misses = 0

    async def _get_backend(self) -> CacheBackend | None:
        """
        Get or initialize the cache backend.

        Returns:
            The cache backend instance, or None if caching is disabled
        """
        if not self._enabled:
            return None

        if self._backend is None:
            # Initialize backend based on configuration
            backend_type = CACHE_BACKEND.lower()

            if backend_type == "memory":
                self._backend = MemoryCacheBackend(max_size=CACHE_MAX_SIZE)
                logger.info(f"Initialized memory cache backend (max_size={CACHE_MAX_SIZE})")
            elif backend_type == "redis":
                # Redis backend will be implemented in US-009
                logger.warning("Redis backend not yet implemented, falling back to memory backend")
                self._backend = MemoryCacheBackend(max_size=CACHE_MAX_SIZE)
            elif backend_type == "file":
                # File backend will be implemented in US-010
                logger.warning("File backend not yet implemented, falling back to memory backend")
                self._backend = MemoryCacheBackend(max_size=CACHE_MAX_SIZE)
            else:
                logger.warning(
                    f"Unknown cache backend '{backend_type}', falling back to memory backend"
                )
                self._backend = MemoryCacheBackend(max_size=CACHE_MAX_SIZE)

        return self._backend

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve
            default: Default value to return if key not found

        Returns:
            The cached value if found, default otherwise
        """
        if not self._enabled:
            return default

        try:
            backend = await self._get_backend()
            if backend is None:
                return default

            value = await backend.get(key)
            if value is not None:
                self._hits += 1
                logger.debug(f"Cache hit: {key}")
                return value
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return default
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache get error for key '{key}': {e}", exc_info=True)
            self._misses += 1
            return default

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional Time-To-Live in seconds
        """
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            await backend.set(key, value, ttl)
            logger.debug(f"Cache set: {key} (ttl={ttl})")
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache set error for key '{key}': {e}", exc_info=True)

    async def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
        """
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            await backend.delete(key)
            logger.debug(f"Cache delete: {key}")
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache delete error for key '{key}': {e}", exc_info=True)

    async def invalidate(self, pattern: str) -> None:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match keys (supports wildcards like '*')
        """
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            # Get matching keys
            matching_keys = await backend.keys(pattern)
            if matching_keys:
                # Delete all matching keys
                for key in matching_keys:
                    await backend.delete(key)
                logger.info(
                    f"Cache invalidated: {len(matching_keys)} entries matching pattern '{pattern}'"
                )
            else:
                logger.debug(f"No cache entries found matching pattern '{pattern}'")
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache invalidation error for pattern '{pattern}': {e}", exc_info=True)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            await backend.clear()
            logger.info("Cache cleared")
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache clear error: {e}", exc_info=True)

    def get_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        stats = {
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 3),
        }

        # Add backend-specific stats if available
        if self._backend and hasattr(self._backend, "size"):
            stats["size"] = self._backend.size()

        return stats


async def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance (singleton pattern).

    Returns:
        The CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager()
        logger.info("Cache manager initialized")

    return _cache_manager
