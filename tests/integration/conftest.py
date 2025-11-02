"""Pytest configuration for integration tests."""

import os

import httpx
import pytest


def is_ha_available() -> bool:
    """Check if Home Assistant is available."""
    ha_url = os.environ.get("HA_URL")
    ha_token = os.environ.get("HA_TOKEN")

    if not ha_url or not ha_token:
        return False

    try:
        response = httpx.get(
            f"{ha_url}/api/",
            headers={"Authorization": f"Bearer {ha_token}"},
            timeout=2.0,
        )
        return response.status_code == 200
    except Exception:
        return False


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Register integration marker
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires real Home Assistant)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if HA is not available."""
    if not is_ha_available():
        skip_integration = pytest.mark.skip(
            reason="Home Assistant not available (set HA_URL and HA_TOKEN environment variables)"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


# Override the mocking from tests/conftest.py for integration tests
@pytest.fixture(autouse=True, scope="session")
def no_mock_env_for_integration():
    """Don't mock environment variables for integration tests."""
    # We want to use real environment variables, so we don't do anything here
    # This fixture exists to override the mock_env_vars from the parent conftest
    return


@pytest.fixture(autouse=True)
def cleanup_client_after_test():
    """Clean up HTTP client after each integration test."""
    from app.core.client import cleanup_client

    yield

    # Clean up the client after each test to avoid event loop issues
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        # Schedule cleanup in the event loop
        asyncio.create_task(cleanup_client())
    except RuntimeError:
        # No running loop, just reset the client
        import app.core.client

        app.core.client._client = None
