"""Unit tests for advanced cache invalidation strategies (US-008)."""

import pytest

from app.core.cache.invalidation import InvalidationStrategy
from app.core.cache.manager import get_cache_manager


class TestPatternExpansion:
    """Test pattern expansion for hierarchical invalidation."""

    @pytest.mark.asyncio
    async def test_expand_entities_pattern(self):
        """Test expanding entities:* pattern."""
        cache = await get_cache_manager()
        await cache.clear()

        # Set up some test data
        await cache.set("entities:list:domain=light", "value1")
        await cache.set("entities:state:id=light.living_room", "value2")
        await cache.set("entities:get:id=light.kitchen", "value3")
        await cache.set("automations:list:", "value4")

        # Invalidate with hierarchical expansion
        result = await cache.invalidate("entities:*", hierarchical=True)

        assert result["total_invalidated"] >= 3  # Should invalidate entities entries
        assert "entities:*" in result["expanded_patterns"]
        assert len(result["expanded_patterns"]) > 1  # Should have expanded

        # Verify automations entry still exists
        value = await cache.get("automations:list:")
        assert value == "value4"

    @pytest.mark.asyncio
    async def test_expand_pattern_no_hierarchy(self):
        """Test that pattern expansion works without hierarchy."""
        cache = await get_cache_manager()
        await cache.clear()

        await cache.set("entities:state:id=light.living_room", "value1")

        # Invalidate without hierarchical expansion
        result = await cache.invalidate("entities:state:*", hierarchical=False)

        assert result["total_invalidated"] == 1
        assert len(result["expanded_patterns"]) == 1


class TestInvalidationChains:
    """Test invalidation chains."""

    @pytest.mark.asyncio
    async def test_get_invalidation_chain(self):
        """Test getting invalidation chain."""
        chain = InvalidationStrategy.get_invalidation_chain(
            "entity_update", entity_id="light.living_room", domain="light"
        )

        assert len(chain) > 0
        assert any("light.living_room" in pattern for pattern in chain)
        assert any("entities:state:id=light.living_room" in pattern for pattern in chain)
        assert any("entities:list:*" in pattern for pattern in chain)

    @pytest.mark.asyncio
    async def test_get_invalidation_chain_automation(self):
        """Test automation invalidation chain."""
        chain = InvalidationStrategy.get_invalidation_chain(
            "automation_update", automation_id="automation_1"
        )

        assert len(chain) > 0
        assert any("automation_1" in pattern for pattern in chain)
        assert any("automations:config:id=automation_1" in pattern for pattern in chain)
        assert any("automations:list:*" in pattern for pattern in chain)

    @pytest.mark.asyncio
    async def test_get_invalidation_chain_missing_variable(self):
        """Test invalidation chain with missing variable."""
        # Should not raise error, but include original pattern
        chain = InvalidationStrategy.get_invalidation_chain("entity_update", entity_id="light.1")

        assert len(chain) > 0
        # Should still include patterns that don't require domain
        assert any("entities:list:*" in pattern for pattern in chain)


class TestTemplateResolution:
    """Test template pattern resolution."""

    def test_resolve_pattern_template(self):
        """Test resolving pattern template with variables."""
        pattern = "entities:state:id={entity_id}*"
        resolved = InvalidationStrategy.resolve_pattern_template(
            pattern, entity_id="light.living_room"
        )

        assert resolved == "entities:state:id=light.living_room*"

    def test_resolve_pattern_template_multiple_vars(self):
        """Test resolving pattern with multiple variables."""
        pattern = "domains:summary:domain={domain}*"
        resolved = InvalidationStrategy.resolve_pattern_template(pattern, domain="light")

        assert resolved == "domains:summary:domain=light*"

    def test_resolve_pattern_template_missing_var(self):
        """Test resolving pattern with missing variable."""
        pattern = "entities:state:id={entity_id}*"
        resolved = InvalidationStrategy.resolve_pattern_template(pattern)

        # Should return original pattern if variable missing
        assert resolved == pattern


