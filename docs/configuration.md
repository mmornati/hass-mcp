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
