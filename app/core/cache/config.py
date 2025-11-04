"""Cache configuration management for hass-mcp.

This module provides configuration management for the cache system, including
support for environment variables, configuration files, and per-endpoint TTL settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None

from app.config import (
    CACHE_BACKEND,
    CACHE_DEFAULT_TTL,
    CACHE_DIR,
    CACHE_ENABLED,
    CACHE_MAX_SIZE,
    REDIS_URL,
)

logger = logging.getLogger(__name__)


class CacheConfig:
    """
    Cache configuration manager.

    This class manages cache configuration from multiple sources:
    1. Environment variables (highest priority)
    2. Configuration file (JSON or YAML)
    3. Default values (lowest priority)

    It also supports per-endpoint TTL configuration and runtime updates.
    """

    def __init__(self):
        """Initialize cache configuration."""
        self._config_file: Path | None = None
        self._config_data: dict[str, Any] = {}
        self._endpoint_ttls: dict[str, int] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from environment variables and config file."""
        # Start with defaults
        self._config_data = {
            "enabled": CACHE_ENABLED,
            "backend": CACHE_BACKEND,
            "default_ttl": CACHE_DEFAULT_TTL,
            "max_size": CACHE_MAX_SIZE,
            "redis_url": REDIS_URL,
            "cache_dir": CACHE_DIR,
            "endpoints": {},
        }

        # Load from config file if it exists
        config_file_path = os.environ.get("HASS_MCP_CACHE_CONFIG_FILE")
        if config_file_path:
            self._config_file = Path(config_file_path)
            if self._config_file.exists():
                self._load_from_file(self._config_file)
            else:
                logger.warning(f"Cache config file not found: {config_file_path}")
        else:
            # Try default locations
            default_paths = [
                Path.home() / ".hass-mcp" / "cache_config.json",
                Path.home() / ".hass-mcp" / "cache_config.yaml",
                Path(".cache_config.json"),
                Path(".cache_config.yaml"),
            ]
            for path in default_paths:
                if path.exists():
                    self._config_file = path
                    self._load_from_file(path)
                    break

        # Override with environment variables (highest priority)
        self._apply_env_overrides()

        # Build endpoint TTL mapping
        self._build_endpoint_ttls()

    def _load_from_file(self, config_path: Path) -> None:
        """Load configuration from a JSON or YAML file."""
        try:
            if config_path.suffix.lower() == ".yaml" or config_path.suffix.lower() == ".yml":
                if yaml is None:
                    logger.warning(
                        "YAML file detected but PyYAML not installed. "
                        "Install with: pip install pyyaml"
                    )
                    return
                with config_path.open() as f:
                    file_data = yaml.safe_load(f)
            else:
                with config_path.open() as f:
                    file_data = json.load(f)

            if file_data:
                # Merge file configuration
                if "enabled" in file_data:
                    self._config_data["enabled"] = file_data["enabled"]
                if "backend" in file_data:
                    self._config_data["backend"] = file_data["backend"]
                if "default_ttl" in file_data:
                    self._config_data["default_ttl"] = int(file_data["default_ttl"])
                if "max_size" in file_data:
                    self._config_data["max_size"] = int(file_data["max_size"])
                if "redis_url" in file_data:
                    self._config_data["redis_url"] = file_data["redis_url"]
                if "cache_dir" in file_data:
                    self._config_data["cache_dir"] = file_data["cache_dir"]
                if "endpoints" in file_data:
                    self._config_data["endpoints"] = file_data["endpoints"]

                logger.info(f"Loaded cache configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load cache config file {config_path}: {e}")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Environment variables take highest priority
        if os.environ.get("HASS_MCP_CACHE_ENABLED"):
            self._config_data["enabled"] = os.environ.get(
                "HASS_MCP_CACHE_ENABLED", "true"
            ).lower() in ("true", "1", "yes")

        if os.environ.get("HASS_MCP_CACHE_BACKEND"):
            self._config_data["backend"] = os.environ.get(
                "HASS_MCP_CACHE_BACKEND", "memory"
            ).lower()

        if os.environ.get("HASS_MCP_CACHE_DEFAULT_TTL"):
            try:
                self._config_data["default_ttl"] = int(
                    os.environ.get("HASS_MCP_CACHE_DEFAULT_TTL", "300")
                )
            except ValueError:
                logger.warning("Invalid HASS_MCP_CACHE_DEFAULT_TTL value, using default")

        if os.environ.get("HASS_MCP_CACHE_MAX_SIZE"):
            try:
                self._config_data["max_size"] = int(
                    os.environ.get("HASS_MCP_CACHE_MAX_SIZE", "1000")
                )
            except ValueError:
                logger.warning("Invalid HASS_MCP_CACHE_MAX_SIZE value, using default")

        if os.environ.get("HASS_MCP_CACHE_REDIS_URL"):
            self._config_data["redis_url"] = os.environ.get("HASS_MCP_CACHE_REDIS_URL")

        if os.environ.get("HASS_MCP_CACHE_DIR"):
            self._config_data["cache_dir"] = os.environ.get("HASS_MCP_CACHE_DIR", ".cache")

    def _build_endpoint_ttls(self) -> None:
        """Build endpoint TTL mapping from configuration."""
        endpoints = self._config_data.get("endpoints", {})
        for endpoint, config in endpoints.items():
            if isinstance(config, dict) and "ttl" in config:
                self._endpoint_ttls[endpoint] = int(config["ttl"])
            elif isinstance(config, int):
                # Simple format: endpoint: ttl
                self._endpoint_ttls[endpoint] = int(config)

    def get_endpoint_ttl(self, domain: str, operation: str | None = None) -> int | None:
        """
        Get TTL for a specific endpoint.

        Args:
            domain: The API domain (e.g., 'entities', 'automations')
            operation: Optional operation name (e.g., 'list', 'get_state')

        Returns:
            TTL in seconds if configured, None otherwise
        """
        # Try domain.operation first
        if operation:
            key = f"{domain}.{operation}"
            if key in self._endpoint_ttls:
                return self._endpoint_ttls[key]

        # Try domain
        if domain in self._endpoint_ttls:
            return self._endpoint_ttls[domain]

        return None

    def get_default_ttl(self) -> int:
        """Get the default TTL."""
        return int(self._config_data.get("default_ttl", CACHE_DEFAULT_TTL))

    def get_backend(self) -> str:
        """Get the configured cache backend."""
        return str(self._config_data.get("backend", CACHE_BACKEND))

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return bool(self._config_data.get("enabled", CACHE_ENABLED))

    def get_max_size(self) -> int:
        """Get the maximum cache size."""
        return int(self._config_data.get("max_size", CACHE_MAX_SIZE))

    def get_redis_url(self) -> str | None:
        """Get Redis URL if configured."""
        redis_url = self._config_data.get("redis_url")
        return str(redis_url) if redis_url else None

    def get_cache_dir(self) -> str:
        """Get the cache directory path."""
        return str(self._config_data.get("cache_dir", CACHE_DIR))

    def update_endpoint_ttl(self, domain: str, ttl: int, operation: str | None = None) -> None:
        """
        Update TTL for an endpoint at runtime.

        Args:
            domain: The API domain
            ttl: TTL in seconds
            operation: Optional operation name
        """
        key = f"{domain}.{operation}" if operation else domain

        self._endpoint_ttls[key] = ttl
        logger.info(f"Updated TTL for {key}: {ttl}s")

        # Update config data
        if "endpoints" not in self._config_data:
            self._config_data["endpoints"] = {}
        if domain not in self._config_data["endpoints"]:
            self._config_data["endpoints"][domain] = {}
        if operation:
            if not isinstance(self._config_data["endpoints"][domain], dict):
                self._config_data["endpoints"][domain] = {}
            self._config_data["endpoints"][domain][operation] = {"ttl": ttl}
        else:
            self._config_data["endpoints"][domain] = {"ttl": ttl}

    def get_all_config(self) -> dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config_data.copy()

    def get_endpoint_config(self, domain: str) -> dict[str, Any] | None:
        """Get configuration for a specific endpoint domain."""
        endpoints = self._config_data.get("endpoints", {})
        config = endpoints.get(domain)
        return config if isinstance(config, dict) else None

    def reload(self) -> None:
        """Reload configuration from file and environment."""
        self._config_data = {
            "enabled": CACHE_ENABLED,
            "backend": CACHE_BACKEND,
            "default_ttl": CACHE_DEFAULT_TTL,
            "max_size": CACHE_MAX_SIZE,
            "redis_url": REDIS_URL,
            "cache_dir": CACHE_DIR,
            "endpoints": {},
        }
        self._endpoint_ttls = {}
        self._load_configuration()


# Global cache config instance
_cache_config: CacheConfig | None = None


def get_cache_config() -> CacheConfig:
    """
    Get the global cache configuration instance (singleton pattern).

    Returns:
        The CacheConfig instance
    """
    global _cache_config
    if _cache_config is None:
        _cache_config = CacheConfig()
        logger.info("Cache configuration loaded")
    return _cache_config
