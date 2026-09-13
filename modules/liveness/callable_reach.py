"""Callable liveness: an exported function is not a called function.

The third rung of a ladder this package already climbed twice.

  reachability.py  -- does anything reach this MODULE?
                      Its header records the lesson that produced it: "a package is
                      reachable if ANY module in it is; that is precisely what hides
                      corpses."
  dispatch.py      -- is this registered HANDLER ever invoked?
                      Its header: "a registered handler is not an invoked handler."
  this file        -- is this exported FUNCTION ever called?

Each rung was added because the rung below it declared something healthy that was not.
Module granularity has the identical blind spot one level finer: a module with one live
caller is REACHABLE, and every other function in it is invisible to the audit -- however
long it has been dead, and however loudly the documentation claims it runs.

Measured 2026-09-13, which is why this exists. `modules/cdio/scorer.py` is reachable and
correctly classed so: `tools/design_gate.py` imports it. Of its 26 public symbols, 6 were
on the automatic path. `review_gate` -- the only function carrying the CDICF dependency
filter, the CDIO-07 conformance filter, and the conformance-aware `is_done` -- had zero
production callers, while `governance/DESIGN_GOVERNANCE.md` sec.8.2 asserted as a
normative rule that it runs at review time. Four test suites were 44/44 green throughout,
because every one of them called it directly. Nothing in the estate could see this.

A REPORTER plus a RATCHET, never a clean-bill gate. The existing population is large and
a gate that is red on arrival gets disabled inside a week, so current offenders are frozen
BY NAME with a reason each, and the gate fails when the set GROWS. It also fails on a
stale entry -- an inventory that outlives its debts becomes a permanent excuse and the
ratchet stops turning.

Imperfection points at the LOUD failure. A resolver that misses a calling shape reports a
live function as dead, which a human investigates and corrects; one that over-matches
reports a dead function as alive, which nobody ever looks at again. So an unrecognised
shape yields "no caller found", and that is a prompt to look, never a proof of death.

WHAT THIS INSTRUMENT CANNOT SEE -- read before quoting its number. The unreached count is
an UPPER BOUND on dead callables, not a census of corpses:

  1. Only PYTHON callers are resolved. A module a JS hook runs as `spawnSync(python,
     ['modules/x/y.py', ...])` has every symbol reported unreached, and this estate
     drives a great deal of Python from `hooks/*.js` in exactly that way.
  2. Shell entrypoints are invisible. `main` is excluded for that reason, but a module
     run as `python modules/x/y.py --flag` reaches other functions no import edge shows.
  3. Dynamic dispatch -- importlib, getattr, a registry keyed by string -- is invisible
     by construction. `dispatch.py` exists precisely because that shape defeats static
     reading, and the two instruments are complements, not substitutes.
  4. A class reached only through a factory, or a dataclass constructed only by the
     module defining it, reads as unreached and frequently is not.

A row here means "no Python import edge names this symbol". That is a question to ask,
not a verdict to act on -- which is why this ships as a reporter and a growth ratchet
rather than as a gate that can refuse anything.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

# Reused, never copied. These three already encode decisions -- which directories are
# live surfaces, which are noise -- that must not drift between the rungs of one ladder.
from modules.liveness.dispatch import _repo_root, _searchable_files, _SKIP_DIRS

CALLED = "CALLED"
PROSE_ONLY = "PROSE_ONLY"
TEST_ONLY = "TEST_ONLY"
NEVER = "NEVER"

UNREACHED = (PROSE_ONLY, TEST_ONLY, NEVER)

INVENTORY = Path("vault") / "liveness" / "callable_inventory.json"

# Dunder and single-underscore names are internal by convention; `main` is an entrypoint
# the shell calls, which no import edge can witness.
_ENTRYPOINTS = {"main"}


def public_symbols(py_path: Path) -> list[str]:
    """Module-level public defs and classes, enumerated STRUCTURALLY.

    Structural because the question is "what does this module export that nothing
    calls", and grepping for a name can only find the places that HAVE one -- which is
    the opposite of the question.
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return []
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_") and node.name not in _ENTRYPOINTS:
                out.append(node.name)
    return out


def alias_bindings(tree: ast.AST, dotted: str) -> set[str]:
    """Every local name this module bound to `dotted`, or to a symbol imported from it.

    THE REUSABLE PART, and the reason this is a function rather than four lines inlined
    at the call site. A receiver is whatever the importing module bound it to -- not a
    name from a hardcoded list of plausible spellings. That error was recorded on
    2026-09-10 (an AST sweep missing a dispatch through an import alias), and made again
    on 2026-09-11 in a different sweep, because the lesson had been written as prose and
    prose does not travel to the moment you type a matcher. This does.

    Handles: `import a.b.c`, `import a.b.c as x`, `from a.b import c`, `from a.b import
    c as x`, `from a.b.c import f`, and a later rebinding `g = mod.f`.
    """
    names: set[str] = set()
    for name, (mod, _sym) in bindings(tree).items():
        if mod == dotted:
            names.add(name[1:] if name.startswith("\x00") else name)
    return names


