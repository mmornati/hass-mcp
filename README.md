# Hass-MCP

A Model Context Protocol (MCP) server for Home Assistant integration with Claude and other LLMs.

<a href="https://glama.ai/mcp/servers/@voska/hass-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@voska/hass-mcp/badge" alt="Hass-MCP MCP server" />
</a>

## Overview

Hass-MCP enables AI assistants like Claude to interact directly with your Home Assistant instance, allowing them to:

- Query the state of devices and sensors
- Control lights, switches, and other entities
- Get summaries of your smart home
- Troubleshoot automations and entities
- Search for specific entities
- Create guided conversations for common tasks

## Screenshots

<img width="700" alt="Screenshot 2025-03-16 at 15 48 01" src="https://github.com/user-attachments/assets/5f9773b4-6aef-4139-a978-8ec2cc8c0aea" />
<img width="400" alt="Screenshot 2025-03-16 at 15 50 59" src="https://github.com/user-attachments/assets/17e1854a-9399-4e6d-92cf-cf223a93466e" />
<img width="400" alt="Screenshot 2025-03-16 at 15 49 26" src="https://github.com/user-attachments/assets/4565f3cd-7e75-4472-985c-7841e1ad6ba8" />

## Features

- **Entity Management**: Get states, control devices, and search for entities
- **Domain Summaries**: Get high-level information about entity types
- **Automation Support**: List and control automations
- **Guided Conversations**: Use prompts for common tasks like creating automations
- **Smart Search**: Find entities by name, type, or state
- **Token Efficiency**: Lean JSON responses to minimize token usage

## Installation

### Prerequisites

- Home Assistant instance with Long-Lived Access Token
- One of the following:
  - Docker (recommended)
  - Python 3.13+ and [uv](https://github.com/astral-sh/uv)

## Setting Up With Claude Desktop

### Docker Installation (Recommended)

1. Pull the Docker image:

   ```bash
   docker pull mmornati/hass-mcp:latest
   ```

2. Add the MCP server to Claude Desktop:

   a. Open Claude Desktop and go to Settings
   b. Navigate to Developer > Edit Config
   c. Add the following configuration to your `claude_desktop_config.json` file:

   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-e",
           "HA_URL",
           "-e",
           "HA_TOKEN",
           "mmornati/hass-mcp"
         ],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN"
         }
       }
     }
   }
   ```

   d. Replace `YOUR_LONG_LIVED_TOKEN` with your actual Home Assistant long-lived access token
   e. Update the `HA_URL`:

   - If running Home Assistant on the same machine: use `http://host.docker.internal:8123` (Docker Desktop on Mac/Windows)
   - If running Home Assistant on another machine: use the actual IP or hostname

   f. Save the file and restart Claude Desktop

3. The "Hass-MCP" tool should now appear in your Claude Desktop tools menu

> **Note**: If you're running Home Assistant in Docker on the same machine, you may need to add `--network host` to the Docker args for the container to access Home Assistant. Alternatively, use the IP address of your machine instead of `host.docker.internal`.

### uv/uvx

1. Install uv on your system.

2. Add the MCP server to Claude Desktop:

   a. Open Claude Desktop and go to Settings
   b. Navigate to Developer > Edit Config
   c. Add the following configuration to your `claude_desktop_config.json` file:

   ```json
   {
     "mcpServers": {
       "hass-mcp": {
         "command": "uvx",
         "args": ["hass-mcp"],
         "env": {
           "HA_URL": "http://homeassistant.local:8123",
           "HA_TOKEN": "YOUR_LONG_LIVED_TOKEN"
         }
       }
     }
   }
   ```

   d. Replace `YOUR_LONG_LIVED_TOKEN` with your actual Home Assistant long-lived access token
   e. Update the `HA_URL`:

   - If running Home Assistant on the same machine: use `http://host.docker.internal:8123` (Docker Desktop on Mac/Windows)
   - If running Home Assistant on another machine: use the actual IP or hostname

   f. Save the file and restart Claude Desktop

