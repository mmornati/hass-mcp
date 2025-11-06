# System Tools

System tools provide information about your Home Assistant instance - version, health, configuration, logs, and system overview.

## Available Tools

### `get_system_info` (Unified Tool)

Unified system info tool that replaces `get_version`, `system_overview`, `system_health`, and `core_config`.

**Parameters:**
- `info_type` (required): Type of system info. Options:
  - `"version"`: Get Home Assistant version
  - `"overview"`: Get comprehensive system overview
  - `"health"`: Get system health information
  - `"config"`: Get core configuration

**Example Usage:**
```
User: "What version of Home Assistant am I running?"
Claude: [Uses get_system_info with info_type="version"]
✅ Home Assistant version: 2025.3.0

User: "Give me an overview of my Home Assistant system"
Claude: [Uses get_system_info with info_type="overview"]
✅ System Overview:
   - Total Entities: 156
   - Domains: light (23), switch (15), sensor (45)...
   - Version: 2025.3.0

User: "Is my Home Assistant system healthy?"
Claude: [Uses get_system_info with info_type="health"]
✅ System Health Check:
   - Home Assistant: Healthy
   - Supervisor: Healthy
   - All components operational

User: "What's my Home Assistant configuration?"
Claude: [Uses get_system_info with info_type="config"]
✅ Core Configuration:
   - Location: Home
   - Timezone: America/New_York
   - Unit System: Imperial
   - Loaded Components: 45
```

### `get_system_data` (Unified Tool)

Unified system data tool that replaces `get_error_log`, `get_cache_statistics`, `get_history`, and `domain_summary`.

**Parameters:**
- `data_type` (required): Type of system data. Options:
  - `"error_log"`: Get error log
  - `"cache_statistics"`: Get cache statistics
  - `"history"`: Get entity history (requires `entity_id`)
  - `"domain_summary"`: Get domain summary (requires `domain`)
- `entity_id` (optional): Entity ID (required for `"history"` type)
- `domain` (optional): Domain name (required for `"domain_summary"` type)

**Example Usage:**
```
User: "Show me the recent errors in my Home Assistant logs"
Claude: [Uses get_system_data with data_type="error_log"]
⚠️ Recent Errors:
   1. [2025-01-15 10:30] Integration 'mqtt' - Connection failed
   2. [2025-01-15 09:15] Entity 'sensor.temperature' unavailable

User: "Get the history for sensor.temperature"
Claude: [Uses get_system_data with data_type="history", entity_id="sensor.temperature"]
✅ Entity History:
   - 2025-01-15 10:00: 22.5°C
   - 2025-01-15 09:00: 22.3°C
   ...

User: "Get a summary of the light domain"
Claude: [Uses get_system_data with data_type="domain_summary", domain="light"]
✅ Light Domain Summary:
   - Total: 23 lights
   - States: on (15), off (8)
   - Examples: light.living_room, light.kitchen
```

### `get_history` (Deprecated - Use `get_system_data`)

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
