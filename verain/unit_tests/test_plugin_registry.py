"""Unit tests for verain.plugins.PluginRegistry (spec/24 Phase 0)."""

import types

import pytest

from verain.plugins import Plugin, PluginError, PluginRegistry


def _write_manifest(root, manifest_text):
    root.mkdir(parents=True, exist_ok=True)
    (root / "verain_plugin.yml").write_text(manifest_text, encoding="utf-8")


def _write_grammar(root, filename, text="FOO:\n  _extends: true\n"):
    grammar_dir = root / "grammar"
    grammar_dir.mkdir(parents=True, exist_ok=True)
    (grammar_dir / filename).write_text(text, encoding="utf-8")
    return f"grammar/{filename}"


@pytest.fixture
def no_entry_point_plugins(monkeypatch):
    """Isolate a test from whatever plugins are *actually* entry-point
    installed in this environment (a real one, like verain-mongoose, often
    is -- for someone to use `react2xml` directly, not just for this test
    suite). Tests that check path-based discovery/sorting/shadowing in
    isolation should not care what else happens to be installed; tests that
    exercise entry-point discovery construct their own fake entry points
    instead of relying on (or fighting with) real machine state.
    """
    monkeypatch.setattr("verain.plugins.importlib_metadata.entry_points", lambda group=None: [])


class _FakeEntryPoint:
    """Stand-in for importlib.metadata.EntryPoint that loads a fake module."""

    def __init__(self, name, module_root):
        self.name = name
        self.value = f"{name}_module"
        self._module_root = module_root

    def load(self):
        module = types.ModuleType(self.name)
        module.__file__ = str(self._module_root / "__init__.py")
        return module


def test_enabled_false_finds_nothing(monkeypatch):
    monkeypatch.delenv("VERAIN_PLUGIN_PATH", raising=False)
    registry = PluginRegistry.load(enabled=False)
    assert registry.plugins() == []


def test_discovery_from_path(tmp_path, monkeypatch, no_entry_point_plugins):
    plugin_root = tmp_path / "plug"
    grammar_file = _write_grammar(plugin_root, "FOO.yml")
    _write_manifest(
        plugin_root,
        f"""
plugin:
  name: plug-a
  version: 1.0.0
  api_version: 1
grammar:
  - {grammar_file}
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    registry = PluginRegistry.load(enabled=True)
    names = [p.name for p in registry.plugins()]
    assert names == ["plug-a"]
    files = registry.grammar_files()
    assert len(files) == 1
    assert files[0][1] == (plugin_root / grammar_file).resolve()


def test_missing_manifest_raises(tmp_path, monkeypatch):
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(empty_root))
    with pytest.raises(PluginError, match="no verain_plugin.yml manifest"):
        PluginRegistry.load(enabled=True)


def test_unknown_manifest_key_raises(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plug"
    _write_manifest(
        plugin_root,
        """
plugin:
  name: plug-b
  version: 1.0.0
  api_version: 1
not_a_real_key: []
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    with pytest.raises(PluginError, match="unknown manifest key"):
        PluginRegistry.load(enabled=True)


def test_missing_referenced_file_raises(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plug"
    _write_manifest(
        plugin_root,
        """
plugin:
  name: plug-c
  version: 1.0.0
  api_version: 1
grammar:
  - grammar/DOES_NOT_EXIST.yml
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    with pytest.raises(PluginError, match="does not exist"):
        PluginRegistry.load(enabled=True).grammar_files()


def test_api_version_mismatch_raises(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plug"
    _write_manifest(
        plugin_root,
        """
plugin:
  name: plug-d
  version: 1.0.0
  api_version: 99
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    with pytest.raises(PluginError, match="api_version"):
        PluginRegistry.load(enabled=True)


def test_requires_verain_mismatch_raises(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plug"
    _write_manifest(
        plugin_root,
        """
plugin:
  name: plug-e
  version: 1.0.0
  api_version: 1
  requires_verain: ">=999.0"
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    with pytest.raises(PluginError, match="requires verain"):
        PluginRegistry.load(enabled=True)


def test_two_path_plugins_same_name_raises(tmp_path, monkeypatch):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    for root in (root_a, root_b):
        _write_manifest(
            root,
            """
plugin:
  name: dupe
  version: 1.0.0
  api_version: 1
""",
        )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", f"{root_a}{__import__('os').pathsep}{root_b}")
    with pytest.raises(PluginError, match="both declare name 'dupe'"):
        PluginRegistry.load(enabled=True)


def test_ordering_is_name_sorted(tmp_path, monkeypatch, no_entry_point_plugins):
    for name in ("zeta", "alpha", "mu"):
        _write_manifest(
            tmp_path / name,
            f"""
plugin:
  name: {name}
  version: 1.0.0
  api_version: 1
""",
        )
    monkeypatch.setenv(
        "VERAIN_PLUGIN_PATH",
        __import__("os").pathsep.join(str(tmp_path / n) for n in ("zeta", "alpha", "mu")),
    )
    registry = PluginRegistry.load(enabled=True)
    assert [p.name for p in registry.plugins()] == ["alpha", "mu", "zeta"]


def test_path_plugin_shadows_entry_point(tmp_path, monkeypatch, capsys):
    ep_root = tmp_path / "installed"
    _write_manifest(
        ep_root,
        """
plugin:
  name: shadowed
  version: 1.0.0
  api_version: 1
""",
    )
    (ep_root / "__init__.py").write_text("", encoding="utf-8")

    dev_root = tmp_path / "dev"
    _write_manifest(
        dev_root,
        """
plugin:
  name: shadowed
  version: 2.0.0
  api_version: 1
""",
    )

    def fake_entry_points(group=None):
        assert group == "verain.plugins"
        return [_FakeEntryPoint("shadowed", ep_root)]

    monkeypatch.setattr("verain.plugins.importlib_metadata.entry_points", fake_entry_points)
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(dev_root))

    registry = PluginRegistry.load(enabled=True)
    plugins = registry.plugins()
    assert len(plugins) == 1
    assert plugins[0].version == "2.0.0"
    assert "shadows" in capsys.readouterr().err


def test_manifest_and_files_are_frozen_plugin_dataclass(tmp_path, monkeypatch, no_entry_point_plugins):
    plugin_root = tmp_path / "plug"
    grammar_file = _write_grammar(plugin_root, "FOO.yml")
    _write_manifest(
        plugin_root,
        f"""
plugin:
  name: plug-f
  version: 1.0.0
  api_version: 1
grammar:
  - {grammar_file}
overrides:
  - CORE.size
emit_order:
  FOO: {{after: MPACT}}
""",
    )
    monkeypatch.setenv("VERAIN_PLUGIN_PATH", str(plugin_root))
    plugin = PluginRegistry.load(enabled=True).plugins()[0]
    assert isinstance(plugin, Plugin)
    assert plugin.overrides() == frozenset({"CORE.size"})
    assert plugin.emit_order() == {"FOO": {"after": "MPACT"}}
    with pytest.raises(Exception):
        plugin.name = "changed"  # frozen dataclass
