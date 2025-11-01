# Integrations Tools

Manage Home Assistant integrations - list, configure, and reload them.

## Available Tools

### `list_integrations`

List all configured integrations.

**Example Usage:**
```
User: "What integrations are configured in my Home Assistant?"
Claude: [Uses list_integrations]
✅ Integrations:
- MQTT (loaded)
- Philips Hue (loaded)
- TP-Link (loaded)
...
```

### `get_integration_config`

Get detailed configuration for a specific integration.

**Parameters:**
- `entry_id` (required): The integration entry ID

**Returns:**
- Integration domain
- Configuration details
- State (loaded, setup_error, etc.)
- Options and preferences

**Example Usage:**
```
User: "Show me the MQTT integration configuration"
Claude: [Uses get_integration_config]
✅ MQTT Integration:
   State: loaded
   Config: ...
```

### `reload_integration`

Reload an integration.

**Parameters:**
- `entry_id` (required): The integration entry ID to reload

**Example Usage:**
```
User: "Reload the MQTT integration"
Claude: [Uses reload_integration]
✅ Integration 'MQTT' reloaded
```

## Use Cases

### Integration Management

```
"List all my integrations"
"Show me the configuration for Philips Hue"
"Reload the TP-Link integration"
```

### Troubleshooting

```
"What's the status of my MQTT integration?"
"Check the configuration for the Zigbee integration"
"Show me integrations with errors"
```
