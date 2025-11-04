"""Cache module for hass-mcp.

This module provides caching infrastructure to reduce API calls to Home Assistant.
"""

from app.core.cache.config import CacheConfig, get_cache_config
from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.invalidation import InvalidationStrategy
from app.core.cache.manager import CacheManager, get_cache_manager
from app.core.cache.metrics import CacheMetrics, get_cache_metrics
from app.core.cache.ttl import (
    TTL_DISABLED,
    TTL_LONG,
    TTL_MEDIUM,
    TTL_SHORT,
    TTL_VERY_LONG,
)

__all__ = [
    "CacheConfig",
    "CacheManager",
    "CacheMetrics",
    "InvalidationStrategy",
    "cached",
    "get_cache_config",
    "get_cache_manager",
    "get_cache_metrics",
    "invalidate_cache",
    "TTL_DISABLED",
    "TTL_SHORT",
    "TTL_MEDIUM",
    "TTL_LONG",
    "TTL_VERY_LONG",
]
