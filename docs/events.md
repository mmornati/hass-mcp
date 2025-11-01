# Events Tools

Fire custom events and manage event types in Home Assistant.

## Available Tools

### `fire_event`

Fire a custom event.

**Parameters:**
- `event_type` (required): The event type
- `event_data` (optional): Event data dictionary

**Example Usage:**
```
User: "Fire a custom event called 'test_event' with data {'value': 123}"
Claude: [Uses fire_event]
✅ Event fired successfully
```

### `list_event_types`

List all event types in Home Assistant.

**Example Usage:**
```
User: "What event types are available?"
Claude: [Uses list_event_types]
✅ Event Types:
- state_changed
- automation_triggered
- custom_event
...
```

### `get_events`

Get recent events.

**Parameters:**
- `event_type` (optional): Filter by event type
- `limit` (optional): Number of events to return

**Example Usage:**
```
User: "Show me recent state_changed events"
Claude: [Uses get_events]
✅ Recent Events:
- 2025-01-15 10:30 - state_changed (light.living_room)
- 2025-01-15 10:29 - state_changed (switch.kitchen)
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
