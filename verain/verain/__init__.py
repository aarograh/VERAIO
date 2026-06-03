"""
VERAIn - VERA Input Parser

A comprehensive toolkit for processing VERA (Virtual Environment for Reactor
Applications) input files and validating hierarchical input specifications.

This package provides:
- Input file parsing and validation
- Hierarchical YAML-based configuration processing
- Command-line tools for batch processing
- Python API for programmatic access

Main Classes:
    DirectoryProcessor: Process hierarchical YAML input specifications
    ValidationEngine: Validate input parameters against rules
    InputParser: Parse VERA ASCII input files

Main Functions:
    process_directory: Process Directory.yml specifications
    validate_input: Validate input parameters

Example:
    >>> from verain import DirectoryProcessor
    >>> processor = DirectoryProcessor("Templates/Directory.yml")
    >>> if processor.load_yaml():
    ...     data = processor.process_all_blocks()
    ...     print(f"Processed {data['block_count']} blocks")
"""

__version__ = "1.0.0"
__author__ = "Veracity Nuclear"
__email__ = "vera-support@veracitynuclear.com"
__license__ = "BSD-3-Clause"

# Templates imports
from .templates.directory_processor import DirectoryProcessor, process_directory

# Parser imports
from .parser.validation import ValidationEngine
from .parser.parser import InputParser, validate_input, parse_input

# XML generation imports
from .xml.xml_generator import XMLGenerator

__all__ = [
    # Classes
    "DirectoryProcessor",
    "ValidationEngine",
    "InputParser",
    "XMLGenerator",
    # Functions
    "process_directory",
    "validate_input",
    "parse_input",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]
