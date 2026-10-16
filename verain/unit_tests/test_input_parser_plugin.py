"""InputParser exercising a merged plugin grammar (spec/24 Phase 1)."""

from pathlib import Path

import pytest

from verain.parser import InputParser


def _write_plugin(tmp_path):
    root = tmp_path / "plug"
    grammar_dir = root / "grammar"
    grammar_dir.mkdir(parents=True)
    (grammar_dir / "CORE.extend.yml").write_text(
        """
CORE:
  _extends: true
  gas_gap_model:
    _datatype: dtword
    _check:
      - in_dictionary() fixed dynamic
""",
        encoding="utf-8",
    )
    (root / "verain_plugin.yml").write_text(
        """
plugin:
  name: plug
  version: 0.1.0
  api_version: 1
grammar:
  - grammar/CORE.extend.yml
""",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def plugin_root(tmp_path, monkeypatch, reset_directory_cache):
    root = _write_plugin(tmp_path)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(root))
    return root


def _write_deck(tmp_path, extra_core_line=""):
    deck = tmp_path / "deck.inp"
    deck.write_text(
        f"""
[CASEID]
  title 'plugin test'

[CORE]
  size 1
  apitch 1.26
  rated 0.01 0.01
  height 1.0
  core_shape
    1
  assm_map
    ASSY1
  bc_rad reflecting
  bc_top reflecting
  bc_bot reflecting
  {extra_core_line}

[ASSEMBLY]
  npin 1
  ppitch 1.26
  fuel U31 10.257 94.5 / 3.1
  cell PIN1 0.4096 0.418 0.475 / U31 he zirc4
  lattice LAT1
    PIN1
  axial ASSY1 0.0 LAT1 1.0
""",
        encoding="utf-8",
    )
    return deck


def test_plugin_keyword_parses_into_core_block(plugin_root, tmp_path):
    deck = _write_deck(tmp_path, extra_core_line="gas_gap_model dynamic")
    parser = InputParser()
    blocks = parser.parse_file(deck)
    assert blocks["CORE"]["gas_gap_model"] == ["dynamic"]


def test_plugin_check_failure_reported_by_validate_input(plugin_root, tmp_path):
    deck = _write_deck(tmp_path, extra_core_line="gas_gap_model annular")
    parser = InputParser()
    blocks = parser.parse_file(deck)
    ok = parser.validate_input(blocks)
    assert not ok
    assert any("gas_gap_model" in e for e in parser.get_validation_errors())


def test_plugins_disabled_makes_keyword_unknown(plugin_root, tmp_path):
    deck = _write_deck(tmp_path, extra_core_line="gas_gap_model dynamic")
    parser = InputParser(plugins_enabled=False)
    blocks = parser.parse_file(deck)
    # Unrecognized tokens are simply skipped by the tokenizer (never stored),
    # exactly as any other unknown keyword would be with no plugin installed.
    assert "gas_gap_model" not in blocks["CORE"]


def test_env_var_off_makes_keyword_unknown(plugin_root, tmp_path, monkeypatch):
    monkeypatch.setenv("VERAIN_PLUGINS", "off")
    deck = _write_deck(tmp_path, extra_core_line="gas_gap_model dynamic")
    parser = InputParser()
    blocks = parser.parse_file(deck)
    assert "gas_gap_model" not in blocks["CORE"]
