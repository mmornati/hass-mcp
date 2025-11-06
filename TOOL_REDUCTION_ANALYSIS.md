# Tool Reduction Analysis for Hass-MCP

## Current State

**Total Tools: 92**
- Home Assistant MCP Server: 92 tools
- User reports: 132 tools total (likely includes other MCP servers)

**Prompts: 8**
- create_automation
- debug_automation
- troubleshoot_entity
- routine_optimizer
- automation_health_check
- entity_naming_consistency
- dashboard_layout_generator

**Resources: 5**
- hass://entities/{entity_id}
- hass://entities
- hass://search/{query}/{limit}
- hass://entities/{entity_id}/detailed
- hass://entities/domain/{domain}

## Complete Tool List

### Entity Tools (6 tools)
1. `get_entity` - Get entity state
2. `entity_action` - Control entity (on/off/toggle)
3. `list_entities` - List all entities
4. `search_entities_tool` - Search entities by keyword
5. `semantic_search_entities_tool` - Semantic search for entities
6. `get_entity_suggestions` - Get related entity suggestions

### Query Processing (1 tool)
7. `process_natural_language_query` - Process natural language queries

### Entity Descriptions (2 tools)
8. `generate_entity_description` - Generate entity description
9. `generate_entity_descriptions_batch` - Batch generate descriptions

### Automation Tools (10 tools)
10. `list_automations` - List all automations
11. `get_automation_config` - Get automation configuration
12. `create_automation` - Create new automation
13. `update_automation` - Update existing automation
14. `delete_automation` - Delete automation
15. `enable_automation` - Enable automation
16. `disable_automation` - Disable automation
17. `trigger_automation` - Manually trigger automation
18. `get_automation_execution_log` - Get execution history
19. `validate_automation_config` - Validate automation config

### Script Tools (4 tools)
20. `list_scripts` - List all scripts
21. `get_script` - Get script configuration
22. `run_script` - Execute script
23. `reload_scripts` - Reload script configurations

### Device Tools (4 tools)
24. `list_devices` - List all devices
25. `get_device` - Get device details
26. `get_device_entities` - Get entities for device
27. `get_device_stats` - Get device statistics

### Area Tools (6 tools)
28. `list_areas` - List all areas
29. `get_area_entities` - Get entities in area
30. `create_area` - Create new area
31. `update_area` - Update area
32. `delete_area` - Delete area
33. `get_area_summary` - Get area summary

### Scene Tools (5 tools)
34. `list_scenes` - List all scenes
35. `get_scene` - Get scene configuration
36. `create_scene` - Create new scene
37. `activate_scene` - Activate scene
38. `reload_scenes` - Reload scene configurations

### Integration Tools (3 tools)
39. `list_integrations` - List all integrations
40. `get_integration_config` - Get integration configuration
41. `reload_integration` - Reload integration

### System Tools (9 tools)
42. `get_version` - Get Home Assistant version
43. `system_overview` - Get system overview
44. `get_error_log` - Get error log
45. `system_health` - Get system health
46. `get_cache_statistics` - Get cache statistics
47. `core_config` - Get core configuration
48. `restart_ha` - Restart Home Assistant
49. `get_history` - Get entity history
50. `domain_summary` - Get domain summary

### Service Tools (1 tool)
51. `call_service` - Call any Home Assistant service

### Template Tools (1 tool)
52. `test_template` - Test Jinja2 template

### Logbook Tools (3 tools)
53. `get_logbook` - Get logbook entries
54. `get_entity_logbook` - Get entity logbook
55. `search_logbook` - Search logbook

### Statistics Tools (3 tools)
56. `get_entity_statistics` - Get entity statistics
57. `get_domain_statistics` - Get domain statistics
58. `analyze_usage_patterns` - Analyze usage patterns

### Diagnostics Tools (4 tools)
59. `diagnose_entity` - Diagnose entity issues
60. `check_entity_dependencies` - Check entity dependencies
61. `analyze_automation_conflicts` - Analyze automation conflicts
62. `get_integration_errors` - Get integration errors

### Blueprint Tools (4 tools)
63. `list_blueprints` - List all blueprints
64. `get_blueprint` - Get blueprint definition
65. `import_blueprint` - Import blueprint from URL
66. `create_automation_from_blueprint` - Create automation from blueprint

### Zone Tools (4 tools)
67. `list_zones` - List all zones
68. `create_zone` - Create new zone
69. `update_zone` - Update zone
70. `delete_zone` - Delete zone

### Event Tools (3 tools)
71. `fire_event` - Fire custom event
72. `list_event_types` - List event types
73. `get_events` - Get recent events

### Notification Tools (3 tools)
74. `list_notification_services` - List notification services
75. `send_notification` - Send notification
76. `test_notification` - Test notification

