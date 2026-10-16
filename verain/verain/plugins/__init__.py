"""Plugin discovery for the verain plugin framework.

A plugin is an installable Python distribution that ships a
``verain_plugin.yml`` manifest plus grammar/template/defaults YAML. This
module discovers installed and path-based plugins and exposes the files they
contribute. No plugin Python code is ever imported beyond the single module
named by its entry point, and that module is never called into -- it exists
only so the manifest has somewhere to live.
"""

import operator
import os
import re
import sys
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Tuple

import yaml

#: api_version values this verain understands. A manifest naming anything
#: else is refused outright rather than guessed at.
API_VERSION_SUPPORTED = {1}

_TOP_LEVEL_KEYS = {"plugin", "grammar", "templates", "defaults", "emit_order", "overrides"}
_PLUGIN_KEYS_REQUIRED = {"name", "version", "api_version"}
_PLUGIN_KEYS_OPTIONAL = {"requires_verain", "description"}
_LIST_KEYS = ("grammar", "templates", "defaults")


class PluginError(Exception):
    """A plugin could not be discovered, loaded, or validated.

    Every raise here names the plugin and the file, per the hard constraint
    in spec/24 S1: a plugin that cannot be loaded stops the run, never a
    warn-and-continue.
    """


@dataclass(frozen=True)
class Plugin:
    """One discovered plugin: its manifest and where its files live."""

    name: str
    version: str
    root: Path
    manifest: Dict[str, Any]
    source: str

    def _files(self, key: str) -> List[Path]:
        entries = self.manifest.get(key) or []
        paths = []
        for entry in entries:
            path = (self.root / entry).resolve()
            if not path.exists():
                raise PluginError(f"plugin '{self.name}': {key} entry '{entry}' does not exist (expected {path})")
            paths.append(path)
        return paths

    def grammar_files(self) -> List[Path]:
        """Directory.yml fragments this plugin contributes, in manifest order."""
        return self._files("grammar")

    def template_files(self) -> List[Path]:
        """XML emission template files this plugin contributes."""
        return self._files("templates")

    def defaults_files(self) -> List[Path]:
        """Init-style ``.ini`` default files this plugin contributes."""
        return self._files("defaults")

    def overrides(self) -> FrozenSet[str]:
        """Fully-qualified ``BLOCK.keyword`` names this plugin is allowed to tighten."""
        return frozenset(self.manifest.get("overrides") or [])

    def emit_order(self) -> Dict[str, Dict[str, str]]:
        """Where this plugin's new blocks land in the XML child order."""
        return dict(self.manifest.get("emit_order") or {})


def default_enabled() -> bool:
    """Whether plugin discovery runs unless told otherwise.

    ``VERAIN_PLUGINS=off`` is the environment-variable escape hatch from
    spec/24 S3.2; callers may also pass an explicit ``enabled=`` to override
    this (e.g. ``react2xml --no-plugins``).
    """
    return os.environ.get("VERAIN_PLUGINS", "").strip().lower() != "off"


def _parse_version(text: str) -> Tuple[int, ...]:
    parts = re.findall(r"\d+", text)
    return tuple(int(p) for p in parts) if parts else (0,)


def _version_satisfies(version: str, spec: str) -> bool:
    """Check a dotted version string against a comma-separated clause spec.

    Supports ``>=``, ``<=``, ``==``, ``!=``, ``>``, ``<`` clauses, e.g.
    ``">=1.1,<2"``.  Deliberately minimal: ``requires_verain`` is the only
    consumer, and it doesn't need the ``packaging`` dependency's full PEP 440
    machinery for six comparison operators on plain dotted integers.
    """
    ops = {
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
    }
    version_t = _parse_version(version)
    for clause in spec.split(","):
        clause = clause.strip()
        if not clause:
            continue
        for op_str in (">=", "<=", "==", "!=", ">", "<"):
            if clause.startswith(op_str):
                bound_t = _parse_version(clause[len(op_str) :].strip())
                width = max(len(version_t), len(bound_t))
                v = version_t + (0,) * (width - len(version_t))
                b = bound_t + (0,) * (width - len(bound_t))
                if not ops[op_str](v, b):
                    return False
                break
        else:
            raise PluginError(f"requires_verain clause '{clause}' has no recognized operator")
    return True


def _installed_verain_version() -> str:
    try:
        return importlib_metadata.version("verain")
    except importlib_metadata.PackageNotFoundError:
        return "0.0.0"


