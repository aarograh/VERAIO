# VERAIn Installation and Usage Guide

This document provides instructions for installing and using VERAIn as a pip package while maintaining compatibility with existing CMake builds.

## Installation Options

### Option 1: Pip Installation (Recommended for Python Development)

```bash
# Install from PyPI (once published)
pip install verain

# Or install from source in development mode
cd /path/to/verain
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

### Option 2: CMake Installation (Full VERA Integration)

```bash
# Standard CMake build (preserves all existing functionality)
mkdir build
cd build
cmake ..
make
make install
```

### Option 3: Dual Installation

You can use both installation methods simultaneously:

```bash
# Build and install via CMake for VERA integration
cmake -S . -B build
cmake --build build
cmake --install build

# Also install Python package for development
pip install -e .
```

## Usage Examples

### Command Line Usage

After pip installation, you can use the command-line tools:

```bash
# Convert VERA input to XML
react2xml input_file.inp output_file.xml

# Process Directory.yml specifications
react2xml --directory-only Templates/Directory.yml

# Convert VERA to Omnibus format
vera2omn input.inp output.omn
```

### Python API Usage

```python
from verain import DirectoryProcessor, ValidationEngine, InputParser, XmlGenerator

# Process hierarchical YAML specifications
processor = DirectoryProcessor("Templates/Directory.yml")
if processor.load_yaml():
    data = processor.process_all_blocks()
    print(f"Processed {data['block_count']} blocks")

# Validate input parameters
engine = ValidationEngine()
errors = engine.validate_parameter("temp", ["300.0"], ["is_float()", "is_gt(0.0)"])

# Parse VERA input files
parser = InputParser()
input_data = parser.parse_file("example.inp")

# Generate XML output
generator = XmlGenerator()
xml_root = generator.create_xml_from_data(input_data)
generator.write_xml("output.xml")
```

### Advanced Usage

```python
# Search for parameters
processor = DirectoryProcessor("Templates/Directory.yml")
processor.load_yaml()
processor.process_all_blocks()

temp_params = processor.search_parameters("temperature")
for block_name, params in temp_params.items():
    print(f"{block_name}: {', '.join(params)}")

# Export processed data
processor.export_to_json("processed_data.json")

# Validate XML structure
generator = XmlGenerator()
# ... create XML ...
issues = generator.validate_xml_structure()
for issue in issues:
    print(f"Warning: {issue}")
```

## Development Setup

For development work on VERAIn:

```bash
# Clone repository
git clone <repository-url>
cd verain

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black verain/
isort verain/

# Type checking
mypy verain/
```

## Integration with Existing Workflows

### CMake Projects

VERAIn maintains full compatibility with existing CMake-based VERA builds:

- All original Perl scripts remain functional
- Python scripts are installed alongside Perl scripts
- All template files and documentation are preserved
- Test suites continue to work unchanged

### Python Projects

The package can be imported and used in Python projects:

```python
# requirements.txt
verain>=1.0.0

# main.py
from verain import DirectoryProcessor
processor = DirectoryProcessor("config.yml")
data = processor.process_all_blocks()
```

## File Organization

The package maintains the original directory structure while adding Python package organization:

```
verain/
├── CMakeLists.txt              # Original CMake configuration
├── pyproject.toml              # Python package configuration
├── setup.py                    # Backward compatibility
├── README.md                   # Package documentation
├── requirements-dev.txt        # Development dependencies
├── scripts/                    # Original scripts (preserved)
│   ├── react2xml.pl           # Original Perl script
│   ├── react2xml.py           # Enhanced Python script
│   └── Templates/             # YAML templates
├── verain/                     # Python package
│   ├── __init__.py            # Package entry point
│   ├── core/                  # Core functionality
│   ├── utils/                 # Utilities
│   ├── scripts/               # Command-line tools
│   └── templates/             # Template files (copied)
├── tests/                      # Python tests
├── src/                        # Fortran sources (preserved)
├── test/                       # CMake tests (preserved)
└── docs/                       # Documentation
```

## Compatibility Notes

### Python Version Support

- Minimum Python version: 3.7
- Tested with Python 3.7-3.12
- Uses type hints compatible with Python 3.7+

### Dependencies

- Required: PyYAML >= 5.1
- Optional: pytest, black, mypy (development)
- No conflicting dependencies with VERA build system

### Backward Compatibility

- All original scripts remain functional
- CMake build system unchanged
- No impact on existing VERA installations
- Original command-line interfaces preserved

## Troubleshooting

### Import Errors

```python
# If you get import errors, ensure the package is installed:
pip list | grep verain

# Or install in development mode:
pip install -e .
```

### Template File Issues

```python
# Templates are included in the package, but you can also point to originals:
processor = DirectoryProcessor("/path/to/original/Templates/Directory.yml")
```

### CMake vs Pip Conflicts

The two installation methods are designed to coexist:
- CMake installs to system directories
- Pip installs to Python environment
- Both can be used simultaneously
- Use `which react2xml` to see which version is in PATH

## Support

For issues and questions:
- Package issues: [Bug Tracker](https://code.ornl.gov/vera/verain/issues)
- VERA integration: [VERA Documentation](https://vera.ornl.gov)
- Python API: See docstrings and examples in the code
