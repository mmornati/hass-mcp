"""Unit tests for cache key builder."""

from app.core.cache.key_builder import CacheKeyBuilder


class TestCacheKeyBuilder:
    """Test cache key builder utility."""

    def test_build_key_simple(self):
        """Test building a simple key without parameters."""
        key = CacheKeyBuilder.build_key("entities", "list")
        assert key == "entities:list:"

    def test_build_key_with_params(self):
        """Test building a key with parameters."""
        key = CacheKeyBuilder.build_key("entities", "list", {"domain": "light", "limit": 100})
        assert key.startswith("entities:list:")
        assert "domain=light" in key
        assert "limit=100" in key

    def test_build_key_with_complex_params(self):
        """Test building a key with complex parameters (dict/list)."""
        key = CacheKeyBuilder.build_key(
            "entities", "list", {"domain": "light", "fields": ["state", "attributes"]}
        )
        assert key.startswith("entities:list:")
        assert "domain=light" in key
        # Complex value should be hashed
        assert "fields=" in key

    def test_build_key_params_normalized(self):
        """Test that parameters are normalized (sorted)."""
        key1 = CacheKeyBuilder.build_key("entities", "list", {"domain": "light", "limit": 100})
        key2 = CacheKeyBuilder.build_key("entities", "list", {"limit": 100, "domain": "light"})
        # Should produce same key regardless of parameter order
        assert key1 == key2

    def test_build_key_none_params_filtered(self):
        """Test that None values are filtered out."""
        key = CacheKeyBuilder.build_key("entities", "list", {"domain": "light", "limit": None})
        assert "limit" not in key
        assert "domain=light" in key

    def test_build_key_automation_config(self):
        """Test building key for automation config."""
        key = CacheKeyBuilder.build_key("automations", "config", {"id": "automation_123"})
        assert key == "automations:config:id=automation_123"

    def test_build_key_areas_list(self):
        """Test building key for areas list."""
        key = CacheKeyBuilder.build_key("areas", "list")
        assert key == "areas:list:"

    def test_normalize_params(self):
        """Test parameter normalization."""
        params = {"domain": "light", "limit": 100, "none_value": None}
        normalized = CacheKeyBuilder.normalize_params(params)
        assert "none_value" not in normalized
        assert normalized["domain"] == "light"
        assert normalized["limit"] == 100

    def test_normalize_params_complex_types(self):
        """Test normalization of complex types."""
        params = {"fields": ["state", "attributes"], "options": {"lean": True}}
        normalized = CacheKeyBuilder.normalize_params(params)
        # Complex types should be hashed
        assert isinstance(normalized["fields"], str)
        assert isinstance(normalized["options"], str)
        assert len(normalized["fields"]) == 32  # MD5 hash length
        assert len(normalized["options"]) == 32  # MD5 hash length

    def test_hash_value_consistency(self):
        """Test that hashing produces consistent results."""
        value = {"field1": "value1", "field2": "value2"}
        hash1 = CacheKeyBuilder._hash_value(value)
        hash2 = CacheKeyBuilder._hash_value(value)
        assert hash1 == hash2

    def test_hash_value_different_values(self):
        """Test that different values produce different hashes."""
        value1 = {"field1": "value1"}
        value2 = {"field1": "value2"}
        hash1 = CacheKeyBuilder._hash_value(value1)
        hash2 = CacheKeyBuilder._hash_value(value2)
        assert hash1 != hash2

    def test_hash_value_list(self):
        """Test hashing list values."""
        value = ["state", "attributes"]
        hash1 = CacheKeyBuilder._hash_value(value)
        hash2 = CacheKeyBuilder._hash_value(value)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length
