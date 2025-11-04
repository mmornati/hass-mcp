"""Cache decorators for hass-mcp.

This module provides decorators for automatic caching of API function results.
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.core.cache.config import get_cache_config
from app.core.cache.key_builder import CacheKeyBuilder
from app.core.cache.manager import get_cache_manager
from app.core.cache.metrics import get_cache_metrics

logger = logging.getLogger(__name__)

# Generic type variable for async functions
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def cached(
    ttl: int | Callable[[tuple[Any, ...], dict[str, Any], Any], int] | None = None,
    key_prefix: str | None = None,
    include_params: list[str] | None = None,
    exclude_params: list[str] | None = None,
    condition: Callable[[tuple[Any, ...], dict[str, Any], Any], bool] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to automatically cache function results.

    This decorator caches the results of async functions based on their
    parameters. It automatically generates cache keys from the function
    name, module path, and normalized parameters.

    Args:
        ttl: Time-To-Live in seconds (uses default if None)
        key_prefix: Custom key prefix (defaults to function module path)
        include_params: List of parameter names to include in cache key
        exclude_params: List of parameter names to exclude from cache key
        condition: Function to determine if result should be cached.
                   Receives (args, kwargs, result) and returns bool.

    Returns:
        Decorator function

    Examples:
        @cached(ttl=300)
        async def get_entities(domain: str | None = None):
            ...

        @cached(
            ttl=1800,
            key_prefix="automations",
            exclude_params=["detailed"],
            condition=lambda args, kwargs, result: "error" not in result
        )
        async def get_automations():
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache manager and metrics
            cache = await get_cache_manager()
            metrics = get_cache_metrics()

            # Build cache key
            cache_key = _build_cache_key(
                func=func,
                args=args,
                kwargs=kwargs,
                key_prefix=key_prefix,
                include_params=include_params,
                exclude_params=exclude_params,
            )

            # Build endpoint identifier
            module_path = func.__module__ or "unknown"
            # Extract domain from module path (e.g., "app.api.entities" -> "entities")
            domain = module_path.split(".")[-1] if "." in module_path else module_path
            operation = func.__name__
            endpoint = f"{domain}:{operation}"

            # Try to get from cache
            try:
                cached_value = await cache.get(cache_key, endpoint=endpoint)
                if cached_value is not None:
                    logger.debug(
                        f"Cache hit for {func.__name__}: {cache_key}",
                        extra={"cache_key": cache_key, "endpoint": endpoint},
                    )
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache get error for {func.__name__}: {e}", exc_info=True)

            # Cache miss - call the function
            logger.debug(
                f"Cache miss for {func.__name__}: {cache_key}",
                extra={"cache_key": cache_key, "endpoint": endpoint},
            )
            try:
                # Record API call start time
                api_start_time = time.time()
                result = await func(*args, **kwargs)
                api_time_ms = (time.time() - api_start_time) * 1000
                metrics.record_api_call(endpoint, api_time_ms)

                # Default condition: don't cache error responses
                # Check if result is an error response (dict with "error" key or list with error dict)
                is_error_response = False
                if isinstance(result, dict) and "error" in result:
                    is_error_response = True
                elif isinstance(result, list) and len(result) == 1:
                    if isinstance(result[0], dict) and "error" in result[0]:
                        is_error_response = True

                # Check condition if provided
                if condition is not None:
                    try:
                        if not condition(args, kwargs, result):
                            logger.debug(
                                f"Condition failed, not caching result for {func.__name__}"
                            )
                            return result
                    except Exception as e:
                        logger.warning(
                            f"Condition check error for {func.__name__}: {e}", exc_info=True
                        )
                        # If condition check fails, don't cache (safer)
                        return result
                elif is_error_response:
                    # Don't cache error responses by default
                    logger.debug(f"Skipping cache for error response in {func.__name__}")
                    return result

                # Determine TTL: explicit > callable > endpoint config > default
                cache_ttl = None
                if callable(ttl):
                    # TTL is a callable function - call it with args, kwargs, result
                    try:
                        cache_ttl = ttl(args, kwargs, result)
                    except Exception as e:
                        logger.warning(
                            f"TTL callable error for {func.__name__}: {e}", exc_info=True
                        )
                        # Fall back to default TTL if callable fails
                        cache_ttl = None
                elif ttl is not None:
                    # TTL is a fixed value
                    cache_ttl = ttl

                if cache_ttl is None:
                    # Try to get TTL from endpoint configuration
                    config = get_cache_config()
                    module_path = func.__module__ or "unknown"
                    # Extract domain from module path (e.g., "app.api.entities" -> "entities")
                    domain = module_path.split(".")[-1] if "." in module_path else module_path
                    operation = func.__name__
                    endpoint_ttl = config.get_endpoint_ttl(domain, operation)
                    if endpoint_ttl is not None:
                        cache_ttl = endpoint_ttl
                    else:
                        cache_ttl = config.get_default_ttl()

                    # Store in cache
                    try:
                        await cache.set(cache_key, result, ttl=cache_ttl, endpoint=endpoint)
                        logger.debug(
                            f"Cached result for {func.__name__}: {cache_key} (ttl={cache_ttl})",
                            extra={"cache_key": cache_key, "endpoint": endpoint, "ttl": cache_ttl},
                        )
                    except Exception as e:
                        logger.warning(f"Cache set error for {func.__name__}: {e}", exc_info=True)
                        # Don't fail the function call if cache set fails

                return result
            except Exception as e:
                # If function fails, don't try to cache
                logger.error(f"Function {func.__name__} failed: {e}", exc_info=True)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def invalidate_cache(
    pattern: str | None = None,
    patterns: list[str] | None = None,
    condition: Callable[[tuple[Any, ...], dict[str, Any], Any], bool] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to invalidate cache entries after function execution.

    This decorator is used for mutation functions (create, update, delete)
    to invalidate related cache entries after the operation completes.

    Args:
        pattern: Single pattern to match cache keys (supports wildcards like '*')
        patterns: List of patterns to match cache keys
        condition: Function to determine if cache should be invalidated.
                   Receives (args, kwargs, result) and returns bool.

    Returns:
        Decorator function

    Examples:
        @invalidate_cache(pattern="entities:*")
        async def create_entity(entity_id: str):
            ...

        @invalidate_cache(
            patterns=["automations:*", "entities:*"],
            condition=lambda args, kwargs, result: result.get("status") == "success"
        )
        async def update_automation(automation_id: str, config: dict):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute the function first
            result = await func(*args, **kwargs)

            # Check condition if provided
            if condition is not None:
                try:
                    if not condition(args, kwargs, result):
                        logger.debug(
                            f"Condition failed, not invalidating cache for {func.__name__}"
                        )
                        return result
                except Exception as e:
                    logger.warning(f"Condition check error for {func.__name__}: {e}", exc_info=True)
                    # If condition check fails, invalidate anyway (safer)
                    pass

            # Get cache manager
            cache = await get_cache_manager()

            # Collect patterns to invalidate
            patterns_to_invalidate: list[str] = []
            if pattern:
                patterns_to_invalidate.append(pattern)
            if patterns:
                patterns_to_invalidate.extend(patterns)

            # Invalidate each pattern
            for invalidation_pattern in patterns_to_invalidate:
                try:
                    await cache.invalidate(invalidation_pattern)
                    logger.debug(
                        f"Invalidated cache pattern '{invalidation_pattern}' for {func.__name__}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Cache invalidation error for {func.__name__}: {e}", exc_info=True
                    )
                    # Don't fail the function call if invalidation fails

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def _build_cache_key(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_prefix: str | None = None,
    include_params: list[str] | None = None,
    exclude_params: list[str] | None = None,
) -> str:
    """
    Build a cache key from function signature and arguments.

    Args:
        func: The function to build a key for
        args: Positional arguments
        kwargs: Keyword arguments
        key_prefix: Custom key prefix
        include_params: List of parameter names to include
        exclude_params: List of parameter names to exclude

    Returns:
        Cache key string
    """
    # Get function signature
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    # Build parameter dictionary
    params: dict[str, Any] = dict(bound_args.arguments)

    # Filter parameters based on include/exclude
    if include_params:
        params = {k: v for k, v in params.items() if k in include_params}
    if exclude_params:
        params = {k: v for k, v in params.items() if k not in exclude_params}

    # Get module path
    module_path = func.__module__ or "unknown"

    # Keep None values - they should be part of the cache key
    # None values are meaningful for cache key generation

    # Build cache key using CacheKeyBuilder
    # Extract domain from module path (e.g., "app.api.entities" -> "entities")
    domain = module_path.split(".")[-1] if "." in module_path else module_path
    operation = func.__name__

    # Use CacheKeyBuilder to normalize parameters
    normalized_params = CacheKeyBuilder.normalize_params(params)
    cache_key = CacheKeyBuilder.build_key(domain, operation, normalized_params)

    # Add prefix if provided
    if key_prefix:
        # If key_prefix is provided, use it as the prefix
        cache_key = (
            f"{key_prefix}:{cache_key.lstrip(key_prefix + ':')}"
            if cache_key.startswith(key_prefix)
            else f"{key_prefix}:{cache_key}"
        )
    else:
        # Use module path as prefix
        cache_key = f"api:{module_path}:{cache_key}"

    return cache_key


def _hash_value(value: Any) -> str:
    """
    Generate a hash for complex values (dicts, lists).

    Args:
        value: The value to hash

    Returns:
        Hash string representation
    """
    try:
        json_str = json.dumps(value, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode(), usedforsecurity=False).hexdigest()  # noqa: B324
    except Exception:
        # Fallback to string representation
        return hashlib.md5(str(value).encode(), usedforsecurity=False).hexdigest()  # noqa: B324
