# Getting Started

This guide will help you set up and configure Hass-MCP to work with Claude Desktop or other MCP-compatible clients.

## Prerequisites

Before you begin, make sure you have:

1. **Home Assistant** instance running (local or remote)
   - Home Assistant Core, OS, or Supervised installation
   - Accessible via HTTP/HTTPS
   - API enabled (enabled by default)

2. **Long-Lived Access Token**
   - Go to Home Assistant → Profile → Long-lived access tokens
   - Click "Create Token"
   - Give it a descriptive name (e.g., "Hass-MCP")
   - Copy the token (you won't be able to see it again!)

3. **Claude Desktop** or another MCP-compatible client

## Installation Methods

### Docker (Recommended)

Docker is the easiest way to run Hass-MCP and is recommended for most users.

1. **Pull the Docker image:**
   ```bash
   docker pull mmornati/hass-mcp:latest
   ```

2. **Configure Claude Desktop:**

   Open Claude Desktop settings (Developer → Edit Config) and add:

   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-e", "HA_URL",
           "-e", "HA_TOKEN",
           "mmornati/hass-mcp:latest"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN"
         }
       }
     }
   }
   ```

3. **Update Configuration:**
   - Replace `YOUR_LONG_LIVED_TOKEN` with your actual token
   - Update `HA_URL` based on your setup:
     - **Same machine (Docker Desktop)**: `http://host.docker.internal:8123`
     - **Local network**: `http://homeassistant.local:8123` or `http://192.168.1.100:8123`
     - **Remote**: `https://your-ha-instance.duckdns.org:8123`

4. **Restart Claude Desktop**

### Python/uv Installation

For users who prefer Python or need more control:

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Configure Claude Desktop:**

   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "uvx",
         "args": ["-m", "hass-mcp"],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN"
         }
       }
     }
   }
   ```

### Local Development

If you're developing or want to run from source:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mmornati/hass-mcp.git
   cd hass-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Claude Desktop:**

   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "uv",
         "args": ["run", "-m", "app"],
         "cwd": "/path/to/hass-mcp",
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN"
         }
       }
     }
   }
   ```

## Verifying Installation

Once configured, verify the connection by asking Claude:

> "List all the lights in my Home Assistant instance"

If the MCP server is working correctly, Claude will use the `list_entities` tool and display your lights.

## Troubleshooting

### Connection Issues

**Problem**: Claude can't connect to Home Assistant

**Solutions**:
- Check that `HA_URL` is correct and accessible
- Verify your `HA_TOKEN` is valid and not expired
- Ensure Home Assistant is running and API is enabled
- Check network connectivity between the MCP server and Home Assistant
- For Docker, ensure the network configuration allows access

### Authentication Errors

**Problem**: "401 Unauthorized" or "403 Forbidden" errors

**Solutions**:
- Verify your `HA_TOKEN` is correct
- Check that the token hasn't been revoked
- Ensure the token has necessary permissions
- Try creating a new token

### Tools Not Appearing

**Problem**: Hass-MCP tools don't appear in Claude

**Solutions**:
- Restart Claude Desktop after configuration changes
- Check the Claude Desktop console for errors
- Verify the MCP server is running (check Docker logs if using Docker)
- Ensure the configuration JSON is valid

### Docker Network Issues

**Problem**: Docker container can't reach Home Assistant

**Solutions**:
- Use `host.docker.internal` for Mac/Windows Docker Desktop
- Use the actual IP address instead of hostname
- Add `--network host` to Docker args (Linux only)
- Check Docker network configuration

## Next Steps

Now that you have Hass-MCP set up, explore the available tools:

- [Entities Tools](entities.md) - Query and control devices
- [Automations Tools](automations.md) - Manage automations
- [System Tools](system.md) - Monitor system health

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Browse the full documentation
- **Home Assistant**: [Official API Documentation](https://www.home-assistant.io/integrations/api/)
