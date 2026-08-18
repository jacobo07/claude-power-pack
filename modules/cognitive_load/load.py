"""How much must an engineer hold in their head to change this unit?

R3 of the UPAC audit. `modules/cdio` scores what an END USER sees and
`modules/cognitive_os` governs what an AGENT's context costs. The load a codebase
places on a HUMAN who has to modify it was unscored.

    python -m modules.cognitive_load.load                 # ranked view
    python -m modules.cognitive_load.load --unit rollback
    python -m modules.cognitive_load.load --json

NON-DUPLICATION, stated because it determined the design.

`modules/uqf/anti_patterns.py` already owns FILE-LOCAL defects: bare except,
silent pass, missing type hints, magic numbers, mutable defaults, god functions
over fifty lines, hardcoded paths. Re-deriving any of those here would be a second
opinion on a question that has an owner, so none of them are computed.

What is left, and unowned, is not a property of a file at all. It is the cost of
ASSEMBLING enough context to change something: how many files you must open, how
wide the surface of the units you depend on is, and whether the unit tells you
where to start. That is the inward direction, and it is the exact complement of
`architecture_horizon`:

    architecture_horizon   if I change X, what breaks?      (dependents, outward)
    cognitive_load         to change X, what must I read?   (upstream, inward)

The dependency graph is IMPORTED from architecture_horizon rather than rebuilt.
Two import graphs in one estate would be two sources of truth for the same fact,
and the second one to drift would be silently wrong.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from modules.architecture_horizon.horizon import build_graph

PP_ROOT = Path(__file__).resolve().parents[2]

# Signals a repository cannot witness. Declared rather than omitted, so the view
# states its own ceiling -- the same discipline as dependency_sovereignty's
# withheld ladder rungs.
UNMEASURED_SIGNALS = {
    "setup_time": "needs a clean machine and a stopwatch",
    "feedback_latency": "needs the edit-run-observe loop timed in practice",
    "error_message_quality": "needs the messages a real failure produces at runtime",
    "debugging_affordances": "needs an engineer attempting a real diagnosis",
    "naming_quality": "not decidable without domain knowledge; a linter that "
                      "judged names would produce confident nonsense",
}


def _public_symbols(pkg_dir: Path) -> int:
    """Top-level public names a caller could bind to, from the package's __init__.

    `__all__` wins when present: it is the author's own statement of the surface,
    and honouring it is the difference between measuring what is exported and
    measuring what happens to be defined.
    """
    init = pkg_dir / "__init__.py"
    if not init.is_file():
        return 0
    try:
        tree = ast.parse(init.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return 0
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        return len(node.value.elts)
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if not bound.startswith("_"):
                    names.add(bound)
    return len(names)


def _declares_entry_point(pkg_dir: Path) -> bool:
    """Does the unit tell you where to start -- a package docstring or __all__?"""
    init = pkg_dir / "__init__.py"
    if not init.is_file():
        return False
    try:
        tree = ast.parse(init.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return False
    if ast.get_docstring(tree):
        return True
    return any(isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "__all__"
                       for t in n.targets)
               for n in tree.body)


def measure(root: Path | None = None) -> list:
    base = (Path(root) if root is not None else PP_ROOT)
    mods = base / "modules"
    if not mods.is_dir():
        return []
    graph = build_graph(base)
    surface = {}
    files = {}
    entry = {}
    for pkg in sorted(p for p in mods.iterdir() if p.is_dir()):
        if pkg.name.startswith((".", "__")):
            continue
        surface[pkg.name] = _public_symbols(pkg)
        files[pkg.name] = len([p for p in pkg.rglob("*.py") if p.is_file()])
        entry[pkg.name] = _declares_entry_point(pkg)

    rows = []
    for unit in sorted(graph):
        upstream = sorted(graph.get(unit, ()))
        upstream_surface = sum(surface.get(u, 0) for u in upstream)
        rows.append({
            "unit": unit,
            "files_to_read": files.get(unit, 0),
            "own_public_symbols": surface.get(unit, 0),
            "upstream_units": upstream,
            "upstream_surface": upstream_surface,
            "declares_entry_point": entry.get(unit, False),
            # A stated formula, not a fitted score: the files you must open plus
            # the exported names you must understand to use what they import.
            # Both terms are counts of things a person actually reads.
            "context_cost": files.get(unit, 0) + upstream_surface,
        })
    rows.sort(key=lambda r: (-r["context_cost"], r["unit"]))
    return rows


def undeclared_entry_points(rows: list) -> list:
    """Units with no package docstring and no __all__ -- you must read the files
    to learn where to start. The cheapest cognitive-load defect to fix."""
    return [r["unit"] for r in rows if not r["declares_entry_point"]]


def render(rows: list, top: int = 12) -> str:
    undeclared = undeclared_entry_points(rows)
    L = [f"cognitive load: {len(rows)} unit(s) measured "
         f"(inward: what you must read to change one)"]
    L.append("  ranked by context cost = files_to_read + upstream_surface:")
    for r in rows[:top]:
        mark = " " if r["declares_entry_point"] else "!"
        L.append(f"  {mark} {r['unit']:<28} cost={r['context_cost']:<5} "
                 f"files={r['files_to_read']:<4} "
                 f"upstream={len(r['upstream_units'])} unit(s)/"
                 f"{r['upstream_surface']} symbol(s)")
    if len(rows) > top:
        L.append(f"    ... {len(rows) - top} more with a lower cost "
                 "(count is exact, not truncated silently)")
    L.append(f"  '!' = no package docstring and no __all__: "
             f"{len(undeclared)} unit(s) do not say where to start")
    L.append("  signals NOT measured here:")
    for name, why in sorted(UNMEASURED_SIGNALS.items()):
        L.append(f"      {name}: {why}")
    L.append("  file-local defects (bare except, type hints, magic numbers, god "
             "functions, hardcoded paths) belong to modules/uqf and are "
             "deliberately not re-derived")
    L.append(f"COGNITIVE_LOAD units={len(rows)} "
             f"undeclared_entry_points={len(undeclared)} "
             f"max_cost={rows[0]['context_cost'] if rows else 0}")
    return "\n".join(L)


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[args.index("--root") + 1]) if "--root" in args else None
    rows = measure(root)

    if "--unit" in args:
        want = args[args.index("--unit") + 1]
        row = next((r for r in rows if r["unit"] == want), None)
        if row is None:
            print(f"{want!r} is not a package under modules/")
            return 0
        if "--json" in args:
            print(json.dumps(row, ensure_ascii=False, indent=2))
        else:
            print(f"to change {want} you must assemble:")
            print(f"  {row['files_to_read']} file(s) in the unit itself")
            print(f"  {len(row['upstream_units'])} upstream unit(s) exporting "
                  f"{row['upstream_surface']} public symbol(s): "
                  f"{', '.join(row['upstream_units']) or '(none)'}")
            print(f"  context cost {row['context_cost']}; entry point "
                  f"{'declared' if row['declares_entry_point'] else 'NOT declared'}")
        return 0

    if "--json" in args:
        print(json.dumps({"rows": rows,
                          "undeclared_entry_points": undeclared_entry_points(rows),
                          "unmeasured_signals": UNMEASURED_SIGNALS},
                         ensure_ascii=False, indent=2))
    else:
        print(render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
