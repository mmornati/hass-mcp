# Cache User Guide

## Overview

The Hass-MCP caching system automatically reduces API calls to Home Assistant by intelligently caching data. This guide explains how caching works, what is cached, and how to monitor and troubleshoot cache performance.

## How Caching Works

The caching system is **transparent** and **automatic**:

1. **First call**: API function fetches data from Home Assistant and caches it
2. **Subsequent calls**: API function returns cached data (if not expired)
3. **After TTL expires**: Cache entry expires and fresh data is fetched
4. **On mutations**: Cache is automatically invalidated when data changes

### Example Flow

```
User: "What's the state of the living room light?"
  ↓
First call: Cache miss → Fetch from HA → Cache result (TTL: 1 min)
  ↓
Return: "on"

User: "What's the state of the living room light?" (within 1 min)
  ↓
Second call: Cache hit → Return cached value
  ↓
Return: "on" (from cache, no HA API call)

User: "Turn off the living room light"
  ↓
Action: Turn off light → Invalidate cache → Update HA
  ↓
Next call: Cache miss → Fetch fresh state → Cache result
  ↓
Return: "off"
```

## What is Cached

### Cached Data (with TTL)

The following data is automatically cached:

#### Very Long TTL (1 hour)
- **Areas**: Area list and configuration
- **Zones**: Zone list and configuration
- **Blueprints**: Blueprint list and configuration
- **System Config**: Home Assistant core configuration
- **HA Version**: Home Assistant version

#### Long TTL (30 minutes)
- **Entities Metadata**: Entity list and metadata (without state)
- **Automations**: Automation list and configuration
- **Scripts**: Script list and configuration
- **Scenes**: Scene list and configuration
- **Devices**: Device list and details
- **Helpers**: Helper list and configuration
- **Tags**: Tag list

#### Medium TTL (5 minutes)
- **Integrations**: Integration list and configuration
- **Device Statistics**: Device statistics
- **Area Entities**: Entities in an area

#### Short TTL (1 minute)
- **Entity States**: Current state of entities
- **Entity Lists with State**: Entity lists including state information
- **Domain Summaries**: Domain summaries with state information

### Not Cached

The following data is **explicitly excluded** from caching:

- **Logbook**: Logbook entries (time-sensitive)
- **History**: Entity history (time-based)
- **Statistics**: Calculated statistics (derived from history)
- **Events**: Event log (time-sensitive)
- **Automation Execution Logs**: Execution history (time-sensitive)
- **Error Logs**: System error logs (time-sensitive)
- **System Overview**: System overview (includes current states)

These endpoints always fetch fresh data from Home Assistant.

## Enabling/Disabling Caching

### Enable Caching (Default)

Caching is enabled by default. No configuration needed.

### Disable Caching

```bash
export HASS_MCP_CACHE_ENABLED=false
```

Or in configuration file:

```json
{
  "enabled": false
}
```

### Verify Cache Status

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Cache enabled: {stats['enabled']}")
```

## Monitoring Cache Performance

### Cache Statistics

Get cache statistics via the API:

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(stats)
```

### Statistics Output

```json
{
  "enabled": true,
  "backend": "memory",
  "statistics": {
    "hits": 1234,
    "misses": 567,
    "sets": 567,
    "deletes": 45,
    "invalidations": 45,
    "hit_rate": 0.685,
    "total_operations": 1801
  },
  "performance": {
    "avg_api_call_time_ms": 45.2,
    "avg_cache_time_ms": 0.5,
    "time_saved_ms": 54321
  },
  "per_endpoint": {
    "entities.get_state": {
      "hits": 500,
      "misses": 100,
      "hit_rate": 0.833
    }
  }
}
```

### Key Metrics

- **Hit Rate**: Percentage of cache hits (target: >70%)
- **Hits**: Number of cache hits
- **Misses**: Number of cache misses
- **Time Saved**: Total time saved by caching (in milliseconds)

### Monitoring Best Practices

1. **Monitor hit rate**: Should be >70% for optimal performance
2. **Check per-endpoint stats**: Identify endpoints with low hit rates
3. **Review time saved**: Measure performance improvement
4. **Watch for errors**: Check for cache operation errors

## Common Operations

### Check Cache Status

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
stats = manager.get_statistics()
print(f"Cache enabled: {stats['enabled']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

### Clear Cache

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
await manager.clear()
```

### Invalidate Specific Cache

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
# Invalidate all entity caches
await manager.invalidate("entities:*")
```

### Get Cache Size

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
if hasattr(backend, "async_size"):
    size = await backend.async_size()
    print(f"Cache size: {size} entries")
```

## Troubleshooting Common Issues

### Cache Not Working

**Symptoms**: Cache statistics show 0 hits, all calls are misses

**Solutions**:
1. Check if caching is enabled: `HASS_MCP_CACHE_ENABLED=true`
2. Verify backend is initialized correctly
3. Check logs for cache errors
4. Ensure cache directory is writable (file backend)

### High Memory Usage

**Symptoms**: Memory usage is high, cache size is large

**Solutions**:
1. Reduce `HASS_MCP_CACHE_MAX_SIZE`
2. Reduce TTL values for less critical data
3. Switch to Redis or file backend
4. Clear cache periodically

### Stale Data

**Symptoms**: Cached data is outdated, changes not reflected

**Solutions**:
1. Check TTL values (may be too long)
2. Verify cache invalidation is working
3. Clear cache manually if needed
4. Check logs for invalidation errors

### Low Hit Rate

**Symptoms**: Hit rate is <50%, cache not effective

**Solutions**:
1. Increase TTL values for stable data
2. Check if endpoints are being called with different parameters
3. Verify cache keys are consistent
4. Review cache invalidation patterns

## Best Practices

### For Users

1. **Monitor cache performance**: Regularly check cache statistics
2. **Adjust TTL if needed**: Customize TTL for your use case
3. **Clear cache when needed**: Clear cache if you suspect stale data
4. **Use appropriate backend**: Choose backend based on your deployment

### For Developers

1. **Use `@cached` decorator**: Add caching to appropriate endpoints
2. **Use `@invalidate_cache` decorator**: Invalidate cache on mutations
3. **Set appropriate TTL**: Use TTL presets based on data volatility
4. **Test cache behavior**: Verify cache hit/miss behavior in tests

## Performance Tips

1. **Use lean format**: Use `lean=True` for entity lists to reduce cache size
2. **Filter queries**: Use domain filters to reduce cache entries
3. **Monitor hit rate**: Aim for >70% hit rate
4. **Choose right backend**: Use Redis for production, memory for development

## Examples

### Basic Usage

```python
# Caching is automatic - no code changes needed
from app.api.entities import get_entity_state

# First call: Cache miss, fetches from HA
state1 = await get_entity_state("light.living_room")

# Second call: Cache hit, returns cached value
state2 = await get_entity_state("light.living_room")
```

### Monitoring Cache

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
print(f"Time saved: {stats['performance']['time_saved_ms']}ms")
```

### Clearing Cache

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
await manager.clear()
print("Cache cleared")
```

## Getting Help

- **Documentation**: See [Architecture](architecture.md) and [Configuration](configuration.md)
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
- **Examples**: See [Examples](examples.md)
- **FAQ**: See [FAQ](faq.md)
