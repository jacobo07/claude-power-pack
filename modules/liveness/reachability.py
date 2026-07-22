#!/usr/bin/env python3
"""reachability.py -- the discovery producer the Liveness Ledger never had.

`liveness_ledger.default_registry()` is a hand-written list. It audits only what a
human remembered to declare, so a component nobody declares is not scored UNKNOWN --
it is absent from the denominator entirely, which reads as health. That is why the
recovery ACCEPTANCE arbiter (`session_resilience/acceptance.py`) sat unwired and
unreported for weeks: never declared, therefore never missed.

This module removes the memory step. It enumerates every module under `modules/` and
computes reachability from the surfaces the harness can actually invoke, so coverage
is total BY CONSTRUCTION and every future module inherits the audit the day it lands.

Three design constraints, each paid for by a real bug:

1. GRANULARITY IS THE MODULE, NOT THE PACKAGE. The first version of this file scanned
   packages and pronounced `session_resilience` REACHABLE -- true, because two hooks
   import `power_beacon` -- while nine of its eleven modules, the acceptance arbiter
   among them, were dead. It would have missed the very bug that motivated it. A
   package is reachable if ANY module in it is; that is precisely what hides corpses.

2. LIVE SURFACES ARE POLYGLOT. `hooks/session_start_hub.js` invokes PP by embedding a
   Python import *inside a JavaScript string*. An import graph built from Python ASTs
   would call the genuinely-live `power_beacon` an orphan. References are matched as
   TEXT across .js/.md/.ps1/.json as well as .py, then closed transitively -- through
   absolute AND relative imports, because a module reached only by a relative import
   from a DEAD module is still dead.

3. THE SAFE DIRECTION IS OVER-REPORTING. A false ORPHAN costs one line in the exemption
   registry. A false REACHABLE hides a dead subsystem for months -- the exact failure
   this module exists to end. Anything unproven is ORPHAN or UNKNOWN, never REACHABLE,
   and UNKNOWN never satisfies the gate.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

REACHABLE = "REACHABLE"
ORPHAN = "ORPHAN"
UNKNOWN = "UNKNOWN"

# Exemption classes. A module may be legitimately unreachable from a live surface; it
# must then SAY SO. Silence is not an exemption.
LIBRARY = "LIBRARY"        # imported by siblings only; never an entrypoint
DEPRECATED = "DEPRECATED"  # dead on purpose, retained for history
PLANNED = "PLANNED"        # wiring pending; MUST carry an OWNER_QUEUE row
SCHEDULED = "SCHEDULED"    # driven by a scheduled task, not by the harness
VALID_CLASSES = (LIBRARY, DEPRECATED, PLANNED, SCHEDULED)

REGISTRY_REL = "vault/liveness/reachability_registry.json"

# Surfaces the harness invokes directly. tools/ is deliberately NOT seeded wholesale:
# a tool nobody calls is itself a finding, so a tool becomes a seed only when a real
# surface names it.
_SEED_GLOBS = ("hooks/*.js", "commands/*.md", "agents/*.md", "SKILL.md", "CLAUDE.md")

# THE REPO IS THE SOURCE; ~/.claude IS THE LIVE INSTALL. The harness loads hooks,
# agents and commands from there, and several of them exist ONLY there. Seeding the
# repo alone declared all nine uqf/principles orphans while two live gates were
# importing them on every Edit. Fail-open: an absent live root simply yields no
# extra seeds (a CI checkout has no ~/.claude and must still scan).
_LIVE_SEED_GLOBS = ("hooks/*.js", "commands/*.md", "agents/*.md",
                    "settings.json", "settings.local.json", "CLAUDE.md")


def live_root() -> Path:
    return Path.home() / ".claude"


# `hooks/*.js` by directory+extension alone is over-broad: a file merely sitting in
# hooks/ is not necessarily invoked by anything. The ONLY thing settings.json actually
# registers is hook-dispatcher.js; that file's own EVENT_MAP/CHAIN_MAP is the real
# registration ledger. Sealed 2026-07-22: hooks/cascade_check_bash.js was registered in
# NEITHER settings.json nor the dispatcher's chain map, yet every prior scan called it
# LIVE purely because it is a .js file living in hooks/. A hooks/*.js file counts as a
# live seed only if it IS the dispatcher itself (settings.json's real entrypoint) or its
# path is named inside the dispatcher's own registries.
_DISPATCHER_NAME = "hook-dispatcher.js"
# Broad by design: ANY quoted string ending .js, relative or absolute. Narrowing to
# `./`/`../`-prefixed refs (the dispatcher's own idiom) missed settings.json's direct
# registrations, which use absolute paths ("C:/Users/User/.claude/skills/.../foo.js")
# -- session_start_hub.js (SessionStart event) is registered THIS way, not through
# the dispatcher at all. Only the basename is ever extracted, so a broader match
# carries negligible false-whitelist risk. The optional leading/trailing `\\?`:
# settings.json's "command" value is itself a JSON string whose embedded path is
# quoted a SECOND time with escaped quotes (`\"C:/...foo.js\"`) -- the delimiter
# immediately touching ".js" is a backslash there, not a bare quote, so a plain
# ['"] boundary silently matched zero settings.json-registered hooks.
_HOOK_REF_RE = re.compile(r"""\\?['"]([^'"\\]+?\.js)\\?['"]""")


def _registered_hooks(root: Path) -> set[str]:
    """Basenames of every .js file named by a REAL registration surface: the
    dispatcher's own EVENT_MAP/CHAIN_MAP, plus settings.json / settings.local.json
    directly (some events, e.g. SessionStart, bypass the dispatcher and register a
    script straight from settings.json -- session_start_hub.js is a confirmed case).

    Filename, not resolved absolute path: a `./foo.js` reference is relative to
    wherever the dispatcher ACTUALLY runs from (~/.claude/hooks), so resolving it
    against the repo's hooks/ dir (a different directory entirely) never matches --
    that mismatch silently un-fixed the bug this function exists to fix, demoting
    genuinely-registered files (learning-sentinel.js, zero-issue-gate.js, ...) to
    false orphans the moment this ran. Basename matching sidesteps the repo-vs-
    live-install path split this whole module already has to account for (see the
    live_root() comment above). Collision risk is negligible: hooks/ is flat
    (_SEED_GLOBS globs one level, not recursive) and every hook file in this repo
    has a distinct, purpose-specific name.

    Fail-open to empty per surface: an absent/unreadable file contributes no names
    rather than raising, matching this module's fail-open contract throughout.
    """
    names: set[str] = set()
    lr = live_root()

    dispatcher = None
    for candidate in (lr / "hooks" / _DISPATCHER_NAME, root / "hooks" / _DISPATCHER_NAME):
        if candidate.is_file():
            dispatcher = candidate
            break
    if dispatcher is not None:
        text = _read(dispatcher)
        if text is not None:
            for ref in _HOOK_REF_RE.findall(text):
                names.add(ref.replace("\\", "/").rsplit("/", 1)[-1])

    for settings_name in ("settings.json", "settings.local.json"):
        settings_path = lr / settings_name
        if settings_path.is_file():
            text = _read(settings_path)
            if text is not None:
                for ref in _HOOK_REF_RE.findall(text):
                    names.add(ref.replace("\\", "/").rsplit("/", 1)[-1])

    return names

# `modules.pkg.mod`, `modules/pkg/mod`, `modules\pkg\mod` -- at ARBITRARY depth. An
# earlier version captured exactly two segments, so a reference to
# `modules.uqf.principles.false_positives_catalog` collapsed to `uqf/__init__` and every
# module in a nested subpackage (uqf/principles, pp_agents/signals, */runners) was
# reported dead. Nesting is the norm here, so depth must be unbounded.
# Hyphens included: auto-testing, arch-decision and code-review cannot be plain-imported.
_PATH_RE = re.compile(r"modules[./\\]((?:[A-Za-z0-9_\-]+[./\\])*[A-Za-z0-9_\-]+)")
# `from modules.pkg.sub import a, b as c` -- the path regex alone stops at the package.
_FROM_RE = re.compile(r"from\s+modules\.([A-Za-z0-9_.]+)\s+import\s+([^\n#]+)")
# `from . import models` / `from .acceptance import X` -- resolved against the package.
_REL_RE = re.compile(r"from\s+\.([A-Za-z0-9_]*)\s+import\s+([^\n#]+)")
_TOOL_RE = re.compile(r"tools[./\\]([A-Za-z0-9_\-]+)\.py")
# The hooks' dominant idiom builds the path in SEGMENTS -- path.join(PP_PATH, 'tools',
# 'recovery_epoch_gate.py') -- so the contiguous form above never matches them, and every
# tool a hook actually runs was read as unreachable. The probe was under-counting the very
# surfaces it exists to trace: an instrument blind to the repo's own idiom measures its
# vocabulary, not the code.
_TOOL_SEG_RE = re.compile(
    r"""['"]tools['"]\s*,\s*['"]([A-Za-z0-9_\-]+)\.py['"]""")
# The SAME segmented-path.join idiom recurs for `modules/<pkg>/.../<file>.py` (e.g.
# d2a_gate.js: path.join(PP_ROOT, 'modules', 'duplicate_to_advantage', 'd2a_engine.py')
# -- 3+ segments, not the 2-segment tools/ case above). Sealed 2026-07-22: this exact
# gap read modules/duplicate_to_advantage/d2a_engine as ORPHAN while it was being
# invoked as a subprocess on every UserPromptSubmit. Captures the run of quoted
# segments between the literal 'modules' and the final '<file>.py' as ONE blob (not
# per-repetition -- Python re keeps only the last iteration of a repeated group), then
# _refs_in_text splits that blob back into segments and joins them into a unit path.
_MODULE_SEG_RE = re.compile(
    r"""['"]modules['"]((?:\s*,\s*['"][A-Za-z0-9_\-]+['"])+)\s*,\s*['"]([A-Za-z0-9_\-]+)\.py['"]""")
_QUOTED_SEG_RE = re.compile(r"""['"]([A-Za-z0-9_\-]+)['"]""")
# A plugin loader -- `import_module(f"modules.uqf.principles.{name}")` -- is a genuine
# live reference whose target is only known at runtime. Text-matching cannot name the
# module, but it CAN name the package being loaded, so every module directly under that
# package inherits reachability from the loader. Without this, the nine uqf/principles
# read as corpses while two live gates import them on every Edit.
_DYN_RE = re.compile(r"""import_module\(\s*f?["']modules\.([A-Za-z0-9_.]+?)\.\{""")


def _repo_root() -> Path:
    return _PP_ROOT


def _read(path: Path) -> str | None:
    """Fail-open text read. utf-8-sig: cross-tool files carry a BOM."""
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def _names(blob: str) -> list[str]:
    """Split an import clause into bare names: 'a, b as c, (d)' -> [a, b, d]."""
    out = []
    for chunk in blob.replace("(", " ").replace(")", " ").split(","):
        name = chunk.strip().split(" as ")[0].strip()
        if name and name != "*":
            out.append(name)
    return out


def module_inventory(repo_root: Path | None = None) -> list[str]:
    """Every module under modules/, as 'pkg/mod' -- the full denominator.

    __init__ is included: an unreferenced package __init__ is a real signal.
    """
    root = Path(repo_root or _repo_root()) / "modules"
    if not root.is_dir():
        return []
    units = []
    for pkg in sorted(p for p in root.iterdir() if p.is_dir()):
        if not (pkg / "__init__.py").is_file():
            continue
        for src in sorted(pkg.rglob("*.py")):
            rel = src.relative_to(pkg).with_suffix("").as_posix()
            units.append(f"{pkg.name}/{rel}")
    return units


def live_seeds(repo_root: Path | None = None) -> list[Path]:
    root = Path(repo_root or _repo_root())
    registered: set[str] | None = None  # lazy -- only paid for if a hooks/*.js glob fires

    def _filter_hooks(found: list[Path]) -> list[Path]:
        nonlocal registered
        if registered is None:
            registered = _registered_hooks(root)
        return [p for p in found
                if p.name == _DISPATCHER_NAME or p.name in registered]

    seeds: list[Path] = []
    for pattern in _SEED_GLOBS:
        found = sorted(root.glob(pattern))
        seeds.extend(_filter_hooks(found) if pattern == "hooks/*.js" else found)
    lr = live_root()
    if lr.is_dir():
        for pattern in _LIVE_SEED_GLOBS:
            found = sorted(lr.glob(pattern))
            seeds.extend(_filter_hooks(found) if pattern == "hooks/*.js" else found)
    return [p for p in seeds if p.is_file()]


def _refs_in_text(text: str, known: set[str], *, pkg: str | None = None) -> set[str]:
    """Every module unit this text reaches. `pkg` enables relative-import resolution."""
    hits: set[str] = set()

    def _norm(dotted: str) -> str:
        return dotted.replace(".", "/").replace("\\", "/")

    for raw in _PATH_RE.findall(text):
        unit = _norm(raw)
        # A filesystem reference ("python modules/liveness/reachability.py") carries an
        # extension that the unbounded-depth pattern happily swallows, yielding the
        # non-unit `liveness/reachability/py`. Shed it before lookup.
        if unit.endswith("/py"):
            unit = unit[:-3]
        if unit in known:                       # modules.pkg.sub.mod
            hits.add(unit)
        elif f"{unit}/__init__" in known:       # modules.pkg.sub  (package import)
            hits.add(f"{unit}/__init__")

    # Segmented path.join construction: path.join(ROOT, 'modules', 'pkg', ..., 'f.py').
    # _PATH_RE above only matches a CONTIGUOUS literal like "modules/pkg/f.py"; a JS
    # hook that builds the path across separate string arguments never produces that
    # contiguous form, so it was invisible here even though the reference is real.
    for seg_blob, fname in _MODULE_SEG_RE.findall(text):
        segs = _QUOTED_SEG_RE.findall(seg_blob)
        if not segs:
            continue
        unit = "/".join(segs + [fname])
        if unit in known:
            hits.add(unit)
        elif f"{unit}/__init__" in known:
            hits.add(f"{unit}/__init__")

    for base, blob in _FROM_RE.findall(text):
        b = _norm(base)
        for n in _names(blob):
            if f"{b}/{n}" in known:             # from modules.pkg.sub import mod
                hits.add(f"{b}/{n}")
            elif f"{b}/{n}/__init__" in known:  # from modules.pkg import subpackage
                hits.add(f"{b}/{n}/__init__")

    if pkg:
        for sub, blob in _REL_RE.findall(text):
            if sub:                                   # from .acceptance import X
                if f"{pkg}/{sub}" in known:
                    hits.add(f"{pkg}/{sub}")
            else:                                     # from . import models, telemetry
                for n in _names(blob):
                    if f"{pkg}/{n}" in known:
                        hits.add(f"{pkg}/{n}")

    # Plugin loaders: every module directly under the dynamically-loaded package.
    for loaded in _DYN_RE.findall(text):
        prefix = loaded.replace(".", "/") + "/"
        depth = prefix.count("/")
        for unit in known:
            if unit.startswith(prefix) and unit.count("/") == depth:
                hits.add(unit)
    return hits


def _tool_seeds(texts: list[str], repo_root: Path) -> list[Path]:
    """A tool named by a live surface is itself live -- its imports carry reachability."""
    names: set[str] = set()
    for t in texts:
        names.update(_TOOL_RE.findall(t))
        names.update(_TOOL_SEG_RE.findall(t))
    return [p for p in (repo_root / "tools" / f"{n}.py" for n in sorted(names)) if p.is_file()]


def _unit_path(repo_root: Path, unit: str) -> Path:
    return repo_root / "modules" / f"{unit}.py"


def load_registry(repo_root: Path | None = None) -> dict:
    """Exemptions + the standing orphan debt. Fail-open to empty."""
    raw = _read(Path(repo_root or _repo_root()) / REGISTRY_REL)
    if raw is None:
        return {"modules": {}, "known_orphans": []}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"modules": {}, "known_orphans": []}
    data.setdefault("modules", {})
    data.setdefault("known_orphans", [])
    return data


