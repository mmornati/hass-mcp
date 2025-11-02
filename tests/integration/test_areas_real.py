"""Integration tests for areas API against real Home Assistant."""

import pytest

from app.api.areas import get_area_entities, get_area_summary, get_areas


@pytest.mark.integration
class TestAreasAPIIntegration:
    """Test areas API with real Home Assistant instance."""

    @pytest.mark.asyncio
    async def test_get_areas_real(self):
        """Test getting areas from real HA instance using template API."""
        areas = await get_areas()

        assert isinstance(areas, list)
        # Should have at least some areas if HA is properly configured
        # Even minimal HA has some default areas

        # Verify structure
        if areas:
            area = areas[0]
            assert "area_id" in area
            assert "name" in area
            assert "aliases" in area
            assert "picture" in area

    @pytest.mark.asyncio
    async def test_get_area_entities_real(self):
        """Test getting area entities from real HA instance."""
        # First, get an area
        areas = await get_areas()

        if areas:
            area_id = areas[0]["area_id"]
            entities = await get_area_entities(area_id)

            assert isinstance(entities, list)
            # Entities may be empty if area has no entities

    @pytest.mark.asyncio
    async def test_get_area_summary_real(self):
        """Test getting area summary from real HA instance."""
        summary = await get_area_summary()

        assert isinstance(summary, dict)
        assert "total_areas" in summary
        assert "areas" in summary

        # Should have at least 0 areas
        assert isinstance(summary["total_areas"], int)
        assert isinstance(summary["areas"], dict)

        # If there are areas, verify structure
        if summary["total_areas"] > 0:
            first_area_id = list(summary["areas"].keys())[0]
            first_area = summary["areas"][first_area_id]

            assert "name" in first_area
            assert "entity_count" in first_area
            assert "domain_counts" in first_area

    @pytest.mark.asyncio
    async def test_create_area_real(self):
        """Test that create area returns error (not supported via REST)."""
        from app.api.areas import create_area

        result = await create_area("Test Area")

        assert isinstance(result, dict)
        assert "error" in result
        assert "not supported" in result["error"].lower() or "REST API" in result["error"]

    @pytest.mark.asyncio
    async def test_update_area_real(self):
        """Test that update area returns error (not supported via REST)."""
        from app.api.areas import update_area

        # Get a real area ID first
        areas = await get_areas()
        if not areas:
            pytest.skip("No areas available to test update")

        area_id = areas[0]["area_id"]
        result = await update_area(area_id, name="New Name")

        assert isinstance(result, dict)
        assert "error" in result
        assert "not supported" in result["error"].lower() or "REST API" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_area_real(self):
        """Test that delete area returns error (not supported via REST)."""
        from app.api.areas import delete_area

        # Get a real area ID first
        areas = await get_areas()
        if not areas:
            pytest.skip("No areas available to test delete")

        area_id = areas[0]["area_id"]
        result = await delete_area(area_id)

        assert isinstance(result, dict)
        assert "error" in result
        assert "not supported" in result["error"].lower() or "REST API" in result["error"]
