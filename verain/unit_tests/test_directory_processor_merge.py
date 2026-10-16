"""Unit tests for DirectoryProcessor's plugin grammar merge."""

from pathlib import Path

import pytest
import yaml

from verain.templates.directory_processor import DirectoryProcessor, PluginMergeError


def _core_processor(tmp_path, core_yaml):
    core_path = tmp_path / "Directory.yml"
    core_path.write_text(core_yaml, encoding="utf-8")
    return DirectoryProcessor(core_path)


CORE_YAML = """
_DATATYPES:
  _dtword: &dtword
    _parse: 'scalar'
    _type: 'word'
  _dtint: &dtint
    _parse: 'scalar'
    _type: 'int'
  _dtblock: &dtblock
    _parse: 'block'
    _named: 0
  _dtblocknamed: &dtblocknamed
    _parse: 'block'
    _named: 1
  _dtlistnamed: &dtlistnamed
    _parse: 'list'
    _named: 1

_DIRECTORY:
  CORE:
  ASSEMBLY:

CORE:
  size:
    <<: *dtint
    _check:
      - is_int()

ASSEMBLY:
  <<: *dtblocknamed
  npin:
    <<: *dtint
"""


def _fragment(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_new_block_appears_in_keys(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "NEW.yml",
        """
THERMOPHYSICS:
  _datatype: dtblock
  model:
    _datatype: dtword
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    assert "THERMOPHYSICS" in processor.keys()
    assert "model" in processor["THERMOPHYSICS"]
    assert processor.source_of("THERMOPHYSICS", "model") == "plug"
    assert "THERMOPHYSICS" in processor.processed_data["metadata"]["directory_structure"]


def test_extension_keyword_appears_in_block(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  gas_gap_model:
    _datatype: dtword
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    assert "gas_gap_model" in processor["CORE"]
    assert processor.source_of("CORE", "gas_gap_model") == "plug"
    assert processor.source_of("CORE", "size") == "base"


def test_datatype_expands_like_merge_key(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  another_int:
    _datatype: dtint
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    plugin_node = processor.processed_data["input_blocks"]["CORE"]["another_int"]
    core_node = processor.processed_data["input_blocks"]["CORE"]["size"]
    assert plugin_node["parse_type"] == core_node["parse_type"] == "scalar"
    assert plugin_node["data_type"] == core_node["data_type"] == "int"


def test_extends_on_nonexistent_block_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
NOTABLOCK:
  _extends: true
  foo:
    _datatype: dtword
""",
    )
    with pytest.raises(PluginMergeError, match="declares _extends: true but no such block exists"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_new_block_without_extends_colliding_with_core_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  foo:
    _datatype: dtword
""",
    )
    with pytest.raises(PluginMergeError, match="must declare _extends: true"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_keyword_collision_with_core_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  size:
    _datatype: dtint
""",
    )
    with pytest.raises(PluginMergeError, match="collides with a base keyword"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_keyword_collision_between_two_plugins_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag_a = _fragment(
        tmp_path,
        "A.yml",
        """
CORE:
  _extends: true
  extra:
    _datatype: dtword
""",
    )
    frag_b = _fragment(
        tmp_path,
        "B.yml",
        """
CORE:
  _extends: true
  extra:
    _datatype: dtword
""",
    )
    with pytest.raises(PluginMergeError, match="collides with plugin 'plug_a'"):
        processor.load_yaml(
            extra_sources=[
                ("plug_a", frag_a, frozenset()),
                ("plug_b", frag_b, frozenset()),
            ]
        )


def test_block_name_must_be_uppercase(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(tmp_path, "EXT.yml", "lowercase:\n  _datatype: dtblock\n")
    with pytest.raises(PluginMergeError, match="must be upper-case"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_block_name_reserved_instance_suffix(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(tmp_path, "EXT.yml", "FOO_0001:\n  _datatype: dtblock\n")
    with pytest.raises(PluginMergeError, match="reserved instance suffix"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_unknown_datatype_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  foo:
    _datatype: not_a_real_type
""",
    )
    with pytest.raises(PluginMergeError, match="unknown _datatype"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_override_without_manifest_entry_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  size:
    _override: true
    _datatype: dtint
""",
    )
    with pytest.raises(PluginMergeError, match="not listed in the manifest's overrides"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset())])


def test_manifest_override_without_node_flag_raises(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  size:
    _datatype: dtint
""",
    )
    with pytest.raises(PluginMergeError, match="does not set _override: true"):
        processor.load_yaml(extra_sources=[("plug", frag, frozenset({"CORE.size"}))])


def test_override_agreed_both_places_succeeds(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "EXT.yml",
        """
CORE:
  _extends: true
  size:
    _override: true
    _datatype: dtint
    _check:
      - is_int()
      - is_geq() 1
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset({"CORE.size"}))])
    processor.process_all_blocks()
    assert processor.source_of("CORE", "size") == "plug"
    assert "is_geq() 1" in processor.get_block_parameter_checks("CORE", "size")


def test_new_repeatable_block_via_dtblocknamed(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "NEW.yml",
        """
WIDGET:
  _datatype: dtblocknamed
  color:
    _datatype: dtword
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    assert processor.is_multi_instance_block("WIDGET")
    assert not processor.is_multi_instance_block("CORE")


def test_named_prefixes_include_plugin_keyword(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "NEW.yml",
        """
THERMOPHYSICS:
  _datatype: dtblock
  window:
    _datatype: dtlistnamed
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    assert "window" in processor.named_prefixes()


def test_plugin_own_datatypes_section_is_usable(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    frag = _fragment(
        tmp_path,
        "NEW.yml",
        """
_DATATYPES:
  _dtfoo:
    _parse: 'scalar'
    _type: 'string'

THERMOPHYSICS:
  _datatype: dtblock
  widget:
    _datatype: dtfoo
""",
    )
    processor.load_yaml(extra_sources=[("plug", frag, frozenset())])
    processor.process_all_blocks()
    node = processor.processed_data["input_blocks"]["THERMOPHYSICS"]["widget"]
    assert node["data_type"] == "string"


def test_no_extra_sources_is_original_single_file_behaviour(tmp_path):
    processor = _core_processor(tmp_path, CORE_YAML)
    processor.load_yaml()
    processor.process_all_blocks()
    assert processor.keys() == ["CORE", "ASSEMBLY"]
    assert processor.sources["CORE"]["size"] == "base"
