#!/usr/bin/env python3
"""
Integration test to validate all test/*.inp files can be processed correctly.

This test ensures that all VERAIn test files can be parsed without validation errors,
as required by the issue specification that all files in verain/test/*.inp are known
to be correct and should process without validation errors.
"""

import pytest
import glob
from verain.parser import InputParser


class TestIntegrationValidation:
    """Integration tests for VERAIn file processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = InputParser()
        self.test_files = glob.glob("regression_tests/*.inp")
        self.test_files.sort()  # Consistent ordering

    def test_validation_error_summary(self):
        """Test validation errors across all files and provide summary."""

        for file_path in self.test_files:
            print(f"Testing file: {file_path}")
            data = self.parser.parse_file(file_path)
            self.parser.validate_input(data)
            errors = self.parser.get_validation_errors()
            assert len(errors) == 0, f"Validation errors found in {file_path}: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
