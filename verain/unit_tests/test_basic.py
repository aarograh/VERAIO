"""
Test suite for VERAIn package.

Basic tests to verify package functionality and imports.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_package_imports():
    """Test that main package imports work correctly."""
    try:
        import verain

        assert verain.__version__ == "1.0.0"
        assert verain.__author__ == "Veracity Nuclear"
    except ImportError as e:
        pytest.fail(f"Failed to import verain package: {e}")


def test_core_imports():
    """Test that core modules import correctly."""
    try:
        from verain import DirectoryProcessor # type: ignore
        from verain import ValidationEngine # type: ignore

        assert DirectoryProcessor is not None
        assert ValidationEngine is not None
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


def test_utils_imports():
    """Test that utility modules import correctly."""
    try:
        from verain import InputParser # type: ignore

        assert InputParser is not None
    except ImportError as e:
        pytest.fail(f"Failed to import utils modules: {e}")


def test_validation_engine_basic():
    """Test basic ValidationEngine functionality."""
    from verain import ValidationEngine # type: ignore

    engine = ValidationEngine()

    # Test simple string validation
    errors = engine.validate_parameter(
        "test_param", ["hello", "world"], ["is_string()"]
    )
    assert len(errors) == 0

    # Test integer validation
    errors = engine.validate_parameter("test_param", ["123", "456"], ["is_int()"])
    assert len(errors) == 0

    # Test failed validation
    errors = engine.validate_parameter("test_param", ["abc"], ["is_int()"])
    assert len(errors) > 0


def test_directory_processor_creation():
    """Test DirectoryProcessor creation."""
    from verain import DirectoryProcessor # type: ignore

    # Test with non-existent file (should not raise exception during creation)
    processor = DirectoryProcessor("nonexistent.yml")
    assert processor is not None

    # Test that load_yaml returns False for non-existent file
    passed = False
    try:
        processor.load_yaml()
        passed = False
    # pylint: disable=bare-except
    except FileNotFoundError:
        passed = True
    assert passed


def test_input_parser_creation():
    """Test InputParser creation."""
    from verain import InputParser # type: ignore

    parser = InputParser()
    assert parser is not None
    assert parser.blocks == {}


def test_convenience_functions():
    """Test package convenience functions."""
    try:
        from verain import process_directory # type: ignore
        from verain import validate_input # type: ignore

        assert process_directory is not None
        assert validate_input is not None

        # Test with non-existent file
        passed = False
        try:
            result = process_directory("nonexistent.yml")
            passed = False
        except FileNotFoundError:
            passed = True
        assert passed

        # Test validation with non-existent file
        result = validate_input("nonexistent.yml")
        assert not result

    except ImportError as e:
        pytest.fail(f"Failed to import convenience functions: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
