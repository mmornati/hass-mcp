"""Test fixtures and utilities for cache testing."""

import asyncio
import tempfile
from contextlib import suppress
from typing import Any

import pytest

from app.core.cache.backend import CacheBackend
from app.core.cache.memory import MemoryCacheBackend


class MockCacheBackend(CacheBackend):
    """Mock cache backend for testing."""

    def __init__(self):
        """Initialize mock cache backend."""
        self._cache: dict[str, Any] = {}
        self._get_calls = 0
        self._set_calls = 0
        self._delete_calls = 0
        self._clear_calls = 0
        self._errors = False

    async def get(self, key: str) -> Any | None:
        """Mock get operation."""
        self._get_calls += 1
        if self._errors:
            raise Exception("Mock error")
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Mock set operation."""
        self._set_calls += 1
        if self._errors:
            raise Exception("Mock error")
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        """Mock delete operation."""
        self._delete_calls += 1
        if self._errors:
            raise Exception("Mock error")
        if key in self._cache:
            del self._cache[key]

    async def clear(self) -> None:
        """Mock clear operation."""
        self._clear_calls += 1
        if self._errors:
            raise Exception("Mock error")
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Mock exists operation."""
        return key in self._cache

    async def keys(self, pattern: str | None = None) -> list[str]:
        """Mock keys operation."""
        self._get_calls += 1  # Track calls
        if self._errors:
            raise Exception("Mock error")
        if pattern is None:
            return list(self._cache.keys())
        # Simple pattern matching
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return [k for k in self._cache if k.startswith(prefix)]
        return [k for k in self._cache if k == pattern]

    def get_call_count(self) -> dict[str, int]:
        """Get call counts for testing."""
        return {
            "get": self._get_calls,
            "set": self._set_calls,
            "delete": self._delete_calls,
            "clear": self._clear_calls,
        }

    def reset_call_count(self) -> None:
        """Reset call counts."""
        self._get_calls = 0
        self._set_calls = 0
        self._delete_calls = 0
        self._clear_calls = 0

    def enable_errors(self) -> None:
        """Enable error simulation."""
        self._errors = True

    def disable_errors(self) -> None:
        """Disable error simulation."""
        self._errors = False

    async def cleanup_expired(self) -> int:
        """Mock cleanup_expired operation."""
        if self._errors:
            raise Exception("Mock error")
        return 0


@pytest.fixture
def mock_cache_backend():
    """Create a mock cache backend for testing."""
    return MockCacheBackend()


@pytest.fixture
async def memory_cache_backend():
    """Create a memory cache backend for testing."""
    backend = MemoryCacheBackend(max_size=1000)
    yield backend
    await backend.clear()


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
async def file_cache_backend(temp_cache_dir):
    """Create a file cache backend for testing."""
    try:
        from app.core.cache.file import FileCacheBackend

        backend = FileCacheBackend(cache_dir=temp_cache_dir)
        yield backend
        with suppress(Exception):
            await backend.clear()
    except ImportError:
        pytest.skip("aiofiles not available for file backend tests")


@pytest.fixture
async def redis_cache_backend():
    """Create a Redis cache backend for testing (if Redis is available)."""
    try:
        from app.core.cache.redis import RedisCacheBackend

        redis_url = "redis://localhost:6379/0"
        backend = RedisCacheBackend(url=redis_url)
        try:
            await backend._get_client()
            yield backend
            with suppress(Exception):
                await backend.clear()
                await backend.close()
        except Exception:
            pytest.skip("Redis not available")
    except ImportError:
        pytest.skip("redis package not installed")


class PerformanceTimer:
    """Utility for measuring performance in tests."""

    def __init__(self):
        """Initialize performance timer."""
        self.start_time: float | None = None
        self.end_time: float | None = None

    def start(self) -> None:
        """Start timing."""
        self.start_time = asyncio.get_event_loop().time()

    def stop(self) -> None:
        """Stop timing."""
        self.end_time = asyncio.get_event_loop().time()

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


@pytest.fixture
def performance_timer():
    """Create a performance timer for testing."""
    return PerformanceTimer()


async def verify_cache_state(
    backend: CacheBackend, expected_keys: list[str], expected_values: dict[str, Any] | None = None
) -> bool:
    """
    Verify cache state matches expected values.

    Args:
        backend: Cache backend to verify
        expected_keys: List of expected cache keys
        expected_values: Optional dict of key-value pairs to verify

    Returns:
        True if cache state matches expectations, False otherwise
    """
    all_keys = await backend.keys()
    if len(all_keys) != len(expected_keys):
        return False

    for key in expected_keys:
        if key not in all_keys:
            return False
        if expected_values and key in expected_values:
            value = await backend.get(key)
            if value != expected_values[key]:
                return False

    return True


async def populate_cache(
    backend: CacheBackend, entries: dict[str, Any], ttl: int | None = None
) -> None:
    """
    Populate cache with test data.

    Args:
        backend: Cache backend to populate
        entries: Dictionary of key-value pairs to cache
        ttl: Optional TTL for all entries
    """
    for key, value in entries.items():
        await backend.set(key, value, ttl=ttl)


async def measure_cache_operation(operation, *args, **kwargs) -> tuple[Any, float]:
    """
    Measure the time taken for a cache operation.

    Args:
        operation: Async function to measure
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Tuple of (result, elapsed_time_ms)
    """
    timer = PerformanceTimer()
    timer.start()
    result = await operation(*args, **kwargs)
    timer.stop()
    return result, timer.elapsed_ms()
