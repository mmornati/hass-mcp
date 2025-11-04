"""Cache manager for hass-mcp.

This module provides a singleton cache manager that initializes and manages
the appropriate cache backend based on configuration.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.cache.backend import CacheBackend
from app.core.cache.config import get_cache_config
from app.core.cache.memory import MemoryCacheBackend
from app.core.cache.metrics import get_cache_metrics

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
        self._config = get_cache_config()
        self._enabled = self._config.is_enabled()
        self._hits = 0
        self._misses = 0
        self._metrics = get_cache_metrics()

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
            backend_type = self._config.get_backend().lower()
            max_size = self._config.get_max_size()

            if backend_type == "memory":
                self._backend = MemoryCacheBackend(max_size=max_size)
                logger.info(f"Initialized memory cache backend (max_size={max_size})")
            elif backend_type == "redis":
                # Redis backend will be implemented in US-009
                logger.warning("Redis backend not yet implemented, falling back to memory backend")
                self._backend = MemoryCacheBackend(max_size=max_size)
            elif backend_type == "file":
                # File backend will be implemented in US-010
                logger.warning("File backend not yet implemented, falling back to memory backend")
                self._backend = MemoryCacheBackend(max_size=max_size)
            else:
                logger.warning(
                    f"Unknown cache backend '{backend_type}', falling back to memory backend"
                )
                self._backend = MemoryCacheBackend(max_size=max_size)

        return self._backend

    async def get(self, key: str, default: Any = None, endpoint: str | None = None) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve
            default: Default value to return if key not found
            endpoint: Optional endpoint identifier for metrics tracking

        Returns:
            The cached value if found, default otherwise
        """
        if not self._enabled:
            return default

        start_time = time.time()
        try:
            backend = await self._get_backend()
            if backend is None:
                return default

            value = await backend.get(key)
            cache_time_ms = (time.time() - start_time) * 1000

            if value is not None:
                self._hits += 1
                if endpoint:
                    self._metrics.record_hit(endpoint, cache_time_ms)
                logger.debug(f"Cache hit: {key}", extra={"cache_key": key, "endpoint": endpoint})
                return value
            self._misses += 1
            if endpoint:
                self._metrics.record_miss(endpoint)
            logger.debug(f"Cache miss: {key}", extra={"cache_key": key, "endpoint": endpoint})
            return default
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache get error for key '{key}': {e}", exc_info=True)
            self._misses += 1
            if endpoint:
                self._metrics.record_miss(endpoint)
            return default

    async def set(
        self, key: str, value: Any, ttl: int | None = None, endpoint: str | None = None
    ) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional Time-To-Live in seconds
            endpoint: Optional endpoint identifier for metrics tracking
        """
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            await backend.set(key, value, ttl)
            if endpoint:
                self._metrics.record_set(endpoint)
            logger.debug(
                f"Cache set: {key} (ttl={ttl})",
                extra={"cache_key": key, "endpoint": endpoint, "ttl": ttl},
            )
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache set error for key '{key}': {e}", exc_info=True)

    async def delete(self, key: str, endpoint: str | None = None) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
            endpoint: Optional endpoint identifier for metrics tracking
        """
        if not self._enabled:
            return

        try:
            backend = await self._get_backend()
            if backend is None:
                return

            await backend.delete(key)
            if endpoint:
                self._metrics.record_delete(endpoint)
            logger.debug(f"Cache delete: {key}", extra={"cache_key": key, "endpoint": endpoint})
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
                self._metrics.record_invalidation(pattern)
                logger.info(
                    f"Cache invalidated: {len(matching_keys)} entries matching pattern '{pattern}'",
                    extra={"pattern": pattern, "count": len(matching_keys)},
                )
            else:
                logger.debug(
                    f"No cache entries found matching pattern '{pattern}'",
                    extra={"pattern": pattern},
                )
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

    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        Get cache keys matching a pattern.

        Args:
            pattern: Optional pattern to match keys (supports wildcards like '*')

        Returns:
            List of matching cache keys
        """
        if not self._enabled:
            return []

        try:
            backend = await self._get_backend()
            if backend is None:
                return []

            return await backend.keys(pattern)
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache keys error for pattern '{pattern}': {e}", exc_info=True)
            return []

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
            "backend": self._config.get_backend(),
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 3),
        }

        # Add backend-specific stats if available
        if self._backend and hasattr(self._backend, "size"):
            stats["size"] = self._backend.size()

        # Add detailed metrics
        metrics_stats = self._metrics.get_statistics()
        stats["statistics"] = metrics_stats
        stats["per_endpoint"] = self._metrics.get_all_endpoint_stats()

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
