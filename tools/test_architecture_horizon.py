"""V-gates for the architecture horizon view (UPAC residue R2).

Graph semantics are proven on synthetic roots with a known shape -- a graph
analysis validated only against the repo it was written on proves nothing about
its arithmetic. Discovery is then proven against the real repository, because a
grapher that finds nothing real is not a grapher.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.architecture_horizon import (  # noqa: E402
    UNMODELLED_STRESSORS, build_graph, cycles, dependents, invalidate, rank,
    transitive_dependents,
)

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {ev}")


def _mk(tmp: Path, spec: dict) -> Path:
    """spec: {package: [absolute-import target package, ...]}"""
    mods = tmp / "modules"
    for pkg, deps in spec.items():
        d = mods / pkg
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").write_text("", encoding="utf-8")
        body = "".join(f"from modules.{t}.core import thing\n" for t in deps)
        (d / "core.py").write_text(body or "thing = 1\n", encoding="utf-8")
    return tmp


def t_chain_direction() -> None:
    """a <- b <- c. Invalidating `a` must carry b and c; invalidating `c` carries
    nothing. Direction is the one thing a dependency view cannot get wrong."""
    gate = "V-AH-DIRECTION"
    with tempfile.TemporaryDirectory() as d:
        root = _mk(Path(d), {"a": [], "b": ["a"], "c": ["b"]})
        g = build_graph(root)
        rev = dependents(g)
        carries_a = transitive_dependents("a", rev)
        carries_c = transitive_dependents("c", rev)
    if carries_a == {"b", "c"} and carries_c == set():
        _ok(gate, "a<-b<-c: invalidating a carries {b,c}; invalidating c carries "
                  "nothing")
    else:
        _fail(gate, f"a->{sorted(carries_a)} c->{sorted(carries_c)}")


def t_cycle_is_named() -> None:
    """Two units importing each other are a group, and neither invalidates first."""
    gate = "V-AH-CYCLE-NAMED"
    with tempfile.TemporaryDirectory() as d:
        root = _mk(Path(d), {"x": ["y"], "y": ["x"], "z": []})
        groups = cycles(root=root)
    if groups == [["x", "y"]]:
        _ok(gate, "mutual import -> one group ['x','y']; the isolated unit is not "
                  "in a group")
    else:
        _fail(gate, f"groups={groups}")


def t_no_false_cycle() -> None:
    gate = "V-AH-NO-FALSE-CYCLE"
    with tempfile.TemporaryDirectory() as d:
        root = _mk(Path(d), {"a": [], "b": ["a"], "c": ["a"]})
        groups = cycles(root=root)
    if groups == []:
        _ok(gate, "a shared dependency is not a cycle -- 0 groups on a fan-in DAG")
    else:
        _fail(gate, f"groups={groups} (fabricated a cycle)")


def t_cycle_survives_traversal() -> None:
    """A recursive walk would not survive this estate's real cycles; the iterative
    closure must terminate and stay exact."""
    gate = "V-AH-CYCLE-TERMINATES"
    with tempfile.TemporaryDirectory() as d:
        root = _mk(Path(d), {"p": ["q"], "q": ["r"], "r": ["p"], "s": ["p"]})
        g = build_graph(root)
        rev = dependents(g)
        closure = transitive_dependents("p", rev)
    if closure == {"q", "r", "s"}:
        _ok(gate, "3-cycle plus an outside dependent terminates with an exact "
                  "closure, and the unit itself is excluded")
    else:
        _fail(gate, f"closure={sorted(closure)}")


def t_relative_imports_resolved() -> None:
    """This estate uses `from ..sibling.x import y`; missing it would undercount
    every edge and report a falsely decoupled architecture."""
    gate = "V-AH-RELATIVE-IMPORTS"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        mods = tmp / "modules"
        for pkg in ("alpha", "beta"):
            p = mods / pkg
            p.mkdir(parents=True, exist_ok=True)
            (p / "__init__.py").write_text("", encoding="utf-8")
        (mods / "alpha" / "core.py").write_text("thing = 1\n", encoding="utf-8")
        (mods / "beta" / "core.py").write_text(
            "from ..alpha.core import thing\n", encoding="utf-8")
        g = build_graph(tmp)
    if g.get("beta") == {"alpha"}:
        _ok(gate, "`from ..alpha.core import thing` resolves to an alpha edge")
    else:
        _fail(gate, f"beta deps={sorted(g.get('beta', ()))}")


def t_self_import_not_an_edge() -> None:
    gate = "V-AH-NO-SELF-EDGE"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = tmp / "modules" / "solo"
        p.mkdir(parents=True, exist_ok=True)
        (p / "__init__.py").write_text("", encoding="utf-8")
        (p / "a.py").write_text("thing = 1\n", encoding="utf-8")
        (p / "b.py").write_text("from .a import thing\n", encoding="utf-8")
        g = build_graph(tmp)
    if g.get("solo") == set():
        _ok(gate, "an intra-package relative import is not a cross-unit edge")
    else:
        _fail(gate, f"solo deps={sorted(g.get('solo', ()))}")


def t_unknown_unit_is_honest() -> None:
    gate = "V-AH-UNKNOWN-UNIT"
    res = invalidate("no_such_package_anywhere", PP)
    if res["known"] is False and not res["closure"]:
        _ok(gate, "an unknown unit reports known=False with an empty closure, "
                  "never a confident zero-impact answer")
    else:
        _fail(gate, f"known={res['known']} closure={res['closure']}")


def t_unmodelled_declared() -> None:
    gate = "V-AH-UNMODELLED-DECLARED"
    required = {"traffic_scale", "latency_inflation", "multi_region",
                "adversarial_traffic", "data_growth"}
    missing = required - set(UNMODELLED_STRESSORS)
    unreasoned = [k for k, v in UNMODELLED_STRESSORS.items() if not str(v).strip()]
    if not missing and not unreasoned:
        _ok(gate, f"{len(UNMODELLED_STRESSORS)} stressors declared unmodelled, "
                  "each with a reason -- the view states its own ceiling")
    else:
        _fail(gate, f"missing={sorted(missing)} unreasoned={unreasoned}")


def t_finds_the_real_repo() -> None:
    gate = "V-AH-DISCOVERS"
    rows = rank(root=PP)
    groups = cycles(root=PP)
    edges = sum(len(v) for v in build_graph(PP).values())
    if len(rows) > 50 and edges > 50:
        core = f"; largest mutual group={len(groups[0])}" if groups else ""
        _ok(gate, f"{len(rows)} units, {edges} intra-estate edges{core}")
    else:
        _fail(gate, f"units={len(rows)} edges={edges} -- grapher found too little "
                    "to be measuring the real repo")


def main() -> int:
    for t in (t_chain_direction,
              t_cycle_is_named,
              t_no_false_cycle,
              t_cycle_survives_traversal,
              t_relative_imports_resolved,
              t_self_import_not_an_edge,
              t_unknown_unit_is_honest,
              t_unmodelled_declared,
              t_finds_the_real_repo):
        t()
    total = _passes + _fails
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"AH_PASS={_passes}/{total}  threshold={total}/{total}  VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
