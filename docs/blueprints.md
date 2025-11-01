# Blueprints Tools

Import and use automation blueprints in Home Assistant.

## Available Tools

### `list_blueprints`

List all available blueprints.

**Example Usage:**
```
User: "What blueprints are available?"
Claude: [Uses list_blueprints]
✅ Blueprints:
- motion_light.yaml
- notify_on_state_change.yaml
...
```

### `get_blueprint`

Get detailed information about a blueprint.

**Parameters:**
- `blueprint_id` (required): The blueprint ID or path

### `import_blueprint`

Import a blueprint into Home Assistant.

**Parameters:**
- `blueprint_url` (required): URL or path to the blueprint

### `create_automation_from_blueprint`

Create an automation from a blueprint.

**Parameters:**
- `blueprint_id` (required): The blueprint ID
- `automation_id` (required): ID for the new automation
- `config` (required): Automation configuration matching the blueprint

**Example Usage:**
```
User: "Create an automation from the motion_light blueprint"
Claude: [Uses create_automation_from_blueprint]
✅ Automation created from blueprint
```

## Use Cases

### Blueprint Management

```
"List available blueprints"
"Import a blueprint from a URL"
"Show me the motion_light blueprint"
```

### Automation Creation

```
"Create an automation from the notify_on_state_change blueprint"
"Use a blueprint to create a motion sensor automation"
```
