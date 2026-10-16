# Writing a verain plugin

A verain plugin is a separately-versioned, separately-installed Python distribution that adds
new VERA input keywords or whole new blocks, with no edit to this repository. See
`verain/verain/plugins/plugin-framework-design.md` in the VCS repository for the full design;
this is the practical how-to.

A worked example lives in `verain-plugin-example/` next to this checkout (a sibling of
`verain/`, not inside it — it is its own repo). Copying it is the fastest way to start.

## What a plugin ships

```
verain_plugin_example/
├── __init__.py           # empty; exists only so the entry point resolves
├── verain_plugin.yml      # the manifest
├── grammar/*.yml          # Directory.yml fragments: new keywords, new blocks
├── templates/*.yml        # XML emission templates
└── defaults/*.ini         # optional Init-style defaults
```

No plugin-supplied Python is honoured beyond the empty `__init__.py` that anchors the data
files — v1 has no hook for custom check functions or `_do` verbs.

## The manifest

```yaml
plugin:
  name: verain-plugin-example     # unique; used in every diagnostic
  version: 0.1.0
  api_version: 1                  # the only value this verain understands today
  requires_verain: ">=1.0,<2"     # optional; checked against the installed verain
  description: One line.

grammar:      [grammar/CORE.extend.yml, grammar/THERMOPHYSICS.yml]
templates:    [templates/CORE.extend.yml, templates/THERMOPHYSICS.yml]
defaults:     [defaults/THERMOPHYSICS.ini]
overrides:    [CORE.some_keyword]           # only if you are deliberately tightening a core check
emit_order:
  THERMOPHYSICS: {after: MPACT}             # or {before: RUN}
```

Any other top-level key, or any unknown key under `plugin:`, is a hard error naming the file —
a typo here cannot silently drop a section.

## Discovery

Two ways, checked in this order:

1. **Installed, via an entry point.** `pip install` your plugin; its `pyproject.toml` declares:
   ```toml
   [project.entry-points."verain.plugins"]
   example = "verain_plugin_example"
   ```
   The value is the importable module whose directory holds `verain_plugin.yml`.

2. **Uninstalled, via `VERAIN_PLUGIN_PATH`.** `os.pathsep`-separated directories, each
   containing a `verain_plugin.yml` directly (i.e. point at the *package* directory, not the
   repo root — `$PWD/verain_plugin_example`, not `$PWD`). For developing a plugin before it is
   packaged.

A path-discovered plugin with the same `name` as an installed one shadows it (prints to stderr
— the one case where a message is not an error). Discovered plugins are sorted by name before
merging, so the result never depends on entry-point iteration order.

Turn discovery off entirely with `VERAIN_PLUGINS=off` or `react2xml --no-plugins`. Both
`InputParser` and `XMLGenerator` also take an explicit `plugins_enabled=True/False` constructor
argument that overrides the environment variable, for callers that embed verain directly.

Run `react2xml --plugins` to see what is actually discovered: name, version, source, every
block it added, and every keyword it added per core block. This is the first thing to run when
a keyword "isn't being recognised."

## Grammar fragments

**A new block** — a top-level key verain doesn't know, with `_datatype: dtblock` (or
`dtblocknamed` for a repeatable one) as a sibling of its keywords:

```yaml
THERMOPHYSICS:
  _datatype: dtblock
  model:
    _datatype: dtword
    _check:
      - in_dictionary() fixed dynamic tabulated
```

**Extending an existing block** must say so explicitly, so a misspelled new block can't
masquerade as one:

```yaml
CORE:
  _extends: true
  gas_gap_model:
    _datatype: dtword
    _check:
      - in_dictionary() fixed dynamic
```

`_extends: true` on a block that doesn't exist (core or another plugin's) is an error; its
absence on a block that does exist is an error.

### `_datatype` instead of `<<: *anchor`

Core `Directory.yml` spells a keyword's parse/type with a YAML anchor: `<<: *dtword`. YAML
anchors are per-document, so a plugin fragment in its own file cannot reference core's anchors.
`_datatype: dtword` is the substitute — it expands to exactly what `<<: *dtword` would, with the
node's own keys (like `_check`) taking precedence, same as merge-key precedence does. The
built datatypes are core's own (`dtword`, `dtstring`, `dtint`, `dtfloat`, `dtdouble`, `dtbool`,
`dtdate`, `dtlist`, `dtlistnamed`, `dtblock`, `dtblocknamed`, plus `dtdblnamed`). An unknown name
is a hard error listing what's available.

