# Cache FAQ

## Frequently Asked Questions

### General Questions

#### Q: What is caching and why do I need it?

**A:** Caching stores frequently accessed data in memory (or Redis/file) to avoid repeated API calls to Home Assistant. This significantly improves response times and reduces load on your Home Assistant instance.

**Benefits:**
- **Faster responses**: Cache hits are 50-200x faster than API calls
- **Reduced API calls**: 60-80% reduction in API calls
- **Better performance**: Improved overall system performance

#### Q: Is caching enabled by default?

**A:** Yes, caching is enabled by default. No configuration is needed to start using caching.

#### Q: Can I disable caching?

**A:** Yes, you can disable caching:

```bash
export HASS_MCP_CACHE_ENABLED=false
```

#### Q: Will caching break my API calls if it fails?

**A:** No, the cache system is designed to gracefully degrade. If cache operations fail, API calls proceed normally without caching. Cache failures never break API calls.

### Configuration Questions

#### Q: Which backend should I use?

**A:** Choose based on your use case:

- **Memory**: Development, single instance, fastest performance
- **Redis**: Production, multiple instances, shared cache
- **File**: Single instance, persistence needed, no Redis

See [Configuration Guide](configuration.md) for details.

#### Q: How do I configure Redis backend?

**A:**

1. Install Redis package: `pip install redis`
2. Start Redis server: `docker run -d -p 6379:6379 redis:latest`
3. Configure: `export HASS_MCP_CACHE_BACKEND=redis`
4. Set Redis URL: `export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0`

See [Configuration Guide](configuration.md) for details.

#### Q: How do I configure file backend?

**A:**

1. Install aiofiles package: `pip install aiofiles`
2. Create cache directory: `mkdir -p .cache`
3. Configure: `export HASS_MCP_CACHE_BACKEND=file`
4. Set cache directory: `export HASS_MCP_CACHE_DIR=.cache`

See [Configuration Guide](configuration.md) for details.

#### Q: Can I use a configuration file instead of environment variables?

**A:** Yes, you can use a JSON or YAML configuration file:

```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300
}
```

See [Configuration Guide](configuration.md) for details.

### TTL Questions

#### Q: What is TTL?

**A:** TTL (Time-To-Live) is the duration in seconds that cached data remains valid. After TTL expires, the cache entry is removed and fresh data is fetched.

#### Q: How do I set TTL for specific endpoints?

**A:** Use the configuration file:

```json
{
  "endpoints": {
    "entities": {
      "get_state": {
        "ttl": 60
      }
    }
  }
}
```

See [Configuration Guide](configuration.md) for details.

#### Q: What are the default TTL values?

**A:**

- **Very Long (1 hour)**: Areas, zones, system config
- **Long (30 minutes)**: Automations, scripts, scenes
- **Medium (5 minutes)**: Integrations, statistics
- **Short (1 minute)**: Entity states

See [Architecture Documentation](architecture.md) for details.

### Performance Questions

#### Q: What hit rate should I expect?

**A:** Target hit rates:

- **Static data**: >95%
- **Stable data**: >85%
- **Semi-dynamic data**: >70%
- **Overall**: >75%

See [Performance Guide](performance.md) for details.

#### Q: How much memory does caching use?

**A:**

- **Per entry**: ~1-5 KB
- **1000 entries**: ~1-5 MB
- **10,000 entries**: ~10-50 MB

See [Performance Guide](performance.md) for details.

#### Q: How do I monitor cache performance?

**A:** Use the cache statistics API:

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
```

See [User Guide](user-guide.md) for details.

### Invalidation Questions

#### Q: When is cache invalidated?

**A:** Cache is automatically invalidated when data is modified:

- **Entity states**: When performing entity actions or calling services
- **Automations**: When creating, updating, or deleting automations
- **Areas**: When creating, updating, or deleting areas
- **And more**: See [Architecture Documentation](architecture.md) for details

#### Q: How do I manually invalidate cache?

**A:** Use the cache manager:

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
await manager.invalidate("entities:*")
```

See [User Guide](user-guide.md) for details.

#### Q: What are invalidation patterns?

**A:** Invalidation patterns use wildcards to match cache keys:

