# Helpers Tools

Manage Home Assistant helpers (input booleans, numbers, text, selects, counters, timers, etc.).

## Available Tools

### `list_helpers`

List all helpers in Home Assistant.

**Parameters:**
- `helper_type` (optional): Filter by type (e.g., `input_boolean`, `input_number`)

**Example Usage:**
```
User: "Show me all my helpers"
Claude: [Uses list_helpers]
✅ Helpers:
- input_boolean.work_from_home (on)
- input_number.temperature_setpoint (22.5)
- input_text.name ("John")
...
```

### `get_helper`

Get detailed information about a helper.

**Parameters:**
- `helper_id` (required): The helper entity ID or name

**Example Usage:**
```
User: "What's the value of input_boolean.work_from_home?"
Claude: [Uses get_helper]
✅ input_boolean.work_from_home:
   State: on
   Friendly Name: Work From Home
```

### `update_helper`

Update a helper's value.

**Parameters:**
- `helper_id` (required): The helper entity ID
- `value` (required): The value to set (format depends on helper type)

**Helper Type Specific Values:**

- **input_boolean**: `true`/`false` or `"on"`/`"off"`
- **input_number**: Numeric value (float)
- **input_text**: String value
- **input_select**: Option string (must match available options)
- **counter**: Integer value, or `"+"` to increment, `"-"` to decrement
- **timer**: `"start"`, `"pause"`, or `"cancel"`
- **input_button**: Any value (triggers press action)

**Example Usage:**
```
User: "Set input_boolean.work_from_home to true"
Claude: [Uses update_helper]
✅ Helper updated successfully

User: "Increment counter.steps"
Claude: [Uses update_helper with value="+"]
✅ Counter incremented

User: "Start timer.countdown"
Claude: [Uses update_helper with value="start"]
✅ Timer started
```

## Helper Types

### Input Boolean

Toggle boolean values on/off.

```
"Set work_from_home to on"
"Turn off input_boolean.guest_mode"
```

### Input Number

Store numeric values with min/max constraints.

```
"Set temperature_setpoint to 22.5"
"Update volume_level to 75"
```

### Input Text

Store text strings.

```
"Set input_text.name to 'John'"
"Update input_text.message to 'Hello'"
```

### Input Select

Select from predefined options.

```
"Set input_select.mode to 'Away'"
"Change input_select.location to 'Living Room'"
```

### Counter

Increment/decrement counters.

```
"Increment counter.steps"
"Set counter.days to 30"
"Decrement counter.count"
```

### Timer

Control timers (start, pause, cancel).

```
"Start timer.countdown"
"Pause timer.break_timer"
"Cancel timer.alarm"
```

### Input Button

Trigger button actions.

```
"Press input_button.reset"
```

## Use Cases

### Helper Management

```
"List all my input booleans"
"Show me the value of input_number.temperature"
"Set input_boolean.vacation_mode to true"
```

### Automation Helpers

```
"Increment counter.daily_steps"
"Update input_text.reminder to 'Take medication'"
"Change input_select.location to 'Office'"
```