def _load_manifest(root: Path, source: str) -> Plugin:
    manifest_path = root / "verain_plugin.yml"
    if not manifest_path.exists():
        raise PluginError(f"{source}: no verain_plugin.yml manifest found at {root}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}

    unknown = set(manifest) - _TOP_LEVEL_KEYS
    if unknown:
        raise PluginError(
            f"{source} ({manifest_path}): unknown manifest key(s) {sorted(unknown)}; "
            f"expected one of {sorted(_TOP_LEVEL_KEYS)}"
        )

    plugin_info = manifest.get("plugin") or {}
    missing = _PLUGIN_KEYS_REQUIRED - set(plugin_info)
    if missing:
        raise PluginError(f"{source} ({manifest_path}): manifest 'plugin:' section is missing {sorted(missing)}")
    unknown_plugin_keys = set(plugin_info) - _PLUGIN_KEYS_REQUIRED - _PLUGIN_KEYS_OPTIONAL
    if unknown_plugin_keys:
        raise PluginError(f"{source} ({manifest_path}): unknown key(s) in 'plugin:' section {sorted(unknown_plugin_keys)}")

    name = plugin_info["name"]
    api_version = plugin_info["api_version"]
    if api_version not in API_VERSION_SUPPORTED:
        raise PluginError(
            f"plugin '{name}' ({manifest_path}): api_version {api_version!r} is not supported "
            f"by this verain (supported: {sorted(API_VERSION_SUPPORTED)})"
        )

    requires_verain = plugin_info.get("requires_verain")
    if requires_verain:
        installed = _installed_verain_version()
        if not _version_satisfies(installed, requires_verain):
            raise PluginError(
                f"plugin '{name}' ({manifest_path}): requires verain {requires_verain}, " f"but {installed} is installed"
            )

    for key in _LIST_KEYS:
        if key in manifest and not isinstance(manifest[key], list):
            raise PluginError(f"plugin '{name}' ({manifest_path}): '{key}:' must be a list of file paths")
    if "overrides" in manifest and not isinstance(manifest["overrides"], list):
        raise PluginError(f"plugin '{name}' ({manifest_path}): 'overrides:' must be a list")
    if "emit_order" in manifest and not isinstance(manifest["emit_order"], dict):
        raise PluginError(f"plugin '{name}' ({manifest_path}): 'emit_order:' must be a mapping")

    return Plugin(name=name, version=str(plugin_info.get("version", "")), root=root, manifest=manifest, source=source)


def _discover_entry_points() -> Dict[str, Plugin]:
    found: Dict[str, Plugin] = {}
    for ep in importlib_metadata.entry_points(group="verain.plugins"):
        module = ep.load()
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            raise PluginError(f"entry-point '{ep.name}' ({ep.value}) has no importable module file")
        root = Path(module_file).resolve().parent
        plugin = _load_manifest(root, source=f"entry-point: {ep.name}")
        if plugin.name in found:
            raise PluginError(
                f"two entry-point plugins both declare name '{plugin.name}' "
                f"({found[plugin.name].source} and {plugin.source})"
            )
        found[plugin.name] = plugin
    return found


def _discover_path_plugins() -> Dict[str, Plugin]:
    found: Dict[str, Plugin] = {}
    raw = os.environ.get("VERAIN_PLUGIN_PATH", "")
    for entry in raw.split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        root = Path(entry).resolve()
        plugin = _load_manifest(root, source=f"VERAIN_PLUGIN_PATH: {root}")
        if plugin.name in found:
            raise PluginError(
                f"two VERAIN_PLUGIN_PATH entries both declare name '{plugin.name}' "
                f"({found[plugin.name].source} and {plugin.source})"
            )
        found[plugin.name] = plugin
    return found


class PluginRegistry:
    """Discovered plugins for this process, sorted by name.

    Loaded once per process and cached by ``enabled``, the same way
    ``InputParser._directory_processor`` was already cached before this
    framework existed. Call :meth:`reset_cache` between test scenarios that
    change discovery inputs (``VERAIN_PLUGIN_PATH``, installed entry points).
    """

    _cache: Dict[bool, "PluginRegistry"] = {}

    def __init__(self, plugins: List[Plugin]):
        self._plugins = list(plugins)

    @classmethod
    def load(cls, enabled: bool = True) -> "PluginRegistry":
        """Return the cached registry for ``enabled``, discovering it first if needed."""
        if enabled in cls._cache:
            return cls._cache[enabled]
        registry = cls._discover(enabled)
        cls._cache[enabled] = registry
        return registry

    @classmethod
    def reset_cache(cls) -> None:
        """Drop the cached registries, forcing the next :meth:`load` to re-discover."""
        cls._cache.clear()

    @classmethod
    def _discover(cls, enabled: bool) -> "PluginRegistry":
        if not enabled:
            return cls([])

        by_name = _discover_entry_points()
        for name, plugin in _discover_path_plugins().items():
            if name in by_name:
                print(
                    f"verain: plugin '{name}' found at {plugin.root} shadows the installed " f"{by_name[name].source}",
                    file=sys.stderr,
                )
            by_name[name] = plugin

        return cls(sorted(by_name.values(), key=lambda p: p.name))

    def plugins(self) -> List[Plugin]:
        """Every discovered plugin, sorted by name."""
        return list(self._plugins)

    def grammar_files(self) -> List[Tuple[Plugin, Path]]:
        """Every plugin's grammar fragments, as ``(plugin, path)`` pairs."""
        return [(p, f) for p in self._plugins for f in p.grammar_files()]

    def template_files(self) -> List[Tuple[Plugin, Path]]:
        """Every plugin's XML emission templates, as ``(plugin, path)`` pairs."""
        return [(p, f) for p in self._plugins for f in p.template_files()]

    def defaults_files(self) -> List[Tuple[Plugin, Path]]:
        """Every plugin's Init-style defaults, as ``(plugin, path)`` pairs."""
        return [(p, f) for p in self._plugins for f in p.defaults_files()]

    def emit_order(self) -> Dict[str, Dict[str, str]]:
        """Every plugin's ``emit_order`` entries, merged."""
        merged: Dict[str, Dict[str, str]] = {}
        for p in self._plugins:
            merged.update(p.emit_order())
        return merged
