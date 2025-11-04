"""Unit tests for app.api.helpers module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.helpers import get_helper, list_helpers, update_helper
from app.core.cache.manager import get_cache_manager


class TestListHelpers:
    """Test the list_helpers function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test to ensure isolation."""
        cache = await get_cache_manager()
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_list_helpers_success_all(self):
        """Test successful retrieval of all helpers."""

        def mock_get_entities(domain=None, **kwargs):
            """Return entities based on domain."""
            if domain == "input_boolean":
                return [
                    {
                        "entity_id": "input_boolean.work_from_home",
                        "state": "on",
                        "attributes": {"friendly_name": "Work From Home"},
                    }
                ]
            if domain == "input_number":
                return [
                    {
                        "entity_id": "input_number.temperature",
                        "state": "22.5",
                        "attributes": {"friendly_name": "Temperature", "min": 0, "max": 100},
                    }
                ]
            return []

        with patch("app.api.helpers.get_entities", side_effect=mock_get_entities):
            result = await list_helpers()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "input_boolean.work_from_home"
            assert result[0]["domain"] == "input_boolean"
            assert result[0]["friendly_name"] == "Work From Home"
            assert result[1]["entity_id"] == "input_number.temperature"
            assert result[1]["domain"] == "input_number"

    @pytest.mark.asyncio
    async def test_list_helpers_with_type_filter(self):
        """Test filtering by helper type."""
        mock_entities = [
            {
                "entity_id": "input_boolean.work_from_home",
                "state": "on",
                "attributes": {"friendly_name": "Work From Home"},
            }
        ]

        with patch("app.api.helpers.get_entities", return_value=mock_entities):
            result = await list_helpers(helper_type="input_boolean")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "input_boolean.work_from_home"
            assert result[0]["domain"] == "input_boolean"

    @pytest.mark.asyncio
    async def test_list_helpers_empty(self):
        """Test when no helpers are found."""
        with patch("app.api.helpers.get_entities", return_value=[]):
            result = await list_helpers()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_helpers_invalid_type(self):
        """Test with invalid helper type."""
        with patch("app.api.helpers.get_entities", return_value=[]):
            result = await list_helpers(helper_type="invalid_type")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_helpers_missing_attributes(self):
        """Test when helpers have missing attributes."""

        def mock_get_entities(domain=None, **kwargs):
            """Return entities based on domain."""
            if domain == "input_text":
                return [
                    {
                        "entity_id": "input_text.name",
                        "state": "John",
                        "attributes": {},
                    }
                ]
            return []

        with patch("app.api.helpers.get_entities", side_effect=mock_get_entities):
            result = await list_helpers()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "input_text.name"
            assert result[0]["friendly_name"] is None


class TestGetHelper:
    """Test the get_helper function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_helper_success_with_domain(self):
        """Test successful retrieval with full entity_id."""
        mock_entity_state = {
            "entity_id": "input_boolean.work_from_home",
            "state": "on",
            "attributes": {"friendly_name": "Work From Home"},
        }

        with patch("app.api.helpers.get_entity_state", return_value=mock_entity_state):
            result = await get_helper("input_boolean.work_from_home")

            assert isinstance(result, dict)
            assert result["entity_id"] == "input_boolean.work_from_home"
            assert result["state"] == "on"

    @pytest.mark.asyncio
    async def test_get_helper_success_without_domain(self):
        """Test successful retrieval without domain (search by name)."""
        mock_helpers = [
            {
                "entity_id": "input_boolean.work_from_home",
                "domain": "input_boolean",
                "state": "on",
                "friendly_name": "Work From Home",
                "attributes": {},
            }
        ]
        mock_entity_state = {
            "entity_id": "input_boolean.work_from_home",
            "state": "on",
            "attributes": {"friendly_name": "Work From Home"},
        }

        with (
            patch("app.api.helpers.list_helpers", return_value=mock_helpers),
            patch("app.api.helpers.get_entity_state", return_value=mock_entity_state),
        ):
            result = await get_helper("work_from_home")

            assert isinstance(result, dict)
            assert result["entity_id"] == "input_boolean.work_from_home"

    @pytest.mark.asyncio
    async def test_get_helper_not_found(self):
        """Test when helper is not found."""
        with patch("app.api.helpers.list_helpers", return_value=[]):
            result = await get_helper("nonexistent")

            assert isinstance(result, dict)
            assert "error" in result
            assert "not found" in result["error"].lower()


