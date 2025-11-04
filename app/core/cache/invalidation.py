"""Advanced cache invalidation strategies for hass-mcp.

This module provides sophisticated cache invalidation strategies including:
- Hierarchical invalidation (parent invalidates children)
- Dependency-based invalidation
- Invalidation chains
- Template-based pattern generation
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class InvalidationStrategy:
    """Advanced invalidation strategies for cache management."""

    # Define hierarchical cache key structure
    # Parent patterns invalidate all child patterns
    HIERARCHY = {
        "entities": {
            "entities:*": ["entities:state:*", "entities:list:*", "entities:get:*"],
            "entities:state:*": ["entities:state:id=*"],
            "entities:list:*": ["entities:list:domain=*", "entities:list:search=*"],
        },
        "automations": {
            "automations:*": ["automations:list:*", "automations:config:*"],
            "automations:config:*": ["automations:config:id=*"],
        },
        "areas": {
            "areas:*": ["areas:list:*", "areas:entities:*"],
            "areas:entities:*": ["areas:entities:id=*"],
        },
        "scenes": {
            "scenes:*": ["scenes:list:*", "scenes:config:*"],
        },
        "scripts": {
            "scripts:*": ["scripts:list:*", "scripts:config:*"],
        },
        "devices": {
            "devices:*": ["devices:list:*", "devices:details:*", "devices:statistics:*"],
        },
    }

    # Define invalidation chains for common operations
    INVALIDATION_CHAINS = {
        "entity_update": [
            "entities:state:id={entity_id}*",
            "entities:list:*",  # May include this entity
            "domains:summary:domain={domain}*",
            "areas:entities:*",  # If entity is in an area
        ],
        "entity_action": [
            "entities:state:id={entity_id}*",
            "entities:list:*",
        ],
        "automation_update": [
            "automations:config:id={automation_id}*",
            "automations:list:*",
        ],
        "automation_create": [
            "automations:list:*",
        ],
        "automation_delete": [
            "automations:config:id={automation_id}*",
            "automations:list:*",
        ],
        "area_update": [
            "areas:list:*",
            "areas:entities:id={area_id}*",
        ],
        "scene_create": [
            "scenes:list:*",
        ],
        "scene_update": [
            "scenes:config:id={scene_id}*",
            "scenes:list:*",
        ],
        "device_update": [
            "devices:list:*",
            "devices:details:id={device_id}*",
            "devices:statistics:*",
        ],
    }

    @classmethod
    def expand_pattern(cls, pattern: str, visited: set[str] | None = None) -> list[str]:
        """
        Expand a pattern to include hierarchical children.

        Args:
            pattern: Base pattern to expand
            visited: Set of already visited patterns to prevent infinite recursion

        Returns:
            List of patterns including parent and all children
        """
        if visited is None:
            visited = set()

        # Prevent infinite recursion
        if pattern in visited:
            return [pattern]

        visited.add(pattern)
        patterns = [pattern]

        # Don't expand specific patterns (patterns with IDs) - only expand parent patterns
        # Specific patterns like "entities:state:id=light.living_room*" should not expand
        # Only general patterns like "entities:*" or "entities:state:*" should expand
        is_specific_pattern = (
            "id=" in pattern or ":" in pattern.split("*")[0] if "*" in pattern else False
        )

        # Check all hierarchies for this pattern
        for _domain, hierarchy in cls.HIERARCHY.items():
            # Only expand if pattern is a parent pattern in the hierarchy
            if pattern in hierarchy:
                # Add all children
                children = hierarchy[pattern]
                patterns.extend(children)
                # Recursively expand children (but not if already visited)
                for child in children:
                    if child not in visited:
                        expanded = cls.expand_pattern(child, visited)
                        patterns.extend(expanded)
            elif not is_specific_pattern:
                # Only check for parent pattern matches if this is not a specific pattern
                # Check if pattern matches a parent pattern
                for parent, children in hierarchy.items():
                    if cls._pattern_matches(pattern, parent):
                        patterns.extend(children)
                        # Recursively expand children (but not if already visited)
                        for child in children:
                            if child not in visited:
                                expanded = cls.expand_pattern(child, visited)
                                patterns.extend(expanded)

        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for p in patterns:
            if p not in seen:
                seen.add(p)
                unique_patterns.append(p)

        return unique_patterns

    @classmethod
    def _pattern_matches(cls, pattern: str, parent_pattern: str) -> bool:
        """
        Check if a pattern matches a parent pattern.

        Args:
            pattern: Pattern to check
            parent_pattern: Parent pattern to match against

        Returns:
            True if pattern matches parent pattern
        """
        # Convert wildcard pattern to regex
        regex_pattern = parent_pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", pattern))

    @classmethod
    def get_invalidation_chain(cls, chain_name: str, **kwargs) -> list[str]:
        """
        Get invalidation chain patterns with template substitution.

        Args:
            chain_name: Name of the invalidation chain
            **kwargs: Template variables for pattern substitution

        Returns:
            List of patterns to invalidate

        Raises:
            ValueError: If chain_name is not found
        """
        if chain_name not in cls.INVALIDATION_CHAINS:
            raise ValueError(f"Invalidation chain '{chain_name}' not found")

        chain = cls.INVALIDATION_CHAINS[chain_name]
        patterns = []

        for pattern_template in chain:
            # Substitute template variables
            try:
                pattern = pattern_template.format(**kwargs)
                patterns.append(pattern)
            except KeyError as e:
                logger.warning(
                    f"Missing template variable {e} for pattern '{pattern_template}' in chain '{chain_name}'"
                )
                # Include original pattern if substitution fails
                patterns.append(pattern_template)

        return patterns

    @classmethod
    def resolve_pattern_template(cls, pattern: str, **kwargs) -> str:
        """
        Resolve a pattern template with variables.

        Args:
            pattern: Pattern template with {variable} placeholders
            **kwargs: Variables for substitution

        Returns:
            Resolved pattern string

        Examples:
            >>> resolve_pattern_template("entities:state:id={entity_id}*", entity_id="light.living_room")
            "entities:state:id=light.living_room*"
        """
        try:
            return pattern.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template variable {e} for pattern '{pattern}'")
            return pattern

    @classmethod
    def extract_entity_id_from_key(cls, cache_key: str) -> str | None:
        """
        Extract entity_id from a cache key if present.

        Args:
            cache_key: Cache key to parse

        Returns:
            Entity ID if found, None otherwise

        Examples:
            >>> extract_entity_id_from_key("entities:state:id=light.living_room")
            "light.living_room"
        """
        # Try to extract entity_id from common patterns
        patterns = [
            r"entities:state:id=([^:]+)",
            r"entities:get:id=([^:]+)",
            r"entity_id=([^:]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, cache_key)
            if match:
                return match.group(1)

        return None

    @classmethod
    def extract_domain_from_key(cls, cache_key: str) -> str | None:
        """
        Extract domain from a cache key if present.

        Args:
            cache_key: Cache key to parse

        Returns:
            Domain if found, None otherwise

        Examples:
            >>> extract_domain_from_key("entities:list:domain=light")
            "light"
        """
        # Try to extract domain from common patterns
        patterns = [
            r"domain=([^:]+)",
            r"entities:list:domain=([^:]+)",
            r"domains:summary:domain=([^:]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, cache_key)
            if match:
                return match.group(1)

        # Try to extract from entity_id
        entity_id = cls.extract_entity_id_from_key(cache_key)
        if entity_id:
            parts = entity_id.split(".")
            if len(parts) > 0:
                return parts[0]

        return None

    @classmethod
    def build_dependency_patterns(cls, cache_key: str) -> list[str]:
        """
        Build dependency patterns for a cache key.

        When a cache entry is created, this method determines what other
        cache entries might depend on it and should be invalidated when
        this entry changes.

        Args:
            cache_key: Cache key to analyze

        Returns:
            List of patterns that should be invalidated when this key changes
        """
        patterns = []

        # Extract information from cache key
        entity_id = cls.extract_entity_id_from_key(cache_key)
        domain = cls.extract_domain_from_key(cache_key)

        # If entity state changes, invalidate related caches
        if entity_id:
            patterns.append(f"entities:state:id={entity_id}*")
            patterns.append("entities:list:*")  # Entity list may include this entity

            if domain:
                patterns.append(f"domains:summary:domain={domain}*")

            # Areas may contain this entity
            patterns.append("areas:entities:*")

        # If domain summary changes, invalidate entity list for that domain
        if domain and "domains:summary" in cache_key:
            patterns.append(f"entities:list:domain={domain}*")

        # If area entities change, invalidate area-related caches
        if "areas:entities" in cache_key:
            patterns.append("areas:list:*")

        return patterns