def bindings(tree: ast.AST) -> dict:
    """local name -> (module, original_symbol | None). THE one resolver.

    `alias_bindings` and `module_references` are two views of this, so a calling shape
    learned in one place is known in both. Two copies of this logic is how a sweep comes
    to understand an import form its sibling does not.

    The ORIGINAL symbol name is carried, never the local one, and that distinction is the
    whole reason this returns a pair. `from m import f as g` binds `g`, but the thing
    `m` exports is `f`: recording the local name reports `f` as uncalled and invents a
    caller for a symbol named `g` that `m` does not have. Two wrong answers from one
    slip, and the accusing one is silent.

    This is the third occurrence of the alias family in this estate -- 2026-09-10 (a
    sweep matching receivers against a hardcoded name list), 2026-09-11 (the same in a
    different sweep), and 2026-09-13, when the synthetic drill in
    tools/test_callable_reach.py caught it here before it shipped. The drill is the
    artifact that made the lesson transfer; the prose twice did not.

    Handles: `import a.b.c [as x]`, `from a.b import c [as x]`, `from a.b.c import f [as
    g]`, and a rebinding `g = mod.f`.
    """
    out: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if not mod.startswith("modules"):
                continue
            for a in node.names:
                # Ambiguous by construction: `from modules.pkg import mod` imports a
                # MODULE, `from modules.pkg.mod import f` imports a SYMBOL, and the AST
                # cannot tell them apart without resolving the package. Both readings
                # are recorded -- as a module target and as a symbol of `mod` -- because
                # the consumer looks up by the subject it is asking about, so the wrong
                # reading simply never matches.
                out[a.asname or a.name] = (f"{mod}.{a.name}", None)
                out[f"\x00{a.asname or a.name}"] = (mod, a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("modules"):
                    out[a.asname or a.name.split(".")[0]] = (a.name, None)
        elif isinstance(node, ast.Assign):
            val = node.value
            base = None
            if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Name):
                base = val.value.id
            elif isinstance(val, ast.Name):
                base = val.id
            if base in out:
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        out[t.id] = out[base]
    return out


