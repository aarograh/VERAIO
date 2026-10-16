"""
Directory processor for VERAIn hierarchical YAML data.

This module provides the DirectoryProcessor class for handling Directory.yml files
that contain hierarchical VERA input specifications, and the plugin merge that lets
a separately-installed plugin extend that grammar.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List, FrozenSet, Sequence
import yaml

from verain.plugins import PluginRegistry, default_enabled


class PluginMergeError(Exception):
    """A plugin grammar fragment could not be merged into the base grammar.

    Every raise here names the plugin and the file responsible, per a
    hard-error-at-merge-time requirement: a keyword collision or a bad
    ``_datatype`` reference must stop the run, never be silently dropped.
    """


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
        #: block -> {keyword: owner}, owner is "base" or a plugin name.
        self.sources: Dict[str, Dict[str, str]] = {}
        self._named_prefixes_cache: Optional[set] = None

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

    def load_yaml(
        self,
        extra_sources: Optional[Sequence[Tuple[str, Union[str, Path], FrozenSet[str]]]] = None,
    ) -> None:
        """Load the YAML file, optionally merging plugin grammar fragments on top.

        Args:
            extra_sources: Optional ``(plugin_name, fragment_path, overrides)`` triples,
                one per plugin grammar file, in the order they should be merged. Omitting
                this (the default) is exactly the original single-file behaviour.
                ``overrides`` is the set of fully-qualified ``BLOCK.keyword`` names that
                plugin's manifest declares it may tighten.
        """
        if self.yaml_file_path is None or not self.yaml_file_path.exists():
            raise FileNotFoundError(f"Error: YAML file not found at {self.yaml_file_path}")

        with open(self.yaml_file_path, "r", encoding="utf-8") as file:
            # Use safe_load to avoid executing arbitrary code
            self.raw_data = yaml.safe_load(file)

        self.sources = self._base_provenance(self.raw_data)
        if extra_sources:
            self._merge_plugins(extra_sources)

    @staticmethod
    def _base_provenance(raw_data: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """Attribute every keyword already in ``raw_data`` to ``"base"``."""
        sources: Dict[str, Dict[str, str]] = {}
        if not raw_data:
            return sources
        for block_name, block_data in raw_data.items():
            if block_name.startswith("_") or not isinstance(block_data, dict):
                continue
            sources[block_name] = {key: "base" for key in block_data if not key.startswith("_")}
        return sources

    def _merge_plugins(self, extra_sources: Sequence[Tuple[str, Union[str, Path], FrozenSet[str]]]) -> None:
        """Apply every plugin grammar fragment in ``extra_sources`` to ``self.raw_data``.

        Fragments are grouped by plugin first, because a plugin's own
        ``_DATATYPES`` section (for its own reuse) has to be
        visible to every one of its fragment files, not just the one that
        declares it.
        """
        base_datatypes = (self.raw_data or {}).get("_DATATYPES", {}) or {}

        by_plugin: "Dict[str, Dict[str, Any]]" = {}
        for plugin_name, path, overrides in extra_sources:
            entry = by_plugin.setdefault(plugin_name, {"paths": [], "overrides": overrides})
            entry["paths"].append(Path(path))

        for plugin_name in sorted(by_plugin):
            info = by_plugin[plugin_name]
            fragment_docs = []
            plugin_datatypes: Dict[str, Any] = {}
            for path in info["paths"]:
                if not path.exists():
                    raise PluginMergeError(f"plugin '{plugin_name}': grammar file not found: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    doc = yaml.safe_load(f) or {}
                dts = doc.pop("_DATATYPES", None)
                if dts:
                    plugin_datatypes.update(dts)
                fragment_docs.append((path, doc))

            datatypes_table = {**base_datatypes, **plugin_datatypes}

            for path, doc in fragment_docs:
                for block_name, block_data in doc.items():
                    if block_name.startswith("_"):
                        raise PluginMergeError(f"plugin '{plugin_name}' ({path}): unexpected top-level key '{block_name}'")
                    self._merge_one_block(plugin_name, path, block_name, block_data, datatypes_table, info["overrides"])

    def _merge_one_block(
        self,
        plugin_name: str,
        path: Path,
        block_name: str,
        block_data: Any,
        datatypes_table: Dict[str, Any],
        overrides: FrozenSet[str],
    ) -> None:
        """Merge one plugin grammar block into ``self.raw_data``."""
        if not isinstance(block_data, dict):
            raise PluginMergeError(f"plugin '{plugin_name}' ({path}): block '{block_name}' must be a mapping")
        if block_name != block_name.upper():
            raise PluginMergeError(f"plugin '{plugin_name}' ({path}): block name '{block_name}' must be upper-case")
        if re.search(r"_\d{4}$", block_name):
            raise PluginMergeError(
                f"plugin '{plugin_name}' ({path}): block name '{block_name}' ends in a reserved " "instance suffix (_NNNN)"
            )

        self._resolve_datatypes(block_data, datatypes_table, f"plugin '{plugin_name}' ({path}) block '{block_name}'")

        extends = bool(block_data.pop("_extends", False))
        exists = isinstance(self.raw_data.get(block_name), dict)

        if extends and not exists:
            raise PluginMergeError(
                f"plugin '{plugin_name}' ({path}): block '{block_name}' declares _extends: true " "but no such block exists"
            )
        if not extends and exists:
            raise PluginMergeError(
                f"plugin '{plugin_name}' ({path}): block '{block_name}' already exists (base or "
                "another plugin) and must declare _extends: true to add keywords to it"
            )

        if not extends:
            self.raw_data[block_name] = {}
            directory = self.raw_data.setdefault("_DIRECTORY", {})
            if directory is None:
                directory = self.raw_data["_DIRECTORY"] = {}
            directory[block_name] = None

        target_block = self.raw_data[block_name]
        target_sources = self.sources.setdefault(block_name, {})

        for key, key_data in block_data.items():
            if key.startswith("_"):
                if not extends:
                    # Block-level metadata from this block's own _datatype expansion
                    # (e.g. _parse/_named from `_datatype: dtblock`).
                    target_block[key] = key_data
                continue

            block_input_name = f"{block_name}.{key}"
            if not isinstance(key_data, dict):
                raise PluginMergeError(f"plugin '{plugin_name}' ({path}): keyword '{block_input_name}' must be a mapping")

            node_override = bool(key_data.pop("_override", False))
            manifest_has = block_input_name in overrides
            if node_override != manifest_has:
                raise PluginMergeError(
                    f"plugin '{plugin_name}' ({path}): '{block_input_name}' "
                    + (
                        "sets _override: true but is not listed in the manifest's overrides"
                        if node_override
                        else "is listed in the manifest's overrides but its grammar node does " "not set _override: true"
                    )
                )

            collides = key in target_sources
            if collides and not node_override:
                owner = target_sources[key]
                raise PluginMergeError(
                    f"plugin '{plugin_name}' ({path}): keyword '{block_input_name}' collides with "
                    + ("a base keyword" if owner == "base" else f"plugin '{owner}'s keyword")
                )
            if node_override and not collides:
                raise PluginMergeError(
                    f"plugin '{plugin_name}' ({path}): '{block_input_name}' is declared as an override but "
                    "no existing keyword exists to override"
                )

            target_block[key] = key_data
            target_sources[key] = plugin_name

    @staticmethod
    def _resolve_datatypes(node: Any, datatypes_table: Dict[str, Any], context: str) -> None:
        """Expand ``_datatype: <name>`` nodes the way ``<<: *name`` would, recursively.

        YAML anchors are per-document, so a plugin fragment in its own file
        cannot write ``<<: *dtword`` against an anchor defined in base's
        Directory.yml. ``_datatype`` is the cross-file substitute: look the name
        up, lay its keys under the node's own (so the node's explicit keys win,
        exactly as ``<<:`` merge-key precedence does), then recurse into
        whatever the node still holds.
        """
        if not isinstance(node, dict):
            return
        if "_datatype" in node:
            name = node.pop("_datatype")
            key = name if str(name).startswith("_") else f"_{name}"
            if key not in datatypes_table:
                available = sorted(str(k).lstrip("_") for k in datatypes_table)
                raise PluginMergeError(f"{context}: unknown _datatype '{name}' (available: {', '.join(available)})")
            expansion = datatypes_table[key]
            if not isinstance(expansion, dict):
                raise PluginMergeError(f"{context}: _datatype '{name}' is not a mapping")
            for ek, ev in expansion.items():
                node.setdefault(ek, ev)
        for v in list(node.values()):
            DirectoryProcessor._resolve_datatypes(v, datatypes_table, context)

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
                "sources": self.sources,
            },
            "input_blocks": input_blocks,
            "block_count": len(input_blocks),
            "parameter_count": sum(len(block) for block in input_blocks.values()),
        }

        return self.processed_data

    def source_of(self, block_name: str, parameter_name: str) -> Optional[str]:
        """Which plugin (or ``"base"``) contributed ``block_name.parameter_name``."""
        return self.sources.get(block_name, {}).get(parameter_name)

    def named_prefixes(self) -> set:
        """Every parameter name anywhere in the grammar that is multi-instance.

        Cached on this instance: since callers share one processor per
        plugin-``enabled`` state (see ``build_directory_processor``), this is
        effectively computed once per process per state, plugin keywords
        included with no extra wiring on the caller's side.
        """
        if self._named_prefixes_cache is None:
            prefixes = set()
            for block_name in self.keys():  # pylint: disable=consider-using-dict-items
                for param_name in self[block_name]:
                    if self.is_multi_instance_parameter(block_name, param_name):
                        prefixes.add(param_name)
            self._named_prefixes_cache = prefixes
        return self._named_prefixes_cache

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


_processor_cache: Dict[bool, "DirectoryProcessor"] = {}


def build_directory_processor(enabled: Optional[bool] = None) -> "DirectoryProcessor":
    """Build (or return the cached) processor for base grammar plus discovered plugins.

    This is the one place ``InputParser`` and ``XMLGenerator`` both go to get
    a merged grammar, so they always agree on it. Cached by ``enabled`` so
    repeated construction -- one ``InputParser``/``XMLGenerator`` per
    ``react2xml`` call, or hundreds across a test session -- does not re-parse
    the 20,000-line base Directory.yml every time.
    """
    if enabled is None:
        enabled = default_enabled()
    if enabled in _processor_cache:
        return _processor_cache[enabled]

    base_path = Path(__file__).parent / "Directory.yml"
    processor = DirectoryProcessor(base_path)
    registry = PluginRegistry.load(enabled=enabled)
    extra_sources = [(plugin.name, path, plugin.overrides()) for plugin, path in registry.grammar_files()]
    processor.load_yaml(extra_sources=extra_sources or None)
    processor.process_all_blocks()

    _processor_cache[enabled] = processor
    return processor


def reset_directory_processor_cache() -> None:
    """Drop the cached merged processors (for tests that change discovery inputs)."""
    _processor_cache.clear()
