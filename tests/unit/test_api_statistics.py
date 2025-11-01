"""Unit tests for app.api.statistics module."""

from unittest.mock import patch

import pytest

from app.api.statistics import (
    analyze_usage_patterns,
    get_domain_statistics,
    get_entity_statistics,
)


class TestGetEntityStatistics:
    """Test the get_entity_statistics function."""

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
    async def test_get_entity_statistics_success(self):
        """Test successful retrieval of entity statistics."""
        # Mock history data - history API returns list of lists
        mock_history = [
            [
                {"state": "20.5", "last_changed": "2025-01-01T10:00:00Z"},
                {"state": "21.0", "last_changed": "2025-01-01T11:00:00Z"},
                {"state": "21.5", "last_changed": "2025-01-01T12:00:00Z"},
            ]
        ]

        with patch("app.api.statistics.get_entity_history", return_value=mock_history):
            result = await get_entity_statistics("sensor.temperature", period_days=7)

            assert isinstance(result, dict)
            assert result["entity_id"] == "sensor.temperature"
            assert result["period_days"] == 7
            assert "statistics" in result
            assert "min" in result["statistics"]
            assert "max" in result["statistics"]
            assert "mean" in result["statistics"]
            assert "median" in result["statistics"]
            assert result["statistics"]["min"] == 20.5
            assert result["statistics"]["max"] == 21.5
            assert result["statistics"]["mean"] == 21.0
            assert result["data_points"] == 3

    @pytest.mark.asyncio
    async def test_get_entity_statistics_no_data(self):
        """Test statistics retrieval with no data."""
        mock_history = []

        with patch("app.api.statistics.get_entity_history", return_value=mock_history):
            result = await get_entity_statistics("sensor.temperature", period_days=7)

            assert isinstance(result, dict)
            assert result["entity_id"] == "sensor.temperature"
            assert "note" in result
            assert result["statistics"] == {}

    @pytest.mark.asyncio
    async def test_get_entity_statistics_non_numeric(self):
        """Test statistics retrieval with non-numeric entity."""
        mock_history = [
            [
                {"state": "on", "last_changed": "2025-01-01T10:00:00Z"},
                {"state": "off", "last_changed": "2025-01-01T11:00:00Z"},
            ]
        ]

        with patch("app.api.statistics.get_entity_history", return_value=mock_history):
            result = await get_entity_statistics("light.living_room", period_days=7)

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert "note" in result
            assert "Entity state is not numeric" in result["note"]
            assert result["statistics"] == {}

    @pytest.mark.asyncio
    async def test_get_entity_statistics_history_error(self):
        """Test statistics retrieval when history API returns error."""
        mock_error = {"error": "Entity not found"}

        with patch("app.api.statistics.get_entity_history", return_value=mock_error):
            result = await get_entity_statistics("sensor.temperature", period_days=7)

            assert isinstance(result, dict)
            assert result["entity_id"] == "sensor.temperature"
            assert "error" in result
            assert result["error"] == "Entity not found"
            assert result["statistics"] == {}

    @pytest.mark.asyncio
    async def test_get_entity_statistics_median_calculation(self):
        """Test median calculation with even and odd number of values."""
        # Test with odd number of values
        mock_history_odd = [[{"state": str(i)} for i in range(5)]]  # [0, 1, 2, 3, 4]

        with patch("app.api.statistics.get_entity_history", return_value=mock_history_odd):
            result = await get_entity_statistics("sensor.temperature", period_days=7)

            assert result["statistics"]["median"] == 2.0

        # Test with even number of values
        mock_history_even = [[{"state": str(i)} for i in range(4)]]  # [0, 1, 2, 3]

        with patch("app.api.statistics.get_entity_history", return_value=mock_history_even):
            result = await get_entity_statistics("sensor.temperature", period_days=7)

            assert result["statistics"]["median"] == 1.5  # (1 + 2) / 2


class TestGetDomainStatistics:
    """Test the get_domain_statistics function."""

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
    async def test_get_domain_statistics_success(self):
        """Test successful retrieval of domain statistics."""
        mock_entities = [
            {"entity_id": "sensor.temperature"},
            {"entity_id": "sensor.humidity"},
        ]

        mock_entity_stats = {
            "entity_id": "sensor.temperature",
            "period_days": 7,
            "statistics": {"min": 20.0, "max": 25.0, "mean": 22.5, "median": 22.5},
        }

        with (
            patch("app.api.statistics.get_entities", return_value=mock_entities),
            patch("app.api.statistics.get_entity_statistics", return_value=mock_entity_stats),
        ):
            result = await get_domain_statistics("sensor", period_days=7)

            assert isinstance(result, dict)
            assert result["domain"] == "sensor"
            assert result["period_days"] == 7
            assert result["total_entities"] == 2
            assert "entity_statistics" in result
            assert len(result["entity_statistics"]) == 2

    @pytest.mark.asyncio
    async def test_get_domain_statistics_no_numeric_entities(self):
        """Test domain statistics with entities that have no numeric statistics."""
        mock_entities = [
            {"entity_id": "sensor.temperature"},
        ]

        mock_entity_stats = {
            "entity_id": "sensor.temperature",
            "period_days": 7,
            "note": "Entity state is not numeric",
            "statistics": {},
        }

        with (
            patch("app.api.statistics.get_entities", return_value=mock_entities),
            patch("app.api.statistics.get_entity_statistics", return_value=mock_entity_stats),
        ):
            result = await get_domain_statistics("sensor", period_days=7)

            assert isinstance(result, dict)
            assert result["entity_statistics"] == {}

    @pytest.mark.asyncio
    async def test_get_domain_statistics_entities_error(self):
        """Test domain statistics when entities API returns error."""
        mock_error = {"error": "Domain not found"}

        with patch("app.api.statistics.get_entities", return_value=mock_error):
            result = await get_domain_statistics("sensor", period_days=7)

            assert isinstance(result, dict)
            assert result["domain"] == "sensor"
            assert "error" in result
            assert result["error"] == "Domain not found"
            assert result["total_entities"] == 0

    @pytest.mark.asyncio
    async def test_get_domain_statistics_limit_to_10(self):
        """Test that domain statistics limits to first 10 entities."""
        mock_entities = [{"entity_id": f"sensor.entity_{i}"} for i in range(15)]

        mock_entity_stats = {
            "entity_id": "sensor.temperature",
            "period_days": 7,
            "statistics": {"min": 20.0, "max": 25.0, "mean": 22.5, "median": 22.5},
        }

        with (
            patch("app.api.statistics.get_entities", return_value=mock_entities),
            patch("app.api.statistics.get_entity_statistics", return_value=mock_entity_stats),
        ):
            result = await get_domain_statistics("sensor", period_days=7)

            # Should only call get_entity_statistics 10 times (for first 10 entities)
            assert len(result["entity_statistics"]) <= 10


