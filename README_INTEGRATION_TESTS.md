# Integration Testing with Real Home Assistant

This document describes how to set up and run integration tests against a real Home Assistant instance.

## Overview

Integration tests validate that the hass-mcp server correctly communicates with a real Home Assistant API. Unlike unit tests that use mocks, these tests verify actual API behavior against your live Home Assistant instance.

## Quick Start

### Using Your Existing Home Assistant Instance (Recommended)

The easiest way to run integration tests is to use your existing Home Assistant instance:

```bash
# Set environment variables
export HA_URL="http://localhost:8123"  # Or your HA IP/hostname
export HA_TOKEN="your_long_lived_token"

# Run tests
uv run pytest tests/integration/ -v

# Or with markers
uv run pytest tests/integration/ -m integration -v
```

### Using Docker Compose (For Development)

For testing with a controlled environment:

```bash
# Start Home Assistant test instance
docker-compose -f docker-compose.test.yml up -d

# Wait for HA to be ready (can take 2-3 minutes)
# Check status with:
docker-compose -f docker-compose.test.yml logs -f --tail=50

# IMPORTANT: Docker HA requires manual setup for now
# Due to Home Assistant's onboarding process, you need to:
# 1. Visit http://localhost:18123 in a browser
# 2. Complete the initial setup wizard
# 3. Generate a long-lived access token from:
#    Profile → Long-lived access tokens → Create Token
# 4. Export the token:
export HA_URL="http://localhost:18123"
export HA_TOKEN="your_generated_token"

# Run integration tests
uv run pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

**Note**: The `SKIP_ONBOARDING=1` environment variable only skips the UI wizard but still requires initial authentication setup. For fully automated CI testing, consider using a pre-provisioned token or HA snapshots.

## Test Structure

Integration tests are located in `tests/integration/` and are marked with `@pytest.mark.integration`:

- `test_areas_real.py` - Tests areas API against real HA
- More integration test files can be added for other APIs

## Running Tests

### All Integration Tests

```bash
uv run pytest tests/integration/ -v
```

### Specific Test Files

```bash
# Test areas API
uv run pytest tests/integration/test_areas_real.py -v

# Run only a specific test
uv run pytest tests/integration/test_areas_real.py::TestAreasAPIIntegration::test_get_areas_real -v
```

### With Coverage

```bash
uv run pytest tests/integration/ --cov=app --cov-report=html
```

## Test Markers

Integration tests use the `integration` marker:

```python
@pytest.mark.integration
class TestAreasAPIIntegration:
    """Test areas API with real Home Assistant instance."""

    @pytest.mark.asyncio
    async def test_get_areas_real(self):
        """Test getting areas from real HA instance."""
        areas = await get_areas()
        assert isinstance(areas, list)
```

## Configuration

Integration tests are configured in `tests/integration/conftest.py`:

- Skips tests if HA is not available
- Uses real environment variables (not mocks)
- Provides fixtures for HA client setup

## Best Practices

1. **Don't modify HA state**: Tests should be read-only or cleanup after themselves
2. **Handle missing HA gracefully**: Tests skip if HA is not available
3. **Use real data**: Tests should handle whatever data exists in your HA instance
4. **Test both success and error paths**: Verify error handling works correctly
5. **Mark as integration**: Always use `@pytest.mark.integration`

## Example Test

```python
@pytest.mark.integration
class TestAreasAPIIntegration:
    """Test areas API with real Home Assistant instance."""

    @pytest.fixture(autouse=True, scope="class")
    def check_ha_available(self):
        """Check if HA is available before running tests."""
        ha_url = os.environ.get("HA_URL")
        ha_token = os.environ.get("HA_TOKEN")

        if not ha_url or not ha_token:
            pytest.skip("HA_URL and HA_TOKEN must be set for integration tests")

    @pytest.mark.asyncio
    async def test_get_areas_real(self):
        """Test getting areas from real HA instance."""
        areas = await get_areas()

        assert isinstance(areas, list)
        if areas:
            assert "area_id" in areas[0]
            assert "name" in areas[0]
```

## Continuous Integration

Integration tests are run optionally in CI:

```yaml
# In .github/workflows/test-integration.yml
# Integration tests run when requested but don't block PRs
```

Set up your CI environment variables:
- `HA_URL`: Your Home Assistant URL
- `HA_TOKEN`: Long-lived access token

## Troubleshooting

### Tests Skip with "Home Assistant not available"

Set the `HA_URL` and `HA_TOKEN` environment variables:

```bash
export HA_URL="http://your-ha-ip:8123"
export HA_TOKEN="your_token_here"
```

### Connection Refused

Check that Home Assistant is running and accessible:

```bash
curl http://your-ha-ip:8123/api/
```

### Authentication Failures

Generate a new long-lived access token in Home Assistant:
1. Go to Profile → Long-lived access tokens
2. Create a new token
3. Use it in `HA_TOKEN` environment variable

### Tests Interfere with Each Other

Ensure tests are independent and don't modify persistent state:
- Use read-only operations where possible
- Clean up any created resources
- Use unique names for test data

## See Also

- `tests/integration/`: Integration test files
- `tests/integration/conftest.py`: Integration test configuration
- `docker-compose.test.yml`: Docker setup for testing
- `README.md`: General project documentation