A plugin can declare its own `_DATATYPES:` section in a fragment, for its own reuse across its
other fragment files — it is not shared with core or with other plugins.

### Merge rules (all hard errors, none silent)

| situation | outcome |
|---|---|
| new keyword on an `_extends: true` block, not colliding | merged |
| new block name, not colliding with core or another plugin | merged, added to `_DIRECTORY` |
| keyword collides with a **core** keyword | error, names the core keyword |
| keyword collides with **another plugin's** | error, names both plugins |
| block name collides with core or another plugin | error |
| block name is not upper-case | error — `[BLOCK]` is upper-cased at parse |
| block name ends in `_NNNN` (4 digits) | error — reserved by instance numbering |
| unknown manifest top-level or `plugin:` key | error |
| `_override: true` without a matching `overrides:` entry, or vice versa | error |

**Overriding a core check** needs agreement in two places — `_override: true` on the grammar
node *and* the fully-qualified `BLOCK.keyword` listed under `overrides:` in the manifest — so it
can never happen by accident, and is trivially greppable later. This is a one-way escape hatch
for a site that genuinely must tighten something; it is not for routine use.

## XML templates

**A new block's template** is a complete file, same shape as any core template
(`templates/<BLOCK>.yml`):

```yaml
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
```

**Extending a core block's template** is `_extends: true` plus `_content` children, merged into
the core template's own `_content`:

```yaml
CORE:
  _extends: true
  _content:
    gas_gap_model:
      _pltype: parameter
      _type: string
      _do:
        - copy CORE/$gas_gap_model
      _content:
```

A plugin may **never** replace a core block's template outright — only extend one, and only a
child name that doesn't already exist. This is what keeps a core-only deck byte-identical with
the plugin installed: a deck that never sets the plugin keyword gets a `None` from `copy`, which
the emitter drops, so nothing changes in the output unless the deck actually uses the keyword.

### Extending a repeatable block

The six blocks that can appear more than once (`STATE`, `ASSEMBLY`, `CONTROL`, `INSERT`,
`DETECTOR`, `BRANCH`) are emitted from a template whose top-level key is the *plural* form
(`ASSEMBLIES.yml`, not `ASSEMBLY.yml` — the grammar block name and the template name disagree
for exactly these six) with the per-instance content nested one level deeper, inside a single
list keyed by the loop variable:

| Grammar block | Template file | Per-instance node |
|---|---|---|
| `STATE` | `STATES.yml` | `State_(_loop)` |
| `ASSEMBLY` | `ASSEMBLIES.yml` | `Assembly_(_loop)` |
| `CONTROL` | `CONTROLS.yml` | `Control_(_loop)` |
| `INSERT` | `INSERTS.yml` | `Insert_(_loop)` |
| `DETECTOR` | `DETECTORS.yml` | `Detector_(_loop)` |
| `BRANCH` | `BRANCHES.yml` | `Branch_(_loop)` |

Reach that nested list by writing the same shape back, with the per-instance node name from the
table above as a `_pltype: list` child of the top-level `_extends`:

```yaml
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
```

The merge descends recursively: a child name that already exists on *both* sides is only ever a
collision error unless both are themselves `_pltype: list` containers, in which case it
continues into their own `_content` instead — which is how writing `Assembly_(_loop)` reaches
`Assembly_(_loop)`'s own children rather than replacing the whole per-instance list. This works
to any depth the plugin and core template agree on, not just the one extra level the six
repeatable blocks need; `%ASSEMBLY/$(_path)/$grid_loss_mult` in the `copy` is the ordinary
`$(_path)` idiom `ASSEMBLIES.yml` itself already uses to reach the current instance's own other
keywords. See `grammar/ASSEMBLY.extend.yml` and `templates/ASSEMBLY.extend.yml` in the worked
example for the complete pairing.

### Referencing another keyword's value: `setvar ...,apply=>&resolve`

Most cross-references in this DSL are by *key* — `%ASSEMBLY/$(_path)/$npin` reaches a specific
instance's own keyword once you already know its path. Occasionally a keyword's own *content*
names something else by value, and you need that value usable as a path segment further down —
`verain-mongoose`'s `grouping_map` is the worked example: a map is defined once under
`[MONGOOSE]` and referenced by name from `assembly_grouping <label> user <map_name>`, and
expanding it needs the *referenced* assembly's own `npin`, not anything local to `[MONGOOSE]`.

