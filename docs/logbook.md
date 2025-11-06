# Logbook Tools

Query and search the Home Assistant logbook for historical events.

## Available Tools

### `get_logbook` (Unified Tool)

Unified logbook tool that replaces `get_logbook`, `get_entity_logbook`, and `search_logbook`. Supports filtering by entity, search query, and timestamp.

**Parameters:**
- `entity_id` (optional): Filter logbook entries by entity ID
- `search_query` (optional): Search query to filter logbook entries
- `timestamp` (optional): Timestamp to start from (ISO format)
- `hours` (optional): Number of hours of history to retrieve (default: 24)

**Example Usage:**
```
User: "Show me logbook entries for the last 24 hours"
Claude: [Uses get_logbook]
✅ Logbook Entries:
- 10:30 - light.living_room turned on
- 10:25 - switch.kitchen turned off
...

User: "Show me logbook entries for light.living_room"
Claude: [Uses get_logbook with entity_id="light.living_room"]
✅ Logbook for light.living_room:
- 10:30 - turned on
- 09:15 - turned off
...

User: "Search logbook for 'light' events"
Claude: [Uses get_logbook with search_query="light"]
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
