# Entities Tools

Entity tools allow you to query, search, and control Home Assistant entities (devices, sensors, lights, switches, etc.).

## Available Tools

### `get_entity`

Get the current state and attributes of a specific entity.

**Parameters:**
- `entity_id` (required): The entity ID, e.g., `light.living_room`
- `fields` (optional): List of specific fields to return, e.g., `["state", "attr.brightness"]`
- `detailed` (optional): If `true`, returns all attributes

**Example Usage:**
```
User: "What's the current state of light.living_room?"
Claude: [Uses get_entity]
✅ light.living_room is currently "on"
   Brightness: 255
   Color mode: brightness
```

**Response Formats:**
- **Lean** (default): Essential fields only for token efficiency
- **Detailed**: All attributes and metadata
- **Fields**: Only specified fields

### `search_entities` (Unified Tool)

Unified entity search tool that replaces `list_entities`, `search_entities_tool`, and `semantic_search_entities_tool`. Supports multiple search modes: keyword, semantic, and hybrid.

**Parameters:**
- `query` (optional): Search query string. If None, returns all entities (up to limit)
- `domain` (optional): Filter by domain, e.g., `light`, `switch`, `sensor`
- `search_mode` (optional): Search mode - `"keyword"` (default), `"semantic"`, or `"hybrid"`
- `limit` (optional): Maximum number of results (default: 100)
- `area_id` (optional): Area filter for semantic search
- `similarity_threshold` (optional): Similarity threshold for semantic search (default: 0.7)

**Example Usage:**
```
User: "Show me all the lights in my house"
Claude: [Uses search_entities with domain="light", search_mode="keyword"]
✅ Found 23 lights:
- light.living_room (on)
- light.kitchen (off)
- light.bedroom (on)
...

User: "Find lights in the living room"
Claude: [Uses search_entities with query="lights", area_id="living_room", search_mode="semantic"]
✅ Found 5 lights in living room:
- light.living_room (on)
- light.living_room_spot_01 (on)
...

User: "Search for temperature sensors"
Claude: [Uses search_entities with query="temperature", search_mode="keyword"]
✅ Found 5 temperature-related entities:
- sensor.living_room_temperature
- sensor.outdoor_temperature
...
```

**Search Modes:**
- `keyword`: Fast keyword-based search (default)
- `semantic`: Semantic search using vector embeddings (requires Vector DB)
- `hybrid`: Combines both semantic and keyword search for best results

### `entity_action`

Perform actions on entities (on, off, toggle).

**Parameters:**
- `entity_id` (required): The entity ID to control
- `action` (required): Action to perform (`on`, `off`, or `toggle`)
- `params` (optional): Additional parameters, e.g., `{"brightness": 255}` for lights

**Example Usage:**
```
User: "Turn on the living room light at 50% brightness"
Claude: [Uses entity_action]
✅ Living room light turned on with brightness 128

User: "Toggle the kitchen switch"
Claude: [Uses entity_action with action="toggle"]
✅ Kitchen switch toggled (now off)
```

**Supported Actions:**
- `on`: Turn the entity on
- `off`: Turn the entity off
- `toggle`: Toggle the entity state

**Domain-Specific Parameters:**
- **Lights**: `brightness` (0-255), `color_temp`, `rgb_color`, `transition`
- **Climate**: `temperature`, `hvac_mode`, `target_temp_high`, `target_temp_low`
- **Covers**: `position` (0-100), `tilt_position`
- **Media Players**: `source`, `volume_level` (0-1)

### `generate_entity_description` (Unified Tool)

Unified entity description generation tool that replaces `generate_entity_description` and `generate_entity_descriptions_batch`. Handles both single entity and batch modes.

**Parameters:**
- `entity_id` (optional): Single entity ID to generate description for (for single entity mode)
- `entity_ids` (optional): List of entity IDs to generate descriptions for (for batch mode)
- `use_template` (optional): Whether to use template-based generation (default: `true`)
- `language` (optional): Language for description (default: `"en"`)

**Example Usage:**
```
User: "Generate a description for light.living_room"
Claude: [Uses generate_entity_description with entity_id="light.living_room"]
✅ Generated description:
   "Living Room Light - light entity in the Living Room area. Supports brightness control. Currently on."

User: "Generate descriptions for all lights"
Claude: [Uses generate_entity_description with entity_ids=["light.living_room", "light.kitchen"]]
✅ Generated 2 descriptions:
   - light.living_room: "Living Room Light - light entity..."
   - light.kitchen: "Kitchen Light - light entity..."
```

**Note:** Either `entity_id` or `entity_ids` must be provided. If `entity_ids` is provided, the tool operates in batch mode.

## Use Cases

### Checking Entity States

```
"Check if all the lights are off"
"What's the temperature in the living room?"
"Is the garage door open?"
```

### Controlling Devices

```
"Turn on all the lights in the living room"
"Set the thermostat to 22 degrees"
"Open the garage door"
```

### Searching Entities

```
"Find all motion sensors"
"Show me all battery-powered devices"
"List all entities in the kitchen area"
```

## Best Practices

1. **Use domain filters** when possible to reduce token usage
2. **Use lean format** for listing operations
3. **Use specific entity IDs** when you know the exact entity
4. **Use search** when you're unsure of exact entity names

## Common Domains

- `light`: Light entities
- `switch`: Switch entities
- `sensor`: Sensor entities
- `binary_sensor`: Binary sensors
- `climate`: Thermostats and climate control
- `cover`: Blinds, garage doors, covers
- `lock`: Smart locks
- `fan`: Fans
- `media_player`: Media players
- `camera`: Cameras
