# Logbook Tools

Query and search the Home Assistant logbook for historical events.

## Available Tools

### `get_logbook`

Get logbook entries for a time period.

**Parameters:**
- `hours` (optional): Number of hours of history (default: 24)
- `entity_id` (optional): Filter by entity ID

**Example Usage:**
```
User: "Show me logbook entries for the last 24 hours"
Claude: [Uses get_logbook]
✅ Logbook Entries:
- 10:30 - light.living_room turned on
- 10:25 - switch.kitchen turned off
...
```

### `get_entity_logbook`

Get logbook entries for a specific entity.

**Parameters:**
- `entity_id` (required): The entity ID
- `hours` (optional): Number of hours of history

**Example Usage:**
```
User: "Show me logbook entries for light.living_room"
Claude: [Uses get_entity_logbook]
✅ Logbook for light.living_room:
- 10:30 - turned on
- 09:15 - turned off
...
```

### `search_logbook`

Search logbook entries by query.

**Parameters:**
- `query` (required): Search query string
- `hours` (optional): Number of hours to search

**Example Usage:**
```
User: "Search logbook for 'light' events"
Claude: [Uses search_logbook]
✅ Found 45 logbook entries matching 'light'
```

## Use Cases

### Historical Review

```
"Show me what happened in the last 24 hours"
"Get logbook entries for yesterday"
"What happened to light.living_room today?"
```

### Troubleshooting

```
"Search logbook for 'error'"
"Show me logbook entries for sensor.temperature"
"What events occurred around 10 AM today?"
```
