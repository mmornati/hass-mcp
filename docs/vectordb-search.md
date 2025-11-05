# Semantic Entity Search

Hass-MCP provides semantic search functionality for entities using natural language queries. This enables finding entities even when you don't know their exact names.

## Overview

Semantic search uses vector embeddings to find entities based on meaning rather than exact text matching. This enables natural language queries like:

- "living room lights"
- "temperature sensors in the kitchen"
- "all switches in the bedroom"
- "Philips Hue lights"

## Quick Start

### Basic Search

```python
from app.core.vectordb.search import semantic_search

# Search for entities using natural language
results = await semantic_search("living room lights")

for result in results:
    print(f"{result['entity_id']}: {result['similarity_score']:.2%}")
    print(f"  {result['explanation']}")
```

### Search with Filters

```python
# Search with domain filter
results = await semantic_search(
    "temperature sensors",
    domain="sensor",
    limit=10
)

# Search with area filter
results = await semantic_search(
    "lights",
    area_id="living_room",
    limit=5
)

# Search with multiple filters
results = await semantic_search(
    "lights",
    domain="light",
    area_id="living_room",
    entity_state="on",
    limit=10
)
```

## Search API

### `semantic_search`

Perform semantic search for entities using natural language queries.

```python
async def semantic_search(
    query: str,
    domain: str | None = None,
    area_id: str | None = None,
    device_manufacturer: str | None = None,
    entity_state: str | None = None,
    limit: int = 10,
    similarity_threshold: float | None = None,
    hybrid_search: bool | None = None,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
```

**Parameters:**

- **query** (required): Natural language search query
- **domain** (optional): Filter by domain (e.g., "light", "sensor", "switch")
- **area_id** (optional): Filter by area/room
- **device_manufacturer** (optional): Filter by device manufacturer
- **entity_state** (optional): Filter by entity state (e.g., "on", "off")
- **limit** (optional): Maximum number of results (default: 10)
- **similarity_threshold** (optional): Minimum similarity score (0.0-1.0, default: 0.7)
- **hybrid_search** (optional): Whether to use hybrid search (default: from config)
- **manager** (optional): VectorDBManager instance
- **config** (optional): VectorDBConfig instance

**Returns:**

List of entities with similarity scores and metadata:
- **entity_id**: Entity ID
- **similarity_score**: Similarity score (0.0-1.0)
- **entity**: Entity state dictionary
- **explanation**: Explanation for why entity matched
- **metadata**: Entity metadata from vector DB

**Example:**

```python
results = await semantic_search("living room lights")

# results = [
#     {
#         "entity_id": "light.living_room",
#         "similarity_score": 0.95,
#         "entity": {
#             "entity_id": "light.living_room",
#             "state": "on",
#             "attributes": {
#                 "friendly_name": "Living Room Light",
#                 "area_id": "living_room"
#             }
#         },
#         "explanation": "Entity 'Living Room Light' (light) in area 'living_room' matched with 95% similarity",
#         "metadata": {
#             "domain": "light",
#             "area_id": "living_room",
#             "friendly_name": "Living Room Light"
#         }
#     },
#     ...
# ]
```

## Search Filters

### Domain Filter

Filter results by entity domain:

```python
# Search only for lights
results = await semantic_search("lights", domain="light")

# Search only for sensors
results = await semantic_search("temperature", domain="sensor")
```

### Area Filter

Filter results by area/room:

```python
# Search only in living room
results = await semantic_search("lights", area_id="living_room")

# Search only in kitchen
results = await semantic_search("sensors", area_id="kitchen")
```

### Device Manufacturer Filter

Filter results by device manufacturer:

```python
# Search only for Philips devices
results = await semantic_search("lights", device_manufacturer="Philips")
```

### Entity State Filter

Filter results by entity state:

```python
# Search only for entities that are on
results = await semantic_search("lights", entity_state="on")

# Search only for entities that are off
results = await semantic_search("switches", entity_state="off")
```

### Combined Filters

Combine multiple filters:

```python
# Search for lights in living room that are on
results = await semantic_search(
    "lights",
    domain="light",
    area_id="living_room",
    entity_state="on",
    limit=10
)
```

## Hybrid Search

Hybrid search combines semantic and keyword search for better results:

```python
# Enable hybrid search
results = await semantic_search(
    "living room lights",
    hybrid_search=True,
    limit=10
)
```

### How Hybrid Search Works

1. **Semantic Search**: Find entities using vector similarity
2. **Keyword Search**: Find entities using string matching
3. **Merge Results**: Combine both result sets
4. **Rank Results**: Rank by combined score
5. **Deduplicate**: Remove duplicate entities
6. **Return Top N**: Return top results

## Result Ranking

Results are ranked by:

1. **Semantic Similarity**: Base similarity score from vector search
2. **Exact Matches**: Entities with exact matches in entity_id or friendly_name get boosted scores
3. **Domain Matches**: Entities matching the domain in the query get boosted scores
4. **Area Matches**: Entities matching the area in the query get boosted scores

