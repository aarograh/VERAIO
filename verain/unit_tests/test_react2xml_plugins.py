"""react2xml CLI and defaults-loading tests for the plugin framework (spec/24 Phase 4)."""

import json

import pytest

from verain.parser import InputParser
from verain.plugins import PluginError
from verain.scripts.react2xml import main as react2xml_main
from verain.xml.xml_generator import XMLGenerator


def _write_thermo_plugin(tmp_path, with_default=True):
    root = tmp_path / "plug"
    (root / "grammar").mkdir(parents=True)
    (root / "grammar" / "THERMOPHYSICS.yml").write_text(
        """
THERMOPHYSICS:
  _datatype: dtblock
  model:
    _datatype: dtword
  n_radial:
    _datatype: dtint
""",
        encoding="utf-8",
    )
    (root / "templates").mkdir(parents=True)
    (root / "templates" / "THERMOPHYSICS.yml").write_text(
        """
THERMOPHYSICS:
  _pltype: list
  _do:
    - setdb MAIN_DB
  _content:
    model:
      _pltype: parameter
      _type: string
      _do:
        - copy THERMOPHYSICS/$model
      _content:
    n_radial:
      _pltype: parameter
      _type: int
      _do:
        - copy THERMOPHYSICS/$n_radial
      _content:
""",
        encoding="utf-8",
    )
    manifest = """
plugin:
  name: thermo
  version: 0.1.0
  api_version: 1
grammar:
  - grammar/THERMOPHYSICS.yml
templates:
  - templates/THERMOPHYSICS.yml
emit_order:
  THERMOPHYSICS: {after: MPACT}
"""
    if with_default:
        (root / "defaults").mkdir(parents=True)
        (root / "defaults" / "THERMOPHYSICS.ini").write_text("model fixed\n", encoding="utf-8")
        manifest += "defaults:\n  - defaults/THERMOPHYSICS.ini\n"
    (root / "verain_plugin.yml").write_text(manifest, encoding="utf-8")
    return root


@pytest.fixture
def thermo_plugin(tmp_path, monkeypatch, reset_directory_cache):
    root = _write_thermo_plugin(tmp_path)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    return root


def _deck_with_thermophysics(tmp_path):
    deck = tmp_path / "deck.inp"
    deck.write_text("[CASEID]\n  title 'plugin defaults test'\n\n[THERMOPHYSICS]\n  n_radial 5\n", encoding="utf-8")
    return deck


def test_plugin_default_applies_when_xinit_absent(thermo_plugin, tmp_path):
    deck = _deck_with_thermophysics(tmp_path)
    parser = InputParser()
    parsed = parser.parse_file(deck)
    gen = XMLGenerator()
    xml = gen.generate(parsed, xinit=False, line_lengths=parser.line_lengths)
    assert '<Parameter name="model" type="string" value="fixed"/>' in xml


def test_plugin_default_absent_when_xinit_present(thermo_plugin, tmp_path):
    deck = _deck_with_thermophysics(tmp_path)
    parser = InputParser()
    parsed = parser.parse_file(deck)
    gen = XMLGenerator()
    xml = gen.generate(parsed, xinit=True, line_lengths=parser.line_lengths)
    assert '<Parameter name="model"' not in xml


def test_plugin_default_for_core_block_raises(tmp_path, monkeypatch, reset_directory_cache):
    root = tmp_path / "plug"
    (root / "defaults").mkdir(parents=True)
    (root / "defaults" / "CORE.ini").write_text("size 1\n", encoding="utf-8")
    (root / "verain_plugin.yml").write_text(
        """
plugin:
  name: bad-defaults
  version: 0.1.0
  api_version: 1
defaults:
  - defaults/CORE.ini
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    deck = tmp_path / "deck.inp"
    deck.write_text("[CASEID]\n  title 'plugin defaults test'\n", encoding="utf-8")
    parser = InputParser()
    parsed = parser.parse_file(deck)
    gen = XMLGenerator()
    with pytest.raises(PluginError, match="core block"):
        gen.generate(parsed, xinit=False, line_lengths=parser.line_lengths)


def test_no_plugins_cli_flag_makes_plugin_block_unrecognized(thermo_plugin, tmp_path):
    """--no-plugins really disables the plugin: its block is then unrecognized,
    which is a hard parse-time error (an unrecognized block name is never
    silently accepted), not a silently-empty block."""
    deck = _deck_with_thermophysics(tmp_path)
    out = tmp_path / "out.xml"
    with pytest.raises(KeyError, match="THERMOPHYSICS"):
        react2xml_main(["--xinit", "--no-plugins", str(deck), str(out)])


def test_plugins_flag_lists_discovered_plugin(thermo_plugin, capsys):
    rc = react2xml_main(["--plugins"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "thermo" in out
    assert "block THERMOPHYSICS" in out


def test_plugins_flag_reports_none_when_disabled(monkeypatch):
    monkeypatch.delenv("VERAIN_PLUGIN_PATH", raising=False)
    rc = react2xml_main(["--plugins"])
    assert rc == 0


def test_schema_no_plugins_matches_baseline_without_plugin(tmp_path, monkeypatch, capsys):
    """The hard constraint: --schema --no-plugins never churns when a plugin is installed.

    Compared against a live baseline generated with no plugin discoverable at
    all, rather than against ``schema.json.gold`` -- that file can go stale
    independent of this framework (see ``test_react2xml.py::test_schema_matches_gold``),
    and this property must hold regardless of whether the gold file is fresh.
    """
    monkeypatch.delenv("VERAIN_PLUGIN_PATH", raising=False)
    rc = react2xml_main(["--schema", "--no-plugins"])
    assert rc == 0
    baseline = capsys.readouterr().out

    root = _write_thermo_plugin(tmp_path)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    rc = react2xml_main(["--schema", "--no-plugins"])
    assert rc == 0
    with_plugin_installed = capsys.readouterr().out

    assert with_plugin_installed == baseline


def test_schema_with_plugins_includes_new_block(thermo_plugin, capsys):
    rc = react2xml_main(["--schema"])
    assert rc == 0
    generated = json.loads(capsys.readouterr().out)
    assert "THERMOPHYSICS" in generated["_blocks"]
    assert "THERMOPHYSICS" in generated["_directory.yml"]["_DIRECTORY"]


def test_write_verain_file_round_trips_plugin_block(thermo_plugin, tmp_path):
    deck = _deck_with_thermophysics(tmp_path)
    parser = InputParser()
    parsed = parser.parse_file(deck)
    out = tmp_path / "roundtrip.inp"
    parser.write_verain_file(out, parsed)

    reparsed_parser = InputParser()
    reparsed = reparsed_parser.parse_file(out)
    assert reparsed["THERMOPHYSICS"]["n_radial"] == ["5"]
