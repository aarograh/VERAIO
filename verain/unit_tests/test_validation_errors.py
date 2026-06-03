#!/usr/bin/env python3
"""
Extended test script to demonstrate validation integration with errors.
"""

from pathlib import Path
from verain.parser import InputParser

def test_validation_with_errors():
    """Test the validation integration with intentional errors."""

    # Create a test input file with some validation errors
    test_input_content = """
[CASEID]
  title Example Test Case

[CORE]
  n_assembly -1
  height abc

[STATE]
  power -3400.0
  tinlet invalid_temp
"""

    # Write test input file
    test_input_path = Path("test_input_errors.inp")
    with open(test_input_path, 'w') as f:
        f.write(test_input_content)

    # Test with validation
    parser_with_validation = InputParser()
    data = parser_with_validation.parse_file(test_input_path)
    parser_with_validation.validate_input(data)

    # Check for validation errors
    errors = parser_with_validation.get_validation_errors()
    assert len(errors) == 2, f"Expected 2 validation errors, got {errors}"
    assert errors[0] == "Parameter 'height' failed validation: is_float()"
    assert errors[1] == "Parameter 'power' failed validation: is_geq() 0"

    # Cleanup
    test_input_path.unlink()

if __name__ == "__main__":
    test_validation_with_errors()