class TestUpdateHelper:
    """Test the update_helper function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_update_helper_input_boolean_true(self):
        """Test updating input_boolean with True."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_boolean.work_from_home", True)

            assert result == []
            mock_call.assert_called_once_with(
                "input_boolean", "turn_on", {"entity_id": "input_boolean.work_from_home"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_input_boolean_false(self):
        """Test updating input_boolean with False."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_boolean.work_from_home", False)

            assert result == []
            mock_call.assert_called_once_with(
                "input_boolean", "turn_off", {"entity_id": "input_boolean.work_from_home"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_input_boolean_string(self):
        """Test updating input_boolean with string values."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_boolean.work_from_home", "on")

            assert result == []
            mock_call.assert_called_once_with(
                "input_boolean", "turn_on", {"entity_id": "input_boolean.work_from_home"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_input_number(self):
        """Test updating input_number."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_number.temperature", 22.5)

            assert result == []
            mock_call.assert_called_once_with(
                "input_number",
                "set_value",
                {"entity_id": "input_number.temperature", "value": 22.5},
            )

    @pytest.mark.asyncio
    async def test_update_helper_input_text(self):
        """Test updating input_text."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_text.name", "John")

            assert result == []
            mock_call.assert_called_once_with(
                "input_text", "set_value", {"entity_id": "input_text.name", "value": "John"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_input_select(self):
        """Test updating input_select."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_select.mode", "home")

            assert result == []
            mock_call.assert_called_once_with(
                "input_select",
                "select_option",
                {"entity_id": "input_select.mode", "option": "home"},
            )

    @pytest.mark.asyncio
    async def test_update_helper_counter_increment(self):
        """Test incrementing counter."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("counter.steps", "+")

            assert result == []
            mock_call.assert_called_once_with(
                "counter", "increment", {"entity_id": "counter.steps"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_counter_decrement(self):
        """Test decrementing counter."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("counter.steps", "-")

            assert result == []
            mock_call.assert_called_once_with(
                "counter", "decrement", {"entity_id": "counter.steps"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_counter_set_value(self):
        """Test setting counter value."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("counter.steps", 10)

            assert result == []
            mock_call.assert_called_once_with(
                "counter", "set_value", {"entity_id": "counter.steps", "value": 10}
            )

    @pytest.mark.asyncio
    async def test_update_helper_timer_start(self):
        """Test starting timer."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("timer.countdown", "start")

            assert result == []
            mock_call.assert_called_once_with("timer", "start", {"entity_id": "timer.countdown"})

    @pytest.mark.asyncio
    async def test_update_helper_timer_pause(self):
        """Test pausing timer."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("timer.countdown", "pause")

            assert result == []
            mock_call.assert_called_once_with("timer", "pause", {"entity_id": "timer.countdown"})

    @pytest.mark.asyncio
    async def test_update_helper_timer_cancel(self):
        """Test canceling timer."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("timer.countdown", "cancel")

            assert result == []
            mock_call.assert_called_once_with("timer", "cancel", {"entity_id": "timer.countdown"})

    @pytest.mark.asyncio
    async def test_update_helper_timer_invalid_action(self):
        """Test timer with invalid action."""
        result = await update_helper("timer.countdown", "invalid")

        assert isinstance(result, dict)
        assert "error" in result
        assert "Unknown timer action" in result["error"]

    @pytest.mark.asyncio
    async def test_update_helper_input_button(self):
        """Test pressing input_button."""
        with patch("app.api.helpers.call_service", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            result = await update_helper("input_button.press_me", "any_value")

            assert result == []
            mock_call.assert_called_once_with(
                "input_button", "press", {"entity_id": "input_button.press_me"}
            )

    @pytest.mark.asyncio
    async def test_update_helper_unsupported_type(self):
        """Test updating unsupported helper type."""
        result = await update_helper("invalid_type.helper", "value")

        assert isinstance(result, dict)
        assert "error" in result
        assert "Cannot update helper" in result["error"]
