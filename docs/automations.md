# Automations Tools

Automation tools allow you to manage Home Assistant automations - list, create, update, enable/disable, trigger, and troubleshoot them.

## Available Tools

### `list_automations`

List all automations in your Home Assistant instance.

**Example Usage:**
```
User: "Show me all my automations"
Claude: [Uses list_automations]
✅ Found 12 automations:
- Morning Routine (enabled)
- Night Mode (disabled)
- Temperature Alert (enabled)
...
```

### `get_automation_config`

Get the complete configuration of an automation including triggers, conditions, and actions.

**Parameters:**
- `automation_id` (required): The automation ID (without `automation.` prefix)

**Example Usage:**
```
User: "Show me the configuration of the 'Morning Routine' automation"
Claude: [Uses get_automation_config]
✅ Morning Routine Configuration:
   Trigger: Time at 07:00
   Condition: Workday
   Actions:
     - Turn on lights
     - Adjust thermostat
```

### `create_automation`

Create a new automation.

**Parameters:**
- `automation_id` (required): Unique ID for the automation
- `config` (required): Complete automation configuration (triggers, conditions, actions)

**Example Usage:**
```
User: "Create an automation that turns on the lights when motion is detected"
Claude: [Uses create_automation with appropriate config]
✅ Automation 'motion_lights' created successfully
```

### `update_automation`

Update an existing automation's configuration.

**Parameters:**
- `automation_id` (required): The automation ID to update
- `config` (required): Updated automation configuration

### `delete_automation`

Delete an automation.

**Parameters:**
- `automation_id` (required): The automation ID to delete

### `enable_automation` / `disable_automation`

Enable or disable an automation without deleting it.

**Parameters:**
- `automation_id` (required): The automation ID

**Example Usage:**
```
User: "Disable the 'Night Mode' automation"
Claude: [Uses disable_automation]
✅ Automation 'Night Mode' disabled
```

### `trigger_automation`

Manually trigger an automation.

**Parameters:**
- `automation_id` (required): The automation ID to trigger

**Example Usage:**
```
User: "Run the 'Morning Routine' automation now"
Claude: [Uses trigger_automation]
✅ Automation 'Morning Routine' triggered successfully
```

### `get_automation_execution_log`

Get the execution history of an automation.

**Parameters:**
- `automation_id` (required): The automation ID
- `limit` (optional): Number of log entries to return (default: 10)

**Example Usage:**
```
User: "Show me the last 5 executions of 'Morning Routine'"
Claude: [Uses get_automation_execution_log]
✅ Last 5 executions:
   1. 2025-01-15 07:00:00 - Success
   2. 2025-01-14 07:00:00 - Success
...
```

### `validate_automation_config`

Validate an automation configuration before creating it.

**Parameters:**
- `config` (required): Automation configuration to validate

## Use Cases

### Automation Management

```
"List all disabled automations"
"Show me the configuration of the 'Vacation Mode' automation"
"Enable all automations related to lighting"
```

### Creating Automations

```
"Create an automation that turns on lights when motion is detected at night"
"Make an automation that alerts me if temperature goes above 25°C"
"Create a morning routine that gradually increases light brightness"
```

### Troubleshooting

```
"Why is the 'Night Mode' automation not running?"
"Show me recent failures for 'Temperature Alert'"
"Validate this automation configuration before creating it"
```
