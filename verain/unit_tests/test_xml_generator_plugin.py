"""XMLGenerator exercising plugin templates and emit_order (spec/24 Phases 2-3)."""

import glob
import os

import pytest

from verain.parser import InputParser
from verain.plugins import PluginError
from verain.xml.xml_generator import XMLGenerator

_EXAMPLE_PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "verain-plugin-example", "verain_plugin_example")
_EXAMPLE_DECK = os.path.join(
    os.path.dirname(__file__), "..", "..", "verain-plugin-example", "tests", "decks", "thermophys.inp"
)


def _has_example_plugin():
    print(_EXAMPLE_PLUGIN_ROOT, os.path.isdir(_EXAMPLE_PLUGIN_ROOT))
    return os.path.isdir(_EXAMPLE_PLUGIN_ROOT)


requires_example_plugin = pytest.mark.skipif(
    not _has_example_plugin(), reason="verain-plugin-example prototype not present next to this checkout"
)


@pytest.fixture
def example_plugin(monkeypatch, reset_directory_cache):
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", _EXAMPLE_PLUGIN_ROOT)


@requires_example_plugin
def test_new_block_emits_in_requested_slot(example_plugin):
    parser = InputParser()
    parsed = parser.parse_file(_EXAMPLE_DECK)
    gen = XMLGenerator()
    xml = gen.generate(parsed, xinit=True, line_lengths=parser.line_lengths)
    assert '<ParameterList name="THERMOPHYSICS">' in xml
    # THERMOPHYSICS must land after MPACT in TEMPLATE_ORDER, per emit_order.
    order = gen.TEMPLATE_ORDER
    assert order.index("THERMOPHYSICS") == order.index("MPACT") + 1


@requires_example_plugin
def test_core_extension_keyword_emits_inside_core_list(example_plugin):
    parser = InputParser()
    parsed = parser.parse_file(_EXAMPLE_DECK)
    print(parsed)
    gen = XMLGenerator()
    xml = gen.generate(parsed, xinit=True, line_lengths=parser.line_lengths)
    print(xml)
    core_start = xml.index('<ParameterList name="CORE">')
    core_end = xml.index("</ParameterList>", core_start)
    core_body = xml[core_start:core_end]
    assert '<Parameter name="gas_gap_model" type="string" value="dynamic"/>' in core_body
    assert '<Parameter name="bypass_fraction" type="double" value="0.0875"/>' in core_body


@requires_example_plugin
def test_core_only_deck_byte_identical_with_plugin_installed(example_plugin):
    """The hard constraint from spec/24 S1: a core-only deck must not change."""
    verain_root = os.path.join(os.path.dirname(__file__), "..")
    golds = sorted(glob.glob(os.path.join(verain_root, "regression_tests", "*.xml.gold")))
    assert golds, "no regression gold files found"
    checked = 0
    for gold in golds[:10]:
        name = gold[: -len(".xml.gold")]
        inp = name + ".inp"
        if not os.path.exists(inp):
            continue
        omn_gold = gold.replace(".xml.gold", ".omn.gold")
        xinit = not os.path.exists(omn_gold)
        parser = InputParser()
        parsed = parser.parse_file(inp)
        gen = XMLGenerator()
        xml = gen.generate(parsed, xinit=xinit, line_lengths=parser.line_lengths)
        with open(gold, "r", encoding="utf-8") as f:
            gold_text = f.read()
        assert xml.rstrip("\n") == gold_text.rstrip("\n"), f"{name} changed with plugin installed"
        checked += 1
    assert checked > 0


@requires_example_plugin
def test_schema_includes_new_block_only_when_plugins_enabled(example_plugin):
    gen_on = XMLGenerator(plugins_enabled=True)
    gen_off = XMLGenerator(plugins_enabled=False)
    assert "THERMOPHYSICS" in gen_on.templates
    assert "THERMOPHYSICS" not in gen_off.templates


