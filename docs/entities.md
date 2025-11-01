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

### `list_entities`

List all entities or filter by domain/search query.

**Parameters:**
- `domain` (optional): Filter by domain, e.g., `light`, `switch`, `sensor`
- `search_query` (optional): Search entities by name or ID
- `limit` (optional): Maximum number of results (default: 100)
- `lean` (optional): Use lean format for efficiency (default: `true`)

**Example Usage:**
```
User: "Show me all the lights in my house"
Claude: [Uses list_entities with domain="light"]
✅ Found 23 lights:
- light.living_room (on)
- light.kitchen (off)
- light.bedroom (on)
...
```

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

### `search_entities_tool`

Search for entities by name, ID, or attributes.

**Parameters:**
- `query` (required): Search query string
- `limit` (optional): Maximum number of results (default: 20)

**Example Usage:**
```
User: "Find all entities with 'temperature' in the name"
Claude: [Uses search_entities_tool]
✅ Found 5 temperature-related entities:
- sensor.living_room_temperature
- sensor.outdoor_temperature
...
```

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
