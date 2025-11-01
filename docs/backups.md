# Backups Tools

Manage Home Assistant backups via the Supervisor API.

## Available Tools

### `list_backups`

List all available backups.

**Example Usage:**
```
User: "Show me my Home Assistant backups"
Claude: [Uses list_backups]
✅ Backups:
- 2025-01-15 12:00 (Full Backup) - 2.3 GB
- 2025-01-14 12:00 (Full Backup) - 2.3 GB
...
```

### `create_backup`

Create a new backup.

**Parameters:**
- `name` (optional): Backup name
- `password` (optional): Backup password
- `addons` (optional): Include addons
- `folders` (optional): Include folders

**Example Usage:**
```
User: "Create a backup of my Home Assistant instance"
Claude: [Uses create_backup]
✅ Backup created successfully:
   Name: backup_2025-01-15
   Size: 2.3 GB
```

### `restore_backup`

Restore a backup.

**Parameters:**
- `slug` (required): Backup slug/ID

**Example Usage:**
```
User: "Restore backup from yesterday"
Claude: [Uses restore_backup]
⚠️ Restoring backup... This may take several minutes.
```

### `delete_backup`

Delete a backup.

**Parameters:**
- `slug` (required): Backup slug/ID

**Example Usage:**
```
User: "Delete the backup from last week"
Claude: [Uses delete_backup]
✅ Backup deleted successfully
```

## Use Cases

### Backup Management

```
"List all my backups"
"Create a new backup"
"Delete old backups"
```

### Restore Operations

```
"Restore the backup from yesterday"
"Show me available backups to restore"
```

## Important Notes

⚠️ **Restoring a backup will replace your current Home Assistant configuration and may take several minutes.**

- Always create a backup before making major changes
- Verify backup integrity before restoring
- Restore operations require Supervisor API access