Two steps get there. First, find the assembly owning a given label — an ordinary key search,
the same `&findfirst`/`&pathlevel` idiom `ASSEMBLIES.yml` uses to find *its own* instance:
```yaml
- setvar _apath,%ASSEMBLY/*/$/%axial/$(_label),apply=>&findfirst
- getvar _apath,apply=>&pathlevel,arg=>3
```
Second, resolve a keyword's own content to a plain value, not a path — `apply=>&resolve`:
```yaml
- setvar _mapname,MONGOOSE/%assembly_grouping/@$(_label):1,apply=>&resolve
```
`_mapname` now holds `"156I"` (a value, not path text — this is the one thing plain `setvar`
and `apply=>&findfirst` cannot do: both work with path *text*, never a resolved value). From
here nothing new is needed: `$(_mapname)` substitutes into any later command exactly like any
other variable, so `%MONGOOSE/%grouping_map/@$(_mapname)` becomes the ordinary, resolvable path
`%MONGOOSE/%grouping_map/@156I` once substituted, and the whole pipeline is one ordinary
`makemap` call:
```yaml
- makemap %ASSEMBLY/$(_apath)/$npin,MONGOOSE/%grouping_map/@$(_mapname),CORE/$bc_sym
```
If the resolve fails (path has no value there — e.g. an `assembly_grouping` entry that isn't
`user` mode has no second content token), the variable is simply never set; a later `$(var)`
substitution with no matching variable leaves the literal text in place, which then fails to
resolve to anything real. No conditional logic is needed in the template for that case — it
degrades to an absent node on its own, the same way every other optional node in this DSL does.
See `verain-mongoose/verain_mongoose/templates/MONGOOSE.yml` for the complete pairing and
`unit_tests/test_setvar_resolve.py` for the mechanism's own regression coverage.

### `emit_order`

```yaml
emit_order:
  THERMOPHYSICS: {after: MPACT}
```

Exactly one of `after`/`before`, naming a block already in the order — a core name, or another
plugin's new block that itself already has a resolved position. A block without `emit_order` is
appended at the end, in plugin-name order. A core block's position is never movable. An unknown
target name is a hard error.

## Defaults

A `defaults/<BLOCK>.ini` file supplies values used only when `--xinit` is *not* passed, merged
in as defaults the user's own input overrides key-by-key — exactly like core's `init/*.ini`. The
block name comes from the file's own stem, so `defaults/THERMOPHYSICS.ini` supplies defaults for
`[THERMOPHYSICS]`. Supplying one for a **core** block is a hard error: it would silently change
the meaning of every existing deck that omits `--xinit`.

## Testing a plugin

- `react2xml --plugins` — confirms discovery and what it contributes.
- `react2xml --schema` vs `--schema --no-plugins` — confirms the new block/keywords show up only
  when plugins are enabled, and that disabling them reproduces core exactly.
- **The core-invariance test, the one that matters most**: run every deck in your downstream
  project's own regression suite (or this repo's `regression_tests/*.inp` / `*.xml.gold`) through
  `react2xml` with your plugin installed, and diff against the existing gold files. They must be
  byte-identical. If they aren't, something in your templates reaches into core's output even
  when the deck doesn't use your keyword — almost always a `copy`/`_do` command that doesn't
  return `None` cleanly for an absent value.
- See `verain-plugin-example/tests/` for worked examples of all of the above, plus grammar-level
  validation tests (a bad `in_dictionary()`/`arraysize()`/range check reports with the keyword
  named in the message).

### A pre-existing gap this surfaces, not introduced by this framework

`InputParser.validate_input` looks a keyword's checks up by its *instanced* name
(`window_0001`) rather than its base name (`window`) for any `_named: 1` (multi-instance)
keyword, so those checks are silently never run today — core's own `mat`, `cell`, `det`, and
every other multi-instance keyword are affected identically. A plugin's own `_named: 1` keyword
(like the worked example's `window`) inherits the same gap; its grammar is still correct and its
checks are exactly what a future fix would need. This is tracked separately, and is not
something installing a plugin changes one way or the other.

## Unrecognized blocks are a hard error

A deck naming a block verain doesn't know — a plugin block with that plugin not installed, run
with `--no-plugins`, or simply a typo — raises at parse time; it is never silently accepted as an
empty block. Run `react2xml --plugins` first when a deck that should work doesn't: an
unrecognized block almost always means the plugin that defines it isn't actually being
discovered (wrong `VERAIN_PLUGIN_PATH`, `VERAIN_PLUGINS=off`, or `--no-plugins`), not a problem
with the plugin's grammar itself.
