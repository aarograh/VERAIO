"""
Tests for XMLGenerator against all test/*.inp and test/*.xml.gold file pairs.

Each .inp file with a matching .xml.gold file becomes a parametrized test case.
New test files added to test/ are automatically discovered.
"""

import os
import glob

import pytest

from verain import InputParser, XMLGenerator

# Discover all .inp files that have a corresponding .xml.gold file,
# excluding tests that require vera2omn post-processing (.omn.gold present).
_TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "regression_tests")
_GOLD_FILES = sorted(glob.glob(os.path.join(_TEST_DIR, "*.xml.gold")))
_TEST_CASES = []
for _gold in _GOLD_FILES:
    _name = os.path.basename(_gold).replace(".xml.gold", "")
    _inp = os.path.join(_TEST_DIR, f"{_name}.inp")
    _omn_gold = _gold.replace(".xml.gold", ".omn.gold")
    if os.path.exists(_inp) and not os.path.exists(_omn_gold):
        _TEST_CASES.append((_name, _inp, _gold))


@pytest.mark.parametrize("name, inp_file, gold_file", _TEST_CASES, ids=[t[0] for t in _TEST_CASES])
def test_xml_gold_match(name, inp_file, gold_file, tmp_path):
    """Generated XML must exactly match the corresponding .xml.gold file."""
    parser = InputParser()
    data = parser.parse_file(inp_file)

    gen = XMLGenerator()
    xml = gen.generate(data, xinit=True, line_lengths=parser.line_lengths)

    out_file = tmp_path / f"{name}.xml"
    out_file.write_text(xml, encoding="utf-8")

    gold_text = open(gold_file, "r", encoding="utf-8").read()

    assert xml == gold_text, (
        f"Output differs from gold for {name}.\n"
        f"Generated: {out_file}\n"
        f"Gold:      {gold_file}\n"
        f"Run 'diff {out_file} {gold_file}' for details."
    )
