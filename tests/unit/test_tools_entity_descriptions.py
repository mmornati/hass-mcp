"""Unit tests for app.tools.entity_descriptions module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.entity_descriptions import (
    generate_entity_description_tool,
    generate_entity_descriptions_batch_tool,
)


class TestGenerateEntityDescriptionTool:
    """Test the generate_entity_description_tool function."""

    @pytest.fixture
    def mock_get_entity_state(self):
        """Create a mock get_entity_state function."""
        return AsyncMock(
            return_value={
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {
                    "friendly_name": "Living Room Light",
                    "area_id": "living_room",
                },
            }
        )

    @pytest.fixture
    def mock_generate_entity_description_enhanced(self):
        """Create a mock generate_entity_description_enhanced function."""
        return AsyncMock(
            return_value="Living Room Light - light entity in the Living Room area. Supports brightness control. Currently on. Part of the Philips Hue Bridge system."
        )

    @pytest.mark.asyncio
    async def test_generate_description_success(
        self, mock_get_entity_state, mock_generate_entity_description_enhanced
    ):
        """Test successful description generation."""
        with (
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_enhanced",
                mock_generate_entity_description_enhanced,
            ),
        ):
            result = await generate_entity_description_tool("light.living_room")

            assert result["entity_id"] == "light.living_room"
            assert "description" in result
            assert result["description"] is not None
            assert result["template_used"] is True
            assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_generate_description_empty_entity_id(
        self, mock_get_entity_state, mock_generate_entity_description_enhanced
    ):
        """Test description generation with empty entity_id."""
        with (
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_enhanced",
                mock_generate_entity_description_enhanced,
            ),
        ):
            result = await generate_entity_description_tool("")

            assert "error" in result
            assert result["description"] is None

    @pytest.mark.asyncio
    async def test_generate_description_entity_not_found(
        self, mock_generate_entity_description_enhanced
    ):
        """Test description generation when entity not found."""
        mock_get_entity_state = AsyncMock(
            return_value={"error": "Entity not found: light.living_room"}
        )

        with (
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_enhanced",
                mock_generate_entity_description_enhanced,
            ),
        ):
            result = await generate_entity_description_tool("light.living_room")

            assert "error" in result
            assert result["description"] is None

    @pytest.mark.asyncio
    async def test_generate_description_without_template(
        self, mock_get_entity_state, mock_generate_entity_description_enhanced
    ):
        """Test description generation without template."""
        with (
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_enhanced",
                mock_generate_entity_description_enhanced,
            ),
        ):
            result = await generate_entity_description_tool("light.living_room", use_template=False)

            assert result["template_used"] is False

    @pytest.mark.asyncio
    async def test_generate_description_error(
        self, mock_get_entity_state, mock_generate_entity_description_enhanced
    ):
        """Test description generation with error."""
        mock_generate_entity_description_enhanced.side_effect = Exception("Generation failed")

        with (
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_enhanced",
                mock_generate_entity_description_enhanced,
            ),
        ):
            result = await generate_entity_description_tool("light.living_room")

            assert "error" in result
            assert result["description"] is None


class TestGenerateEntityDescriptionsBatchTool:
    """Test the generate_entity_descriptions_batch_tool function."""

    @pytest.fixture
    def mock_get_entities(self):
        """Create a mock get_entities function."""
        return AsyncMock(
            return_value=[
                {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "attributes": {"friendly_name": "Living Room Light"},
                },
                {
                    "entity_id": "sensor.temperature",
                    "state": "22.5",
                    "attributes": {"friendly_name": "Temperature Sensor"},
                },
            ]
        )

    @pytest.fixture
    def mock_get_entity_state(self):
        """Create a mock get_entity_state function."""
        return AsyncMock(
            return_value={
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            }
        )

    @pytest.fixture
    def mock_generate_entity_description_batch(self):
        """Create a mock generate_entity_description_batch function."""
        return AsyncMock(
            return_value={
                "light.living_room": "Living Room Light - light entity...",
                "sensor.temperature": "Temperature Sensor - sensor entity...",
            }
        )

    @pytest.mark.asyncio
    async def test_generate_descriptions_batch_success(
        self,
        mock_get_entities,
        mock_get_entity_state,
        mock_generate_entity_description_batch,
    ):
        """Test successful batch description generation."""
        with (
            patch("app.api.entities.get_entities", mock_get_entities),
            patch("app.tools.entity_descriptions.get_entity_state", mock_get_entity_state),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_batch",
                mock_generate_entity_description_batch,
            ),
        ):
            result = await generate_entity_descriptions_batch_tool(
                entity_ids=["light.living_room", "sensor.temperature"]
            )

            assert result["total"] == 2
            assert result["succeeded"] == 2
            assert result["failed"] == 0
            assert "descriptions" in result
            assert len(result["descriptions"]) == 2

    @pytest.mark.asyncio
    async def test_generate_descriptions_batch_all_entities(
        self, mock_get_entities, mock_generate_entity_description_batch
    ):
        """Test batch description generation for all entities."""
        with (
            patch("app.api.entities.get_entities", mock_get_entities),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_batch",
                mock_generate_entity_description_batch,
            ),
        ):
            result = await generate_entity_descriptions_batch_tool(entity_ids=None)

            assert result["total"] == 2
            assert result["succeeded"] == 2
            assert "descriptions" in result

    @pytest.mark.asyncio
    async def test_generate_descriptions_batch_error(
        self, mock_get_entities, mock_generate_entity_description_batch
    ):
        """Test batch description generation with error."""
        mock_generate_entity_description_batch.side_effect = Exception("Batch generation failed")

        with (
            patch("app.api.entities.get_entities", mock_get_entities),
            patch(
                "app.tools.entity_descriptions.generate_entity_description_batch",
                mock_generate_entity_description_batch,
            ),
        ):
            result = await generate_entity_descriptions_batch_tool(entity_ids=None)

            assert "error" in result
            assert result["total"] == 0
            assert result["succeeded"] == 0