def scan(repo_root: Path | None = None, registry: dict | None = None) -> list[dict]:
    """Reachability of every module from the live surfaces, transitively closed.

    Returns one row per module: {unit, package, status, via, klass, note}. `via` names
    the surface that PROVES reachability -- evidence, not a boolean.
    """
    root = Path(repo_root or _repo_root())
    reg = registry if registry is not None else load_registry(root)
    known = set(module_inventory(root))
    if not known:
        return []

    def _label(p: Path) -> str:
        """Evidence label. Live-install seeds sit OUTSIDE the repo -- relative_to would
        raise, so they are tagged `live:` and named by what the harness actually loads."""
        try:
            return p.relative_to(root).as_posix()
        except ValueError:
            return "live:" + p.name

    seed_texts: list[tuple[str, str]] = []
    for p in live_seeds(root):
        t = _read(p)
        if t is not None:
            seed_texts.append((_label(p), t))
    for p in _tool_seeds([t for _, t in seed_texts], root):
        t = _read(p)
        if t is not None:
            seed_texts.append((_label(p), t))

    via: dict[str, str] = {}
    frontier: list[str] = []
    for label, text in seed_texts:
        for unit in _refs_in_text(text, known):
            if unit not in via:
                via[unit] = label
                frontier.append(unit)

    # Transitive closure. A module reached only from a DEAD module stays dead: the
    # frontier only ever grows from units already proven reachable.
    while frontier:
        current = frontier.pop()
        # Package-init closure: importing modules.pkg.sub.mod always executes
        # pkg/__init__.py and pkg/sub/__init__.py first -- Python's import system
        # guarantees it regardless of whether anything explicitly imports the
        # package itself. Without this, every package __init__ read as a false
        # ORPHAN unless something happened to import the bare package too.
        parts = current.split("/")
        for depth in range(1, len(parts)):
            init_unit = "/".join(parts[:depth] + ["__init__"])
            if init_unit in known and init_unit not in via:
                via[init_unit] = f"package-init of {current}"
                frontier.append(init_unit)
        text = _read(_unit_path(root, current))
        if text is None:
            continue
        pkg = current.split("/", 1)[0]
        for unit in _refs_in_text(text, known, pkg=pkg):
            if unit not in via:
                via[unit] = f"modules/{current}"
                frontier.append(unit)

    rows: list[dict] = []
    for unit in sorted(known):
        declared = reg["modules"].get(unit) or {}
        klass = declared.get("class")
        if klass is not None and klass not in VALID_CLASSES:
            klass = None  # a malformed exemption is not an exemption
        if unit in via:
            status = REACHABLE
        elif not _unit_path(root, unit).is_file():
            status = UNKNOWN  # cannot prove anything -> never REACHABLE
        else:
            status = ORPHAN
        rows.append({
            "unit": unit,
            "package": unit.split("/", 1)[0],
            "status": status,
            "via": via.get(unit, ""),
            "klass": klass,
            "note": declared.get("note", ""),
        })
    return rows


