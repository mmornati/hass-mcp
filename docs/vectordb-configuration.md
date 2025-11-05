# Vector DB Configuration

Hass-MCP provides flexible configuration options for the vector database system, supporting both configuration files and environment variables.

## Configuration Sources

Configuration is loaded in the following order (later sources override earlier ones):

1. **Default Values** - Built-in defaults
2. **Configuration Files** - JSON or YAML files
3. **Environment Variables** - Override config files

## Configuration Files

### File Discovery

Configuration files are automatically discovered in these locations:

1. Current working directory
2. Home directory (`~`)
3. `HASS_MCP_CONFIG_DIR` environment variable
4. `/etc/hass-mcp`

### Supported File Names

- `vectordb.json`
- `vectordb.yaml`
- `vectordb.yml`
- `.vectordb.json`
- `.vectordb.yaml`

### JSON Configuration Format

```json
{
  "vector_db": {
    "backend": "chroma",
    "path": ".vectordb",
    "collection_name": "entities",
    "embeddings": {
      "model": "sentence-transformers",
      "model_name": "all-MiniLM-L6-v2",
      "dimensions": 384,
      "device": "cpu"
    },
    "indexing": {
      "batch_size": 100,
      "auto_index": false,
      "update_on_change": true
    },
    "search": {
      "default_limit": 10,
      "similarity_threshold": 0.7,
      "hybrid_search": false
    }
  }
}
```

### YAML Configuration Format

```yaml
vector_db:
  backend: chroma
  path: .vectordb
  collection_name: entities
  embeddings:
    model: sentence-transformers
    model_name: all-MiniLM-L6-v2
    dimensions: 384
    device: cpu
  indexing:
    batch_size: 100
    auto_index: false
    update_on_change: true
  search:
    default_limit: 10
    similarity_threshold: 0.7
    hybrid_search: false
```

### Nested Configuration Sections

The configuration supports nested sections for better organization:

- **`embeddings`**: Embedding model configuration
- **`indexing`**: Entity indexing configuration
- **`search`**: Search behavior configuration

## Environment Variables

Environment variables override configuration file values. All environment variables are optional if using configuration files.

### Backend Configuration

```bash
# Backend selection (default: chroma)
export HASS_MCP_VECTOR_DB_BACKEND=chroma  # Options: chroma, qdrant, weaviate, pinecone

# Enable/disable vector DB (default: true)
export HASS_MCP_VECTOR_DB_ENABLED=true

# Collection name (default: entities)
export HASS_MCP_VECTOR_DB_COLLECTION=entities
```

### Chroma Configuration

```bash
# Chroma database path (default: .vectordb)
export HASS_MCP_VECTOR_DB_PATH=.vectordb
```

### Qdrant Configuration

```bash
# Qdrant URL (default: http://localhost:6333)
export HASS_MCP_QDRANT_URL=http://localhost:6333

# Qdrant API key (optional)
export HASS_MCP_QDRANT_API_KEY=your_api_key
```

### Weaviate Configuration

```bash
# Weaviate URL (default: http://localhost:8080)
export HASS_MCP_WEAVIATE_URL=http://localhost:8080

# Weaviate API key (optional)
export HASS_MCP_WEAVIATE_API_KEY=your_api_key
```

### Pinecone Configuration

```bash
# Pinecone API key (required for Pinecone)
export HASS_MCP_PINECONE_API_KEY=your_api_key

# Pinecone environment (required for Pinecone)
export HASS_MCP_PINECONE_ENVIRONMENT=your_environment

# Pinecone index name (default: entities)
export HASS_MCP_PINECONE_INDEX_NAME=entities
```

### Embedding Model Configuration

#### sentence-transformers

```bash
# Embedding model type (default: sentence-transformers)
export HASS_MCP_EMBEDDING_MODEL=sentence-transformers

# Model name (default: all-MiniLM-L6-v2)
export HASS_MCP_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Embedding dimensions (default: 384)
export HASS_MCP_EMBEDDING_DIMENSIONS=384

# Device (default: cpu)
export HASS_MCP_EMBEDDING_DEVICE=cpu  # Options: cpu, gpu, cuda
```

#### OpenAI

```bash
# Embedding model type
export HASS_MCP_EMBEDDING_MODEL=openai

# OpenAI API key (required for OpenAI)
export HASS_MCP_OPENAI_API_KEY=sk-...

# OpenAI model name (default: text-embedding-3-small)
export HASS_MCP_OPENAI_MODEL=text-embedding-3-small

# Embedding dimensions (default: 1536)
export HASS_MCP_EMBEDDING_DIMENSIONS=1536
```

#### Cohere

```bash
# Embedding model type
export HASS_MCP_EMBEDDING_MODEL=cohere

# Cohere API key (required for Cohere)
export HASS_MCP_COHERE_API_KEY=your_api_key

# Cohere model name (default: embed-english-v3.0)
export HASS_MCP_COHERE_MODEL=embed-english-v3.0

# Embedding dimensions (default: 1024)
export HASS_MCP_EMBEDDING_DIMENSIONS=1024
```

### Performance Configuration

#### Indexing

