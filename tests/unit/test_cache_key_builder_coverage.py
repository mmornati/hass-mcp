"""Additional tests for cache key builder to improve coverage."""

from app.core.cache.key_builder import CacheKeyBuilder


class TestCacheKeyBuilderCoverage:
    """Additional tests to improve coverage."""

    def test_build_key_empty_params(self):
        """Test building key with empty params dict."""
        key = CacheKeyBuilder.build_key("entities", "list", {})
        assert key == "entities:list:"

    def test_build_key_none_params(self):
        """Test building key with None params."""
        key = CacheKeyBuilder.build_key("entities", "list", None)
        assert key == "entities:list:"

    def test_normalize_params_empty(self):
        """Test normalize_params with empty dict."""
        normalized = CacheKeyBuilder.normalize_params({})
        assert normalized == {}

    def test_normalize_params_none(self):
        """Test normalize_params with None."""
        normalized = CacheKeyBuilder.normalize_params(None)
        assert normalized == {}
