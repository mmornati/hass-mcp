# Calendars Tools

Manage calendar entities and events in Home Assistant.

## Available Tools

### `list_calendars`

List all calendar entities.

**Example Usage:**
```
User: "What calendars do I have?"
Claude: [Uses list_calendars]
✅ Calendars:
- calendar.google (Google Calendar)
- calendar.local (Local Calendar)
...
```

### `get_calendar_events`

Get events from a calendar for a date range.

**Parameters:**
- `entity_id` (required): The calendar entity ID
- `start_date` (required): Start date in ISO 8601 format (e.g., `2025-01-01` or `2025-01-01T00:00:00`)
- `end_date` (required): End date in ISO 8601 format

**Example Usage:**
```
User: "Show me events from calendar.google for the next week"
Claude: [Uses get_calendar_events]
✅ Calendar Events:
- 2025-01-16 10:00 - Meeting
- 2025-01-17 14:00 - Doctor Appointment
...
```

### `create_calendar_event`

Create a new calendar event.

**Parameters:**
- `entity_id` (required): The calendar entity ID
- `summary` (required): Event title/summary
- `start` (required): Start date/time in ISO 8601 format
- `end` (required): End date/time in ISO 8601 format
- `description` (optional): Event description

**Example Usage:**
```
User: "Create a calendar event for a meeting tomorrow at 10 AM"
Claude: [Uses create_calendar_event]
✅ Event created successfully:
   Title: Meeting
   Start: 2025-01-16T10:00:00
   End: 2025-01-16T11:00:00
```

## Use Cases

### Calendar Queries

```
"What events do I have today?"
"Show me calendar events for next week"
"List all events from calendar.google"
```

### Event Management

```
"Create a calendar event for a doctor appointment tomorrow"
"Add an event to my calendar for the weekend"
"Create an all-day event for my birthday"
```

## Date Formats

Dates can be provided in ISO 8601 format:

- **Date only**: `2025-01-01` (for all-day events)
- **Date and time**: `2025-01-01T10:00:00`
- **With timezone**: `2025-01-01T10:00:00+00:00`

If only a date is provided, times default to:
- Start: `00:00:00`
- End: `23:59:59`
