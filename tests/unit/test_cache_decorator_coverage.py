"""Additional tests for cache decorators to improve coverage."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.cache.decorator import cached, invalidate_cache


class TestCacheDecoratorCoverage:
    """Additional tests to improve coverage for edge cases."""

    @pytest.mark.asyncio
    async def test_cached_condition_check_error(self, caplog):
        """Test that condition check errors are handled gracefully."""
        import logging

        call_count = 0

        def failing_condition(args, kwargs, result):
            """Condition that raises an error."""
            raise ValueError("Condition check failed")

        @cached(ttl=60, condition=failing_condition)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        with caplog.at_level(logging.WARNING):
            # Should still work even if condition check fails
            result = await test_function("test")
            assert result == "result_test"
            assert call_count == 1

        # Verify warning was logged
        assert "Condition check error" in caplog.text

    @pytest.mark.asyncio
    async def test_cached_function_failure(self):
        """Test that function failures are handled correctly."""

        @cached(ttl=60)
        async def failing_function(value: str) -> str:
            raise ValueError("Function failed")

        # Should raise the exception
        with pytest.raises(ValueError, match="Function failed"):
            await failing_function("test")

    @pytest.mark.asyncio
    async def test_cached_cache_set_error(self, caplog):
        """Test that cache set errors don't break the function."""
        import logging

        call_count = 0

        @cached(ttl=60)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock cache.set to raise an error
        with patch("app.core.cache.decorator.get_cache_manager") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_cache.set.side_effect = Exception("Cache set error")
            mock_get_cache.return_value = mock_cache

            with caplog.at_level(logging.WARNING):
                # Should still work even if cache set fails
                result = await test_function("test")
                assert result == "result_test"
                assert call_count == 1

            # Verify warning was logged
            assert "Cache set error" in caplog.text

    @pytest.mark.asyncio
    async def test_invalidate_cache_condition_error(self, caplog):
        """Test that condition check errors in invalidate_cache are handled."""
        import logging

        def failing_condition(args, kwargs, result):
            """Condition that raises an error."""
            raise ValueError("Condition check failed")

        @invalidate_cache(pattern="test:*", condition=failing_condition)
        async def mutation_function(value: str) -> str:
            return f"mutated_{value}"

        with caplog.at_level(logging.WARNING):
            # Should still work even if condition check fails
            result = await mutation_function("test")
            assert result == "mutated_test"

        # Verify warning was logged
        assert "Condition check error" in caplog.text

    @pytest.mark.asyncio
    async def test_hash_value_exception_fallback(self):
        """Test _hash_value fallback when JSON encoding fails."""
        from app.core.cache.decorator import _hash_value

        # Create an object that can't be JSON encoded
        class Unserializable:
            def __str__(self):
                return "unserializable"

        obj = Unserializable()
        # This should use the fallback string representation
        hash_result = _hash_value(obj)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_build_key_with_key_prefix_starting_with_prefix(self):
        """Test cache key building when key_prefix matches start of generated key."""
        from app.core.cache.decorator import _build_cache_key

        async def test_function(value: str) -> str:
            return f"result_{value}"

        # Build key with prefix that matches start of generated key
        key = _build_cache_key(test_function, ("test",), {}, key_prefix="test_cache")
        assert key.startswith("test_cache:")

    @pytest.mark.asyncio
    async def test_build_key_with_empty_params_after_filtering(self):
        """Test cache key building when all params are filtered out."""
        from app.core.cache.decorator import _build_cache_key

        async def test_function(value: str = "default") -> str:
            return f"result_{value}"

        # Filter out all params (using exclude_params)
        key = _build_cache_key(test_function, (), {"value": "test"}, exclude_params=["value"])
        # Should still generate a valid key
        assert ":" in key
        # Should end with empty params section
        assert key.endswith(":")
