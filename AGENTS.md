# AGENTS.md - AI Coding Agent Guide

This document provides comprehensive guidance for AI coding agents working on the hass-mcp repository. It covers architecture, conventions, testing requirements, and development workflows.

## Table of Contents

- [Project Overview](#project-overview)
- [Quick Reference](#quick-reference)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [Code Patterns and Conventions](#code-patterns-and-conventions)
- [Testing Requirements](#testing-requirements)
- [Adding New Features](#adding-new-features)
- [Code Quality and CI/CD](#code-quality-and-cicd)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

**Hass-MCP** is a Model Context Protocol (MCP) server that enables AI assistants (Claude, etc.) to interact with Home Assistant instances. The project provides a comprehensive set of tools for querying, controlling, and managing smart home devices.

### Key Technologies

- **Python 3.13+** - Required Python version
- **uv** - Package manager (required; replaces pip)
- **FastMCP** - MCP server framework (`mcp[cli]>=1.4.1`)
- **httpx** - Async HTTP client for Home Assistant API
- **pytest** - Testing framework with async support
- **Ruff** - Linter and formatter
- **MyPy** - Static type checker
- **Bandit** - Security vulnerability scanner

### Project Statistics

- **33 unified tools** (consolidated from 92 specialized tools)
- **20+ categories** (entities, automations, devices, areas, etc.)
- **3-layer architecture** (Core, API, Tools)
- **>80% test coverage** requirement

---

## Quick Reference

### Essential Commands

```bash
# Setup
make setup           # Install deps + pre-commit hooks
uv sync --extra dev  # Just install dependencies

# Testing
make test            # Run all tests
make test-cov        # Run tests with coverage
uv run pytest tests/unit/           # Unit tests only
uv run pytest tests/integration/    # Integration tests only
uv run pytest tests/ -k "test_name" # Run specific test

# Code Quality
make check           # Run all quality checks (lint, format, type, security)
make lint            # Check linting (ruff check)
make lint-fix        # Auto-fix linting issues
make format          # Format code (ruff format)
make type-check      # Type checking (mypy)
make security        # Security scan (bandit)
make pre-commit      # Run all pre-commit hooks

# Development
npx @modelcontextprotocol/inspector uv run -m app  # MCP Inspector for testing
uv run python -m app                                # Run server directly
```

### Key Directories

```
hass-mcp/
├── app/                    # Main application code
│   ├── __main__.py         # Entry point
│   ├── server.py           # MCP server orchestration (815 lines)
│   ├── config.py           # Configuration management
│   ├── prompts.py          # Guided conversation prompts
│   │
│   ├── core/               # Core infrastructure layer
│   │   ├── client.py       # HTTP client management (get_client())
│   │   ├── decorators.py   # async_handler, error decorators
│   │   ├── errors.py       # Error handling utilities
│   │   ├── types.py        # Shared type definitions
│   │   ├── cache/          # Caching system (memory, redis, file backends)
│   │   └── vectordb/       # Vector database for semantic search
│   │
│   ├── api/                # API layer (business logic)
│   │   ├── base.py         # BaseAPI class (inherit for new APIs)
│   │   ├── entities.py     # Entity management
│   │   ├── automations.py  # Automation CRUD & execution
│   │   ├── scripts.py      # Script management
│   │   ├── devices.py      # Device management
│   │   ├── areas.py        # Area management
│   │   ├── scenes.py       # Scene management
│   │   ├── integrations.py # Integration management
│   │   ├── system.py       # System functions
│   │   ├── services.py     # Service calls
│   │   ├── templates.py    # Template testing
│   │   ├── logbook.py      # Logbook access
│   │   ├── statistics.py   # Statistics & analytics
│   │   ├── diagnostics.py  # Debugging tools
│   │   ├── blueprints.py   # Blueprint management
│   │   ├── zones.py        # Zone management
│   │   ├── events.py       # Event firing
│   │   ├── notifications.py # Notification services
│   │   ├── calendars.py    # Calendar & event management
│   │   ├── helpers.py      # Input helpers
│   │   ├── tags.py         # RFID/NFC tag management
│   │   ├── webhooks.py     # Webhook management
│   │   └── backups.py      # Backup & restore
│   │
│   └── tools/              # MCP Tool layer (thin wrappers)
│       ├── unified.py      # Unified tools (15 consolidated tools)
│       └── ...             # Specialized tools mirroring API structure
│
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest configuration & fixtures
│   ├── fixtures/           # Test fixtures (JSON payloads, etc.)
│   ├── unit/               # Unit tests for API layer
│   ├── integration/        # Integration tests for tools
│   └── performance/        # Performance benchmarks
│
├── docs/                   # User documentation (MkDocs)
├── .github/workflows/      # GitHub Actions CI/CD
└── scripts/                # Utility scripts
```

### Key Files

| File | Purpose |
|------|---------|
| `app/server.py` | MCP server setup, tool registration |
| `app/core/client.py` | HTTP client factory (`get_client()`) |
| `app/core/decorators.py` | `async_handler` decorator for tools |
| `app/api/base.py` | `BaseAPI` class for API modules |
| `app/tools/unified.py` | Unified tool implementations |
| `tests/conftest.py` | Pytest fixtures and mock setup |
| `pyproject.toml` | Project config, dependencies, tool settings |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |
| `Makefile` | Development commands |

---

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client (Claude)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
┌─────────────────────────▼───────────────────────────────────┐
│                    Tools Layer (app/tools/)                  │
│  • Thin wrappers around API functions                        │
│  • Registered with MCP server in server.py                   │
│  • Use async_handler decorator                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     API Layer (app/api/)                     │
│  • Business logic for Home Assistant interactions            │
│  • Inherit from BaseAPI                                      │
│  • Use caching decorators                                    │
│  • Return structured data                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Core Layer (app/core/)                    │
│  • HTTP client management                                    │
│  • Error handling                                            │
│  • Type definitions                                          │
│  • Caching system                                            │
│  • Vector database                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST API
┌─────────────────────────▼───────────────────────────────────┐
│                    Home Assistant                            │
└─────────────────────────────────────────────────────────────┘
```

### Unified Tools Architecture

The project consolidates 92 specialized tools into 33 unified tools:

**Core Unified Tools (`app/tools/unified.py`):**

| Tool | Replaces | Purpose |
|------|----------|---------|
| `list_items` | `list_automations`, `list_scripts`, `list_scenes`, `list_areas`, etc. | List items by type |
| `get_item` | `get_automation_config`, `get_script`, `get_scene`, etc. | Get specific item |
| `manage_item` | `create_*`, `update_*`, `delete_*`, `enable_*`, `disable_*` | CRUD operations |
| `search_entities` | `list_entities`, `search_entities_tool`, `semantic_search` | Entity search |
| `generate_entity_description` | Single and batch description generators | Description generation |
| `get_logbook` | `get_logbook`, `get_entity_logbook`, `search_logbook` | Logbook access |
| `get_statistics` | `get_entity_statistics`, `get_domain_statistics`, `analyze_usage` | Statistics |
| `diagnose` | `diagnose_entity`, `check_dependencies`, `analyze_conflicts` | Diagnostics |
| `manage_events` | `fire_event`, `list_event_types`, `get_events` | Event management |
| `manage_notifications` | `list_notification_services`, `send_notification`, `test_notification` | Notifications |
| `manage_webhooks` | `list_webhooks`, `test_webhook` | Webhook management |
| `get_system_info` | `get_version`, `system_overview`, `system_health`, `core_config` | System info |
| `get_system_data` | `get_error_log`, `get_cache_statistics`, `get_history` | System data |
| `get_item_entities` | `get_device_entities`, `get_area_entities` | Item entities |
| `get_item_summary` | `get_device_stats`, `get_area_summary` | Item summaries |

**Specialized Tools (not unified):**
- `get_entity`, `entity_action` - Core entity operations
- `get_automation_execution_log`, `validate_automation_config` - Automation specifics
- `get_calendar_events`, `create_calendar_event` - Calendar specifics
- `update_helper` - Helper updates
- `restart_ha` - System restart
- `call_service_tool` - Generic service calls
- `test_template_tool` - Template testing

---

## Development Setup

### Prerequisites

1. **Python 3.13+** (check with `python --version`)
2. **uv** package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Git** for version control
4. **Node.js** (optional, for MCP Inspector)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/mmornati/hass-mcp.git
cd hass-mcp

# Setup development environment (recommended)
make setup

# Or manually:
uv sync --extra dev
uv run pre-commit install
```

### Environment Variables

```bash
# Required for testing with real Home Assistant
export HA_URL="http://localhost:8123"
export HA_TOKEN="your_long_lived_token"

# Optional
export HA_TIMEOUT="30"              # Request timeout
export HA_SSL_VERIFY="true"         # SSL verification (true, false, or path to CA)
export LOG_LEVEL="INFO"             # Logging level

# Cache configuration
export HASS_MCP_CACHE_ENABLED="true"
export HASS_MCP_CACHE_BACKEND="memory"  # memory, redis, file
export HASS_MCP_CACHE_DEFAULT_TTL="300"
```

---

## Code Patterns and Conventions

### 1. API Module Pattern

Create new API modules in `app/api/`:

```python
# app/api/my_domain.py
"""My domain API module."""

from app.api.base import BaseAPI
from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.ttl import TTL_LONG

class MyDomainAPI(BaseAPI):
    """API for my domain operations."""

    @cached(key_prefix="my_domain", ttl=TTL_LONG)
    async def get_items(self, search_query: str | None = None) -> list[dict]:
        """Get items with optional search filtering.

        Args:
            search_query: Optional search query to filter items.

        Returns:
            List of items matching the query.
        """
        response = await self._request("GET", "/api/my_domain")
        items = response.json()

        if search_query:
            items = [i for i in items if search_query.lower() in i["name"].lower()]

        return items

    @invalidate_cache(pattern="my_domain:*")
    async def create_item(self, config: dict) -> dict:
        """Create a new item.

        Args:
            config: Item configuration.

        Returns:
            Created item data.
        """
        response = await self._request("POST", "/api/my_domain", json=config)
        return response.json()
```

### 2. Tool Wrapper Pattern

Create thin wrappers in `app/tools/`:

```python
# app/tools/my_domain.py
"""My domain MCP tools."""

from app.api.my_domain import MyDomainAPI


async def get_items_tool(search_query: str | None = None) -> list[dict]:
    """Get items from my domain.

    Args:
        search_query: Optional search query to filter items.

    Returns:
        List of items.
    """
    return await MyDomainAPI().get_items(search_query=search_query)


async def create_item_tool(config: dict) -> dict:
    """Create a new item.

    Args:
        config: Item configuration with required fields.

    Returns:
        Created item data.
    """
    return await MyDomainAPI().create_item(config)
```

### 3. Server Registration Pattern

Register tools in `app/server.py`:

```python
# In app/server.py

# Import the tools module
from app.tools import my_domain

# Register tools with MCP
mcp.tool()(async_handler("get_my_domain_items")(my_domain.get_items_tool))
mcp.tool()(async_handler("create_my_domain_item")(my_domain.create_item_tool))
```

### 4. Caching Pattern

Use appropriate TTL presets:

```python
from app.core.cache.decorator import cached, invalidate_cache
from app.core.cache.ttl import (
    TTL_VERY_LONG,  # 1 hour - stable data (areas, zones, system config)
    TTL_LONG,       # 30 min - semi-stable (automations, scripts, devices)
    TTL_MEDIUM,     # 5 min - moderately dynamic (integrations)
    TTL_SHORT,      # 1 min - dynamic (entity states)
    TTL_DISABLED,   # 0 - no caching (logs, events)
)

@cached(key_prefix="my_data", ttl=TTL_LONG)
async def get_data():
    ...

@invalidate_cache(pattern="my_data:*")
async def update_data():
    ...
```

### 5. Error Handling Pattern

```python
from app.core.errors import HassAPIError

async def my_function():
    try:
        result = await api_call()
        return {"status": "success", "data": result}
    except HassAPIError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {e}"}
```

### 6. Type Hints

All functions must have type hints:

```python
async def get_entity(
    entity_id: str,
    fields: list[str] | None = None,
    detailed: bool = False,
) -> dict[str, Any]:
    """Get entity state.

    Args:
        entity_id: The entity ID (e.g., "light.living_room").
        fields: Optional list of specific fields to return.
        detailed: Whether to include all attributes.

    Returns:
        Entity state dictionary.
    """
    ...
```

---

## Testing Requirements

### Test Structure

```
tests/
├── conftest.py          # Fixtures and configuration
├── fixtures/            # Test data files
├── unit/                # Unit tests (mock httpx client)
│   ├── test_api_*.py    # Tests for app/api/ modules
│   └── test_core_*.py   # Tests for app/core/ modules
├── integration/         # Integration tests (may use real HA)
│   └── test_*.py        # End-to-end tool tests
└── performance/         # Performance tests
    └── test_*.py        # Benchmarks and load tests
```

### Writing Unit Tests

```python
# tests/unit/test_api_my_domain.py
"""Unit tests for my_domain API module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMyDomainAPI:
    """Tests for MyDomainAPI class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        mock = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "item1", "name": "Test"}]
        mock.get = AsyncMock(return_value=mock_response)
        return mock

    @pytest.mark.asyncio
    async def test_get_items_returns_list(self, mock_client):
        """Test that get_items returns a list of items."""
        with patch("app.api.my_domain.get_client", return_value=mock_client):
            from app.api.my_domain import MyDomainAPI

            result = await MyDomainAPI().get_items()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "item1"

    @pytest.mark.asyncio
    async def test_get_items_with_search(self, mock_client):
        """Test search filtering."""
        mock_client.get.return_value.json.return_value = [
            {"id": "item1", "name": "Living Room"},
            {"id": "item2", "name": "Kitchen"},
        ]

        with patch("app.api.my_domain.get_client", return_value=mock_client):
            from app.api.my_domain import MyDomainAPI

            result = await MyDomainAPI().get_items(search_query="living")

            assert len(result) == 1
            assert result[0]["name"] == "Living Room"
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
uv run pytest tests/unit/test_api_my_domain.py

# Specific test
uv run pytest tests/unit/test_api_my_domain.py::TestMyDomainAPI::test_get_items

# Verbose output
uv run pytest tests/ -vv

# With print statements
uv run pytest tests/ -s
```

### Coverage Requirements

- **Minimum >80%** overall coverage
- All new features must include tests
- Both success and error cases should be tested

---

## Adding New Features

### Step 1: Create API Module

1. Create `app/api/my_domain.py`
2. Inherit from `BaseAPI`
3. Implement business logic methods
4. Add appropriate caching decorators
5. Add type hints and docstrings

### Step 2: Create Tool Module

1. Create `app/tools/my_domain.py`
2. Create thin async wrapper functions
3. Add descriptive docstrings (used by MCP)

### Step 3: Register with Server

1. Import tool module in `app/server.py`
2. Register tools with `mcp.tool()(async_handler("name")(func))`

### Step 4: Add Tests

1. Create `tests/unit/test_api_my_domain.py`
2. Create `tests/unit/test_tools_my_domain.py` (optional)
3. Add integration tests if needed

### Step 5: Add Documentation

1. Create `docs/my-domain.md`
2. Add to `mkdocs.yml` navigation
3. Update `README.md` if significant feature

### Step 6: Verify

```bash
# Run tests
make test

# Check code quality
make check

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run -m app
```

---

## Code Quality and CI/CD

### Pre-commit Hooks

The project uses pre-commit hooks (`.pre-commit-config.yaml`):

- **pre-commit-hooks**: trailing whitespace, EOF, YAML/TOML/JSON check, merge conflicts
- **Ruff**: linting and formatting
- **Bandit**: security scanning

Run manually:
```bash
uv run pre-commit run --all-files
```

### Ruff Configuration

Key settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "PT", "RET", "PL"]
```

Notable ignored rules:
- `ARG001/ARG002`: Unused arguments (common in async handlers)
- `PLR0913`: Too many arguments (API methods often need many params)
- `PLW0603`: Global statement (acceptable for module-level client)

### MyPy Configuration

```toml
[tool.mypy]
python_version = "3.13"
disallow_untyped_defs = false  # Temporarily relaxed
check_untyped_defs = true
```

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | push, PR | Run test suite |
| `validate.yml` | push, PR | Lint, type check, security, coverage |
| `docker.yml` | push, PR | Build Docker image |
| `release.yml` | tag push | Publish to Docker Hub, PyPI |
| `docs-deploy.yml` | push to main | Deploy docs to GitHub Pages |

### CI Requirements Before Merge

1. ✅ All tests pass
2. ✅ No lint errors (Ruff)
3. ✅ Pre-commit hooks pass
4. ⚠️ Type check (non-blocking currently)
5. ✅ Security scan passes

---

## Common Tasks

### Adding a New Domain

```bash
# 1. Create API module
touch app/api/my_domain.py

# 2. Create tool module
touch app/tools/my_domain.py

# 3. Create test files
touch tests/unit/test_api_my_domain.py

# 4. Create documentation
touch docs/my-domain.md

# 5. Update server.py imports and registration
# 6. Update mkdocs.yml navigation
# 7. Run verification
make check test
```

### Debugging with MCP Inspector

```bash
# Start Inspector
npx @modelcontextprotocol/inspector uv run -m app

# With environment variables
HA_URL=http://localhost:8123 HA_TOKEN=token \
  npx @modelcontextprotocol/inspector uv run -m app
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package httpx

# Sync after lock
uv sync --extra dev
```

### Fixing Lint Issues

```bash
# Auto-fix what's possible
make lint-fix

# Format code
make format

# Check what's left
make lint
```

---

## Troubleshooting

### Import Errors

- Ensure you're importing from new module paths (`app.api.*`, `app.tools.*`)
- Legacy `app.hass` module was removed
- Check `app/server.py` for correct import paths

### Test Failures

```bash
# Verbose output
uv run pytest tests/ -vv

# See print statements
uv run pytest tests/ -s

# Run specific test
uv run pytest tests/path/to/test.py::TestClass::test_method
```

### Pre-commit Issues

```bash
# Update hooks
uv run pre-commit autoupdate

# Run specific hook
uv run pre-commit run ruff --verbose

# Skip hooks (not recommended)
git commit --no-verify
```

### Type Checking Errors

```bash
# Detailed mypy output
uv run mypy app/ --show-error-codes

# Ignore missing imports
uv run mypy app/ --ignore-missing-imports
```

---

## Additional Resources

- **Documentation Site**: https://mmornati.github.io/hass-mcp
- **Home Assistant API**: https://www.home-assistant.io/integrations/api/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp
- **Ruff**: https://docs.astral.sh/ruff/
- **uv**: https://docs.astral.sh/uv/

---

## Questions or Issues?

- Create an issue on GitHub
- Check existing documentation
- Review test files for usage examples