class TestAnalyzeUsagePatterns:
    """Test the analyze_usage_patterns function."""

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
    async def test_analyze_usage_patterns_success(self):
        """Test successful usage pattern analysis."""

        mock_logbook = [
            {"when": "2025-01-15T18:00:00Z", "entity_id": "light.living_room"},
            {"when": "2025-01-15T18:30:00Z", "entity_id": "light.living_room"},
            {"when": "2025-01-16T19:00:00Z", "entity_id": "light.living_room"},
            {"when": "2025-01-17T18:00:00Z", "entity_id": "light.living_room"},
        ]

        with patch("app.api.statistics.get_entity_logbook", return_value=mock_logbook):
            result = await analyze_usage_patterns("light.living_room", days=30)

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert result["period_days"] == 30
            assert result["total_events"] == 4
            assert "hourly_distribution" in result
            assert "daily_distribution" in result
            assert "peak_hour" in result
            assert "peak_day" in result
            # Should have hour 18 and 19 in hourly_distribution
            assert 18 in result["hourly_distribution"]
            assert 19 in result["hourly_distribution"]
            # Peak hour should be 18 (3 events)
            assert result["peak_hour"] == 18

    @pytest.mark.asyncio
    async def test_analyze_usage_patterns_no_events(self):
        """Test usage pattern analysis with no events."""
        mock_logbook = []

        with patch("app.api.statistics.get_entity_logbook", return_value=mock_logbook):
            result = await analyze_usage_patterns("light.living_room", days=30)

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert result["total_events"] == 0
            assert result["hourly_distribution"] == {}
            assert result["daily_distribution"] == {}
            assert result["peak_hour"] is None
            assert result["peak_day"] is None

    @pytest.mark.asyncio
    async def test_analyze_usage_patterns_logbook_error(self):
        """Test usage pattern analysis when logbook API returns error."""
        mock_error = [{"error": "Entity not found"}]

        with patch("app.api.statistics.get_entity_logbook", return_value=mock_error):
            result = await analyze_usage_patterns("light.living_room", days=30)

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert "error" in result
            assert result["error"] == "Entity not found"
            assert result["total_events"] == 0

    @pytest.mark.asyncio
    async def test_analyze_usage_patterns_invalid_timestamp(self):
        """Test usage pattern analysis with invalid timestamp format."""
        mock_logbook = [
            {"when": "invalid-timestamp", "entity_id": "light.living_room"},
            {"when": "2025-01-15T18:00:00Z", "entity_id": "light.living_room"},
        ]

        with patch("app.api.statistics.get_entity_logbook", return_value=mock_logbook):
            result = await analyze_usage_patterns("light.living_room", days=30)

            # Should skip invalid timestamps but process valid ones
            assert isinstance(result, dict)
            assert result["total_events"] == 2  # Both entries in logbook
            # Should have hour 18 in hourly_distribution from valid entry
            assert 18 in result["hourly_distribution"]

    @pytest.mark.asyncio
    async def test_analyze_usage_patterns_daily_distribution(self):
        """Test that daily distribution is calculated correctly."""
        # Create logbook entries for different days of week
        mock_logbook = [
            {"when": "2025-01-13T10:00:00Z", "entity_id": "light.living_room"},  # Monday
            {"when": "2025-01-14T10:00:00Z", "entity_id": "light.living_room"},  # Tuesday
            {"when": "2025-01-15T10:00:00Z", "entity_id": "light.living_room"},  # Wednesday
            {"when": "2025-01-13T11:00:00Z", "entity_id": "light.living_room"},  # Monday
        ]

        with patch("app.api.statistics.get_entity_logbook", return_value=mock_logbook):
            result = await analyze_usage_patterns("light.living_room", days=30)

            assert isinstance(result, dict)
            assert "daily_distribution" in result
            # Monday should have 2 events
            assert result["daily_distribution"]["Monday"] == 2
            # Tuesday should have 1 event
            assert result["daily_distribution"]["Tuesday"] == 1
            # Peak day should be Monday
            assert result["peak_day"] == "Monday"