def offenders(rows: list[dict], registry: dict | None = None,
              repo_root: Path | None = None) -> list[dict]:
    """Rows that FAIL the gate: unreachable, unclassified, not in the standing debt.

    Absolutes only -- a NAMED set of modules, never a percentage. A ratio gate is
    satisfied by growing its denominator; this one can only be satisfied by wiring the
    module or declaring why it is not wired.
    """
    reg = registry if registry is not None else load_registry(repo_root)
    baseline = set(reg.get("known_orphans", []))
    declared = reg.get("modules", {})

    def _klass(r: dict) -> str | None:
        """The registry HANDED TO THIS CALL wins over whatever scan() baked into the row.
        Otherwise passing a registry here would silently do half the job -- exemptions
        ignored, debt honoured -- and a caller would never see the difference."""
        k = (declared.get(r["unit"]) or {}).get("class", r["klass"])
        return k if k in VALID_CLASSES else None

    return [
        r for r in rows
        if r["status"] != REACHABLE
        and _klass(r) is None
        and r["unit"] not in baseline
    ]


def gate(repo_root: Path | None = None) -> tuple[bool, list[dict], list[dict]]:
    """(passed, offenders, rows). Fails CLOSED: an unscannable repo does not pass."""
    root = Path(repo_root or _repo_root())
    reg = load_registry(root)
    rows = scan(root, registry=reg)
    if not rows:
        return False, [{"unit": "<inventory>", "package": "", "status": UNKNOWN,
                        "via": "", "klass": None,
                        "note": "no modules found -- scanner cannot prove health"}], []
    offs = offenders(rows, registry=reg, repo_root=root)
    return (not offs), offs, rows


