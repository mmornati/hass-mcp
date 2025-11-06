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

### `get_item_entities` (Unified Tool)

Unified tool that replaces `get_device_entities` and `get_area_entities`.

**Parameters:**
- `item_type` (required): Type of item. Options:
  - `"device"`: Get entities for a device
  - `"area"`: Get entities in an area
- `item_id` (required): The item ID (device_id or area_id)

**Example Usage:**
```
User: "What entities are on the Living Room Device?"
Claude: [Uses get_item_entities with item_type="device", item_id="device_123"]
✅ Device Entities:
- light.living_room
- sensor.living_room_temperature
...

User: "What entities are in the Living Room area?"
Claude: [Uses get_item_entities with item_type="area", item_id="living_room"]
✅ Area Entities:
- light.living_room
- switch.living_room_fan
...
```

### `get_item_summary` (Unified Tool)

Unified tool that replaces `get_device_stats` and `get_area_summary`.

**Parameters:**
- `item_type` (required): Type of item. Options:
  - `"device"`: Get device statistics (requires `item_id`)
  - `"area"`: Get area summary (`item_id` optional, returns all areas if None)
- `item_id` (optional): Item ID (device_id for `"device"`, area_id for `"area"`)

**Example Usage:**
```
User: "Get statistics for device XYZ"
Claude: [Uses get_item_summary with item_type="device", item_id="device_123"]
✅ Device Statistics:
   - Total entities: 5
   - Manufacturer: Philips Hue
   - Model: Bridge

User: "Show me a summary of all areas"
Claude: [Uses get_item_summary with item_type="area"]
✅ Area Summary:
   - Living Room: 15 entities
   - Kitchen: 12 entities
   ...

User: "Get summary for the Living Room area"
Claude: [Uses get_item_summary with item_type="area", item_id="living_room"]
✅ Living Room Summary:
   - Total entities: 15
   - Domains: light (5), switch (3), sensor (7)
```

## Areas Tools

### `list_areas`

List all areas in your Home Assistant instance.

**Example Usage:**
```
User: "What areas are configured in my Home Assistant?"
Claude: [Uses list_areas via list_items with item_type="area"]
✅ Areas:
- Living Room
- Kitchen
- Bedroom
...
```

### `create_area` / `update_area` / `delete_area`

Manage areas in Home Assistant (via `manage_item` unified tool).

**Parameters:**
- `action` (required): Action to perform (`"create"`, `"update"`, or `"delete"`)
- `item_type` (required): Set to `"area"`
- `item_id` (required for update/delete): The area ID
- `config` (required): Area configuration with `name`, `aliases`, `picture`

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