- `entities:*` - Invalidates all entity caches
- `entities:state:*` - Invalidates all entity state caches
- `entities:state:id=light.living_room*` - Invalidates specific entity state

See [Architecture Documentation](architecture.md) for details.

### Troubleshooting Questions

#### Q: Cache is not working. What should I check?

**A:**

1. Check if caching is enabled: `echo $HASS_MCP_CACHE_ENABLED`
2. Verify backend is initialized
3. Check logs for cache errors
4. Verify cache directory is writable (file backend)

See [Troubleshooting Guide](troubleshooting.md) for details.

#### Q: I'm seeing stale data. How do I fix it?

**A:**

1. Reduce TTL values
2. Verify cache invalidation is working
3. Clear cache manually
4. Check invalidation patterns

See [Troubleshooting Guide](troubleshooting.md) for details.

#### Q: My hit rate is low. How do I improve it?

**A:**

1. Increase TTL values for stable data
2. Reduce cache invalidation frequency
3. Optimize cache keys
4. Review cache invalidation patterns

See [Troubleshooting Guide](troubleshooting.md) for details.

#### Q: Redis connection is failing. What should I do?

**A:**

1. Check Redis URL: `echo $HASS_MCP_CACHE_REDIS_URL`
2. Verify Redis is running: `redis-cli ping`
3. Check network connectivity
4. Verify Redis authentication

See [Troubleshooting Guide](troubleshooting.md) for details.

### Development Questions

#### Q: How do I add caching to a new endpoint?

**A:** Add the `@cached` decorator:

```python
from app.core.cache.decorator import cached
from app.core.cache.ttl import TTL_LONG

@cached(ttl=TTL_LONG)
async def get_data():
    ...
```

See [Developer Guide](developer-guide.md) for details.

#### Q: How do I invalidate cache on mutations?

**A:** Add the `@invalidate_cache` decorator:

```python
from app.core.cache.decorator import invalidate_cache

@invalidate_cache(pattern="data:*")
async def create_data(config: dict):
    ...
```

See [Developer Guide](developer-guide.md) for details.

#### Q: How do I test cache behavior?

**A:** Test cache hit/miss behavior:

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.mark.asyncio
async def test_cache():
    manager = await get_cache_manager()
    await manager.clear()

    # First call: Cache miss
    result1 = await get_data()
    assert manager.get_statistics()["misses"] == 1

    # Second call: Cache hit
    result2 = await get_data()
    assert manager.get_statistics()["hits"] == 1
```

See [Developer Guide](developer-guide.md) for details.

### Backend Questions

#### Q: Can I use multiple backends at once?

**A:** No, only one backend can be active at a time. However, you can migrate between backends.

See [Migration Guide](migration.md) for details.

#### Q: What happens if Redis is unavailable?

**A:** The system automatically falls back to memory backend with a warning. API calls continue normally.

#### Q: What happens if file backend fails?

**A:** The system automatically falls back to memory backend with a warning. API calls continue normally.

#### Q: Can I share cache between multiple instances?

**A:** Yes, with Redis backend. Memory and file backends are per-instance.

### Data Questions

#### Q: What data is cached?

**A:** See [User Guide](user-guide.md) for a complete list. Generally:

- **Cached**: Entity metadata, automations, scripts, scenes, areas, zones, system config
- **Not cached**: Logbook, history, statistics, events, execution logs

#### Q: What data is not cached?

**A:** Highly dynamic, time-sensitive data is not cached:

- Logbook entries
- Entity history
- Statistics calculations
- Events
- Automation execution logs
- Error logs

See [User Guide](user-guide.md) for details.

#### Q: How long is data cached?

**A:** Depends on the data type:

- **Very stable data**: 1 hour
- **Stable data**: 30 minutes
- **Moderately stable data**: 5 minutes
- **Semi-dynamic data**: 1 minute

See [Architecture Documentation](architecture.md) for details.

## Getting Help

If you have questions not covered in this FAQ:

1. **Check documentation**: See [Architecture](architecture.md), [Configuration](configuration.md), [User Guide](user-guide.md)
2. **Review examples**: See [Examples](examples.md)
3. **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
4. **GitHub Issues**: Create an issue on GitHub

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Developer Guide](developer-guide.md)
- [Performance Guide](performance.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Examples](examples.md)
