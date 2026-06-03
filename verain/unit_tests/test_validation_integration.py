#!/usr/bin/env python3
"""
Test script to demonstrate the validation integration in the InputParser.
"""

from pathlib import Path
from verain.parser import InputParser

def test_validation_integration():
    """Test the validation integration with a sample input."""

    # Create a simple test input file
    test_input_content = """
[CASEID]
  title Example Test Case

[CORE]
  name TestCore
  size 365.76

[STATE]
  power 3400.0
  flow 93.0
"""

    # Write test input file
    test_input_path = Path("test_input.inp")
    with open(test_input_path, 'w') as f:
        f.write(test_input_content)

    print("Testing parser without validation...")
    # Test without validation
    parser_no_validation = InputParser()
    parsed_data = parser_no_validation.parse_file(test_input_path)
    print(f"Parsed {len(parsed_data)} blocks without validation")

    # Test with validation
    parser_with_validation = InputParser()
    parsed_data_validated = parser_with_validation.parse_file(test_input_path)

    print(f"Parsed {len(parsed_data_validated)} blocks with validation")

    # Check for validation errors
    errors = parser_with_validation.get_validation_errors()
    assert len(errors) == 0

    # Test class method with validation
    print("\nTesting class method with validation...")
    parser_with_validation = InputParser()
    parsed_data_2  = parser_with_validation.parse_file(test_input_path)
    parser_with_validation.validate_input(parsed_data_2)
    validation_errors = parser_with_validation.get_validation_errors()
    print(f"Class method found {len(validation_errors)} validation errors")


    # Cleanup
    test_input_path.unlink()
    print("\nTest completed!")

if __name__ == "__main__":
    test_validation_integration()
