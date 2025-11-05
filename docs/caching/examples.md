# Cache Examples

## Overview

This document provides practical examples for configuring and using the Hass-MCP caching system.

## Basic Configuration Examples

### Example 1: Default Configuration (Memory Backend)

```bash
# No configuration needed - uses defaults
# Backend: memory
# TTL: 300 seconds (5 minutes)
# Max size: 1000 entries
```

### Example 2: Redis Backend Configuration

```bash
# Install Redis package
pip install redis

# Start Redis server
docker run -d -p 6379:6379 redis:latest

# Configure Hass-MCP
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
export HASS_MCP_CACHE_DEFAULT_TTL=300
export HASS_MCP_CACHE_MAX_SIZE=10000
```

### Example 3: File Backend Configuration

```bash
# Install aiofiles package
pip install aiofiles

# Create cache directory
mkdir -p /var/cache/hass-mcp
chmod 755 /var/cache/hass-mcp

# Configure Hass-MCP
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=/var/cache/hass-mcp
export HASS_MCP_CACHE_DEFAULT_TTL=300
```

### Example 4: Custom TTL Configuration

```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300,
  "endpoints": {
    "entities": {
      "get_state": {
        "ttl": 60
      },
      "get_entities": {
        "ttl": 1800
      }
    },
    "automations": {
      "ttl": 1800
    },
    "areas": {
      "ttl": 3600
    }
  }
}
```

## Configuration File Examples

### Example 1: JSON Configuration File

Create `~/.hass-mcp/cache_config.json`:

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
      },
      "get_entities": {
        "ttl": 1800
      }
    },
    "automations": {
      "ttl": 1800
    },
    "areas": {
      "ttl": 3600
    }
  }
}
```

### Example 2: YAML Configuration File

Create `~/.hass-mcp/cache_config.yaml`:

```yaml
enabled: true
backend: memory
default_ttl: 300
max_size: 1000
endpoints:
  entities:
    get_state:
      ttl: 60
    get_entities:
      ttl: 1800
  automations:
    ttl: 1800
  areas:
    ttl: 3600
```

### Example 3: Production Configuration (Redis)

Create `~/.hass-mcp/cache_config.json`:

```json
{
  "enabled": true,
  "backend": "redis",
  "redis_url": "redis://redis.example.com:6379/0",
  "default_ttl": 300,
  "max_size": 10000,
  "endpoints": {
    "entities": {
      "get_state": {
        "ttl": 60
      },
      "get_entities": {
        "ttl": 1800
      }
    },
    "automations": {
      "ttl": 1800
    },
    "areas": {
      "ttl": 3600
    }
  }
}
```

## Usage Examples

### Example 1: Check Cache Status

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Cache enabled: {stats['enabled']}")
print(f"Backend: {stats['backend']}")
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
```

### Example 2: Clear Cache

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
await manager.clear()
print("Cache cleared")
```

### Example 3: Invalidate Specific Cache

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
# Invalidate all entity caches
result = await manager.invalidate("entities:*")
print(f"Invalidated {result['total_invalidated']} entries")
```

### Example 4: Get Cache Size

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
if hasattr(backend, "async_size"):
    size = await backend.async_size()
    print(f"Cache size: {size} entries")
```

## Docker Configuration Examples

### Example 1: Docker with Memory Backend

```yaml
version: '3.8'
services:
  hass-mcp:
    image: mmornati/hass-mcp:latest
    environment:
      - HA_URL=http://homeassistant.local:8123
      - HA_TOKEN=${HA_TOKEN}
      - HASS_MCP_CACHE_ENABLED=true
      - HASS_MCP_CACHE_BACKEND=memory
      - HASS_MCP_CACHE_MAX_SIZE=1000
```

### Example 2: Docker with Redis Backend

```yaml
version: '3.8'
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  hass-mcp:
    image: mmornati/hass-mcp:latest
    depends_on:
      - redis
    environment:
      - HA_URL=http://homeassistant.local:8123
      - HA_TOKEN=${HA_TOKEN}
      - HASS_MCP_CACHE_ENABLED=true
      - HASS_MCP_CACHE_BACKEND=redis
      - HASS_MCP_CACHE_REDIS_URL=redis://redis:6379/0
      - HASS_MCP_CACHE_MAX_SIZE=10000
