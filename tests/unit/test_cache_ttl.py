"""Unit tests for TTL presets."""

from app.core.cache.ttl import (
    TTL_DISABLED,
    TTL_LONG,
    TTL_MEDIUM,
    TTL_SHORT,
    TTL_VERY_LONG,
)


class TestTTLPresets:
    """Test TTL preset constants."""

    def test_ttl_values(self):
        """Test that TTL values are correct."""
        assert TTL_SHORT == 60  # 1 minute
        assert TTL_MEDIUM == 300  # 5 minutes
        assert TTL_LONG == 1800  # 30 minutes
        assert TTL_VERY_LONG == 3600  # 1 hour
        assert TTL_DISABLED == 0  # No caching

    def test_ttl_ordering(self):
        """Test that TTL values are ordered correctly."""
        assert TTL_DISABLED < TTL_SHORT < TTL_MEDIUM < TTL_LONG < TTL_VERY_LONG

    def test_ttl_all_positive(self):
        """Test that all TTL values are non-negative."""
        assert TTL_SHORT >= 0
        assert TTL_MEDIUM >= 0
        assert TTL_LONG >= 0
        assert TTL_VERY_LONG >= 0
        assert TTL_DISABLED >= 0