3. The "Hass-MCP" tool should now appear in your Claude Desktop tools menu

## Other MCP Clients

### Cursor

1. Go to Cursor Settings > MCP > Add New MCP Server
2. Fill in the form:
   - Name: `Hass-MCP`
   - Type: `command`
   - Command:
     ```
     docker run -i --rm -e HA_URL=http://homeassistant.local:8123 -e HA_TOKEN=YOUR_LONG_LIVED_TOKEN voska/hass-mcp
     ```
   - Replace `YOUR_LONG_LIVED_TOKEN` with your actual Home Assistant token
   - Update the HA_URL to match your Home Assistant instance address
3. Click "Add" to save

### Claude Code (CLI)

To use with Claude Code CLI, you can add the MCP server directly using the `mcp add` command:

**Using Docker (recommended):**

```bash
claude mcp add hass-mcp -e HA_URL=http://homeassistant.local:8123 -e HA_TOKEN=YOUR_LONG_LIVED_TOKEN -- docker run -i --rm -e HA_URL -e HA_TOKEN voska/hass-mcp
```

Replace `YOUR_LONG_LIVED_TOKEN` with your actual Home Assistant token and update the HA_URL to match your Home Assistant instance address.

## Usage Examples

Here are some examples of prompts you can use with Claude once Hass-MCP is set up:

- "What's the current state of my living room lights?"
- "Turn off all the lights in the kitchen"
- "List all my sensors that contain temperature data"
- "Give me a summary of my climate entities"
- "Create an automation that turns on the lights at sunset"
- "Help me troubleshoot why my bedroom motion sensor automation isn't working"
- "Search for entities related to my living room"

## Available Tools

Hass-MCP provides several tools for interacting with Home Assistant:

- `get_version`: Get the Home Assistant version
- `get_entity`: Get the state of a specific entity with optional field filtering
- `entity_action`: Perform actions on entities (turn on, off, toggle)
- `list_entities`: Get a list of entities with optional domain filtering and search
- `search_entities_tool`: Search for entities matching a query
- `domain_summary_tool`: Get a summary of a domain's entities
- `list_automations`: Get a list of all automations
- `get_automation_config`: Get full automation configuration including triggers, conditions, actions
- `create_automation`: Create a new automation from configuration dictionary
- `update_automation`: Update an existing automation with new configuration
- `delete_automation`: Delete an automation (permanent, no undo)
- `enable_automation`: Enable an automation
- `disable_automation`: Disable an automation (preserves configuration)
- `trigger_automation`: Manually trigger an automation for testing
- `get_automation_execution_log`: Get automation execution history from logbook
- `validate_automation_config`: Validate an automation configuration before creating/updating
- `list_scripts`: Get a list of all scripts in Home Assistant
- `get_script`: Get script configuration and details
- `run_script`: Execute a script with optional variables
- `reload_scripts`: Reload all scripts from configuration
- `test_template`: Test Jinja2 template rendering
- `list_areas`: Get a list of all areas in Home Assistant
- `get_area_entities`: Get all entities belonging to a specific area
- `create_area`: Create a new area with optional aliases and picture
- `update_area`: Update an existing area (name, aliases, picture)
- `delete_area`: Delete an area (permanent, removes area_id from entities)
- `get_area_summary`: Get summary of all areas with entity distribution
- `list_devices`: Get a list of all devices, optionally filtered by integration domain
- `get_device`: Get detailed device information
- `get_device_entities`: Get all entities belonging to a specific device
- `get_device_stats`: Get statistics about devices (by manufacturer, model, integration)
- `list_scenes`: Get a list of all scenes in Home Assistant
- `get_scene`: Get scene configuration (what entities/values it saves)
- `create_scene`: Create a new scene (may provide YAML example if API unavailable)
- `activate_scene`: Activate/restore a scene to restore saved states
- `reload_scenes`: Reload scenes from configuration
- `diagnose_entity`: Comprehensive entity diagnostics with issues and recommendations
- `check_entity_dependencies`: Find what depends on an entity (automations, scripts, scenes)
- `analyze_automation_conflicts`: Detect conflicting automations (opposing actions, etc.)
- `get_integration_errors`: Get errors specific to integrations
- `call_service_tool`: Call any Home Assistant service
- `restart_ha`: Restart Home Assistant
- `system_overview`: Get a comprehensive overview of the entire Home Assistant system
- `get_history`: Get the state history of an entity
- `get_error_log`: Get the Home Assistant error log
- `system_health`: Get system health information for all components
- `core_config`: Get core configuration (location, timezone, unit system, components)
- `list_integrations`: Get a list of all configuration entries (integrations) with optional domain filtering
- `get_integration_config`: Get detailed configuration for a specific integration entry
- `reload_integration`: Reload a specific integration (use with caution)
- `list_blueprints`: Get a list of all available blueprints, optionally filtered by domain
- `get_blueprint`: Get blueprint definition and metadata
- `import_blueprint`: Import blueprint from URL
- `create_automation_from_blueprint`: Create automation from blueprint with specified inputs
- `list_zones`: Get a list of all zones (GPS coordinates) in Home Assistant
- `create_zone`: Create a new zone with GPS coordinates and radius
- `update_zone`: Update an existing zone (name, location, radius, icon)
- `delete_zone`: Delete a zone (permanent, system zones may not be deletable)
- `get_logbook`: Get logbook entries for a time range, optionally filtered by entity
- `get_entity_logbook`: Get logbook entries for a specific entity
- `search_logbook`: Search logbook entries by query string
- `get_entity_statistics`: Get statistics for an entity (min, max, mean, median)
- `get_domain_statistics`: Get aggregate statistics for all entities in a domain
- `analyze_usage_patterns`: Analyze usage patterns (when device is used most)
- `list_calendars`: Get a list of all calendar entities in Home Assistant
- `get_calendar_events`: Get calendar events for a date range
- `create_calendar_event`: Create a calendar event
- `list_notification_services`: Get a list of all available notification platforms
- `send_notification`: Send a notification to a specific platform or default
- `test_notification`: Test notification delivery to a specific platform
- `fire_event`: Fire a custom event
- `list_event_types`: List common event types used in Home Assistant
- `get_events`: Get recent events for an entity (via logbook)
- `list_tags`: Get a list of all RFID/NFC tags in Home Assistant
- `create_tag`: Create a new tag for NFC-based automations
- `delete_tag`: Delete a tag
- `get_tag_automations`: Get automations triggered by a tag
- `list_helpers`: Get a list of all input helpers in Home Assistant
- `get_helper`: Get helper state and configuration
- `update_helper`: Update helper value (supports all helper types)
- `list_webhooks`: Get a list of registered webhooks in Home Assistant
- `test_webhook`: Test webhook endpoint with optional payload
- `list_backups`: List available backups (if Supervisor API available)
- `create_backup`: Create a full or partial backup (if Supervisor API available)
- `restore_backup`: Restore a backup (if Supervisor API available)
- `delete_backup`: Delete a backup (if Supervisor API available)

## Prompts for Guided Conversations

Hass-MCP includes several prompts for guided conversations:

- `create_automation`: Guide for creating Home Assistant automations based on trigger type
- `debug_automation`: Troubleshooting help for automations that aren't working
- `troubleshoot_entity`: Diagnose issues with entities
- `routine_optimizer`: Analyze usage patterns and suggest optimized routines based on actual behavior
- `automation_health_check`: Review all automations, find conflicts, redundancies, or improvement opportunities
- `entity_naming_consistency`: Audit entity names and suggest standardization improvements
- `dashboard_layout_generator`: Create optimized dashboards based on user preferences and usage patterns

