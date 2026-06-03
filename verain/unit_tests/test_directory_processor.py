#!/usr/bin/env python3
"""
Unit tests for DirectoryProcessor class.

This test suite covers the DirectoryProcessor functionality for
processing hierarchical YAML input specifications.
"""

import pytest
import tempfile
from pathlib import Path
from verain.templates import DirectoryProcessor


class TestDirectoryProcessor:
    """Unit tests for DirectoryProcessor class."""

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file."""
        processor = DirectoryProcessor("nonexistent.yml")
        assert processor.yaml_file_path == Path("nonexistent.yml")
        assert processor.raw_data is None
        assert processor.processed_data == {}

    def test_load_nonexistent_yaml(self):
        """Test loading non-existent YAML file."""
        processor = DirectoryProcessor("nonexistent.yml")
        try:
            processor.load_yaml()
            result = False
        # pylint: disable=bare-except
        except:
            result = True
        assert result

    def test_load_valid_yaml(self):
        """Test loading valid YAML content."""
        yaml_content = """
_DATATYPES:
  _dtstring: &dtstring
    _parse: 'scalar'
    _type: 'string'

TESTBLOCK:
  test_param:
    <<: *dtstring
    _check:
      - is_string()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            processor.load_yaml()
            assert processor.raw_data is not None

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML content."""
        yaml_content = """
invalid: yaml: content: [
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            try:
              processor.load_yaml()
              passed = False
            except:
              passed = True
            assert passed

    def test_extract_datatypes(self):
        """Test extracting datatypes from YAML."""
        yaml_content = """
_DATATYPES:
  _dtstring: &dtstring
    _parse: 'scalar'
    _type: 'string'
  _dtint: &dtint
    _parse: 'scalar'
    _type: 'int'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            processor.load_yaml()
            datatypes = processor.extract_datatypes()

            assert "dtstring" in datatypes
            assert "dtint" in datatypes
            assert datatypes["dtstring"]["parse"] == "scalar"

    def test_process_all_blocks(self):
        """Test processing all blocks from YAML."""
        yaml_content = """
_DATATYPES:
  _dtstring: &dtstring
    _parse: 'scalar'
    _type: 'string'

TESTBLOCK:
  test_param:
    <<: *dtstring
    _check:
      - is_string()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            processor.load_yaml()
            result = processor.process_all_blocks()

            assert "input_blocks" in result
            assert "TESTBLOCK" in result["input_blocks"]
            assert "test_param" in result["input_blocks"]["TESTBLOCK"]

    def test_keys(self):
        """Test getting block names."""
        yaml_content = """
BLOCK1:
  param1:
    _parse: 'scalar'
BLOCK2:
  param2:
    _parse: 'scalar'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            processor.load_yaml()
            processor.process_all_blocks()

            block_names = processor.keys()
            assert "BLOCK1" in block_names
            assert "BLOCK2" in block_names

    def test_export_to_json(self):
        """Test exporting processed data to JSON."""
        yaml_content = """
TESTBLOCK:
  test_param:
    _parse: 'scalar'
    _type: 'string'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp.flush()

            processor = DirectoryProcessor(tmp.name)
            processor.load_yaml()
            processor.process_all_blocks()

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as json_tmp:
                result = processor.export_to_json(json_tmp.name)
                assert result is True

                # Verify JSON file was created and contains expected data
                import json

                with open(json_tmp.name, "r") as f:
                    data = json.load(f)
                    assert "input_blocks" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
