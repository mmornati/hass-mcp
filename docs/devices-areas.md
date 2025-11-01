# Devices & Areas Tools

Manage devices and areas in your Home Assistant instance.

## Devices Tools

### `list_devices`

List all devices registered in Home Assistant.

**Example Usage:**
```
User: "Show me all my devices"
Claude: [Uses list_devices]
✅ Found 45 devices:
- Living Room Device (Philips Hue)
- Kitchen Device (TP-Link)
...
```

### `get_device`

Get detailed information about a specific device.

**Parameters:**
- `device_id` (required): The device ID

### `get_device_entities`

Get all entities associated with a device.

**Parameters:**
- `device_id` (required): The device ID

### `get_device_stats`

Get statistics about a device.

**Parameters:**
- `device_id` (required): The device ID

## Areas Tools

### `list_areas`

List all areas in your Home Assistant instance.

**Example Usage:**
```
User: "What areas are configured in my Home Assistant?"
Claude: [Uses list_areas]
✅ Areas:
- Living Room
- Kitchen
- Bedroom
...
```

### `get_area_entities`

Get all entities in a specific area.

**Parameters:**
- `area_id` (required): The area ID or name

### `create_area` / `update_area` / `delete_area`

Manage areas in Home Assistant.

**Parameters:**
- `area_id` (required): The area ID
- `name` (required): The area name
- `aliases` (optional): Area aliases

### `get_area_summary`

Get a summary of an area including entity counts and types.

**Parameters:**
- `area_id` (required): The area ID or name

## Use Cases

### Device Management

```
"Show me all my Philips Hue devices"
"What entities are on the Living Room Device?"
"Get statistics for device XYZ"
```

### Area Management

```
"List all my areas"
"What devices are in the Living Room?"
"Create a new area called 'Garden'"
"Show me a summary of the Kitchen area"
```
