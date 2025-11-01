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
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables to prevent tests from using real credentials."""
    with patch.dict(
        os.environ, {"HA_URL": "http://localhost:8123", "HA_TOKEN": "mock_token_for_tests"}
    ):
        yield


# Mock httpx client
@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for testing."""
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
def mock_get_client(mock_httpx_client):
    """Mock the get_client function to return our mock client."""
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
