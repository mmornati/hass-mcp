# Vector DB Core Infrastructure

Hass-MCP includes a comprehensive vector database infrastructure for semantic search capabilities. This enables natural language understanding and semantic entity discovery.

## Overview

The Vector DB infrastructure provides:

- **Multiple Backend Support**: Chroma, Qdrant, Weaviate, Pinecone
- **Multiple Embedding Models**: sentence-transformers, OpenAI, Cohere
- **Unified Interface**: Single API for all vector operations
- **Graceful Degradation**: Fallback to keyword search if vector DB unavailable

## Configuration

### Environment Variables

#### Backend Selection

```bash
# Vector DB backend (default: chroma)
export HASS_MCP_VECTOR_DB_BACKEND=chroma  # Options: chroma, qdrant, weaviate, pinecone

# Enable/disable vector DB (default: true)
export HASS_MCP_VECTOR_DB_ENABLED=true
```

#### Embedding Model Configuration

```bash
# Embedding model type (default: sentence-transformers)
export HASS_MCP_EMBEDDING_MODEL=sentence-transformers  # Options: sentence-transformers, openai, cohere

# Model name for sentence-transformers (default: all-MiniLM-L6-v2)
export HASS_MCP_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Embedding dimensions (default: 384)
export HASS_MCP_EMBEDDING_DIMENSIONS=384
```

#### Chroma Configuration

```bash
# Chroma database path (default: .vectordb)
export HASS_MCP_VECTOR_DB_PATH=.vectordb
```

#### Qdrant Configuration

```bash
# Qdrant URL (default: http://localhost:6333)
export HASS_MCP_QDRANT_URL=http://localhost:6333

# Qdrant API key (optional)
export HASS_MCP_QDRANT_API_KEY=your_api_key
```

#### Weaviate Configuration

```bash
# Weaviate URL (default: http://localhost:8080)
export HASS_MCP_WEAVIATE_URL=http://localhost:8080

# Weaviate API key (optional)
export HASS_MCP_WEAVIATE_API_KEY=your_api_key
```

#### Pinecone Configuration

```bash
# Pinecone API key (required for Pinecone)
export HASS_MCP_PINECONE_API_KEY=your_api_key

# Pinecone environment (required for Pinecone)
export HASS_MCP_PINECONE_ENVIRONMENT=your_environment
```

#### OpenAI Configuration

```bash
# OpenAI API key (required for OpenAI embeddings)
export HASS_MCP_OPENAI_API_KEY=sk-...
```

#### Cohere Configuration

```bash
# Cohere API key (required for Cohere embeddings)
export HASS_MCP_COHERE_API_KEY=your_api_key
```

## Installation

### Basic Setup (Chroma + sentence-transformers)

```bash
# Install with basic vector DB support
uv pip install hass-mcp[vectordb]
```

### OpenAI Embeddings

```bash
# Install with OpenAI embeddings support
uv pip install hass-mcp[vectordb-openai]
```

### Cohere Embeddings

```bash
# Install with Cohere embeddings support
uv pip install hass-mcp[vectordb-cohere]
```

### All Embeddings

```bash
# Install with all embedding model support
uv pip install hass-mcp[vectordb-all]
```

## Usage

### Basic Usage

```python
from app.core.vectordb import get_vectordb_manager

# Get the vector DB manager
manager = get_vectordb_manager()

# Initialize (happens automatically on first use)
await manager.initialize()

# Add vectors to a collection
await manager.add_vectors(
    collection_name="entities",
    texts=["Living room light", "Kitchen temperature sensor"],
    ids=["light.living_room", "sensor.kitchen_temperature"],
    metadata=[
        {"domain": "light", "area": "living_room"},
        {"domain": "sensor", "area": "kitchen"},
    ],
)

# Search for similar entities
results = await manager.search_vectors(
    collection_name="entities",
    query_text="light in the living room",
    limit=5,
)
```

### Collection Management

```python
# Create a collection
await manager.create_collection(
    collection_name="entities",
    metadata={"description": "Home Assistant entities"},
)

# Check if collection exists
exists = await manager.collection_exists("entities")

# Get collection statistics
stats = await manager.get_collection_stats("entities")
# Returns: {"count": 10, "dimensions": 384, "metadata": {...}}

# Delete a collection
await manager.delete_collection("entities")
```

### Vector Operations

```python
# Add vectors
await manager.add_vectors(
    collection_name="entities",
    texts=["text1", "text2"],
    ids=["id1", "id2"],
    metadata=[{"key": "value1"}, {"key": "value2"}],
)

# Update vectors
await manager.update_vectors(
    collection_name="entities",
    texts=["updated_text1"],
    ids=["id1"],
    metadata=[{"key": "updated_value"}],
)

# Delete vectors
await manager.delete_vectors(
    collection_name="entities",
    ids=["id1", "id2"],
)

# Search vectors
results = await manager.search_vectors(
    collection_name="entities",
    query_text="query text",
    limit=10,
    filter_metadata={"domain": "light"},
)
```

## Backend Comparison

