"""Cache key builder for hass-mcp.

This module provides utilities for building hierarchical cache keys.
"""

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CacheKeyBuilder:
    """
    Utility class for building hierarchical cache keys.

    Builds cache keys in the format: {domain}:{operation}:{params_hash}
    """

    @staticmethod
    def build_key(
        domain: str,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """
        Build a hierarchical cache key.

        Args:
            domain: The domain (e.g., 'entities', 'automations', 'areas')
            operation: The operation (e.g., 'list', 'config', 'state')
            params: Optional parameters to include in the key

        Returns:
            A hierarchical cache key string

        Examples:
            >>> CacheKeyBuilder.build_key("entities", "list", {"domain": "light", "limit": 100})
            'entities:list:domain=light:limit=100'
            >>> CacheKeyBuilder.build_key("automations", "config", {"id": "automation_123"})
            'automations:config:id=automation_123'
            >>> CacheKeyBuilder.build_key("areas", "list")
            'areas:list:'
        """
        # Start with domain and operation
        key_parts = [domain, operation]

        # Add parameters if provided
        if params:
            # Normalize parameters: sort keys and filter out None values
            normalized_params = {k: v for k, v in sorted(params.items()) if v is not None}

            if normalized_params:
                # Build parameter string
                param_parts = []
                for key, value in normalized_params.items():
                    # Handle complex types by hashing them
                    if isinstance(value, (dict, list)):
                        value_str = CacheKeyBuilder._hash_value(value)
                    else:
                        value_str = str(value)
                    param_parts.append(f"{key}={value_str}")

                key_parts.append(":".join(param_parts))
            else:
                key_parts.append("")
        else:
            key_parts.append("")

        return ":".join(key_parts)

    @staticmethod
    def _hash_value(value: Any) -> str:
        """
        Generate a hash for complex values (dicts, lists).

        Args:
            value: The value to hash

        Returns:
            A hash string representation
        """
        # Convert to JSON string for consistent hashing
        json_str = json.dumps(value, sort_keys=True)
        # Generate MD5 hash
        return hashlib.md5(json_str.encode()).hexdigest()

    @staticmethod
    def normalize_params(params: dict[str, Any] | None) -> dict[str, Any]:
        """
        Normalize parameters for consistent key generation.

        Args:
            params: The parameters to normalize

        Returns:
            Normalized parameters dictionary
        """
        if not params:
            return {}

        # Sort keys and filter out None values
        normalized = {k: v for k, v in sorted(params.items()) if v is not None}

        # Convert complex types to hash strings
        result = {}
        for key, value in normalized.items():
            if isinstance(value, (dict, list)):
                result[key] = CacheKeyBuilder._hash_value(value)
            else:
                result[key] = value

        return result
