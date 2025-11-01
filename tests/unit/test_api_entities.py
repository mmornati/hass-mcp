"""Unit tests for app.api.entities module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.entities import (
    filter_fields,
    get_all_entity_states,
    get_entities,
    get_entity_history,
    get_entity_state,
)


class TestFilterFields:
    """Test the filter_fields function."""

    def test_filter_fields_empty_fields(self):
        """Test filter_fields with empty fields list returns all data."""
        data = {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}}
        result = filter_fields(data, [])
        assert result == data

    def test_filter_fields_none_fields(self):
        """Test filter_fields with None fields returns all data."""
        data = {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}}
        result = filter_fields(data, [])
        assert result == data

    def test_filter_fields_state_only(self):
        """Test filter_fields with state field."""
        data = {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}}
        result = filter_fields(data, ["state"])
        assert result == {"entity_id": "light.test", "state": "on"}

    def test_filter_fields_attributes(self):
        """Test filter_fields with attributes field."""
        data = {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}}
        result = filter_fields(data, ["attributes"])
        assert result == {"entity_id": "light.test", "attributes": {"brightness": 255}}

    def test_filter_fields_attr_specific(self):
        """Test filter_fields with specific attribute."""
        data = {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}}
        result = filter_fields(data, ["attr.brightness"])
        assert result == {"entity_id": "light.test", "attributes": {"brightness": 255}}

    def test_filter_fields_multiple_attrs(self):
        """Test filter_fields with multiple attributes."""
        data = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255, "color_temp": 400},
        }
        result = filter_fields(data, ["attr.brightness", "attr.color_temp"])
        assert result == {
            "entity_id": "light.test",
            "attributes": {"brightness": 255, "color_temp": 400},
        }

    def test_filter_fields_context(self):
        """Test filter_fields with context field."""
        data = {
            "entity_id": "light.test",
            "state": "on",
            "context": {"id": "abc123"},
        }
        result = filter_fields(data, ["context"])
        assert result == {"entity_id": "light.test", "context": {"id": "abc123"}}

    def test_filter_fields_timestamp_fields(self):
        """Test filter_fields with timestamp fields."""
        data = {
            "entity_id": "light.test",
            "state": "on",
            "last_updated": "2024-01-01T00:00:00Z",
            "last_changed": "2024-01-01T00:00:00Z",
        }
        result = filter_fields(data, ["last_updated", "last_changed"])
        assert result == {
            "entity_id": "light.test",
            "last_updated": "2024-01-01T00:00:00Z",
            "last_changed": "2024-01-01T00:00:00Z",
        }

    def test_filter_fields_multiple_fields(self):
        """Test filter_fields with multiple field types."""
        data = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255},
            "last_updated": "2024-01-01T00:00:00Z",
        }
        result = filter_fields(data, ["state", "attr.brightness", "last_updated"])
        assert result == {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255},
            "last_updated": "2024-01-01T00:00:00Z",
        }


class TestGetAllEntityStates:
    """Test the get_all_entity_states function."""

    @pytest.mark.asyncio
    async def test_get_all_entity_states_success(self):
        """Test get_all_entity_states with successful response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "light.test1", "state": "on"},
            {"entity_id": "light.test2", "state": "off"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client):
            result = await get_all_entity_states()

            assert isinstance(result, dict)
            assert "light.test1" in result
            assert "light.test2" in result
            assert result["light.test1"]["state"] == "on"
            assert result["light.test2"]["state"] == "off"

    @pytest.mark.asyncio
    async def test_get_all_entity_states_empty(self):
        """Test get_all_entity_states with empty response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client):
            result = await get_all_entity_states()

            assert isinstance(result, dict)
            assert len(result) == 0


class TestGetEntityState:
    """Test the get_entity_state function."""

    @pytest.mark.asyncio
    async def test_get_entity_state_success(self):
        """Test get_entity_state with successful response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255},
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entity_state("light.test")

            assert result["entity_id"] == "light.test"
            assert result["state"] == "on"

    @pytest.mark.asyncio
    async def test_get_entity_state_with_fields(self):
        """Test get_entity_state with field filtering."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255},
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entity_state("light.test", fields=["state", "attr.brightness"])

            assert result["entity_id"] == "light.test"
            assert result["state"] == "on"
            assert result["attributes"]["brightness"] == 255
            assert "last_updated" not in result

    @pytest.mark.asyncio
    async def test_get_entity_state_lean(self):
        """Test get_entity_state with lean mode."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 255, "color_temp": 400},
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entity_state("light.test", lean=True)

            assert result["entity_id"] == "light.test"
            assert result["state"] == "on"
            # Should include domain-specific attributes for light
            assert "attributes" in result


class TestGetEntities:
    """Test the get_entities function."""

    @pytest.mark.asyncio
    async def test_get_entities_success(self):
        """Test get_entities with successful response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "light.test1", "state": "on"},
            {"entity_id": "switch.test2", "state": "off"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities()

            assert isinstance(result, list)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_entities_with_domain_filter(self):
        """Test get_entities with domain filtering."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "light.test1", "state": "on"},
            {"entity_id": "light.test2", "state": "off"},
            {"entity_id": "switch.test3", "state": "off"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities(domain="light")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(entity["entity_id"].startswith("light.") for entity in result)

    @pytest.mark.asyncio
    async def test_get_entities_with_search(self):
        """Test get_entities with search query."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "light.kitchen", "state": "on", "attributes": {"friendly_name": "Kitchen Light"}},
            {"entity_id": "light.bedroom", "state": "off", "attributes": {"friendly_name": "Bedroom Light"}},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities(search_query="kitchen")

            assert isinstance(result, list)
            assert len(result) == 1
            assert "kitchen" in result[0]["entity_id"].lower()

    @pytest.mark.asyncio
    async def test_get_entities_with_limit(self):
        """Test get_entities with limit."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": f"light.test{i}", "state": "on"} for i in range(10)
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities(limit=5)

            assert isinstance(result, list)
            assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_entities_with_fields(self):
        """Test get_entities with field filtering."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "light.test", "state": "on", "attributes": {"brightness": 255}},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities(fields=["state", "attr.brightness"])

            assert isinstance(result, list)
            assert len(result) == 1
            assert "entity_id" in result[0]
            assert "state" in result[0]
            assert "attributes" in result[0]
            assert "last_updated" not in result[0]

    @pytest.mark.asyncio
    async def test_get_entities_lean_mode(self):
        """Test get_entities with lean mode."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"brightness": 255, "color_temp": 400},
            },
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entities(lean=True)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "light.test"
            assert result[0]["state"] == "on"


class TestGetEntityHistory:
    """Test the get_entity_history function."""

    @pytest.mark.asyncio
    async def test_get_entity_history_success(self):
        """Test get_entity_history with successful response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [
                {
                    "entity_id": "light.test",
                    "state": "on",
                    "last_changed": "2024-01-01T00:00:00Z",
                }
            ]
        ]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            result = await get_entity_history("light.test", hours=24)

            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_entity_history_with_params(self):
        """Test get_entity_history constructs correct URL and params."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.entities.get_client", return_value=mock_client), patch(
            "app.core.decorators.HA_TOKEN", "test_token"
        ):
            await get_entity_history("light.test", hours=12)

            call_args = mock_client.get.call_args
            assert "/api/history/period/" in call_args[0][0]
            assert call_args[1]["params"]["filter_entity_id"] == "light.test"
            assert "end_time" in call_args[1]["params"]

