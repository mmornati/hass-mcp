# Templates Tools

Test Jinja2 templates in Home Assistant.

## Available Tools

### `test_template`

Test a Jinja2 template.

**Parameters:**
- `template` (required): The Jinja2 template string

**Example Usage:**
```
User: "Test the template: '{{ states('light.living_room') }}'"
Claude: [Uses test_template]
✅ Template Result: "on"
```

**Common Template Examples:**

```
"Test: 'The temperature is {{ states('sensor.temperature') }}°C'"
"Evaluate: '{{ states.light | selectattr('state', 'eq', 'on') | list | length }} lights are on'"
"Check: '{{ now().strftime('%Y-%m-%d %H:%M:%S') }}'"
```

## Use Cases

### Template Testing

```
"Test this template: '{{ states('sensor.temperature') }}'"
"Evaluate a Jinja2 expression"
"Check if my template is working correctly"
```

### Template Development

```
"Help me write a template that shows the number of lights on"
"Test a template before using it in an automation"
```
