# Entity Relationship Graph

The entity relationship graph module provides relationship graph construction, storage, and querying for intelligent entity discovery and context-aware suggestions.

## Overview

The relationship graph module enables:

- **Relationship Graph Construction**: Build entity relationship graph from Home Assistant data
- **Relationship Storage**: Store relationships in vector database for semantic search
- **Relationship Queries**: Find entities by relationship type, area, device, etc.
- **Graph Traversal**: Traverse relationship graph to find related entities
- **Relationship Statistics**: Get insights into relationship patterns

## Relationship Types

The module supports the following relationship types:

- **in_area**: Entity is in an area/room
- **from_device**: Entity is from a device
- **same_device**: Entities from same device
- **same_area**: Entities in same area
- **same_domain**: Entities of same domain
- **in_automation**: Entity used in automation
- **device_parent**: Device parent relationship
- **device_child**: Device child relationship

## Usage

### Building Relationship Graph

```python
from app.core.vectordb.relationships import build_relationship_graph

# Build relationship graph from Home Assistant data
result = await build_relationship_graph()

print(result["total_relationships"])  # Total number of relationships
print(result["relationships_by_type"])  # Count by relationship type
print(result["entities_count"])  # Number of entities
print(result["areas_count"])  # Number of areas
print(result["devices_count"])  # Number of devices
```

### Finding Entities by Relationship

```python
from app.core.vectordb.relationships import find_entities_by_relationship

# Find all relationships of a specific type
relationships = await find_entities_by_relationship(
    relationship_type="in_area",
    limit=50,
)

# Find relationships for a specific entity
relationships = await find_entities_by_relationship(
    entity_id="light.living_room",
    limit=50,
)

# Find relationships with a specific target
relationships = await find_entities_by_relationship(
    target="living_room",
    relationship_type="in_area",
    limit=50,
)
```

### Getting Entities in Area

```python
from app.core.vectordb.relationships import get_entities_in_area

# Get all entities in an area
entities = await get_entities_in_area("living_room")

print(entities)  # ["light.living_room", "sensor.temperature", ...]
```

### Getting Entities from Device

```python
from app.core.vectordb.relationships import get_entities_from_device

# Get all entities from a device
entities = await get_entities_from_device("device1")

print(entities)  # ["light.living_room", "light.kitchen", ...]
```

### Getting Related Entities

```python
from app.core.vectordb.relationships import get_related_entities

# Get all related entities
related = await get_related_entities("light.living_room")

# Get related entities with specific relationship types
related = await get_related_entities(
    "light.living_room",
    relationship_types=["same_area", "same_device"],
    limit=20,
)

for entity_info in related:
    print(entity_info["entity_id"])
    print(entity_info["relationship_type"])
```

### Relationship Statistics

```python
from app.core.vectordb.relationships import get_relationship_statistics

# Get relationship graph statistics
stats = await get_relationship_statistics()

print(stats["total_relationships"])  # Total number of relationships
print(stats["relationships_by_type"])  # Count by relationship type
print(stats["entities_with_relationships"])  # Entities with relationships
print(stats["areas_with_entities"])  # Areas with entities
print(stats["devices_with_entities"])  # Devices with entities
```

## Relationship Graph Structure

The relationship graph is structured as follows:

```
Entity Graph:
  Area: Living Room
    ├── light.living_room (in_area)
    ├── sensor.temperature (in_area)
    └── switch.living_room (in_area)

  Device: Philips Hue Bridge
    ├── light.living_room (from_device)
    ├── light.kitchen (from_device)
    └── light.bedroom (from_device)

  Device Hierarchy:
    ├── device1 (device_parent)
    │   └── device2 (device_child)
```

## Integration with Other Modules

The relationship graph integrates with other Vector DB modules:

### With Semantic Search

```python
from app.core.vectordb.relationships import get_entities_in_area
from app.core.vectordb.search import semantic_search

# Get entities in area
area_entities = await get_entities_in_area("living_room")

# Perform semantic search on area entities
results = await semantic_search("lights", area_id="living_room")
```

### With Entity Suggestions

```python
from app.core.vectordb.relationships import get_related_entities

# Get related entities for suggestions
related = await get_related_entities("light.living_room")

# Use related entities for context-aware suggestions
for entity_info in related:
    print(f"Related: {entity_info['entity_id']} via {entity_info['relationship_type']}")
```

## Relationship Queries

### Query by Relationship Type

```python
# Find all area relationships
area_relationships = await find_entities_by_relationship(
    relationship_type="in_area",
    limit=100,
)

# Find all device relationships
device_relationships = await find_entities_by_relationship(
    relationship_type="from_device",
    limit=100,
)
```

### Query by Entity

```python
# Find all relationships for an entity
relationships = await find_entities_by_relationship(
    entity_id="light.living_room",
    limit=50,
)

# Find related entities
related = await get_related_entities("light.living_room")
```

### Query by Area

```python
# Get all entities in an area
entities = await get_entities_in_area("living_room")

# Find relationships in an area
relationships = await find_entities_by_relationship(
    target="living_room",
    relationship_type="in_area",
    limit=50,
)
```

### Query by Device

```python
# Get all entities from a device
entities = await get_entities_from_device("device1")

# Find relationships from a device
relationships = await find_entities_by_relationship(
    target="device1",
    relationship_type="from_device",
    limit=50,
)
```

## Best Practices

1. **Build graph periodically**: Rebuild the relationship graph when entities, areas, or devices change.

2. **Use relationship queries for context**: Use relationship queries to provide context-aware suggestions.

3. **Combine with semantic search**: Combine relationship queries with semantic search for better results.

4. **Monitor statistics**: Use relationship statistics to understand your entity structure.

5. **Update graph on changes**: Update the relationship graph when entities are added, removed, or modified.

## Limitations

- **Simplified automation relationships**: Current implementation has simplified automation relationship extraction. Full automation parsing would require parsing automation YAML/JSON.

- **No real-time updates**: The relationship graph is built on-demand. Real-time updates would require event listeners.

- **Storage limitations**: Large relationship graphs may require additional storage management.

## Future Enhancements

Future versions may include:
- Real-time relationship graph updates
- Full automation dependency mapping
- Relationship graph visualization
- Advanced graph traversal algorithms
- Relationship-based entity clustering
