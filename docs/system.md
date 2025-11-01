# System Tools

System tools provide information about your Home Assistant instance - version, health, configuration, logs, and system overview.

## Available Tools

### `get_version`

Get the Home Assistant version.

**Example Usage:**
```
User: "What version of Home Assistant am I running?"
Claude: [Uses get_version]
✅ Home Assistant version: 2025.3.0
```

### `system_overview`

Get a comprehensive overview of your Home Assistant system.

**Returns:**
- Total number of entities
- Entities by domain
- Sample entities for each domain
- System version

**Example Usage:**
```
User: "Give me an overview of my Home Assistant system"
Claude: [Uses system_overview]
✅ System Overview:
   - Total Entities: 156
   - Domains: light (23), switch (15), sensor (45)...
   - Version: 2025.3.0
```

### `system_health`

Check the health status of Home Assistant components.

**Returns:**
- Health status of various components
- Version information
- Component availability

**Example Usage:**
```
User: "Is my Home Assistant system healthy?"
Claude: [Uses system_health]
✅ System Health Check:
   - Home Assistant: Healthy
   - Supervisor: Healthy
   - All components operational
```

### `core_config`

Get core configuration information.

**Returns:**
- Location name
- Timezone
- Unit system
- Loaded components
- Version

**Example Usage:**
```
User: "What's my Home Assistant configuration?"
Claude: [Uses core_config]
✅ Core Configuration:
   - Location: Home
   - Timezone: America/New_York
   - Unit System: Imperial
   - Loaded Components: 45
```

### `get_error_log`

Retrieve Home Assistant error logs.

**Parameters:**
- `limit` (optional): Number of log entries (default: 50)

**Example Usage:**
```
User: "Show me the recent errors in my Home Assistant logs"
Claude: [Uses get_error_log]
⚠️ Recent Errors:
   1. [2025-01-15 10:30] Integration 'mqtt' - Connection failed
   2. [2025-01-15 09:15] Entity 'sensor.temperature' unavailable
```

### `get_history`

Get entity state history.

**Parameters:**
- `entity_id` (required): The entity ID
- `hours` (optional): Number of hours of history (default: 24)

**Example Usage:**
```
User: "Show me the temperature history for the last 48 hours"
Claude: [Uses get_history]
📊 Temperature History (48h):
   07:00 - 22.5°C
   08:00 - 23.1°C
   ...
```

### `domain_summary`

Get a summary of entities in a specific domain.

**Parameters:**
- `domain` (required): Domain to summarize, e.g., `light`, `sensor`

**Returns:**
- Total count of entities
- State distribution
- Example entities
- Common attributes

**Example Usage:**
```
User: "Summarize all my light entities"
Claude: [Uses domain_summary]
💡 Light Domain Summary:
   - Total Lights: 23
   - States: on (15), off (8)
   - Examples: light.living_room, light.kitchen...
```

### `restart_ha`

Restart Home Assistant (use with caution).

**Example Usage:**
```
User: "Restart Home Assistant"
Claude: [Uses restart_ha]
⚠️ Restarting Home Assistant...
   This may take a few minutes.
```

## Use Cases

### System Monitoring

```
"What's the current status of my Home Assistant system?"
"Show me system health"
"Check for recent errors"
```

### Configuration Review

```
"What's my Home Assistant configuration?"
"What timezone is my system using?"
"List all loaded components"
```

### Troubleshooting

```
"Show me recent errors"
"Check the history of sensor.temperature"
"Summarize all sensor entities"
```
