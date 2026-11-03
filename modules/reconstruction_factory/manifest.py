"""recon.toml: the project manifest. The ONLY source of paths, tools, flags and function lists. Unknown key = refusal.

Schema (schema = 1):
  schema            int, must be 1
  [project]         name (str), description (str, optional)
  [toolchain]       adapter  "gcc-ppc" | "mwcc"
                    cc, cxx, objdump : list of command candidates (first that resolves wins; absolute path or on PATH)
                    runner           : optional wrapper command list (mwcc only; never shipped)
                    [toolchain.recipe.<id>]  flags (list[str]), lang_flags.c / lang_flags.cxx (list[str], optional)
                    [toolchain.variant.<id>] base (recipe id), add (list[str]), drop (list[str])   -- Build Twin alternatives
  [corpus]          include (list[dir]), ref_dir, skeleton_dir, mutant_dir (optional), heldout_dir, heldout_seal (file),
                    target_dir (optional: prebuilt target objects <function>.o; absent = targets are built from ref_dir sources)
  [[function]]      name, source (file in ref_dir), recipe (recipe id), symbols (list[str]), lang "c"|"cxx" (default by extension),
                    group (optional str), heldout (bool, optional; source then lives in heldout_dir)
Relative paths resolve against the manifest's directory. Nothing else is read from anywhere.
"""
import os
import tomllib

SCHEMA = 1


class ManifestError(ValueError):
    pass


def _check(table, spec, where):
    """spec: key -> (type|tuple, required). Unknown key is a refusal; wrong type is a refusal."""
    for k in table:
        if k not in spec:
            raise ManifestError("unknown key %r in [%s]" % (k, where))
    for k, (typ, req) in spec.items():
        if k not in table:
            if req:
                raise ManifestError("missing key %r in [%s]" % (k, where))
            continue
        v = table[k]
        if not isinstance(v, typ) or (typ is int and isinstance(v, bool)):
            raise ManifestError("key %r in [%s] must be %s" % (k, where, typ.__name__ if isinstance(typ, type) else typ))


def _strs(v, where):
    if not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v):
        raise ManifestError("%s must be a non-empty list of strings" % where)


def validate(doc):
    _check(doc, {"schema": (int, True), "project": (dict, True), "toolchain": (dict, True), "corpus": (dict, True), "function": (list, True)}, "root")
    if doc["schema"] != SCHEMA:
        raise ManifestError("schema must be %d" % SCHEMA)
    _check(doc["project"], {"name": (str, True), "description": (str, False)}, "project")
    tc = doc["toolchain"]
    _check(tc, {"adapter": (str, True), "cc": (list, True), "cxx": (list, False), "objdump": (list, True), "runner": (list, False),
                "recipe": (dict, True), "variant": (dict, False)}, "toolchain")
    if tc["adapter"] not in ("gcc-ppc", "mwcc"):
        raise ManifestError("toolchain.adapter must be gcc-ppc or mwcc")
    for k in ("cc", "objdump"):
        _strs(tc[k], "toolchain." + k)
    if "cxx" in tc:
        _strs(tc["cxx"], "toolchain.cxx")
    for rid, r in tc["recipe"].items():
        if not isinstance(r, dict):
            raise ManifestError("toolchain.recipe.%s must be a table" % rid)
        _check(r, {"flags": (list, True), "lang_flags": (dict, False)}, "toolchain.recipe." + rid)
        if not all(isinstance(x, str) for x in r["flags"]):
            raise ManifestError("toolchain.recipe.%s.flags must be strings" % rid)
        for lk, lv in r.get("lang_flags", {}).items():
            if lk not in ("c", "cxx") or not isinstance(lv, list):
                raise ManifestError("toolchain.recipe.%s.lang_flags.%s invalid" % (rid, lk))
    for vid, v in tc.get("variant", {}).items():
        _check(v, {"base": (str, True), "add": (list, False), "drop": (list, False)}, "toolchain.variant." + vid)
        if v["base"] not in tc["recipe"]:
            raise ManifestError("toolchain.variant.%s.base names no recipe" % vid)
    _check(doc["corpus"], {"include": (list, True), "ref_dir": (str, True), "skeleton_dir": (str, True), "mutant_dir": (str, False),
                           "heldout_dir": (str, False), "heldout_seal": (str, False), "target_dir": (str, False)}, "corpus")
    seen = set()
    for f in doc["function"]:
        _check(f, {"name": (str, True), "source": (str, True), "recipe": (str, True), "symbols": (list, True), "lang": (str, False),
                   "group": (str, False), "heldout": (bool, False)}, "function")
        _strs(f["symbols"], "function.symbols")
        if f["recipe"] not in tc["recipe"]:
            raise ManifestError("function %s: unknown recipe %r" % (f["name"], f["recipe"]))
        if f.get("lang", "c") not in ("c", "cxx"):
            raise ManifestError("function %s: lang must be c or cxx" % f["name"])
        if f["name"] in seen:
            raise ManifestError("duplicate function %s" % f["name"])
        seen.add(f["name"])
    return doc


class Project:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.root = os.path.dirname(self.path)
        with open(self.path, "rb") as fh:
            try:
                doc = tomllib.load(fh)
            except tomllib.TOMLDecodeError as e:
                raise ManifestError("invalid TOML: %s" % e)
        self.doc = validate(doc)
        self.name = doc["project"]["name"]
        self.functions = {f["name"]: dict(f, lang=f.get("lang") or ("cxx" if f["source"].endswith((".cpp", ".cc", ".cxx")) else "c"))
                          for f in doc["function"]}

    def p(self, rel):
        return rel if os.path.isabs(rel) else os.path.join(self.root, rel)

    @property
    def include_dirs(self):
        return [self.p(d) for d in self.doc["corpus"]["include"]]

    def source_dir(self, kind):
        key = {"ref": "ref_dir", "skeleton": "skeleton_dir", "mutant": "mutant_dir", "heldout": "heldout_dir"}[kind]
        return self.p(self.doc["corpus"][key]) if key in self.doc["corpus"] else None

    def source_path(self, fn, kind="ref"):
        f = self.functions[fn]
        return os.path.join(self.source_dir("heldout" if f.get("heldout") and kind == "ref" else kind), f["source"])

    def names(self, heldout=False):
        return sorted(n for n, f in self.functions.items() if bool(f.get("heldout")) == heldout)

    def flags(self, recipe, lang, variant=None):
        tc = self.doc["toolchain"]
        base = recipe
        add, drop = [], []
        if variant:
            v = tc["variant"][variant]
            base, add, drop = v["base"], v.get("add", []), v.get("drop", [])
        r = tc["recipe"][base]
        out = [x for x in r["flags"] if x not in drop] + list(r.get("lang_flags", {}).get(lang, [])) + list(add)
        return out
