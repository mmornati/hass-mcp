# Cache Performance Guide

## Overview

This guide explains performance considerations for the Hass-MCP caching system, including expected improvements, hit rate targets, memory/disk usage guidelines, and backend selection recommendations.

## Expected Performance Improvements

### API Call Reduction

Caching can significantly reduce API calls to Home Assistant:

- **Static data** (areas, zones, automations): 95%+ reduction
- **Semi-dynamic data** (entity states): 70-90% reduction
- **Overall**: 60-80% reduction in API calls

### Response Time Improvement

Cache hits are significantly faster than API calls:

- **Cache hit**: <1ms (in-memory), <5ms (Redis), <10ms (file)
- **API call**: 50-200ms (depending on network latency)
- **Improvement**: 50-200x faster for cache hits

### Example Performance

```
Without Cache:
- 1000 entity state queries: 1000 API calls × 100ms = 100 seconds

With Cache (70% hit rate):
- 300 cache misses × 100ms = 30 seconds
- 700 cache hits × 1ms = 0.7 seconds
- Total: 30.7 seconds (69% improvement)
```

## Hit Rate Targets

### Target Hit Rates

| Data Type | Target Hit Rate | Typical Range |
|-----------|----------------|---------------|
| Static data (areas, zones) | >95% | 90-99% |
| Stable data (automations, scripts) | >85% | 80-95% |
| Semi-dynamic data (entity states) | >70% | 60-85% |
| **Overall** | **>75%** | **70-90%** |

### Monitoring Hit Rate

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
hit_rate = stats["statistics"]["hit_rate"]
print(f"Hit rate: {hit_rate:.2%}")

if hit_rate < 0.70:
    print("Warning: Hit rate below target (70%)")
```

### Improving Hit Rate

1. **Increase TTL** for stable data
2. **Reduce invalidation** frequency
3. **Optimize cache keys** to avoid unnecessary misses
4. **Review cache invalidation patterns**

## Memory/Disk Usage Guidelines

### Memory Backend

**Memory Usage:**
- **Per entry**: ~1-5 KB (depending on data size)
- **1000 entries**: ~1-5 MB
- **10,000 entries**: ~10-50 MB

**Guidelines:**
- **Development**: 1000 entries (default)
- **Production**: 10,000 entries (adjust based on available memory)
- **Maximum**: Set `HASS_MCP_CACHE_MAX_SIZE` based on available memory

**Configuration:**
```bash
export HASS_MCP_CACHE_MAX_SIZE=10000
```

### Redis Backend

**Memory Usage:**
- **Per entry**: ~1-5 KB (depending on data size)
- **1000 entries**: ~1-5 MB
- **10,000 entries**: ~10-50 MB

**Guidelines:**
- **Development**: 1000 entries
- **Production**: 10,000+ entries (Redis can handle much more)
- **Maximum**: Limited by Redis server memory

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379/0
```

### File Backend

**Disk Usage:**
- **Per entry**: ~2-10 KB (including metadata)
- **1000 entries**: ~2-10 MB
- **10,000 entries**: ~20-100 MB

**Guidelines:**
- **Development**: 1000 entries
- **Production**: 10,000+ entries (limited by disk space)
- **Maximum**: Limited by available disk space

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=/var/cache/hass-mcp
```

## Backend Selection Based on Use Case

### Development Environment

**Recommended**: Memory Backend

**Reasons:**
- Fastest performance
- No additional setup
- No persistence needed
- Simple configuration

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=memory
export HASS_MCP_CACHE_MAX_SIZE=1000
```

### Single Instance Production

**Recommended**: File Backend or Memory Backend

**File Backend** (if persistence needed):
- Cache survives restarts
- No external dependencies
- Moderate performance

**Memory Backend** (if persistence not needed):
- Fastest performance
- Simple setup
- Cache lost on restart

**Configuration (File):**
```bash
export HASS_MCP_CACHE_BACKEND=file
export HASS_MCP_CACHE_DIR=/var/cache/hass-mcp
export HASS_MCP_CACHE_MAX_SIZE=10000
```

### Multiple Instance Production

**Recommended**: Redis Backend

