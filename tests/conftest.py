import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_collection_modifyitems(config, items):
    """Filter out test items from application code (not test files)."""
    filtered_items = []
    for item in items:
        # Skip test_* functions from application code - they're application functions, not tests
        # When imported into test files, pytest tries to collect them as tests
        if hasattr(item, "name") and (
            item.name == "test_template"
            or item.name == "test_notification_delivery"
            or item.name == "test_webhook"
        ):
            # Check if this is actually the function from app/api modules
            # by checking the item's location
            try:
                if hasattr(item, "location"):
                    location = item.location
                    if location and len(location) > 0:
                        file_path = location[0]
                        # Skip if it's from the templates, notifications, or webhooks module
                        if (
                            "app/api/templates.py" in file_path
                            or "app/api/notifications.py" in file_path
                            or "app/api/webhooks.py" in file_path
                            or (
                                (
                                    "templates.py" in file_path
                                    or "notifications.py" in file_path
                                    or "webhooks.py" in file_path
                                )
                                and "/app/" in file_path
                            )
                        ):
                            continue
            except Exception:
                # If we can't determine location, skip if nodeid suggests it's from app/
                if hasattr(item, "nodeid"):
                    nodeid = str(item.nodeid)
                    # Skip if nodeid doesn't match a real test pattern
                    # (all real tests are test_test_*_*)
                    if (
                        (
                            "test_template" in nodeid
                            or "test_notification_delivery" in nodeid
                            or "test_webhook" in nodeid
                        )
                        and "test_test_template" not in nodeid
                        and "test_test_notification" not in nodeid
                        and "test_test_webhook" not in nodeid
                    ):
                        # Check if it's actually from app/ modules
                        if (
                            "app/api/templates" in nodeid
                            or "app/api/notifications" in nodeid
                            or "app/api/webhooks" in nodeid
                            or (
                                ("test_api_templates" in nodeid and "::test_template" in nodeid)
                                or (
                                    "test_api_notifications" in nodeid
                                    and "::test_notification_delivery" in nodeid
                                )
                                or ("test_api_webhooks" in nodeid and "::test_webhook" in nodeid)
                            )
                        ):
                            continue

        # Skip functions from app/ directory that aren't in test files
        item_path = None
        if hasattr(item, "fspath"):
            item_path = str(item.fspath)
        elif hasattr(item, "path"):
            item_path = str(item.path)

        if item_path and "/app/" in item_path and "/tests/" not in item_path:
            continue

        filtered_items.append(item)
    items[:] = filtered_items


# Mock environment variables before imports
# Only apply to non-integration tests
def _is_integration_test(request) -> bool:
    """Check if this test is marked as an integration test."""
    try:
        # Check if the test has the integration marker
        # This works for both function and class markers
        if hasattr(request, "keywords") and "integration" in request.keywords:
            return True
        # Also check the item's path for integration tests directory
        if hasattr(request, "path") and "integration" in str(request.path):
            return True
        # Check nodeid for integration tests
        return hasattr(request, "nodeid") and "/integration/" in str(request.nodeid)
    except Exception:
        return False


@pytest.fixture(autouse=True)
def mock_env_vars(request):
    """Mock environment variables to prevent tests from using real credentials."""
    # Skip mocking for integration tests
    if _is_integration_test(request):
        yield
        return

    with patch.dict(
        os.environ, {"HA_URL": "http://localhost:8123", "HA_TOKEN": "mock_token_for_tests"}
    ):
        yield


# Mock httpx client
@pytest.fixture
def mock_httpx_client(request):
    """Create a mock httpx client for testing."""
    # Skip mocking for integration tests
    if _is_integration_test(request):
        yield None
        return

    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={})
    mock_response.raise_for_status = MagicMock()
    mock_response.text = ""

    # Set up methods to return the mock response
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)

    # Create a patched httpx.AsyncClient constructor
    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client


# Patch app.core.client.get_client and all API modules
@pytest.fixture(autouse=True)
def mock_get_client(request, mock_httpx_client):
    """Mock the get_client function to return our mock client."""
    # Skip mocking for integration tests
    if _is_integration_test(request):
        yield None
        return

    # If mock_httpx_client is None (for integration tests), skip
    if mock_httpx_client is None:
        yield None
        return

    with (
        patch("app.core.client.get_client", return_value=mock_httpx_client),
        patch("app.api.automations.get_client", return_value=mock_httpx_client),
        patch("app.api.entities.get_client", return_value=mock_httpx_client),
        patch("app.api.scenes.get_client", return_value=mock_httpx_client),
        patch("app.api.integrations.get_client", return_value=mock_httpx_client),
        patch("app.api.system.get_client", return_value=mock_httpx_client),
        patch("app.api.services.get_client", return_value=mock_httpx_client),
        patch("app.api.templates.get_client", return_value=mock_httpx_client),
        patch("app.api.webhooks.get_client", return_value=mock_httpx_client),
        patch("app.api.backups.get_client", return_value=mock_httpx_client),
        patch("app.api.areas.get_client", return_value=mock_httpx_client),
        patch("app.api.base.get_client", return_value=mock_httpx_client),
    ):
        yield mock_httpx_client


# Mock HA session
@pytest.fixture
def mock_hass_session():
    """Create a mock Home Assistant session."""
    mock_session = MagicMock()

    # Mock common methods
    mock_session.get = MagicMock()
    mock_session.post = MagicMock()
    mock_session.delete = MagicMock()

    # Configure default returns
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json = MagicMock(return_value={})

    mock_session.post.return_value.__aenter__.return_value.status = 200
    mock_session.post.return_value.__aenter__.return_value.json = MagicMock(return_value={})

    mock_session.delete.return_value.__aenter__.return_value.status = 200
    mock_session.delete.return_value.__aenter__.return_value.json = MagicMock(return_value={})

    return mock_session


# Mock config
@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "hass_url": "http://localhost:8123",
        "hass_token": "mock_token",
        "config_dir": "/Users/matt/Developer/hass-mcp/config",
        "log_level": "INFO",
    }


# Clear cache before each test to prevent interference between tests
# Note: We use separate fixtures for sync and async tests to avoid hanging
@pytest.fixture(autouse=True)
def clear_cache_before_test_sync(request):
    """Clear cache before each test (sync version for sync tests)."""
    # Skip for integration tests
    if _is_integration_test(request):
        yield
        return

    # Check if this is a synchronous test that doesn't need cache
    test_nodeid = getattr(request.node, "nodeid", "")
    is_sync_metrics_test = (
        "test_cache_metrics" in test_nodeid
        and "TestCacheMetrics" in test_nodeid
        and "test_cache_manager" not in test_nodeid
        and "TestCacheMetricsIntegration" not in test_nodeid
    )

    # Check if test is marked as async
    is_async_test = False
    if hasattr(request.node, "pytestmark"):
        for mark in request.node.pytestmark:
            if mark.name == "asyncio":
                is_async_test = True
                break

    # If it's a sync metrics test and not async, skip cache clearing
    if is_sync_metrics_test and not is_async_test:
        yield
        return

    # For async tests, skip this sync fixture (they'll use the async one)
    if is_async_test:
        yield
        return

    # For other sync tests that need cache, skip clearing to avoid async issues
    # Individual test files can provide their own cache clearing fixtures
    yield


# Note: We don't use autouse for async fixture to avoid pytest-asyncio
# trying to create event loops for sync tests. Async tests will use
# their own cache clearing fixtures in their test files.
