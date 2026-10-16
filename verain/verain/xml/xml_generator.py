"""XMLGenerator: Converts parsed VERAIn data to XML format.

This module translates parsed input data through YAML template rules
into XML output that matches the .xml.gold reference files exactly.
"""

import os
import re
import tempfile
from typing import Any, Dict, Optional
from xml.sax.saxutils import escape as xml_escape
import yaml
from verain.parser import InputParser
from verain.plugins import Plugin, PluginError, PluginRegistry, default_enabled
from verain.templates.directory_processor import build_directory_processor


class XMLGenerator:
    """Generates VERA XML output from parsed input data using YAML templates.

    The generator takes parsed data from InputParser and processes it through
    YAML template files to produce XML output.

    Parameters
    ----------
    template_dir : str, optional
        Directory containing YAML templates (default: "templates" subdir of this module);
        this usually does not need to be provided.
    plugins_enabled : bool, optional
        Whether to merge discovered verain plugins' templates and grammar
        into this generator. Defaults to the ``VERAIN_PLUGINS``
        environment variable (unset/anything but ``"off"`` means on).
    """

    #: The 19 core blocks' XML child order. Fixed: a plugin may insert new
    #: entries around these (its own ``emit_order``), but may never move one.
    _CORE_TEMPLATE_ORDER = [
        "CASEID",
        "BRANCHES",
        "STATES",
        "CORE",
        "ASSEMBLIES",
        "CONTROLS",
        "DETECTORS",
        "INSERTS",
        "SHIFT",
        "EDITS",
        "COBRATF",
        "COUPLING",
        "MPACT",
        "MAMBA",
        "VERAONEWAY",
        "BISON",
        "FAST",
        "RUN",
        "TRANSIENT",
    ]

    def __init__(self, template_dir: Optional[str] = None, plugins_enabled: Optional[bool] = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.template_dir = template_dir
        self._plugins_enabled = plugins_enabled if plugins_enabled is not None else default_enabled()
        self.templates = {}
        self._db = {}
        self._vars = {}
        self._excludes = set()
        self._directory = build_directory_processor(enabled=self._plugins_enabled)
        self._load_templates()
        self._named_prefixes = self._directory.named_prefixes()

    @property
    def directory_processor(self):
        """The merged DirectoryProcessor (core grammar plus any plugins') this generator uses."""
        return self._directory

    @staticmethod
    def _preprocess_yaml(text: str) -> str:
        """Quote YAML values starting with % (KeyTree path notation).

        Parameters
        ----------
        text : str
            Raw YAML text.

        Returns
        -------
        str
            YAML text with %-prefixed values quoted.
        """
        return re.sub(r"(:\s+)(%\S+.*)$", r'\1"\2"', text, flags=re.MULTILINE)

    def _load_templates(self) -> None:
        """Loads all the block-specific template files, core first, then plugins'.

        Core templates are loaded under their fixed ``_CORE_TEMPLATE_ORDER``
        names. Each plugin template file is then merged in: a fresh
        top-level key becomes a new block (inserted into ``TEMPLATE_ORDER``
        per its manifest's ``emit_order``); a key matching a core block name
        must declare ``_extends: true`` and is merged into that block's
        ``_content`` instead.
        """
        self.templates = {}
        for name in self._CORE_TEMPLATE_ORDER:
            filepath = os.path.join(self.template_dir, f"{name}.yml")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = self._preprocess_yaml(f.read())
                    self.templates[name] = yaml.safe_load(text)

        self._plugin_new_blocks: list = []
        emit_order: Dict[str, Dict[str, str]] = {}
        if self._plugins_enabled:
            registry = PluginRegistry.load(enabled=True)
            for plugin, path in registry.template_files():
                with open(path, "r", encoding="utf-8") as f:
                    text = self._preprocess_yaml(f.read())
                doc = yaml.safe_load(text) or {}
                for top_key, top_val in doc.items():
                    self._merge_template_fragment(plugin, path, top_key, top_val)
            emit_order = registry.emit_order()

        self._emit_order = emit_order
        self.TEMPLATE_ORDER = self._compute_template_order()

    def _merge_template_fragment(self, plugin: Plugin, path: str, top_key: str, top_val: Any) -> None:
        """Merge one top-level key from a plugin template file.

        See ``_load_templates`` for the extend-vs-new-block rule this enforces.
        """
        is_core_name = top_key in self._CORE_TEMPLATE_ORDER
        extends = bool(isinstance(top_val, dict) and top_val.get("_extends", False))

        if is_core_name:
            if not extends:
                raise PluginError(
                    f"plugin '{plugin.name}' ({path}): template '{top_key}' already exists as a "
                    "core block's template; a plugin may not replace it, only extend it with "
                    "'_extends: true'"
                )
            core_doc = self.templates.get(top_key)
            if core_doc is None or top_key not in core_doc:
                raise PluginError(f"plugin '{plugin.name}' ({path}): core template '{top_key}.yml' was not found to extend")
            self._merge_template_content(plugin, path, top_key, core_doc[top_key], top_val)
            return

        if top_key in self.templates:
            raise PluginError(f"plugin '{plugin.name}' ({path}): template block '{top_key}' already defined by another plugin")
        if extends:
            raise PluginError(
                f"plugin '{plugin.name}' ({path}): '_extends: true' on '{top_key}', but no core "
                "template of that name exists"
            )

        self.templates[top_key] = {top_key: top_val}
        self._plugin_new_blocks.append(top_key)

    @classmethod
    def _merge_template_content(cls, plugin: Plugin, path: str, block_name: str, core_inner: dict, ext_tmpl: dict) -> None:
        """Merge an extension template's ``_content`` children into the core block's.

        A flat block's whole ``_content`` is one list, so this is where a
        plugin keyword ends up. A repeatable block's template nests one more
        level -- ``ASSEMBLIES``'s own ``_content`` holds exactly one
        per-instance list, ``Assembly_(_loop)``, and *that* list's own
        ``_content`` is where a per-instance keyword like a plugin's
        ``grid_loss_mult`` has to land. So the merge recurses: a child name
        that already exists on both sides is only ever a hard error unless
        both are themselves ``_pltype: list`` containers, in which case it
        descends into their own ``_content`` and tries again -- which is how
        a plugin fragment reaches ``Assembly_(_loop)._content`` by writing
        that same nested shape (see ``PLUGINS.md``'s per-instance node name
        table). Depth is not hard-coded to one extra level; it walks however
        deep the plugin's fragment and the core template agree to go.
        """
        ext_content = ext_tmpl.get("_content") or {}
        core_content = core_inner.setdefault("_content", {})
        cls._merge_content_dict(plugin, path, block_name, core_content, ext_content)

    @classmethod
    def _merge_content_dict(cls, plugin: Plugin, path: str, context_label: str, core_content: dict, ext_content: dict) -> None:
        """Recursive worker for :meth:`_merge_template_content`.

        Collision-checked the same way grammar merging is: a plugin child
        name already present is a hard error, never a silent replace --
        unless both sides are ``_pltype: list`` containers, the signal that
        the plugin means "merge into this nested list," not "replace it."
        Order doesn't matter here -- the emitter sorts a list's children
        alphabetically before writing XML -- so a merged child can only ever
        appear, never reorder existing output.
        """
        for child_name, child_tmpl in ext_content.items():
            if child_name.startswith("_"):
                continue
            if child_name not in core_content:
                core_content[child_name] = child_tmpl
                continue

            core_child = core_content[child_name]
            ext_is_list = isinstance(child_tmpl, dict) and child_tmpl.get("_pltype") == "list"
            core_is_list = isinstance(core_child, dict) and core_child.get("_pltype") == "list"
            if not (ext_is_list and core_is_list):
                raise PluginError(
                    f"plugin '{plugin.name}' ({path}): template child '{context_label}.{child_name}' "
                    "collides with an existing template entry"
                )

            core_grandchildren = core_child.setdefault("_content", {})
            ext_grandchildren = child_tmpl.get("_content") or {}
            cls._merge_content_dict(plugin, path, f"{context_label}.{child_name}", core_grandchildren, ext_grandchildren)

    def _compute_template_order(self) -> list:
        """The 19 core names, unchanged, with plugin blocks inserted per ``emit_order``.

        A block without an ``emit_order`` entry is appended at the end, in
        plugin-name order (``self._plugin_new_blocks`` is already in that
        order, since ``PluginRegistry`` sorts plugins by name). A core name
        is never moved: it is only ever a landmark other blocks are placed
        ``after``/``before``.
        """
        order = list(self._CORE_TEMPLATE_ORDER)
        placed = set(order)
        unplaced = []
        for block in self._plugin_new_blocks:
            spec = self._emit_order.get(block)
            if not spec:
                unplaced.append(block)
                continue
            if not isinstance(spec, dict) or len(spec) != 1:
                raise PluginError(f"emit_order for '{block}' must name exactly one of 'after'/'before'")
            ((rel, target),) = spec.items()
            if rel not in ("after", "before"):
                raise PluginError(f"emit_order for '{block}': expected key 'after' or 'before', got '{rel}'")
            if target not in placed:
                raise PluginError(f"emit_order for '{block}': unknown block '{target}'")
            idx = order.index(target)
            order.insert(idx + 1 if rel == "after" else idx, block)
            placed.add(block)
        order.extend(unplaced)
        return order

    # =========================================================================
    # Public API
    # =========================================================================

    def _load_init_data(self, parsed_data: dict) -> None:
        """Load Init/*.ini files and merge default data into parsed_data.

        Init data is used for each block when --xinit is NOT set:
        for each block, if an Init/{BLOCK}.ini file exists, its contents
        are parsed and merged as defaults (input data takes priority).

        A plugin may contribute its own defaults, named the same way core's are:
        a defaults file's stem is the block it applies to. It may not supply one
        for a core block -- that would silently change the meaning of every
        existing deck that omits ``--xinit``.

        Parameters
        ----------
        parsed_data : dict
            Parsed input data dictionary (modified in-place).
        """

        init_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "init")

        plugin_defaults: Dict[str, Any] = {}
        if self._plugins_enabled:
            core_block_names = set(build_directory_processor(enabled=False).keys())
            for plugin, path in PluginRegistry.load(enabled=True).defaults_files():
                block = os.path.splitext(os.path.basename(str(path)))[0]
                if block in core_block_names:
                    raise PluginError(
                        f"plugin '{plugin.name}' ({path}): supplies a default for core block "
                        f"'{block}'; a plugin may only supply defaults for its own blocks"
                    )
                plugin_defaults[block] = (plugin, str(path))

        # Process all blocks that exist in both parsed_data and a default source
        for block in list(parsed_data.keys()):
            ini_path = os.path.join(init_dir, f"{block}.ini")
            if not os.path.exists(ini_path):
                plugin_entry = plugin_defaults.get(block)
                if plugin_entry is None:
                    continue
                ini_path = plugin_entry[1]
            # Parse the init file by wrapping it in a block header
            with (
                tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=False, encoding="utf-8") as tmp,
                open(ini_path, encoding="utf-8") as tmp_ini,
            ):
                tmp.write(f"[{block}]\n" + tmp_ini.read())
                tmp_path = tmp.name
            try:
                init_parser = InputParser(plugins_enabled=self._plugins_enabled)
                init_data = init_parser.parse_file(tmp_path)
            finally:
                os.unlink(tmp_path)

            init_block = init_data.get(block, {})
            data_block = parsed_data.get(block, {})
            if not data_block:
                continue

            # Merge init entries as defaults: only add keys that don't exist
            # in the user's input data. For multi-instance params like mat_NNNN,
            # check if user already has any mat entries.
            existing_prefixes = set()
            for k in data_block:
                base = re.sub(r"_\d+$", "", k)
                existing_prefixes.add(base)

            for k, v in init_block.items():
                if k.startswith("_"):
                    continue
                base = re.sub(r"_\d+$", "", k)
                if base not in existing_prefixes:
                    data_block[k] = v

    def generate(
        self,
        parsed_data: dict,
        case_id: Optional[str] = None,
        xinit: bool = True,
        line_lengths: Optional[dict] = None,
    ) -> str:
        """Generate XML string from parsed VERAIn data.

        Parameters
        ----------
        parsed_data : dict
            Dictionary from InputParser.
        case_id : str, optional
            Optional case ID override.
        xinit : bool, optional
            If True (default), skip loading Init/*.ini defaults.
            If False, load Init/*.ini files to provide default material definitions.
        line_lengths : dict, optional
            Line-length metadata from ``InputParser.line_lengths``.  Keyed by
            block name → {param_name: [lengths]}.  When provided, the metadata
            is injected into the block dicts before processing so that multi-line
            array formatting is preserved in the XML output.

        Returns
        -------
        str
            XML string.
        """
        if line_lengths:
            for block_key, ll_map in line_lengths.items():
                if block_key in parsed_data and isinstance(parsed_data[block_key], dict):
                    parsed_data[block_key]["_line_lengths"] = ll_map
        if not xinit:
            self._load_init_data(parsed_data)
        self._db = self._build_db(parsed_data)
        self._vars = {}
        self._excludes = set()

        if case_id is None:
            title_val = self._db.get("CASEID", {}).get("title", []).get("_content", [])
            case_id = " ".join(title_val) if title_val else ""

        # Build root CASEID node with its own content first, then blocks in template order
        # Within each block, children are sorted alphabetically.

        # Process CASEID template for case_id parameter
        caseid_children = []
        caseid_children.append({"_tag": "param", "_name": "case_id", "_type": "string", "_val": case_id})

        # Process each template block in order
        for block_key in self.TEMPLATE_ORDER:
            if block_key == "CASEID":
                continue
            if block_key not in self.templates:
                continue
            block_tmpl = self.templates[block_key][block_key]

            self._vars = {}
            self._excludes = set()

            result = self._process_list(block_key, block_tmpl)
            if result is not None and result.get("_children"):
                caseid_children.append(result)

        # Generate XML
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<?xml-stylesheet version="1.0" type="text/xsl" href="PL9.xsl"?>')

        # Emit root CASEID with children in fixed order (not sorted)
        lines.append('<ParameterList name="CASEID">')
        for child in caseid_children:
            self._emit(child, 1, lines)
        lines.append("</ParameterList>")

        xml = "\n".join(lines) + "\n"

        return xml

    def generate_to_file(self, parsed_data: dict, output_file: str, case_id: Optional[str] = None, xinit: bool = True) -> None:
        """Generate XML and write to output_file.

        Parameters
        ----------
        parsed_data : dict
            Dictionary from InputParser.
        output_file : str
            Path to write XML output.
        case_id : str, optional
            Optional case ID override.
        xinit : bool, optional
            If True (default), skip loading Init/*.ini defaults.
            If False, load Init/*.ini files to provide default
            material definitions.
        """
        xml_str = self.generate(parsed_data, case_id, xinit=xinit)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xml_str)
            f.write("\n")

    # =========================================================================
    # Source DB construction
    # =========================================================================

    def _build_db(self, parsed_data: dict) -> dict:
        """Build a hierarchical database from flat parser output.

        The database contains key and content for each parameter:
        - CORE/mat/he/_content = ['0.000176']
        - CORE/mat/he/_key = 'he'
        - STATE/1/power/_content = ['100.0']
        - ASSEMBLY/1/cell/1/_content = ['0.4096','0.418','0.475','/','U31','he','zirc']

        Parameters
        ----------
        parsed_data : dict
            Flat dictionary from InputParser.

        Returns
        -------
        dict
            Hierarchical database structured for template processing.
        """
        db = {}
        for block_key, block_data in parsed_data.items():
            base = self._strip_instance_suffix(block_key)
            num = self._get_instance_num(block_key)

            if self._directory.is_multi_instance_block(base):
                if base not in db:
                    db[base] = {}
                idx = str(num) if num else "1"
                db[base][idx] = self._build_block_db(block_data)
            else:
                db[base] = self._build_block_db(block_data)
        return db

    @staticmethod
    def _strip_commas(values: list) -> list:
        """Strip trailing/leading commas from values and drop comma-only tokens.

        Strip commas that act as separators (trailing/leading on tokens),
        preserving commas within quoted multi-word strings.

        Parameters
        ----------
        values : list
            List of string values to process.

        Returns
        -------
        list
            List of processed string values with commas stripped as needed.
        """
        out = []
        for v in values:
            # Only strip commas if token doesn't contain spaces (i.e., not a quoted multi-word value)
            if " " not in v:
                v = v.strip(",")
            if v:
                out.append(v)
        return out

    @staticmethod
    def _parse_content_and_params(tokens: list[str]) -> tuple[list[str], dict[str, str]]:
        """Split a token list into content and key=value parameters after '/'.

        Handles ``key=value``, ``/key=value``, and ``key = value`` forms.

        Parameters
        ----------
        tokens : list of str
            Token list to parse.

        Returns
        -------
        tuple of (list, dict)
            ``(content_tokens, params_dict)``.
        """
        content: list[str] = []
        params: dict[str, str] = {}
        past_slash = False
        i = 0
        while i < len(tokens):
            v = tokens[i]
            if v == "/":
                past_slash = True
                content.append(v)
                i += 1
                continue
            # Handle combined /key=value tokens
            if v.startswith("/") and "=" in v:
                past_slash = True
                v_inner = v[1:]
                eqparts = v_inner.split("=", 1)
                if len(eqparts) == 2 and re.match(r"^[a-zA-Z_]\w*$", eqparts[0]):
                    params[eqparts[0]] = eqparts[1]
                    i += 1
                    continue
            if past_slash:
                if "=" in v:
                    eqparts = v.split("=", 1)
                    if len(eqparts) == 2 and re.match(r"^[a-zA-Z_]\w*$", eqparts[0]):
                        params[eqparts[0]] = eqparts[1]
                        i += 1
                        continue
                if re.match(r"^[a-zA-Z_]\w*$", v) and i + 2 < len(tokens) and tokens[i + 1] == "=":
                    params[v] = tokens[i + 2]
                    i += 3
                    continue
            content.append(v)
            i += 1
        return content, params

    def _build_block_db(self, block_data: dict[str, Any]) -> dict[str, Any]:
        """Build a hierarchical block from flat param data.

        Parameters
        ----------
        block_data : dict
            Flat dictionary of parameters for a block from InputParser.

        Returns
        -------
        dict
            Hierarchical dictionary structured for template processing.
        """

        result = {}
        # Line-length metadata from parser (maps param_name -> [lengths])
        parser_line_lengths = block_data.get("_line_lengths", {})
        for key, values in block_data.items():
            if key == "_line_lengths":
                continue
            values = self._strip_commas(values)
            base_p = self._strip_instance_suffix(key)
            p_num = self._get_instance_num(key)

            if base_p in self._named_prefixes and p_num is not None:  # pylint: disable=unsupported-membership-test
                name = values[0]
                rest = values[1:]
                content, params = self._parse_content_and_params(rest)

                if base_p not in result:
                    result[base_p] = {}
                entry = {"_content": content, "_key": name}
                if params:
                    entry["_parameters"] = params

                # Material density override: if we already have a full definition
                # and new entry is density-only, merge (replace density, keep isotopes)
                if base_p == "mat" and name in result[base_p]:
                    existing = result[base_p][name]
                    existing_content = existing.get("_content", [])
                    existing_no_slash = [c for c in existing_content if c != "/"]
                    new_no_slash = [c for c in content if c != "/"]
                    if len(new_no_slash) <= 1 < len(existing_no_slash):
                        merged_content = list(existing_content)
                        if new_no_slash:
                            merged_content[0] = new_no_slash[0]
                        entry["_content"] = merged_content
                        merged_params = dict(existing.get("_parameters", {}))
                        merged_params.update(params)
                        if merged_params:
                            entry["_parameters"] = merged_params

                result[base_p][name] = entry
            else:
                # Strip leading '=' from values (comes from 'param = value' syntax)
                clean_values = [v for v in values if v != "="]
                content, params = self._parse_content_and_params(clean_values)
                entry: dict = {"_content": content}
                # Get line lengths from parser metadata
                orig_key = key
                if isinstance(parser_line_lengths, dict) and orig_key in parser_line_lengths:
                    entry["_line_lengths"] = parser_line_lengths[orig_key]
                if params:
                    entry["_parameters"] = params
                result[key] = entry

        # Apply aliases from Directory.yml: lattice is an alias for rodmap
        if "lattice" in result and "rodmap" not in result:
            result["rodmap"] = result["lattice"]

        return result

    # =========================================================================
    # Template processing
    # =========================================================================

    def _process_list(self, name: str, tmpl: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Process a list-type template node.

        Parameters
        ----------
        name : str
            Name of the list node.
        tmpl : dict
            Template dictionary for this node.

        Returns
        -------
        dict or None
            Processed list node or None if no valid keys.
        """
        node = {"_tag": "list", "_name": name, "_children": []}

        # Handle _do directives at list level
        do_cmds = tmpl.get("_do", [])
        if do_cmds:
            for cmd in do_cmds:
                cmd = cmd.strip()
                if cmd.startswith("setdb"):
                    pass  # We always use main DB
                elif cmd.startswith("exclude"):
                    self._handle_exclude(cmd)
                elif cmd.startswith("namesunique"):
                    pass  # Validation only
                elif cmd.startswith("isinmaps"):
                    pass  # Validation only
                elif cmd.startswith("setvar"):
                    self._handle_setvar(cmd)
                elif cmd.startswith("getvar"):
                    self._handle_getvar(cmd)
                elif cmd.startswith("matmap"):
                    children = self._handle_matmap(cmd)
                    if children:
                        node["_children"].extend(children)
                elif cmd.startswith("fuelmap"):
                    children = self._handle_fuelmap(cmd)
                    if children:
                        node["_children"].extend(children)
                elif cmd.startswith("cellsmaps"):
                    children = self._handle_cellsmaps(cmd)
                    if children:
                        node["_children"].extend(children)
                elif cmd.startswith("mpact_mesh"):
                    children = self._handle_mpact_mesh(cmd)
                    if children:
                        node["_children"].extend(children)
                elif cmd.startswith("blademaps"):
                    children = self._handle_blademaps(cmd)
                    if children:
                        node["_children"].extend(children)
                elif cmd.startswith("axialtype"):
                    self._handle_axialtype(cmd)
                elif cmd.startswith("clearvar"):
                    self._handle_clearvar(cmd)
                elif cmd.startswith("sourcemap"):
                    pass  # Not commonly used

        # Handle _tr (template repetition)
        tr = tmpl.get("_tr")
        content = tmpl.get("_content", {})

        if tr:
            loop_var = tr.get("_name", "_loop")
            loop_src = tr.get("_content", "")
            loop_keys = self._resolve_tr_keys(loop_src)

            if not loop_keys:
                return None

            for lk in loop_keys:
                old_vars = dict(self._vars)
                self._vars[loop_var] = lk

                for child_name, child_tmpl in (content or {}).items():
                    if child_name.startswith("_"):
                        continue
                    if not isinstance(child_tmpl, dict):
                        continue

                    resolved_name = self._substitute_vars(child_name)
                    result = self._process_node(resolved_name, child_tmpl)
                    if result is not None:
                        node["_children"].append(result)

                self._vars = old_vars
        else:
            for child_name, child_tmpl in (content or {}).items():
                if child_name.startswith("_"):
                    continue
                if not isinstance(child_tmpl, dict):
                    continue

                resolved_name = self._substitute_vars(child_name)
                result = self._process_node(resolved_name, child_tmpl)
                if result is not None:
                    node["_children"].append(result)

        # Trim empty children
        node["_children"] = [c for c in node["_children"] if self._is_nonempty(c)]

        return node if node["_children"] else None

    def _process_node(self, name: str, tmpl: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Process a single template node based on its _pltype.

        Parameters
        ----------
        name : str
            Name of the node.
        tmpl : dict
            Template dictionary for this node.

        Returns
        -------
        dict or None
            Processed node or None if no valid keys.
        """
        pltype = tmpl.get("_pltype", "")

        if pltype == "list":
            return self._process_list(name, tmpl)
        if pltype == "parameter":
            return self._process_parameter(name, tmpl)
        if pltype == "array":
            return self._process_array(name, tmpl)
        return None

    def _process_parameter(self, name: str, tmpl: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Process a parameter-type template node.

        Parameters
        ----------
        name : str
            Name of the parameter node.
        tmpl : dict
            Template dictionary for this node.

        Returns
        -------
        dict or None
            Processed parameter node or None if no valid keys.
        """
        dtype = tmpl.get("_type", "string")
        do_cmds = tmpl.get("_do", [])

        for cmd in do_cmds:
            cmd = cmd.strip()
            val = self._execute_do_cmd(cmd, "parameter")
            if val is not None:
                if isinstance(val, list):
                    val = " ".join(str(v) for v in val)
                return {"_tag": "param", "_name": name, "_type": dtype, "_val": str(val)}

        return None

    def _process_array(self, name: str, tmpl: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Process an array-type template node.

        Parameters
        ----------
        name : str
            Name of the array node.
        tmpl : dict
            Template dictionary for this node.

        Returns
        -------
        dict or None
            Processed array node or None if no valid keys.
        """
        dtype = tmpl.get("_type", "string")
        do_cmds = tmpl.get("_do", [])

        for cmd in do_cmds:
            cmd = cmd.strip()
            val = self._execute_do_cmd(cmd, "array")
            if val is not None:
                if not isinstance(val, list):
                    val = [val]
                if val:
                    return {"_tag": "array", "_name": name, "_type": dtype, "_val": [str(v) for v in val]}

        return None

    # =========================================================================
    # _do command execution
    # =========================================================================

    def _execute_do_cmd(self, cmd: str, context_type: str = "parameter") -> Any:
        """Execute a single _do command and return the value.

        Parameters
        ----------
        cmd : str
            The _do command string (e.g. ``'copy CORE/$power'``).
        context_type : str, optional
            Either ``'parameter'`` or ``'array'`` (default ``'parameter'``).

        Returns
        -------
        Any
            Resolved value, or None if the command produced no output.
        """
        cmd = self._substitute_vars(cmd)

        if cmd.startswith("copy "):
            return self._do_copy(cmd[5:], context_type)
        if cmd.startswith("copyarray "):
            return self._do_copyarray(cmd[10:])
        if cmd.startswith("copytable "):
            return self._do_copytable(cmd[10:])
        if cmd.startswith("value "):
            return self._do_value(cmd[6:])
        if cmd.startswith("tocelsius "):
            return self._do_tocelsius(cmd[10:])
        if cmd.startswith("coremapmap "):
            return self._do_coremapmap(cmd[11:])
        if cmd.startswith("makemap "):
            return self._do_makemap(cmd[8:])
        if cmd.startswith("matmap "):
            return None  # Handled at list level
        if cmd.startswith("fuelmap "):
            return None  # Handled at list level
        if cmd.startswith("cellsmaps "):
            return None  # Handled at list level
        if cmd.startswith("setvar "):
            self._handle_setvar("setvar " + cmd[7:])
            return None
        if cmd.startswith("getvar "):
            self._handle_getvar("getvar " + cmd[7:])
            return None
        if cmd.startswith("exclude "):
            self._handle_exclude("exclude " + cmd[8:])
            return None

        return None

    # =========================================================================
    # _do directive implementations
    # =========================================================================

    def _do_copy(self, args_str: str, context_type: str = "parameter") -> Any:
        """Handle 'copy' directive.

        Parameters
        ----------
        args_str : str
            Path and options string (e.g. ``'CORE/$power,apply=>...'``).
        context_type : str, optional
            Either ``'parameter'`` or ``'array'`` (default ``'parameter'``).

        Returns
        -------
        Any
            Resolved and optionally transformed value, or None.
        """
        path_str, opts = self._split_path_opts(args_str)
        if context_type == "array":
            val = self._resolve_path_list(path_str)
        else:
            val = self._resolve_path(path_str)
        if val is None:
            return None

        # Apply section extraction (split by '/' separators, pick section N)
        if isinstance(val, list) and "section" in opts:
            sections = [[]]
            for v in val:
                if v == "/":
                    sections.append([])
                else:
                    sections[-1].append(v)
            sec_idx = int(opts["section"])
            if sec_idx < len(sections):
                val = sections[sec_idx]
            else:
                return None
            # Apply isection (skip first N elements within the selected section)
            if "isection" in opts:
                isec = int(opts["isection"])
                val = val[isec:]

        # Apply select option (select=>even or select=>odd)
        if isinstance(val, list) and "select" in opts:
            sel = opts["select"]
            if sel == "even":
                val = val[0::2]
            elif sel == "odd":
                val = val[1::2]

        # Apply start/stride slicing (e.g. start=>0,stride=>2)
        if isinstance(val, list) and ("start" in opts or "stride" in opts):
            start = int(opts.get("start", 0))
            stride = int(opts.get("stride", 1))
            val = val[start::stride]

        # Apply transform
        apply_expr = opts.get("apply")
        if apply_expr:
            val = self._apply_transform(apply_expr, val)
            if isinstance(val, float):
                val = self._format_number(val)

        # For array context, return list as-is
        if context_type == "array" and isinstance(val, list):
            return val

        # For parameter context, join list values with space
        if isinstance(val, list):
            return " ".join(str(v) for v in val)
        return val

    def _do_copyarray(self, args_str: str) -> Optional[list[str]]:
        """Handle 'copyarray' directive.

        Parameters
        ----------
        args_str : str
            Path and options string.

        Returns
        -------
        list of str or None
            Resolved list of values with slicing applied, or None.
        """
        path_str, opts = self._split_path_opts(args_str)
        val = self._resolve_path_list(path_str)
        if val is None:
            return None
        if not isinstance(val, list):
            val = [val]

        result = list(val)

        # Apply start
        start = opts.get("start")
        if start is not None:
            start = int(start)
            result = result[start:]

        # Apply length
        length = opts.get("length")
        if length is not None:
            result = result[: int(length)]

        # Apply stride
        stride = opts.get("stride")
        if stride is not None:
            result = result[:: int(stride)]

        # Apply select
        select = opts.get("select")
        if select:
            orig = list(val)
            start_int = int(start) if start is not None else 0
            if select.lower() == "even":
                result = orig[start_int::2]
            elif select.lower() == "odd":
                result = orig[start_int + 1 :: 2]

        return result if result else None

    def _do_copytable(self, args_str: str) -> Optional[list[str]]:
        """Handle 'copytable' directive.

        The raw table data from the parser is: [col1,...,col_nc, y1, d11,...,d1nc, y2, d21,...].
        Use _line_lengths metadata to determine the number of columns and rows.

        Parameters
        ----------
        args_str : str
            Path and options string (expects ``columns``, ``rows``, or ``data`` option).

        Returns
        -------
        list of str or None
            Requested table component (columns, rows, or data), or None.
        """
        path_str, opts = self._split_path_opts(args_str)

        # Resolve path to get the dict entry (with _line_lengths metadata)
        # The path typically uses @ prefix like CORE/@bypass_flow_table
        # Strip @ to get the raw dict, then extract _content and _line_lengths
        raw_path = path_str.replace("/@", "/")
        if raw_path.startswith("@"):
            raw_path = raw_path[1:]
        entry = self._resolve_path(raw_path)

        if entry is None:
            return None

        if isinstance(entry, dict):
            val = entry.get("_content", [])
            line_lengths = entry.get("_line_lengths")
        elif isinstance(entry, list):
            val = entry
            line_lengths = None
        else:
            return None

        if not isinstance(val, list) or len(val) < 2:
            return None

        # Determine nc from line lengths if available
        if line_lengths and len(line_lengths) >= 2:
            nc = line_lengths[0]
            nr = len(line_lengths) - 1
        else:
            # Fallback: try to find nc from data structure
            total = len(val)
            nc = None
            nr = None
            for try_nc in range(1, total):
                remaining = total - try_nc
                if remaining > 0 and remaining % (try_nc + 1) == 0:
                    nc = try_nc
                    nr = remaining // (try_nc + 1)
                    break
            if nc is None or nr is None:
                return None

        # Extract columns (first nc values)
        columns = val[:nc]
        rest = val[nc:]

        # Extract rows and data from interleaved format
        rows = []
        data = []
        for r in range(nr):
            offset = r * (nc + 1)
            if offset + 1 + nc <= len(rest):
                rows.append(rest[offset])
                data.extend(rest[offset + 1 : offset + 1 + nc])

        if "columns" in opts:
            return columns
        if "rows" in opts:
            return rows
        if "data" in opts:
            return data

        return None

    def _do_value(self, args_str: str) -> str:
        """Handle 'value' directive - returns a literal value.

        Parameters
        ----------
        args_str : str
            Literal value string.

        Returns
        -------
        str
            The trimmed literal value.
        """
        return args_str.strip()

    def _do_tocelsius(self, args_str: str) -> Optional[str]:
        """Handle 'tocelsius' directive.

        Parameters
        ----------
        args_str : str
            Path and options string pointing to a temperature value with unit.

        Returns
        -------
        str or None
            Temperature converted to Celsius as a formatted string, or None.
        """
        path_str, opts = self._split_path_opts(args_str)
        val = self._resolve_path(path_str)
        if val is None:
            return None
        if isinstance(val, dict):
            val = val.get("_content", [])
        if not isinstance(val, list) or len(val) < 2:
            return None

        temp_val = float(val[0])
        unit = val[1].strip().upper()

        if unit == "F":
            celsius = (temp_val - 32.0) / 1.8
        elif unit == "K":
            celsius = temp_val - 273.15
        elif unit == "C":
            celsius = temp_val
        else:
            return None

        apply_expr = opts.get("apply")
        if apply_expr:
            celsius = self._apply_transform(apply_expr, celsius)

        return self._format_number(celsius)

    def _do_coremapmap(self, args_str: str) -> Optional[list[str]]:
        """Handle 'coremapmap' directive.

        Parameters
        ----------
        args_str : str
            Comma-separated paths for core size, shape, map, and bc_sym.

        Returns
        -------
        list of str or None
            Expanded core map, or None if inputs are missing.
        """
        parts_str, opts = self._split_path_opts(args_str)
        parts = [p.strip() for p in parts_str.split(",")]
        if len(parts) < 4:
            return None

        size_val = self._resolve_path_scalar(parts[0])
        shape_val = self._resolve_path_list(parts[1])
        map_val = self._resolve_path_list(parts[2])
        bcsym_val = self._resolve_path_scalar(parts[3]) if len(parts) > 3 else "rot"

        if size_val is None or shape_val is None or map_val is None:
            return None

        csize = int(size_val)
        bc_sym = bcsym_val if bcsym_val else "rot"

        return self._core_map(shape_val, map_val, csize, bc_sym, opts)

    def _do_makemap(self, args_str: str) -> Optional[list[str]]:
        """Handle 'makemap' directive.

        Parameters
        ----------
        args_str : str
            Comma-separated paths for npin, map data, and bc_sym.

        Returns
        -------
        list of str or None
            Expanded pin-level map, or None if inputs are missing.
        """
        parts_str, _ = self._split_path_opts(args_str)
        parts = [p.strip() for p in parts_str.split(",")]
        if len(parts) < 3:
            return None

        npin_val = self._resolve_path_scalar(parts[0])
        map_val = self._resolve_path_list(parts[1])
        bcsym_val = self._resolve_path_scalar(parts[2]) if len(parts) > 2 else "rot"

        if npin_val is None or map_val is None:
            return None

        npin = int(npin_val)
        bc_sym = bcsym_val if bcsym_val else "rot"

        if bc_sym == "mir":
            return self._fullcellmap(npin, map_val)
        return self._fullcellmap_rot(npin, map_val)

    # =========================================================================
    # List-level _do handlers (matmap, fuelmap, cellsmaps)
    # =========================================================================

    def _handle_matmap(self, cmd: str) -> list[dict[str, Any]]:
        """Handle 'matmap' directive - creates Material_ sublists.

        Parameters
        ----------
        cmd : str
            Full matmap command string.

        Returns
        -------
        list of dict
            List of Material ParameterList XML node dicts.
        """
        # matmap Material_,CORE/%mat/*
        cmd = self._substitute_vars(cmd)
        m = re.match(r"matmap\s+(\S+),(.+)", cmd)
        if not m:
            return []
        prefix = m.group(1)
        path_pattern = m.group(2).strip()

        mat_db = self._resolve_path(path_pattern.rstrip("/*"))
        if mat_db is None or not isinstance(mat_db, dict):
            return []

        # Get CORE material DB for inheriting isotopes from short-form materials
        core_mat_db = self._resolve_path("CORE/mat")
        if not isinstance(core_mat_db, dict):
            core_mat_db = {}

        children = []
        for mat_name in sorted(mat_db.keys()):
            if mat_name.startswith("_"):
                continue
            mat_entry = mat_db[mat_name]
            content = mat_entry.get("_content", []) if isinstance(mat_entry, dict) else []
            params = mat_entry.get("_parameters", {}) if isinstance(mat_entry, dict) else {}

            # If material has only density (short-form), inherit isotopes from CORE
            content_no_slash = [c for c in content if c != "/"]
            if len(content_no_slash) <= 1 and mat_name in core_mat_db:
                core_entry = core_mat_db[mat_name]
                if isinstance(core_entry, dict):
                    core_content = core_entry.get("_content", [])
                    core_params = core_entry.get("_parameters", {})
                    if len([c for c in core_content if c != "/"]) > 1:
                        # Replace density with local density, keep isotopes
                        new_content = list(core_content)
                        if content_no_slash:
                            new_content[0] = content_no_slash[0]
                        content = new_content
                        # Merge params: local params override core params
                        merged_params = dict(core_params)
                        merged_params.update(params)
                        params = merged_params

            mat_node = self._build_material_node(prefix + mat_name, mat_name, content, params)
            if mat_node:
                children.append(mat_node)

        return children

    def _handle_fuelmap(self, cmd: str) -> list[dict[str, Any]]:
        """Handle 'fuelmap' directive - creates Fuel_ sublists.

        Parameters
        ----------
        cmd : str
            Full fuelmap command string.

        Returns
        -------
        list of dict
            List of Fuel ParameterList XML node dicts.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"fuelmap\s+(\S+),(.+)", cmd)
        if not m:
            return []
        prefix = m.group(1)
        path_pattern = m.group(2).strip()

        fuel_db = self._resolve_path(path_pattern.rstrip("/*"))
        if fuel_db is None or not isinstance(fuel_db, dict):
            return []

        children = []
        for fuel_name in sorted(fuel_db.keys()):
            if fuel_name.startswith("_"):
                continue
            fuel_entry = fuel_db[fuel_name]
            content = fuel_entry.get("_content", []) if isinstance(fuel_entry, dict) else []
            params = fuel_entry.get("_parameters", {}) if isinstance(fuel_entry, dict) else {}

            fuel_node = self._build_fuel_node(prefix + fuel_name, fuel_name, content, params)
            if fuel_node:
                children.append(fuel_node)

        return children

    def _handle_cellsmaps(self, cmd: str) -> list[dict[str, Any]]:
        """Handle 'cellsmaps' directive - creates CellMaps and Cells sublists.

        Parameters
        ----------
        cmd : str
            Full cellsmaps command string.

        Returns
        -------
        list of dict
            List containing CellMaps and Cells ParameterList XML node dicts.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"cellsmaps\s+(.+)", cmd)
        if not m:
            return []

        # Gate on _axtyp: if set, only run when _axtyp == 'rodmap'
        if "_axtyp" in self._vars:
            if self._vars["_axtyp"] != "rodmap":
                return []

        args_str = m.group(1)
        positional, kw_opts = self._parse_positional_and_kw(args_str)

        if len(positional) < 4:
            return []

        rodmap_path = positional[0]
        cell_path = positional[1]
        npin_path = positional[2]
        axial_path = positional[3]
        matsearch_paths = kw_opts.get("matsearch", "")

        # Get npin
        npin_val = self._resolve_path_scalar(npin_path)
        if npin_val is None:
            return []
        npin = int(npin_val)

        # Get axial content
        axial_ref = self._resolve_path(axial_path)
        if axial_ref is None:
            return []
        if isinstance(axial_ref, dict):
            axial_content = axial_ref.get("_content", [])
        else:
            axial_content = axial_ref if isinstance(axial_ref, list) else []

        axial_labels = axial_content[1::2]
        axial_labels_unique = list(dict.fromkeys(axial_labels))

        # Gather fuel material names for cell type detection
        fuel_names = set()
        if matsearch_paths:
            for search_path in matsearch_paths.split(":"):
                search_path = search_path.strip()
                if "fuel" in search_path.lower() or "%fuel" in search_path:
                    ref = self._resolve_path(search_path.rstrip("/*"))
                    if ref and isinstance(ref, dict):
                        fuel_names.update(k for k in ref.keys() if not k.startswith("_"))

        # Get rodmap/lattice data
        rodmap_ref = self._resolve_path(rodmap_path)
        cell_ref = self._resolve_path(cell_path)

        if rodmap_ref is None or cell_ref is None:
            return []

        if not isinstance(rodmap_ref, dict) or not isinstance(cell_ref, dict):
            return []

        # Build CellMaps
        cellmaps_node = {"_tag": "list", "_name": "CellMaps", "_children": []}
        all_used_cells = []

        for label in axial_labels_unique:
            if label not in rodmap_ref or label.startswith("_"):
                continue
            rm_entry = rodmap_ref[label]
            rm_content = rm_entry.get("_content", []) if isinstance(rm_entry, dict) else []

            expanded = self._fullcellmap(npin, rm_content)

            cm_node = {"_tag": "list", "_name": f"CellMap_{label}", "_children": []}
            cm_node["_children"].append({"_tag": "array", "_name": "cell_map", "_type": "string", "_val": expanded})
            cm_node["_children"].append({"_tag": "param", "_name": "label", "_type": "string", "_val": label})
            cellmaps_node["_children"].append(cm_node)

            # Track cells used (from UNEXPANDED map)
            for c in rm_content:
                if c != "-" and c not in all_used_cells:
                    all_used_cells.append(c)

        # Build Cells
        cells_node = {"_tag": "list", "_name": "Cells", "_children": []}
        for cell_label in all_used_cells:
            if cell_label not in cell_ref or cell_label.startswith("_"):
                continue
            cell_entry = cell_ref[cell_label]
            cell_content = cell_entry.get("_content", []) if isinstance(cell_entry, dict) else []

            cell_node = self._build_cell_node(cell_label, cell_content, fuel_names, prefix="Cell")
            if cell_node:
                cells_node["_children"].append(cell_node)

        result = []
        if cellmaps_node["_children"]:
            result.append(cellmaps_node)
        if cells_node["_children"]:
            result.append(cells_node)
        return result

    def _handle_axialtype(self, cmd: str) -> None:
        """Handle 'axialtype' directive.

        Sets the ``_axtyp`` variable based on whether axial labels match
        rodmap names or bladetype names.

        Parameters
        ----------
        cmd : str
            Full axialtype command string.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"axialtype\s+(.+)", cmd)
        if not m:
            return

        args_str = m.group(1)
        positional, _ = self._parse_positional_and_kw(args_str)
        if len(positional) < 4:
            return

        varname = positional[0]
        cellmap_path = positional[1]
        blade_path = positional[2]
        axial_path = positional[3]

        # Get axial content
        axial_ref = self._resolve_path(axial_path)
        if axial_ref is None:
            return
        if isinstance(axial_ref, dict):
            axial_content = axial_ref.get("_content", [])
        else:
            axial_content = axial_ref if isinstance(axial_ref, list) else []

        axial_labels = axial_content[1::2]
        axial_labels_unique = list(dict.fromkeys(axial_labels))

        # Get available rodmap labels
        cellmap_ref = self._resolve_path(cellmap_path)
        cellmap_available = []
        if cellmap_ref and isinstance(cellmap_ref, dict):
            cellmap_available = [k for k in cellmap_ref.keys() if not k.startswith("_")]

        # Get available bladetype labels
        blademap_ref = self._resolve_path(blade_path)
        blademap_available = []
        if blademap_ref and isinstance(blademap_ref, dict):
            blademap_available = [k for k in blademap_ref.keys() if not k.startswith("_")]

        # Check which set matches all axial labels
        cellmap_common = [l for l in axial_labels_unique if l in cellmap_available]
        blademap_common = [l for l in axial_labels_unique if l in blademap_available]

        if len(cellmap_common) == len(axial_labels_unique):
            self._vars[varname] = "rodmap"
        elif len(blademap_common) == len(axial_labels_unique):
            self._vars[varname] = "bladetype"

    def _handle_clearvar(self, cmd: str) -> None:
        """Handle 'clearvar' directive - removes a variable.

        Parameters
        ----------
        cmd : str
            Full clearvar command string.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"clearvar\s+(\S+)", cmd)
        if not m:
            return
        varname = m.group(1)
        self._vars.pop(varname, None)

    def _handle_blademaps(self, cmd: str) -> list[dict[str, Any]]:
        """Handle 'blademaps' directive - creates BladeTypes, BladeGeoms, BladeCells sublists.

        Parameters
        ----------
        cmd : str
            Full blademaps command string.

        Returns
        -------
        list of dict
            List of BladeTypes, BladeGeoms, and BladeCells XML node dicts.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"blademaps\s+(.+)", cmd)
        if not m:
            return []

        # Gate on _axtyp: if set, only run when _axtyp == 'bladetype'
        if "_axtyp" in self._vars:
            if self._vars["_axtyp"] != "bladetype":
                return []

        args_str = m.group(1)
        positional, kw_opts = self._parse_positional_and_kw(args_str)

        if len(positional) < 4:
            return []

        blade_path = positional[0]
        blade_geom_path = positional[1]
        cell_path = positional[2]
        axial_path = positional[3]
        matsearch_paths = kw_opts.get("matsearch", "")

        # Get axial content
        axial_ref = self._resolve_path(axial_path)
        if axial_ref is None:
            return []
        if isinstance(axial_ref, dict):
            axial_content = axial_ref.get("_content", [])
        else:
            axial_content = axial_ref if isinstance(axial_ref, list) else []

        axial_labels = axial_content[1::2]
        axial_labels_unique = list(dict.fromkeys(axial_labels))

        # Resolve bladetype, bladegeom, and cell references
        blademap_ref = self._resolve_path(blade_path)
        blade_geommap_ref = self._resolve_path(blade_geom_path)
        cell_ref = self._resolve_path(cell_path)

        if blademap_ref is None or not isinstance(blademap_ref, dict):
            return []
        if blade_geommap_ref is None or not isinstance(blade_geommap_ref, dict):
            return []
        if cell_ref is None or not isinstance(cell_ref, dict):
            return []

        # Gather fuel material names for cell type detection
        fuel_names = set()
        if matsearch_paths:
            for search_path in matsearch_paths.split(":"):
                search_path = search_path.strip()
                if not search_path:
                    continue
                parent_path = search_path.rstrip("/*")
                ref = self._resolve_path(parent_path)
                if ref and isinstance(ref, dict):
                    for k in ref:
                        if k.startswith("_"):
                            continue
                        # Check if this is under a "fuel" path section
                        if "fuel" in parent_path.lower():
                            fuel_names.add(k)

        # Collect bladetype entries that match axial labels
        blademap_common = [l for l in axial_labels_unique if l in blademap_ref and not l.startswith("_")]

        # Collect all referenced blade geom labels and blade cell labels
        all_geom_labels = []
        all_cell_labels = []
        blademap_content = {}
        for label in blademap_common:
            entry = blademap_ref[label]
            content = entry.get("_content", []) if isinstance(entry, dict) else []
            blademap_content[label] = content
            # content[0] = bladegeomlabel, [1] = blademat, [2] = tubeorient, [3] = ntube, [4:] = tubecell labels
            if content:
                geom_label = content[0]
                if geom_label not in all_geom_labels:
                    all_geom_labels.append(geom_label)
                ntube = int(content[3]) if len(content) > 3 else 0
                for i in range(4, 4 + ntube):
                    if i < len(content):
                        cell_label = content[i]
                        if cell_label not in all_cell_labels:
                            all_cell_labels.append(cell_label)

        # Build BladeTypes list
        bladetypes_node = {"_tag": "list", "_name": "BladeTypes", "_children": []}
        for label in blademap_common:
            content = blademap_content[label]
            bt_node = {"_tag": "list", "_name": f"BladeType_{label}", "_children": []}
            bt_node["_children"].append(
                {"_tag": "param", "_name": "bladegeomlabel", "_type": "string", "_val": content[0] if content else ""}
            )
            bt_node["_children"].append(
                {"_tag": "param", "_name": "blademat", "_type": "string", "_val": content[1] if len(content) > 1 else ""}
            )
            bt_node["_children"].append({"_tag": "param", "_name": "label", "_type": "string", "_val": label})
            ntube = int(content[3]) if len(content) > 3 else 0
            bt_node["_children"].append({"_tag": "param", "_name": "ntube", "_type": "int", "_val": str(ntube)})
            tube_cells = content[4 : 4 + ntube] if len(content) > 4 else []
            bt_node["_children"].append({"_tag": "array", "_name": "tubecells", "_type": "string", "_val": tube_cells})
            bt_node["_children"].append(
                {"_tag": "param", "_name": "tubeorient", "_type": "string", "_val": content[2] if len(content) > 2 else ""}
            )
            bladetypes_node["_children"].append(bt_node)

        # Build BladeGeoms list
        bladegeoms_node = {"_tag": "list", "_name": "BladeGeoms", "_children": []}
        for geom_label in all_geom_labels:
            if geom_label not in blade_geommap_ref:
                continue
            entry = blade_geommap_ref[geom_label]
            content = entry.get("_content", []) if isinstance(entry, dict) else []
            bg_node = {"_tag": "list", "_name": f"BladeGeom_{geom_label}", "_children": []}
            bg_node["_children"].append({"_tag": "param", "_name": "label", "_type": "string", "_val": geom_label})
            bg_node["_children"].append(
                {
                    "_tag": "param",
                    "_name": "sheaththickness",
                    "_type": "double",
                    "_val": content[3] if len(content) > 3 else "0",
                }
            )
            bg_node["_children"].append(
                {"_tag": "param", "_name": "span", "_type": "double", "_val": content[0] if content else "0"}
            )
            bg_node["_children"].append(
                {"_tag": "param", "_name": "thickness", "_type": "double", "_val": content[1] if len(content) > 1 else "0"}
            )
            bg_node["_children"].append(
                {"_tag": "param", "_name": "tipradius", "_type": "double", "_val": content[2] if len(content) > 2 else "0"}
            )
            bg_node["_children"].append(
                {"_tag": "param", "_name": "winglength", "_type": "double", "_val": content[4] if len(content) > 4 else "0"}
            )
            bladegeoms_node["_children"].append(bg_node)

        # Build BladeCells list
        bladecells_node = {"_tag": "list", "_name": "BladeCells", "_children": []}
        for cell_label in all_cell_labels:
            if cell_label not in cell_ref:
                continue
            cell_entry = cell_ref[cell_label]
            cell_content = cell_entry.get("_content", []) if isinstance(cell_entry, dict) else []
            cell_node = self._build_cell_node(cell_label, cell_content, fuel_names, prefix="BladeCell", append_mod=True)
            if cell_node:
                bladecells_node["_children"].append(cell_node)

        result = []
        if bladecells_node["_children"]:
            result.append(bladecells_node)
        if bladegeoms_node["_children"]:
            result.append(bladegeoms_node)
        if bladetypes_node["_children"]:
            result.append(bladetypes_node)
        return result

    def _handle_mpact_mesh(self, cmd: str) -> list[dict[str, Any]]:
        """Handle 'mpact_mesh' directive - creates pinmesh sublists.

        Parameters
        ----------
        cmd : str
            Full mpact_mesh command string.

        Returns
        -------
        list of dict
            List of pinmesh ParameterList XML node dicts.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"mpact_mesh\s+(\S+),(.+)", cmd)
        if not m:
            return []
        basename = m.group(1)
        paths = [p.strip() for p in m.group(2).split(",")]

        children = []
        for path in paths:
            # Strip trailing /* to get the parent dict
            path = re.sub(r"/\*$", "", path)
            # Resolve the path to find the mesh group
            resolved = self._resolve_path(path)
            if resolved is None or not isinstance(resolved, dict):
                continue

            for mesh_name, mesh_data in sorted(resolved.items()):
                if mesh_name.startswith("_"):
                    continue
                if not isinstance(mesh_data, dict):
                    continue
                content = mesh_data.get("_content", [])
                if not content:
                    continue

                # Count slashes
                slash_indices = [i for i, v in enumerate(content) if v == "/"]
                node = {"_tag": "list", "_name": basename + mesh_name, "_children": []}
                node["_children"].append({"_tag": "param", "_name": "label", "_type": "string", "_val": mesh_name})

                if len(slash_indices) == 1:
                    # Split by slash: part1=num_rad, part2=num_theta
                    si = slash_indices[0]
                    num_rad = content[:si]
                    num_theta = content[si + 1 :]
                    node["_children"].append({"_tag": "array", "_name": "num_rad", "_type": "int", "_val": num_rad})
                    node["_children"].append({"_tag": "array", "_name": "num_theta", "_type": "int", "_val": num_theta})
                elif len(slash_indices) == 0 and len(content) == 2:
                    # Rectangular mesh: nx, ny
                    node["_children"].append({"_tag": "param", "_name": "nx", "_type": "int", "_val": content[0]})
                    node["_children"].append({"_tag": "param", "_name": "ny", "_type": "int", "_val": content[1]})
                else:
                    continue

                children.append(node)

        return children

    # =========================================================================
    # Material / Fuel / Cell node builders
    # =========================================================================

    def _build_material_node(
        self, node_name: str, mat_name: str, content: list[str], params: Optional[dict[str, str]] = None
    ) -> Optional[dict[str, Any]]:
        """Build a Material ParameterList XML node.

        Parameters
        ----------
        node_name : str
            XML node name (e.g. ``'Material_zirc'``).
        mat_name : str
            Material key name.
        content : list of str
            Content tokens: density followed by interleaved isotope/fraction pairs.
        params : dict of str, optional
            Key-value parameters (e.g. thexp, depletable).

        Returns
        -------
        dict or None
            Material XML node dict, or None if content is empty.
        """
        if not content:
            return None
        if params is None:
            params = {}

        density = content[0]
        rest = content[1:]

        # Strip trailing / separator
        while rest and rest[-1] == "/":
            rest = rest[:-1]

        mat_names = []
        mat_fracs = []
        if len(rest) >= 2:
            mat_names = rest[0::2]
            mat_fracs = rest[1::2]
        elif len(rest) == 1:
            mat_names = [rest[0]]
            mat_fracs = ["1"]
        else:
            mat_names = [mat_name]
            mat_fracs = ["1"]

        node = {"_tag": "list", "_name": node_name, "_children": []}

        if "depletable" in params:
            node["_children"].append({"_tag": "param", "_name": "depletable", "_type": "bool", "_val": params["depletable"]})

        node["_children"].append({"_tag": "param", "_name": "density", "_type": "double", "_val": density})
        node["_children"].append({"_tag": "param", "_name": "key_name", "_type": "string", "_val": mat_name})
        node["_children"].append({"_tag": "array", "_name": "mat_fracs", "_type": "double", "_val": mat_fracs})
        node["_children"].append({"_tag": "array", "_name": "mat_names", "_type": "string", "_val": mat_names})

        if "form" in params:
            node["_children"].append({"_tag": "param", "_name": "form", "_type": "string", "_val": params["form"]})
        if "thcnd" in params:
            node["_children"].append({"_tag": "param", "_name": "thcnd", "_type": "double", "_val": params["thcnd"]})
        if "thexp" in params:
            node["_children"].append({"_tag": "param", "_name": "thexp", "_type": "double", "_val": params["thexp"]})

        return node

    def _build_fuel_node(
        self, node_name: str, fuel_name: str, content: list[str], params: Optional[dict[str, str]] = None
    ) -> Optional[dict[str, Any]]:
        """Build a Fuel ParameterList XML node.

        Parameters
        ----------
        node_name : str
            XML node name (e.g. ``'Fuel_U31'``).
        fuel_name : str
            Fuel key name.
        content : list of str
            Content tokens: density thden / enrichments [/ gad].
        params : dict of str, optional
            Key-value parameters (e.g. enr_ratio, form).

        Returns
        -------
        dict or None
            Fuel XML node dict, or None if content is empty.
        """
        if not content:
            return None
        if params is None:
            params = {}

        # content after _key removal: density thden / enrichments [/ gad]
        parts = self._split_by_slash(content)
        part1 = parts[0] if parts else []
        part2 = parts[1] if len(parts) > 1 else []
        part3 = parts[2] if len(parts) > 2 else []

        density = part1[0] if part1 else "0"
        thden = part1[1] if len(part1) > 1 else None

        # Enrichment data
        fuel_names = []
        enrichments = []
        if part2:
            # Expand NAME=value tokens into separate name, value pairs
            expanded = []
            for item in part2:
                if "=" in item:
                    n, v = item.split("=", 1)
                    expanded.extend([n, v])
                else:
                    expanded.append(item)
            items = list(expanded)
            # If first item is numeric, prepend u-235
            try:
                float(items[0])
                items = ["u-235"] + items
            except (ValueError, IndexError):
                pass
            fuel_names = items[0::2]
            enrichments = items[1::2]

        gad_mat = None
        gad_frac = None
        if part3:
            gad_mat = part3[0]
            gad_frac = part3[1] if len(part3) > 1 else None
        # Check params for gad material (key=value after slash, e.g., gad=3.0)
        non_gad_params = {"enr_ratio", "thexp", "thden", "depletable", "form"}
        for gp in sorted(params.keys()):
            if gp not in non_gad_params:
                gad_mat = gp
                gad_frac = params[gp]
                break

        node = {"_tag": "list", "_name": node_name, "_children": []}
        node["_children"].append({"_tag": "param", "_name": "density", "_type": "double", "_val": density})
        node["_children"].append({"_tag": "array", "_name": "enrichments", "_type": "double", "_val": enrichments})
        node["_children"].append({"_tag": "array", "_name": "fuel_names", "_type": "string", "_val": fuel_names})
        if gad_frac:
            node["_children"].append({"_tag": "param", "_name": "gad_frac", "_type": "double", "_val": gad_frac})
        if gad_mat:
            node["_children"].append({"_tag": "param", "_name": "gad_mat", "_type": "string", "_val": gad_mat})
        node["_children"].append({"_tag": "param", "_name": "key_name", "_type": "string", "_val": fuel_name})
        if thden:
            node["_children"].append({"_tag": "param", "_name": "thden", "_type": "double", "_val": thden})

        # Additional options from fuel definition (e.g. enr_ratio, form, thexp)
        string_params = {"form"}
        for opt_key in sorted(params.keys()):
            if opt_key not in non_gad_params and gad_mat and opt_key == gad_mat:
                continue
            opt_type = "string" if opt_key in string_params else "double"
            node["_children"].append({"_tag": "param", "_name": opt_key, "_type": opt_type, "_val": params[opt_key]})

        return node

    def _build_cell_node(
        self,
        label: str,
        content: list[str],
        fuel_names: set[str],
        prefix: str = "Cell",
        append_mod: bool = False,
    ) -> Optional[dict[str, Any]]:
        """Build a Cell or BladeCell ParameterList XML node.

        Parameters
        ----------
        label : str
            Cell label identifier.
        content : list of str
            Slash-separated cell definition tokens (radii / materials [/ type]).
        fuel_names : set of str
            Known fuel material names for cell-type detection.
        prefix : str, optional
            Node name prefix (default ``'Cell'``).
        append_mod : bool, optional
            If True, append ``'mod'`` when radii count equals materials count
            (used for blade cells).

        Returns
        -------
        dict or None
            Cell XML node dict, or None.
        """
        parts = self._split_by_slash(content)

        node = {"_tag": "list", "_name": f"{prefix}_{label}", "_children": []}
        node["_children"].append({"_tag": "param", "_name": "label", "_type": "string", "_val": label})

        if len(parts) < 2:
            return node

        radii = parts[0]
        mats = list(parts[1])

        if append_mod and len(radii) == len(mats):
            mats.append("mod")

        cell_types_possible = {"large4"}
        cell_type = "other"
        table_label = None
        if len(parts) >= 3 and parts[2]:
            if parts[2][0] in cell_types_possible:
                cell_type = parts[2][0]
            else:
                table_label = parts[2][0]

        for mat in mats:
            if mat in fuel_names:
                cell_type = "fuel"
                break

        node["_children"].append({"_tag": "array", "_name": "mats", "_type": "string", "_val": mats})
        node["_children"].append({"_tag": "param", "_name": "num_rings", "_type": "int", "_val": str(len(radii))})
        node["_children"].append({"_tag": "array", "_name": "radii", "_type": "double", "_val": radii})
        if table_label is not None:
            node["_children"].append({"_tag": "param", "_name": "table_label", "_type": "string", "_val": table_label})
        node["_children"].append({"_tag": "param", "_name": "type", "_type": "string", "_val": cell_type})

        return node

    # =========================================================================
    # Path resolution
    # =========================================================================

    def _resolve_path(self, path_str: str) -> Any:
        """Resolve a path string to a value in the DB.

        Path notation:

        - ``%name`` -> named sub-dictionary (grouped params like mat, cell)
        - ``$name`` -> scalar param's _content
        - ``@name`` -> array param's _content (returned as list)
        - ``:N``    -> index into content list
        - ``^``     -> _parameters dict

        Parameters
        ----------
        path_str : str
            KeyTree-style path string.

        Returns
        -------
        Any
            Resolved value (str, list, dict, or None).
        """
        path_str = path_str.strip()
        if not path_str:
            return None

        parts = self._tokenize_path(path_str)
        return self._navigate_db(parts)

    def _resolve_path_scalar(self, path_str: str) -> Optional[str]:
        """Resolve a path to a scalar string value.

        Parameters
        ----------
        path_str : str
            KeyTree-style path string.

        Returns
        -------
        str or None
            First element of resolved content, or None.
        """
        val = self._resolve_path(path_str)
        if val is None:
            return None
        if isinstance(val, dict):
            content = val.get("_content", [])
            if isinstance(content, list):
                return content[0] if content else None
            return content
        if isinstance(val, list):
            return val[0] if val else None
        return str(val)

    def _resolve_path_list(self, path_str: str) -> Optional[list[str]]:
        """Resolve a path to a list of values.

        Parameters
        ----------
        path_str : str
            KeyTree-style path string.

        Returns
        -------
        list of str or None
            Resolved content as a list, or None.
        """
        path_str = path_str.strip()
        if not path_str:
            return None
        parts = self._tokenize_path(path_str)
        val = self._navigate_db(parts, list_mode=True)
        if val is None:
            return None
        if isinstance(val, dict):
            content = val.get("_content", [])
            return content if isinstance(content, list) else [content]
        if isinstance(val, list):
            return val
        return [val]

    def _tokenize_path(self, path_str: str) -> list[tuple]:
        """Tokenize a path string into components.

        Parameters
        ----------
        path_str : str
            KeyTree-style path string.

        Returns
        -------
        list of tuple
            Token list where each tuple is ``(kind, name)`` or ``(kind,)``.
        """
        tokens = []
        # Split by /
        segments = path_str.split("/")
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            if seg == "*":
                tokens.append(("wildcard",))
                continue

            # Check for :N index
            idx_match = re.match(r"^(.+):(\d+)$", seg)
            if idx_match:
                base_seg = idx_match.group(1)
                index = int(idx_match.group(2))
                tokens.extend(self._parse_segment(base_seg))
                tokens.append(("index", index))
                continue

            # Check for ^ (parameters access)
            if seg.endswith("^"):
                base_seg = seg[:-1]
                # Per YAML: @name^ -> name/_parameters (not name/_content/_parameters)
                # and $name^ -> name/_parameters
                if base_seg.startswith("@") or base_seg.startswith("$"):
                    tokens.append(("key", base_seg[1:]))
                else:
                    tokens.extend(self._parse_segment(base_seg))
                tokens.append(("parameters",))
                continue

            tokens.extend(self._parse_segment(seg))

        return tokens

    def _parse_segment(self, seg: str) -> list[tuple[str, str]]:
        """Parse a single path segment with prefix.

        Parameters
        ----------
        seg : str
            Single path segment (e.g. ``'%mat'``, ``'$power'``, ``'@axial'``).

        Returns
        -------
        list of tuple
            Single-element list with ``(kind, name)`` tuple.
        """
        if seg.startswith("%"):
            return [("named", seg[1:])]
        if seg.startswith("$"):
            return [("scalar", seg[1:])]
        if seg.startswith("@"):
            return [("content", seg[1:])]
        return [("key", seg)]

    def _navigate_db(self, tokens: list[tuple], list_mode: bool = False) -> Any:
        """Navigate the DB following token path.

        Parameters
        ----------
        tokens : list of tuple
            Token list from ``_tokenize_path``.
        list_mode : bool, optional
            If True, ``$`` tokens return ``_content`` as a list
            instead of ``_content[0]`` (default False).

        Returns
        -------
        Any
            Resolved value, or None if path not found.
        """
        current = self._db
        i = 0
        while i < len(tokens):
            if current is None:
                return None

            tok = tokens[i]
            kind = tok[0]

            if kind == "key":
                name = tok[1]
                if isinstance(current, dict):
                    if name in current:
                        current = current[name]
                    else:
                        return None
                else:
                    return None

            elif kind == "named":
                # %name -> access the named group dict
                name = tok[1]
                if isinstance(current, dict):
                    if name in current:
                        current = current[name]
                    else:
                        return None
                else:
                    return None

            elif kind == "scalar":
                # $name -> get _content[0] of param (or full _content in list_mode)
                # $ alone (empty name) -> no-op, stay at current level
                name = tok[1]
                if not name:
                    i += 1
                    continue
                # If the next token is an index, resolve as list so index can work
                next_is_index = i + 1 < len(tokens) and tokens[i + 1][0] == "index"
                use_list = list_mode or next_is_index
                if isinstance(current, dict):
                    if name in current:
                        val = current[name]
                        if isinstance(val, dict):
                            content = val.get("_content", [])
                            if use_list:
                                current = content if isinstance(content, list) else [content]
                            elif isinstance(content, list) and len(content) >= 1:
                                current = content[0]
                            else:
                                current = content
                        elif isinstance(val, list):
                            if use_list:
                                current = val
                            else:
                                current = val[0] if val else None
                        else:
                            current = val
                    else:
                        return None
                else:
                    return None

            elif kind == "content":
                # @name -> get _content as list
                # @ alone (empty name) -> no-op
                name = tok[1]
                if not name:
                    i += 1
                    continue
                if isinstance(current, dict):
                    if name in current:
                        val = current[name]
                        if isinstance(val, dict):
                            current = val.get("_content", [])
                        elif isinstance(val, list):
                            current = val
                        else:
                            current = [val]
                    else:
                        return None
                else:
                    return None

            elif kind == "index":
                idx = tok[1]
                if isinstance(current, list):
                    if idx < len(current):
                        current = current[idx]
                    else:
                        return None
                elif isinstance(current, dict):
                    content = current.get("_content", [])
                    if isinstance(content, list) and idx < len(content):
                        current = content[idx]
                    else:
                        return None
                else:
                    return None

            elif kind == "parameters":
                if isinstance(current, dict):
                    current = current.get("_parameters", {})
                else:
                    return None

            elif kind == "wildcard":
                # Skip wildcard - just continue into next level
                # This is used in patterns like %ASSEMBLY/*/$/%axial
                # The * means "any key at this level"
                if isinstance(current, dict):
                    # Get all non-underscore keys
                    keys = [k for k in current if not k.startswith("_")]
                    if keys:
                        current = current[keys[0]]
                    else:
                        return None
                else:
                    return None

            i += 1

        return current

    # =========================================================================
    # Variable handling
    # =========================================================================

    def _handle_setvar(self, cmd: str) -> None:
        """Handle setvar directive.

        Plain form stores the RAW path string (after variable substitution) as
        the variable value -- it does NOT resolve the path through the data
        structure. ``apply=>&findfirst`` searches for a matching *key* and
        stores the path to it. ``apply=>&resolve`` is the other direction:
        it resolves an already-fully-specified path to its scalar *value*
        (via ``_resolve_path_scalar``, the same resolution every ``copy``
        parameter node already uses) and stores that -- which is what lets a
        later command's ``$(var)`` substitution turn a parsed value (e.g. one
        keyword's content referencing another keyword by name) into a usable
        path segment, something no other combination of existing verbs can
        do (they only ever search for or manipulate path *text*).

        Parameters
        ----------
        cmd : str
            Full setvar command string.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"setvar\s+(\w+),(.+)", cmd)
        if not m:
            return
        var_name = m.group(1)
        rest = m.group(2).strip()

        # Split off apply=> options
        apply_match = re.search(r",apply=>(.+)", rest)
        if apply_match:
            path = rest[: apply_match.start()]
            apply_expr = apply_match.group(1)
        else:
            path = rest
            apply_expr = None

        if apply_expr and "findfirst" in apply_expr:
            val = self._find_first_path(path)
            if val:
                self._vars[var_name] = val
            return

        if apply_expr and "resolve" in apply_expr:
            val = self._resolve_path_scalar(path)
            if val is not None:
                self._vars[var_name] = str(val)
            return

        # Store the raw path string
        self._vars[var_name] = path

    def _handle_getvar(self, cmd: str) -> None:
        """Handle getvar directive.

        Parameters
        ----------
        cmd : str
            Full getvar command string.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"getvar\s+(\w+),apply=>(.+)", cmd)
        if not m:
            return
        var_name = m.group(1)
        apply_expr = m.group(2)

        val = self._vars.get(var_name)
        if val is None:
            return

        # Handle pathlevel
        pl_match = re.search(r"pathlevel.*arg=>(\d+)", apply_expr)
        if pl_match:
            arg = int(pl_match.group(1))
            # Extract the Nth level from the path
            path_parts = [p for p in val.split("/") if p]
            if arg <= len(path_parts):
                self._vars[var_name] = path_parts[arg - 1]
            return

        # Other applies
        result = self._apply_transform(apply_expr, val)
        if result is not None:
            self._vars[var_name] = str(result)

    def _handle_exclude(self, cmd: str) -> None:
        """Handle exclude directive.

        Parameters
        ----------
        cmd : str
            Full exclude command string.
        """
        cmd = self._substitute_vars(cmd)
        m = re.match(r"exclude\s+(.+)", cmd)
        if m:
            for path in m.group(1).split(","):
                self._excludes.add(path.strip())

    def _find_first_path(self, path_pattern: str) -> Optional[str]:
        """Find the first matching path (for findfirst apply).

        Generates path with ``_key``/``_content`` levels to
        match the YAML path format used by pathlevel.

        For path ``%ASSEMBLY/*/$/%axial/A1`` in YAML, parse_path produces::

            ASSEMBLY/_key/*/_content/axial/_key/A1

        Result: ``ASSEMBLY/_key/1/_content/axial/_key/A1``
        So ``pathlevel(3) = "1"``.

        Parameters
        ----------
        path_pattern : str
            Path pattern with optional wildcards.

        Returns
        -------
        str or None
            First matching YAML-compatible path, or None.
        """
        parts = path_pattern.split("/")
        if not parts:
            return None

        return self._find_first_path_recursive(self._db, parts, 0, [])

    def _find_first_path_recursive(self, current: Any, parts: list[str], idx: int, result_path: list[str]) -> Optional[str]:
        """Recursively search for first matching path, expanding wildcards.

        Parameters
        ----------
        current : Any
            Current position in the DB hierarchy.
        parts : list of str
            Path segments to match.
        idx : int
            Current index into *parts*.
        result_path : list of str
            Accumulated YAML-compatible path segments.

        Returns
        -------
        str or None
            Joined path string on success, or None.
        """
        if current is None:
            return None
        if idx >= len(parts):
            return "/".join(result_path)

        part = parts[idx].strip()
        if not part:
            return self._find_first_path_recursive(current, parts, idx + 1, result_path)

        if part == "*":
            if isinstance(current, dict):
                keys = sorted(k for k in current if not k.startswith("_"))
                for k in keys:
                    result = self._find_first_path_recursive(current[k], parts, idx + 1, result_path + [k])
                    if result is not None:
                        return result
            return None
        if part.startswith("%"):
            name = part[1:]
            if isinstance(current, dict) and name in current:
                return self._find_first_path_recursive(current[name], parts, idx + 1, result_path + [name, "_key"])
            return None
        if part == "$":
            return self._find_first_path_recursive(current, parts, idx + 1, result_path + ["_content"])
        if part.startswith("$"):
            name = part[1:]
            if isinstance(current, dict) and name in current:
                new_path = result_path + [name, "_content"]
                val = current[name]
                if isinstance(val, dict):
                    next_cur = val.get("_content", [])
                    if isinstance(next_cur, list) and next_cur:
                        next_cur = next_cur[0]
                else:
                    next_cur = val
                return self._find_first_path_recursive(next_cur, parts, idx + 1, new_path)
            if isinstance(current, dict):
                for k in sorted(current.keys()):
                    if k.startswith("_"):
                        continue
                    subval = current[k]
                    if isinstance(subval, dict):
                        key = subval.get("_key")
                        if key == name:
                            return self._find_first_path_recursive(subval, parts, idx + 1, result_path + [k])
            return None
        if part.startswith("@"):
            name = part[1:]
            if isinstance(current, dict) and name in current:
                return self._find_first_path_recursive(current[name], parts, idx + 1, result_path + [name])
            return None
        if isinstance(current, dict) and part in current:
            return self._find_first_path_recursive(current[part], parts, idx + 1, result_path + [part])
        return None

    def _substitute_vars(self, text: str) -> str:
        """Substitute ``$(_varname)`` and ``(_varname)`` with variable values.

        Parameters
        ----------
        text : str
            Text containing variable references.

        Returns
        -------
        str
            Text with variables substituted.
        """

        def repl_dollar(m):
            var = m.group(1)
            return self._vars.get(var, m.group(0))

        def repl_bare(m):
            var = m.group(1)
            if var in self._vars:
                return self._vars[var]
            return m.group(0)

        # First substitute $(_varname) patterns
        text = re.sub(r"\$\((\w+)\)", repl_dollar, text)
        # Then substitute bare (_varname) patterns (used in template node names)
        text = re.sub(r"\((\w+)\)", repl_bare, text)
        return text

    # =========================================================================
    # _tr resolution
    # =========================================================================

    def _resolve_tr_keys(self, path_str: str) -> list[str]:
        """Resolve template repetition keys, collecting across all wildcard matches.

        Parameters
        ----------
        path_str : str
            KeyTree-style path string (may contain variables and wildcards).

        Returns
        -------
        list of str
            Unique keys in insertion order.
        """
        path_str = self._substitute_vars(path_str)
        parts = self._tokenize_path(path_str)

        # Collect terminal keys by expanding wildcards into all matches
        results = self._collect_keys_wildcard(self._db, parts, 0)
        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for k in results:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        return ordered

    def _collect_keys_wildcard(self, current: Any, tokens: list[tuple], i: int) -> list[str]:
        """Navigate tokens collecting terminal dict keys, expanding wildcards.

        Parameters
        ----------
        current : Any
            Current position in the DB hierarchy.
        tokens : list of tuple
            Token list from ``_tokenize_path``.
        i : int
            Current index into *tokens*.

        Returns
        -------
        list of str
            Collected keys from all matching paths.
        """
        if current is None:
            return []
        if i >= len(tokens):
            if isinstance(current, dict):
                return [k for k in current if not k.startswith("_")]
            return []

        tok = tokens[i]
        kind = tok[0]

        if kind == "wildcard":
            if isinstance(current, dict):
                all_keys = []
                for k in current:
                    if k.startswith("_"):
                        continue
                    all_keys.extend(self._collect_keys_wildcard(current[k], tokens, i + 1))
                return all_keys
            return []

        # For non-wildcard tokens, navigate normally
        next_current = self._navigate_single_step(current, tok)
        return self._collect_keys_wildcard(next_current, tokens, i + 1)

    def _navigate_single_step(self, current: Any, tok: tuple) -> Any:
        """Navigate a single token step, returning the result.

        Parameters
        ----------
        current : Any
            Current position in the DB hierarchy.
        tok : tuple
            Single token ``(kind, name)`` or ``(kind,)``.

        Returns
        -------
        Any
            Value after navigating one step, or None.
        """
        kind = tok[0]
        if kind in ("key", "named"):
            name = tok[1]
            if isinstance(current, dict) and name in current:
                return current[name]
        elif kind == "scalar":
            name = tok[1]
            if not name:
                return current
            if isinstance(current, dict) and name in current:
                val = current[name]
                if isinstance(val, dict):
                    content = val.get("_content", [])
                    return content[0] if isinstance(content, list) and content else content
                return val
        elif kind == "content":
            name = tok[1]
            if not name:
                return current
            if isinstance(current, dict) and name in current:
                val = current[name]
                if isinstance(val, dict):
                    return val.get("_content", [])
                return val
        elif kind == "parameters":
            if isinstance(current, dict):
                return current.get("_parameters", {})
        elif kind == "index":
            idx = tok[1]
            if isinstance(current, list) and idx < len(current):
                return current[idx]
            if isinstance(current, dict):
                content = current.get("_content", [])
                if isinstance(content, list) and idx < len(content):
                    return content[idx]
        return None

    # =========================================================================
    # Map expansion utilities
    # =========================================================================

    def _fullcellmap(self, npin: int, cellmap: list[str]) -> list[str]:
        """Expand partial cellmap to full npin x npin (mirror symmetry).

        Parameters
        ----------
        npin : int
            Number of pins per side.
        cellmap : list of str
            Partial cellmap (octant, quarter, diagonal, or full).

        Returns
        -------
        list of str
            Full ``npin * npin`` cellmap.
        """
        n_total = npin * npin
        n_input = len(cellmap)
        if n_input == n_total:
            return list(cellmap)
        if n_input == self._qtr_size(npin):
            return self._gen_quad_list(npin, cellmap)
        if n_input == self._oct_size(npin):
            return self._gen_oct_list(npin, cellmap)
        if n_input == self._dia_size(npin):
            return self._gen_dia_list(npin, cellmap)
        return list(cellmap)

    def _fullcellmap_rot(self, npin: int, cellmap: list[str]) -> list[str]:
        """Expand partial cellmap to full npin x npin (rotational symmetry).

        Parameters
        ----------
        npin : int
            Number of pins per side.
        cellmap : list of str
            Partial cellmap (quarter or octant).

        Returns
        -------
        list of str
            Full ``npin * npin`` cellmap.
        """
        n_total = npin * npin
        n_input = len(cellmap)
        if n_input == n_total:
            return list(cellmap)
        if n_input == self._qtr_size(npin):
            return self._gen_quad_list_rot(npin, cellmap)
        if n_input == self._oct_size(npin):
            return self._gen_oct_list(npin, cellmap)
        return list(cellmap)

    @staticmethod
    def _dia_size(size: int) -> int:
        """Diagonal symmetry size: n*(n+1)/2.

        Parameters
        ----------
        size : int
            Side length of the map.

        Returns
        -------
        int
            Number of elements in the lower triangle.
        """
        return size * (size + 1) // 2

    @staticmethod
    def _half_size(size: int) -> int:
        """Compute the half-dimension used for symmetry expansion."""
        return (size - 1) // 2 + 1 if size % 2 == 1 else size // 2

    @staticmethod
    def _symmetric_bounds(size: int) -> list:
        """Build the symmetric index bounds array used by map expansion."""
        ibound = size // 2
        if size % 2 == 1:
            return list(range(-ibound, ibound + 1))
        ibound -= 1
        neg: list = list(range(-ibound, 1))
        neg[-1] = -0.1
        pos = [-x for x in reversed(neg)]
        return neg + pos

    @staticmethod
    def _qtr_size(size: int) -> int:
        """Quarter symmetry size."""
        half = XMLGenerator._half_size(size)
        return half * half

    @staticmethod
    def _oct_size(size: int) -> int:
        """Octant symmetry size."""
        half = XMLGenerator._half_size(size)
        return half * (half + 1) // 2

    @staticmethod
    def _extract_map(core_arr: list[str], n: int, maptype: str) -> list[str]:
        """Extract octant or quarter from center of NxN array.

        Parameters
        ----------
        core_arr : list of str
            Flat NxN core array.
        n : int
            Side length of the array.
        maptype : str
            ``'OCTANT'`` or ``'QUARTER'``.

        Returns
        -------
        list of str
            Extracted sub-map.
        """
        nhalf = n // 2
        icenter = nhalf * n + nhalf
        if n % 2 == 0:
            nhalf -= 1
        result = []
        if maptype == "OCTANT":
            for i in range(nhalf + 1):
                for j in range(i + 1):
                    result.append(core_arr[icenter + i * n + j])
        elif maptype == "QUARTER":
            for i in range(nhalf + 1):
                for j in range(nhalf + 1):
                    result.append(core_arr[icenter + i * n + j])
        return result

    def _gen_oct_list(self, size: int, cellmap: list[str]) -> list[str]:
        """Expand octant map to full map (mirror symmetry).

        Parameters
        ----------
        size : int
            Side length of the full map.
        cellmap : list of str
            Triangular octant data.

        Returns
        -------
        list of str
            Full ``size * size`` map.
        """
        half = self._half_size(size)

        # Build 2D octant array (triangular)
        oct_data = []
        idx = 0
        for row in range(half):
            row_data = []
            for _ in range(row + 1):
                row_data.append(cellmap[idx] if idx < len(cellmap) else "-")
                idx += 1
            oct_data.append(row_data)

        bounds = self._symmetric_bounds(size)

        # Generate full map using octant mirror symmetry
        result = []
        for i in bounds:
            for j in bounds:
                ai = abs(int(i))
                aj = abs(int(j))
                r = max(ai, aj)
                c = min(ai, aj)
                if r < len(oct_data) and c < len(oct_data[r]):
                    result.append(oct_data[r][c])
                else:
                    result.append("-")
        return result

    @staticmethod
    def _gen_dia_list(size: int, cellmap: list[str]) -> list[str]:
        """Expand diagonal symmetry map to full map.

        Input is a lower-triangular list: row 0 has 1 element, row 1 has 2,
        etc.  For ``(i, j)``: if ``j <= i`` use ``part[i][j]``, else use
        ``part[j][i]``.

        Parameters
        ----------
        size : int
            Side length of the full map.
        cellmap : list of str
            Lower-triangular data.

        Returns
        -------
        list of str
            Full ``size * size`` map.
        """
        # Partition into rows of increasing size
        parts = []
        idx = 0
        for row in range(size):
            row_data = []
            for _ in range(row + 1):
                row_data.append(cellmap[idx] if idx < len(cellmap) else "-")
                idx += 1
            parts.append(row_data)

        # Generate full map
        result = []
        for i in range(size):
            for j in range(size):
                if j <= i:
                    result.append(parts[i][j])
                else:
                    result.append(parts[j][i])
        return result

    def _gen_quad_list(self, size: int, cellmap: list[str]) -> list[str]:
        """Expand quarter map to full map (mirror symmetry).

        Parameters
        ----------
        size : int
            Side length of the full map.
        cellmap : list of str
            Quarter-map data.

        Returns
        -------
        list of str
            Full ``size * size`` map.
        """
        half = self._half_size(size)

        # Build 2D quarter array
        qtr = []
        idx = 0
        for _ in range(half):
            row_data = []
            for _ in range(half):
                row_data.append(cellmap[idx] if idx < len(cellmap) else "-")
                idx += 1
            qtr.append(row_data)

        bounds = self._symmetric_bounds(size)

        # Generate full map using mirror symmetry
        result = []
        for i in bounds:
            for j in bounds:
                ai = abs(int(i))
                aj = abs(int(j))
                if ai < len(qtr) and aj < len(qtr[0]):
                    result.append(qtr[ai][aj])
                else:
                    result.append("-")
        return result

    def _gen_quad_list_rot(self, size: int, cellmap: list[str]) -> list[str]:
        """Expand quarter map to full map (rotational symmetry).

        Parameters
        ----------
        size : int
            Side length of the full map.
        cellmap : list of str
            Quarter-map data.

        Returns
        -------
        list of str
            Full ``size * size`` map.
        """
        half = self._half_size(size)

        # Build 2D quarter array
        qtr = []
        idx = 0
        for _ in range(half):
            row_data = []
            for _ in range(half):
                row_data.append(cellmap[idx] if idx < len(cellmap) else "-")
                idx += 1
            qtr.append(row_data)

        bounds = self._symmetric_bounds(size)

        # Rotational symmetry index mapping
        def rot_index(ibar, jbar):
            # SE quadrant (default): ibar>=0, jbar>=0 → region 1
            ai = abs(ibar)
            aj = abs(jbar)
            if ibar >= 0 and jbar >= 0:
                return qtr[ai][aj] if ai < len(qtr) and aj < len(qtr[0]) else "-"
            if ibar < 0 <= jbar:
                # NE → region 2: rotate 90 CW
                return qtr[aj][ai] if aj < len(qtr) and ai < len(qtr[0]) else "-"
            if ibar < 0 and jbar < 0:
                # NW → region 3: rotate 180
                return qtr[ai][aj] if ai < len(qtr) and aj < len(qtr[0]) else "-"
            # SW → region 4: rotate 270 CW
            return qtr[aj][ai] if aj < len(qtr) and ai < len(qtr[0]) else "-"

        result = []
        for i in bounds:
            for j in bounds:
                result.append(rot_index(i, j))
        return result

    def _core_map(
        self, core_shape: list[str], map_data: list[str], csize: int, bc_sym: str, opts: Optional[dict[str, str]] = None
    ) -> list[str]:
        """Expand a core-level map using core shape.

        Parameters
        ----------
        core_shape : list of str
            Flat core shape array (``'0'`` for empty, non-zero for active).
        map_data : list of str
            Map values to fill into the active positions.
        csize : int
            Core side length.
        bc_sym : str
            Boundary-condition symmetry (``'mir'`` or ``'rot'``).
        opts : dict, optional
            Options dict (keys: ``'ignore'``, ``'expand'``).

        Returns
        -------
        list of str
            Expanded core map with empty positions removed.
        """
        if opts is None:
            opts = {}

        # Convert core_shape to markers
        core = []
        for v in core_shape:
            if str(v) == "0":
                core.append("_EMPTY_")
            else:
                core.append("_USED_")

        nfull = sum(1 for v in core if v == "_USED_")

        # Extract octant and quarter from core shape
        core_map_o = self._extract_map(core, csize, "OCTANT")
        noct = sum(1 for v in core_map_o if v == "_USED_")
        core_map_q = self._extract_map(core, csize, "QUARTER")
        nquad = sum(1 for v in core_map_q if v == "_USED_")

        nmmap = len(map_data)
        ignore = opts.get("ignore", "-")
        # Strip surrounding quotes from ignore value
        if len(ignore) >= 2 and ignore[0] in ("'", '"') and ignore[-1] == ignore[0]:
            ignore = ignore[1:-1]
        do_expand = opts.get("expand", "1") != "0"

        fullm = list(core)

        if nmmap == noct:
            # Fill values into octant shape
            resmap = self._fillin(core_map_o, map_data)
            if not do_expand:
                self._replace_in_array(fullm, "_USED_", ignore)
                self._map_on_core(fullm, csize, resmap, "OCTANT")
            else:
                # Octant symmetry is always mirror
                fullm = self._fullcellmap(csize, resmap)
        elif nmmap == nquad:
            # Fill values into quarter shape
            resmap = self._fillin(core_map_q, map_data)
            if not do_expand:
                self._replace_in_array(fullm, "_USED_", ignore)
                self._map_on_core(fullm, csize, resmap, "QUARTER")
            else:
                if bc_sym == "mir":
                    fullm = self._fullcellmap(csize, resmap)
                else:
                    fullm = self._fullcellmap_rot(csize, resmap)
        elif nmmap == nfull:
            fullm = list(map_data)
        else:
            return list(map_data)

        # Handle empty entries based on expansion mode
        if do_expand:
            return [v for v in fullm if v != "_EMPTY_"]

        # expand=0: keep only active positions (where shape!=0), purge empty
        return [v for v in fullm if v != "_EMPTY_"]

    @staticmethod
    def _fillin(shape: list[str], values: list[str]) -> list[str]:
        """Replace ``_USED_`` entries with values from list, ``_EMPTY_`` stays.

        Parameters
        ----------
        shape : list of str
            Shape template containing ``'_USED_'`` and ``'_EMPTY_'`` markers.
        values : list of str
            Values to fill into ``'_USED_'`` positions.

        Returns
        -------
        list of str
            Filled shape.
        """
        result = []
        idx = 0
        for v in shape:
            if v == "_USED_":
                result.append(values[idx] if idx < len(values) else "-")
                idx += 1
            else:
                result.append("_EMPTY_")
        return result

    @staticmethod
    def _replace_in_array(arr: list[str], from_val: str, to_val: str) -> None:
        """Replace all occurrences of *from_val* with *to_val* in-place.

        Parameters
        ----------
        arr : list of str
            Array to modify in-place.
        from_val : str
            Value to search for.
        to_val : str
            Replacement value.
        """
        for i, v in enumerate(arr):
            if v == from_val:
                arr[i] = to_val

    def _map_on_core(self, core_arr: list[str], n: int, resmap: list[str], maptype: str) -> None:
        """Write *resmap* onto *core_arr* at octant/quarter positions.

        Parameters
        ----------
        core_arr : list of str
            Flat NxN core array (modified in-place).
        n : int
            Side length of the core array.
        resmap : list of str
            Values to write.
        maptype : str
            ``'OCTANT'`` or ``'QUARTER'``.
        """
        nhalf = n // 2
        icenter = nhalf * n + nhalf
        if n % 2 == 0:
            nhalf -= 1
        idx = 0
        if maptype == "OCTANT":
            for i in range(nhalf + 1):
                for j in range(i + 1):
                    core_arr[icenter + i * n + j] = resmap[idx]
                    idx += 1
        elif maptype == "QUARTER":
            for i in range(nhalf + 1):
                for j in range(nhalf + 1):
                    core_arr[icenter + i * n + j] = resmap[idx]
                    idx += 1

    # =========================================================================
    # Utility functions
    # =========================================================================

    def _apply_transform(self, apply_str: str, value: Any) -> Any:
        """Apply a YAML-style transform expression to a value.

        Parameters
        ----------
        apply_str : str
            Transform expression (e.g. ``'($_[0])*2.54'``).
        value : Any
            Input value (converted to float internally).

        Returns
        -------
        Any
            Transformed numeric result.
        """
        apply_str = apply_str.strip()
        val = float(value) if not isinstance(value, (int, float)) else value

        # ($_[0])*factor or $_[0]*factor
        m = re.match(r"\(?[\$_\[\]0]+\)?\s*\*\s*([\d.eE+\-]+)", apply_str)
        if m:
            return float(val) * float(m.group(1))

        # ($_[0]+offset) or $_[0]+offset
        m = re.match(r"\(?[\$_\[\]0]+\s*\+\s*([\d.eE+\-]+)\)?", apply_str)
        if m:
            return float(val) + float(m.group(1))

        # ($_[0])-offset
        m = re.match(r"\(?[\$_\[\]0]+\)?\s*-\s*([\d.eE+\-]+)", apply_str)
        if m:
            return float(val) - float(m.group(1))

        return val

    @staticmethod
    def _format_number(val: Any) -> str:
        """Format a numeric value to match ``%.15g`` behavior.

        Parameters
        ----------
        val : Any
            Value to format.

        Returns
        -------
        str
            Formatted string.
        """
        if isinstance(val, float):
            if val == int(val) and abs(val) < 1e15:
                return str(int(val))
            return f"{val:.15g}"
        return str(val)

    def _split_path_opts(self, args_str: str) -> tuple[str, dict[str, str]]:
        """Split a ``path,opt1=>v1,opt2=>v2`` string into path and options dict.

        Parameters
        ----------
        args_str : str
            Combined path and option string.

        Returns
        -------
        tuple of (str, dict)
            ``(path, options_dict)``.
        """
        opts = {}

        # Extract key=>value pairs
        opt_matches = list(re.finditer(r",(\w+)=>([^,]*)", args_str))
        if opt_matches:
            # Path is everything before first option
            path_end = opt_matches[0].start()
            path = args_str[:path_end].strip()
            for m in opt_matches:
                opts[m.group(1)] = m.group(2)
        else:
            path = args_str.strip()

        return path, opts

    def _parse_positional_and_kw(self, args_str: str) -> tuple[list[str], dict[str, str]]:
        """Parse positional args and ``key=>value`` keywords.

        Parameters
        ----------
        args_str : str
            Comma-separated argument string.

        Returns
        -------
        tuple of (list, dict)
            ``(positional_args, keyword_dict)``.
        """
        positional = []
        kwargs = {}

        parts = args_str.split(",")
        for part in parts:
            part = part.strip()
            kw_match = re.match(r"(\w+)=>(.+)", part)
            if kw_match:
                kwargs[kw_match.group(1)] = kw_match.group(2)
            else:
                positional.append(part)

        return positional, kwargs

    @staticmethod
    def _split_by_slash(content: list[str]) -> list[list[str]]:
        """Split a list by ``/`` delimiters.

        Parameters
        ----------
        content : list of str
            Flat list potentially containing ``'/'`` separators.

        Returns
        -------
        list of list of str
            Sub-lists split at each ``'/'``.
        """
        parts = []
        current = []
        for item in content:
            if str(item) == "/":
                parts.append(current)
                current = []
            else:
                current.append(item)
        parts.append(current)
        return parts

    @staticmethod
    def _strip_instance_suffix(key: str) -> str:
        """Strip ``_NNNN`` instance suffix from a block or parameter name.

        Parameters
        ----------
        key : str
            Key (e.g. ``'STATE_0001'`` or ``'mat_0002'``).

        Returns
        -------
        str
            Base name (e.g. ``'STATE'``).
        """
        m = re.match(r"^(.+?)_\d{4}$", key)
        return m.group(1) if m else key

    @staticmethod
    def _get_instance_num(key: str) -> Optional[int]:
        """Extract instance number from a block or parameter key.

        Parameters
        ----------
        key : str
            Key (e.g. ``'STATE_0001'``).

        Returns
        -------
        int or None
            Instance number (e.g. ``1``), or None if not instanced.
        """
        m = re.match(r"^.+?_(\d{4})$", key)
        return int(m.group(1)) if m else None

    @staticmethod
    def _is_nonempty(node: dict[str, Any]) -> bool:
        """Check if a node has meaningful content.

        Parameters
        ----------
        node : dict
            XML node dictionary.

        Returns
        -------
        bool
            True if the node contains data worth emitting.
        """
        tag = node.get("_tag")
        if tag == "param":
            return node.get("_val") is not None
        if tag == "array":
            return bool(node.get("_val"))
        if tag == "list":
            return bool(node.get("_children"))
        return False

    # =========================================================================
    # XML emission
    # =========================================================================

    def _emit(self, node: dict[str, Any], indent: int, lines: list[str]) -> None:
        """Emit a node as XML.

        Parameters
        ----------
        node : dict
            XML node dictionary with ``_tag``, ``_name``, and content keys.
        indent : int
            Current indentation level.
        lines : list of str
            Output line accumulator (modified in-place).
        """
        tag = node.get("_tag", "list")
        name = node.get("_name", "")
        prefix = "  " * indent

        if tag == "list":
            lines.append(f'{prefix}<ParameterList name="{name}">')
            children = node.get("_children", [])
            # Sort children alphabetically by name
            children_sorted = sorted(children, key=lambda c: c.get("_name", ""))
            for child in children_sorted:
                self._emit(child, indent + 1, lines)
            lines.append(f"{prefix}</ParameterList>")

        elif tag == "param":
            dtype = node.get("_type", "string")
            val = xml_escape(str(node.get("_val", "")), {'"': "&quot;"})
            lines.append(f'{prefix}<Parameter name="{name}" type="{dtype}" value="{val}"/>')

        elif tag == "array":
            dtype = node.get("_type", "string")
            vals = node.get("_val", [])
            val_str = ",".join(xml_escape(str(v), {'"': "&quot;"}) for v in vals)
            lines.append(f'{prefix}<Parameter name="{name}" type="Array({dtype})" value="{{{val_str}}}"/>')
