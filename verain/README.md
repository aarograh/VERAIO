# VERAIn - VERA Input Parser

[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/verain.svg)](https://badge.fury.io/py/verain)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

VERAIn is a reactor-aware ASCII input parser for VERA (Virtual Environment for Reactor Applications). This package provides tools for converting VERA input files to XML format and processing hierarchical YAML-based input specifications.

## Features

- **Input Processing**: Parse VERA ASCII input files and convert to XML
- **Validation Engine**: Comprehensive validation of input parameters
- **Hierarchical Structure**: Process complex nested input specifications
- **Template System**: Configurable templates for different input blocks
- **Command Line Tools**: Easy-to-use CLI for batch processing
- **Python API**: Programmatic access for integration into other tools

## Installation

### From PyPI (recommended)

```bash
pip install verain
```

### From Source

```bash
git clone <repository-url>
cd verain
pip install -e .
```

### Development Installation

```bash
git clone <repository-url>
cd verain
pip install -e .[dev]
```

## Quick Start

### Command Line Usage

Convert a VERA input file to XML:

```bash
react2xml input_file.inp output_file.xml
```

### Python API Usage

```python
from verain import DirectoryProcessor

# Initialize processor with YAML template
processor = DirectoryProcessor("Templates/Directory.yml")

# Load and process hierarchical data
if processor.load_yaml():
    data = processor.process_all_blocks()

    # Access processed data
    print(f"Found {data['block_count']} input blocks")
    print(f"Total parameters: {data['parameter_count']}")

# Search for specific parameters
temp_params = processor.search_parameters("temperature")
for block_name, params in temp_params.items():
    print(f"{block_name}: {', '.join(params)}")
```

## Input Blocks Supported

VERAIn supports processing of the following VERA input blocks:

- **CASEID**: Case identification and metadata
- **CORE**: Core geometry and configuration
- **STATE**: State point definitions
- **ASSEMBLIES**: Assembly specifications
- **MATERIALS**: Material properties
- **MPACT**: MPACT-specific parameters
- **COBRATF**: COBRA-TF thermal hydraulics parameters
- **SHIFT**: SHIFT Monte Carlo parameters
- **BISON**: BISON fuel performance parameters
- **MAMBA**: MAMBA depletion parameters
- And more...

## Data Types and Validation

The parser supports multiple data types with comprehensive validation:

- **Scalars**: `word`, `string`, `int`, `float`, `double`
- **Arrays**: Multi-dimensional arrays with type checking
- **Validation**: Range checks, format validation, dependency checking
- **Conversion**: Automatic type conversion and unit handling

## Template System

VERAIn uses a flexible YAML-based template system:

```yaml
# Example parameter definition
parameter_name:
  parse: scalar
  type: double
  check:
    - is_float()
    - is_geq(0.0)
  default: 1.0
  description: "Parameter description"
```

## Examples

### Processing Complex Input Files

```python
from verain import ValidationEngine, DirectoryProcessor

# Load configuration
processor = DirectoryProcessor("path/to/Directory.yml")
processor.load_yaml()

# Get specific block parameters
core_params = processor['CORE']
print(f"CORE block has {len(core_params)} parameters")

# Validate input data
validator = ValidationEngine()
is_valid = validator.validate_parameter(
    "temperature", [300.0, 350.0], ["is_float()", "is_gt(273.15)"]
)
```

### Exporting Processed Data

```python
# Export complete processed data
processor.export_to_json("processed_vera_input.json")

# Export specific blocks
subset_data = {
    'core': processor['CORE'],
    'state': processor['STATE']
}
```

## Integration with CMake

VERAIn maintains full compatibility with existing CMake-based build systems. The package can be installed via pip while preserving all CMake installation procedures.

### CMake Integration

The package preserves all existing CMake functionality:

- Fortran source compilation (`src/` directory)
- Test suite execution
- Installation of Perl scripts and templates
- Documentation and example installation

### Dual Installation

You can use both installation methods:

```bash
# Install via pip for Python development
pip install verain

# Or build via CMake for full VERA integration
cmake -S . -B build
cmake --build build
cmake --install build
```

## Development

### Setting Up Development Environment

```bash
git clone <repository-url>
cd verain
pip install -e .[dev]
pre-commit install
```

### Running Tests

```bash
# Run Python tests
pytest

# Run CMake tests (if available)
cd build && ctest
```

### Code Quality

```bash
# Format code
black verain/

# Lint code
pylint verain/

# Type checking
mypy verain/
```

## Documentation

- [User Manual](https://code.ornl.gov/vera/verain_usersmanual)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [Development Guide](docs/development.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the BSD 3-Clause License. See [COPYRIGHT.txt](COPYRIGHT.txt) for details.

## Citation

If you use VERAIn in your research, please cite:

```bibtex
@software{verain,
  title = {VERAIn: VERA Input Parser},
  author = {{VERA Development Team}},
  url = {https://code.ornl.gov/vera/verain},
  year = {2024}
}
```

## Support

- Documentation: [User Manual](https://code.ornl.gov/vera/verain_usersmanual)
- Issues: [Bug Tracker](https://code.ornl.gov/vera/verain/issues)
- Discussions: [VERA Forum](https://vera.ornl.gov/forum)

## Acknowledgments

VERAIn is developed as part of the VERA project, supported by the U.S. Department of Energy.
