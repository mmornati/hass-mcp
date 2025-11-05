# Cache Developer Guide

## Overview

This guide explains how to add caching to new endpoints, use cache decorators, implement cache invalidation, and follow best practices for cache development.

## Adding Caching to Endpoints

### Basic Caching

Add the `@cached` decorator to automatically cache function results:

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG

@cached(ttl=TTL_LONG)
async def get_automations():
    """Get all automations."""
    # Function implementation
    ...
```

### Using TTL Presets

Use TTL presets based on data volatility:

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_VERY_LONG, TTL_LONG, TTL_MEDIUM, TTL_SHORT

# Very stable data (1 hour)
@cached(ttl=TTL_VERY_LONG)
async def get_areas():
    ...

# Stable data (30 minutes)
@cached(ttl=TTL_LONG)
async def get_automations():
    ...

# Moderately stable data (5 minutes)
@cached(ttl=TTL_MEDIUM)
async def get_integrations():
    ...

# Semi-dynamic data (1 minute)
@cached(ttl=TTL_SHORT)
async def get_entity_state(entity_id: str):
    ...
```

### Custom TTL

Specify a custom TTL value:

```python
@cached(ttl=120)  # 2 minutes
async def get_custom_data():
    ...
```

### Dynamic TTL

Use a callable function for dynamic TTL based on function parameters:

```python
def get_entities_ttl(args: tuple, kwargs: dict, result: Any) -> int:
    """Return TTL based on lean parameter."""
    if kwargs.get("lean", False):
        return TTL_LONG  # Metadata only, longer TTL
    return TTL_SHORT  # Includes state, shorter TTL

@cached(ttl=get_entities_ttl)
async def get_entities(lean: bool = False):
    """Get entities with optional lean format."""
    ...
```

### Custom Key Prefix

Specify a custom key prefix:

```python
@cached(ttl=TTL_LONG, key_prefix="automations")
async def get_automations():
    ...
```

### Parameter Filtering

Include or exclude specific parameters from the cache key:

```python
# Include only specific parameters
@cached(ttl=TTL_LONG, include_params=["domain", "entity_id"])
async def get_entity(domain: str, entity_id: str, detailed: bool = False):
    ...

# Exclude specific parameters
@cached(ttl=TTL_LONG, exclude_params=["detailed", "verbose"])
async def get_entities(domain: str, detailed: bool = False, verbose: bool = False):
    ...
```

### Conditional Caching

Cache only when a condition is met:

```python
def should_cache_entity_state(args: tuple, kwargs: dict, result: Any) -> bool:
    """Only cache if state is not 'unknown' or 'unavailable'."""
    if isinstance(result, dict):
        state = result.get("state", "")
        return state not in ("unknown", "unavailable")
    return True

@cached(ttl=TTL_SHORT, condition=should_cache_entity_state)
async def get_entity_state(entity_id: str):
    """Get entity state with conditional caching."""
    ...
```

## Cache Invalidation

### Basic Invalidation

Add `@invalidate_cache` decorator to invalidate cache on mutations:

```python
from app.core.cache.decorator import invalidate_cache

@invalidate_cache(pattern="automations:*")
async def create_automation(config: dict):
    """Create automation and invalidate cache."""
    ...
```

### Pattern-Based Invalidation

Use wildcard patterns to invalidate multiple cache entries:

```python
# Invalidate all entity caches
@invalidate_cache(pattern="entities:*")
async def update_entity(entity_id: str, state: dict):
    ...

# Invalidate specific entity state
@invalidate_cache(pattern="entities:state:id=light.living_room*")
async def turn_on_light(entity_id: str):
    ...
```

### Multiple Patterns

Invalidate multiple patterns:

```python
@invalidate_cache(
    patterns=[
        "entities:state:*",
        "entities:list:*",
        "entities:domain:*"
    ]
)
async def update_entity(entity_id: str, state: dict):
    ...
```

### Template-Based Invalidation

Use template variables for dynamic invalidation:

```python
@invalidate_cache(pattern="entities:state:id={entity_id}*")
async def entity_action(entity_id: str, action: str):
    """Invalidate cache for specific entity."""
    ...
```

The decorator automatically extracts `entity_id` from function arguments.

### Invalidation Chains

Use pre-configured invalidation chains:

```python
@invalidate_cache(chain="entity_update", template_vars={"entity_id": "entity_id"})
async def update_entity(entity_id: str, state: dict):
    """Use entity_update chain to invalidate related caches."""
    ...
```