**Reasons:**
- Shared cache across instances
- Cache persists across restarts
- Scalable for high traffic
- Production-ready

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://redis.example.com:6379/0
export HASS_MCP_CACHE_MAX_SIZE=10000
```

### High-Traffic Production

**Recommended**: Redis Backend with Connection Pooling

**Reasons:**
- Best performance for high traffic
- Shared cache across instances
- Automatic connection pooling
- Scalable architecture

**Configuration:**
```bash
export HASS_MCP_CACHE_BACKEND=redis
export HASS_MCP_CACHE_REDIS_URL=redis://redis.example.com:6379/0
export HASS_MCP_CACHE_MAX_SIZE=50000
```

## Performance Optimization Tips

### 1. Use Lean Format

Use `lean=True` for entity lists to reduce cache size:

```python
# Smaller cache entry
entities = await get_entities(lean=True)

# Larger cache entry
entities = await get_entities(lean=False)
```

### 2. Optimize TTL Values

Adjust TTL values based on data volatility:

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
    }
  }
}
```

### 3. Reduce Cache Invalidation

Minimize unnecessary cache invalidation:

```python
# Only invalidate when operation succeeds
@invalidate_cache(
    pattern="entities:*",
    condition=lambda args, kwargs, result: result.get("status") == "success"
)
async def update_entity(entity_id: str, state: dict):
    ...
```

### 4. Use Appropriate Backend

Choose backend based on use case:

- **Memory**: Development, single instance
- **Redis**: Production, multiple instances
- **File**: Single instance, persistence needed

### 5. Monitor Performance

Regularly monitor cache performance:

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
print(f"Time saved: {stats['performance']['time_saved_ms']}ms")
```

## Performance Benchmarks

### Cache Hit Performance

| Backend | Average Time | P95 Time | P99 Time |
|---------|--------------|----------|----------|
| Memory | <1ms | <2ms | <5ms |
| Redis (local) | <5ms | <10ms | <20ms |
| Redis (remote) | <20ms | <50ms | <100ms |
| File | <10ms | <20ms | <50ms |

### Cache Miss Performance

| Backend | Average Time | P95 Time | P99 Time |
|---------|--------------|----------|----------|
| Memory | 50-200ms | 100-300ms | 200-500ms |
| Redis | 50-200ms | 100-300ms | 200-500ms |
| File | 50-200ms | 100-300ms | 200-500ms |

*Note: Cache miss time includes API call time to Home Assistant*

## Performance Monitoring

### Key Metrics

1. **Hit Rate**: Percentage of cache hits (target: >75%)
2. **Time Saved**: Total time saved by caching
3. **Average API Call Time**: Average time for API calls
4. **Average Cache Time**: Average time for cache operations
5. **Cache Size**: Number of cache entries

### Monitoring Tools

```python
from app.api.system import get_cache_statistics

stats = await get_cache_statistics()

# Overall statistics
print(f"Hit rate: {stats['statistics']['hit_rate']:.2%}")
print(f"Time saved: {stats['performance']['time_saved_ms']}ms")

# Per-endpoint statistics
for endpoint, endpoint_stats in stats['per_endpoint'].items():
    print(f"{endpoint}: {endpoint_stats['hit_rate']:.2%}")
```

## Performance Troubleshooting

### Low Hit Rate

**Symptoms**: Hit rate <70%

**Solutions**:
1. Increase TTL values for stable data
2. Reduce cache invalidation frequency
3. Review cache key generation
4. Check for parameter variations

### High Memory Usage

**Symptoms**: Memory usage is high

**Solutions**:
1. Reduce `HASS_MCP_CACHE_MAX_SIZE`
2. Use lean format for entity lists
3. Switch to Redis or file backend
4. Clear cache periodically

### Slow Cache Operations

**Symptoms**: Cache operations are slow

**Solutions**:
1. Check backend performance
2. Review network latency (Redis)
3. Check disk I/O (file backend)
4. Monitor backend health

## Best Practices

1. **Monitor hit rate**: Aim for >75% hit rate
2. **Optimize TTL**: Adjust TTL based on data volatility
3. **Use appropriate backend**: Choose based on use case
4. **Monitor performance**: Regularly check cache statistics
5. **Optimize cache keys**: Ensure consistent key generation
6. **Reduce invalidation**: Minimize unnecessary cache invalidation

## Additional Resources

- [Architecture Documentation](architecture.md)
- [Configuration Guide](configuration.md)
- [User Guide](user-guide.md)
- [Troubleshooting Guide](troubleshooting.md)