def discovered_rows(repo_root: Path | None = None) -> list[dict]:
    """Liveness-Ledger registry rows, one per module -- coverage by construction.

    This is the bridge that makes declaring optional: the ledger stops auditing what
    someone remembered and starts auditing what exists.
    """
    return [
        {
            "id": f"module:{r['unit']}",
            "surface": "reachability",
            "desc": f"modules/{r['unit']}.py -- reachable from a live surface?",
            "probe": {"type": "reachability", "unit": r["unit"]},
        }
        for r in scan(repo_root)
    ]


def _report_md(rows: list[dict], offs: list[dict]) -> str:
    n_r = sum(1 for r in rows if r["status"] == REACHABLE)
    n_o = sum(1 for r in rows if r["status"] == ORPHAN)
    n_u = sum(1 for r in rows if r["status"] == UNKNOWN)
    dead = sorted(
        (r for r in rows if r["status"] != REACHABLE and r["klass"] is None),
        key=lambda r: r["unit"],
    )
    lines = [
        "# Reachability Ledger (module granularity)",
        "",
        f"modules: {len(rows)}  |  REACHABLE: {n_r}  |  ORPHAN: {n_o}  |  UNKNOWN: {n_u}"
        f"  |  gate offenders: {len(offs)}",
        "",
        "## Unreachable and undeclared",
        "",
        "| module | status | via |",
        "|---|---|---|",
    ]
    lines += [f"| {r['unit']} | {r['status']} | {r['via'] or '-'} |" for r in dead]
    return "\n".join(lines) + "\n"


def write_baseline(repo_root: Path | None = None) -> tuple[Path, int]:
    """Freeze today's unreachable set as the STANDING DEBT, preserving declared classes.

    The debt is enumerated BY NAME, never by count: a threshold ("no more than 156
    orphans") is satisfied by deleting a module, and a ratio is satisfied by adding a
    reachable one. Only a named set forces the number to fall for the right reason.
    From here on, any NEW orphan fails the gate.
    """
    root = Path(repo_root or _repo_root())
    reg = load_registry(root)
    rows = scan(root, registry=reg)
    reg["known_orphans"] = sorted(
        r["unit"] for r in rows if r["status"] != REACHABLE and r["klass"] is None
    )
    path = root / REGISTRY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, len(reg["known_orphans"])


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--baseline" in argv:
        path, n = write_baseline()
        print(f"baseline written: {path}  ({n} modules of standing debt)")
        return 0
    passed, offs, rows = gate()
    if "--json" in argv:
        print(json.dumps({"passed": passed, "offenders": offs, "rows": rows}, indent=2))
    else:
        print(_report_md(rows, offs))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