class TestKeyExtraction:
    """Test extracting information from cache keys."""

    def test_extract_entity_id_from_key(self):
        """Test extracting entity_id from cache key."""
        key = "entities:state:id=light.living_room"
        entity_id = InvalidationStrategy.extract_entity_id_from_key(key)

        assert entity_id == "light.living_room"

    def test_extract_domain_from_key(self):
        """Test extracting domain from cache key."""
        key = "entities:list:domain=light"
        domain = InvalidationStrategy.extract_domain_from_key(key)

        assert domain == "light"

    def test_extract_domain_from_entity_id(self):
        """Test extracting domain from entity_id in key."""
        key = "entities:state:id=light.living_room"
        domain = InvalidationStrategy.extract_domain_from_key(key)

        assert domain == "light"

    def test_extract_domain_from_domain_summary(self):
        """Test extracting domain from domain summary key."""
        key = "domains:summary:domain=light"
        domain = InvalidationStrategy.extract_domain_from_key(key)

        assert domain == "light"


class TestDependencyPatterns:
    """Test building dependency patterns."""

    def test_build_dependency_patterns_entity_state(self):
        """Test building dependency patterns for entity state."""
        key = "entities:state:id=light.living_room"
        patterns = InvalidationStrategy.build_dependency_patterns(key)

        assert len(patterns) > 0
        assert any("entities:state:id=light.living_room" in p for p in patterns)
        assert any("entities:list:*" in p for p in patterns)

    def test_build_dependency_patterns_domain_summary(self):
        """Test building dependency patterns for domain summary."""
        key = "domains:summary:domain=light"
        patterns = InvalidationStrategy.build_dependency_patterns(key)

        assert len(patterns) > 0
        assert any("entities:list:domain=light" in p for p in patterns)


