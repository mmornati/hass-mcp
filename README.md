# Hass-MCP

A Model Context Protocol (MCP) server for Home Assistant integration with Claude and other LLMs.

> **Note**: This README is for developers and contributors. For user documentation, see [docs/](docs/) or visit [the documentation site](https://mmornati.github.io/hass-mcp).

## About This Fork

This project is a fork of [@voska/hass-mcp](https://github.com/voska/hass-mcp). The original repository was created by Matt Voska and provided the initial MCP server implementation for Home Assistant.

### Major Changes from Original

This fork includes significant improvements:

- **Modular Architecture**: Complete refactoring from monolithic files into a modular architecture with clear separation of concerns
- **Comprehensive Testing**: Unit and integration tests with >80% coverage
- **Enhanced Toolset**: 86+ tools organized across 20+ categories
- **CI/CD Pipeline**: Automated testing, validation, and deployment
- **Developer Tooling**: Pre-commit hooks, linting, type checking, and security scanning
- **Documentation**: Comprehensive documentation site built with MkDocs
- **Additional Features**: Blueprints, calendars, helpers, tags, webhooks, backups, and more

### Original Repository

- **Source**: [@voska/hass-mcp](https://github.com/voska/hass-mcp)
- **Author**: Matt Voska
- **License**: MIT License

## Project Overview

Hass-MCP provides a Model Context Protocol server that enables AI assistants to interact with Home Assistant instances. The project is organized into three main layers:

1. **Core Layer** (`app/core/`): Shared infrastructure (HTTP client, decorators, error handling, types, caching)
2. **API Layer** (`app/api/`): Business logic for interacting with Home Assistant (entities, automations, system, etc.)
3. **Tools Layer** (`app/tools/`): Thin MCP tool wrappers that register with the MCP server

## Caching System

Hass-MCP includes a comprehensive caching system to reduce API calls to Home Assistant and improve response times. The cache is designed to be transparent and automatically handles caching, expiration, and invalidation.

### Configuration

Caching can be configured via environment variables:

```bash
# Enable/disable caching (default: true)
export HASS_MCP_CACHE_ENABLED=true

# Cache backend type (default: memory)
export HASS_MCP_CACHE_BACKEND=memory  # Options: memory, redis, file

# Default TTL in seconds (default: 300)
export HASS_MCP_CACHE_DEFAULT_TTL=300

# Maximum cache size (default: 1000)
export HASS_MCP_CACHE_MAX_SIZE=1000

# Redis URL (if using Redis backend)
export HASS_MCP_CACHE_REDIS_URL=redis://localhost:6379

# Cache directory (if using file backend)
export HASS_MCP_CACHE_DIR=.cache
```

### Cache Behavior

The caching system automatically:

1. **Caches successful responses** from API functions decorated with `@cached`
2. **Expires cached data** based on TTL (Time-To-Live) settings
3. **Invalidates cache** when data is modified (via `@invalidate_cache` decorator)
4. **Skips caching** for error responses by default
5. **Gracefully degrades** if cache operations fail (never breaks API calls)

### TTL Presets

Different types of data have different TTL values:

- **TTL_VERY_LONG** (1 hour): Very stable data (HA version, areas, zones, blueprints, system config)
- **TTL_LONG** (30 minutes): Stable data (automations, scripts, scenes, devices, tags, helpers, entity metadata)
- **TTL_MEDIUM** (5 minutes): Moderately stable data (integrations, device statistics, area entities)
- **TTL_SHORT** (1 minute): Semi-dynamic data (entity states, entity lists with state info, domain summaries)
- **TTL_DISABLED** (0): No caching (for highly dynamic data like logs)

### Cached Functions

The following API functions are automatically cached:

- **Entities**:
  - `get_entity_state` (TTL_SHORT, 1 min) - entity states with conditional caching
  - `get_entities` (TTL_LONG for metadata, TTL_SHORT for state info) - dynamic TTL based on lean flag
  - `summarize_domain` (TTL_SHORT, 1 min) - domain summaries with state information
- **Automations**: `get_automations`, `get_automation_config` (TTL_LONG, 30 min)
- **Scripts**: `get_scripts`, `get_script_config` (TTL_LONG, 30 min)
- **Scenes**: `get_scenes`, `get_scene_config` (TTL_LONG, 30 min)
- **Areas**: `get_areas` (TTL_VERY_LONG, 1 hour), `get_area_entities` (TTL_MEDIUM, 5 min)
- **Zones**: `list_zones` (TTL_VERY_LONG, 1 hour)
- **Devices**: `get_devices`, `get_device_details` (TTL_LONG, 30 min), `get_device_statistics` (TTL_MEDIUM, 5 min)
- **Integrations**: `get_integrations`, `get_integration_config` (TTL_MEDIUM, 5 min)
- **Helpers**: `list_helpers` (TTL_LONG, 30 min)
- **Blueprints**: `list_blueprints`, `get_blueprint` (TTL_VERY_LONG, 1 hour)
- **Tags**: `list_tags` (TTL_LONG, 30 min)
- **System**: `get_hass_version`, `get_core_config` (TTL_VERY_LONG, 1 hour)

### Excluded from Caching (US-006)

The following API functions are **explicitly excluded from caching** because they return highly dynamic, time-sensitive data:

- **Logbook**: `get_logbook`, `get_entity_logbook`, `search_logbook` - Logbook entries are time-sensitive and change frequently
- **History**: `get_entity_history` - Entity history is time-based and highly dynamic
- **Statistics**: `get_entity_statistics`, `get_domain_statistics`, `analyze_usage_patterns` - Statistics are derived from history/logbook data and are highly dynamic
- **Events**: `get_events` - Events are time-sensitive and change frequently
- **Automation Execution Logs**: `get_automation_execution_log` - Execution logs are time-sensitive and change frequently
- **System**: `get_hass_error_log`, `get_system_overview` - Error logs and system overview include current entity states which are highly dynamic

These endpoints will always fetch fresh data from Home Assistant and never use cached results, ensuring accuracy for time-sensitive operations.

### Cache Invalidation

Cache is automatically invalidated when data is modified:

- **Entity States**: When performing entity actions (turn_on, turn_off, toggle) or calling services that affect entities
- **Automations**: When creating, updating, or deleting automations
- **Areas**: When creating, updating, or deleting areas
- **Zones**: When creating, updating, or deleting zones
- **Scenes**: When creating scenes
- **Integrations**: When reloading integrations
- **Tags**: When creating or deleting tags

### Dynamic TTL Selection

The cache system supports dynamic TTL selection based on function parameters:

- **`get_entities`**: Uses TTL_LONG (30 min) for metadata-only queries (`lean=True`), TTL_SHORT (1 min) for state-included queries (`lean=False` or `fields` specified)
- **`get_entity_state`**: Uses TTL_SHORT (1 min) with conditional caching (skips caching for errors, unavailable states)

### Conditional Caching

Some functions use conditional caching to skip caching in certain scenarios:

- **`get_entity_state`**: Only caches successful responses with available states (not "unknown" or "unavailable")
- **Error responses**: Never cached by default
- **Unavailable entities**: Not cached to ensure fresh data when entities become available

### Cache Statistics

You can check cache statistics programmatically:

```python
from app.core.cache.manager import get_cache_manager

cache = await get_cache_manager()
stats = cache.get_statistics()
# Returns: {"enabled": True, "hits": 100, "misses": 50, "total_requests": 150, "hit_rate": 0.667, "size": 42}
```

### Disabling Caching

To disable caching entirely:

```bash
export HASS_MCP_CACHE_ENABLED=false
```

This will bypass all cache operations without affecting functionality.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Home Assistant instance (for testing)

### Quick Start

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

   Or use the setup script:
   ```bash
   ./scripts/setup-dev.sh
   ```

   Or use Make:
   ```bash
   make setup
   ```

4. **Configure environment variables:**
   ```bash
   export HA_URL="http://localhost:8123"
   export HA_TOKEN="your_long_lived_token"
   ```

## Development Tools

The project uses several tools to ensure code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Bandit**: Security vulnerability scanner
- **Pytest**: Testing framework with coverage
- **Pre-commit**: Git hooks for quality checks

### Quick Commands

**Using Make (recommended):**
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

**Manual commands:**
```bash
# Tests
uv run pytest tests/                    # Run all tests
uv run pytest tests/ --cov=app          # Run with coverage
uv run pytest tests/unit/               # Run unit tests
uv run pytest tests/integration/        # Run integration tests

# Code Quality
uv run ruff check app/ tests/           # Check linting
uv run ruff check app/ tests/ --fix     # Fix linting issues
uv run ruff format app/ tests/          # Format code
uv run mypy app/                        # Type checking
uv run bandit -r app/                   # Security scan
```

## Running Tests

### Test Structure

- **Unit tests** (`tests/unit/`): Test API modules in isolation
- **Integration tests** (`tests/integration/`): Test complete tool workflows

### Running Tests

```bash
# All tests
uv run pytest tests/

# With coverage report
uv run pytest tests/ --cov=app --cov-report=html

# Specific test file
uv run pytest tests/test_server.py

# Integration tests only
uv run pytest tests/integration/

# Unit tests only
uv run pytest tests/unit/

# Verbose output
uv run pytest tests/ -v
```

## Debugging with MCP Inspector

The [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) is an interactive developer tool for testing and debugging MCP servers.

### Installation

Runs directly through `npx` without requiring installation:

```bash
npx @modelcontextprotocol/inspector <command>
```

### Usage

**For locally developed servers:**
```bash
# Using uv
npx @modelcontextprotocol/inspector uv run -m app

# Or with environment variables
HA_URL=http://localhost:8123 HA_TOKEN=your_token \
  npx @modelcontextprotocol/inspector uv run -m app
```

**With Docker:**
```bash
npx @modelcontextprotocol/inspector docker run -i --rm \
  -e HA_URL=http://homeassistant.local:8123 \
  -e HA_TOKEN=your_token \
  mmornati/hass-mcp:latest
```

The Inspector provides:
- **Tools Tab**: Test all available tools with custom inputs
- **Prompts Tab**: Test guided conversation prompts
- **Resources Tab**: Inspect resource endpoints
- **Notifications Pane**: Monitor server logs and errors

## Project Structure

```
hass-mcp/
├── app/                      # Main application code
│   ├── __main__.py           # Entry point
│   ├── config.py             # Configuration management
│   ├── run.py                # Server runner
│   ├── server.py             # MCP server orchestration
│   ├── prompts.py            # Guided conversation prompts
│   │
│   ├── core/                 # Core infrastructure layer
│   │   ├── client.py         # HTTP client management
│   │   ├── decorators.py     # Async handlers, error decorators
│   │   ├── errors.py         # Error handling utilities
│   │   └── types.py          # Shared type definitions
│   │
│   ├── api/                  # API layer (business logic)
│   │   ├── base.py           # BaseAPI class for common patterns
│   │   ├── entities.py       # Entity management
│   │   ├── automations.py    # Automation CRUD & execution
│   │   ├── scripts.py        # Script management
│   │   ├── devices.py        # Device management
│   │   ├── areas.py          # Area management
│   │   ├── scenes.py         # Scene management
│   │   ├── integrations.py   # Integration management
│   │   ├── system.py         # System functions
│   │   ├── services.py       # Service calls
│   │   ├── templates.py      # Template testing
│   │   ├── logbook.py        # Logbook access
│   │   ├── statistics.py     # Statistics & analytics
│   │   ├── diagnostics.py    # Debugging tools
│   │   ├── blueprints.py     # Blueprint management
│   │   ├── zones.py          # Zone management
│   │   ├── events.py         # Event firing
│   │   ├── notifications.py   # Notification services
│   │   ├── calendars.py      # Calendar & event management
│   │   ├── helpers.py        # Input helpers
│   │   ├── tags.py           # RFID/NFC tag management
│   │   ├── webhooks.py       # Webhook management
│   │   └── backups.py        # Backup & restore
│   │
│   └── tools/                # MCP Tool layer (thin wrappers)
│       └── ...               # Tool modules mirroring API structure
│
├── tests/                    # Test suite
│   ├── conftest.py           # Pytest configuration & fixtures
│   ├── test_server.py        # Server tests
│   ├── unit/                 # Unit tests for API layer
│   └── integration/          # Integration tests
│
├── docs/                     # User documentation (MkDocs)
├── .github/workflows/         # GitHub Actions workflows
├── scripts/                  # Utility scripts
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── mkdocs.yml                # MkDocs configuration
├── pyproject.toml             # Project configuration & dependencies
├── Makefile                  # Development convenience commands
└── Dockerfile                # Docker image definition
```

## Architecture Principles

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

## Adding New Features

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

## Development Guidelines

### Code Style

- Follow PEP 8 style guide (enforced by Ruff)
- Line length: 100 characters
- Use type hints for all function signatures
- Use async/await for asynchronous operations
- Document all public functions and classes

### Type Hints

All functions should have type hints:
```python
async def get_entity(entity_id: str, fields: list[str] | None = None) -> dict:
    """Get entity state with optional field filtering."""
    ...
```

### Architecture Patterns

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

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and error cases
- Mock external API calls in tests
- Add integration tests for new tools

### Commit Messages

Follow conventional commit format:
```
feat: Add new automation management tools
fix: Fix entity state retrieval error
docs: Update README with new features
test: Add tests for area management
refactor: Simplify error handling
```

### Pull Requests

Before creating a PR:

1. Ensure all tests pass: `uv run pytest tests/`
2. Run code quality checks: `uv run pre-commit run --all-files`
3. Update documentation if needed
4. Add tests for new features (unit + integration)
5. Ensure CI workflows pass
6. Test with MCP Inspector (if adding new tools)
7. Update `docs/` if adding user-facing features

## Continuous Integration

The project uses GitHub Actions for CI/CD validation:

### Workflows

1. **Test Workflow** (`.github/workflows/test.yml`)
   - Runs on: push, pull_request
   - Executes: Test suite with coverage
   - Uploads: Coverage reports as artifacts

2. **Validate Workflow** (`.github/workflows/validate.yml`)
   - Runs on: push, pull_request
   - Includes: Lint, type check, security scan, coverage, pre-commit hooks

3. **Release Workflow** (`.github/workflows/release.yml`)
   - Runs on: tag push
   - Builds and publishes Docker image and PyPI package

4. **Docker Workflow** (`.github/workflows/docker.yml`)
   - Builds Docker image for testing
   - Validates: Docker image can run successfully

5. **Documentation Deployment** (`.github/workflows/docs-deploy.yml`)
   - Runs on: push to main (docs changes)
   - Deploys: Documentation to GitHub Pages

All workflows must pass before merging pull requests.

## Troubleshooting

### Pre-commit Hooks Failing

```bash
# Update hooks to latest versions
uv run pre-commit autoupdate

# Run specific hook to see detailed error
uv run pre-commit run ruff --verbose
```

### Type Checking Errors

```bash
# See detailed MyPy errors
uv run mypy app/ --show-error-codes
```

### Test Failures

```bash
# Run with more verbose output
uv run pytest tests/ -vv

# Run with print statements visible
uv run pytest tests/ -s

# Run specific test
uv run pytest tests/test_server.py::TestMCPServer::test_tool_functions_exist
```

### MCP Inspector Connection Issues

```bash
# Verify environment variables are set
echo $HA_URL
echo $HA_TOKEN

# Test server directly
uv run python -m app

# Check server logs in Inspector's Notifications pane
```

### Import Errors After Refactoring

- Ensure you're importing from new modules (`app.api.*`, `app.tools.*`)
- Legacy `app.hass` module has been removed
- Check `app/server.py` for correct import paths

## License

[MIT License](LICENSE)
