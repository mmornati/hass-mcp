# Zones Tools

Manage zones for location tracking in Home Assistant.

## Available Tools

### `list_zones`

List all zones.

**Example Usage:**
```
User: "What zones do I have configured?"
Claude: [Uses list_zones]
✅ Zones:
- Home (52.5200, 13.4050)
- Work (52.5300, 13.4100)
...
```

### `create_zone`

Create a new zone.

**Parameters:**
- `zone_id` (required): Unique zone ID
- `name` (required): Zone name
- `latitude` (required): Latitude
- `longitude` (required): Longitude
- `radius` (optional): Zone radius in meters

**Example Usage:**
```
User: "Create a zone called 'Gym' at coordinates 52.5400, 13.4200"
Claude: [Uses create_zone]
✅ Zone created successfully
```

### `update_zone`

Update an existing zone.

**Parameters:**
- `zone_id` (required): The zone ID to update
- `name` (optional): New zone name
- `latitude` (optional): New latitude
- `longitude` (optional): New longitude
- `radius` (optional): New radius

### `delete_zone`

Delete a zone.

**Parameters:**
- `zone_id` (required): The zone ID to delete

## Use Cases

### Zone Management

```
"List all my zones"
"Create a zone for the gym"
"Update the Home zone location"
"Delete the old Work zone"
```
