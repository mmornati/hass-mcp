# Prompts (Guided Conversations)

Prompts provide guided conversations for common Home Assistant tasks. These are higher-level interactions that combine multiple tools to accomplish complex goals.

## Available Prompts

### `create_automation`

Guided conversation for creating a new automation.

**Example Usage:**
```
User: "I want to create an automation that turns on the lights when motion is detected"
Claude: [Uses create_automation prompt]
🤖 I'll help you create that automation. Let me guide you through the process...
```

### `debug_automation`

Guided conversation for debugging automation issues.

**Example Usage:**
```
User: "Why isn't my Morning Routine automation working?"
Claude: [Uses debug_automation prompt]
🔍 Let me help you debug that automation. I'll check...
```

### `troubleshoot_entity`

Guided conversation for troubleshooting entity issues.

**Example Usage:**
```
User: "sensor.temperature is showing as unavailable, help me fix it"
Claude: [Uses troubleshoot_entity prompt]
🛠️ Let me investigate why that sensor is unavailable...
```

### `routine_optimizer`

Guided conversation for optimizing automations and routines.

**Example Usage:**
```
User: "Help me optimize my automations"
Claude: [Uses routine_optimizer prompt]
⚡ Let me analyze your automations for optimization opportunities...
```

### `automation_health_check`

Guided conversation for checking automation health.

**Example Usage:**
```
User: "Check the health of all my automations"
Claude: [Uses automation_health_check prompt]
💚 Running automation health check...
```

### `entity_naming_consistency`

Guided conversation for checking entity naming consistency.

**Example Usage:**
```
User: "Check if my entities follow consistent naming conventions"
Claude: [Uses entity_naming_consistency prompt]
📝 Analyzing entity naming patterns...
```

### `dashboard_layout_generator`

Guided conversation for generating dashboard layouts.

**Example Usage:**
```
User: "Help me create a dashboard layout for my living room"
Claude: [Uses dashboard_layout_generator prompt]
🎨 Let me help you create an optimal dashboard layout...
```

## How Prompts Work

Prompts are interactive conversations that:

1. **Ask clarifying questions** to understand your needs
2. **Use multiple tools** to gather information
3. **Provide recommendations** based on analysis
4. **Guide you through** complex tasks step-by-step

## Best Practices

1. **Be specific** about what you want to accomplish
2. **Provide context** when possible (entity IDs, automation names, etc.)
3. **Follow the prompts** - they will ask for needed information
4. **Review suggestions** before applying changes
