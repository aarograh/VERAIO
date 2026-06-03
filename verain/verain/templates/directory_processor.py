"""
Directory processor for VERAIn hierarchical YAML data.

This module provides the DirectoryProcessor class for handling Directory.yml files
that contain hierarchical VERA input specifications.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
import yaml


class DirectoryProcessor:
    """Class to handle processing of Directory.yml hierarchical data."""

    def __init__(self, yaml_file_path: Optional[Union[str, Path]]):
        """
        Initialize the processor with the path to Directory.yml

        Args:
            yaml_file_path: Path to the Directory.yml file
        """
        if yaml_file_path is not None:
            self.yaml_file_path = Path(yaml_file_path)
        else:
            self.yaml_file_path = None
        self.raw_data = None
        self.processed_data = {}

    def __contains__(self, item: Union[str, Tuple[str, str]]) -> bool:
        """
        Check if a block or parameter exists in the processed data.

        Args:
            item: Block name as str or (block_name, parameter_name) as tuple
        """
        if isinstance(item, str):
            return item in self.processed_data
        if isinstance(item, tuple) and len(item) == 2:
            block_name, param_name = item
            if block_name in self.processed_data:
                return param_name in self.processed_data[block_name]
        return False

    def __getitem__(self, item: Union[str, Tuple[str, str]]) -> Any:
        """
        Get a block or parameter from the processed data.

        Args:
            item: Block name as str or (block_name, parameter_name) as tuple
        """
        if isinstance(item, str):
            return self.processed_data.get("input_blocks", {})[item]
        if isinstance(item, tuple) and len(item) == 2:
            block_name, param_name = item
            block = self.processed_data.get("input_blocks", {}).get(block_name, {})
            return block.get(param_name)
        raise KeyError(f"Item {item} of type {type(item)} not found in processed data.")

    def get(self, item: Union[str, Tuple[str, str]], default: Any = None) -> Any:
        """
        Get a block or parameter from the processed data with a default.

        Args:
            item: Block name as str or (block_name, parameter_name) as tuple
            default: Default value if item not found
        """
        try:
            return self[item]
        except KeyError as e:
            if default is not None:
                return default
            raise e

    def __iter__(self):
        """
        Iterate over block names in the processed data.
        """
        yield from self.processed_data.get("input_blocks", {}).keys()

    def keys(self) -> List[str]:
        """
        Get list of all block names in the processed data.

        Returns:
            List of block names
        """
        return list(self.processed_data.get("input_blocks", {}).keys())

    def load_yaml(self) -> None:
        """Load the YAML file and parse it."""
        if self.yaml_file_path is None or not self.yaml_file_path.exists():
            raise FileNotFoundError(f"Error: YAML file not found at {self.yaml_file_path}")

        with open(self.yaml_file_path, "r", encoding="utf-8") as file:
            # Use safe_load to avoid executing arbitrary code
            self.raw_data = yaml.safe_load(file)

    def extract_datatypes(self) -> Dict[str, Any]:
        """
        Extract the _DATATYPES section for reference.

        Returns:
            Dictionary containing datatype definitions
        """
        if not self.raw_data:
            return {}

        datatypes = self.raw_data.get("_DATATYPES", {})

        # Clean up the datatype definitions by removing YAML anchor markers
        clean_datatypes = {}
        for key, value in datatypes.items():
            # Remove leading underscore and clean key
            clean_key = key.lstrip("_")
            if isinstance(value, dict):
                clean_datatypes[clean_key] = {k.lstrip("_"): v for k, v in value.items()}
            else:
                clean_datatypes[clean_key] = value

        return clean_datatypes

    def extract_directory_structure(self) -> Dict[str, Any]:
        """
        Extract the _DIRECTORY section showing main blocks.

        Returns:
            Dictionary containing directory structure
        """
        if not self.raw_data:
            return {}

        return self.raw_data.get("_DIRECTORY", {})

    def process_input_block(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single input block (e.g., CASEID, BRANCH, STATE, etc.).

        Args:
            block_data: Raw block data from YAML

        Returns:
            Processed block data with parameters flattened directly under the block
        """
        processed_params = {}

        for param_name, param_data in block_data.items():
            if isinstance(param_data, dict):
                processed_param = self.process_parameter(param_data)
                processed_params[param_name] = processed_param
            else:
                # Handle simple values (like strings, None, etc.)
                processed_params[param_name] = {
                    "value": param_data,
                    "data_type": type(param_data).__name__,
                    "parse_type": "simple",
                }

        return processed_params

    def process_parameter(self, param_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single parameter within a block.

        Args:
            param_data: Raw parameter data

        Returns:
            Processed parameter data
        """
        processed_param = {
            "parse_type": param_data.get("_parse", "unknown"),
            "data_type": param_data.get("_type", "unknown"),
            "named": param_data.get("_named", None),
            "style": param_data.get("_style", None),
            "content": param_data.get("_content", None),
            "overwrite": param_data.get("_overwrite", None),
            "options": param_data.get("_options", None),
            "defaults": param_data.get("_defaults", None),
            "checks": param_data.get("_check", []),
        }

        # Handle _slash specially: if the key exists in param_data, set it to True
        if "_slash" in param_data:
            processed_param["slash"] = True

        # Remove None values to keep the dictionary clean
        processed_param = {k: v for k, v in processed_param.items() if v is not None}

        return processed_param

    def process_all_blocks(self) -> Dict[str, Any]:
        """
        Process all input blocks from the YAML file.

        Returns:
            Complete processed data structure
        """
        if not self.raw_data:
            raise RuntimeError("No data loaded. Call load_yaml() first.")

        # Extract metadata
        datatypes = self.extract_datatypes()
        directory = self.extract_directory_structure()

        # Process all main input blocks
        input_blocks = {}
        for key, value in self.raw_data.items():
            # Skip metadata sections
            if key.startswith("_"):
                continue

            if isinstance(value, dict):
                processed_block = self.process_input_block(value)
                input_blocks[key] = processed_block

        # Build complete processed data structure
        self.processed_data = {
            "metadata": {
                "source_file": str(self.yaml_file_path),
                "datatypes": datatypes,
                "directory_structure": directory,
            },
            "input_blocks": input_blocks,
            "block_count": len(input_blocks),
            "parameter_count": sum(len(block) for block in input_blocks.values()),
        }

        return self.processed_data

    def get_block_parameter_checks(self, block_name: str, parameter_name: str) -> List[Any]:
        """
        Get validation checks for a specific parameter in a block.

        Args:
            block_name: Name of the block
            parameter_name: Name of the parameter

        Returns:
            List of validation checks for the specified parameter
        """
        if not self.processed_data:
            return []

        input_blocks = self.processed_data.get("input_blocks", {})
        block_data = input_blocks.get(block_name, {})
        param_data = block_data.get(parameter_name, {})

        return param_data.get("checks", [])

    def is_multi_instance_block(self, block_name: str) -> bool:
        """
        Check if a block can appear multiple times based on Directory.yml metadata.

        Blocks with _named: 1 in their definition can have multiple instances
        (e.g., STATE, BRANCH, ASSEMBLY, CONTROL, INSERT, DETECTOR).

        Args:
            block_name: Name of the block to check

        Returns:
            True if block can appear multiple times, False otherwise
        """
        if not self.processed_data:
            return False

        input_blocks = self.processed_data.get("input_blocks", {})
        block_data = input_blocks.get(block_name, {})

        # Check if block has _named parameter set to 1
        named_param = block_data.get("_named")
        if isinstance(named_param, dict):
            return named_param.get("value") == 1

        return False

    def is_multi_instance_parameter(self, block_name: str, parameter_name: str) -> bool:
        """
        Check if a parameter within a block can have multiple instances.

        Parameters with _named: 1 in their definition can have multiple instances
        (e.g., control rods in CONTROL block).

        Args:
            block_name: Name of the block containing the parameter
            parameter_name: Name of the parameter to check

        Returns:
            True if parameter can have multiple instances, False otherwise
        """
        if not self.processed_data:
            return False

        input_blocks = self.processed_data.get("input_blocks", {})
        block_data = input_blocks.get(block_name, {})
        param_data = block_data.get(parameter_name, {})
        return param_data.get("named", 0) == 1

    def search_parameters(self, search_term: str, case_sensitive: bool = False) -> Dict[str, List[str]]:
        """
        Search for parameters containing a specific term.

        Args:
            search_term: Term to search for
            case_sensitive: Whether search should be case sensitive

        Returns:
            Dictionary with block names as keys and matching parameters as values
        """
        if not self.processed_data:
            return {}

        results = {}
        search_term = search_term if case_sensitive else search_term.lower()

        for block_name, block_data in self.processed_data.get("input_blocks", {}).items():
            matching_params = []

            for param_name in block_data:
                param_check = param_name if case_sensitive else param_name.lower()
                if search_term in param_check:
                    matching_params.append(param_name)

            if matching_params:
                results[block_name] = matching_params

        return results

    def export_to_json(self, output_file: str, indent: int = 2) -> bool:
        """
        Export processed data to JSON file.

        Args:
            output_file: Path for output JSON file
            indent: JSON indentation level

        Returns:
            True if successful, False otherwise
        """
        if not self.processed_data:
            print("Error: No processed data available. Call process_all_blocks() first.")
            return False

        try:
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(self.processed_data, file, indent=indent, ensure_ascii=False)

            return True

        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

    def print_summary(self):
        """Print a summary of the processed data."""
        if not self.processed_data:
            print("No data processed yet.")
            return

        print("\n" + "=" * 60)
        print("DIRECTORY.YML PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Source file: {self.processed_data['metadata']['source_file']}")
        print(f"Total blocks: {self.processed_data['block_count']}")
        print(f"Total parameters: {self.processed_data['parameter_count']}")

        print("\nAvailable datatypes: " f"{len(self.processed_data['metadata']['datatypes'])}")
        for dtype in self.processed_data["metadata"]["datatypes"].keys():
            print(f"  - {dtype}")

        print("\nInput blocks:")
        for block_name, block_data in self.processed_data["input_blocks"].items():
            param_count = len(block_data)
            print(f"  - {block_name}: {param_count} parameters")


# Convenience imports for common use cases
def process_directory(yaml_path) -> Dict[str, Any]:
    """
    Convenience function to process a Directory.yml file.

    Args:
        yaml_path (str): Path to the Directory.yml file

    Returns:
        dict: Processed hierarchical data or None if failed
    """
    processor = DirectoryProcessor(yaml_path)
    processor.load_yaml()
    return processor.process_all_blocks()
