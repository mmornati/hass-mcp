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

2. **Configure Claude Desktop or Cursor:**

   Open your MCP client settings (Claude Desktop: Developer → Edit Config, or Cursor: Settings → MCP) and add:

   #### Basic Configuration

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

   #### Recommended Configuration with File Cache and Vector DB

   For persistent cache and vector DB data, mount volumes to your home directory. **Important**: Docker doesn't expand `~`, so you must use the full path.

   **macOS/Linux:**
   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-e", "HA_URL",
           "-e", "HA_TOKEN",
           "-e", "HASS_MCP_CACHE_BACKEND",
           "-e", "HASS_MCP_CACHE_DIR",
           "-e", "HASS_MCP_VECTOR_DB_ENABLED",
           "-e", "HASS_MCP_VECTOR_DB_BACKEND",
           "-e", "HASS_MCP_VECTOR_DB_PATH",
           "-v", "/Users/YOUR_USERNAME/.hass-mcp/cache:/app/.cache",
           "-v", "/Users/YOUR_USERNAME/.hass-mcp/vectordb:/app/.vectordb",
           "mmornati/hass-mcp:latest"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN",
           "HASS_MCP_CACHE_BACKEND": "file",
           "HASS_MCP_CACHE_DIR": "/app/.cache",
           "HASS_MCP_VECTOR_DB_ENABLED": "true",
           "HASS_MCP_VECTOR_DB_BACKEND": "chroma",
           "HASS_MCP_VECTOR_DB_PATH": "/app/.vectordb"
         }
       }
     }
   }
   ```

   **Windows:**
   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-e", "HA_URL",
           "-e", "HA_TOKEN",
           "-e", "HASS_MCP_CACHE_BACKEND",
           "-e", "HASS_MCP_CACHE_DIR",
           "-e", "HASS_MCP_VECTOR_DB_ENABLED",
           "-e", "HASS_MCP_VECTOR_DB_BACKEND",
           "-e", "HASS_MCP_VECTOR_DB_PATH",
           "-v", "C:\\Users\\YOUR_USERNAME\\.hass-mcp\\cache:/app/.cache",
           "-v", "C:\\Users\\YOUR_USERNAME\\.hass-mcp\\vectordb:/app/.vectordb",
           "mmornati/hass-mcp:latest"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN",
           "HASS_MCP_CACHE_BACKEND": "file",
           "HASS_MCP_CACHE_DIR": "/app/.cache",
           "HASS_MCP_VECTOR_DB_ENABLED": "true",
           "HASS_MCP_VECTOR_DB_BACKEND": "chroma",
           "HASS_MCP_VECTOR_DB_PATH": "/app/.vectordb"
         }
       }
     }
   }
   ```

   **Linux:**
   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-e", "HA_URL",
           "-e", "HA_TOKEN",
           "-e", "HASS_MCP_CACHE_BACKEND",
           "-e", "HASS_MCP_CACHE_DIR",
           "-e", "HASS_MCP_VECTOR_DB_ENABLED",
           "-e", "HASS_MCP_VECTOR_DB_BACKEND",
           "-e", "HASS_MCP_VECTOR_DB_PATH",
           "-v", "/home/YOUR_USERNAME/.hass-mcp/cache:/app/.cache",
           "-v", "/home/YOUR_USERNAME/.hass-mcp/vectordb:/app/.vectordb",
           "mmornati/hass-mcp:latest"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN",
           "HASS_MCP_CACHE_BACKEND": "file",
           "HASS_MCP_CACHE_DIR": "/app/.cache",
           "HASS_MCP_VECTOR_DB_ENABLED": "true",
           "HASS_MCP_VECTOR_DB_BACKEND": "chroma",
           "HASS_MCP_VECTOR_DB_PATH": "/app/.vectordb"
         }
       }
     }
   }
   ```

   #### Configuration Explanation

   - **File Cache**: `HASS_MCP_CACHE_BACKEND=file` enables persistent file-based caching
   - **Cache Directory**: `HASS_MCP_CACHE_DIR=/app/.cache` sets the cache location (mounted to `~/.hass-mcp/cache`)
   - **Vector DB**: `HASS_MCP_VECTOR_DB_ENABLED=true` enables semantic search features
   - **Chroma Backend**: `HASS_MCP_VECTOR_DB_BACKEND=chroma` uses ChromaDB for vector storage
   - **Vector DB Path**: `HASS_MCP_VECTOR_DB_PATH=/app/.vectordb` sets the vector DB location (mounted to `~/.hass-mcp/vectordb`)

   The volume mounts (`-v`) ensure that:
   - Cache data persists between container restarts
   - Vector DB embeddings are preserved
   - Data is stored in your home directory for easy access

3. **Create Directories (Optional but Recommended):**

   Before first run, create the directories to ensure proper permissions:

   ```bash
   # macOS/Linux
   mkdir -p ~/.hass-mcp/cache ~/.hass-mcp/vectordb

   # Windows (PowerShell)
   New-Item -ItemType Directory -Path "$env:USERPROFILE\.hass-mcp\cache" -Force
   New-Item -ItemType Directory -Path "$env:USERPROFILE\.hass-mcp\vectordb" -Force
   ```

4. **Update Configuration:**
   - Replace `YOUR_LONG_LIVED_TOKEN` with your actual token
   - Replace `YOUR_USERNAME` with your actual username (for volume paths)
   - Update `HA_URL` based on your setup:
     - **Same machine (Docker Desktop)**: `http://host.docker.internal:8123`
     - **Local network**: `http://homeassistant.local:8123` or `http://192.168.1.100:8123`
     - **Remote**: `https://your-ha-instance.duckdns.org:8123`

5. **Restart your MCP client** (Claude Desktop or Cursor)

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
