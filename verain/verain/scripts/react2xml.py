#!/usr/bin/env python3
"""react2xml - Convert VERA ASCII input files to XML format."""

import argparse
import os
import sys
import json

import yaml

from verain.parser.parser import InputParser
from verain.xml.xml_generator import XMLGenerator
from verain.init.vera2omn import VERAOmnibusGenerator

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_DATE = 20260430


def _build_parser():
    """Build the argument parser for react2xml."""
    parser = argparse.ArgumentParser(
        prog="react2xml",
        description="Convert VERA reactor input file to XML format.",
        usage="%(prog)s [options ...] reactor_input_file [output_xml_file]",
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="VERA reactor input file (.inp)",
    )
    parser.add_argument(
        "output_file",
        type=str,
        nargs="?",
        default=None,
        help="Output XML file (default: input filename with .xml extension)",
    )
    parser.add_argument(
        "--xml",
        type=str,
        default="on",
        metavar="(on|off)",
        help="Write XML declaration header (default: on)",
    )
    parser.add_argument(
        "--xslt",
        type=str,
        default="on",
        metavar="(on|off|filename)",
        help="Write XSLT processing instruction (default: on, uses PL9.xsl)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print processing information to stderr",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Create debug output files",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Write the VERAIn input schematic to stdout as JSON",
    )
    init_group = parser.add_mutually_exclusive_group()
    init_group.add_argument(
        "--init",
        action="store_true",
        help="Use initialization files (default behaviour)",
    )
    init_group.add_argument(
        "--xinit",
        "--xInit",
        action="store_true",
        help="Skip loading Init/*.ini default initialization files",
    )
    parser.add_argument(
        "--python_exe",
        default="python",
        metavar="PATH",
        help="Python executable path (unused, kept for backward compatibility)",
    )
    return parser


def _stringify_scalars(data):
    """Convert non-string scalar YAML values to strings in-place.

    This function walks a nested dict/list structure and converts int and bool
    leaves to the string representation that is expected by downstream consumption
    for NEAMS Workbench integration (e.g. ``False`` → ``"no"``).  This particular
    mapping has its roots in the old Perl processor.
    """
    _BOOL_MAP = {True: "yes", False: "no"}

    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, bool):
                data[key] = _BOOL_MAP[val]
            elif isinstance(val, int):
                data[key] = str(val)
            elif isinstance(val, (dict, list)):
                _stringify_scalars(val)
    elif isinstance(data, list):
        for i, val in enumerate(data):
            if isinstance(val, bool):
                data[i] = _BOOL_MAP[val]
            elif isinstance(val, int):
                data[i] = str(val)
            elif isinstance(val, (dict, list)):
                _stringify_scalars(val)


def main(argv=None):
    """Entry point for the react2xml console script."""
    # Handle --version and --schema before argparse to avoid required-arg errors
    raw = argv if argv is not None else sys.argv[1:]
    if "--version" in raw:
        print(f"major {VERSION_MAJOR}\nminor {VERSION_MINOR}\ndate  {VERSION_DATE}", file=sys.stderr)
        return 0
    if "--schema" in raw:
        gen = XMLGenerator()
        directory_yml = os.path.join(gen.template_dir, "Directory.yml")
        with open(directory_yml, "r", encoding="utf-8") as f:
            directory_data = yaml.safe_load(f.read())
        _stringify_scalars(directory_data)
        blocks = {}
        for name in gen.TEMPLATE_ORDER:
            tmpl = gen.templates.get(name, {})
            if name in tmpl:
                blocks[name] = tmpl[name]
            else:
                blocks.update(tmpl)
        schema = {"_directory.yml": directory_data, "_blocks": blocks}
        print(json.dumps(schema, indent=2))
        return 0

    parser = _build_parser()
    args = parser.parse_args(argv)

    # Validate input file
    input_file = args.input_file
    if not os.path.isfile(input_file):
        print(f"react2xml: input file {input_file} does not exist or is not readable.", file=sys.stderr)
        return 1

    # Derive output file if not provided
    output_file = args.output_file
    if output_file is None:
        base, _ = os.path.splitext(input_file)
        output_file = base + ".xml"

    # Check input != output
    if os.path.abspath(input_file) == os.path.abspath(output_file):
        print(f"react2xml: files {input_file} and {output_file} are the same.", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Reading {input_file} ...", file=sys.stderr)

    # Parse
    inp = InputParser()
    parsed_data = inp.parse_file(input_file)
    line_lengths = inp.line_lengths

    if args.verbose:
        print(f"File {input_file} read.\n", file=sys.stderr)

    if args.debug:
        debug_file = input_file + ".dbg.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, default=str)
        if args.verbose:
            print(f"Debug data written to {debug_file}", file=sys.stderr)

    # Generate XML
    gen = XMLGenerator()
    xinit = bool(args.xinit)

    xml = gen.generate(parsed_data, xinit=xinit, line_lengths=line_lengths)

    # The generator always includes XML + XSLT headers.
    # Apply --xml / --xslt overrides by stripping and re-adding as needed.
    # Strip existing headers so we can re-add based on flags
    lines = xml.split("\n")
    body_lines = []
    for line in lines:
        if line.startswith("<?xml ") or line.startswith("<?xml-stylesheet"):
            continue
        body_lines.append(line)

    # Determine XSLT filename
    xslt_file = "PL9.xsl"
    if args.xslt not in ("on", "off"):
        xslt_file = args.xslt

    header_lines = []
    # Print XML header unless both XML and XSLT are off
    if not (args.xml == "off" and args.xslt == "off"):
        header_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    if args.xslt != "off":
        header_lines.append(f'<?xml-stylesheet version="1.0" type="text/xsl" href="{xslt_file}"?>')

    xml = "\n".join(header_lines + body_lines)

    # Write output
    if args.verbose:
        print(f"Writing {output_file} ...", file=sys.stderr)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(xml)

    # Run vera2omn post-processing (unconditionally after XML write).
    # vera2omn.load() returns False if the XML lacks bioshield/vessel/SHIFT data,
    # in which case no modifications are made to the output file.
    output_base, _ = os.path.splitext(output_file)
    # vera2omn expects script_dir such that script_dir + "Init/" contains templates.
    # In the installed package, templates live in verain/init/ (one level up from
    # verain/scripts/), so script_dir must be the verain/ package root with the
    # path separator appended.
    script_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..")) + os.sep
    vera2omn_gen = VERAOmnibusGenerator(output_base, script_dir)
    if vera2omn_gen.load():
        if args.verbose:
            print("Writing Omnibus excore input file", file=sys.stderr)
        vera2omn_gen.write()
        vera2omn_gen.update_vera_xml()

    if args.verbose:
        print(f"Output written to {output_file}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
