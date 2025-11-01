# Best Practices

This guide covers best practices for using Hass-MCP effectively and efficiently.

## Token Efficiency

Hass-MCP is designed to minimize token usage while providing comprehensive functionality:

### Use Lean Format

When listing entities, use the lean format (default):

```
✅ Good: "List all lights" (uses lean format automatically)
❌ Avoid: "List all lights with detailed=True" (unless you need all attributes)
```

### Filter by Domain

Use domain filters to narrow results:

```
✅ Good: "List all lights" (only returns lights)
❌ Avoid: "List all entities" then filter manually
```

### Use Specific Searches

When looking for specific entities, use search:

```
✅ Good: "Search for entities with 'temperature' in the name"
❌ Avoid: "List all entities" then search manually
```

### Limit Results

When listing entities, specify limits:

```
✅ Good: "List the first 20 lights"
❌ Avoid: "List all lights" when you have 100+ lights
```

## Error Handling

### Check Entity Existence

Before performing actions, verify entities exist:

```
✅ Good: "Check if light.living_room exists, then turn it on"
❌ Avoid: "Turn on light.living_room" without checking
```

### Handle Errors Gracefully

All tools include error handling:

- Invalid entity IDs return clear error messages
- Connection issues are reported with actionable guidance
- Missing permissions are identified and explained

### Verify Actions

After performing actions, verify they succeeded:

```
✅ Good: "Turn on light.living_room and check its state"
❌ Avoid: "Turn on light.living_room" without verification
```

## Security

### Token Management

- **Never share your `HA_TOKEN`** - it provides full access to Home Assistant
- **Use environment variables** or secure configuration management
- **Rotate tokens regularly** (every 90 days recommended)
- **Grant only necessary permissions** when creating tokens

### Network Security

- **Use HTTPS** for remote Home Assistant instances
- **Use VPN** for remote access when possible
- **Limit token permissions** to only what's needed
- **Review access logs** periodically

## Performance

### Batch Operations

When possible, batch similar operations:

```
✅ Good: "List all lights, then turn on the first 10"
❌ Avoid: "Turn on light 1, turn on light 2, ..." (multiple separate calls)
```

### Cache Results

When appropriate, cache results from list operations:

```
✅ Good: "List all automations once, then reference them"
❌ Avoid: "List automations" multiple times in the same conversation
```

### Use Appropriate Tools

Choose the right tool for the task:

```
✅ Good: Use `entity_action` for simple on/off/toggle
✅ Good: Use `call_service` for advanced service calls
❌ Avoid: Using `call_service` when `entity_action` would work
```

## Workflow Patterns

### Discovery First

When exploring your Home Assistant instance:

1. Start with `system_overview` for a high-level view
2. Use `list_entities` with domain filters for specific types
3. Use `get_entity` for detailed information when needed

### Troubleshooting Pattern

When troubleshooting issues:

1. Use `get_entity` or `diagnose_entity` to check current state
2. Use `get_history` or `get_entity_logbook` to review recent changes
3. Use `get_error_log` to check for related errors
4. Use appropriate tools to fix identified issues

### Automation Management Pattern

When managing automations:

1. Use `list_automations` to see all automations
2. Use `get_automation_config` to review configuration
3. Use `get_automation_execution_log` to check execution history
4. Use appropriate tools to modify or troubleshoot

## Common Patterns

### "Show Me" Pattern

```
"Show me all [entity type] in [area]"
"Show me the state of [entity]"
"Show me recent [events/logs/errors]"
```

### "Control" Pattern

```
"Turn on/off [entity]"
"Set [entity] to [value]"
"Activate [scene/script]"
```

### "Analyze" Pattern

```
"Analyze [entities/automations/usage]"
"Diagnose [entity/automation]"
"Troubleshoot [issue]"
```

## Tips for Effective Conversations

### Be Specific

```
✅ Good: "Turn on light.living_room at 80% brightness"
❌ Vague: "Turn on some lights"
```

### Provide Context

```
✅ Good: "The living room lights aren't working, help me troubleshoot"
❌ Less helpful: "Something's broken"
```

### Use Natural Language

```
✅ Good: "Turn on the living room lights"
✅ Good: "What's the temperature in the bedroom?"
❌ Technical: "Call light.turn_on service with entity_id light.living_room"
```

### Break Down Complex Tasks

```
✅ Good:
  1. "First, list all my automations"
  2. "Then show me the configuration of Morning Routine"
  3. "Finally, help me debug why it's not working"
❌ Complex: "Debug my Morning Routine automation and fix all related issues"
```
