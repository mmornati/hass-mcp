"""Cache module for hass-mcp.

This module provides caching infrastructure to reduce API calls to Home Assistant.
"""

from app.core.cache.manager import CacheManager, get_cache_manager
from app.core.cache.ttl import (
    TTL_DISABLED,
    TTL_LONG,
    TTL_MEDIUM,
    TTL_SHORT,
    TTL_VERY_LONG,
)

__all__ = [
    "CacheManager",
    "get_cache_manager",
    "TTL_DISABLED",
    "TTL_SHORT",
    "TTL_MEDIUM",
    "TTL_LONG",
    "TTL_VERY_LONG",
]