def module_references(py_path: Path) -> dict:
    """{dotted module: {symbols this file references}} for every modules.* import.

    Parsed ONCE per file. The first version of this asked the question per (subject,
    caller) pair, which is O(modules x files) parses -- around 80,000 for this estate,
    and it does not finish. An instrument nobody can afford to run is not an instrument.
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return {}
    b = bindings(tree)
    bound = {k: v[0] for k, v in b.items() if not k.startswith("\x00")}
    sym_of = {k[1:]: v for k, v in b.items() if k.startswith("\x00")}
    if not bound:
        return {}

    hits: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in sym_of:
            # `from m import f [as g]` then a bare `g` -- record f, the name the module
            # exports, NOT g, the name this file happens to call it by.
            mod, original = sym_of[node.id]
            hits.setdefault(mod, set()).add(original)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            target = bound.get(node.value.id)
            if target:
                hits.setdefault(target, set()).add(node.attr)   # `m.f(...)`
    return hits


def _named_in_prose(symbol: str, dotted: str, blob: str) -> bool:
    """Is this callable named in documentation as something to RUN?

    PROSE_ONLY is its own state because it is the interesting one: a capability an agent
    can reach only by reading a markdown file and choosing to type a command. That is
    operator discipline, not wiring, and the distinction is exactly what separated
    `review_gate` (instructed in an agent file, never called by code) from a function
    nobody has ever mentioned.

    Deliberately narrow. A bare name appearing anywhere in any .md would match English
    words and every changelog that ever mentioned the symbol, which would launder real
    corpses into "documented". So it must appear either fully qualified, or as an
    invocation with parentheses -- both shapes a human wrote on purpose.
    """
    return f"{dotted}.{symbol}" in blob or f"{symbol}(" in blob


def _is_test(p: Path) -> bool:
    n = p.name.lower()
    return (n.startswith("test_") or n.endswith("_test.py")
            or n.endswith(".test.js") or "tests" in p.parts)


def _module_files(root: Path) -> list[Path]:
    """Subjects: non-test modules under modules/.

    Test files that live under modules/ (ccf/test_ccf.py, */_v_block-style suites) are
    excluded as SUBJECTS. Their functions are invoked by a runner, not imported, so
    counting them would add pure noise to a report whose whole value is signal -- and
    `reachability.py`'s registry already lists several of them as known orphans.
    """
    base = root / "modules"
    if not base.is_dir():
        return []
    return [p for p in base.rglob("*.py")
            if not any(d in p.parts for d in _SKIP_DIRS)
            and p.name != "__init__.py"
            and not _is_test(p)]


def _dotted(root: Path, p: Path) -> str:
    return ".".join(p.relative_to(root).with_suffix("").parts)


def scan(repo_root: Path | None = None) -> list[dict]:
    """Every public callable under modules/, and the strongest caller found for it."""
    root = Path(repo_root or _repo_root())
    subjects = _module_files(root)
    searchable = _searchable_files(root)

    prod_py = [p for p in searchable if p.suffix == ".py" and not _is_test(p)]
    test_py = [p for p in searchable if p.suffix == ".py" and _is_test(p)]
    prose = [p for p in searchable if p.suffix == ".md"]

    prose_blob = ""
    for p in prose:
        try:
            prose_blob += p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

    # One parse per caller, not one per (subject, caller) pair.
    prod_ref: dict = {}
    for p in prod_py:
        for dotted, syms in module_references(p).items():
            if _dotted(root, p) == dotted:
                continue                             # self-reference is not reach
            prod_ref.setdefault(dotted, set()).update(syms)
    test_ref: dict = {}
    for p in test_py:
        for dotted, syms in module_references(p).items():
            test_ref.setdefault(dotted, set()).update(syms)

    rows: list[dict] = []
    for subj in subjects:
        symbols = public_symbols(subj)
        if not symbols:
            continue
        dotted = _dotted(root, subj)
        unit = "/".join(subj.relative_to(root / "modules").with_suffix("").parts)
        prod_hits = prod_ref.get(dotted, set())
        test_hits = test_ref.get(dotted, set())

        for sym in symbols:
            if sym in prod_hits:
                state = CALLED
            elif _named_in_prose(sym, dotted, prose_blob):
                state = PROSE_ONLY
            elif sym in test_hits:
                state = TEST_ONLY
            else:
                state = NEVER
            rows.append({"unit": unit, "symbol": sym, "state": state,
                         "id": f"{unit}::{sym}"})
    return rows


def gaps(repo_root: Path | None = None) -> list[dict]:
    return [r for r in scan(repo_root) if r["state"] in UNREACHED]


def load_inventory(repo_root: Path | None = None) -> dict:
    root = Path(repo_root or _repo_root())
    try:
        with open(root / INVENTORY, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"frozen": {}}


def ratchet(repo_root: Path | None = None) -> dict:
    """Compare today's unreached set against the frozen inventory.

    Two failures, in opposite directions, because an inventory held from one side only
    rots or pads. NEW is debt that arrived after the freeze. STALE is an entry whose
    subject is no longer unreached -- delete it, or the list becomes a permanent excuse.
    """
    root = Path(repo_root or _repo_root())
    inv = load_inventory(root)
    frozen = set(inv.get("frozen", {}))
    today = {r["id"] for r in gaps(root)}

    new = sorted(today - frozen)
    stale = sorted(frozen - today)
    return {"new": new, "stale": stale, "frozen": len(frozen),
            "unreached_today": len(today),
            "ok": not new and not stale}


def render(res: dict) -> str:
    lines = [f"callable liveness: {res['unreached_today']} unreached, "
             f"{res['frozen']} frozen"]
    if res["new"]:
        lines.append(f"\n  NEW unreached callables ({len(res['new'])}) -- each is a "
                     f"function nothing calls, added since the freeze:")
        lines += [f"    + {i}" for i in res["new"][:40]]
        if len(res["new"]) > 40:
            lines.append(f"    ... and {len(res['new']) - 40} more")
    if res["stale"]:
        lines.append(f"\n  STALE inventory entries ({len(res['stale'])}) -- these are "
                     f"reachable now; delete them so the ratchet keeps turning:")
        lines += [f"    - {i}" for i in res["stale"][:40]]
        if len(res["stale"]) > 40:
            lines.append(f"    ... and {len(res['stale']) - 40} more")
    if res["ok"]:
        lines.append("  no new debt, no stale entries")
    return "\n".join(lines)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="An exported function is not a called function.")
    ap.add_argument("--freeze", action="store_true",
                    help="rewrite the inventory from today's unreached set")
    ap.add_argument("--list", action="store_true", help="print every unreached callable")
    args = ap.parse_args(argv)

    root = _repo_root()
    if args.list:
        for r in sorted(gaps(root), key=lambda r: r["id"]):
            print(f"{r['state']:<11} {r['id']}")
        return 0

    if args.freeze:
        rows = gaps(root)
        payload = {
            "_doc": "Frozen callable-liveness debt. The gate fails when this set GROWS "
                    "and when an entry goes stale. Clear an entry by WIRING the "
                    "callable, or DELETING it -- never by editing this file to make a "
                    "red run green.",
            "frozen": {r["id"]: f"unreached at freeze ({r['state']})"
                       for r in sorted(rows, key=lambda r: r["id"])},
        }
        path = root / INVENTORY
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"frozen {len(rows)} unreached callable(s) -> {INVENTORY}")
        return 0

    res = ratchet(root)
    print(render(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