Available chains:
- `entity_update`: Invalidates entity state, list, domain summary, and area entities
- `automation_update`: Invalidates automation config and list
- `area_update`: Invalidates area list and area entities
- `zone_update`: Invalidates zone list
- `scene_update`: Invalidates scene list
- `tag_update`: Invalidates tag list
- `integration_update`: Invalidates integration config and list

### Conditional Invalidation

Invalidate only when a condition is met:

```python
@invalidate_cache(
    pattern="automations:*",
    condition=lambda args, kwargs, result: result.get("status") == "success"
)
async def create_automation(config: dict):
    """Only invalidate if operation succeeds."""
    ...
```

### Hierarchical Invalidation

Hierarchical invalidation is automatic:

```python
# Invalidating "entities:*" also invalidates:
# - entities:state:*
# - entities:list:*
# - entities:domain:*
@invalidate_cache(pattern="entities:*")
async def update_entity(entity_id: str, state: dict):
    ...
```

## Best Practices

### 1. Choose Appropriate TTL

- **Very Long (1 hour)**: Very stable data (areas, zones, system config)
- **Long (30 minutes)**: Stable data (automations, scripts, scenes)
- **Medium (5 minutes)**: Moderately stable data (integrations, statistics)
- **Short (1 minute)**: Semi-dynamic data (entity states)

### 2. Use Conditional Caching

Don't cache error responses or invalid states:

```python
def should_cache(result: Any) -> bool:
    """Only cache successful responses."""
    if isinstance(result, dict):
        return "error" not in result
    return True

@cached(ttl=TTL_LONG, condition=should_cache)
async def get_data():
    ...
```

### 3. Invalidate on Mutations

Always invalidate cache when data is modified:

```python
@invalidate_cache(pattern="entities:*")
async def create_entity(config: dict):
    ...

@invalidate_cache(pattern="entities:*")
async def update_entity(entity_id: str, state: dict):
    ...

@invalidate_cache(pattern="entities:*")
async def delete_entity(entity_id: str):
    ...
```

### 4. Use Invalidation Chains

Use pre-configured chains for common operations:

```python
@invalidate_cache(chain="entity_update", template_vars={"entity_id": "entity_id"})
async def entity_action(entity_id: str, action: str):
    ...
```

### 5. Exclude Dynamic Data

Don't cache highly dynamic data:

```python
# Don't cache logbook, history, statistics
# These are explicitly excluded from caching
async def get_logbook():
    """Logbook is not cached - always fresh."""
    ...
```

### 6. Test Cache Behavior

Test cache hit/miss behavior:

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.mark.asyncio
async def test_cache_behavior():
    """Test cache hit/miss behavior."""
    manager = await get_cache_manager()
    await manager.clear()

    # First call: Cache miss
    result1 = await get_entity_state("light.living_room")
    assert manager.get_statistics()["misses"] == 1

    # Second call: Cache hit
    result2 = await get_entity_state("light.living_room")
    assert manager.get_statistics()["hits"] == 1
```

## Examples

### Example 1: Basic Caching

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG

@cached(ttl=TTL_LONG)
async def get_automations():
    """Get all automations."""
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/automation", headers=get_ha_headers())
    response.raise_for_status()
    return response.json()
```

### Example 2: Conditional Caching

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_SHORT

def should_cache_entity_state(args: tuple, kwargs: dict, result: Any) -> bool:
    """Only cache if state is valid."""
    if isinstance(result, dict):
        state = result.get("state", "")
        return state not in ("unknown", "unavailable")
    return True

@cached(ttl=TTL_SHORT, condition=should_cache_entity_state)
async def get_entity_state(entity_id: str):
    """Get entity state with conditional caching."""
    client = await get_client()
    response = await client.get(
        f"{HA_URL}/api/states/{entity_id}",
        headers=get_ha_headers()
    )
    response.raise_for_status()
    return response.json()
```

### Example 3: Dynamic TTL

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG, TTL_SHORT

def get_entities_ttl(args: tuple, kwargs: dict, result: Any) -> int:
    """Return TTL based on lean parameter."""
    if kwargs.get("lean", False):
        return TTL_LONG  # Metadata only
    return TTL_SHORT  # Includes state

@cached(ttl=get_entities_ttl)
async def get_entities(lean: bool = False):
    """Get entities with dynamic TTL."""
    client = await get_client()
    response = await client.get(f"{HA_URL}/api/states", headers=get_ha_headers())
    response.raise_for_status()
    entities = response.json()

    if lean:
        # Return only metadata
        return [{"entity_id": e["entity_id"]} for e in entities]

    # Return full data with state
    return entities
```

