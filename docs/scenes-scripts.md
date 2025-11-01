# Scenes & Scripts Tools

Manage scenes and scripts in your Home Assistant instance.

## Scenes Tools

### `list_scenes`

List all scenes in Home Assistant.

**Example Usage:**
```
User: "Show me all my scenes"
Claude: [Uses list_scenes]
✅ Scenes:
- Morning Scene
- Night Mode
- Movie Time
...
```

### `get_scene`

Get detailed information about a scene.

**Parameters:**
- `scene_id` (required): The scene ID (without `scene.` prefix)

### `create_scene`

Create a new scene.

**Parameters:**
- `scene_id` (required): Unique scene ID
- `config` (required): Scene configuration

### `activate_scene`

Activate a scene.

**Parameters:**
- `scene_id` (required): The scene ID to activate

**Example Usage:**
```
User: "Activate the Night Mode scene"
Claude: [Uses activate_scene]
✅ Scene 'Night Mode' activated
```

### `reload_scenes`

Reload all scenes from configuration.

## Scripts Tools

### `list_scripts`

List all scripts in Home Assistant.

**Example Usage:**
```
User: "What scripts do I have?"
Claude: [Uses list_scripts]
✅ Scripts:
- Morning Routine
- Cleanup
- Backup Script
...
```

### `get_script`

Get detailed information about a script.

**Parameters:**
- `script_id` (required): The script ID (without `script.` prefix)

### `run_script`

Execute a script.

**Parameters:**
- `script_id` (required): The script ID to run

**Example Usage:**
```
User: "Run the Morning Routine script"
Claude: [Uses run_script]
✅ Script 'Morning Routine' executed
```

### `reload_scripts`

Reload all scripts from configuration.

## Use Cases

### Scene Management

```
"List all my scenes"
"Show me what's in the 'Morning Scene'"
"Activate the Movie Time scene"
"Create a new scene for reading"
```

### Script Management

```
"What scripts are available?"
"Show me the Morning Routine script configuration"
"Run the backup script"
```
