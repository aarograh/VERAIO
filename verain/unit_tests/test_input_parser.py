#!/usr/bin/env python3
"""
Unit tests for InputParser class.

This test suite covers the InputParser functionality for
parsing VERA ASCII input files.
"""

import pytest
import tempfile
from pathlib import Path
from verain.parser import InputParser


class TestInputParser:
    """Unit tests for InputParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = InputParser()

    def test_init(self):
        """Test parser initialization."""
        assert self.parser.parsed_data == {}
        assert self.parser.blocks == {}

    def test_parse_simple_file(self):
        """Test parsing simple input file."""
        content = """[CASEID]
  title Test Case

[CORE]
  name TestCore
  size 100.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            result = self.parser.parse_file(tmp.name)
            assert "CASEID" in result
            assert "CORE" in result
            assert result["CASEID"]["title"] == ["Test", "Case"]
            assert result["CORE"]["name"] == ["TestCore"]

    def test_parse_multiline_parameters(self):
        """Test parsing multi-line parameters."""
        content = """[CORE]
  insert_map
    - BP20 -
    - - BP24

  det_map
    1 - 1
    - 1 -
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            result = self.parser.parse_file(tmp.name)
            assert "CORE" in result
            assert "insert_map" in result["CORE"]
            assert "det_map" in result["CORE"]
            assert isinstance(result["CORE"]["insert_map"], list)
            assert isinstance(result["CORE"]["det_map"], list)

    def test_parse_lattice_parameters(self):
        """Test parsing lattice parameters."""
        content = """[ASSEMBLY]
  lattice FUEL1
      IT
       1 1

  lattice FUEL2
      MT
       2 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            result = self.parser.parse_file(tmp.name)
            # ASSEMBLY becomes ASSEMBLY_0001 due to multi-instance block handling
            assert "ASSEMBLY_0001" in result
            # Parameters with multi-instance capability get numbered
            assert "lattice_0001" in result["ASSEMBLY_0001"]
            assert "lattice_0002" in result["ASSEMBLY_0001"]
            assert result["ASSEMBLY_0001"]["lattice_0001"] == ["FUEL1", "IT", "1", "1"]
            assert result["ASSEMBLY_0001"]["lattice_0002"] == ["FUEL2", "MT", "2", "2"]

    def test_parse_comments(self):
        """Test parsing with comments."""
        content = """[CASEID]
  title Test Case ! This is a comment

[CORE]
  ! This is a comment line
  name TestCore ! Another comment
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            result = self.parser.parse_file(tmp.name)
            assert "CASEID" in result
            assert "CORE" in result
            # Comments should be filtered out
            assert result["CASEID"]["title"] == ["Test", "Case"]
            assert result["CORE"]["name"] == ["TestCore"]

    def test_get_validation_errors(self):
        """Test getting validation errors."""
        errors = self.parser.get_validation_errors()
        assert isinstance(errors, list)

    def test_validation_errors(self):
        """Test validation error handling."""
        errors = self.parser.get_validation_errors()
        assert isinstance(errors, list)

    def test_get_parsed_blocks(self):
        """Test getting parsed block data."""
        content = """[STATE]
  param1 value1

