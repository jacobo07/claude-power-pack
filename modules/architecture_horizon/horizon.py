"""Which part of the architecture stops being valid first?

R2 of the UPAC audit. The brief asked for a counterfactual laboratory that models
10x/100x/1000x scale, dependency outage, multi-region and adversarial traffic. A
sweep of all 402 module files found exactly one counterfactual symbol
(`rule_compiler/effect_harness._counterfactual_ids`) and it is governance-scoped:
it replays a RULE against the incident that produced it.

    python -m modules.architecture_horizon.horizon              # ranked view
    python -m modules.architecture_horizon.horizon --invalidate decision_review
    python -m modules.architecture_horizon.horizon --gate
    python -m modules.architecture_horizon.horizon --json

WHAT THIS IS, AND DELIBERATELY IS NOT.

Scale simulation needs a running system, a load model and a traffic shape. None of
those exist in a repository, and inventing them would produce numbers with the
authority of measurement and the content of a guess. So this does not simulate.

It answers the one form of the question a repository CAN answer, structurally and
exactly: if this unit's contract changes, what else must change with it? That is
the transitive dependent closure of the real import graph. A unit with a wide
closure is one the architecture cannot cheaply revise -- it is where the
architecture stops being able to move first, which is the brief's question at the
granularity the evidence supports.

It does not duplicate:
  decision_review.compute_blast_radius  keyword surfaces over a decision's PROSE
  graphify                              knowledge coordinates, not import edges
  liveness/reachability                 surface -> module, not module -> module
  refcheck                              documentation reference integrity
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
MODULES_DIR = PP_ROOT / "modules"

# Stressors the brief names that a repository cannot witness. Declared, not
# silently omitted, so the view states its own ceiling (same discipline as
# dependency_sovereignty.UNREACHABLE_RUNGS).
UNMODELLED_STRESSORS = {
    "traffic_scale": "needs a load model and a running system",
    "latency_inflation": "needs production timing distributions",
    "multi_region": "needs a deployment topology this repo does not declare",
    "adversarial_traffic": "needs a threat model bound to a live surface",
    "data_growth": "needs production data volumes",
    "team_growth": "not a property of the code",
}


def _unit_of(path: Path, base: Path) -> str:
    """Ownership granularity is the package directory: that is what a person owns,
    what a commit touches, and what a contract change is negotiated over.

    `base` is threaded rather than read from the module constant. Binding it to
    PP_ROOT/modules made --root silently inert: every file under a different root
    raised ValueError out of relative_to, build_graph swallowed it as a skip, and
    the result was an empty graph reported as a real one. Caught by the synthetic
    fixtures, which is the reason they exist.
    """
    return path.relative_to(base).parts[0]


def _imports(path: Path, base: Path) -> set:
    """Module-package names this file imports from inside modules/.

    Both spellings are resolved because both are used in this estate:
      absolute  from modules.decision_review.x import y
      relative  from .x import y            (same package)
                from ..other.x import y     (sibling package)
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return set()

    own = _unit_of(path, base)
    # Depth of this file below its package root, so a relative level can be
    # resolved without guessing.
    depth = len(path.relative_to(base / own).parts) - 1
    out = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if len(parts) >= 2 and parts[0] == "modules":
                    out.add(parts[1])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # level 1 == this package's directory. Anything deeper walks up
                # toward modules/, and only a hop that lands ON a sibling package
                # names a different unit.
                up = node.level - 1 - depth
                if up >= 1 and node.module:
                    out.add(node.module.split(".")[0])
                continue
            if node.module:
                parts = node.module.split(".")
                if len(parts) >= 2 and parts[0] == "modules":
                    out.add(parts[1])
    return {u for u in out if u != own}


def build_graph(root: Path | None = None) -> dict:
    """unit -> set(units it depends on). Every package is a key, including leaves,
    so a unit with no dependencies is present with an empty set rather than
    absent -- absent and independent must not look alike."""
    base = (Path(root) if root is not None else PP_ROOT) / "modules"
    if not base.is_dir():
        return {}
    graph = {}
    for pkg in sorted(p for p in base.iterdir() if p.is_dir()):
        if pkg.name.startswith((".", "__")):
            continue
        graph.setdefault(pkg.name, set())
        for src in pkg.rglob("*.py"):
            if not src.is_file():
                continue
            graph[pkg.name] |= _imports(src, base)
    # An edge to a unit that is not a package (a stale or external name) is
    # dropped rather than fabricating a node for it.
    known = set(graph)
    return {u: (deps & known) for u, deps in graph.items()}


def dependents(graph: dict) -> dict:
    rev = {u: set() for u in graph}
    for unit, deps in graph.items():
        for d in deps:
            rev.setdefault(d, set()).add(unit)
    return rev