class TestInvalidationDecorator:
    """Test enhanced invalidate_cache decorator."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_template(self):
        """Test invalidate_cache decorator with template variables."""
        from app.core.cache.decorator import invalidate_cache

        cache = await get_cache_manager()
        await cache.clear()

        # Set up test data
        await cache.set("entities:state:id=light.living_room", "value1")
        await cache.set("entities:state:id=light.kitchen", "value2")

        @invalidate_cache(
            pattern="entities:state:id={entity_id}*", template_vars={"entity_id": "entity_id"}
        )
        async def test_function(entity_id: str) -> dict:
            return {"status": "success"}

        # Call function
        result = await test_function("light.living_room")

        # Verify specific entity cache was invalidated
        value = await cache.get("entities:state:id=light.living_room")
        assert value is None

        # Verify other entity cache still exists
        value2 = await cache.get("entities:state:id=light.kitchen")
        assert value2 == "value2"

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_chain(self):
        """Test invalidate_cache decorator with invalidation chain."""
        from app.core.cache.decorator import invalidate_cache

        cache = await get_cache_manager()
        await cache.clear()

        # Set up test data
        await cache.set("entities:state:id=light.living_room", "value1")
        await cache.set("entities:list:", "value2")
        await cache.set("domains:summary:domain=light", "value3")

        @invalidate_cache(chain="entity_update", template_vars={"entity_id": "entity_id"})
        async def test_function(entity_id: str) -> dict:
            return {"status": "success"}

        # Call function
        result = await test_function("light.living_room")

        # Verify entity state cache was invalidated
        value = await cache.get("entities:state:id=light.living_room")
        assert value is None

        # Verify entity list cache was invalidated (part of chain)
        value2 = await cache.get("entities:list:")
        assert value2 is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_auto_extract_vars(self):
        """Test invalidate_cache decorator auto-extracting template variables."""
        from app.core.cache.decorator import invalidate_cache

        cache = await get_cache_manager()
        await cache.clear()

        await cache.set("entities:state:id=light.living_room", "value1")

        @invalidate_cache(pattern="entities:state:id={entity_id}*")
        async def test_function(entity_id: str) -> dict:
            return {"status": "success"}

        # Call function - should auto-extract entity_id from parameter
        result = await test_function("light.living_room")

        # Verify cache was invalidated
        value = await cache.get("entities:state:id=light.living_room")
        assert value is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_condition(self):
        """Test invalidate_cache decorator with condition."""
        from app.core.cache.decorator import invalidate_cache

        cache = await get_cache_manager()
        await cache.clear()

        await cache.set("entities:state:id=light.living_room", "value1")

        @invalidate_cache(
            pattern="entities:state:id={entity_id}*",
            condition=lambda args, kwargs, result: result.get("status") == "success",
        )
        async def test_function(entity_id: str) -> dict:
            return {"status": "success"}

        # Call with success result
        result = await test_function("light.living_room")
        value = await cache.get("entities:state:id=light.living_room")
        assert value is None  # Should be invalidated

        # Set cache again
        await cache.set("entities:state:id=light.living_room", "value1")

        @invalidate_cache(
            pattern="entities:state:id={entity_id}*",
            condition=lambda args, kwargs, result: result.get("status") == "success",
        )
        async def test_function_fail(entity_id: str) -> dict:
            return {"status": "error"}

        # Call with error result
        result = await test_function_fail("light.living_room")
        value = await cache.get("entities:state:id=light.living_room")
        assert value == "value1"  # Should NOT be invalidated due to condition

    @pytest.mark.asyncio
    async def test_invalidate_cache_hierarchical(self):
        """Test invalidate_cache decorator with hierarchical invalidation."""
        from app.core.cache.decorator import invalidate_cache

        cache = await get_cache_manager()
        await cache.clear()

        # Set up test data with hierarchical structure
        await cache.set("entities:list:", "value1")
        await cache.set("entities:state:id=light.living_room", "value2")
        await cache.set("entities:get:id=light.kitchen", "value3")

        @invalidate_cache(pattern="entities:*", hierarchical=True)
        async def test_function() -> dict:
            return {"status": "success"}

        # Call function
        result = await test_function()

        # All entities caches should be invalidated
        value1 = await cache.get("entities:list:")
        value2 = await cache.get("entities:state:id=light.living_room")
        value3 = await cache.get("entities:get:id=light.kitchen")

        assert value1 is None
        assert value2 is None
        assert value3 is None


class TestInvalidationManager:
    """Test invalidation manager methods."""

    @pytest.mark.asyncio
    async def test_invalidate_returns_results(self):
        """Test that invalidate returns detailed results."""
        cache = await get_cache_manager()
        await cache.clear()

        await cache.set("entities:state:id=light.living_room", "value1")
        await cache.set("entities:state:id=light.kitchen", "value2")

        result = await cache.invalidate("entities:state:*", hierarchical=False)

        assert "pattern" in result
        assert "expanded_patterns" in result
        assert "total_invalidated" in result
        assert "keys_invalidated" in result
        assert result["total_invalidated"] == 2
        assert len(result["keys_invalidated"]) == 2

    @pytest.mark.asyncio
    async def test_invalidate_with_hierarchical_expansion(self):
        """Test invalidate with hierarchical expansion."""
        cache = await get_cache_manager()
        await cache.clear()

        # Set up hierarchical cache structure
        await cache.set("entities:list:", "value1")
        await cache.set("entities:state:id=light.living_room", "value2")
        await cache.set("entities:get:id=light.kitchen", "value3")

        result = await cache.invalidate("entities:*", hierarchical=True)

        assert result["total_invalidated"] >= 3
        assert len(result["expanded_patterns"]) > 1

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup_expired method."""
        cache = await get_cache_manager()
        await cache.clear()

        # Set entries with different TTLs
        await cache.set("key1", "value1", ttl=1)
        await cache.set("key2", "value2", ttl=100)

        # Wait for first entry to expire
        import asyncio

        await asyncio.sleep(1.1)

        # Cleanup expired entries
        removed = await cache.cleanup_expired()

        assert removed >= 1
        # Verify expired entry is gone
        value1 = await cache.get("key1")
        assert value1 is None

        # Verify non-expired entry still exists
        value2 = await cache.get("key2")
        assert value2 == "value2"
