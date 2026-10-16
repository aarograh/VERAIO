"""
Tests for react2xml CLI against all test/*.inp and test/*.xml.gold file pairs.

Mirrors test_xml_generator.py but exercises the full react2xml.main() path
(argument parsing, file I/O, header handling) instead of calling
XMLGenerator.generate() directly.
"""

import os
import glob
import json

import pytest

from verain.scripts.react2xml import main as react2xml_main

# Discover all .inp files that have a corresponding .xml.gold file
_TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "regression_tests")
_GOLD_FILES = sorted(glob.glob(os.path.join(_TEST_DIR, "*.xml.gold")))
_TEST_CASES = []
for _gold in _GOLD_FILES:
    _name = os.path.basename(_gold).replace(".xml.gold", "")
    _inp = os.path.join(_TEST_DIR, f"{_name}.inp")
    if os.path.exists(_inp):
        _TEST_CASES.append((_name, _inp, _gold))


@pytest.mark.parametrize("name, inp_file, gold_file", _TEST_CASES, ids=[t[0] for t in _TEST_CASES])
def test_react2xml_gold_match(name, inp_file, gold_file, tmp_path):
    """react2xml CLI output must exactly match the corresponding .xml.gold file."""
    # Tests with a matching .omn.gold file run without --xinit
    omn_gold = gold_file.replace(".xml.gold", ".omn.gold")
    xinit = not os.path.exists(omn_gold)

    out_file = str(tmp_path / f"{name}.xml")

    argv = [inp_file, out_file]
    if xinit:
        argv.insert(0, "--xinit")

    rc = react2xml_main(argv)
    assert rc == 0, f"react2xml returned non-zero exit code {rc} for {name}"

    assert os.path.isfile(out_file), f"Output file {out_file} was not created"

    generated = open(out_file, "r", encoding="utf-8").read()
    gold_text = open(gold_file, "r", encoding="utf-8").read()

    assert generated == gold_text, (
        f"Output differs from gold for {name}.\n"
        f"Generated: {out_file}\n"
        f"Gold:      {gold_file}\n"
        f"Run 'diff {out_file} {gold_file}' for details."
    )


_SCHEMA_GOLD = os.path.join(os.path.dirname(__file__), "schema.json.gold")


def test_schema_matches_gold(capsys):
    """--schema --no-plugins must match schema.json.gold (order-independent).

    --no-plugins matters: schema.json.gold is core's own baseline schema, and
    a real plugin may legitimately be entry-point installed in this
    environment for someone to use `react2xml` directly with (verain-mongoose,
    for one) -- this test should verify core hasn't drifted regardless of
    that, not fail because something else is installed. See spec/24 S3.9:
    "--schema --no-plugins emits core only... the gold file never churns
    when a plugin is installed."
    """
    rc = react2xml_main(["--schema", "--no-plugins"])
    assert rc == 0
    captured = capsys.readouterr()
    generated = json.loads(captured.out)
    with open(_SCHEMA_GOLD, "r", encoding="utf-8") as f:
        gold = json.load(f)
    assert generated == gold
