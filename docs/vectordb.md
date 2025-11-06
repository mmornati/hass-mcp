# Vector DB Core Infrastructure

Hass-MCP includes a comprehensive vector database infrastructure for semantic search capabilities. This enables natural language understanding and semantic entity discovery.

## Overview

The Vector DB infrastructure provides:

- **Multiple Backend Support**: Chroma, Qdrant, Weaviate, Pinecone
- **Multiple Embedding Models**: sentence-transformers, OpenAI, Cohere
- **Unified Interface**: Single API for all vector operations
- **Graceful Degradation**: Fallback to keyword search if vector DB unavailable

## Configuration

Vector DB configuration can be set via:
1. **Configuration Files** (JSON/YAML) - Recommended for complex setups
2. **Environment Variables** - Override config files
3. **Default Values** - Fallback if not specified

Configuration files are automatically discovered in:
- Current working directory
- Home directory
- `HASS_MCP_CONFIG_DIR` environment variable
- `/etc/hass-mcp`

Supported file names:
- `vectordb.json`, `vectordb.yaml`, `vectordb.yml`
- `.vectordb.json`, `.vectordb.yaml`

### Configuration File Format

#### JSON Configuration

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

#### YAML Configuration

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

### Environment Variables

Environment variables override configuration file values.

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

# OpenAI model name (default: text-embedding-3-small)
export HASS_MCP_OPENAI_MODEL=text-embedding-3-small
```

#### Cohere Configuration

```bash
# Cohere API key (required for Cohere embeddings)
export HASS_MCP_COHERE_API_KEY=your_api_key

# Cohere model name (default: embed-english-v3.0)
export HASS_MCP_COHERE_MODEL=embed-english-v3.0
```

#### Performance Configuration

```bash
# Indexing batch size (default: 100)
export HASS_MCP_INDEXING_BATCH_SIZE=100

# Auto-index on startup (default: false)
export HASS_MCP_INDEXING_AUTO_INDEX=false

# Update index on entity changes (default: true)
export HASS_MCP_INDEXING_UPDATE_ON_CHANGE=true

# Search default limit (default: 10)
export HASS_MCP_SEARCH_DEFAULT_LIMIT=10

# Search similarity threshold (default: 0.7)
export HASS_MCP_SEARCH_SIMILARITY_THRESHOLD=0.7

# Use hybrid search (default: false)
export HASS_MCP_SEARCH_HYBRID_SEARCH=false
```

#### Embedding Model Configuration

```bash
# Embedding device (default: cpu)
export HASS_MCP_EMBEDDING_DEVICE=cpu  # Options: cpu, gpu, cuda

# Collection name (default: entities)
export HASS_MCP_VECTOR_DB_COLLECTION=entities

# Pinecone index name (default: entities)
export HASS_MCP_PINECONE_INDEX_NAME=entities
```

### Configuration Validation

The configuration system validates settings on initialization:

```python
from app.core.vectordb.config import VectorDBConfig

config = VectorDBConfig()
is_valid, errors = config.validate()

if not is_valid:
    for error in errors:
        print(f"Configuration error: {error}")
```

Validation checks:
- Backend and embedding model validity
- Required API keys for cloud services
- Performance settings within valid ranges
- Device configuration validity

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

## Semantic Search

### Natural Language Entity Search

Entities can be searched using natural language queries:

```python
from app.core.vectordb.search import semantic_search

# Search for entities using natural language
results = await semantic_search("living room lights")
# Returns: [
#     {
#         "entity_id": "light.living_room",
#         "similarity_score": 0.95,
#         "entity": {...},
#         "explanation": "Entity 'Living Room Light' (light) matched with 95% similarity",
#         "metadata": {...}
#     },
#     ...
# ]

# Search with filters
results = await semantic_search(
    "temperature sensors",
    domain="sensor",
    area_id="kitchen",
    limit=10,
    similarity_threshold=0.7
)
```

### Hybrid Search

Hybrid search combines semantic and keyword search for better results:

```python
# Enable hybrid search (combines semantic + keyword)
results = await semantic_search(
    "living room lights",
    hybrid_search=True,
    limit=10
)
```

### Search Filters

Filter search results by:
- **Domain**: Filter by entity domain (light, sensor, switch, etc.)
- **Area**: Filter by area/room
- **Device Manufacturer**: Filter by device manufacturer
- **Entity State**: Filter by entity state (on, off, etc.)

### Result Ranking

Results are ranked by:
- Semantic similarity score
- Exact matches (entity_id, friendly_name) get boosted scores
- Domain matches get boosted scores
- Area/room matches get boosted scores

## Query Intent Classification

### Natural Language Understanding

The query intent classification module processes natural language queries to understand user intent and extract relevant information:

```python
from app.core.vectordb.classification import process_query

# Process a query
result = await process_query("turn on the living room lights to 50% brightness")

