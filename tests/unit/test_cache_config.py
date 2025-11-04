"""Unit tests for cache configuration management."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.cache.config import CacheConfig, get_cache_config


class TestCacheConfig:
    """Test cache configuration management."""

    def test_config_defaults(self):
        """Test that configuration loads with defaults."""
        # Clear any existing config instance
        import app.core.cache.config as config_module

        config_module._cache_config = None

        config = CacheConfig()
        assert config.is_enabled() in (True, False)  # Can be True or False depending on env
        assert config.get_backend() in ("memory", "redis", "file")  # Can vary
        assert isinstance(config.get_default_ttl(), int)
        assert isinstance(config.get_max_size(), int)

    def test_config_from_json_file(self):
        """Test loading configuration from JSON file."""
        import app.core.cache.config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "enabled": True,
                "backend": "memory",
                "default_ttl": 600,
                "max_size": 2000,
                "endpoints": {
                    "entities": {"ttl": 1800},
                    "automations": {"ttl": 3600},
                },
            }
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            # Clear any existing config instance
            config_module._cache_config = None

            # Mock environment variable
            with patch.dict(os.environ, {"HASS_MCP_CACHE_CONFIG_FILE": str(config_path)}):
                config = CacheConfig()
                assert config.get_default_ttl() == 600
                assert config.get_max_size() == 2000
                assert config.get_endpoint_ttl("entities") == 1800
                assert config.get_endpoint_ttl("automations") == 3600
        finally:
            config_path.unlink()

    def test_config_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        import app.core.cache.config as config_module

        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "enabled": True,
                "backend": "memory",
                "default_ttl": 600,
                "max_size": 2000,
                "endpoints": {
                    "entities": {"ttl": 1800},
                },
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            # Clear any existing config instance
            config_module._cache_config = None

            with patch.dict(os.environ, {"HASS_MCP_CACHE_CONFIG_FILE": str(config_path)}):
                config = CacheConfig()
                assert config.get_default_ttl() == 600
                assert config.get_max_size() == 2000
                assert config.get_endpoint_ttl("entities") == 1800
        finally:
            config_path.unlink()

    def test_config_env_vars_override_file(self):
        """Test that environment variables override file configuration."""
        import app.core.cache.config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"default_ttl": 600, "max_size": 2000}
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            # Clear any existing config instance
            config_module._cache_config = None

            with patch.dict(
                os.environ,
                {
                    "HASS_MCP_CACHE_CONFIG_FILE": str(config_path),
                    "HASS_MCP_CACHE_DEFAULT_TTL": "900",
                },
            ):
                config = CacheConfig()
                # Environment variable should override file
                assert config.get_default_ttl() == 900
                # File value should still be used for max_size
                assert config.get_max_size() == 2000
        finally:
            config_path.unlink()

    def test_endpoint_ttl_configuration(self):
        """Test per-endpoint TTL configuration."""
        config = CacheConfig()
        # Initially no endpoint TTL
        assert config.get_endpoint_ttl("entities") is None

        # Update endpoint TTL at runtime
        config.update_endpoint_ttl("entities", 1800)
        assert config.get_endpoint_ttl("entities") == 1800

        # Update with operation
        config.update_endpoint_ttl("entities", 300, operation="list")
        assert config.get_endpoint_ttl("entities", "list") == 300
        # Domain-level TTL should still exist
        assert config.get_endpoint_ttl("entities") == 1800

    def test_endpoint_ttl_priority(self):
        """Test that operation-specific TTL takes priority over domain TTL."""
        config = CacheConfig()
        config.update_endpoint_ttl("entities", 1800)
        config.update_endpoint_ttl("entities", 300, operation="list")

        # Operation-specific should be returned
        assert config.get_endpoint_ttl("entities", "list") == 300
        # Domain-level should still be available
        assert config.get_endpoint_ttl("entities") == 1800

    def test_get_all_config(self):
        """Test getting all configuration."""
        config = CacheConfig()
        all_config = config.get_all_config()

        assert "enabled" in all_config
        assert "backend" in all_config
        assert "default_ttl" in all_config
        assert "max_size" in all_config
        assert "endpoints" in all_config

    def test_get_endpoint_config(self):
        """Test getting endpoint-specific configuration."""
        config = CacheConfig()
        config.update_endpoint_ttl("entities", 1800)

        endpoint_config = config.get_endpoint_config("entities")
        assert endpoint_config is not None
        assert "ttl" in endpoint_config
        assert endpoint_config["ttl"] == 1800

        # Non-existent endpoint
        assert config.get_endpoint_config("nonexistent") is None

    def test_reload_configuration(self):
        """Test reloading configuration."""
        config = CacheConfig()
        initial_ttl = config.get_default_ttl()

        # Update endpoint TTL
        config.update_endpoint_ttl("entities", 1800)
        assert config.get_endpoint_ttl("entities") == 1800

        # Reload should reset
        config.reload()
        assert config.get_default_ttl() == initial_ttl
        assert config.get_endpoint_ttl("entities") is None

    def test_singleton_pattern(self):
        """Test that get_cache_config returns the same instance."""
        config1 = get_cache_config()
        config2 = get_cache_config()
        assert config1 is config2

    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        import app.core.cache.config as config_module

        # Clear any existing config instance
        config_module._cache_config = None

        with patch.dict(os.environ, {"HASS_MCP_CACHE_CONFIG_FILE": "/nonexistent/file.json"}):
            # Should not raise an error, just use defaults
            config = CacheConfig()
            assert isinstance(config.get_default_ttl(), int)  # Should have a default value

    def test_invalid_json_file(self):
        """Test handling of invalid JSON file."""
        import app.core.cache.config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content{")
            config_path = Path(f.name)

        try:
            # Clear any existing config instance
            config_module._cache_config = None

            with patch.dict(os.environ, {"HASS_MCP_CACHE_CONFIG_FILE": str(config_path)}):
                # Should not raise an error, just use defaults
                config = CacheConfig()
                assert isinstance(config.get_default_ttl(), int)  # Should have a default value
        finally:
            config_path.unlink()

    def test_simple_endpoint_ttl_format(self):
        """Test simple endpoint TTL format (just integer)."""
        import app.core.cache.config as config_module

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "endpoints": {
                    "entities": 1800,  # Simple format
                    "automations": {"ttl": 3600},  # Complex format
                }
            }
            json.dump(config_data, f)
            config_path = Path(f.name)

        try:
            # Clear any existing config instance
            config_module._cache_config = None

            with patch.dict(os.environ, {"HASS_MCP_CACHE_CONFIG_FILE": str(config_path)}):
                config = CacheConfig()
                assert config.get_endpoint_ttl("entities") == 1800
                assert config.get_endpoint_ttl("automations") == 3600
        finally:
            config_path.unlink()