| Backend | Type | Pros | Cons |
|---------|------|------|------|
| **Chroma** | Local | Simple, no setup, fast | Limited scalability |
| **Qdrant** | Local/Cloud | Fast, scalable, good Python support | Requires setup |
| **Weaviate** | Local/Cloud | GraphQL, rich features | More complex |
| **Pinecone** | Cloud | Managed, scalable | Requires API key, cost |

## Embedding Model Comparison

| Model | Type | Dimensions | Pros | Cons |
|-------|------|------------|------|------|
| **sentence-transformers/all-MiniLM-L6-v2** | Local | 384 | Free, fast, good quality | Local resources |
| **OpenAI text-embedding-3-small** | Cloud | 1536 | High quality | API cost |
| **Cohere embed-english-v3.0** | Cloud | 1024 | Fast, good quality | API cost |

## Architecture

```
┌─────────────────────────────────────────┐
│         MCP Server / API Layer          │
│  ┌───────────────────────────────────┐ │
│  │    Semantic Search Function        │ │
│  │    - Query embedding               │ │
│  │    - Vector search                 │ │
│  │    - Result ranking                 │ │
│  └───────────────────────────────────┘ │
│                  │                       │
│                  ▼                       │
│  ┌───────────────────────────────────┐ │
│  │       VectorDBManager               │ │
│  │  - Connection management           │ │
│  │  - Embedding model                 │ │
│  │  - Vector operations               │ │
│  └───────────────────────────────────┘ │
│                  │                       │
│                  ▼                       │
│  ┌───────────────────────────────────┐ │
│  │       Vector DB Backend            │ │
│  │  - Chroma / Qdrant / Weaviate      │ │
│  │  - Vector storage                  │ │
│  │  - Similarity search               │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Error Handling

The vector DB infrastructure includes graceful error handling:

- **Connection Errors**: Automatically retries with exponential backoff
- **Embedding Errors**: Falls back to keyword search if embedding fails
- **Backend Unavailable**: Falls back to keyword search if backend unavailable
- **Health Checks**: Regular health checks ensure backend availability

## Best Practices

1. **Use Chroma for Development**: Chroma requires no setup and is perfect for development
2. **Use Qdrant for Production**: Qdrant offers better scalability for production deployments
3. **Choose Embedding Model Based on Use Case**:
   - Use sentence-transformers for local, free embeddings
   - Use OpenAI for highest quality embeddings
   - Use Cohere for fast, good quality embeddings
4. **Collection Organization**: Create separate collections for different entity types
5. **Metadata Filtering**: Use metadata filters to improve search relevance
6. **Batch Operations**: Use batch operations for better performance when adding many vectors

## Troubleshooting

### Vector DB Not Initializing

**Problem**: Vector DB manager fails to initialize

**Solutions**:
- Check that required dependencies are installed
- Verify environment variables are set correctly
- Check backend health with `await manager.health_check()`
- Review logs for initialization errors

### Embedding Model Errors

**Problem**: Embedding model fails to generate embeddings

**Solutions**:
- Verify API keys are set correctly (for OpenAI/Cohere)
- Check that model dependencies are installed
- Review logs for embedding errors
- Consider switching to a different embedding model

### Backend Connection Errors

**Problem**: Cannot connect to vector DB backend

**Solutions**:
- Verify backend is running (for Qdrant/Weaviate)
- Check network connectivity
- Verify backend URL configuration
- Check backend logs for errors

## Entity Indexing

### Indexing Entities

Entities can be automatically indexed in the vector database for semantic search:

```python
from app.core.vectordb.indexing import index_entity, index_entities, get_indexing_status

# Index a single entity
result = await index_entity("light.living_room")
# Returns: {"entity_id": "light.living_room", "success": True, "description": "..."}

# Index all entities
result = await index_entities(batch_size=100)
# Returns: {"total": 50, "succeeded": 50, "failed": 0, "results": [...]}

# Get indexing status
status = await get_indexing_status()
# Returns: {"collection_exists": True, "total_entities": 50, "dimensions": 384, ...}
```

### Entity Descriptions

Entity descriptions are automatically generated from metadata:

- Friendly name
- Domain type
- Area/room information
- Device information (manufacturer, model)
- Domain-specific capabilities (brightness, color modes, etc.)
- Current state

Example descriptions:
- `"Living Room Light - light entity in the Living Room area. Supports brightness, color_temp. Currently on."`
- `"Temperature - temperature sensor in the Kitchen area. measured in °C. Currently 21.5."`

### Batch Indexing

Batch indexing processes entities in configurable batch sizes for performance:

```python
# Index all entities in batches of 100
result = await index_entities(batch_size=100)

# Index specific entities
result = await index_entities(
    entity_ids=["light.living_room", "sensor.temperature"],
    batch_size=50,
)
```

### Incremental Updates

Update entities when they change:

```python
# Update an entity in the index
result = await update_entity_index("light.living_room")

# Remove an entity from the index
result = await remove_entity_from_index("light.living_room")
```

## Related Features

- **US-VD-002**: Entity Embedding and Indexing (✅ Implemented)
- **US-VD-003**: Vector DB Configuration
- **US-VD-004**: Semantic Entity Search

## See Also

- [Configuration Guide](configuration.md)
- [Best Practices](best-practices.md)
- [Troubleshooting](troubleshooting.md)