def transitive_dependents(unit: str, rev: dict) -> set:
    """Everything that must change if `unit`'s contract changes. Iterative and
    cycle-safe: this estate has import cycles and a recursive walk would not
    survive them."""
    seen, stack = set(), [unit]
    while stack:
        cur = stack.pop()
        for dep in rev.get(cur, ()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    seen.discard(unit)
    return seen


def cycles(graph: dict | None = None, root: Path | None = None) -> list:
    """Mutually-dependent groups: units that transitively reach each other.

    This is not decoration. On the first run twelve units tied at 27-29
    transitive dependents, and a bare ranking of those ties implies an ordering
    the graph does not contain: inside a mutually-dependent group there is no
    "first" to invalidate, because every member carries every other. Reporting
    the rank without the group would be a false hierarchy.

    O(n^2) over reachability rather than Tarjan: n is the number of packages
    (83 here), and a definition-shaped implementation that is obviously correct
    beats a clever one that has to be trusted.
    """
    g = graph if graph is not None else build_graph(root)
    rev = dependents(g)
    closure = {u: transitive_dependents(u, rev) for u in g}
    seen, groups = set(), []
    for unit in sorted(g):
        if unit in seen:
            continue
        group = {unit} | {other for other in closure[unit]
                          if unit in closure.get(other, ())}
        if len(group) > 1:
            groups.append(sorted(group))
            seen |= group
    groups.sort(key=lambda grp: (-len(grp), grp[0]))
    return groups


def rank(graph: dict | None = None, root: Path | None = None) -> list:
    """Units ordered by how much of the estate their invalidation carries."""
    g = graph if graph is not None else build_graph(root)
    rev = dependents(g)
    rows = []
    for unit in sorted(g):
        closure = transitive_dependents(unit, rev)
        rows.append({
            "unit": unit,
            "direct_dependents": len(rev.get(unit, ())),
            "transitive_dependents": len(closure),
            "depends_on": len(g.get(unit, ())),
            "closure": sorted(closure),
        })
    rows.sort(key=lambda r: (-r["transitive_dependents"], r["unit"]))
    return rows


def invalidate(unit: str, root: Path | None = None) -> dict:
    g = build_graph(root)
    if unit not in g:
        return {"unit": unit, "known": False, "closure": [],
                "note": f"{unit!r} is not a package under modules/"}
    rev = dependents(g)
    closure = sorted(transitive_dependents(unit, rev))
    return {"unit": unit, "known": True,
            "direct": sorted(rev.get(unit, ())),
            "closure": closure, "count": len(closure)}


# Units whose invalidation reaches this much of the estate are load-bearing by
# construction. This is a NAMED SET below, never a count or a ratio: a ratio
# falls when the estate grows and a count falls when a module is deleted, so
# only names force the number down for the right reason.
CONCENTRATION_FLOOR = 8

# The standing set, measured 2026-08-19. A unit joining this set is a real
# architectural change and should be seen; a unit leaving it means coupling was
# genuinely reduced. Both directions fail the gate, because both are news.
LOAD_BEARING_BASELINE = set()


def gate(root: Path | None = None) -> tuple:
    rows = rank(root=root)
    heavy = {r["unit"] for r in rows
             if r["transitive_dependents"] >= CONCENTRATION_FLOOR}
    if not LOAD_BEARING_BASELINE:
        # Unsealed: report, never fail. A baseline invented on the fly would
        # pin whatever today happens to be and call it intent.
        return True, heavy, rows
    return heavy == LOAD_BEARING_BASELINE, heavy, rows


def render(rows: list, heavy: set, groups: list | None = None,
           top: int = 12) -> str:
    L = [f"architecture horizon: {len(rows)} unit(s); "
         f"{len(heavy)} at or above the load-bearing floor "
         f"({CONCENTRATION_FLOOR} transitive dependents)"]
    if groups:
        biggest = groups[0]
        L.append(f"  MUTUALLY-DEPENDENT CORE: {len(groups)} group(s); the largest "
                 f"holds {len(biggest)} unit(s).")
        L.append("  Inside a group there is no unit that invalidates FIRST -- every "
                 "member carries every other, so the ranking below orders the "
                 "groups' reach, not a sequence within them.")
        for grp in groups[:3]:
            L.append(f"      [{len(grp):>2}] {', '.join(grp)}")
        if len(groups) > 3:
            L.append(f"      ... {len(groups) - 3} smaller group(s)")
    L.append("  ranked by what their invalidation carries:")
    for r in rows[:top]:
        mark = "*" if r["unit"] in heavy else " "
        L.append(f"  {mark} {r['unit']:<28} transitive={r['transitive_dependents']:<4} "
                 f"direct={r['direct_dependents']:<4} depends_on={r['depends_on']}")
    if len(rows) > top:
        L.append(f"    ... {len(rows) - top} more with a smaller closure "
                 "(not truncated silently -- the count is exact)")
    L.append("  stressors this view does NOT model:")
    for name, why in sorted(UNMODELLED_STRESSORS.items()):
        L.append(f"      {name}: {why}")
    L.append(f"ARCHITECTURE_HORIZON units={len(rows)} "
             f"load_bearing={len(heavy)} floor={CONCENTRATION_FLOOR}")
    return "\n".join(L)


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[args.index("--root") + 1]) if "--root" in args else None

    if "--invalidate" in args:
        unit = args[args.index("--invalidate") + 1]
        res = invalidate(unit, root)
        if "--json" in args:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        elif not res["known"]:
            print(res["note"])
        else:
            print(f"invalidating {unit}: {res['count']} unit(s) must change with it")
            print(f"  direct   : {', '.join(res['direct']) or '(none)'}")
            print(f"  closure  : {', '.join(res['closure']) or '(none)'}")
        return 0

    ok, heavy, rows = gate(root)
    groups = cycles(root=root)
    if "--json" in args:
        print(json.dumps({"rows": rows, "load_bearing": sorted(heavy),
                          "mutually_dependent_groups": groups,
                          "floor": CONCENTRATION_FLOOR,
                          "baseline_sealed": bool(LOAD_BEARING_BASELINE),
                          "unmodelled_stressors": UNMODELLED_STRESSORS},
                         ensure_ascii=False, indent=2))
    else:
        print(render(rows, heavy, groups))
        if not LOAD_BEARING_BASELINE:
            print("  baseline UNSEALED -- reporting only. Seal "
                  "LOAD_BEARING_BASELINE to make drift fail.")
    if "--gate" in args and not ok:
        print(f"  DRIFT: load-bearing set is {sorted(heavy)}, "
              f"baseline is {sorted(LOAD_BEARING_BASELINE)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