```bash
# Batch size for indexing (default: 100)
export HASS_MCP_INDEXING_BATCH_SIZE=100

# Auto-index on startup (default: false)
export HASS_MCP_INDEXING_AUTO_INDEX=false

# Update index on entity changes (default: true)
export HASS_MCP_INDEXING_UPDATE_ON_CHANGE=true
```

#### Search

```bash
# Default search result limit (default: 10)
export HASS_MCP_SEARCH_DEFAULT_LIMIT=10

# Similarity threshold (default: 0.7)
export HASS_MCP_SEARCH_SIMILARITY_THRESHOLD=0.7

# Use hybrid search (default: false)
export HASS_MCP_SEARCH_HYBRID_SEARCH=false
```

## Configuration Validation

The configuration system validates settings to ensure they are correct:

```python
from app.core.vectordb.config import VectorDBConfig

config = VectorDBConfig()
is_valid, errors = config.validate()

if not is_valid:
    for error in errors:
        print(f"Configuration error: {error}")
```

### Validation Checks

The validation system checks:

1. **Backend Validity**: Ensures backend is one of: chroma, qdrant, weaviate, pinecone
2. **Embedding Model Validity**: Ensures model is one of: sentence-transformers, openai, cohere
3. **Required API Keys**: Verifies API keys are provided for cloud services
4. **Performance Settings**: Validates batch sizes, limits, and thresholds are within valid ranges
5. **Device Configuration**: Ensures device is one of: cpu, gpu, cuda

### Validation Errors

Common validation errors:

- **Invalid backend**: Backend not in supported list
- **Invalid embedding model**: Model not in supported list
- **Missing API key**: Required API key not provided (Pinecone, OpenAI, Cohere)
- **Missing environment**: Pinecone environment not provided
- **Invalid batch size**: Batch size must be at least 1
- **Invalid search limit**: Search limit must be at least 1
- **Invalid similarity threshold**: Threshold must be between 0.0 and 1.0
- **Invalid embedding dimensions**: Dimensions must be at least 1
- **Invalid device**: Device must be cpu, gpu, or cuda

## Configuration Priority

Configuration is loaded in this order (later overrides earlier):

1. **Defaults**: Built-in default values
2. **Config File**: Values from JSON/YAML configuration file
3. **Environment Variables**: Values from environment variables

## Example Configurations

### Development (Local Chroma)

```json
{
  "vector_db": {
    "backend": "chroma",
    "path": ".vectordb",
    "embeddings": {
      "model": "sentence-transformers",
      "model_name": "all-MiniLM-L6-v2"
    }
  }
}
```

### Production (Qdrant with OpenAI)

```json
{
  "vector_db": {
    "backend": "qdrant",
    "qdrant_url": "http://qdrant:6333",
    "qdrant_api_key": "your_api_key",
    "embeddings": {
      "model": "openai",
      "model_name": "text-embedding-3-small"
    },
    "indexing": {
      "batch_size": 500,
      "auto_index": true
    },
    "search": {
      "default_limit": 20,
      "similarity_threshold": 0.8
    }
  }
}
```

### Cloud (Pinecone with Cohere)

```json
{
  "vector_db": {
    "backend": "pinecone",
    "pinecone_api_key": "your_api_key",
    "pinecone_environment": "us-east-1",
    "pinecone_index_name": "entities",
    "embeddings": {
      "model": "cohere",
      "model_name": "embed-english-v3.0"
    },
    "indexing": {
      "batch_size": 1000
    }
  }
}
```

## Best Practices

1. **Use Configuration Files**: For production deployments, use configuration files rather than environment variables
2. **Version Control**: Keep configuration files in version control (excluding sensitive keys)
3. **Environment Variables for Secrets**: Use environment variables for API keys and sensitive information
4. **Validate Configuration**: Always validate configuration on startup
5. **Separate Configs**: Use different configuration files for development, staging, and production
6. **Documentation**: Document your configuration choices in comments or documentation

## Troubleshooting

### Configuration File Not Found

**Problem**: Configuration file not being loaded

**Solutions**:
- Check file is in one of the discovery locations
- Verify file name matches supported patterns
- Check file permissions
- Use explicit path: `VectorDBConfig(config_file="/path/to/config.json")`

### Environment Variables Not Overriding

**Problem**: Environment variables not taking effect

**Solutions**:
- Verify environment variable names are correct
- Check variable values are set before importing/configuring
- Ensure variables are exported in shell

### Validation Errors

**Problem**: Configuration validation failing

**Solutions**:
- Review validation error messages
- Check required API keys are set
- Verify backend and model names are correct
- Check performance settings are within valid ranges

### Configuration File Parse Errors

**Problem**: JSON/YAML parsing errors

**Solutions**:
- Validate JSON/YAML syntax
- Check for typos in configuration keys
- Verify nested structure is correct
- Use a JSON/YAML validator

## Related Features

- **US-VD-001**: Vector DB Core Infrastructure
- **US-VD-002**: Entity Embedding and Indexing

## See Also

- [Vector DB Overview](vectordb.md)
- [Entity Indexing](vectordb-indexing.md)
- [Best Practices](best-practices.md)
