"""
Input parser utilities for VERAIn.

This module provides classes and functions for parsing VERA ASCII input files.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union
import shlex

from verain.templates import DirectoryProcessor
from verain.parser.validation import ValidationEngine


class InputParser:
    """
    Parser for VERA ASCII input files.

    This class provides functionality to parse VERA input files and extract
    structured data that can be converted to XML or other formats.
    """

    _directory_processor_is_init = False
    _directory_processor = DirectoryProcessor(None)

    def __init__(self):
        """Initialize the input parser."""
        self.parsed_data = {}
        self.blocks = {}
        self.validation_errors = []
        self.line_lengths: dict = {}
        self.directory_yml_path = Path(os.path.abspath(__file__)).parent.parent / "templates" / "Directory.yml"

        if not InputParser._directory_processor_is_init:
            InputParser._directory_processor = DirectoryProcessor(self.directory_yml_path)
            InputParser._directory_processor.load_yaml()
            InputParser._directory_processor.process_all_blocks()
            InputParser._directory_processor_is_init = True

        self.validation_engine = ValidationEngine()

    def __contains__(self, item: Union[str, Tuple[str, str]]) -> bool:
        """
        Check if a block or parameter exists in the parsed data.

        Args:
            item: Block name as str or (block_name, parameter_name) as tuple
        """
        if isinstance(item, str):
            return item in self.blocks
        if isinstance(item, tuple) and len(item) == 2:
            block_name, param_name = item
            if block_name in self.blocks:
                return param_name in self.blocks[block_name]
        return False

    def __getitem__(self, item: Union[str, Tuple[str, str]]) -> Any:
        """
        Get a block or parameter value from the parsed data.

        Args:
            item: Block name as str or (block_name, parameter_name) as tuple
        """
        if isinstance(item, str):
            return self.blocks[item]
        if isinstance(item, tuple) and len(item) == 2:
            block_name, param_name = item
            block = self.blocks[block_name]
            return block[param_name]
        raise KeyError(f"Item {item} of type {type(item)} not found in parsed data.")

    def __iter__(self):
        """Iterator over block names in the parsed data."""
        yield from self.blocks

    def keys(self) -> List[str]:
        """
        Get list of block names in the parsed data.

        Returns:
            List of block names
        """
        return list(self.blocks.keys())

    def base_block_name(self, block_name: str) -> str:
        """
        Get the base block name for numbered blocks.

        Args:
            block_name: Full block name (e.g., STATE_0001)

        Returns:
            Base block name (e.g., STATE)
        """
        if "_" in block_name:
            base_block = "_".join(block_name.split("_")[:-1])
            return base_block if InputParser._directory_processor.is_multi_instance_block(base_block) else block_name
        return block_name

    def base_parameter_name(self, block_name: str, param_name: str) -> str:
        """
        Get the base parameter name for numbered parameters.

        Args:
            block_name: Full block name (e.g., STATE_0001)
            param_name: Full parameter name (e.g., temp_1)

        Returns:
            Base parameter name (e.g., temp)
        """
        if "_" in param_name:
            base_param = "_".join(param_name.split("_")[:-1])
            base_block = self.base_block_name(block_name)
            return (
                base_param
                if InputParser._directory_processor.is_multi_instance_parameter(base_block, base_param)
                else param_name
            )
        return param_name

    def parse_file(self, input_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse a VERA input file.

        Args:
            input_file: Path to the input file

        Returns:
            Dictionary containing parsed input data
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.blocks = {}
        self.validation_errors = []  # Reset validation errors for each file

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        self._process_content(content, input_path.parent)

        # Extract _line_lengths from blocks into self.line_lengths, then strip
        # from the returned dict so downstream consumers see clean data.
        self.line_lengths = {}
        for block_key, block_data in self.blocks.items():
            if isinstance(block_data, dict) and "_line_lengths" in block_data:
                self.line_lengths[block_key] = block_data.pop("_line_lengths")

        return self.blocks

    def _process_content(self, content: str, base_dir: Union[Path, None] = None) -> None:
        """
        Process file content using the new token-based approach.

        Args:
            content: File content as string
            base_dir: Base directory for resolving relative include paths
        """
        # Join all lines and tokenize the entire file
        tokens = self._tokenize_file(content, base_dir)

        # Process all tokens
        self._process_tokens(tokens)

    def _tokenize_file(
        self, content: str, base_dir: Union[Path, None] = None, included_files: Union[set, None] = None
    ) -> List[str]:
        """
        Tokenize the entire file content into a flat list of tokens.
        Handle include statements by recursively processing included files.

        Args:
            content: File content as string
            base_dir: Base directory for resolving relative include paths
            included_files: Set of already included files to prevent infinite recursion

        Returns:
            List of tokens with quoted strings preserved and includes expanded
        """
        if included_files is None:
            included_files = set()

        tokens = []
        lines = content.split("\n")

        for line in lines:
            # Remove comments
            comment_index = line.find("!")
            if comment_index != -1:
                line = line[:comment_index]

            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            try:
                line_tokens = shlex.split(line)
                # Identify which tokens were originally quoted
                quoted = self._identify_quoted_tokens(line, line_tokens)
                # Split by semicolons into sub-commands
                sub_lines = [[]]
                sub_quoted = [[]]
                for j, tok in enumerate(line_tokens):
                    q = quoted[j] if j < len(quoted) else False
                    if not q and tok == ";":
                        sub_lines.append([])
                        sub_quoted.append([])
                    elif not q and tok.endswith(";"):
                        sub_lines[-1].append(tok[:-1])
                        sub_quoted[-1].append(q)
                        sub_lines.append([])
                        sub_quoted.append([])
                    else:
                        sub_lines[-1].append(tok)
                        sub_quoted[-1].append(q)
                for sl, sq in zip(sub_lines, sub_quoted):
                    if not sl:
                        continue
                    # Process include statements first
                    expanded_tokens = self._process_includes(sl, base_dir, included_files)
                    # Then expand special syntax tokens
                    final_tokens = []
                    for j, token in enumerate(expanded_tokens):
                        expanded = self._expand_special_syntax(token)
                        for et in expanded:
                            if j < len(sq) and sq[j]:
                                final_tokens.append("\x00QUOTED\x00" + et)
                            else:
                                final_tokens.append(et)
                    tokens.extend(final_tokens)
                    tokens.append("\x00NEWLINE\x00")
            except ValueError:
                # If shlex fails (unmatched quotes), fall back to simple split
                line_tokens = line.split()
                # Process include statements first
                expanded_tokens = self._process_includes(line_tokens, base_dir, included_files)
                # Then expand special syntax tokens
                final_tokens = []
                for token in expanded_tokens:
                    final_tokens.extend(self._expand_special_syntax(token))
                tokens.extend(final_tokens)
                tokens.append("\x00NEWLINE\x00")

        return tokens

    @staticmethod
    def _identify_quoted_tokens(line, tokens):
        """Identify which tokens in the shlex output were originally quoted."""
        quoted = [False] * len(tokens)
        pos = 0
        for i, token in enumerate(tokens):
            # Find this token in the line starting from pos
            idx = line.find(token, pos)
            if idx > 0 and line[idx - 1] in ("'", '"'):
                quoted[i] = True
            elif idx >= 0:
                # Check if preceded by quote with possible whitespace
                before = line[:idx].rstrip()
                if before and before[-1] in ("'", '"'):
                    quoted[i] = True
            if idx >= 0:
                pos = idx + len(token)
        return quoted

    def _process_includes(self, tokens: List[str], base_dir: Union[Path, None], included_files: set) -> List[str]:
        """
        Process include statements in tokens and replace them with file contents.

        Args:
            tokens: List of tokens from a line
            base_dir: Base directory for resolving relative include paths
            included_files: Set of already included files to prevent infinite recursion

        Returns:
            List of tokens with includes expanded
        """
        if len(tokens) < 2:
            return tokens

        result_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i] == "include" and i + 1 < len(tokens):
                # Found include statement
                include_path = tokens[i + 1]

                # First try to resolve relative to the current directory
                if base_dir:
                    resolved_path = base_dir / include_path
                else:
                    resolved_path = Path(include_path)

                # If file doesn't exist, try verain/init/ as fallback
                # (verain/init/ is the installed package location of the Init files;
                # parser.py lives at verain/parser/parser.py so parent.parent = verain/)
                if not resolved_path.exists():
                    parser_dir = Path(__file__).parent.parent
                    scripts_init_path = parser_dir / "init" / include_path

                    if scripts_init_path.exists():
                        resolved_path = scripts_init_path
                    else:
                        raise FileNotFoundError(f"Include file not found: {resolved_path} (also checked {scripts_init_path})")

                # Convert to absolute path for tracking included files
                abs_path = resolved_path.resolve()

                # Check for infinite recursion
                if abs_path in included_files:
                    raise ValueError(f"Circular include detected: {abs_path}")

                # Add to included files set
                included_files.add(abs_path)

                try:
                    # Read and process the included file
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        include_content = f.read()

                    # Recursively tokenize the included file with a copy of included_files
                    include_tokens = self._tokenize_file(include_content, resolved_path.parent, included_files)
                    result_tokens.extend(include_tokens)

                    # Skip the include and path tokens
                    i += 2
                finally:
                    # Remove from included files set after processing
                    included_files.discard(abs_path)
            else:
                result_tokens.append(tokens[i])
                i += 1

        return result_tokens

    def _expand_special_syntax(self, token: str) -> List[str]:
        """
        Expand special VERAIn syntax tokens into lists of values.

        Args:
            token: Single token that might contain special syntax

        Returns:
            List of expanded tokens (single token if no expansion needed)
        """
        # Handle range specifications like <11.951..221.111x5.0>
        if token.startswith("<") and token.endswith(">") and ".." in token:
            return self._expand_range_syntax(token)

        # Handle multiplication expressions like 225*48
        if "*" in token and len(token.split("*")) == 2:
            return self._expand_multiplication_syntax(token)

        # Return original token if no expansion needed
        return [token]

    def _expand_range_syntax(self, token: str) -> List[str]:
        """
        Expand range syntax like <start..stopxspacing> into a list of values.

        Args:
            token: Range token like <11.951..221.111x5.0>

        Returns:
            List of expanded numeric values as strings
        """
        try:
            # Remove angle brackets
            inner = token[1:-1]

            # Split on 'x' to get range and spacing
            if "x" not in inner and ".." in inner:
                range_part, spacing_str = inner, "1"
            elif "x" not in inner:
                return [token]  # Return original if invalid format
            else:
                range_part, spacing_str = inner.split("x", 1)
            spacing = float(spacing_str)

            # Split range on '..'
            if ".." not in range_part:
                return [token]  # Return original if invalid format

            start_str, stop_str = range_part.split("..", 1)
            start = float(start_str)
            stop = float(stop_str)

            # Generate the sequence
            values = []
            current = start
            while current <= stop + 1e-10:  # Small epsilon for floating point comparison
                values.append(str(int(current)) if current.is_integer() else str(current))
                current += spacing

            return values

        except (ValueError, IndexError):
            # Return original token if parsing fails
            return [token]

    def _expand_multiplication_syntax(self, token: str) -> List[str]:
        """
        Expand multiplication syntax like 225*48 or 21*TUBE into repeated values.

        Args:
            token: Multiplication token like 225*48 or 21*TUBE

        Returns:
            List with the second value repeated first value times
        """
        try:
            parts = token.split("*")
            if len(parts) != 2:
                return [token]

            count_str, value_str = parts
            count = int(count_str)

            # Return list with value repeated count times
            return [value_str] * count

        except (ValueError, TypeError):
            # Return original token if parsing fails
            return [token]

    def _process_tokens(self, tokens: List[str]) -> None:
        """
        Process all tokens and build the parsed data structure.

        Args:
            tokens: List of tokens from the file
        """
        QUOTE_MARKER = "\x00QUOTED\x00"
        NEWLINE_MARKER = "\x00NEWLINE\x00"
        i = 0
        current_block = None
        block_counters = {}  # Track multiple instances of blocks
        param_counters = {}  # Track multiple instances of parameters

        while i < len(tokens):
            token = tokens[i]

            # Skip newline markers at top level
            if token == NEWLINE_MARKER:
                i += 1
                continue

            is_quoted = token.startswith(QUOTE_MARKER)
            if is_quoted:
                token = token[len(QUOTE_MARKER) :]

            # Check if this is a block name
            if not is_quoted and token.startswith("[") and token.endswith("]"):
                block_name = token[1:-1].strip().upper()

                # Handle blocks that can appear multiple times
                if self._is_multi_instance_block(block_name):
                    if block_name not in block_counters:
                        block_counters[block_name] = 0
                    block_counters[block_name] += 1
                    current_block = f"{block_name}_{block_counters[block_name]:04d}"
                else:
                    current_block = block_name

                self.blocks[current_block] = {}
                i += 1
                continue

            # If we're not in a block, skip token
            if not current_block:
                i += 1
                continue

            # Check if this token is a parameter (quoted tokens are never parameters)
            base_block = self.base_block_name(current_block)
            if not is_quoted and self._is_parameter(token, base_block):
                param_name = token
                param_values = []
                i += 1
                same_line = True  # Still on the same line as param keyword
                is_multi_instance = False

                # Handle special case for parameters that can appear multiple times
                if InputParser._directory_processor.is_multi_instance_parameter(base_block, param_name):
                    is_multi_instance = True
                    param_counters.setdefault(param_name, 0)
                    param_counters[param_name] += 1
                    param_name = f"{param_name}_{param_counters[param_name]:04d}"

                # Collect all following tokens until we hit another parameter or block
                while i < len(tokens):
                    next_token = tokens[i]

                    # Handle newline markers
                    if next_token == NEWLINE_MARKER:
                        same_line = False
                        param_values.append(NEWLINE_MARKER)
                        i += 1
                        continue

                    next_is_quoted = next_token.startswith(QUOTE_MARKER)
                    if next_is_quoted:
                        next_token = next_token[len(QUOTE_MARKER) :]

                    # Check if next token is a block
                    if not next_is_quoted and next_token.startswith("[") and next_token.endswith("]"):
                        break

                    # Check if next token is a parameter
                    # On a new line, always break on a recognized parameter.
                    # On the same line, break only for non-multi-instance params
                    # that already have values (handles inline [STATE] power 46 boron 1023).
                    # Multi-instance params (det, cell, etc.) have complex data that
                    # may contain tokens matching other param names, so never break same-line.
                    if not next_is_quoted and self._is_parameter(next_token, base_block):
                        if not same_line:
                            break
                        if not is_multi_instance and param_values:
                            break

                    param_values.append(next_token)
                    i += 1

                # Compute line lengths from NEWLINE_MARKERs, then strip them
                line_lengths = self._extract_line_lengths(param_values, NEWLINE_MARKER)
                clean_values = [v for v in param_values if v != NEWLINE_MARKER]

                # Store the parameter (clean, no markers)
                self.blocks[current_block][param_name] = clean_values

                # Store line-length metadata if present
                if line_lengths:
                    if "_line_lengths" not in self.blocks[current_block]:
                        self.blocks[current_block]["_line_lengths"] = {}
                    self.blocks[current_block]["_line_lengths"][param_name] = line_lengths
            else:
                i += 1

    @staticmethod
    def _extract_line_lengths(values, marker):
        """Extract line lengths from a value list containing newline markers.

        Returns a list of token counts per line, or None if no markers found.
        """
        if marker not in values:
            return None
        lengths = []
        count = 0
        for v in values:
            if v == marker:
                if count > 0:
                    lengths.append(count)
                count = 0
            else:
                count += 1
        if count > 0:
            lengths.append(count)
        return lengths if lengths else None

    def _is_multi_instance_block(self, block_name: str) -> bool:
        """
        Check if a block can appear multiple times.

        Args:
            block_name: Block name to check

        Returns:
            True if block can appear multiple times
        """
        if not InputParser._directory_processor:
            return False
        return InputParser._directory_processor.is_multi_instance_block(block_name)

    def _is_parameter(self, token: str, current_block: str) -> bool:
        """
        Check if a token is a valid parameter for the current block.

        Args:
            token: Token to check
            current_block: Current block name

        Returns:
            True if token is a valid parameter
        """
        # Special case for include parameter
        if token == "include":
            return True

        # Cannot validate without directory processor or block context
        if not InputParser._directory_processor or not current_block:
            return False

        # Get base block name for lookup
        lookup_block = self.base_block_name(current_block)

        # Get valid parameters for this block
        block_params = InputParser._directory_processor[lookup_block].keys()
        return token in block_params

    def validate_input(self, blocks: Dict[str, Any]) -> bool:
        """
        Validate input blocks using the validation engine.

        Args:
            blocks: Dictionary of parsed blocks to validate

        Returns:
            True if validation passed, False otherwise
        """
        if not self.validation_engine:
            self.validation_errors.append("ValidationEngine not initialized")
            return False

        validation_errors = []
        for block, block_data in blocks.items():
            for parameter, values in block_data.items():
                try:
                    validation_errors.extend(
                        self.validation_engine.validate_parameter(
                            parameter,
                            values,
                            InputParser._directory_processor.get_block_parameter_checks(
                                self.base_block_name(block), parameter
                            ),
                        )
                    )
                # pylint: disable=broad-exception-caught
                except Exception as e:
                    validation_errors.append(f"Validation error: {e}")
        if validation_errors:
            self.validation_errors.extend(validation_errors)
            return False
        return True

    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors.

        Returns:
            List of validation error messages
        """
        return self.validation_errors.copy()

    def write_verain_file(self, output_file: Union[str, Path], data: Dict[str, Any]) -> None:
        """
        Write the parsed data back to a VERA input file.

        Args:
            output_file: Path to the output file
            data: Dictionary containing parsed input data
        """
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            self._write_blocks(f, data)

    def _write_blocks(self, file_handle, data: Dict[str, Any]) -> None:
        """
        Write blocks to the file handle.

        Args:
            file_handle: Open file handle to write to
            data: Dictionary containing parsed input data
        """
        preferred_order = [
            "CASEID",
            "BRANCH",
            "STATE",
            "TRANSIENT",
            "CORE",
            "ASSEMBLY",
            "INSERT",
            "CONTROL",
            "DETECTOR",
            "EDITS",
            "MPACT",
            "COBRATF",
            "SHIFT",
            "BISON",
            "FAST",
            "MAMBA",
            "COUPLING",
            "VERAONEWAY",
            "RUN",
        ]

        # Write blocks in preferred order first
        written_order = set()
        for block in preferred_order:
            for k in sorted(data.keys()):
                if self.base_block_name(k) == block:
                    self._write_block(file_handle, self.base_block_name(k), data[k])
                    written_order.add(k)

        # Write any remaining blocks not in preferred order
        for k in sorted(data.keys()):
            if k not in written_order:
                self._write_block(file_handle, self.base_block_name(k), data[k])

    def _write_block(self, file_handle, block_name: str, block_data: Dict[str, Any]) -> None:
        """
        Write a single block to the file handle.

        Args:
            file_handle: Open file handle to write to
            block_name: Name of the block
            block_data: Dictionary containing block parameters and values
        """

        # Don't write empty blocks
        if not block_data:
            return

        # Write block header
        file_handle.write(f"[{block_name}]\n")

        # Write block parameters
        for param, values in block_data.items():
            write_vals = [str(v) for v in values] if isinstance(values, list) else [str(values)]
            write_vals = [v if " " not in v else f'"{v}"' for v in write_vals]
            value_str = " ".join(" ".join(str(v2) for v2 in v) if isinstance(v, list) else str(v) for v in write_vals)
            file_handle.write(f"  {self.base_parameter_name(block_name, param)} {value_str}\n")
        file_handle.write("\n")


def validate_input(input_file: Union[str, Path]) -> bool:
    """
    Convenience function to validate a VERAIn input file.

    Args:
        input_file: Path to input file

    Returns:
        True if validation passed, False otherwise
    """
    parser = InputParser()
    try:
        blocks = parser.parse_file(input_file)
        return parser.validate_input(blocks)
    # pylint: disable=broad-exception-caught
    except Exception:
        return False


def parse_input(input_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Convenience function to parse a VERAIn input file.

    Args:
        input_file: Path to input file

    Returns:
        Dictionary containing parsed input data
    """
    parser = InputParser()
    return parser.parse_file(input_file)
