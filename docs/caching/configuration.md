# Cache Configuration Guide

## Overview

The Hass-MCP caching system can be configured via environment variables, configuration files, or a combination of both. Environment variables take precedence over configuration files.

## Configuration Priority

1. **Environment variables** (highest priority)
2. **Configuration file** (JSON or YAML)
3. **Default values** (lowest priority)

## Environment Variables

### Basic Configuration

```bash
# Enable/disable caching (default: true)
export HASS_MCP_CACHE_ENABLED=true

# Cache backend type (default: memory)
export HASS_MCP_CACHE_BACKEND=memory  # Options: memory, redis, file

# Default TTL in seconds (default: 300)
export HASS_MCP_CACHE_DEFAULT_TTL=300

# Maximum cache size (default: 1000)
export HASS_MCP_CACHE_MAX_SIZE=1000
```

### Redis Backend Configuration

```bash
# Set backend to Redis
export HASS_MCP_CACHE_BACKEND=redis

# Set Redis URL (optional, defaults to redis://localhost:6379/0)
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
# Or use REDIS_URL (alternative)
export REDIS_URL=redis://localhost:6379/0
```

**Redis URL Formats:**
- `redis://localhost:6379/0` - Local Redis on default port, database 0
- `redis://user:password@host:port/db` - Redis with authentication
- `rediss://host:port/db` - Redis with SSL/TLS
- `unix:///path/to/redis.sock` - Unix socket connection

### File Backend Configuration

```bash
# Set backend to file
export HASS_MCP_CACHE_BACKEND=file

# Set cache directory (optional, defaults to .cache)
export HASS_MCP_CACHE_DIR=.cache
```

### Configuration File Location

```bash
# Specify custom config file location
export HASS_MCP_CACHE_CONFIG_FILE=/path/to/cache_config.json
```

## Configuration File Format

### JSON Configuration

Create a file at `~/.hass-mcp/cache_config.json` or `.cache_config.json`:

```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300,
  "max_size": 1000,
  "redis_url": "redis://localhost:6379/0",
  "cache_dir": ".cache",
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

### YAML Configuration

Create a file at `~/.hass-mcp/cache_config.yaml` or `.cache_config.yaml`:

```yaml
enabled: true
backend: memory
default_ttl: 300
max_size: 1000
redis_url: redis://localhost:6379/0
cache_dir: .cache
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

## Per-Endpoint TTL Configuration

You can configure TTL for specific endpoints in the configuration file:

### Simple Format

```json
{
  "endpoints": {
    "entities": 1800,
    "automations": 1800,
    "areas": 3600
  }
}
```

### Detailed Format

```json
{
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
      "list": {
        "ttl": 1800
      },
      "get_config": {
        "ttl": 1800
      }
    }
  }
}
```

## Backend Selection Guide

### When to Use Memory Backend

- **Development environment**
- **Single instance deployment**
- **No persistence requirements**
- **Fastest performance needed**
- **No additional dependencies desired**

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=memory
```

### When to Use Redis Backend

- **Production environment**
- **Multiple server instances**
- **Cache persistence required**
- **High-traffic deployments**
- **Distributed caching needed**

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
```

**Installation:**
```bash
pip install redis
# Or with uv
uv pip install redis
```

### When to Use File Backend

- **Single instance deployment**
- **Cache persistence required**
- **Redis not available**
- **No network dependencies desired**

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=.cache
```

**Installation:**
```bash
pip install aiofiles
# Or with uv
uv pip install aiofiles
```

## TTL Configuration Best Practices

### Default TTL Values

The system uses these default TTL values:

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Entity states | 60s (1 min) | Frequently changing |
| Entity metadata | 1800s (30 min) | Relatively stable |
| Automations | 1800s (30 min) | Stable configuration |
| Areas | 3600s (1 hour) | Very stable |
| Zones | 3600s (1 hour) | Very stable |
| System config | 3600s (1 hour) | Very stable |

### Custom TTL Configuration

You can override default TTL values:

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

### Dynamic TTL

Some endpoints use dynamic TTL based on function parameters:

```python
@cached(ttl=lambda args, kwargs, result: TTL_LONG if kwargs.get("lean") else TTL_SHORT)
async def get_entities(lean: bool = False):
    ...
```

## Runtime Configuration Updates

You can update configuration at runtime using the `CacheConfig` API:

```python
from app.core.cache.config import get_cache_config

config = get_cache_config()

# Update endpoint TTL
config.update_endpoint_ttl("entities", 120, "get_state")

# Reload configuration
config.reload()
```

## Configuration Validation

The cache system validates configuration:

- **Invalid backend**: Falls back to memory backend with warning
- **Invalid TTL**: Uses default TTL with warning
- **Invalid Redis URL**: Falls back to memory backend with warning
- **Invalid cache directory**: Falls back to memory backend with warning

## Configuration Examples

### Development Setup

```bash
# Minimal configuration for development
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=memory
```

### Production Setup with Redis

```bash
# Production configuration with Redis
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://redis.example.com:6379/0
export HASS_MCP_CACHE_DEFAULT_TTL=300
export HASS_MCP_CACHE_MAX_SIZE=10000
```

### Production Setup with File Backend

```bash
# Production configuration with file backend
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=/var/cache/hass-mcp
export HASS_MCP_CACHE_DEFAULT_TTL=300
```

### Custom TTL Configuration

```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300,
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

## Troubleshooting Configuration

### Check Current Configuration

```python
from app.core.cache.config import get_cache_config

config = get_cache_config()
print(config.get_all_config())
```

### Verify Backend

```python
from app.core.cache.manager import get_cache_manager

manager = await get_cache_manager()
backend = await manager._get_backend()
print(f"Backend: {backend.__class__.__name__}")
```

### Check Statistics

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(stats)
```

## Security Considerations

- **Redis authentication**: Use password-protected Redis in production
- **File permissions**: Ensure cache directory has appropriate permissions
- **Environment variables**: Use secure configuration management (secrets manager, etc.)
- **Configuration files**: Store in secure locations with appropriate permissions