## Available Resources

Hass-MCP provides the following resource endpoints:

- `hass://entities/{entity_id}`: Get the state of a specific entity
- `hass://entities/{entity_id}/detailed`: Get detailed information about an entity with all attributes
- `hass://entities`: List all Home Assistant entities grouped by domain
- `hass://entities/domain/{domain}`: Get a list of entities for a specific domain
- `hass://search/{query}/{limit}`: Search for entities matching a query with custom result limit

## Development

Hass-MCP has undergone a comprehensive refactoring to improve maintainability, testability, and extensibility. The project now features a modular architecture with clear separation of concerns.

### Architecture Overview

The project is organized into three main layers:

1. **Core Layer** (`app/core/`): Shared infrastructure (HTTP client, decorators, error handling, types)
2. **API Layer** (`app/api/`): Business logic for interacting with Home Assistant (entities, automations, system, etc.)
3. **Tools Layer** (`app/tools/`): Thin MCP tool wrappers that register with the MCP server

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Home Assistant instance (for testing)

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mmornati/hass-mcp.git
   cd hass-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

3. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

   This will install git hooks that automatically run code quality checks before commits.

   Or use the setup script:
   ```bash
   ./scripts/setup-dev.sh
   ```

   Or use Make (if available):
   ```bash
   make setup
   ```

4. **Configure environment variables:**
   ```bash
   export HA_URL="http://localhost:8123"
   export HA_TOKEN="your_long_lived_token"
   ```

### Development Tools

The project uses several tools to ensure code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Bandit**: Security vulnerability scanner
- **Pytest**: Testing framework with coverage
- **Pre-commit**: Git hooks for quality checks

### Running Tests

**Run all tests:**
```bash
uv run pytest tests/
```

**Run tests with coverage:**
```bash
uv run pytest tests/ --cov=app --cov-report=html
```

**Run specific test file:**
```bash
uv run pytest tests/test_server.py
```

**Run integration tests:**
```bash
uv run pytest tests/integration/
```

**Run unit tests:**
```bash
uv run pytest tests/unit/
```

**Run tests with verbose output:**
```bash
uv run pytest tests/ -v
```

### Debugging with MCP Inspector

The [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) is an interactive developer tool for testing and debugging MCP servers. It provides a web-based interface to interact with your MCP server and test tools, prompts, and resources.

#### Installation

The MCP Inspector runs directly through `npx` without requiring installation:

```bash
npx @modelcontextprotocol/inspector <command>
```

#### Basic Usage

**For locally developed servers (Python):**

```bash
# Using uv
npx @modelcontextprotocol/inspector uv run -m app

# Or with environment variables
HA_URL=http://localhost:8123 HA_TOKEN=your_token \
  npx @modelcontextprotocol/inspector uv run -m app
```

**Using uvx (if published to PyPI):**

```bash
npx @modelcontextprotocol/inspector uvx -m hass-mcp
```

**With Docker:**

```bash
npx @modelcontextprotocol/inspector docker run -i --rm \
  -e HA_URL=http://homeassistant.local:8123 \
  -e HA_TOKEN=your_token \
  mmornati/hass-mcp:latest
```

#### Inspector Features

The MCP Inspector provides several features for debugging your server:

1. **Server Connection Pane**
   - Select transport for connecting to the server
   - Customize command-line arguments and environment variables
   - Configure connection settings

2. **Tools Tab**
   - Lists all 86+ available tools
   - Shows tool schemas and descriptions
   - Enables tool testing with custom inputs
   - Displays tool execution results
   - Useful for verifying tool parameters and responses

3. **Prompts Tab**
   - Displays available prompt templates
   - Shows prompt arguments and descriptions
   - Enables prompt testing with custom arguments
   - Previews generated messages
   - Tests guided conversation flows

4. **Resources Tab**
   - Lists all available resources
   - Shows resource metadata (MIME types, descriptions)
   - Allows resource content inspection
   - Supports subscription testing

