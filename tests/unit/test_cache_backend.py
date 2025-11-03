"""Unit tests for cache backend interface."""

import pytest

from app.core.cache.backend import CacheBackend


class TestCacheBackend:
    """Test cache backend abstract interface."""

    def test_backend_interface_methods(self):
        """Test that CacheBackend defines all required methods."""
        # Check that all required methods exist
        assert hasattr(CacheBackend, "get")
        assert hasattr(CacheBackend, "set")
        assert hasattr(CacheBackend, "delete")
        assert hasattr(CacheBackend, "clear")
        assert hasattr(CacheBackend, "exists")
        assert hasattr(CacheBackend, "keys")

    def test_backend_is_abstract(self):
        """Test that CacheBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CacheBackend()  # type: ignore
