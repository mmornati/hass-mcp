# Events Tools

Fire custom events and manage event types in Home Assistant.

## Available Tools

### `manage_events` (Unified Tool)

Unified events tool that replaces `fire_event`, `list_event_types`, and `get_events`.

**Parameters:**
- `action` (required): Action to perform. Options:
  - `"fire"`: Fire a custom event (requires `event_type`)
  - `"list_types"`: List common event types
  - `"get"`: Get recent events (optional `entity_id` filter)
- `event_type` (optional): Event type name (required for `"fire"` action)
- `event_data` (optional): Event data/payload (for `"fire"` action)
- `entity_id` (optional): Entity ID to filter events (for `"get"` action)
- `hours` (optional): Number of hours of history to retrieve (default: 1, for `"get"` action)

**Example Usage:**
```
User: "Fire a custom event called 'test_event' with data {'value': 123}"
Claude: [Uses manage_events with action="fire", event_type="test_event", event_data={"value": 123}]
✅ Event fired successfully

User: "What event types are available?"
Claude: [Uses manage_events with action="list_types"]
✅ Event Types:
- state_changed
- automation_triggered
- custom_event
...

User: "Show me recent events for light.living_room"
Claude: [Uses manage_events with action="get", entity_id="light.living_room", hours=24]
✅ Recent Events:
- 2025-01-15 10:30 - state_changed (light.living_room)
- 2025-01-15 10:29 - state_changed (light.living_room)
...
```

## Use Cases

### Event Firing

```
"Fire a custom event called 'motion_detected'"
"Trigger event 'door_opened' with data {'door': 'front'}"
```

### Event Monitoring

```
"What events have occurred recently?"
"Show me all state_changed events"
"List all available event types"
```
