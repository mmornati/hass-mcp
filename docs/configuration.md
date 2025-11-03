# Configuration

This page covers advanced configuration options for Hass-MCP.

## Environment Variables

Hass-MCP uses the following environment variables:

### Required Variables

- **`HA_URL`**: Home Assistant URL
  - Format: `http://hostname:port` or `https://hostname:port`
  - Examples:
    - `http://homeassistant.local:8123`
    - `https://ha.example.com:8123`
    - `http://192.168.1.100:8123`

- **`HA_TOKEN`**: Long-lived access token
  - Create in Home Assistant → Profile → Long-lived access tokens
  - Format: Long alphanumeric string

### Optional Variables

- **`HA_TIMEOUT`**: HTTP request timeout in seconds (default: 30)
- **`LOG_LEVEL`**: Logging level (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Cache Configuration Variables

- **`HASS_MCP_CACHE_ENABLED`**: Enable/disable caching (default: `true`)
  - Options: `true`, `false`, `1`, `0`, `yes`, `no`
- **`HASS_MCP_CACHE_BACKEND`**: Cache backend type (default: `memory`)
  - Options: `memory`, `redis`, `file`
- **`HASS_MCP_CACHE_DEFAULT_TTL`**: Default cache TTL in seconds (default: `300`)
- **`HASS_MCP_CACHE_MAX_SIZE`**: Maximum cache size (default: `1000`)
- **`HASS_MCP_CACHE_REDIS_URL`**: Redis URL for Redis backend (optional)
  - Example: `redis://localhost:6379/0`
- **`HASS_MCP_CACHE_DIR`**: Cache directory for file backend (default: `.cache`)
- **`HASS_MCP_CACHE_CONFIG_FILE`**: Path to cache configuration file (optional)
  - Supports JSON and YAML formats
  - Example: `/path/to/cache_config.json`

## Configuration Examples

### Basic Configuration

```json
{
  "mcpServers": {
    "hass-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "HA_URL", "-e", "HA_TOKEN", "mmornati/hass-mcp"],
      "env": {
        "HA_URL": "http://homeassistant.local:8123",
        "HA_TOKEN": "your_token_here"
      }
    }
  }
}
```

### With Custom Timeout

```json
{
  "mcpServers": {
    "hass-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "HA_URL", "-e", "HA_TOKEN", "-e", "HA_TIMEOUT", "mmornati/hass-mcp"],
      "env": {
        "HA_URL": "http://homeassistant.local:8123",
        "HA_TOKEN": "your_token_here",
        "HA_TIMEOUT": "60"
      }
    }
  }
}
```

### With Debug Logging

```json
{
  "mcpServers": {
    "hass-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "HA_URL", "-e", "HA_TOKEN", "-e", "LOG_LEVEL", "mmornati/hass-mcp"],
      "env": {
        "HA_URL": "http://homeassistant.local:8123",
        "HA_TOKEN": "your_token_here",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Docker with Network Configuration

For Docker Desktop on Mac/Windows:

```json
{
  "mcpServers": {
    "hass-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "HA_URL",
        "-e", "HA_TOKEN",
        "--network", "host",
        "mmornati/hass-mcp"
      ],
      "env": {
        "HA_URL": "http://localhost:8123",
        "HA_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Network Configuration

### Local Network Setup

If Home Assistant is on the same local network:

- Use the Home Assistant hostname: `http://homeassistant.local:8123`
- Or use the IP address: `http://192.168.1.100:8123`

### Docker Desktop (Mac/Windows)

When running Docker Desktop:

- Use `http://host.docker.internal:8123` to access host services
- Or use the actual IP address of your host machine

### Remote Access

For remote Home Assistant instances:

- Use HTTPS: `https://ha.example.com:8123`
- Ensure proper SSL certificates
- May require firewall/port forwarding configuration

## Security Considerations

1. **Token Security**
   - Never commit tokens to version control
   - Use environment variables or secure configuration management
   - Rotate tokens regularly

2. **Network Security**
   - Use HTTPS for remote access
   - Use strong passwords and tokens
   - Consider VPN for remote access

3. **Permissions**
   - Grant only necessary permissions when creating tokens
   - Review token permissions regularly

## Cache Configuration

The caching system reduces API calls to Home Assistant by caching relatively static data. Configuration can be managed via environment variables or a configuration file.

### Environment Variables

All cache configuration can be set via environment variables (highest priority):

```bash
export HASS_MCP_CACHE_ENABLED=true
export HASS_MCP_CACHE_BACKEND=memory
export HASS_MCP_CACHE_DEFAULT_TTL=300
export HASS_MCP_CACHE_MAX_SIZE=1000
```

### Configuration File

You can also use a configuration file (JSON or YAML) for more complex setups:

**JSON Example** (`cache_config.json`):
```json
{
  "enabled": true,
  "backend": "memory",
  "default_ttl": 300,
  "max_size": 1000,
  "endpoints": {
    "entities": {"ttl": 1800},
    "automations": {"ttl": 3600},
    "areas": {"ttl": 3600}
  }
}
```

**YAML Example** (`cache_config.yaml`):
```yaml
enabled: true
backend: memory
default_ttl: 300
max_size: 1000
endpoints:
  entities:
    ttl: 1800
  automations:
    ttl: 3600
  areas:
    ttl: 3600
```

**Simple Format** (integer TTL):
```json
{
  "endpoints": {
    "entities": 1800,
    "automations": 3600
  }
}
```

### Per-Endpoint TTL Configuration

You can configure different TTL values for different endpoints:

```json
{
  "endpoints": {
    "entities": {"ttl": 60},           // 1 minute for entity states
    "entities.list": {"ttl": 1800},    // 30 minutes for entity lists
    "automations": {"ttl": 3600},      // 1 hour for automations
    "areas": {"ttl": 3600}             // 1 hour for areas
  }
}
```

### Configuration Priority

Configuration is loaded in the following order (highest to lowest priority):

1. **Environment Variables** - Highest priority
2. **Configuration File** - Medium priority
3. **Default Values** - Lowest priority

### Runtime Configuration Management

You can manage cache configuration at runtime using the API:

- **Get configuration**: `get_cache_configuration()`
- **Update endpoint TTL**: `update_cache_endpoint_ttl(domain, ttl, operation)`
- **Reload configuration**: `reload_cache_config()`

### Cache Backends

The cache system supports multiple backends:

- **`memory`**: In-memory cache (default, fastest, no persistence)
- **`redis`**: Redis backend (distributed, persistent, requires Redis)
- **`file`**: File-based cache (persistent, slower, no external dependencies)

### Recommended TTL Values

Based on data volatility:

- **Very Long TTL (1 hour)**: Areas, zones, blueprints, system config, HA version
- **Long TTL (30 minutes)**: Entities metadata, automations, scripts, scenes, devices, helpers, tags
- **Medium TTL (5 minutes)**: Integrations, device statistics, domain summaries
- **Short TTL (1 minute)**: Entity states, entity lists with state info
- **No Caching**: Logbook, history, statistics, events, templates, notifications

## Troubleshooting Configuration

### Invalid URL Format

**Error**: "Invalid URL format"

**Solution**: Ensure URL includes protocol (`http://` or `https://`) and port

### Connection Timeout

**Error**: "Connection timeout"

**Solution**:
- Increase `HA_TIMEOUT` value
- Check network connectivity
- Verify Home Assistant is accessible

### Authentication Failed

**Error**: "401 Unauthorized"

**Solution**:
- Verify `HA_TOKEN` is correct
- Check token hasn't been revoked
- Create a new token if needed

### Cache Configuration Issues

**Error**: "Cache config file not found"

**Solution**:
- Verify the path in `HASS_MCP_CACHE_CONFIG_FILE` is correct
- Check file permissions
- Use absolute paths for clarity

**Error**: "Invalid cache configuration"

**Solution**:
- Verify JSON/YAML syntax is correct
- Check that TTL values are positive integers
- Ensure backend type is one of: `memory`, `redis`, `file`
