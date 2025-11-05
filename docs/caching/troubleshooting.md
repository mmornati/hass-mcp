# Cache Troubleshooting Guide

## Overview

This guide helps you troubleshoot common cache issues, including cache not working, high memory usage, stale data, and backend-specific problems.

## Common Issues

### Cache Not Working

**Symptoms:**
- Cache statistics show 0 hits
- All calls are cache misses
- No performance improvement

**Diagnosis:**
```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Cache enabled: {stats['enabled']}")
print(f"Backend: {stats['backend']}")
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
```

**Solutions:**

1. **Check if caching is enabled:**
   ```bash
   echo $HASS_MCP_CACHE_ENABLED
   # Should be "true" or unset (defaults to true)
   ```

2. **Verify backend is initialized:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   backend = await manager._get_backend()
   print(f"Backend: {backend.__class__.__name__}")
   ```

3. **Check logs for cache errors:**
   ```bash
   # Look for cache-related errors in logs
   grep -i "cache" logs/app.log
   ```

4. **Verify cache directory is writable (file backend):**
   ```bash
   ls -ld $HASS_MCP_CACHE_DIR
   # Should be writable
   ```

### High Memory Usage

**Symptoms:**
- Memory usage is high
- Cache size is large
- System performance degradation

**Diagnosis:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
if hasattr(backend, "async_size"):
    size = await backend.async_size()
    print(f"Cache size: {size} entries")
```

**Solutions:**

1. **Reduce cache size:**
   ```bash
   export HASS_MCP_CACHE_MAX_SIZE=1000
   ```

2. **Reduce TTL values:**
   ```json
   {
     "endpoints": {
       "entities": {
         "get_state": {
           "ttl": 30
         }
       }
     }
   }
   ```

3. **Switch to Redis or file backend:**
   ```bash
   export HASS_MCP_CACHE_BACKEND=redis
   ```

4. **Clear cache periodically:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   await manager.clear()
   ```

### Stale Data

**Symptoms:**
- Cached data is outdated
- Changes not reflected immediately
- Data doesn't match Home Assistant

**Diagnosis:**
```python
# Check TTL values
from app.core.cache.config import get_cache_config

config = get_cache_config()
print(config.get_all_config())
```

**Solutions:**

1. **Reduce TTL values:**
   ```json
   {
     "endpoints": {
       "entities": {
         "get_state": {
           "ttl": 30
         }
       }
     }
   }
   ```

2. **Verify cache invalidation is working:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   # Check invalidation statistics
   stats = manager.get_statistics()
   print(f"Invalidations: {stats['invalidations']}")
   ```

3. **Clear cache manually:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   await manager.clear()
   ```

4. **Check invalidation patterns:**
   ```python
   # Verify invalidation patterns match cache keys
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   keys = await manager.keys("entities:*")
   print(f"Entity cache keys: {keys}")
   ```

### Low Hit Rate

**Symptoms:**
- Hit rate <50%
- Cache not effective
- High number of cache misses

**Diagnosis:**
```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
print(f"Per-endpoint stats: {stats['per_endpoint']}")
```

**Solutions:**

1. **Increase TTL values:**
   ```json
   {
     "endpoints": {
       "entities": {
         "get_state": {
           "ttl": 120
         }
       }
     }
   }
   ```

2. **Check for parameter variations:**
   ```python
   # Verify cache keys are consistent
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   keys = await manager.keys("entities:*")
   print(f"Cache keys: {keys}")
   ```

3. **Review cache invalidation patterns:**
   ```python
   # Check if invalidation is too frequent
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   stats = manager.get_statistics()
   print(f"Invalidations: {stats['invalidations']}")
   ```

4. **Optimize cache keys:**
   ```python
   # Use include_params or exclude_params to optimize keys
   @cached(ttl=TTL_LONG, exclude_params=["verbose", "detailed"])
   async def get_data(verbose: bool = False, detailed: bool = False):
       ...
   ```

## Backend-Specific Issues

### Redis Connection Problems

**Symptoms:**
- Redis backend not working
- Connection errors in logs
- Fallback to memory backend

**Diagnosis:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
# Should be RedisCacheBackend, not MemoryCacheBackend
```

**Solutions:**

1. **Check Redis URL:**
   ```bash
   echo $HASS_MCP_CACHE_REDIS_URL
   # Should be valid Redis URL
   ```

2. **Verify Redis is running:**
   ```bash
   redis-cli ping
   # Should return "PONG"
   ```

3. **Check Redis connection:**
   ```bash
   redis-cli -u $HASS_MCP_CACHE_REDIS_URL ping
   # Should return "PONG"
   ```

4. **Check Redis authentication:**
   ```bash
   # If Redis requires authentication
   export HASS_MCP_CACHE_REDIS_URL=redis://user:password@host:port/db
   ```

5. **Check network connectivity:**
   ```bash
   # Test network connection
   telnet redis-host 6379
   ```

### File Backend Issues

**Symptoms:**
- File backend not working
- Permission errors in logs
- Fallback to memory backend

**Diagnosis:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
# Should be FileCacheBackend, not MemoryCacheBackend
```

**Solutions:**

1. **Check cache directory permissions:**
   ```bash
   ls -ld $HASS_MCP_CACHE_DIR
   # Should be writable
   ```

2. **Create cache directory:**
   ```bash
   mkdir -p $HASS_MCP_CACHE_DIR
   chmod 755 $HASS_MCP_CACHE_DIR
   ```

3. **Check disk space:**
   ```bash
   df -h $HASS_MCP_CACHE_DIR
   # Should have sufficient space
   ```

4. **Verify aiofiles is installed:**
   ```bash
   pip list | grep aiofiles
   # Should show aiofiles package
   ```

5. **Check file system permissions:**
   ```bash
   # Ensure user has write permissions
   touch $HASS_MCP_CACHE_DIR/test.txt
   rm $HASS_MCP_CACHE_DIR/test.txt
   ```

### Memory Backend Issues

**Symptoms:**
- High memory usage
- Cache size exceeds limit
- Performance degradation

**Solutions:**

1. **Reduce cache size:**
   ```bash
   export HASS_MCP_CACHE_MAX_SIZE=1000
   ```

2. **Clear cache periodically:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   await manager.clear()
   ```

3. **Switch to Redis or file backend:**
   ```bash
   export HASS_MCP_CACHE_BACKEND=redis
   ```

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.getLogger("app.core.cache").setLevel(logging.DEBUG)
```

### Check Cache Statistics

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(stats)
```

### Inspect Cache Keys

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
keys = await manager.keys("entities:*")
print(f"Entity cache keys: {keys}")
```

### Test Cache Operations

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()

# Test set
await manager.set("test_key", "test_value", ttl=60)

# Test get
value = await manager.get("test_key")
print(f"Value: {value}")

# Test delete
await manager.delete("test_key")
```

## Getting Help

If you're still experiencing issues:

1. **Check logs**: Look for cache-related errors
2. **Review documentation**: See [Architecture](architecture.md) and [Configuration](configuration.md)
3. **Check statistics**: Use `get_cache_statistics()` to diagnose issues
4. **Test cache operations**: Verify cache is working with test operations
5. **Report issues**: Create a GitHub issue with logs and statistics

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Performance Guide](performance.md)
- [Examples](examples.md)
- [FAQ](faq.md)
