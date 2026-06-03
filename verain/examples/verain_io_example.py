#!/usr/bin/env python3
"""
Example script demonstrating VERAIn file reading and writing capabilities.
"""

from pathlib import Path
import sys

# Add the parent directory to Python path to import verain
sys.path.insert(0, str(Path(__file__).parent.parent))

from verain.parser import InputParser


def create_sample_verain_data():
    """Create a sample VERAIn data structure."""
    data = {
        'CASEID': {
            'title': "'Sample 17x17 PWR Core Model'"
        },
        'STATE': {
            'power': '100',
            'sym': 'qtr',
            'feedback': 'off',
            'thexp': 'on',
            'boron': '500',
            'tinlet': '585 K',
            'tfuel': '900 K',
            'modden': '0.701038',
            'deplete': 'GWDMT 0.0 0.1 0.5 1.0 2.0 3.0 5.0 10.0 15.0 20.0'
        },
        'CORE': {
            'size': '17',
            'apitch': '1.26',
            'rated': '2.05062e-2 0.01',
            'height': '1.0',
            'core_shape': [
                '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',
                '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',
                '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',
                '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',
                '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1'
            ],
            'assm_map': [
                'F',
                'F F',
                'F F F'
            ],
            'insert_map': [
                '-',
                '- -',
                '- - -'
            ],
            'bc_rad': 'reflecting',
            'bc_top': 'reflecting',
            'bc_bot': 'reflecting'
        },
        'ASSEMBLY': {
            'npin': '1',
            'ppitch': '1.26',
            'fuel': 'U 10.416 96 / 4.5',
            'cell': '1 0.4096 0.418 0.475 / U he zirc4',
            'lattice': 'FUEL 1',
            'axial': 'F 0.0 FUEL 1.0'
        },
        'MPACT': {
            'nodal_edits': 'nem',
            'ray_spacing': '0.01',
            'num_angle': '-8'
        },
        'RUN': {
            'walltime': '1.0'
        }
    }
    return data


def main():
    """Main example function."""

    # Create a parser instance
    parser = InputParser()

    # Example 1: Create and write a VERAIn file
    print("Creating sample VERAIn data structure...")
    sample_data = create_sample_verain_data()

    output_file = Path("sample_output.inp")
    print(f"Writing VERAIn file to {output_file}...")
    parser.write_verain_file(output_file, sample_data)
    print("VERAIn file written successfully!")

    # Example 2: Read the file back
    print(f"\nReading back the VERAIn file from {output_file}...")
    _ = parser.parse_file(output_file)

    print("\nParsed blocks:")
    for block_name in parser:
        print(f"  [{block_name}]")
        block_data = parser.blocks[block_name]
        for param_name, param_value in block_data.items():
            if isinstance(param_value, list):
                print(f"    {param_name}:")
                for line in param_value:
                    print(f"      {line}")
            else:
                print(f"    {param_name} = {param_value}")

    # Example 3: Access specific parameters
    print(f"\nAccessing specific parameters:")
    print(f"Power level: {parser[('STATE_0001', 'power')]}")
    print(f"Core size: {parser[('CORE', 'size')]}")
    print(f"Title: {parser[('CASEID', 'title')]}")

    # Example 4: Use class method for convenience
    print(f"\nUsing class method to write another file...")
    output_file2 = Path("sample_output2.inp")
    parser.write_verain_file(output_file2, sample_data)
    print(f"Second VERAIn file written to {output_file2}")

    # Clean up example files
    print(f"\nCleaning up example files...")
    if output_file.exists():
        output_file.unlink()
    if output_file2.exists():
        output_file2.unlink()
    print("Example files cleaned up.")


if __name__ == "__main__":
    main()