### Example 4: Cache Invalidation

```python
from app.core.cache.decorator import invalidate_cache

@invalidate_cache(pattern="automations:*")
async def create_automation(config: dict):
    """Create automation and invalidate cache."""
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/automation",
        json=config,
        headers=get_ha_headers()
    )
    response.raise_for_status()
    return response.json()
```

### Example 5: Template-Based Invalidation

```python
from app.core.cache.decorator import invalidate_cache

@invalidate_cache(pattern="entities:state:id={entity_id}*")
async def entity_action(entity_id: str, action: str):
    """Perform entity action and invalidate cache."""
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/services/{entity_id.split('.')[0]}/{action}",
        json={"entity_id": entity_id},
        headers=get_ha_headers()
    )
    response.raise_for_status()
    return response.json()
```

### Example 6: Invalidation Chain

```python
from app.core.cache.decorator import invalidate_cache

@invalidate_cache(chain="entity_update", template_vars={"entity_id": "entity_id"})
async def update_entity(entity_id: str, state: dict):
    """Update entity using invalidation chain."""
    client = await get_client()
    response = await client.post(
        f"{HA_URL}/api/states/{entity_id}",
        json=state,
        headers=get_ha_headers()
    )
    response.raise_for_status()
    return response.json()
```

## Testing Cache Code

### Test Cache Hit/Miss

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.mark.asyncio
async def test_cache_hit_miss():
    """Test cache hit and miss behavior."""
    manager = await get_cache_manager()
    await manager.clear()

    # First call: Cache miss
    result1 = await get_entity_state("light.living_room")
    stats = manager.get_statistics()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # Second call: Cache hit
    result2 = await get_entity_state("light.living_room")
    stats = manager.get_statistics()
    assert stats["misses"] == 1
    assert stats["hits"] == 1
```

### Test Cache Invalidation

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation."""
    manager = await get_cache_manager()
    await manager.clear()

    # Cache entity state
    state1 = await get_entity_state("light.living_room")
    assert await manager.get("entities:state:id=light.living_room") is not None

    # Invalidate cache
    await entity_action("light.living_room", "turn_off")

    # Cache should be invalidated
    assert await manager.get("entities:state:id=light.living_room") is None
```

### Test Conditional Caching

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.mark.asyncio
async def test_conditional_caching():
    """Test conditional caching."""
    manager = await get_cache_manager()
    await manager.clear()

    # Cache valid state
    state1 = await get_entity_state("light.living_room")
    assert await manager.get("entities:state:id=light.living_room") is not None

    # Don't cache invalid state
    # (Assuming entity returns "unknown" state)
    state2 = await get_entity_state("sensor.unknown")
    assert await manager.get("entities:state:id=sensor.unknown") is None
```

## Common Patterns

### Pattern 1: Read Operations

```python
@cached(ttl=TTL_LONG)
async def get_data():
    """Read operation - cache with long TTL."""
    ...
```

### Pattern 2: Write Operations

```python
@invalidate_cache(pattern="data:*")
async def create_data(config: dict):
    """Write operation - invalidate cache."""
    ...
```

### Pattern 3: Update Operations

```python
@invalidate_cache(pattern="data:*")
async def update_data(id: str, config: dict):
    """Update operation - invalidate cache."""
    ...
```

### Pattern 4: Delete Operations

```python
@invalidate_cache(pattern="data:*")
async def delete_data(id: str):
    """Delete operation - invalidate cache."""
    ...
```

## Troubleshooting

### Cache Not Working

1. Check if caching is enabled
2. Verify decorator is applied correctly
3. Check logs for cache errors
4. Verify cache key generation

### Cache Not Invalidating

1. Check invalidation pattern matches cache keys
2. Verify decorator is applied to mutation functions
3. Check logs for invalidation errors
4. Verify hierarchical invalidation is working

### Low Hit Rate

1. Check TTL values (may be too short)
2. Verify cache keys are consistent
3. Check if parameters are changing
4. Review cache invalidation patterns

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Performance Guide](performance.md)
- [Troubleshooting Guide](troubleshooting.md)
