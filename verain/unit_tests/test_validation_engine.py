#!/usr/bin/env python3
"""
Unit tests for ValidationEngine class.

This test suite covers the ValidationEngine functionality for
validating input parameters against validation rules.
"""

import pytest
from verain.parser import ValidationEngine


class TestValidationEngine:
    """Unit tests for ValidationEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ValidationEngine()

    def test_string_validation(self):
        """Test string validation."""
        errors = self.engine.validate_parameter(
            "test", ["hello", "world"], ["is_string()"]
        )
        assert len(errors) == 0

    def test_word_validation(self):
        """Test word validation."""
        errors = self.engine.validate_parameter(
            "test", ["hello", "world"], ["is_word()"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter("test", ["hello world"], ["is_word()"])
        assert len(errors) > 0

    def test_int_validation(self):
        """Test integer validation."""
        errors = self.engine.validate_parameter("test", ["123", "456"], ["is_int()"])
        assert len(errors) == 0

        errors = self.engine.validate_parameter("test", ["abc"], ["is_int()"])
        assert len(errors) > 0

    def test_float_validation(self):
        """Test float validation."""
        errors = self.engine.validate_parameter(
            "test", ["123.45", "67.89"], ["is_float()"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter("test", ["abc"], ["is_float()"])
        assert len(errors) > 0

    def test_geq_validation(self):
        """Test greater than or equal validation."""
        errors = self.engine.validate_parameter("test", ["10", "20"], ["is_geq() 5"])
        assert len(errors) == 0

        errors = self.engine.validate_parameter("test", ["1"], ["is_geq() 5"])
        assert len(errors) > 0

    def test_arraysize_validation(self):
        """Test array size validation."""
        errors = self.engine.validate_parameter(
            "test", ["a", "b", "c"], ["arraysize()==3"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter("test", ["a", "b"], ["arraysize()==3"])
        assert len(errors) > 0

    def test_in_dictionary_validation(self):
        """Test in dictionary validation."""
        errors = self.engine.validate_parameter(
            "test", ["red"], ["in_dictionary(red,blue,green)"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter(
            "test", ["yellow"], ["in_dictionary(red,blue,green)"]
        )
        assert len(errors) > 0

    def test_strictly_increasing_validation(self):
        """Test strictly increasing validation."""
        errors = self.engine.validate_parameter(
            "test", ["1", "2", "3"], ["is_strictlyincreasing()"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter(
            "test", ["3", "2", "1"], ["is_strictlyincreasing()"]
        )
        assert len(errors) > 0

    def test_multiple_checks(self):
        """Test multiple validation checks."""
        errors = self.engine.validate_parameter(
            "test", ["10"], ["is_int()", "is_geq() 5"]
        )
        assert len(errors) == 0

        errors = self.engine.validate_parameter(
            "test", ["abc"], ["is_int()", "is_geq() 5"]
        )
        assert len(errors) == 1, f"Expected 1 error, got {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