### Calendar Tools (3 tools)
77. `list_calendars` - List all calendars
78. `get_calendar_events` - Get calendar events
79. `create_calendar_event` - Create calendar event

### Helper Tools (3 tools)
80. `list_helpers` - List all helpers
81. `get_helper` - Get helper state
82. `update_helper` - Update helper value

### Tag Tools (4 tools)
83. `list_tags` - List all tags
84. `create_tag` - Create new tag
85. `delete_tag` - Delete tag
86. `get_tag_automations` - Get tag automations

### Webhook Tools (2 tools)
87. `list_webhooks` - List webhooks
88. `test_webhook` - Test webhook

### Backup Tools (4 tools)
89. `list_backups` - List backups
90. `create_backup` - Create backup
91. `restore_backup` - Restore backup
92. `delete_backup` - Delete backup

## Reduction Strategies (Without Changing Repository)

### Strategy 1: Use MCP Server Configuration to Disable Tools

**Approach**: Configure the MCP server to only expose essential tools via environment variables or configuration.

**Implementation**: Create a configuration file or environment variable that lists which tool categories to enable/disable.

**Recommended Tool Categories to Keep (Core Functionality - ~40 tools)**:
- Entity Tools (6) - Essential for basic operations
- Query Processing (1) - Core semantic search
- Automation Tools (10) - Core automation management
- System Tools (9) - Essential system info
- Service Tools (1) - Universal service caller
- Statistics Tools (3) - Useful analytics
- Diagnostics Tools (4) - Troubleshooting

**Tool Categories to Disable (Advanced/Specialized - ~52 tools)**:
- Entity Descriptions (2) - Can be generated on-demand
- Script Tools (4) - Less frequently used
- Device Tools (4) - Can use entity tools instead
- Area Tools (6) - Less frequently used
- Scene Tools (5) - Less frequently used
- Integration Tools (3) - Advanced use case
- Template Tools (1) - Advanced use case
- Logbook Tools (3) - Can use history instead
- Blueprint Tools (4) - Advanced use case
- Zone Tools (4) - Less frequently used
- Event Tools (3) - Advanced use case
- Notification Tools (3) - Less frequently used
- Calendar Tools (3) - Specialized use case
- Helper Tools (3) - Less frequently used
- Tag Tools (4) - Specialized use case
- Webhook Tools (2) - Advanced use case
- Backup Tools (4) - Less frequently used

### Strategy 2: Consolidate Similar Tools

**Approach**: Use a single unified tool with parameters instead of multiple specialized tools.

**Examples**:
- **List Operations**: Instead of `list_automations`, `list_scripts`, `list_scenes`, etc., use a single `list_items(type="automation|script|scene")` tool
- **Get Operations**: Instead of `get_automation_config`, `get_script`, `get_scene`, use a single `get_item(type, id)` tool
- **CRUD Operations**: Instead of separate create/update/delete tools, use a single `manage_item(action="create|update|delete", type, ...)` tool

**Potential Consolidations**:
- List tools: 15 tools → 1 tool (save 14)
- Get tools: 12 tools → 1 tool (save 11)
- CRUD operations: 20 tools → 1 tool (save 19)
- **Total potential reduction: 44 tools**

### Strategy 3: Use Resources Instead of Tools

**Approach**: Move read-only operations to resources, which are more efficient for the LLM.

**Candidates for Resource Conversion**:
- `list_automations` → Resource: `hass://automations`
- `list_scripts` → Resource: `hass://scripts`
- `list_scenes` → Resource: `hass://scenes`
- `list_devices` → Resource: `hass://devices`
- `list_areas` → Resource: `hass://areas`
- `list_integrations` → Resource: `hass://integrations`
- `get_automation_config` → Resource: `hass://automations/{id}`
- `get_script` → Resource: `hass://scripts/{id}`
- `get_scene` → Resource: `hass://scenes/{id}`

**Potential reduction: ~15 tools → resources**

### Strategy 4: Prioritize by Usage Frequency

**Approach**: Disable rarely-used tools and keep only frequently-used ones.

**High Priority Tools (Keep - ~35 tools)**:
- All Entity Tools (6)
- Query Processing (1)
- Core Automation Tools: list, get, create, update, delete, enable, disable, trigger (8)
- Core System Tools: get_version, system_overview, get_error_log, system_health, core_config (5)
- Service Tools (1)
- Statistics Tools (3)
- Diagnostics Tools (4)
- Essential List Tools: list_automations, list_entities (2)
- Essential Get Tools: get_entity, get_automation_config (2)

**Medium Priority Tools (Optional - ~25 tools)**:
- Remaining Automation Tools (2)
- Script Tools (4)
- Device Tools (4)
- Area Tools (6)
- Scene Tools (5)
- Integration Tools (3)
- Logbook Tools (3)