def test_plugin_template_may_not_replace_core_block(tmp_path, monkeypatch):
    root = tmp_path / "plug"
    templates_dir = root / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "CORE.yml").write_text(
        "CORE:\n  _pltype: list\n  _content:\n    foo:\n      _pltype: parameter\n      _type: string\n",
        encoding="utf-8",
    )
    (root / "verain_plugin.yml").write_text(
        """
plugin:
  name: replaces-core
  version: 0.1.0
  api_version: 1
templates:
  - templates/CORE.yml
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    with pytest.raises(PluginError, match="may not replace it"):
        XMLGenerator(plugins_enabled=True)


def test_emit_order_unknown_target_raises(tmp_path, monkeypatch):
    root = tmp_path / "plug"
    templates_dir = root / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "NEWBLOCK.yml").write_text(
        "NEWBLOCK:\n  _pltype: list\n  _content:\n"
        "    foo:\n      _pltype: parameter\n      _type: string\n      _do:\n"
        "        - copy NEWBLOCK/$foo\n      _content:\n",
        encoding="utf-8",
    )
    (root / "verain_plugin.yml").write_text(
        """
plugin:
  name: bad-emit-order
  version: 0.1.0
  api_version: 1
templates:
  - templates/NEWBLOCK.yml
emit_order:
  NEWBLOCK: {after: NOSUCHBLOCK}
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    with pytest.raises(PluginError, match="unknown block 'NOSUCHBLOCK'"):
        XMLGenerator(plugins_enabled=True)


# --- Extending a repeatable block's per-instance template content ---
#
# STATE/ASSEMBLY/CONTROL/INSERT/DETECTOR/BRANCH are each emitted from a
# template whose top-level key is the *plural* form (ASSEMBLIES.yml, not
# ASSEMBLY.yml) with the per-instance content one level deeper, inside a
# single nested list keyed e.g. Assembly_(_loop). A plugin reaches that
# nested list by writing the same shape back: a template child whose name
# matches the core one exactly, itself `_pltype: list`, so the merge
# recurses into its own `_content` instead of treating the name collision
# as an error. See PLUGINS.md for the full per-block key-name table.

_ASSEMBLY_GRAMMAR_EXTEND = """
ASSEMBLY:
  _extends: true
  grid_loss_mult:
    _datatype: dtdouble
    _check:
      - is_float()
"""

_ASSEMBLY_TEMPLATE_EXTEND = """
ASSEMBLIES:
  _extends: true
  _content:
    Assembly_(_loop):
      _pltype: list
      _content:
        grid_loss_mult:
          _pltype: parameter
          _type: double
          _do:
            - copy %ASSEMBLY/$(_path)/$grid_loss_mult
          _content:
"""

_ASSEMBLY_DECK = """[CASEID]
  title 'nested template merge test'

[STATE]
  power    0.0
  tinlet   565 K
  tfuel    565 K
  modden   0.743
  boron    1300
  sym      full
  feedback off

[CORE]
  size   1
  apitch 1.26
  rated  0.01 0.01
  height 1.0
  core_shape
    1
  assm_map
    ASSY1
  bc_rad reflecting
  bc_top reflecting
  bc_bot reflecting

[ASSEMBLY]
  title "pin cell"
  npin 1
  ppitch 1.26
  grid_loss_mult 1.15
  fuel U31 10.257 94.5 / 3.1
  cell PIN1 0.4096 0.418 0.475 / U31 he zirc4
  lattice LAT1
     PIN1
  axial ASSY1 0.0 LAT1 1.0

[MPACT]
  res_up_scatter false
"""


def _write_assembly_extend_plugin(root, template_text=_ASSEMBLY_TEMPLATE_EXTEND):
    grammar_dir = root / "grammar"
    templates_dir = root / "templates"
    grammar_dir.mkdir(parents=True)
    templates_dir.mkdir(parents=True)
    (grammar_dir / "ASSEMBLY.extend.yml").write_text(_ASSEMBLY_GRAMMAR_EXTEND, encoding="utf-8")
    (templates_dir / "ASSEMBLY.extend.yml").write_text(template_text, encoding="utf-8")
    (root / "verain_plugin.yml").write_text(
        """
plugin:
  name: assembly-extend
  version: 0.1.0
  api_version: 1
grammar:
  - grammar/ASSEMBLY.extend.yml
templates:
  - templates/ASSEMBLY.extend.yml
""",
        encoding="utf-8",
    )


def test_repeatable_block_keyword_reaches_per_instance_xml(tmp_path, monkeypatch, reset_directory_cache):
    root = tmp_path / "plug"
    _write_assembly_extend_plugin(root)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))

    deck = tmp_path / "deck.inp"
    deck.write_text(_ASSEMBLY_DECK, encoding="utf-8")
    parser = InputParser()
    parsed = parser.parse_file(deck)
    gen = XMLGenerator()
    xml = gen.generate(parsed, xinit=True, line_lengths=parser.line_lengths)

    assert '<ParameterList name="Assembly_ASSY1">' in xml
    assert '<Parameter name="grid_loss_mult" type="double" value="1.15"/>' in xml
    # And it landed inside the assembly's own list, not the root CASEID list:
    # the emitter sorts each list's children alphabetically, and grid_loss_mult
    # only exists as a per-assembly keyword, so its line has to be indented
    # deeper than a direct CASEID child (2 spaces) would be.
    line = next(line for line in xml.splitlines() if "grid_loss_mult" in line)
    assert line.startswith(" " * 6)


def test_repeatable_block_leaf_collision_still_raises(tmp_path, monkeypatch, reset_directory_cache):
    """A plugin can merge into the nested per-instance list, but not replace
    or collide with a keyword that's already there."""
    colliding_template = """
ASSEMBLIES:
  _extends: true
  _content:
    Assembly_(_loop):
      _pltype: list
      _content:
        label:
          _pltype: parameter
          _type: string
          _do:
            - copy %ASSEMBLY/$(_path)/$grid_loss_mult
          _content:
"""
    root = tmp_path / "plug"
    _write_assembly_extend_plugin(root, template_text=colliding_template)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    with pytest.raises(PluginError, match=r"Assembly_\(_loop\)\.label.*collides"):
        XMLGenerator(plugins_enabled=True)


def test_repeatable_block_wrapper_replace_still_raises(tmp_path, monkeypatch, reset_directory_cache):
    """A plugin cannot swap the per-instance node out for something that
    isn't itself a `_pltype: list` container -- that's a replace, not a merge."""
    replace_template = """
ASSEMBLIES:
  _extends: true
  _content:
    Assembly_(_loop):
      _pltype: parameter
      _type: string
"""
    root = tmp_path / "plug"
    _write_assembly_extend_plugin(root, template_text=replace_template)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    with pytest.raises(PluginError, match=r"Assembly_\(_loop\).*collides"):
        XMLGenerator(plugins_enabled=True)
