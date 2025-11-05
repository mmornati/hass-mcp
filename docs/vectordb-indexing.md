# Entity Embedding and Indexing

Hass-MCP provides automatic entity embedding and indexing for semantic search capabilities. This enables natural language discovery of entities based on their descriptions and metadata.

## Overview

Entity indexing automatically:

- **Generates Rich Descriptions**: Creates comprehensive text descriptions from entity metadata
- **Creates Embeddings**: Converts descriptions to vector embeddings
- **Indexes in Vector DB**: Stores embeddings with metadata for semantic search
- **Handles Updates**: Automatically updates index when entities change
- **Batch Processing**: Efficiently processes large numbers of entities

## Quick Start

### Index a Single Entity

```python
from app.core.vectordb.indexing import index_entity

# Index a single entity
result = await index_entity("light.living_room")
if result["success"]:
    print(f"Indexed: {result['entity_id']}")
    print(f"Description: {result['description']}")
```

### Index All Entities

```python
from app.core.vectordb.indexing import index_entities

# Index all entities in batches
result = await index_entities(batch_size=100)
print(f"Indexed {result['succeeded']} out of {result['total']} entities")
```

### Check Indexing Status

```python
from app.core.vectordb.indexing import get_indexing_status

# Get indexing status
status = await get_indexing_status()
print(f"Total indexed: {status['total_entities']}")
print(f"Collection exists: {status['collection_exists']}")
```

## Entity Description Generation

Entity descriptions are automatically generated from metadata to provide rich context for semantic search.

### Description Components

1. **Friendly Name**: Primary identifier for the entity
2. **Domain Type**: Entity type (light, sensor, switch, etc.)
3. **Area/Room**: Location information
4. **Device Information**: Manufacturer and model
5. **Capabilities**: Domain-specific features
6. **Current State**: Current entity state

### Example Descriptions

**Light Entity:**
```
Living Room Light - light entity in the Living Room area.
Supports brightness, color_temp. brightness control. color temperature control.
Currently on.
```

**Sensor Entity:**
```
Temperature - temperature sensor in the Kitchen area.
measured in °C. Currently 21.5.
```

**Climate Entity:**
```
Living Room Thermostat - climate entity in the Living Room area.
current temperature 21.5. target temperature 22.0. mode heat.
```

### Custom Descriptions

You can generate custom descriptions:

```python
from app.core.vectordb.indexing import generate_entity_description

entity = {
    "entity_id": "light.living_room",
    "state": "on",
    "attributes": {
        "friendly_name": "Living Room Light",
        "area_id": "living_room",
    },
}

description = generate_entity_description(
    entity,
    area_name="Living Room",
    device_info={"manufacturer": "Philips", "model": "Hue"},
)
```

## Indexing Functions

### `index_entity`

Index a single entity in the vector database.

```python
async def index_entity(
    entity_id: str,
    manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Index a single entity in the vector database.

    Args:
        entity_id: The entity ID to index
        manager: Optional VectorDBManager instance

    Returns:
        Dictionary with indexing result:
        - entity_id: The entity ID indexed
        - success: Boolean indicating if indexing succeeded
        - description: Generated description
        - error: Error message if indexing failed
    """
```

**Example:**
```python
result = await index_entity("light.living_room")
# {
#     "entity_id": "light.living_room",
#     "success": True,
#     "description": "Living Room Light - light entity..."
# }
```

### `index_entities`

Index multiple entities in batches.

```python
async def index_entities(
    entity_ids: list[str] | None = None,
    batch_size: int = 100,
    manager: VectorDBManager | None = None,
) -> dict[str, Any]:
    """
    Index multiple entities in batches.

    Args:
        entity_ids: Optional list of entity IDs to index.
                   If None, indexes all entities.
        batch_size: Number of entities to process in each batch
        manager: Optional VectorDBManager instance

    Returns:
        Dictionary with indexing results:
        - total: Total number of entities processed
        - succeeded: Number of successfully indexed entities
        - failed: Number of failed entities
        - results: List of individual indexing results
    """
```

**Example:**
```python
# Index all entities
result = await index_entities()

# Index specific entities
result = await index_entities(
    entity_ids=["light.living_room", "sensor.temperature"],
    batch_size=50,
)
```

### `update_entity_index`

Update an existing entity in the index.

```python
async def update_entity_index(
    entity_id: str,
    manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Update an existing entity in the index.

    Args:
        entity_id: The entity ID to update
        manager: Optional VectorDBManager instance

    Returns:
        Dictionary with update result
    """
```

**Example:**
```python
# Update entity after changes
result = await update_entity_index("light.living_room")
```

### `remove_entity_from_index`

Remove an entity from the index.

```python
async def remove_entity_from_index(
    entity_id: str,
    manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Remove an entity from the index.

    Args:
        entity_id: The entity ID to remove
        manager: Optional VectorDBManager instance

    Returns:
        Dictionary with removal result
    """
```

**Example:**
```python
# Remove deleted entity
result = await remove_entity_from_index("light.living_room")
```