print(result["intent"])  # "CONTROL"
print(result["action"])  # "on"
print(result["domain"])  # "light"
print(result["entity_filters"]["area_id"])  # "living_room"
print(result["action_params"]["value"])  # 50
```

### Intent Types

The module classifies queries into six intent types:
- **SEARCH**: Find or discover entities
- **CONTROL**: Control or modify entities
- **STATUS**: Get the current status of entities
- **CONFIGURE**: Configure or setup entities
- **DISCOVER**: Discover related entities
- **ANALYZE**: Analyze entity data or patterns

### Integration with Semantic Search

Classification results can be used to improve semantic search:

```python
from app.core.vectordb.classification import process_query
from app.core.vectordb.search import semantic_search

# Classify query
classification = await process_query("find all temperature sensors in the kitchen")

# Use classification results for semantic search
results = await semantic_search(
    query=classification["refined_query"],
    domain=classification["domain"],
    area_id=classification["entity_filters"].get("area_id"),
    limit=10,
)
```

For more details, see the [Query Intent Classification Guide](vectordb-classification.md).

## Query History and Learning

### Learning from User Patterns

The query history and learning module stores query history and learns from user patterns:

```python
from app.core.vectordb.history import store_query_history, boost_entity_ranking
from app.core.vectordb.search import semantic_search

# Perform semantic search
results = await semantic_search("living room lights")

# Boost results based on popularity
boosted_results = await boost_entity_ranking(results)

# Store query history
await store_query_history(
    query="living room lights",
    results=boosted_results,
    selected_entity_id=boosted_results[0]["entity_id"] if boosted_results else None,
)
```

### Query Statistics

Get insights into query patterns:

```python
from app.core.vectordb.history import get_query_statistics

# Get statistics for the last 30 days
stats = await get_query_statistics(days=30)

print(stats["total_queries"])  # Total number of queries
print(stats["most_common_queries"])  # Most common queries
print(stats["most_selected_entities"])  # Most selected entities
```

For more details, see the [Query History and Learning Guide](vectordb-history.md).

## Entity Relationship Graph

### Understanding Entity Relationships

The entity relationship graph module builds and maintains entity relationships:

```python
from app.core.vectordb.relationships import build_relationship_graph, get_entities_in_area

# Build relationship graph
result = await build_relationship_graph()

# Get entities in an area
entities = await get_entities_in_area("living_room")
```

### Relationship Queries

Find entities by relationship type:

```python
from app.core.vectordb.relationships import get_related_entities

# Get related entities
related = await get_related_entities("light.living_room")

for entity_info in related:
    print(f"{entity_info['entity_id']} via {entity_info['relationship_type']}")
```

For more details, see the [Entity Relationship Graph Guide](vectordb-relationships.md).

## Enhanced Entity Search Tool

### MCP Tool Integration

The semantic search functionality is available as an MCP tool:

```python
# Use semantic_search_entities_tool via MCP
result = await semantic_search_entities_tool(
    query="living room lights",
    domain="light",
    area_id="living_room",
    limit=10,
    similarity_threshold=0.7,
    search_mode="hybrid",
)
```

The tool supports three search modes:
- **semantic**: Pure semantic search
- **keyword**: Pure keyword search (fallback)
- **hybrid**: Combines both (default)

For more details, see the [Entities Tools Documentation](entities.md#semantic_search_entities_tool).

## Natural Language Query Processing

### Processing Natural Language Queries

The natural language query processing tool processes user queries to extract entities, actions, and parameters:

```python
from app.tools.query_processing import process_natural_language_query

# Process a natural language query
result = await process_natural_language_query("Turn on the living room lights")

print(result["intent"])  # "CONTROL"
print(result["entities"])  # [{"entity_id": "light.living_room", "confidence": 0.92}, ...]
print(result["action"])  # "on"
print(result["execution_plan"])  # [{"entity": "light.living_room", "action": "on"}, ...]
```

### Query Processing Pipeline

The tool processes queries through:
1. **Intent Classification**: Identifies query intent (CONTROL, STATUS, SEARCH, etc.)
2. **Entity Resolution**: Resolves entity references using semantic search
3. **Action Extraction**: Extracts actions (on, off, set, etc.)
4. **Parameter Extraction**: Extracts parameters (temperature, brightness, etc.)
5. **Execution Plan**: Builds structured execution plans

For more details, see the [Natural Language Query Processing Guide](query-processing.md).

## Related Features

- **US-VD-002**: Entity Embedding and Indexing (✅ Implemented)
- **US-VD-003**: Vector DB Configuration (✅ Implemented)
- **US-VD-004**: Semantic Entity Search (✅ Implemented)
- **US-VD-006**: Query Intent Classification (✅ Implemented)
- **US-VD-007**: Query History and Learning (✅ Implemented)
- **US-VD-008**: Entity Relationship Graph (✅ Implemented)
- **US-VD-009**: Enhanced Entity Search Tool (✅ Implemented)
- **US-VD-010**: Natural Language Query Processing (✅ Implemented)

## See Also

- [Configuration Guide](configuration.md)
- [Best Practices](best-practices.md)
- [Troubleshooting](troubleshooting.md)
