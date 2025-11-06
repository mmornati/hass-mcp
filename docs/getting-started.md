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

#### Available Docker Images

Hass-MCP provides two Docker images:

1. **Base Image** (`mmornati/hass-mcp:latest` or `mmornati/hass-mcp:latest-vectordb`)
   - **Size**: ~200-300MB (base) or ~2GB (with VectorDB)
   - **VectorDB**: Disabled by default (base) or enabled (vectordb tag)
   - **Use Case**: Base image for minimal deployments or when using external VectorDB server

2. **VectorDB Image** (`mmornati/hass-mcp:latest-vectordb`)
   - **Size**: ~2GB
   - **VectorDB**: Enabled by default with CPU-only PyTorch
   - **Use Case**: Full semantic search capabilities with built-in embeddings

**Choose based on your needs:**
- **Base image** (`latest`): Smaller, faster pulls, no ML dependencies. Use if you don't need semantic search or want to use an external VectorDB server.
- **VectorDB image** (`latest-vectordb`): Full semantic search with built-in embeddings. Use if you want semantic search without external dependencies.

1. **Pull the Docker image:**
   ```bash
   # Base image (without VectorDB)
   docker pull mmornati/hass-mcp:latest

   # Or VectorDB image (with semantic search)
   docker pull mmornati/hass-mcp:latest-vectordb
   ```

2. **Configure Claude Desktop or Cursor:**

   Open your MCP client settings (Claude Desktop: Developer → Edit Config, or Cursor: Settings → MCP) and add:

   #### Basic Configuration (Base Image - No VectorDB)

   This configuration uses the base image without VectorDB dependencies (~200-300MB):

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

   **Note**: VectorDB is disabled by default in the base image. Semantic search features will fall back to keyword search.

   #### Configuration with VectorDB (Built-in Semantic Search)

   This configuration uses the VectorDB image (`latest-vectordb`) with built-in semantic search capabilities:

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
           "mmornati/hass-mcp:latest-vectordb"
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
           "mmornati/hass-mcp:latest-vectordb"
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
           "mmornati/hass-mcp:latest-vectordb"
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

   #### Configuration with External VectorDB Server

   **Note**: External VectorDB backends (Qdrant, Weaviate, Pinecone) are planned but not yet implemented. This section shows the configuration for when they become available.

   If you're using a separate VectorDB server (e.g., Qdrant, Weaviate, Pinecone), use the base image and configure it to connect to your external server:

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
           "-e", "HASS_MCP_QDRANT_URL",
           "-e", "HASS_MCP_EMBEDDING_MODEL",
           "-e", "HASS_MCP_OPENAI_API_KEY",
           "-v", "/Users/YOUR_USERNAME/.hass-mcp/cache:/app/.cache",
           "mmornati/hass-mcp:latest"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN",
           "HASS_MCP_CACHE_BACKEND": "file",
           "HASS_MCP_CACHE_DIR": "/app/.cache",
           "HASS_MCP_VECTOR_DB_ENABLED": "true",
           "HASS_MCP_VECTOR_DB_BACKEND": "qdrant",
           "HASS_MCP_QDRANT_URL": "http://your-qdrant-server:6333",
           "HASS_MCP_EMBEDDING_MODEL": "openai",
           "HASS_MCP_OPENAI_API_KEY": "your-openai-api-key"
         }
       }
     }
   }
   ```

   **Supported External VectorDB Backends** (when implemented):
   - **Qdrant**: `HASS_MCP_VECTOR_DB_BACKEND=qdrant`, `HASS_MCP_QDRANT_URL=http://qdrant-server:6333`, `HASS_MCP_QDRANT_API_KEY=your-api-key` (optional)
   - **Weaviate**: `HASS_MCP_VECTOR_DB_BACKEND=weaviate`, `HASS_MCP_WEAVIATE_URL=http://weaviate-server:8080`, `HASS_MCP_WEAVIATE_API_KEY=your-api-key` (optional)
   - **Pinecone**: `HASS_MCP_VECTOR_DB_BACKEND=pinecone`, `HASS_MCP_PINECONE_API_KEY=your-api-key`, `HASS_MCP_PINECONE_ENVIRONMENT=us-east-1`

   **Note**: When using external VectorDB servers with the base image, you need embedding models. You can:
   - Use cloud embeddings (OpenAI, Cohere) with `HASS_MCP_EMBEDDING_MODEL=openai` or `cohere` (requires API keys)
   - Or use the VectorDB image (`latest-vectordb`) which includes sentence-transformers for local embeddings

   #### Configuration Explanation

   **Base Image (`latest`):**
   - **Size**: ~200-300MB (no ML dependencies)
   - **File Cache**: `HASS_MCP_CACHE_BACKEND=file` enables persistent file-based caching
   - **Cache Directory**: `HASS_MCP_CACHE_DIR=/app/.cache` sets the cache location (mounted to `~/.hass-mcp/cache`)
   - **Vector DB**: `HASS_MCP_VECTOR_DB_ENABLED=false` by default (can be enabled for external servers)
   - **Use Case**: Minimal deployments, external VectorDB servers, or when semantic search is not needed

   **VectorDB Image (`latest-vectordb`):**
   - **Size**: ~2GB (includes CPU-only PyTorch and sentence-transformers)
   - **File Cache**: Same as base image
   - **Vector DB**: `HASS_MCP_VECTOR_DB_ENABLED=true` by default
   - **Chroma Backend**: `HASS_MCP_VECTOR_DB_BACKEND=chroma` uses ChromaDB for vector storage
   - **Vector DB Path**: `HASS_MCP_VECTOR_DB_PATH=/app/.vectordb` sets the vector DB location (mounted to `~/.hass-mcp/vectordb`)
   - **Embeddings**: Includes sentence-transformers for local embeddings (no API keys needed)
   - **Use Case**: Full semantic search capabilities with built-in embeddings

   The volume mounts (`-v`) ensure that:
   - Cache data persists between container restarts
   - Vector DB embeddings are preserved (when using built-in ChromaDB)
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