5. **Notifications Pane**
   - Presents all logs recorded from the server
   - Shows notifications received from the server
   - Useful for debugging and monitoring

#### Development Workflow with Inspector

1. **Start Development:**
   ```bash
   # Terminal 1: Start the MCP Inspector
   npx @modelcontextprotocol/inspector uv run -m app

   # The Inspector will open in your browser
   # Configure environment variables in the Inspector UI
   ```

2. **Test Tools:**
   - Navigate to the **Tools** tab
   - Select a tool (e.g., `get_entity`)
   - Enter test parameters (e.g., `entity_id: "light.living_room"`)
   - Execute and review results

3. **Test Prompts:**
   - Navigate to the **Prompts** tab
   - Select a prompt (e.g., `create_automation`)
   - Test with different arguments
   - Preview generated messages

4. **Monitor Logs:**
   - Check the **Notifications** pane
   - Review server logs
   - Debug connection issues

#### Debugging Tips

- **Connection Issues**: Verify `HA_URL` and `HA_TOKEN` are set correctly in the Inspector's environment configuration
- **Tool Failures**: Check the Notifications pane for error messages
- **Parameter Validation**: Use the Tools tab to test parameter combinations
- **Response Validation**: Verify tool responses match expected formats

#### Example: Testing a Tool

1. Open MCP Inspector
2. Go to **Tools** tab
3. Select `get_entity` tool
4. Enter parameters:
   ```json
   {
     "entity_id": "light.living_room",
     "detailed": false
   }
   ```
5. Click **Execute**
6. Review results and verify response structure

This allows you to test tools independently without needing Claude Desktop or other MCP clients.

### Quick Start with Make

If you have `make` installed, you can use these convenient commands:

```bash
make setup          # Setup development environment
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Check linting
make lint-fix       # Fix linting issues
make format         # Format code
make type-check     # Check types
make security       # Run security scan
make check          # Run all quality checks
make all            # Run all checks and tests
make clean          # Clean up generated files
```

See `make help` for all available commands.

### Code Quality Checks

**Linting (Ruff):**
```bash
# Check for linting issues
uv run ruff check app/ tests/

# Auto-fix linting issues
uv run ruff check app/ tests/ --fix

# Format code
uv run ruff format app/ tests/

# Check formatting without making changes
uv run ruff format app/ tests/ --check
```

**Type Checking (MyPy):**
```bash
uv run mypy app/
```

**Security Scan (Bandit):**
```bash
uv run bandit -r app/
```

**Run all checks:**
```bash
# Lint, format check, type check, and security scan
uv run ruff check app/ tests/
uv run ruff format --check app/ tests/
uv run mypy app/
uv run bandit -r app/
```

### Pre-commit Hooks

Pre-commit hooks automatically run when you commit code. They check:
- Code formatting (Ruff)
- Linting issues (Ruff)
- Type checking (MyPy)
- Security issues (Bandit)
- Basic file checks (trailing whitespace, end-of-file, etc.)
- Test suite

**Manually run pre-commit hooks:**
```bash
# Run on staged files (default)
uv run pre-commit run

# Run on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff
```

**Bypass hooks (not recommended):**
```bash
git commit --no-verify
```

### Continuous Integration (CI)

The project uses GitHub Actions for CI/CD validation:

#### Workflows

1. **Test Workflow** (`.github/workflows/test.yml`)
   - Runs on: push, pull_request
   - Executes: Test suite with coverage
   - Uploads: Coverage reports as artifacts
   - Validates: All unit and integration tests pass

2. **Validate Workflow** (`.github/workflows/validate.yml`)
   - Runs on: push, pull_request
   - Includes:
     - **Lint**: Ruff linting and format checking
     - **Type Check**: MyPy type validation
     - **Security**: Bandit security scanning
     - **Coverage**: Test coverage reporting (target: 80%+)
     - **Pre-commit**: All pre-commit hooks

