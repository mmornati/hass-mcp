"""Redis cache backend for hass-mcp.

This module provides a Redis cache backend implementation for distributed caching.
Redis backend allows cache to be shared across multiple MCP server instances and
survive server restarts.
"""

from __future__ import annotations

import json
import logging
import pickle  # nosec B403 - Used for serializing complex types in trusted cache
from typing import Any

try:
    import redis.asyncio as redis
    from redis.exceptions import (
        ConnectionError as RedisConnectionError,
    )
    from redis.exceptions import (
        DataError as RedisDataError,
    )
    from redis.exceptions import (
        RedisError,
    )
    from redis.exceptions import (
        TimeoutError as RedisTimeoutError,
    )
except ImportError:
    redis = None  # type: ignore[assignment]
    # Define fallback exception classes for when redis is not installed
    RedisConnectionError = Exception  # type: ignore[assignment, misc]
    RedisDataError = Exception  # type: ignore[assignment, misc]
    RedisError = Exception  # type: ignore[assignment, misc]
    RedisTimeoutError = Exception  # type: ignore[assignment, misc]

from app.core.cache.backend import CacheBackend

logger = logging.getLogger(__name__)


class RedisCacheBackend(CacheBackend):
    """
    Redis cache backend using redis.asyncio.

    This backend stores cache entries in Redis with TTL support.
    It uses connection pooling and handles reconnection automatically.
    """

    def __init__(self, url: str, decode_responses: bool = False):
        """
        Initialize the Redis cache backend.

        Args:
            url: Redis connection URL (e.g., 'redis://localhost:6379/0')
            decode_responses: If True, decode responses as strings (default: False for binary data)

        Raises:
            ImportError: If redis package is not installed
            ValueError: If Redis URL is invalid
        """
        # Import redis from the module to get the current value (may be updated in tests)
        # This is intentionally done at runtime to support test mocking
        import app.core.cache.redis as redis_module  # noqa: PLC0415

        current_redis = redis_module.redis

        # Check if redis is None
        # Note: In tests, redis may be a mock, so we allow it to pass
        # The actual validation happens when we try to use redis.ConnectionPool.from_url
        if current_redis is None:
            raise ImportError("Redis package is not installed. Install it with: pip install redis")

        # Use the current redis value (may be updated in tests)
        self._redis = current_redis

        self.url = url
        self.decode_responses = decode_responses
        self._client: Any | None = None  # Type: redis.Redis[bytes] | None
        self._connection_pool: Any | None = None  # Type: redis.ConnectionPool | None

    async def _get_client(self) -> Any:  # Type: redis.Redis[bytes]
        """
        Get or create Redis client.

        Returns:
            Redis client instance

        Raises:
            redis.ConnectionError: If connection to Redis fails
        """
        if self._client is None:
            try:
                # Create connection pool for better performance
                self._connection_pool = self._redis.ConnectionPool.from_url(
                    self.url,
                    decode_responses=self.decode_responses,
                    max_connections=10,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                self._client = self._redis.Redis(
                    connection_pool=self._connection_pool,
                    decode_responses=self.decode_responses,
                )

                # Test connection
                await self._client.ping()
                logger.info(f"Connected to Redis at {self.url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
                raise

        return self._client

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize a value for storage in Redis.

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
        Deserialize a value from Redis.

        Args:
            data: Serialized bytes from Redis

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
                # nosec B301 - Cache data is trusted (from our own Redis instance)
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
            The cached value if found, None otherwise
        """
        try:
            client = await self._get_client()
            data = await client.get(key)

            if data is None:
                return None

            return self._deserialize(data)
        except (RedisConnectionError, RedisTimeoutError, RedisError, ValueError) as e:
            logger.warning(f"Redis get error for key '{key}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.warning(f"Redis get error for key '{key}': {e}", exc_info=True)
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
            client = await self._get_client()
            data = self._serialize(value)

            if ttl and ttl > 0:
                # Use SETEX for set with expiration
                await client.setex(key, ttl, data)
            else:
                # Set without expiration
                await client.set(key, data)
        except (RedisConnectionError, RedisTimeoutError, RedisError, ValueError) as e:
            logger.warning(f"Redis set error for key '{key}': {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Redis set error for key '{key}': {e}", exc_info=True)

    async def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete
        """
        try:
            client = await self._get_client()
            await client.delete(key)
        except (RedisConnectionError, RedisTimeoutError, RedisError) as e:
            logger.warning(f"Redis delete error for key '{key}': {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Redis delete error for key '{key}': {e}", exc_info=True)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        try:
            client = await self._get_client()
            # Use FLUSHDB to clear current database (not FLUSHALL which clears all databases)
            await client.flushdb()
            logger.info("Redis cache cleared")
        except (RedisConnectionError, RedisTimeoutError, RedisError) as e:
            logger.warning(f"Redis clear error: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Redis clear error: {e}", exc_info=True)

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists, False otherwise
        """
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return bool(result)
        except (RedisConnectionError, RedisTimeoutError, RedisError) as e:
            logger.warning(f"Redis exists error for key '{key}': {e}", exc_info=True)
            return False
        except Exception as e:
            logger.warning(f"Redis exists error for key '{key}': {e}", exc_info=True)
            return False

    async def keys(self, pattern: str | None = None) -> list[str]:
        """
        Get all cache keys, optionally filtered by pattern.

        Args:
            pattern: Optional pattern to match keys (supports wildcards like '*')

        Returns:
            List of matching cache keys

        Note:
            Uses SCAN instead of KEYS for production-safe pattern matching.
            SCAN is non-blocking and iterates over the keyspace incrementally.
        """
        try:
            client = await self._get_client()
            keys: list[str] = []

            if pattern:
                # Use SCAN for pattern matching (non-blocking, production-safe)
                async for key in client.scan_iter(match=pattern):
                    if isinstance(key, bytes):
                        keys.append(key.decode("utf-8"))
                    else:
                        keys.append(key)
            else:
                # Get all keys (use SCAN with no pattern)
                async for key in client.scan_iter():
                    if isinstance(key, bytes):
                        keys.append(key.decode("utf-8"))
                    else:
                        keys.append(key)

            return keys
        except (RedisConnectionError, RedisTimeoutError, RedisError) as e:
            logger.warning(f"Redis keys error for pattern '{pattern}': {e}", exc_info=True)
            return []
        except Exception as e:
            logger.warning(f"Redis keys error for pattern '{pattern}': {e}", exc_info=True)
            return []

    def size(self) -> int:
        """
        Get the current number of cache entries.

        Returns:
            Number of entries in the current Redis database, or -1 if not available

        Note:
            This is a synchronous wrapper. For accurate size, use async_size().
            Uses cached size if available, otherwise returns -1.
        """
        # For synchronous access, we can't easily get the size
        # Return -1 to indicate it's not available synchronously
        # Size can be queried via get_statistics_async() if needed
        return -1

    async def async_size(self) -> int:
        """
        Get the current number of cache entries asynchronously.

        Returns:
            Number of entries in the current Redis database

        Note:
            Uses DBSIZE command which is fast and accurate for the current database.
        """
        try:
            client = await self._get_client()
            return await client.dbsize()
        except Exception as e:
            logger.warning(f"Redis size error: {e}", exc_info=True)
            return -1

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Redis automatically removes expired entries, so this method
        just checks for and removes any expired keys manually.

        Returns:
            Number of expired entries removed (always 0 for Redis as it's automatic)
        """
        # Redis automatically handles TTL expiration, so no cleanup needed
        # But we can verify connection is healthy
        try:
            client = await self._get_client()
            await client.ping()
            return 0
        except Exception as e:
            logger.warning(f"Redis cleanup check error: {e}", exc_info=True)
            return 0

    async def close(self) -> None:
        """
        Close Redis connection pool.

        This should be called when the backend is no longer needed.
        """
        if self._client:
            try:
                await self._client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}", exc_info=True)
            finally:
                self._client = None
                self._connection_pool = None
