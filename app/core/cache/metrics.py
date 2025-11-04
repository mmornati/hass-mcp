"""Cache metrics for hass-mcp.

This module provides cache metrics collection and per-endpoint statistics tracking.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any

logger = None  # Will be set when logging is imported


@dataclass
class EndpointStats:
    """Statistics for a specific endpoint."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    total_api_time_ms: float = 0.0
    total_cache_time_ms: float = 0.0
    api_call_count: int = 0
    cache_call_count: int = 0

    def hit_rate(self) -> float:
        """Calculate hit rate for this endpoint."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def avg_api_time_ms(self) -> float:
        """Calculate average API call time in milliseconds."""
        return self.total_api_time_ms / self.api_call_count if self.api_call_count > 0 else 0.0

    def avg_cache_time_ms(self) -> float:
        """Calculate average cache retrieval time in milliseconds."""
        return (
            self.total_cache_time_ms / self.cache_call_count if self.cache_call_count > 0 else 0.0
        )

    def time_saved_ms(self) -> float:
        """Calculate average time saved per request by using cache."""
        if self.api_call_count == 0:
            return 0.0
        avg_api_time = self.avg_api_time_ms()
        avg_cache_time = self.avg_cache_time_ms()
        return avg_api_time - avg_cache_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": round(self.hit_rate(), 3),
            "avg_api_time_ms": round(self.avg_api_time_ms(), 2),
            "avg_cache_time_ms": round(self.avg_cache_time_ms(), 2),
            "time_saved_ms": round(self.time_saved_ms(), 2),
            "api_call_count": self.api_call_count,
            "cache_call_count": self.cache_call_count,
        }


class CacheMetrics:
    """
    Cache metrics collector.

    This class tracks cache statistics including hits, misses, sets, deletes,
    and per-endpoint statistics. It is thread-safe and provides methods
    for querying statistics.
    """

    def __init__(self):
        """Initialize cache metrics."""
        self._lock = Lock()
        self._total_hits = 0
        self._total_misses = 0
        self._total_sets = 0
        self._total_deletes = 0
        self._total_invalidations = 0
        self._per_endpoint: dict[str, EndpointStats] = defaultdict(EndpointStats)
        self._start_time = time.time()

    def record_hit(self, endpoint: str, cache_time_ms: float = 0.0) -> None:
        """Record a cache hit."""
        with self._lock:
            self._total_hits += 1
            stats = self._per_endpoint[endpoint]
            stats.hits += 1
            stats.cache_call_count += 1
            if cache_time_ms > 0:
                stats.total_cache_time_ms += cache_time_ms

    def record_miss(self, endpoint: str) -> None:
        """Record a cache miss."""
        with self._lock:
            self._total_misses += 1
            self._per_endpoint[endpoint].misses += 1

    def record_set(self, endpoint: str) -> None:
        """Record a cache set operation."""
        with self._lock:
            self._total_sets += 1
            self._per_endpoint[endpoint].sets += 1

    def record_delete(self, endpoint: str) -> None:
        """Record a cache delete operation."""
        with self._lock:
            self._total_deletes += 1
            self._per_endpoint[endpoint].deletes += 1

    def record_invalidation(self, pattern: str) -> None:
        """Record a cache invalidation operation."""
        with self._lock:
            self._total_invalidations += 1

    def record_api_call(self, endpoint: str, api_time_ms: float) -> None:
        """Record an API call with its duration."""
        with self._lock:
            stats = self._per_endpoint[endpoint]
            stats.api_call_count += 1
            stats.total_api_time_ms += api_time_ms

    def get_total_hits(self) -> int:
        """Get total cache hits."""
        with self._lock:
            return self._total_hits

    def get_total_misses(self) -> int:
        """Get total cache misses."""
        with self._lock:
            return self._total_misses

    def get_total_sets(self) -> int:
        """Get total cache sets."""
        with self._lock:
            return self._total_sets

    def get_total_deletes(self) -> int:
        """Get total cache deletes."""
        with self._lock:
            return self._total_deletes

    def get_total_invalidations(self) -> int:
        """Get total cache invalidations."""
        with self._lock:
            return self._total_invalidations

    def hit_rate(self) -> float:
        """Calculate overall hit rate."""
        with self._lock:
            total = self._total_hits + self._total_misses
            return self._total_hits / total if total > 0 else 0.0

    def get_endpoint_stats(self, endpoint: str) -> EndpointStats:
        """Get statistics for a specific endpoint."""
        with self._lock:
            return self._per_endpoint[endpoint]

    def get_all_endpoint_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all endpoints."""
        with self._lock:
            return {endpoint: stats.to_dict() for endpoint, stats in self._per_endpoint.items()}

    def get_top_endpoints(
        self, limit: int = 10, sort_by: str = "hits"
    ) -> list[tuple[str, dict[str, Any]]]:
        """
        Get top endpoints by a specific metric.

        Args:
            limit: Maximum number of endpoints to return
            sort_by: Metric to sort by ('hits', 'misses', 'hit_rate', 'time_saved_ms')

        Returns:
            List of tuples (endpoint, stats_dict) sorted by the specified metric
        """
        with self._lock:
            endpoints = [(ep, stats.to_dict()) for ep, stats in self._per_endpoint.items()]

            if sort_by == "hits":
                endpoints.sort(key=lambda x: x[1]["hits"], reverse=True)
            elif sort_by == "misses":
                endpoints.sort(key=lambda x: x[1]["misses"], reverse=True)
            elif sort_by == "hit_rate":
                endpoints.sort(key=lambda x: x[1]["hit_rate"], reverse=True)
            elif sort_by == "time_saved_ms":
                endpoints.sort(key=lambda x: x[1]["time_saved_ms"], reverse=True)
            else:
                endpoints.sort(key=lambda x: x[1]["hits"], reverse=True)

            return endpoints[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get complete cache statistics."""
        with self._lock:
            total_requests = self._total_hits + self._total_misses
            uptime_seconds = time.time() - self._start_time

            # Calculate overall performance metrics
            total_api_time = sum(stats.total_api_time_ms for stats in self._per_endpoint.values())
            total_cache_time = sum(
                stats.total_cache_time_ms for stats in self._per_endpoint.values()
            )
            total_api_calls = sum(stats.api_call_count for stats in self._per_endpoint.values())
            total_cache_calls = sum(stats.cache_call_count for stats in self._per_endpoint.values())

            avg_api_time = total_api_time / total_api_calls if total_api_calls > 0 else 0.0
            avg_cache_time = total_cache_time / total_cache_calls if total_cache_calls > 0 else 0.0
            time_saved = avg_api_time - avg_cache_time if avg_api_time > 0 else 0.0

            return {
                "total_hits": self._total_hits,
                "total_misses": self._total_misses,
                "total_sets": self._total_sets,
                "total_deletes": self._total_deletes,
                "total_invalidations": self._total_invalidations,
                "total_requests": total_requests,
                "hit_rate": round(self.hit_rate(), 3),
                "uptime_seconds": round(uptime_seconds, 2),
                "performance": {
                    "avg_api_time_ms": round(avg_api_time, 2),
                    "avg_cache_time_ms": round(avg_cache_time, 2),
                    "time_saved_ms": round(time_saved, 2),
                    "total_api_calls": total_api_calls,
                    "total_cache_calls": total_cache_calls,
                },
                "endpoint_count": len(self._per_endpoint),
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._total_hits = 0
            self._total_misses = 0
            self._total_sets = 0
            self._total_deletes = 0
            self._total_invalidations = 0
            self._per_endpoint.clear()
            self._start_time = time.time()


# Global metrics instance
_metrics: CacheMetrics | None = None


def get_cache_metrics() -> CacheMetrics:
    """
    Get the global cache metrics instance (singleton pattern).

    Returns:
        The CacheMetrics instance
    """
    global _metrics

    if _metrics is None:
        _metrics = CacheMetrics()

    return _metrics
