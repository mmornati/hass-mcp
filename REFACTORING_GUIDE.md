# 🏗️ Hass-MCP Refactoring and Modularization Guide

This guide provides detailed instructions for implementing the project modularization across 5 phases. All work has been organized into GitHub issues (#29-#54).

## 📚 Quick Links

- **Epic Overview**: https://github.com/mmornati/hass-mcp/issues/28
- **Roadmap & Summary**: https://github.com/mmornati/hass-mcp/issues/55
- **All Issues**: See project board for current status

## 🎯 Overall Strategy

### Goal
Transform the project from monolithic files (2000+ lines) into a modular architecture organized by domain, improving maintainability, testability, and making it easier to add new features.

### Architecture

```
app/
├── core/                          # Shared infrastructure
│   ├── __init__.py
│   ├── client.py                 # HTTP client management
│   ├── decorators.py             # Async handlers, error decorators
│   ├── errors.py                 # Error handling utilities
│   └── types.py                  # Shared type definitions
│
├── api/                          # API layer (business logic)
│   ├── __init__.py
│   ├── base.py                   # Base class for API calls
│   ├── entities.py               # Entity management
│   ├── automations.py            # Automation CRUD & execution
│   ├── scripts.py                # Script management
│   ├── devices.py                # Device management
│   ├── areas.py                  # Area management
│   ├── scenes.py                 # Scene management
│   ├── integrations.py           # Integration management
│   ├── system.py                 # System functions
│   ├── services.py               # Service calls
│   ├── templates.py              # Template testing
│   ├── logbook.py                # [NEW] Logbook access
│   ├── statistics.py             # [NEW] Statistics & analytics
│   ├── diagnostics.py            # [NEW] Debugging tools
│   ├── blueprints.py             # [NEW] Blueprints
│   ├── zones.py                  # [NEW] Zones
│   ├── events.py                 # [NEW] Events
│   ├── notifications.py          # [NEW] Notifications
│   ├── calendars.py              # [NEW] Calendars
│   ├── helpers.py                # [NEW] Input helpers
│   ├── tags.py                   # [NEW] Tags
│   ├── webhooks.py               # [NEW] Webhooks
│   └── backups.py                # [NEW] Backups & restore
│
├── tools/                        # MCP Tool layer (thin wrappers)
│   ├── __init__.py
│   ├── entities.py               # Entity MCP tools
│   ├── automations.py            # Automation MCP tools
│   ├── scripts.py                # Script MCP tools
│   ├── devices.py                # Device MCP tools
│   ├── areas.py                  # Area MCP tools
│   ├── scenes.py                 # Scene MCP tools
│   ├── integrations.py           # Integration MCP tools
│   ├── system.py                 # System MCP tools
│   ├── services.py               # Service MCP tools
│   ├── templates.py              # Template MCP tools
│   └── [matching api/]           # Tools for new domains
│
├── server.py                     # [REFACTORED] MCP orchestration (~100 lines)
├── config.py                     # Configuration
├── run.py                        # Entry point
└── __main__.py                   # Main module
```

## 📋 Implementation Phases

### Phase 1: Core Infrastructure (#29)
**Duration**: ~2-4 hours
**Complexity**: Easy (single issue, no dependencies)

**Tasks**:
- Extract `core/client.py` - HTTP client management
- Extract `core/decorators.py` - Async handlers and error decorators
- Extract `core/errors.py` - Error handling utilities
- Extract `core/types.py` - Shared type definitions
- Create unit tests for each module
- Maintain backwards compatibility

**Key Files to Modify**:
- `app/hass.py` → import from `core/`
- `app/server.py` → import from `core/`
- Create `app/core/` module

**Validation**:
```bash
pytest tests/unit/test_core_*
# All tests should pass
# No imports should fail
```

---

### Phase 2: API Layer Refactoring (#30-#37)
**Duration**: ~15-20 hours (can be parallelized)
**Complexity**: Medium (8 issues, linear but interdependent)

#### Phase 2.1: Base API and Entities (#30)
**Prerequisites**: #29 complete
**Key Pattern**: This establishes the pattern for all subsequent API modules

**Tasks**:
- Create `api/base.py` with `BaseAPI` class
- Create `api/entities.py` by extracting from `hass.py`
- Implement lean/detailed response filtering
- Create unit tests
- Ensure `hass.py` re-exports for backwards compatibility

**Code Pattern**:
```python
# api/base.py
class BaseAPI:
    async def _get(self, endpoint, **kwargs): ...
    async def _post(self, endpoint, data, **kwargs): ...
    # Common patterns shared across domains

# api/entities.py
class EntitiesAPI(BaseAPI):
    async def get_entities(self, domain=None, lean=True): ...
    async def get_entity_state(self, entity_id, lean=False): ...

# hass.py (for backwards compat)
from api.entities import EntitiesAPI
_entities_api = EntitiesAPI()
async def get_entities(*args, **kwargs):
    return await _entities_api.get_entities(*args, **kwargs)
```

#### Phases 2.2-2.8: Additional Domains
**Prerequisites**: #30 complete, parallel execution ok
**Pattern**: Same pattern established in 2.1

Each issue extracts one or two related domains:
- #31: Automations
- #32: Scripts
- #33: Devices
- #34: Areas
- #35: Scenes
- #36: Integrations & System
- #37: Services & Templates

**Tasks** (for each):
1. Create `api/{domain}.py`
2. Extract related functions from `hass.py`
3. Follow `BaseAPI` pattern
4. Create unit tests
5. Update `hass.py` to re-export

**Validation**:
```bash
pytest tests/unit/test_api_*
# All tests should pass
# Coverage should be > 80%
```

---

### Phase 3: Tools Layer Refactoring (#38-#40)
**Duration**: ~8-10 hours (can be parallelized)
**Complexity**: Medium (3 issues, parallel possible)

**Prerequisites**: Phase 2 complete

#### Phase 3.1: Entities Tools (#38)
**Key Pattern**: This establishes tool extraction pattern

**Tasks**:
- Create `tools/entities.py`
- Extract `@mcp.tool()` decorated functions from `server.py`
- Import from `api/entities.py`
- Keep functions as thin wrappers (no business logic)
- Create integration tests

**Code Pattern**:
```python
# tools/entities.py
from app.api.entities import EntitiesAPI

_entities_api = EntitiesAPI()

@mcp.tool()
async def get_entity(entity_id: str, fields=None, detailed=False):
    """Get entity state and details."""
    return await _entities_api.get_entity_state(entity_id, lean=not detailed)

# server.py
from app.tools import entities
# That's it - decorators register automatically
```

#### Phases 3.2-3.3: Additional Tools
**Pattern**: Same as 3.1

Each issue extracts tools for multiple domains:
- #39: Automations, Scripts, Devices, Areas tools
- #40: Scenes, Integrations, System, Services, Templates tools

**Tasks** (for each):
1. Create `tools/{domain}.py`
2. Extract `@mcp.tool()` functions from `server.py`
3. Import from `api/{domain}.py`
4. Update `server.py` to import from tools
5. Create integration tests

**Validation**:
```bash
pytest tests/integration/test_tools_*
# All tools should register
# All existing functionality should work
```

---

### Phase 4: New Features (#41-#52)
**Duration**: ~20-30 hours (high parallelization possible)
**Complexity**: Easy-Medium (12 issues, independent)

**Prerequisites**: Phase 3 complete

Each feature follows same pattern:

1. **Create API Module**: `api/{domain}.py`
   - Implement all functions
   - Use `BaseAPI` pattern
   - Handle errors properly

2. **Create Tools Module**: `tools/{domain}.py`
   - Implement `@mcp.tool()` functions
   - Import from `api/{domain}.py`
   - Validate parameters

3. **Update `server.py`**:
   - Import `tools.{domain}`

4. **Testing**:
   - Create `tests/unit/test_api_{domain}.py`
   - Create `tests/integration/test_tools_{domain}.py`

5. **Documentation**:
   - Add docstrings
   - Update README

**Features to Implement**:
- #41: Logbook Access (Issue #11)
- #42: Statistics & Analytics (Issue #12)
- #43: Debugging & Diagnostics (Issue #8)
- #44: Blueprints Management (Issue #9)
- #45: Zones Management (Issue #10)
- #46: Events Management (Issue #15)
- #47: Notifications & Alerting (Issue #14)
- #48: Calendar Management (Issue #13)
- #49: Helpers Management (Issue #17)
- #50: Tags Management (Issue #16)
- #51: Webhooks Management (Issue #18)
- #52: Backup & Restore (Issue #19)

**Code Example** (Logbook):
```python
# api/logbook.py
class LogbookAPI(BaseAPI):
    async def get_logbook(self, timestamp=None, entity_id=None, hours=24):
        """Get logbook entries for a time range."""
        # Implementation

# tools/logbook.py
from app.api.logbook import LogbookAPI

_logbook_api = LogbookAPI()

@mcp.tool()
async def get_logbook(timestamp=None, entity_id=None, hours=24):
    """Get logbook entries."""
    return await _logbook_api.get_logbook(timestamp, entity_id, hours)

# server.py
from app.tools import logbook
```

**Validation**:
```bash
pytest tests/unit/test_api_*
pytest tests/integration/test_tools_*
# All new features working
```

---

### Phase 5: Legacy Cleanup (#54)
**Duration**: ~4-6 hours
**Complexity**: Easy

**Prerequisites**: All other phases complete

**Tasks**:
1. Remove `app/hass.py` (all functionality in `api/`)
2. Update all imports throughout codebase
3. Update tests to use new import paths
4. Optimize `server.py` (should be ~100 lines now)
5. Run full quality checks
6. Update documentation

**Validation**:
```bash
# Full test suite
pytest

# Code quality
ruff check app tests
mypy app tests
bandit -r app

# No direct imports from hass.py should exist
grep -r "from app.hass import" app tests
# Should return nothing
```

---

## 🧪 Testing Strategy

### Unit Tests
- **Location**: `tests/unit/test_*.py`
- **What**: Test individual API functions in isolation
- **Mocking**: Mock HTTP calls, use fixtures
- **Coverage**: Aim for 100% coverage per module

### Integration Tests
- **Location**: `tests/integration/test_*.py`
- **What**: Test MCP tool registration and wrappers
- **Mocking**: May use real HTTP or mocks
- **Focus**: Tool parameter validation, response formatting

### Test Organization

```
tests/
├── unit/
│   ├── test_core_client.py
│   ├── test_core_decorators.py
│   ├── test_core_errors.py
│   ├── test_api_base.py
│   ├── test_api_entities.py
│   ├── test_api_automations.py
│   └── [test_api_*.py for each domain]
│
├── integration/
│   ├── test_tools_entities.py
│   ├── test_tools_automations.py
│   └── [test_tools_*.py for each domain]
│
├── conftest.py                  # Shared fixtures
├── fixtures/                    # Fixture data
│   ├── automations.py
│   ├── devices.py
│   └── [fixtures for each domain]
```

### Fixture Pattern

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
async def mock_ha_client():
    """Mock Home Assistant HTTP client."""
    client = AsyncMock()
    # Configure mocks
    return client

@pytest.fixture
async def entities_api(mock_ha_client):
    """Provide EntitiesAPI with mocked client."""
    from app.api.entities import EntitiesAPI
    api = EntitiesAPI()
    api._client = mock_ha_client
    return api
```

---

## 📝 Implementation Checklist

For each issue implementation:

### Before Starting
- [ ] Read issue description carefully
- [ ] Understand dependencies
- [ ] Review related code in current codebase
- [ ] Check if tests already exist

### Implementation
- [ ] Create new module(s) as specified
- [ ] Extract code from existing files
- [ ] Update imports in existing files
- [ ] Maintain backwards compatibility (until Phase 5)
- [ ] Add docstrings and type hints
- [ ] Handle errors properly

### Testing
- [ ] Write unit tests for API functions
- [ ] Write integration tests for tools
- [ ] Ensure all tests pass
- [ ] Check code coverage (target 80%+)
- [ ] Test backwards compatibility if applicable

### Code Quality
- [ ] Run `ruff check` - must pass
- [ ] Run `mypy` - must pass
- [ ] Run `bandit` - must pass
- [ ] Code follows existing patterns

### Documentation
- [ ] Add module docstring
- [ ] Add function docstrings
- [ ] Update README if adding new features
- [ ] Add examples if appropriate

### Submission
- [ ] All tests passing
- [ ] Code quality checks passing
- [ ] Issue marked as complete
- [ ] PR includes tests and documentation

---

## 🔗 Key Files Reference

### Configuration
- `pyproject.toml` - Project configuration
- `README.md` - Project documentation
- `.env.example` - Environment variables

### Main Application
- `app/__init__.py` - Package initialization
- `app/config.py` - Configuration loading
- `app/run.py` - Application entry point
- `app/__main__.py` - Main module

### During Phase 1
- `app/core/client.py` - HTTP client (NEW)
- `app/core/decorators.py` - Decorators (NEW)
- `app/core/errors.py` - Error handling (NEW)
- `app/core/types.py` - Type definitions (NEW)

### During Phase 2
- `app/api/__init__.py` - API package (NEW)
- `app/api/base.py` - Base class (NEW)
- `app/api/entities.py` - Entities API (NEW, from hass.py)
- `app/api/automations.py` - Automations API (NEW, from hass.py)
- [etc. for each domain]

### During Phase 3
- `app/tools/__init__.py` - Tools package (NEW)
- `app/tools/entities.py` - Entities tools (NEW, from server.py)
- `app/tools/automations.py` - Automations tools (NEW, from server.py)
- [etc. for each domain]

### Tests
- `tests/conftest.py` - Test configuration (UPDATE)
- `tests/unit/` - Unit tests directory (NEW)
- `tests/integration/` - Integration tests directory (NEW)

---

## 💡 Tips for Implementation

### Pattern Recognition
1. **Read existing code carefully** - Understand current patterns before refactoring
2. **Follow the established pattern** - Each phase builds on previous
3. **Test as you go** - Don't wait until the end

### Common Issues & Solutions

**Issue**: Import errors after extraction
**Solution**: Update `__init__.py` files to re-export functions for backwards compatibility

**Issue**: Tests failing due to mocks
**Solution**: Create shared fixtures in `tests/conftest.py` for reuse

**Issue**: Circular imports
**Solution**: Move shared code to `core/` module; tools import from api, not vice versa

**Issue**: Lost functionality
**Solution**: Always keep backwards compatibility layer until Phase 5

### Performance Considerations

- HTTP client connection pooling (already handled)
- Lean vs detailed response filtering (important for token efficiency)
- Error handling consistency across domains

---

## 🚀 Getting Started

1. **Start with Phase 1** (#29) - Sets up foundation
2. **Validate each phase** - Run full test suite
3. **Follow dependencies** - Respect issue ordering
4. **Parallelize where possible** - Issues can run in parallel if dependencies met
5. **Document as you go** - Makes Phase 5 easier

## 📞 Questions?

Refer to:
- **Epic**: https://github.com/mmornati/hass-mcp/issues/28
- **Roadmap**: https://github.com/mmornati/hass-mcp/issues/55
- **Each Issue**: Contains detailed tasks and acceptance criteria

---

## 🎯 Final Checklist

After ALL phases complete:
- [ ] All issues (#29-#54) closed
- [ ] Full test suite passing
- [ ] Code coverage > 80%
- [ ] All code quality checks passing
- [ ] Documentation updated
- [ ] README reflects new architecture
- [ ] No backwards compatibility layer remaining (Phase 5)
- [ ] Project ready for continued development

Good luck! 🚀