```

### Example 3: Docker with File Backend

```yaml
version: '3.8'
services:
  hass-mcp:
    image: mmornati/hass-mcp:latest
    volumes:
      - ./cache:/app/.cache
    environment:
      - HA_URL=http://homeassistant.local:8123
      - HA_TOKEN=${HA_TOKEN}
      - HASS_MCP_CACHE_ENABLED=true
      - HASS_MCP_CACHE_BACKEND=file
      - HASS_MCP_CACHE_DIR=/app/.cache
```

## Development Examples

### Example 1: Disable Caching for Testing

```bash
export HASS_MCP_CACHE_ENABLED=false
```

### Example 2: Use Memory Backend for Development

```bash
export HASS_MCP_CACHE_BACKEND=memory
export HASS_MCP_CACHE_MAX_SIZE=1000
```

### Example 3: Clear Cache Before Tests

```python
import pytest
from app.core.cache.manager import get_cache_manager

@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear cache before each test."""
    manager = await get_cache_manager()
    await manager.clear()
    yield
    await manager.clear()
```

## Production Examples

### Example 1: Production with Redis

```bash
# Environment variables
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://redis.example.com:6379/0
export HASS_MCP_CACHE_DEFAULT_TTL=300
export HASS_MCP_CACHE_MAX_SIZE=50000
```

### Example 2: Production with File Backend

```bash
# Environment variables
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=/var/cache/hass-mcp
export HASS_MCP_CACHE_DEFAULT_TTL=300
```

### Example 3: Production with Custom TTL

```json
{
  "enabled": true,
  "backend": "redis",
  "redis_url": "redis://redis.example.com:6379/0",
  "default_ttl": 300,
  "max_size": 50000,
  "endpoints": {
    "entities": {
      "get_state": {
        "ttl": 30
      },
      "get_entities": {
        "ttl": 600
      }
    },
    "automations": {
      "ttl": 3600
    }
  }
}
```

## Monitoring Examples

### Example 1: Monitor Cache Performance

```python
from app.api.system import get_cache_statistics
import time

while True:
    stats = await get_cache_statistics()
    print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
    print(f"Time saved: {stats['performance']['time_saved_ms']}ms")
    time.sleep(60)  # Check every minute
```

### Example 2: Monitor Per-Endpoint Performance

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
for endpoint, endpoint_stats in stats['per_endpoint'].items():
    hit_rate = endpoint_stats['hit_rate']
    if hit_rate < 0.70:
        print(f"Warning: {endpoint} has low hit rate: {hit_rate:.2%}")
```

### Example 3: Alert on Low Hit Rate

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
hit_rate = stats['statistics']['hit_rate']

if hit_rate < 0.70:
    print(f"Alert: Cache hit rate is low: {hit_rate:.2%}")
    # Send alert notification
```

## Troubleshooting Examples

### Example 1: Debug Cache Issues

```python
import logging
from app.core.cache.manager import get_cache_manager

# Enable debug logging
logging.getLogger("app.core.cache").setLevel(logging.DEBUG)

# Check cache status
manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")

# Check cache keys
keys = await manager.keys("entities:*")
print(f"Entity cache keys: {keys[:10]}")  # First 10 keys
```

### Example 2: Test Cache Operations

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()

# Test set
await manager.set("test_key", "test_value", ttl=60)
print("Set test_key")

# Test get
value = await manager.get("test_key")
print(f"Got value: {value}")

# Test delete
await manager.delete("test_key")
print("Deleted test_key")

# Verify deleted
value = await manager.get("test_key")
print(f"Value after delete: {value}")  # Should be None
```

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Developer Guide](developer-guide.md)
- [Performance Guide](performance.md)
- [Troubleshooting Guide](troubleshooting.md)
- [FAQ](faq.md)
