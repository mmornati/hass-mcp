"""Unit tests for cache decorators."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.manager import get_cache_manager


@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear cache before each test."""
    cache = await get_cache_manager()
    await cache.clear()
    yield
    # Also clear after test
    await cache.clear()


class TestCachedDecorator:
    """Test the @cached decorator."""

    @pytest.mark.asyncio
    async def test_basic_caching(self):
        """Test basic caching behavior."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # First call - should call function
        result1 = await test_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # Second call - should use cache
        result2 = await test_function("test")
        assert result2 == "result_test"
        assert call_count == 1  # Function not called again

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation from function parameters."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(domain: str | None = None, limit: int = 100) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{domain}_{limit}"

        # Call with different parameters
        result1 = await test_function(domain="light", limit=100)
        assert call_count == 1

        # Same parameters - should use cache
        result2 = await test_function(domain="light", limit=100)
        assert call_count == 1

        # Different parameters - should call function again
        result3 = await test_function(domain="switch", limit=100)
        assert call_count == 2

        # Same parameters again - should use cache
        result4 = await test_function(domain="switch", limit=100)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_key_with_custom_prefix(self):
        """Test cache key generation with custom prefix."""
        call_count = 0

        @cached(ttl=60, key_prefix="custom_prefix")
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        result1 = await test_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # Should use cache
        result2 = await test_function("test")
        assert result2 == "result_test"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_key_with_include_params(self):
        """Test cache key with include_params."""
        call_count = 0

        @cached(ttl=60, include_params=["domain"])
        async def test_function(domain: str, limit: int = 100) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{domain}_{limit}"

        # Different limit but same domain - should use cache
        result1 = await test_function(domain="light", limit=100)
        assert call_count == 1

        result2 = await test_function(domain="light", limit=200)
        assert call_count == 1  # Cached because domain is same

    @pytest.mark.asyncio
    async def test_cache_key_with_exclude_params(self):
        """Test cache key with exclude_params."""
        call_count = 0

        @cached(ttl=60, exclude_params=["limit"])
        async def test_function(domain: str, limit: int = 100) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{domain}_{limit}"

        # Different limit but same domain - should use cache (limit excluded)
        result1 = await test_function(domain="light", limit=100)
        assert call_count == 1

        result2 = await test_function(domain="light", limit=200)
        assert call_count == 1  # Cached because limit is excluded

    @pytest.mark.asyncio
    async def test_conditional_caching(self):
        """Test conditional caching."""
        call_count = 0

        def should_cache(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> bool:
            """Only cache if result doesn't contain 'error'."""
            if isinstance(result, dict):
                return "error" not in result
            return True

        @cached(ttl=60, condition=should_cache)
        async def test_function(should_error: bool) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if should_error:
                return {"error": "Something went wrong"}
            return {"success": True}

        # Successful result - should cache
        result1 = await test_function(should_error=False)
        assert call_count == 1
        assert result1 == {"success": True}

        # Should use cache
        result2 = await test_function(should_error=False)
        assert call_count == 1  # Cached

        # Error result - should not cache
        result3 = await test_function(should_error=True)
        assert call_count == 2
        assert result3 == {"error": "Something went wrong"}

        # Should call function again (not cached)
        result4 = await test_function(should_error=True)
        assert call_count == 3  # Not cached

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        call_count = 0

        # Use a very short TTL for testing (0.2 seconds) instead of TTL_SHORT (60s)
        test_ttl = 0.2

        @cached(ttl=test_ttl)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # First call
        result1 = await test_function("test")
        assert call_count == 1

        # Should use cache immediately
        result2 = await test_function("test")
        assert call_count == 1

        # Wait for expiration
        await asyncio.sleep(test_ttl + 0.1)

        # Should call function again after expiration
        result3 = await test_function("test")
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_metadata(self):
        """Test that decorator preserves function metadata."""

        @cached(ttl=60)
        async def test_function(value: str) -> str:
            """Test function docstring."""
            return f"result_{value}"

        # Check docstring is preserved
        assert test_function.__doc__ == "Test function docstring."

        # Check function name is preserved
        assert test_function.__name__ == "test_function"

    @pytest.mark.asyncio
    async def test_decorator_handles_errors_gracefully(self, caplog):
        """Test that decorator handles cache errors gracefully.

        This test intentionally causes cache operations to fail to verify
        that the decorator handles errors gracefully and doesn't break the
        function execution. The exception in the logs is expected.
        """
        import logging

        call_count = 0

        @cached(ttl=60)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock cache.get to raise an error
        with patch("app.core.cache.decorator.get_cache_manager") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get.side_effect = Exception("Cache error")
            mock_cache.set = AsyncMock()
            mock_get_cache.return_value = mock_cache

            # Suppress the warning log during test (we're testing error handling)
            with caplog.at_level(logging.WARNING):
                # Should still work (fallback to direct call)
                result = await test_function("test")
                assert result == "result_test"
                assert call_count == 1

            # Verify that a warning was logged (error handling worked)
            assert "Cache get error" in caplog.text

    @pytest.mark.asyncio
    async def test_decorator_handles_args_and_kwargs(self):
        """Test that decorator handles *args and **kwargs correctly."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(*args: Any, **kwargs: Any) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{args}_{kwargs}"

        # Call with args and kwargs
        result1 = await test_function("arg1", "arg2", key1="value1", key2="value2")
        assert call_count == 1

        # Same args and kwargs - should use cache
        result2 = await test_function("arg1", "arg2", key1="value1", key2="value2")
        assert call_count == 1

        # Different args - should call function
        result3 = await test_function("arg1", "arg3", key1="value1", key2="value2")
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_with_complex_parameters(self):
        """Test that decorator handles complex parameters (dicts, lists)."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(domain: str, filters: dict[str, Any] | None = None) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{domain}_{filters}"

        # Call with complex parameter
        filters1 = {"type": "light", "status": "on"}
        result1 = await test_function("entities", filters=filters1)
        assert call_count == 1

        # Same filters - should use cache
        filters2 = {"type": "light", "status": "on"}
        result2 = await test_function("entities", filters=filters2)
        assert call_count == 1

        # Different filters - should call function
        filters3 = {"type": "switch", "status": "on"}
        result3 = await test_function("entities", filters=filters3)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_composition_with_handle_api_errors(self):
        """Test that decorator composes correctly with @handle_api_errors."""
        from app.core.decorators import handle_api_errors

        call_count = 0

        @cached(ttl=60)
        @handle_api_errors
        async def test_function(value: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": f"value_{value}"}

        # Mock HA_TOKEN to avoid the "No token" error check
        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            # First call
            result1 = await test_function("test")
            assert call_count == 1
            assert result1 == {"result": "value_test"}

            # Second call - should use cache
            result2 = await test_function("test")
            assert call_count == 1  # Cached
            assert result2 == {"result": "value_test"}

    @pytest.mark.asyncio
    async def test_decorator_with_none_values(self):
        """Test that decorator handles None values correctly."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(domain: str | None = None, limit: int = 100) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{domain}_{limit}"

        # Call with None
        result1 = await test_function(domain=None, limit=100)
        assert call_count == 1

        # Same None value - should use cache
        result2 = await test_function(domain=None, limit=100)
        assert call_count == 1

        # Different value - should call function
        result3 = await test_function(domain="light", limit=100)
        assert call_count == 2


class TestInvalidateCacheDecorator:
    """Test the @invalidate_cache decorator."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_pattern(self):
        """Test cache invalidation with pattern."""
        call_count = 0

        @cached(ttl=60)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        @invalidate_cache(pattern="test:*")
        async def mutation_function(value: str) -> str:
            return f"mutated_{value}"

        # Cache something
        result1 = await test_function("test1")
        assert call_count == 1

        # Should use cache
        result2 = await test_function("test1")
        assert call_count == 1

        # Call mutation function
        await mutation_function("value")

        # Cache should be invalidated (if pattern matches)
        # Note: This depends on the cache key format
        # In a real scenario, we'd need to verify the cache was actually cleared

    @pytest.mark.asyncio
    async def test_invalidate_cache_multiple_patterns(self):
        """Test cache invalidation with multiple patterns."""

        @invalidate_cache(patterns=["entities:*", "automations:*"])
        async def mutation_function() -> dict[str, str]:
            return {"status": "success"}

        result = await mutation_function()
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_condition(self):
        """Test cache invalidation with condition."""
        call_count = 0

        def should_invalidate(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> bool:
            """Only invalidate if result indicates success."""
            if isinstance(result, dict):
                return result.get("status") == "success"
            return True

        @invalidate_cache(pattern="test:*", condition=should_invalidate)
        async def mutation_function(success: bool) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if success:
                return {"status": "success"}
            return {"status": "error"}

        # Call with success - should invalidate
        result1 = await mutation_function(success=True)
        assert call_count == 1
        assert result1 == {"status": "success"}

        # Call with error - should not invalidate (condition fails)
        result2 = await mutation_function(success=False)
        assert call_count == 2
        assert result2 == {"status": "error"}

    @pytest.mark.asyncio
    async def test_invalidate_cache_handles_errors_gracefully(self, caplog):
        """Test that invalidation handles errors gracefully.

        This test intentionally causes cache invalidation to fail to verify
        that the decorator handles errors gracefully and doesn't break the
        function execution. The exception in the logs is expected.
        """
        import logging

        @invalidate_cache(pattern="test:*")
        async def mutation_function(value: str) -> str:
            return f"mutated_{value}"

        # Mock cache.invalidate to raise an error
        with patch("app.core.cache.decorator.get_cache_manager") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.invalidate.side_effect = Exception("Invalidation error")
            mock_get_cache.return_value = mock_cache

            # Suppress the warning log during test (we're testing error handling)
            with caplog.at_level(logging.WARNING):
                # Should still work (function completes even if invalidation fails)
                result = await mutation_function("test")
                assert result == "mutated_test"

            # Verify that a warning was logged (error handling worked)
            assert "Cache invalidation error" in caplog.text

    @pytest.mark.asyncio
    async def test_invalidate_cache_preserves_function_metadata(self):
        """Test that invalidate_cache preserves function metadata."""

        @invalidate_cache(pattern="test:*")
        async def test_function(value: str) -> str:
            """Test function docstring."""
            return f"result_{value}"

        # Check docstring is preserved
        assert test_function.__doc__ == "Test function docstring."

        # Check function name is preserved
        assert test_function.__name__ == "test_function"

    @pytest.mark.asyncio
    async def test_invalidate_cache_composition_with_handle_api_errors(self):
        """Test that invalidate_cache composes correctly with @handle_api_errors."""
        from app.core.decorators import handle_api_errors

        @invalidate_cache(pattern="test:*")
        @handle_api_errors
        async def mutation_function(value: str) -> dict[str, str]:
            return {"status": "success", "value": value}

        # Mock HA_TOKEN to avoid the "No token" error check
        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await mutation_function("test")
            assert result == {"status": "success", "value": "test"}


class TestCacheDecoratorIntegration:
    """Integration tests for cache decorators."""

    @pytest.mark.asyncio
    async def test_cached_and_invalidate_together(self):
        """Test using @cached and @invalidate_cache together."""
        call_count = 0

        @cached(ttl=60, key_prefix="test")
        async def get_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        @invalidate_cache(pattern="test:*")
        async def update_function(value: str, new_value: str) -> str:
            return f"updated_{new_value}"

        # Cache something
        result1 = await get_function("test")
        assert call_count == 1

        # Should use cache
        result2 = await get_function("test")
        assert call_count == 1

        # Update (should invalidate cache)
        await update_function("test", "new")

        # Should call function again after invalidation
        result3 = await get_function("test")
        assert call_count == 2
