"""Unit tests for XMLGenerator's ``setvar ...,apply=>&resolve`` mode.

``&resolve`` turns a fully-specified KeyTree path into its scalar *value*,
stored in ``self._vars`` for later ``$(var)`` substitution -- the missing
piece that lets one keyword's content (naming another keyword by value) be
turned into a usable path key. See spec/24 S7 / VCS CLAUDE.md for why this
was added: `verain-mongoose`'s `grouping_map` needed to reference the
`npin` of whichever `[ASSEMBLY]` an `assembly_grouping` entry names, and
nothing else in the existing `_do` vocabulary resolves a parsed value into
a reusable path segment (`setvar` alone stores raw path *text*;
`apply=>&findfirst` searches for a matching *key*, not a value).
"""

from verain.xml.xml_generator import XMLGenerator


def _generator_with_db(db):
    gen = XMLGenerator()
    gen._db = db  # pylint: disable=protected-access
    gen._vars = {}  # pylint: disable=protected-access
    return gen


def test_resolve_stores_the_value_not_the_path():
    gen = _generator_with_db(
        {
            "MONGOOSE": {
                "assembly_grouping": {
                    "ASSY1": {"_content": ["user", "156I"], "_key": "ASSY1"},
                }
            }
        }
    )
    gen._handle_setvar(  # pylint: disable=protected-access
        "setvar _mapname,MONGOOSE/%assembly_grouping/@ASSY1:1,apply=>&resolve"
    )
    assert gen._vars["_mapname"] == "156I"  # pylint: disable=protected-access


def test_resolve_leaves_var_unset_when_path_has_no_value():
    """A non-`user`-mode assembly_grouping entry has no second content token;
    &resolve must not raise, and must not set the variable at all."""
    gen = _generator_with_db(
        {
            "MONGOOSE": {
                "assembly_grouping": {
                    "ASSY2": {"_content": ["pin"], "_key": "ASSY2"},
                }
            }
        }
    )
    gen._handle_setvar(  # pylint: disable=protected-access
        "setvar _mapname,MONGOOSE/%assembly_grouping/@ASSY2:1,apply=>&resolve"
    )
    assert "_mapname" not in gen._vars  # pylint: disable=protected-access


def test_unset_resolved_var_degrades_to_unresolvable_path():
    """When &resolve leaves a variable unset, a later $(var) substitution
    leaves the literal text in place (verain/PLUGINS.md's documented
    graceful-degrade), which then fails to resolve to any real DB entry --
    it never crashes and never picks the wrong thing."""
    gen = _generator_with_db({})
    substituted = gen._substitute_vars("MONGOOSE/%grouping_map/@$(_mapname)")  # pylint: disable=protected-access
    assert substituted == "MONGOOSE/%grouping_map/@$(_mapname)"
    assert gen._resolve_path(substituted) is None  # pylint: disable=protected-access


def test_resolved_value_is_usable_as_a_later_path_key():
    """The whole point: a &resolve'd value substituted into a later command
    becomes an ordinary, resolvable path -- the same textual substitution
    BRANCHES.yml's %BRANCH/(_path)/%branch_set/@(_bloop) idiom already
    relies on for a loop variable, just fed by &resolve instead."""
    gen = _generator_with_db(
        {
            "MONGOOSE": {
                "assembly_grouping": {
                    "ASSY1": {"_content": ["user", "156I"], "_key": "ASSY1"},
                },
                "grouping_map": {
                    "156I": {"_content": ["0", "2", "2"], "_key": "156I"},
                },
            }
        }
    )
    gen._handle_setvar(  # pylint: disable=protected-access
        "setvar _mapname,MONGOOSE/%assembly_grouping/@ASSY1:1,apply=>&resolve"
    )
    path = gen._substitute_vars("MONGOOSE/%grouping_map/@$(_mapname)")  # pylint: disable=protected-access
    assert path == "MONGOOSE/%grouping_map/@156I"
    resolved = gen._resolve_path_list(path)  # pylint: disable=protected-access
    assert resolved == ["0", "2", "2"]


def test_existing_findfirst_mode_is_unaffected():
    """&resolve is additive: the pre-existing &findfirst mode (path search,
    not value resolution) must behave exactly as before."""
    gen = _generator_with_db(
        {
            "ASSEMBLY": {
                "1": {"axial": {"ASSY1": {"_content": ["0.0", "LAT1", "1.0"], "_key": "ASSY1"}}},
            }
        }
    )
    gen._handle_setvar("setvar _path,%ASSEMBLY/*/$/%axial/ASSY1,apply=>&findfirst")  # pylint: disable=protected-access
    gen._handle_getvar("getvar _path,apply=>&pathlevel,arg=>3")  # pylint: disable=protected-access
    assert gen._vars["_path"] == "1"  # pylint: disable=protected-access
