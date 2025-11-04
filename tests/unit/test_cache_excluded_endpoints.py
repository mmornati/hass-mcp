"""Unit tests for explicitly excluded dynamic data endpoints (US-006)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.automations import get_automation_execution_log
from app.api.entities import get_entity_history
from app.api.events import get_events
from app.api.logbook import get_entity_logbook, get_logbook, search_logbook
from app.api.statistics import analyze_usage_patterns, get_domain_statistics, get_entity_statistics
from app.api.system import get_hass_error_log, get_system_overview
from app.core.cache.manager import get_cache_manager


@pytest.fixture(autouse=True)
async def clear_cache_fixture():
    """Clear cache before each test to ensure isolation."""
    cache = await get_cache_manager()
    await cache.clear()
    yield
    await cache.clear()


class TestLogbookEndpointsNotCached:
    """Test that logbook endpoints are not cached."""

    @pytest.mark.asyncio
    async def test_get_logbook_not_cached(self):
        """Test that get_logbook is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Entity",
                "entity_id": "light.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.logbook._logbook_api._get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_logbook()
            assert isinstance(result1, list)

            # Verify cache is empty after first call
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_logbook()
            assert isinstance(result2, list)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries

    @pytest.mark.asyncio
    async def test_get_entity_logbook_not_cached(self):
        """Test that get_entity_logbook is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Entity",
                "entity_id": "light.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.logbook._logbook_api._get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_entity_logbook("light.test")
            assert isinstance(result1, list)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_entity_logbook("light.test")
            assert isinstance(result2, list)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries

    @pytest.mark.asyncio
    async def test_search_logbook_not_cached(self):
        """Test that search_logbook is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Entity",
                "entity_id": "light.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.logbook._logbook_api._get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await search_logbook("test")
            assert isinstance(result1, list)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await search_logbook("test")
            assert isinstance(result2, list)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries


class TestHistoryEndpointsNotCached:
    """Test that history endpoints are not cached."""

    @pytest.mark.asyncio
    async def test_get_entity_history_not_cached(self):
        """Test that get_entity_history is not cached."""
        mock_history = [[{"state": "on", "last_changed": "2025-01-01T10:00:00Z"}]]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_history
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.entities.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_entity_history("light.test", hours=24)
            assert isinstance(result1, list)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_entity_history("light.test", hours=24)
            assert isinstance(result2, list)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries


class TestStatisticsEndpointsNotCached:
    """Test that statistics endpoints are not cached."""

    @pytest.mark.asyncio
    async def test_get_entity_statistics_not_cached(self):
        """Test that get_entity_statistics is not cached."""
        mock_history = [
            [
                {"state": "20.5", "last_changed": "2025-01-01T10:00:00Z"},
                {"state": "21.0", "last_changed": "2025-01-01T11:00:00Z"},
            ]
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_history
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.entities.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_entity_statistics("sensor.temperature", period_days=7)
            assert isinstance(result1, dict)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_entity_statistics("sensor.temperature", period_days=7)
            assert isinstance(result2, dict)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries

    @pytest.mark.asyncio
    async def test_get_domain_statistics_not_cached(self):
        """Test that get_domain_statistics is not cached."""
        mock_entities = [{"entity_id": "sensor.temperature", "state": "20.5"}]
        mock_history = [
            [
                {"state": "20.5", "last_changed": "2025-01-01T10:00:00Z"},
            ]
        ]
        mock_client = AsyncMock()
        mock_response_entities = MagicMock()
        mock_response_entities.json.return_value = mock_entities
        mock_response_entities.raise_for_status = MagicMock()
        mock_response_history = MagicMock()
        mock_response_history.json.return_value = mock_history
        mock_response_history.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(side_effect=[mock_response_entities, mock_response_history])

        with (
            patch("app.api.entities.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_domain_statistics("sensor", period_days=7)
            assert isinstance(result1, dict)

            # Verify no cache entries for statistics endpoints
            # (get_domain_statistics calls get_entities which is cached, so there may be entities:* entries)
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            # Check that there are no cache entries for statistics endpoints specifically
            stats_keys = [
                k for k in keys if "statistics" in k.lower() or "domain_statistics" in k.lower()
            ]
            assert len(stats_keys) == 0  # No statistics cache entries

            # Second call - should NOT be cached
            result2 = await get_domain_statistics("sensor", period_days=7)
            assert isinstance(result2, dict)

            # Verify still no statistics cache entries
            keys = await cache.keys("*")
            stats_keys = [
                k for k in keys if "statistics" in k.lower() or "domain_statistics" in k.lower()
            ]
            assert len(stats_keys) == 0  # Still no statistics cache entries

    @pytest.mark.asyncio
    async def test_analyze_usage_patterns_not_cached(self):
        """Test that analyze_usage_patterns is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Entity",
                "entity_id": "light.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.logbook._logbook_api._get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await analyze_usage_patterns("light.test", days=30)
            assert isinstance(result1, dict)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await analyze_usage_patterns("light.test", days=30)
            assert isinstance(result2, dict)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries


class TestEventsEndpointsNotCached:
    """Test that events endpoints are not cached."""

    @pytest.mark.asyncio
    async def test_get_events_not_cached(self):
        """Test that get_events is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Entity",
                "entity_id": "light.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.logbook._logbook_api._get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_events(entity_id="light.test", hours=1)
            assert isinstance(result1, list)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_events(entity_id="light.test", hours=1)
            assert isinstance(result2, list)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries


class TestAutomationExecutionLogNotCached:
    """Test that automation execution logs are not cached."""

    @pytest.mark.asyncio
    async def test_get_automation_execution_log_not_cached(self):
        """Test that get_automation_execution_log is not cached."""
        mock_logbook = [
            {
                "when": "2025-01-01T10:00:00Z",
                "name": "Test Automation",
                "entity_id": "automation.test",
                "state": "on",
            }
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.automations.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_automation_execution_log("test", hours=24)
            assert isinstance(result1, dict)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_automation_execution_log("test", hours=24)
            assert isinstance(result2, dict)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries


class TestSystemEndpointsNotCached:
    """Test that dynamic system endpoints are not cached."""

    @pytest.mark.asyncio
    async def test_get_hass_error_log_not_cached(self):
        """Test that get_hass_error_log is not cached."""
        mock_error_log = "ERROR: Test error message\nWARNING: Test warning"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = mock_error_log
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.system.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_hass_error_log()
            assert isinstance(result1, dict)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_hass_error_log()
            assert isinstance(result2, dict)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries

    @pytest.mark.asyncio
    async def test_get_system_overview_not_cached(self):
        """Test that get_system_overview is not cached."""
        mock_entities = [
            {"entity_id": "light.test", "state": "on", "attributes": {"friendly_name": "Test"}}
        ]
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_entities
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("app.api.system.get_client", return_value=mock_client),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            # First call
            result1 = await get_system_overview()
            assert isinstance(result1, dict)

            # Verify cache is empty
            cache = await get_cache_manager()
            keys = await cache.keys("*")
            assert len(keys) == 0  # No cache entries

            # Second call - should NOT be cached
            result2 = await get_system_overview()
            assert isinstance(result2, dict)

            # Verify cache is still empty
            keys = await cache.keys("*")
            assert len(keys) == 0  # Still no cache entries