### Score Boosting

- **Exact entity_id match**: +0.2 to similarity score
- **Exact friendly_name match**: +0.15 to similarity score
- **Domain match**: +0.1 to similarity score
- **Area match**: +0.1 to similarity score

## Similarity Threshold

Filter results by minimum similarity score:

```python
# Only return results with similarity >= 0.8
results = await semantic_search(
    "lights",
    similarity_threshold=0.8
)
```

The similarity threshold determines how closely results must match the query:
- **0.9-1.0**: Very close matches
- **0.7-0.9**: Good matches
- **0.5-0.7**: Moderate matches
- **<0.5**: Weak matches

## Result Format

Each search result contains:

```python
{
    "entity_id": "light.living_room",
    "similarity_score": 0.95,
    "entity": {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {
            "friendly_name": "Living Room Light",
            "area_id": "living_room",
            ...
        }
    },
    "explanation": "Entity 'Living Room Light' (light) in area 'living_room' matched with 95% similarity",
    "metadata": {
        "domain": "light",
        "area_id": "living_room",
        "friendly_name": "Living Room Light",
        "device_id": "device_123",
        ...
    }
}
```

## Examples

### Example 1: Natural Language Query

```python
# Search for "living room lights"
results = await semantic_search("living room lights")

# Results:
# 1. light.lumiere_salon (similarity: 0.92) - "Lumiere Salon" in "Salon" area
# 2. light.salon_spot_01 (similarity: 0.89) - "Salon Spot 01" in "Salon" area
# 3. light.lumiere_salle_a_manager (similarity: 0.85) - "Salle à Manager" light
```

### Example 2: Domain-Specific Query

```python
# Search for "temperature sensors"
results = await semantic_search("temperature sensors", domain="sensor")

# Results:
# 1. sensor.living_room_temperature (similarity: 0.95)
# 2. sensor.kitchen_temperature (similarity: 0.93)
# 3. sensor.outdoor_temperature (similarity: 0.91)
```

### Example 3: Filtered Search

```python
# Search for lights in kitchen that are on
results = await semantic_search(
    "lights",
    domain="light",
    area_id="kitchen",
    entity_state="on",
    limit=5
)
```

### Example 4: Hybrid Search

```python
# Use hybrid search for better results
results = await semantic_search(
    "living room lights",
    hybrid_search=True,
    limit=10
)
```

## Performance

### Search Performance

- **Typical queries**: <100ms
- **Concurrent searches**: Supported
- **Caching**: Frequent queries are cached
- **Optimization**: Embedding generation is optimized

### Best Practices

1. **Use Filters**: Apply filters to reduce search space
2. **Set Limits**: Use appropriate limits for better performance
3. **Adjust Threshold**: Tune similarity threshold for your use case
4. **Use Hybrid Search**: Enable hybrid search for better results
5. **Cache Results**: Cache frequent queries for better performance

## Error Handling

Semantic search handles errors gracefully:

### Vector DB Disabled

If vector DB is disabled, falls back to keyword search:

```python
results = await semantic_search("lights")
# Falls back to keyword search if vector DB is disabled
```

### Search Errors

If semantic search fails, falls back to keyword search:

```python
results = await semantic_search("lights")
# Falls back to keyword search if semantic search fails
```

### Missing Entities

If an entity is not found during result processing, it's skipped:

```python
results = await semantic_search("lights")
# Missing entities are skipped, search continues
```

## Troubleshooting

### Low Similarity Scores

**Problem**: Results have low similarity scores

**Solutions**:
- Check if entities are indexed
- Verify entity descriptions are rich
- Try adjusting similarity threshold
- Use hybrid search for better results

### No Results

**Problem**: Search returns no results

**Solutions**:
- Check if entities are indexed
- Verify search query is clear
- Lower similarity threshold
- Check filters are not too restrictive
- Try hybrid search

### Slow Searches

**Problem**: Searches are slow

**Solutions**:
- Reduce search limit
- Apply filters to reduce search space
- Check vector DB performance
- Verify embedding model is optimized

## Configuration

Semantic search respects configuration settings:

```python
from app.core.vectordb.config import get_vectordb_config

config = get_vectordb_config()

# Default limit
limit = config.get_search_default_limit()  # Default: 10

# Default similarity threshold
threshold = config.get_search_similarity_threshold()  # Default: 0.7

# Hybrid search enabled
hybrid = config.get_search_hybrid_search()  # Default: false
```

## Related Features

- **US-VD-001**: Vector DB Core Infrastructure
- **US-VD-002**: Entity Embedding and Indexing
- **US-VD-003**: Vector DB Configuration

## See Also

- [Vector DB Overview](vectordb.md)
- [Entity Indexing](vectordb-indexing.md)
- [Configuration](vectordb-configuration.md)