3. **Release Workflow** (`.github/workflows/release.yml`)
   - Runs on: tag push
   - Builds and publishes Docker image and PyPI package

4. **Docker Workflow** (`.github/workflows/docker.yml`)
   - Builds Docker image for testing
   - Validates: Docker image can run successfully

5. **Documentation Deployment** (`.github/workflows/docs-deploy.yml`)
   - Runs on: push to main (docs changes)
   - Deploys: Documentation to GitHub Pages
   - Updates: Documentation automatically on changes

6. **Documentation Preview** (`.github/workflows/docs-preview.yml`)
   - Runs on: pull requests (docs changes)
   - Provides: Preview links for documentation changes
   - Comments: PRs with preview URLs

All workflows must pass before merging pull requests.

### Adding New Features

When adding new features to Hass-MCP:

1. **Create API Module** (`app/api/{domain}.py`):
   - Inherit from `BaseAPI` for common patterns
   - Implement business logic
   - Add error handling
   - Add unit tests

2. **Create Tools Module** (`app/tools/{domain}.py`):
   - Create thin wrappers around API functions
   - Add MCP tool registration in `server.py`
   - Add integration tests

3. **Add Documentation**:
   - Add user documentation in `docs/{domain}.md`
   - Update `mkdocs.yml` navigation
   - Add examples and use cases

4. **Test with MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector uv run -m app
   ```
   - Verify tools appear correctly
   - Test tool parameters
   - Verify responses

5. **Update README**:
   - Add new tools to the "Available Tools" section
   - Update project structure if needed

### Recent Improvements

#### Major Refactoring (Completed)

The project has undergone a comprehensive refactoring to improve maintainability and testability:

#### ✅ Completed Phases

- **Phase 1: Core Infrastructure** - Extracted shared infrastructure (HTTP client, decorators, error handling)
- **Phase 2: API Layer** - Modularized all Home Assistant API interactions into domain-specific modules
- **Phase 3: Tools Layer** - Extracted MCP tools into separate modules
- **Phase 4: New Features** - Added support for calendars, helpers, tags, webhooks, backups
- **Phase 5: Legacy Cleanup** - Removed deprecated `hass.py` module

#### 🎯 Benefits

- **86+ tools** organized across 20+ tool categories
- **Modular architecture** with clear separation of concerns
- **Comprehensive test coverage** with unit and integration tests
- **Better maintainability** with domain-specific modules
- **Easier extensibility** following established patterns

### Development Guidelines

#### Code Style

- Follow PEP 8 style guide (enforced by Ruff)
- Line length: 100 characters
- Use type hints for all function signatures
- Use async/await for asynchronous operations
- Document all public functions and classes

#### Type Hints

All functions should have type hints:
```python
async def get_entity(entity_id: str, fields: list[str] | None = None) -> dict:
    """Get entity state with optional field filtering."""
    ...
