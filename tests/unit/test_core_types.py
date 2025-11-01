"""Unit tests for app.core.types module."""

from app.core.types import (
    DEFAULT_LEAN_FIELDS,
    DEFAULT_STANDARD_FIELDS,
    DOMAIN_IMPORTANT_ATTRIBUTES,
    F,
    T,
)


class TestCoreTypes:
    """Test the core types module."""

    def test_type_variables_exist(self):
        """Test that type variables T and F are defined."""
        # Type variables should be TypeVar instances
        assert T is not None
        assert F is not None

    def test_default_lean_fields(self):
        """Test DEFAULT_LEAN_FIELDS contains expected fields."""
        assert isinstance(DEFAULT_LEAN_FIELDS, list)
        assert "entity_id" in DEFAULT_LEAN_FIELDS
        assert "state" in DEFAULT_LEAN_FIELDS
        assert "attr.friendly_name" in DEFAULT_LEAN_FIELDS

    def test_default_standard_fields(self):
        """Test DEFAULT_STANDARD_FIELDS contains expected fields."""
        assert isinstance(DEFAULT_STANDARD_FIELDS, list)
        assert "entity_id" in DEFAULT_STANDARD_FIELDS
        assert "state" in DEFAULT_STANDARD_FIELDS
        assert "attributes" in DEFAULT_STANDARD_FIELDS
        assert "last_updated" in DEFAULT_STANDARD_FIELDS

    def test_domain_important_attributes_structure(self):
        """Test DOMAIN_IMPORTANT_ATTRIBUTES structure."""
        assert isinstance(DOMAIN_IMPORTANT_ATTRIBUTES, dict)

        # Check some expected domains exist
        assert "light" in DOMAIN_IMPORTANT_ATTRIBUTES
        assert "sensor" in DOMAIN_IMPORTANT_ATTRIBUTES
        assert "climate" in DOMAIN_IMPORTANT_ATTRIBUTES

        # Check values are lists
        assert isinstance(DOMAIN_IMPORTANT_ATTRIBUTES["light"], list)
        assert isinstance(DOMAIN_IMPORTANT_ATTRIBUTES["sensor"], list)

    def test_domain_important_attributes_content(self):
        """Test DOMAIN_IMPORTANT_ATTRIBUTES contains expected attributes."""
        # Check light domain
        assert "brightness" in DOMAIN_IMPORTANT_ATTRIBUTES["light"]
        assert "color_temp" in DOMAIN_IMPORTANT_ATTRIBUTES["light"]

        # Check sensor domain
        assert "device_class" in DOMAIN_IMPORTANT_ATTRIBUTES["sensor"]
        assert "unit_of_measurement" in DOMAIN_IMPORTANT_ATTRIBUTES["sensor"]

        # Check climate domain
        assert "hvac_mode" in DOMAIN_IMPORTANT_ATTRIBUTES["climate"]
        assert "temperature" in DOMAIN_IMPORTANT_ATTRIBUTES["climate"]
