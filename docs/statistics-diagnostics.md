# Statistics & Diagnostics Tools

Analyze usage patterns, troubleshoot issues, and diagnose problems in your Home Assistant instance.

## Statistics Tools

### `get_statistics` (Unified Tool)

Unified statistics tool that replaces `get_entity_statistics`, `get_domain_statistics`, and `analyze_usage_patterns`.

**Parameters:**
- `type` (required): Type of statistics. Options:
  - `"entity"`: Get statistics for a specific entity (requires `entity_id`)
  - `"domain"`: Get statistics for a domain (requires `domain`)
  - `"usage_patterns"`: Analyze usage patterns for an entity (requires `entity_id`)
- `entity_id` (optional): Entity ID (required for `"entity"` and `"usage_patterns"` types)
- `domain` (optional): Domain name (required for `"domain"` type)
- `period_days` (optional): Number of days to analyze (default: 7, used for `"entity"` and `"domain"`)
- `days` (optional): Number of days to analyze (default: 30, used for `"usage_patterns"`)

**Example Usage:**
```
User: "Show me temperature statistics for the last week"
Claude: [Uses get_statistics with type="entity", entity_id="sensor.temperature", period_days=7]
✅ Temperature Statistics (7 days):
   Average: 22.5°C
   Min: 18.2°C
   Max: 26.1°C
   Trend: Stable

User: "Get statistics for all sensors"
Claude: [Uses get_statistics with type="domain", domain="sensor", period_days=7]
✅ Sensor Domain Statistics:
   - Total entities: 45
   - Average values per entity
   - Min/Max ranges

User: "Analyze usage patterns for light.living_room"
Claude: [Uses get_statistics with type="usage_patterns", entity_id="light.living_room", days=30]
✅ Usage Patterns:
   - Peak hour: 18:00 (evening)
   - Peak day: Friday
   - Total events: 234
```

## Diagnostics Tools

### `diagnose` (Unified Tool)

Unified diagnostics tool that replaces `diagnose_entity`, `check_entity_dependencies`, `analyze_automation_conflicts`, and `get_integration_errors`.

**Parameters:**
- `type` (required): Type of diagnostics. Options:
  - `"entity"`: Diagnose a specific entity (requires `entity_id`)
  - `"dependencies"`: Check entity dependencies (requires `entity_id`)
  - `"automation_conflicts"`: Analyze automation conflicts
  - `"integration_errors"`: Get integration errors (optional `domain` filter)
- `entity_id` (optional): Entity ID (required for `"entity"` and `"dependencies"` types)
- `domain` (optional): Domain filter for `"integration_errors"` type

**Example Usage:**
```
User: "Why is sensor.temperature showing as unavailable?"
Claude: [Uses diagnose with type="entity", entity_id="sensor.temperature"]
🔍 Diagnostic Results:
   - State: unavailable
   - Last update: 2 hours ago
   - Related device: Living Room Device
   - Error: Connection timeout
   - Suggestion: Check device connectivity

User: "Check dependencies for light.living_room"
Claude: [Uses diagnose with type="dependencies", entity_id="light.living_room"]
✅ Dependencies:
   - Used by 3 automations
   - Used by 1 script
   - Used by 2 scenes

User: "What automations might be conflicting?"
Claude: [Uses diagnose with type="automation_conflicts"]
⚠️ Found 2 conflicts:
   - Automation A and B both control light.living_room
   - Suggestion: Review trigger conditions

User: "Show me integration errors for MQTT"
Claude: [Uses diagnose with type="integration_errors", domain="mqtt"]
⚠️ Integration Errors:
   - Connection failed at 10:30
   - Reconnection timeout at 09:15
```

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
