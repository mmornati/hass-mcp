# Cache Architecture

## Overview

The Hass-MCP caching system is designed to reduce API calls to Home Assistant by intelligently caching data based on its volatility. The cache is transparent, automatically handles expiration and invalidation, and gracefully degrades if cache operations fail.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server / API Layer                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              @cached Decorator                        │  │
│  │  - Automatic caching                                  │  │
│  │  - TTL management                                     │  │
│  │  - Conditional caching                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Cache Manager (Singleton)                  │  │
│  │  - Cache operations (get, set, delete)               │  │
│  │  - Statistics tracking                               │  │
│  │  - Invalidation management                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Cache Backend (Abstract)                   │  │
│  │  - Memory Backend (default)                          │  │
│  │  - Redis Backend (optional)                          │  │
│  │  - File Backend (optional)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Cache Decorator (`@cached`)

The `@cached` decorator automatically caches function results:

- **Automatic key generation** from function parameters
- **TTL management** based on data type or custom TTL
- **Conditional caching** to skip caching error responses
- **Metrics tracking** for cache performance

### 2. Cache Manager

The `CacheManager` is a singleton that provides:

- **Unified interface** for cache operations
- **Backend management** (initialization and fallback)
- **Statistics tracking** (hits, misses, hit rate)
- **Invalidation coordination** with hierarchical support

### 3. Cache Backends

The system supports multiple backend implementations:

#### Memory Backend (Default)
- **Storage**: In-process memory
- **Performance**: Fastest (no I/O overhead)
- **Persistence**: Lost on restart
- **Use case**: Single instance, development

#### Redis Backend (Optional)
- **Storage**: Redis database
- **Performance**: Fast (network latency minimal with local Redis)
- **Persistence**: Survives restarts
- **Use case**: Multiple instances, production deployments

#### File Backend (Optional)
- **Storage**: Filesystem
- **Performance**: Moderate (disk I/O)
- **Persistence**: Survives restarts
- **Use case**: Single instance, no Redis available

## Cache Key Structure

Cache keys follow a hierarchical structure:

```
{prefix}:{type}:{parameters}
```

Examples:
- `entities:state:id=light.living_room` - Entity state
- `entities:list:domain=light:lean=True` - Entity list
- `automations:list:` - Automation list
- `automations:config:id=automation_123` - Automation config

### Key Components

1. **Prefix**: Identifies the data category (e.g., `entities`, `automations`)
2. **Type**: Identifies the operation type (e.g., `state`, `list`, `config`)
3. **Parameters**: Function parameters encoded as key-value pairs

## TTL Strategy

Different data types have different TTL (Time-To-Live) values based on volatility:

| TTL Preset | Duration | Use Case |
|------------|----------|----------|
| `TTL_VERY_LONG` | 1 hour | Very stable data (HA version, areas, zones, blueprints, system config) |
| `TTL_LONG` | 30 minutes | Stable data (automations, scripts, scenes, devices, tags, helpers, entity metadata) |
| `TTL_MEDIUM` | 5 minutes | Moderately stable data (integrations, device statistics, area entities) |
| `TTL_SHORT` | 1 minute | Semi-dynamic data (entity states, entity lists with state info, domain summaries) |
| `TTL_DISABLED` | 0 | No caching (highly dynamic data like logs, history, statistics) |

## Invalidation Strategy

Cache invalidation uses multiple strategies:

### 1. Pattern-Based Invalidation

Wildcard patterns match cache keys:
- `entities:*` - Invalidates all entity caches
- `entities:state:*` - Invalidates all entity state caches
- `entities:state:id=light.living_room*` - Invalidates specific entity state

### 2. Hierarchical Invalidation

Parent patterns automatically invalidate child patterns:
- Invalidating `entities:*` also invalidates `entities:state:*`, `entities:list:*`, etc.
- Specific patterns (with IDs) don't expand to avoid over-invalidation

### 3. Invalidation Chains

Pre-configured chains invalidate related caches:
- **Entity update chain**: Invalidates state, list, domain summary, and area entities
- **Automation update chain**: Invalidates config and list
- **Area update chain**: Invalidates list and area entities

### 4. Template-Based Invalidation

Patterns support template variables:
```python
@invalidate_cache(pattern="entities:state:id={entity_id}*")
async def entity_action(entity_id: str, action: str):
    ...
```

### 5. Conditional Invalidation

Invalidation can be conditional:
```python
@invalidate_cache(
    pattern="automations:*",
    condition=lambda args, kwargs, result: result.get("status") == "success"
)
async def create_automation(config: dict):
    ...
```

## Graceful Degradation

The cache system is designed to never break API calls:

- **Cache failures are logged** but don't raise exceptions
- **Backend initialization failures** fall back to memory backend
- **Cache operations** return defaults (None, empty list, etc.) on error
- **API calls proceed normally** even if caching is disabled or fails

## Metrics and Monitoring

The cache system tracks:

- **Hit/Miss statistics**: Total hits, misses, hit rate
- **Per-endpoint statistics**: Hits, misses, hit rate per endpoint
- **Performance metrics**: Average API call time, cache retrieval time, time saved
- **Cache health**: Backend availability, size limits, hit rate thresholds

## Data Flow

### Cache Hit Flow

```
1. API function called
2. @cached decorator generates cache key
3. Cache manager checks cache
4. Cache hit → Return cached value
5. Record hit statistics
```

### Cache Miss Flow

```
1. API function called
2. @cached decorator generates cache key
3. Cache manager checks cache
4. Cache miss → Call Home Assistant API
5. Store result in cache with TTL
6. Record miss statistics
7. Return result
```

### Invalidation Flow

```
1. Mutation operation (create, update, delete)
2. @invalidate_cache decorator triggered
3. Generate invalidation patterns
4. Expand hierarchical patterns
5. Match cache keys
6. Delete matching entries
7. Record invalidation statistics
```

## Backend Comparison

| Feature | Memory | Redis | File |
|---------|--------|-------|------|
| **Speed** | Fastest | Fast | Moderate |
| **Persistence** | No | Yes | Yes |
| **Shared** | No | Yes | No* |
| **Dependencies** | None | redis | aiofiles |
| **Setup** | None | Redis server | None |
| **Use Case** | Dev, single instance | Production, multiple instances | Single instance, no Redis |

*File backend can be shared if using a shared filesystem (NFS, etc.)

## Design Principles

1. **Transparency**: Caching is automatic and transparent to API consumers
2. **Flexibility**: Multiple backends for different use cases
3. **Reliability**: Graceful degradation ensures API calls never fail due to cache issues
4. **Performance**: Optimized for speed with minimal overhead
5. **Observability**: Comprehensive metrics for monitoring and debugging
