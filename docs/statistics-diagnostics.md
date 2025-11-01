# Statistics & Diagnostics Tools

Analyze usage patterns, troubleshoot issues, and diagnose problems in your Home Assistant instance.

## Statistics Tools

### `get_entity_statistics`

Get statistics for a specific entity over time.

**Parameters:**
- `entity_id` (required): The entity ID
- `hours` (optional): Number of hours of statistics (default: 24)

**Example Usage:**
```
User: "Show me temperature statistics for the last week"
Claude: [Uses get_entity_statistics]
✅ Temperature Statistics (168h):
   Average: 22.5°C
   Min: 18.2°C
   Max: 26.1°C
   Trend: Stable
```

### `get_domain_statistics`

Get statistics for all entities in a domain.

**Parameters:**
- `domain` (required): Domain to analyze, e.g., `sensor`, `light`
- `hours` (optional): Number of hours of statistics

### `analyze_usage_patterns`

Analyze usage patterns across entities.

**Parameters:**
- `domain` (optional): Filter by domain
- `hours` (optional): Time period to analyze

## Diagnostics Tools

### `diagnose_entity`

Diagnose issues with a specific entity.

**Parameters:**
- `entity_id` (required): The entity ID to diagnose

**Returns:**
- Current state and attributes
- Related devices and areas
- Recent state changes
- Error messages (if any)
- Suggestions for resolution

**Example Usage:**
```
User: "Why is sensor.temperature showing as unavailable?"
Claude: [Uses diagnose_entity]
🔍 Diagnostic Results:
   - State: unavailable
   - Last update: 2 hours ago
   - Related device: Living Room Device
   - Error: Connection timeout
   - Suggestion: Check device connectivity
```

### `check_entity_dependencies`

Check dependencies for an entity.

**Parameters:**
- `entity_id` (required): The entity ID

**Returns:**
- Related entities
- Dependencies
- Automation dependencies
- Script dependencies

### `analyze_automation_conflicts`

Analyze potential conflicts between automations.

**Returns:**
- Conflicting automations
- Overlapping triggers
- Conflicting actions
- Suggestions for resolution

### `get_integration_errors`

Get errors from specific integrations.

**Parameters:**
- `domain` (optional): Integration domain to check

**Returns:**
- Error messages
- Timestamps
- Related entities
- Suggestions for resolution

## Use Cases

### Statistics Analysis

```
"Show me energy usage statistics for the last month"
"What's the average temperature in the living room?"
"Analyze usage patterns for my lights"
```

### Troubleshooting

```
"Diagnose why sensor.temperature is unavailable"
"Check dependencies for light.living_room"
"Show me integration errors for MQTT"
"What automations might be conflicting?"
```

### Performance Analysis

```
"Analyze entity statistics for the sensor domain"
"Show me usage patterns for my switches"
"Get statistics for all climate entities"
```