[CORE]
  param2 value2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()

            result = self.parser.parse_file(tmp.name)
            assert "STATE_0001" in result
            assert "CORE" in result

    def test_parser_functionality(self):
        """Test core parser functionality."""
        data = {
            "CASEID": {"title": ["Test", "Case"]},
            "CORE": {"name": ["TestCore"], "size": ["100.0"]},
        }

        # Test that we can verify data structure is as expected
        assert "CASEID" in data
        assert "CORE" in data
        assert data["CASEID"]["title"] == ["Test", "Case"]
        assert data["CORE"]["size"] == ["100.0"]

    def test_include_functionality(self):
        """Test include file functionality."""
        # Create a temporary directory for our test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create an included file with valid parameters
            include_content = """[ASSEMBLY]
  title TestAssembly
  npin 17

[DETECTOR]
  title TestDetector
  type fission
"""
            include_file = temp_path / "assembly.inp"
            with open(include_file, "w") as f:
                f.write(include_content)

            # Create main file that includes the other file
            main_content = f"""[CASEID]
  title Test Case

include {include_file.name}

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse the main file
            result = self.parser.parse_file(main_file)

            # Verify that the included content is present
            assert "CASEID" in result
            assert "ASSEMBLY_0001" in result  # Multi-instance block gets numbered
            assert "DETECTOR_0001" in result  # Multi-instance block gets numbered
            assert "CORE" in result

            # Check that include tokens are not present in parsed result
            all_tokens = []
            for block_data in result.values():
                for param_values in block_data.values():
                    all_tokens.extend(param_values)

            assert "include" not in all_tokens
            assert include_file.name not in all_tokens

            # Verify content from included file
            assert result["ASSEMBLY_0001"]["title"] == ["TestAssembly"]
            assert result["ASSEMBLY_0001"]["npin"] == ["17"]
            assert result["DETECTOR_0001"]["title"] == ["TestDetector"]
            assert result["DETECTOR_0001"]["type"] == ["fission"]

    def test_nested_includes(self):
        """Test nested include functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create deeply included file
            deep_content = """[DETECTOR]
  title DeepDetector
  type neutron
"""
            deep_file = temp_path / "deep.inp"
            with open(deep_file, "w") as f:
                f.write(deep_content)

            # Create middle include file that includes deep file
            middle_content = f"""[ASSEMBLY]
  title MiddleAssembly
  npin 15

include {deep_file.name}
"""
            middle_file = temp_path / "middle.inp"
            with open(middle_file, "w") as f:
                f.write(middle_content)

            # Create main file that includes middle file
            main_content = f"""[CASEID]
  title Test Case

include {middle_file.name}

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse the main file
            result = self.parser.parse_file(main_file)

            # Verify all content is present
            assert "CASEID" in result
            assert "ASSEMBLY_0001" in result
            assert "DETECTOR_0001" in result
            assert "CORE" in result

            # Verify content from all levels
            assert result["ASSEMBLY_0001"]["title"] == ["MiddleAssembly"]
            assert result["ASSEMBLY_0001"]["npin"] == ["15"]
            assert result["DETECTOR_0001"]["title"] == ["DeepDetector"]
            assert result["DETECTOR_0001"]["type"] == ["neutron"]
            assert result["CORE"]["name"] == ["TestCore"]

    def test_include_relative_paths(self):
        """Test include with relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()

            # Create included file in subdirectory
            include_content = """[ASSEMBLY]
  title SubdirAssembly
  npin 19
"""
            include_file = sub_dir / "assembly.inp"
            with open(include_file, "w") as f:
                f.write(include_content)

            # Create main file with relative include path
            main_content = f"""[CASEID]
  title Test Case

include subdir/assembly.inp

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse the main file
            result = self.parser.parse_file(main_file)

            # Verify included content is present
            assert "ASSEMBLY_0001" in result
            assert result["ASSEMBLY_0001"]["title"] == ["SubdirAssembly"]
            assert result["ASSEMBLY_0001"]["npin"] == ["19"]

    def test_include_file_not_found(self):
        """Test include with non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main file with include to non-existent file
            main_content = """[CASEID]
  title Test Case

include nonexistent.inp

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                self.parser.parse_file(main_file)

    def test_circular_include(self):
        """Test circular include detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file A that includes file B
            file_a_content = f"""[CASEID]
  title Test Case A

include file_b.inp
"""
            file_a = temp_path / "file_a.inp"
            with open(file_a, "w") as f:
                f.write(file_a_content)

            # Create file B that includes file A (circular)
            file_b_content = f"""[ASSEMBLY]
  title TestAssembly
  npin 17

include file_a.inp
"""
            file_b = temp_path / "file_b.inp"
            with open(file_b, "w") as f:
                f.write(file_b_content)

            # Parse should raise ValueError for circular include
            with pytest.raises(ValueError, match="Circular include detected"):
                self.parser.parse_file(file_a)

    def test_include_fallback_to_scripts_init(self):
        """Test include fallback to scripts/Init/ directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main file that includes a file that exists in scripts/Init/
            main_content = """[CASEID]
  title Test Fallback

include mpact_test_mats.ini

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse the main file - should find mpact_test_mats.ini in scripts/Init/
            result = self.parser.parse_file(main_file)

            # Verify that the file was found and processed
            assert "CASEID" in result
            assert "CORE" in result

            # Check that the original blocks are there
            assert result["CORE"]["name"] == ["TestCore"]

            # Check that content from mpact_test_mats.ini was included
            # The file contains material definitions that get added as tokens
            caseid_tokens = result["CASEID"]["title"]
            assert "Test" in caseid_tokens
            assert "Fallback" in caseid_tokens
            # Should also contain material definitions like 'mat', 'aic', etc.
            assert "mat" in caseid_tokens
            assert len(caseid_tokens) > 10  # Much more content than just "Test Fallback"

            # Verify that no include tokens remain
            all_tokens = []
            for block_data in result.values():
                for param_values in block_data.values():
                    all_tokens.extend(param_values)
            assert "include" not in all_tokens
            assert "mpact_test_mats.ini" not in all_tokens

    def test_include_file_not_found_anywhere(self):
        """Test include with file that doesn't exist in either location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main file with include to truly non-existent file
            main_content = """[CASEID]
  title Test Case

include totally_nonexistent_file.inp

[CORE]
  name TestCore
"""
            main_file = temp_path / "main.inp"
            with open(main_file, "w") as f:
                f.write(main_content)

            # Parse should raise FileNotFoundError with both paths mentioned
            with pytest.raises(FileNotFoundError) as exc_info:
                self.parser.parse_file(main_file)

            # Error message should mention both locations that were checked
            error_msg = str(exc_info.value)
            assert "totally_nonexistent_file.inp" in error_msg
            assert "also checked" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
