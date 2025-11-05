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
from app.core.cache.invalidation import InvalidationStrategy
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
                try:
                    # Import is done here to avoid circular imports and allow optional dependency
                    from app.core.cache.redis import RedisCacheBackend  # noqa: PLC0415

                    redis_url = self._config.get_redis_url()
                    if not redis_url:
                        logger.warning(
                            "Redis backend selected but no Redis URL configured. "
                            "Falling back to memory backend. "
                            "Set HASS_MCP_CACHE_REDIS_URL environment variable."
                        )
                        self._backend = MemoryCacheBackend(max_size=max_size)
                    else:
                        self._backend = RedisCacheBackend(url=redis_url)
                        logger.info(f"Initialized Redis cache backend (url={redis_url})")
                except ImportError as e:
                    logger.warning(
                        f"Redis package not installed: {e}. "
                        "Install it with: pip install redis or uv pip install redis. "
                        "Falling back to memory backend."
                    )
                    self._backend = MemoryCacheBackend(max_size=max_size)
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize Redis backend: {e}. Falling back to memory backend.",
                        exc_info=True,
                    )
                    self._backend = MemoryCacheBackend(max_size=max_size)
            elif backend_type == "file":
                try:
                    # Import is done here to avoid circular imports and allow optional dependency
                    from app.core.cache.file import FileCacheBackend  # noqa: PLC0415

                    cache_dir = self._config.get_cache_dir()
                    self._backend = FileCacheBackend(cache_dir=cache_dir)
                    logger.info(f"Initialized file cache backend (cache_dir={cache_dir})")
                except ImportError as e:
                    logger.warning(
                        f"File backend package not installed: {e}. "
                        "Install it with: pip install aiofiles or uv pip install aiofiles. "
                        "Falling back to memory backend."
                    )
                    self._backend = MemoryCacheBackend(max_size=max_size)
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize file backend: {e}. Falling back to memory backend.",
                        exc_info=True,
                    )
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

    async def invalidate(
        self, pattern: str, hierarchical: bool = True, expand_children: bool = True
    ) -> dict[str, Any]:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match keys (supports wildcards like '*')
            hierarchical: If True, also invalidate hierarchical children (default: True)
            expand_children: If True, expand pattern to include child patterns (default: True)

        Returns:
            Dictionary with invalidation results:
            - pattern: Original pattern
            - expanded_patterns: List of patterns that were invalidated
            - total_invalidated: Total number of cache entries invalidated
            - keys_invalidated: List of cache keys that were invalidated
        """
        if not self._enabled:
            return {
                "pattern": pattern,
                "expanded_patterns": [],
                "total_invalidated": 0,
                "keys_invalidated": [],
            }

        try:
            backend = await self._get_backend()
            if backend is None:
                return {
                    "pattern": pattern,
                    "expanded_patterns": [],
                    "total_invalidated": 0,
                    "keys_invalidated": [],
                }

            # Expand pattern to include hierarchical children if requested
            patterns_to_invalidate = [pattern]
            if expand_children and hierarchical:
                expanded = InvalidationStrategy.expand_pattern(pattern)
                patterns_to_invalidate = expanded

            # Collect all matching keys
            all_invalidated_keys: list[str] = []
            total_invalidated = 0

            for invalidation_pattern in patterns_to_invalidate:
                matching_keys = await backend.keys(invalidation_pattern)
                if matching_keys:
                    # Delete all matching keys
                    for key in matching_keys:
                        if key not in all_invalidated_keys:
                            await backend.delete(key)
                            all_invalidated_keys.append(key)
                            total_invalidated += 1

            if total_invalidated > 0:
                self._metrics.record_invalidation(pattern)
                logger.info(
                    f"Cache invalidated: {total_invalidated} entries matching pattern '{pattern}' "
                    f"(expanded to {len(patterns_to_invalidate)} patterns)",
                    extra={
                        "pattern": pattern,
                        "expanded_patterns": patterns_to_invalidate,
                        "count": total_invalidated,
                        "keys": all_invalidated_keys[:10],  # Log first 10 keys
                    },
                )
            else:
                logger.debug(
                    f"No cache entries found matching pattern '{pattern}' "
                    f"(checked {len(patterns_to_invalidate)} patterns)",
                    extra={"pattern": pattern, "expanded_patterns": patterns_to_invalidate},
                )

            return {
                "pattern": pattern,
                "expanded_patterns": patterns_to_invalidate,
                "total_invalidated": total_invalidated,
                "keys_invalidated": all_invalidated_keys,
            }
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache invalidation error for pattern '{pattern}': {e}", exc_info=True)
            return {
                "pattern": pattern,
                "expanded_patterns": [],
                "total_invalidated": 0,
                "keys_invalidated": [],
                "error": str(e),
            }

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

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        This method proactively cleans up expired entries that haven't
        been automatically removed during get operations.

        Returns:
            Number of expired entries removed
        """
        if not self._enabled:
            return 0

        try:
            backend = await self._get_backend()
            if backend is None:
                return 0

            # Check if backend supports cleanup
            if hasattr(backend, "cleanup_expired"):
                removed = await backend.cleanup_expired()
                if removed > 0:
                    logger.info(f"Cleaned up {removed} expired cache entries")
                return removed
            # For backends without explicit cleanup, use keys() which auto-cleans
            # This will trigger cleanup of expired entries
            await backend.keys(None)
            return 0
        except Exception as e:
            # Never break API calls on cache errors
            logger.warning(f"Cache cleanup error: {e}", exc_info=True)
            return 0

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
