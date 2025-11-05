# Cache Migration Guide

## Overview

This guide explains how to enable caching on an existing Hass-MCP installation, migrate between backends, and update configuration.

## Enabling Caching on Existing Installation

### Step 1: Verify Current Configuration

Check if caching is already enabled:

```bash
echo $HASS_MCP_CACHE_ENABLED
# If unset, caching is enabled by default
```

### Step 2: Enable Caching (if disabled)

```bash
export HASS_MCP_CACHE_ENABLED=true
```

Or in configuration file:

```json
{
  "enabled": true
}
```

### Step 3: Choose Backend

Select appropriate backend based on your use case:

**Memory Backend (Default):**
```bash
export HASS_MCP_CACHE_BACKEND=memory
```

**Redis Backend:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
```

**File Backend:**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=.cache
```

### Step 4: Verify Caching is Working

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Cache enabled: {stats['enabled']}")
print(f"Backend: {stats['backend']}")
```

## Backend Migration

### Migrating from Memory to Redis

**Step 1: Install Redis package:**
```bash
pip install redis
# Or with uv
uv pip install redis
```

**Step 2: Start Redis server:**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install Redis locally
# (See Redis documentation for your OS)
```

**Step 3: Update configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
```

**Step 4: Restart Hass-MCP:**
```bash
# Restart the MCP server
# Cache will be empty initially (expected)
```

**Step 5: Verify migration:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
# Should be RedisCacheBackend
```

### Migrating from Memory to File

**Step 1: Install aiofiles package:**
```bash
pip install aiofiles
# Or with uv
uv pip install aiofiles
```

**Step 2: Create cache directory:**
```bash
mkdir -p .cache
chmod 755 .cache
```

**Step 3: Update configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=.cache
```

**Step 4: Restart Hass-MCP:**
```bash
# Restart the MCP server
# Cache will be empty initially (expected)
```

**Step 5: Verify migration:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
# Should be FileCacheBackend
```

### Migrating from File to Redis

**Step 1: Install Redis package:**
```bash
pip install redis
```

**Step 2: Start Redis server:**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Step 3: Update configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
```

**Step 4: Restart Hass-MCP:**
```bash
# Restart the MCP server
# Cache will be empty initially (expected)
```

**Note:** Cache data from file backend is not automatically migrated. Cache will be rebuilt as endpoints are called.

### Migrating from Redis to File

**Step 1: Install aiofiles package:**
```bash
pip install aiofiles
```

**Step 2: Create cache directory:**
```bash
mkdir -p .cache
chmod 755 .cache
```

**Step 3: Update configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=.cache
```

**Step 4: Restart Hass-MCP:**
```bash
# Restart the MCP server
# Cache will be empty initially (expected)
```

**Note:** Cache data from Redis is not automatically migrated. Cache will be rebuilt as endpoints are called.

## Configuration Migration

### Migrating from Environment Variables to Configuration File

**Step 1: Create configuration file:**
```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300,
  "max_size": 1000,
  "endpoints": {
    "entities": {
      "get_state": {
        "ttl": 60
      }
    }
  }
}
```

**Step 2: Specify configuration file:**
```bash
export HASS_MCP_CACHE_CONFIG_FILE=/path/to/cache_config.json
```

**Step 3: Remove environment variables (optional):**
```bash
# Environment variables still take precedence
# But you can remove them if using config file
unset HASS_MCP_CACHE_BACKEND
unset HASS_MCP_CACHE_DEFAULT_TTL
```

### Migrating from Configuration File to Environment Variables

**Step 1: Export environment variables:**
```bash
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=memory
export HASS_MCP_CACHE_DEFAULT_TTL=300
export HASS_MCP_CACHE_MAX_SIZE=1000
```

**Step 2: Remove configuration file (optional):**
```bash
rm ~/.hass-mcp/cache_config.json
```

**Note:** Environment variables take precedence over configuration files.

## TTL Configuration Migration

### Updating TTL Values

**Step 1: Update configuration file:**
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

**Step 2: Reload configuration:**
```python
from app.core.cache.config import get_cache_config

config = get_cache_config()
config.reload()
```

**Step 3: Verify TTL:**
```python
from app.core.cache.config import get_cache_config

config = get_cache_config()
ttl = config.get_endpoint_ttl("entities", "get_state")
print(f"TTL: {ttl} seconds")
```

## Cache Data Migration

### Manual Cache Migration

Cache data is not automatically migrated between backends. To migrate:

**Step 1: Export cache data (if needed):**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
keys = await manager.keys()

# Export cache data
cache_data = {}
for key in keys:
    value = await manager.get(key)
    if value is not None:
        cache_data[key] = value

# Save to file
import json
with open("cache_export.json", "w") as f:
    json.dump(cache_data, f)
```

**Step 2: Import cache data (if needed):**
```python
from app.core.cache.manager import get_cache_manager
import json

manager = await get_cache_manager()

# Load from file
with open("cache_export.json", "r") as f:
    cache_data = json.load(f)

# Import cache data
for key, value in cache_data.items():
    await manager.set(key, value, ttl=300)
```

**Note:** Manual migration is usually not necessary. Cache will rebuild automatically as endpoints are called.

## Rollback Procedures

### Rollback to Previous Backend

**Step 1: Update configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=memory
```

**Step 2: Restart Hass-MCP:**
```bash
# Restart the MCP server
```

**Step 3: Verify rollback:**
```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
```

### Disable Caching

**Step 1: Disable caching:**
```bash
export HASS_MCP_CACHE_ENABLED=false
```

**Step 2: Restart Hass-MCP:**
```bash
# Restart the MCP server
```

**Step 3: Verify caching is disabled:**
```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Cache enabled: {stats['enabled']}")
# Should be False
```

## Best Practices

1. **Test migration in development first**
2. **Backup configuration before migration**
3. **Monitor cache performance after migration**
4. **Verify cache is working correctly**
5. **Keep old configuration as backup**

## Troubleshooting Migration

### Migration Issues

If migration fails:

1. **Check logs** for errors
2. **Verify backend is available** (Redis, file system)
3. **Check permissions** (file backend)
4. **Verify configuration** is correct
5. **Rollback** to previous configuration if needed

### Cache Not Working After Migration

1. **Verify backend is initialized:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   backend = await manager._get_backend()
   print(f"Backend: {backend.__class__.__name__}")
   ```

2. **Check cache statistics:**
   ```python
   from app.api.system import get_cache_statistics

   stats = await get_cache_statistics()
   print(stats)
   ```

3. **Clear cache and rebuild:**
   ```python
   from app.core.cache.manager import get_cache_manager

   manager = await get_cache_manager()
   await manager.clear()
   ```

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Troubleshooting Guide](troubleshooting.md)
