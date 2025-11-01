# Tags Tools

Manage RFID/NFC tags used for triggering automations in Home Assistant.

## Available Tools

### `list_tags`

List all RFID/NFC tags.

**Example Usage:**
```
User: "What tags do I have configured?"
Claude: [Uses list_tags]
✅ Tags:
- ABC123 (Front Door Key)
- XYZ789 (Office Access Card)
...
```

### `create_tag`

Create a new tag.

**Parameters:**
- `tag_id` (required): Unique tag ID (e.g., `ABC123`)
- `name` (required): Display name for the tag

**Example Usage:**
```
User: "Create a new tag called 'Garage Key' with ID 'DEF456'"
Claude: [Uses create_tag]
✅ Tag created successfully
```

### `delete_tag`

Delete a tag.

**Parameters:**
- `tag_id` (required): The tag ID to delete

### `get_tag_automations`

Find automations triggered by a specific tag.

**Parameters:**
- `tag_id` (required): The tag ID

**Example Usage:**
```
User: "What automations are triggered by tag ABC123?"
Claude: [Uses get_tag_automations]
✅ Automations triggered by tag ABC123:
- automation.front_door_unlock (enabled)
- automation.lights_on (enabled)
```

## Use Cases

### Tag Management

```
"List all my tags"
"Create a new tag for the garage"
"Delete tag ABC123"
```

### Automation Dependencies

```
"What automations use tag XYZ789?"
"Show me all tags that trigger automations"
```