```

#### Architecture Patterns

When adding new features, follow these patterns:

1. **API Module** (`app/api/{domain}.py`):
   ```python
   from app.api.base import BaseAPI

   class DomainAPI(BaseAPI):
       async def get_domain_entities(self, ...):
           # Business logic here
   ```

2. **Tools Module** (`app/tools/{domain}.py`):
   ```python
   from app.api.domain import DomainAPI

   async def get_domain_tool(...):
       # Thin wrapper calling API
       return await DomainAPI().get_domain_entities(...)
   ```

3. **Server Registration** (`app/server.py`):
   ```python
   mcp.tool()(async_handler("get_domain")(tools.domain.get_domain_tool))
   ```

#### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and error cases
- Mock external API calls in tests
- Add integration tests for new tools

**Test Structure:**
- **Unit tests** (`tests/unit/`): Test API modules in isolation
- **Integration tests** (`tests/integration/`): Test complete tool workflows

#### Commit Messages

Follow conventional commit format:
```
feat: Add new automation management tools
fix: Fix entity state retrieval error
docs: Update README with new features
test: Add tests for area management
refactor: Simplify error handling
```

#### Pull Requests

Before creating a PR:
1. Ensure all tests pass: `uv run pytest tests/`
2. Run code quality checks: `uv run pre-commit run --all-files`
3. Update documentation if needed
4. Add tests for new features (unit + integration)
5. Ensure CI workflows pass
6. Test with MCP Inspector (if adding new tools)
7. Update `docs/` if adding user-facing features

### Project Structure

The project follows a modular architecture with clear separation of concerns:

```
hass-mcp/
├── app/                      # Main application code
│   ├── __main__.py           # Entry point
│   ├── config.py             # Configuration management
│   ├── run.py                # Server runner
│   ├── server.py             # MCP server orchestration (~800 lines)
│   ├── prompts.py            # Guided conversation prompts
│   │
│   ├── core/                 # Core infrastructure layer
│   │   ├── __init__.py
│   │   ├── client.py         # HTTP client management
│   │   ├── decorators.py     # Async handlers, error decorators
│   │   ├── errors.py         # Error handling utilities
│   │   └── types.py          # Shared type definitions
│   │
│   ├── api/                  # API layer (business logic)
│   │   ├── __init__.py
│   │   ├── base.py           # BaseAPI class for common patterns
│   │   ├── entities.py       # Entity management (get, list, search)
│   │   ├── automations.py    # Automation CRUD & execution
│   │   ├── scripts.py        # Script management
│   │   ├── devices.py        # Device management
│   │   ├── areas.py          # Area management
│   │   ├── scenes.py         # Scene management
│   │   ├── integrations.py   # Integration management
│   │   ├── system.py         # System functions (version, health, config)
│   │   ├── services.py       # Service calls
│   │   ├── templates.py      # Template testing
│   │   ├── logbook.py        # Logbook access
│   │   ├── statistics.py     # Statistics & analytics
│   │   ├── diagnostics.py    # Debugging tools
│   │   ├── blueprints.py     # Blueprint management
│   │   ├── zones.py          # Zone management
│   │   ├── events.py         # Event firing
│   │   ├── notifications.py  # Notification services
│   │   ├── calendars.py     # Calendar & event management
│   │   ├── helpers.py        # Input helpers (booleans, numbers, etc.)
│   │   ├── tags.py           # RFID/NFC tag management
│   │   ├── webhooks.py       # Webhook management
│   │   └── backups.py        # Backup & restore (Supervisor API)
│   │
│   └── tools/                # MCP Tool layer (thin wrappers)
│       ├── __init__.py
│       ├── entities.py       # Entity MCP tools
│       ├── automations.py    # Automation MCP tools
│       ├── scripts.py        # Script MCP tools
│       ├── devices.py        # Device MCP tools
│       ├── areas.py          # Area MCP tools
│       ├── scenes.py         # Scene MCP tools
│       ├── integrations.py   # Integration MCP tools
│       ├── system.py         # System MCP tools
│       ├── services.py       # Service MCP tools
│       ├── templates.py      # Template MCP tools
│       ├── logbook.py        # Logbook MCP tools
│       ├── statistics.py    # Statistics MCP tools
│       ├── diagnostics.py   # Diagnostics MCP tools
│       ├── blueprints.py     # Blueprint MCP tools
│       ├── zones.py          # Zone MCP tools
│       ├── events.py         # Event MCP tools
│       ├── notifications.py  # Notification MCP tools
│       ├── calendars.py     # Calendar MCP tools
│       ├── helpers.py        # Helper MCP tools
│       ├── tags.py           # Tag MCP tools
│       ├── webhooks.py       # Webhook MCP tools
│       └── backups.py        # Backup MCP tools
│
├── tests/                    # Test suite
│   ├── conftest.py           # Pytest configuration & fixtures
│   ├── test_config.py        # Configuration tests
│   ├── test_server.py        # Server tests
│   ├── test_hass.py          # Legacy API tests (maintained for compatibility)
│   │
│   ├── unit/                 # Unit tests for API layer
│   │   ├── test_api_entities.py
│   │   ├── test_api_automations.py
│   │   ├── test_api_areas.py
│   │   ├── test_api_scenes.py
│   │   ├── test_api_calendars.py
│   │   ├── test_api_helpers.py
│   │   ├── test_api_tags.py
│   │   ├── test_api_webhooks.py
│   │   ├── test_api_backups.py
│   │   └── ...               # Tests for all API modules
│   │
│   └── integration/          # Integration tests
│       ├── test_mcp_server_integration.py  # Comprehensive MCP server tests
│       └── test_tools_entities.py          # Entity tools integration tests
│
├── docs/                     # User documentation (MkDocs)
│   ├── index.md              # Documentation home
│   ├── getting-started.md    # Setup guide
│   ├── configuration.md      # Configuration options
│   ├── entities.md            # Entities tools documentation
│   ├── automations.md        # Automations tools documentation
│   └── ...                   # Documentation for all tool categories
│
├── .github/
│   └── workflows/             # GitHub Actions workflows
│       ├── test.yml          # Test workflow
│       ├── validate.yml      # Code quality validation
│       ├── release.yml       # Release workflow
│       ├── docker.yml        # Docker build workflow
│       ├── docs-deploy.yml   # Documentation deployment
│       └── docs-preview.yml  # Documentation preview
│
├── scripts/                  # Utility scripts
│   ├── setup-dev.sh          # Development environment setup
│   └── check-and-fix-ci.sh   # CI/CD validation script
│
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── mkdocs.yml                # MkDocs configuration
├── pyproject.toml            # Project configuration & dependencies
├── Makefile                  # Development convenience commands
├── Dockerfile                # Docker image definition
├── REFACTORING_GUIDE.md      # Detailed refactoring documentation
└── README.md                 # This file
```

### Architecture Principles

1. **Separation of Concerns**:
   - **Core**: Infrastructure and shared utilities
   - **API**: Business logic for Home Assistant interactions
   - **Tools**: MCP tool registration (thin wrappers)

2. **Testability**:
   - Unit tests for each API module
   - Integration tests for tool functionality
   - Comprehensive test coverage (>80%)

3. **Extensibility**:
   - New features can be added by creating API modules and corresponding tools
   - Follows established patterns for consistency

4. **Maintainability**:
   - Modular structure makes it easy to locate and modify code
   - Clear naming conventions
   - Comprehensive documentation

### Troubleshooting

**Pre-commit hooks failing:**
```bash
# Update hooks to latest versions
uv run pre-commit autoupdate

# Run specific hook to see detailed error
uv run pre-commit run ruff --verbose
```

**Type checking errors:**
```bash
# See detailed MyPy errors
uv run mypy app/ --show-error-codes

# Ignore specific errors (add to pyproject.toml)
```

**Test failures:**
```bash
# Run with more verbose output
uv run pytest tests/ -vv

# Run with print statements visible
uv run pytest tests/ -s

# Run specific test
uv run pytest tests/test_server.py::TestMCPServer::test_tool_functions_exist

# Run only integration tests
uv run pytest tests/integration/ -v

# Run only unit tests
uv run pytest tests/unit/ -v
```

**MCP Inspector connection issues:**
```bash
# Verify environment variables are set
echo $HA_URL
echo $HA_TOKEN

# Test server directly
uv run python -m app

# Check server logs in Inspector's Notifications pane
```

**Import errors after refactoring:**
- Ensure you're importing from new modules (`app.api.*`, `app.tools.*`)
- Legacy `app.hass` module has been removed
- Check `app/server.py` for correct import paths

## License

[MIT License](LICENSE)
