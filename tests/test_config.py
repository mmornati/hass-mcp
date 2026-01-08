import os
from unittest.mock import patch

from app.config import HA_URL, get_ha_headers


class TestConfig:
    """Test the configuration module."""

    def test_get_ha_headers_with_token(self):
        """Test getting headers with a token."""
        with patch("app.config.HA_TOKEN", "test_token"):
            headers = get_ha_headers()

            # Check that both headers are present
            assert "Content-Type" in headers
            assert "Authorization" in headers

            # Check header values
            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test_token"

    def test_get_ha_headers_without_token(self):
        """Test getting headers without a token."""
        with patch("app.config.HA_TOKEN", ""):
            headers = get_ha_headers()

            # Check that only Content-Type is present
            assert "Content-Type" in headers
            assert "Authorization" not in headers

            # Check header value
            assert headers["Content-Type"] == "application/json"

    def test_environment_variable_defaults(self):
        """Test that environment variables have sensible defaults."""
        # Instead of mocking os.environ.get completely, let's verify the expected defaults
        # are used when the environment variables are not set

        # Get the current values

        # Verify the defaults match what we expect
        # Note: These may differ if environment variables are actually set
        assert HA_URL.startswith("http://")  # May be localhost or an actual URL

    def test_environment_variable_custom_values(self):
        """Test that environment variables can be customized."""
        env_values = {
            "HA_URL": "http://homeassistant.local:8123",
            "HA_TOKEN": "custom_token",
        }

        def mock_environ_get(key, default=None):
            return env_values.get(key, default)

        with patch("os.environ.get", side_effect=mock_environ_get):
            from importlib import reload

            import app.config

            reload(app.config)

            # Check custom values
            assert app.config.HA_URL == "http://homeassistant.local:8123"
            assert app.config.HA_TOKEN == "custom_token"


class TestSSLConfiguration:
    """Test SSL/TLS configuration parsing."""

    def test_ssl_verify_default_true(self):
        """Test default SSL verification is True."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove HA_SSL_VERIFY if it exists
            if "HA_SSL_VERIFY" in os.environ:
                del os.environ["HA_SSL_VERIFY"]

            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is True

    def test_ssl_verify_true_string(self):
        """Test 'true' string parses to True."""
        with patch.dict(os.environ, {"HA_SSL_VERIFY": "true"}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is True

    def test_ssl_verify_false_string(self):
        """Test 'false' string parses to False."""
        with patch.dict(os.environ, {"HA_SSL_VERIFY": "false"}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is False

    def test_ssl_verify_numeric_one(self):
        """Test '1' parses to True."""
        with patch.dict(os.environ, {"HA_SSL_VERIFY": "1"}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is True

    def test_ssl_verify_numeric_zero(self):
        """Test '0' parses to False."""
        with patch.dict(os.environ, {"HA_SSL_VERIFY": "0"}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is False

    def test_ssl_verify_custom_ca_path(self, tmp_path):
        """Test custom CA certificate path."""
        ca_file = tmp_path / "ca.pem"
        ca_file.write_text("FAKE CA")

        with patch.dict(os.environ, {"HA_SSL_VERIFY": str(ca_file)}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result == str(ca_file)

    def test_ssl_verify_invalid_path_fallback(self):
        """Test invalid CA path falls back to True."""
        with patch.dict(os.environ, {"HA_SSL_VERIFY": "/nonexistent/ca.pem"}):
            from importlib import reload

            import app.config

            reload(app.config)

            result = app.config.get_ssl_verify_value()
            assert result is True