### `get_indexing_status`

Get indexing status for the entity collection.

```python
async def get_indexing_status(
    manager: VectorDBManager | None = None
) -> dict[str, Any]:
    """
    Get indexing status for the entity collection.

    Args:
        manager: Optional VectorDBManager instance

    Returns:
        Dictionary with indexing status:
        - collection_exists: Whether the collection exists
        - total_entities: Total number of indexed entities
        - dimensions: Vector dimensions
        - metadata: Collection metadata
    """
```

**Example:**
```python
status = await get_indexing_status()
# {
#     "collection_exists": True,
#     "total_entities": 50,
#     "dimensions": 384,
#     "metadata": {}
# }
```

## Metadata Storage

Entities are indexed with rich metadata for filtering and search:

```python
{
    "entity_id": "light.living_room",
    "domain": "light",
    "friendly_name": "Living Room Light",
    "area_id": "living_room",
    "device_id": "device_123",
    "device_class": None,
    "manufacturer": "Philips",
    "model": "Hue",
    "last_updated": "2025-01-01T12:00:00Z",
    "indexed_at": "2025-01-01T12:00:00Z"
}
```

### Metadata Fields

- **entity_id**: Unique entity identifier
- **domain**: Entity domain (light, sensor, etc.)
- **friendly_name**: Display name
- **area_id**: Area/room identifier
- **device_id**: Device identifier
- **device_class**: Device class (if applicable)
- **manufacturer**: Device manufacturer (if available)
- **model**: Device model (if available)
- **last_updated**: Last entity update timestamp
- **indexed_at**: Indexing timestamp

## Batch Processing

Batch indexing processes entities in configurable batches for performance:

### Batch Size Configuration

```python
# Small batches for slower systems
result = await index_entities(batch_size=50)

# Large batches for faster systems
result = await index_entities(batch_size=500)

# Default batch size (100)
result = await index_entities()
```

### Progress Tracking

```python
result = await index_entities(batch_size=100)

print(f"Total: {result['total']}")
print(f"Succeeded: {result['succeeded']}")
print(f"Failed: {result['failed']}")

# Check individual results
for item in result["results"]:
    if not item["success"]:
        print(f"Failed to index {item['entity_id']}: {item.get('error')}")
```

## Incremental Updates

Entities can be updated incrementally when they change:

### Manual Updates

```python
# Update entity after changes
await update_entity_index("light.living_room")
```

### Automatic Updates

For automatic updates, you would typically:

1. Listen to entity state changes
2. Detect relevant changes (name, area, attributes)
3. Call `update_entity_index()` for changed entities

**Example:**
```python
# When entity name changes
async def on_entity_changed(entity_id: str):
    await update_entity_index(entity_id)
```

## Error Handling

Indexing functions handle errors gracefully:

### Entity Not Found

```python
result = await index_entity("light.nonexistent")
# {
#     "entity_id": "light.nonexistent",
#     "success": False,
#     "error": "Entity not found"
# }
```

### Vector DB Disabled

```python
# If vector DB is disabled
result = await index_entity("light.living_room")
# {
#     "entity_id": "light.living_room",
#     "success": False,
#     "error": "Vector DB is disabled"
# }
```

### Partial Failures

When indexing multiple entities, individual failures don't stop the process:

```python
result = await index_entities(
    entity_ids=["light.living_room", "sensor.nonexistent"],
)

# result["succeeded"] == 1
# result["failed"] == 1
# Check individual results for details
```

## Best Practices

1. **Initial Indexing**: Index all entities on startup or first run
2. **Batch Size**: Use batch sizes of 100-500 for optimal performance
3. **Incremental Updates**: Update entities when they change (name, area, attributes)
4. **Error Handling**: Check individual results for failures
5. **Status Monitoring**: Regularly check indexing status
6. **Cleanup**: Remove deleted entities from the index

## Performance Considerations

- **Batch Processing**: Process entities in batches for better performance
- **Async Operations**: All operations are async for non-blocking I/O
- **Error Recovery**: Individual entity failures don't stop batch processing
- **Metadata Caching**: Area and device information is cached for performance

## Troubleshooting

### Entities Not Indexing

**Problem**: Entities fail to index

**Solutions**:
- Check vector DB is enabled
- Verify entity exists in Home Assistant
- Check entity metadata is valid
- Review logs for specific errors

### Slow Indexing

**Problem**: Indexing is slow

**Solutions**:
- Reduce batch size for slower systems
- Check vector DB backend performance
- Verify embedding model is working correctly
- Check network connectivity (for cloud embeddings)

### Index Out of Sync

**Problem**: Index doesn't match current entities

**Solutions**:
- Re-index all entities: `await index_entities()`
- Check for indexing errors
- Verify entity updates are being processed
- Check vector DB collection status

## Related Features

- **US-VD-001**: Vector DB Core Infrastructure
- **US-VD-004**: Semantic Entity Search

## See Also

- [Vector DB Overview](vectordb.md)
- [Configuration Guide](configuration.md)
- [Best Practices](best-practices.md)
