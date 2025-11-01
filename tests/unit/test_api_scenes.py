"""Unit tests for app.api.scenes module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.scenes import (
    activate_scene,
    create_scene,
    get_scene_config,
    get_scenes,
    reload_scenes,
)


class TestGetScenes:
    """Test the get_scenes function."""

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
    async def test_get_scenes_success(self):
        """Test successful retrieval of all scenes."""
        mock_scene_entities = [
            {
                "entity_id": "scene.living_room_dim",
                "state": "scening",
                "attributes": {
                    "friendly_name": "Living Room Dim",
                    "entity_id": ["light.living_room", "light.kitchen"],
                    "snapshot": [{"light.living_room": {"state": "on", "brightness": 128}}],
                },
            },
            {
                "entity_id": "scene.kitchen_bright",
                "state": "scening",
                "attributes": {"friendly_name": "Kitchen Bright"},
            },
        ]

        with patch("app.api.scenes.get_entities", return_value=mock_scene_entities):
            result = await get_scenes()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "scene.living_room_dim"
            assert result[0]["friendly_name"] == "Living Room Dim"
            assert result[0]["entity_id_list"] == ["light.living_room", "light.kitchen"]
            assert result[1]["entity_id"] == "scene.kitchen_bright"

    @pytest.mark.asyncio
    async def test_get_scenes_empty(self):
        """Test retrieval when no scenes are found."""
        with patch("app.api.scenes.get_entities", return_value=[]):
            scenes = await get_scenes()
            assert scenes == []

    @pytest.mark.asyncio
    async def test_get_scenes_api_error(self):
        """Test handling of API errors from get_entities."""
        error_response = {"error": "API connection failed"}
        with patch("app.api.scenes.get_entities", return_value=error_response):
            result = await get_scenes()
            # Should return list with error dict for consistency
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestGetSceneConfig:
    """Test the get_scene_config function."""

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
    async def test_get_scene_config_success_with_prefix(self):
        """Test successful retrieval of scene configuration with 'scene.' prefix."""
        scene_id = "scene.living_room_dim"
        mock_entity = {
            "entity_id": "scene.living_room_dim",
            "state": "scening",
            "attributes": {
                "friendly_name": "Living Room Dim",
                "entity_id": ["light.living_room", "light.kitchen"],
                "snapshot": [{"light.living_room": {"state": "on", "brightness": 128}}],
            },
        }

        with patch("app.api.scenes.get_entity_state", return_value=mock_entity):
            result = await get_scene_config(scene_id)

            assert isinstance(result, dict)
            assert result["entity_id"] == "scene.living_room_dim"
            assert result["friendly_name"] == "Living Room Dim"
            assert result["entity_id_list"] == ["light.living_room", "light.kitchen"]
            assert "snapshot" in result

    @pytest.mark.asyncio
    async def test_get_scene_config_success_without_prefix(self):
        """Test successful retrieval of scene configuration without 'scene.' prefix."""
        scene_id = "living_room_dim"
        mock_entity = {
            "entity_id": "scene.living_room_dim",
            "state": "scening",
            "attributes": {
                "friendly_name": "Living Room Dim",
                "entity_id": ["light.living_room"],
            },
        }

        with patch("app.api.scenes.get_entity_state", return_value=mock_entity):
            result = await get_scene_config(scene_id)

            assert isinstance(result, dict)
            assert result["entity_id"] == "scene.living_room_dim"
            # Should have called with scene. prefix
            # The function should add the prefix automatically

    @pytest.mark.asyncio
    async def test_get_scene_config_error(self):
        """Test handling of error when getting entity state."""
        scene_id = "nonexistent"
        error_response = {"error": "Entity not found"}

        with patch("app.api.scenes.get_entity_state", return_value=error_response):
            result = await get_scene_config(scene_id)

            assert isinstance(result, dict)
            assert "error" in result


class TestCreateScene:
    """Test the create_scene function."""

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
    async def test_create_scene_success(self):
        """Test successful scene creation."""
        name = "Living Room Dim"
        entity_ids = ["light.living_room", "light.kitchen"]
        mock_response = {
            "entity_id": "scene.living_room_dim",
            "name": "Living Room Dim",
        }
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = mock_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await create_scene(name, entity_ids)

            assert isinstance(result, dict)
            assert result["entity_id"] == "scene.living_room_dim"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/scene/create"
            assert call_args[1]["json"]["name"] == name
            assert call_args[1]["json"]["entities"] == entity_ids

    @pytest.mark.asyncio
    async def test_create_scene_with_states(self):
        """Test scene creation with specific states."""
        name = "Living Room Dim"
        entity_ids = ["light.living_room", "light.kitchen"]
        states = {"light.living_room": {"state": "on", "brightness": 128}}
        mock_response = {"entity_id": "scene.living_room_dim", "name": "Living Room Dim"}
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = mock_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await create_scene(name, entity_ids, states)

            assert isinstance(result, dict)
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["states"] == states

    @pytest.mark.asyncio
    async def test_create_scene_api_unavailable(self):
        """Test scene creation when API is unavailable."""
        name = "Living Room Dim"
        entity_ids = ["light.living_room"]
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 404
        mock_post_response.json.return_value = {"error": "Service not found"}
        mock_post_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=httpx.Request("POST", "url"), response=mock_post_response
        )
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await create_scene(name, entity_ids)

            assert isinstance(result, dict)
            assert "error" in result
            assert "Scene creation via API is not available" in result["error"]
            assert "example_config" in result


class TestActivateScene:
    """Test the activate_scene function."""

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
    async def test_activate_scene_success_with_prefix(self):
        """Test successful scene activation with 'scene.' prefix."""
        scene_id = "scene.living_room_dim"
        mock_response = []
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = mock_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await activate_scene(scene_id)

            assert isinstance(result, list)
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/scene/turn_on"
            assert call_args[1]["json"]["entity_id"] == "scene.living_room_dim"

    @pytest.mark.asyncio
    async def test_activate_scene_success_without_prefix(self):
        """Test successful scene activation without 'scene.' prefix."""
        scene_id = "living_room_dim"
        mock_response = []
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = mock_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await activate_scene(scene_id)

            assert isinstance(result, list)
            call_args = mock_client.post.call_args
            # Should add scene. prefix automatically
            assert call_args[1]["json"]["entity_id"] == "scene.living_room_dim"

    @pytest.mark.asyncio
    async def test_activate_scene_http_error(self):
        """Test handling of HTTP error."""
        scene_id = "nonexistent"
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 404
        mock_post_response.json.return_value = {"error": "Scene not found"}
        mock_post_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=httpx.Request("POST", "url"), response=mock_post_response
        )
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await activate_scene(scene_id)

            assert isinstance(result, dict)
            assert "error" in result


class TestReloadScenes:
    """Test the reload_scenes function."""

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
    async def test_reload_scenes_success(self):
        """Test successful reloading of scenes."""
        mock_response = []
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = mock_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await reload_scenes()

            assert isinstance(result, list)
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/scene/reload"
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_reload_scenes_api_error(self):
        """Test handling of API errors during reload."""
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 500
        mock_post_response.json.return_value = {"error": "Server error"}
        mock_post_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("POST", "url"),
            response=mock_post_response,
        )
        mock_client.post = AsyncMock(return_value=mock_post_response)

        with patch("app.api.scenes.get_client", return_value=mock_client):
            result = await reload_scenes()

            assert isinstance(result, dict)
            assert "error" in result
            assert "HTTP error: 500" in result["error"]
