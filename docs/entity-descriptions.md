# Entity Description Generation

The entity description generation module provides enhanced entity description generation with templates, multi-language support, and context-aware descriptions for better semantic search.

## Overview

The entity description generation module enables:

- **Template-Based Generation**: Uses domain-specific templates for consistent descriptions
- **Rich Metadata Extraction**: Extracts device information, area information, and capabilities
- **Context-Aware Descriptions**: Includes contextual information (location, device, usage)
- **Multi-Language Support**: Supports multiple languages (currently English)
- **Batch Processing**: Generates descriptions for multiple entities efficiently

## Usage

### Basic Usage

```python
from app.core.vectordb.description import generate_entity_description_enhanced

# Generate description for a single entity
entity = {
    "entity_id": "light.living_room",
    "state": "on",
    "attributes": {
        "friendly_name": "Living Room Light",
        "area_id": "living_room",
    },
}

description = await generate_entity_description_enhanced(
    entity, use_template=True, language="en"
)

print(description)
# "Living Room Light - light entity in the Living Room area. Supports brightness control. Currently on. Part of the Philips Hue Bridge system."
```

### Batch Processing

```python
from app.core.vectordb.description import generate_entity_description_batch

# Generate descriptions for multiple entities
entities = [
    {"entity_id": "light.living_room", "state": "on", "attributes": {...}},
    {"entity_id": "sensor.temperature", "state": "22.5", "attributes": {...}},
]

descriptions = await generate_entity_description_batch(
    entities, use_template=True, language="en"
)

print(descriptions["light.living_room"])
print(descriptions["sensor.temperature"])
```

### Using MCP Tools

```python
from app.tools.entity_descriptions import (
    generate_entity_description_tool,
    generate_entity_descriptions_batch_tool,
)

# Generate description for a single entity
result = await generate_entity_description_tool(
    entity_id="light.living_room",
    use_template=True,
    language="en",
)

print(result["description"])

# Generate descriptions for multiple entities
result = await generate_entity_descriptions_batch_tool(
    entity_ids=["light.living_room", "sensor.temperature"],
    use_template=True,
    language="en",
)

print(result["descriptions"])
```

## Description Templates

The module uses domain-specific templates for consistent descriptions:

### Light Template

```
{friendly_name} - {domain} entity in the {area_name} area.
Supports {capabilities}. Currently {state}.
Part of the {manufacturer} {model} system.
```

### Sensor Template

```
{friendly_name} - {domain} entity ({device_class}) in the {area_name} area.
Measures {unit_of_measurement}. Currently {state}.
Manufactured by {manufacturer}.
```

### Climate Template

```
{friendly_name} - {domain} entity in the {area_name} area.
Current temperature: {current_temperature}°C.
Target temperature: {temperature}°C. Mode: {hvac_mode}.
```

### Switch Template

```
{friendly_name} - {domain} entity in the {area_name} area.
Currently {state}. Part of {device_name}.
```

### Default Template

```
{friendly_name} - {domain} entity in the {area_name} area.
Currently {state}. Part of {device_name}.
```

## Template Variables

Templates support the following variables:

- **friendly_name**: Entity friendly name
- **domain**: Entity domain (light, sensor, etc.)
- **area_name**: Area/room name
- **state**: Current entity state
- **capabilities**: Entity capabilities (extracted from attributes)
- **manufacturer**: Device manufacturer
- **model**: Device model
- **device_name**: Device name
- **device_class**: Device class (for sensors)
- **unit_of_measurement**: Unit of measurement (for sensors)
- **current_temperature**: Current temperature (for climate)
- **temperature**: Target temperature (for climate)
- **hvac_mode**: HVAC mode (for climate)

## Capability Extraction

The module extracts capabilities based on entity domain:

### Light Capabilities

- Color modes (brightness, color_temp, rgb, etc.)
- Brightness control
- Color temperature control
- RGB color control

### Sensor Capabilities

- Device class (temperature, humidity, motion, etc.)

### Climate Capabilities

- HVAC modes (heat, cool, off, etc.)
- Temperature control

### Cover Capabilities

- Cover control features

## Metadata Extraction

The module extracts rich metadata from entities:

### Device Information

- Manufacturer
- Model
- Device name
- Device type

### Area Information

- Area/room name
- Area ID

### Entity Attributes

- Friendly name
- Domain
- State
- Capabilities
- Domain-specific attributes

## Integration with Indexing

The enhanced description generation is automatically used in entity indexing:

```python
from app.core.vectordb.indexing import index_entity

# Index entity (uses enhanced description generation)
result = await index_entity("light.living_room")
```

The indexing module automatically uses `generate_entity_description_enhanced` for better semantic search results.

## Best Practices

1. **Use Templates**: Use template-based generation for consistent descriptions
2. **Batch Processing**: Use batch processing for multiple entities
3. **Provide Context**: Provide area_name and device_info when available
4. **Language Support**: Use language parameter for future multi-language support
5. **Error Handling**: Handle errors gracefully when generation fails

## Limitations

- **Language Support**: Currently supports English primarily
- **Template Variables**: Some template variables may be missing for certain entities
- **Device Information**: Device information may not be available for all entities

## Future Enhancements

Future versions may include:
- Full multi-language support
- Custom template support
- Template inheritance
- Description versioning
- Description change tracking