**Low Priority Tools (Disable - ~32 tools)**:
- Entity Descriptions (2)
- Template Tools (1)
- Blueprint Tools (4)
- Zone Tools (4)
- Event Tools (3)
- Notification Tools (3)
- Calendar Tools (3)
- Helper Tools (3)
- Tag Tools (4)
- Webhook Tools (2)
- Backup Tools (4)

## Recommended Implementation

### Option A: Minimal Configuration (~35 tools)
Keep only essential tools for core functionality:
- Entity Tools (6)
- Query Processing (1)
- Core Automation Tools (8)
- Core System Tools (5)
- Service Tools (1)
- Statistics Tools (3)
- Diagnostics Tools (4)
- Essential List/Get Tools (4)

**Total: ~32 tools**

### Option B: Balanced Configuration (~50 tools)
Keep essential + frequently used tools:
- All from Option A
- Script Tools (4)
- Device Tools (4)
- Area Tools (6)
- Scene Tools (5)
- Integration Tools (3)
- Logbook Tools (3)

**Total: ~50 tools**

### Option C: Use Resources for Read Operations (~60 tools)
Keep all tools but convert read-only operations to resources:
- Convert 15 list/get tools to resources
- Keep all write/action tools
- **Result: ~77 tools → ~62 tools**

## Implementation Without Repository Changes

Since you cannot modify the repository, you can:

1. **Use MCP Client Configuration**: Configure Cursor to only use specific tools by creating a custom MCP client configuration that filters tools.

2. **Create a Proxy/Wrapper**: Create a lightweight proxy MCP server that wraps the main server and only exposes selected tools.

3. **Use Environment Variables**: If the server supports it, use environment variables to disable tool categories (this would require repository support).

4. **Manual Tool Selection in Cursor**: Configure Cursor's MCP settings to manually specify which tools to use (if supported).

5. **Create a Tool Filter Script**: Create a script that filters the tool list before passing to Cursor (requires MCP protocol knowledge).

## Best Recommendation

**Create a tool filtering configuration file** that can be used by the MCP client to only expose essential tools. This would require:

1. A configuration file (e.g., `tool_filter.json`) listing enabled/disabled tools
2. A wrapper script that filters tools based on the configuration
3. Update Cursor's MCP configuration to use the wrapper

**Example Configuration**:
```json
{
  "enabled_tools": [
    "get_entity",
    "entity_action",
    "list_entities",
    "search_entities_tool",
    "semantic_search_entities_tool",
    "process_natural_language_query",
    "list_automations",
    "get_automation_config",
    "create_automation",
    "update_automation",
    "delete_automation",
    "enable_automation",
    "disable_automation",
    "trigger_automation",
    "get_version",
    "system_overview",
    "get_error_log",
    "system_health",
    "core_config",
    "call_service",
    "get_entity_statistics",
    "get_domain_statistics",
    "diagnose_entity"
  ],
  "disabled_tools": [
    "generate_entity_description",
    "generate_entity_descriptions_batch",
    "get_entity_suggestions",
    "list_scripts",
    "get_script",
    "run_script",
    "reload_scripts",
    "list_devices",
    "get_device",
    "get_device_entities",
    "get_device_stats",
    "list_areas",
    "get_area_entities",
    "create_area",
    "update_area",
    "delete_area",
    "get_area_summary",
    "list_scenes",
    "get_scene",
    "create_scene",
    "activate_scene",
    "reload_scenes",
    "list_integrations",
    "get_integration_config",
    "reload_integration",
    "get_cache_statistics",
    "restart_ha",
    "get_history",
    "domain_summary",
    "test_template",
    "get_logbook",
    "get_entity_logbook",
    "search_logbook",
    "analyze_usage_patterns",
    "check_entity_dependencies",
    "analyze_automation_conflicts",
    "get_integration_errors",
    "list_blueprints",
    "get_blueprint",
    "import_blueprint",
    "create_automation_from_blueprint",
    "list_zones",
    "create_zone",
    "update_zone",
    "delete_zone",
    "fire_event",
    "list_event_types",
    "get_events",
    "list_notification_services",
    "send_notification",
    "test_notification",
    "list_calendars",
    "get_calendar_events",
    "create_calendar_event",
    "list_helpers",
    "get_helper",
    "update_helper",
    "list_tags",
    "create_tag",
    "delete_tag",
    "get_tag_automations",
    "list_webhooks",
    "test_webhook",
    "list_backups",
    "create_backup",
    "restore_backup",
    "delete_backup",
    "get_automation_execution_log",
    "validate_automation_config"
  ]
}
```

This would reduce from **92 tools to ~23 essential tools**, a **75% reduction**.
