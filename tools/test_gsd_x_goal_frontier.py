"""Frontier suite for GSD X Phase 3 (W2 execution frontier and scheduling).

Drives modules/gsd_x/goal/frontier.py through the real GoalLog, epoch writer and reconciler.
Hermetic: HOME, USERPROFILE and GSDX_GOALS_ROOT are redirected before any engine import.

Summary line: GSDX_FRONTIER_PASS=n/m  threshold=m/m
"""
from __future__ import annotations

import dataclasses
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="frontier-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="frontier-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)
os.environ.pop("GSDX_FRONTIER", None)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import epoch as ep               # noqa: E402
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal import proof as pf               # noqa: E402
from modules.gsd_x.goal import reconcile as rc           # noqa: E402
from modules.gsd_x.goal import sweep as sw               # noqa: E402
from modules.gsd_x.mission import closure as mcl        # noqa: E402

REPO = "f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1"
TREE = "git:" + "f" * 40
OLD_TREE = "git:" + "a" * 40
PIN = (("tools/gate.py", "9" * 64),)
ABSENT = "RED-first: modules.gsd_x.goal.frontier absent"

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    """A raise is a FAIL line, never an escape: the summary line always prints."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def load_frontier():
    try:
        from modules.gsd_x.goal import frontier  # noqa: PLC0415
        return frontier
    except ImportError:
        return None


def need(*names):
    fr = load_frontier()
    if fr is None or any(not hasattr(fr, n) for n in names):
        return None
    return fr


def build(name: str, specs: list, base: Path | None = None):
    """GoalLog with one declared goal and the given obligations.

    specs: (obligation id, plane, gate class). Returns (log, base dir)."""
    base = base or Path(tempfile.mkdtemp(prefix="frontier-"))
    log = gl.GoalLog(REPO, name, base=base)
    gc.declare(log, f"goal {name}", ["it works"], [], {"paths": ["src"]})
    for plane in cv.PLANES:
        s = gc.project(log)
        cv.set_plane(log, s, plane, plane in cv.ALWAYS or plane == cv.REALITY,
                     "" if plane in cv.ALWAYS or plane == cv.REALITY else "not claimed", "t")
    for oid, plane, gate_class in specs:
        cv.accept_obligation(log, gc.project(log), oid, plane, "do it", "python tools/gate.py",
                             PIN, "t", gate_class=gate_class)
    return log, base


def ctx_for(log, **kw):
    st = gc.project(log)
    return rc.Context(state=st, tree_hash=kw.pop("tree", TREE), scope_hash="scope1",
                      providers=kw.pop("providers", ("gate",)), now=kw.pop("now", 1000.0),
                      budget=kw.pop("budget", st.budget), **kw)


def obligation(log, oid):
    return cv.project_convergence(gc.project(log)).obligations[oid]


def open_gate_epoch(log, oid):
    """A real dispatched-and-running gate epoch for `oid`."""
    st = gc.project(log)
    e = ep.begin(log, st, "gate", {"obligation": oid, "tree_hash": TREE,
                                   "gate": {"id": oid, "command": [], "class": "unit", "files": []}},
                 f"key-{oid}", "initial", "t")
    ep.mark_running(log, gc.project(log), e.epoch_id, {"pid": 1}, "t")
    return e.epoch_id


def ids(units):
    return [u["obligation"] for u in units]


# ---------------------------------------------------------------- 03-01 gates

def gate_hermetic():
    root = Path(os.environ["GSDX_GOALS_ROOT"]).resolve()
    ok = (Path.home().resolve() == _TMP_HOME.resolve() and Path.home().resolve() != REAL_HOME.resolve()
          and root.parent.parent == Path(tempfile.gettempdir()).resolve())
    return ok, f"goals_root_under_temp={root.parent.parent == Path(tempfile.gettempdir()).resolve()}"


def gate_switch():
    fr = need("frontier_enabled")
    if fr is None:
        return False, ABSENT
    table = {None: True, "": True, "on": True, "1": True, "true": True, "yes": True, " ON ": True,
             "0": False, "off": False, "false": False, "onn": False, "no": False}
    bad = []
    old = os.environ.get("GSDX_FRONTIER")
    off_file = sw.state_dir() / "FRONTIER.off"
    try:
        for val, want in table.items():
            if val is None:
                os.environ.pop("GSDX_FRONTIER", None)
            else:
                os.environ["GSDX_FRONTIER"] = val
            if fr.frontier_enabled() != want:
                bad.append((val, want))
        os.environ["GSDX_FRONTIER"] = "on"
        off_file.parent.mkdir(parents=True, exist_ok=True)
        off_file.write_text("off", encoding="utf-8")
        file_forces_off = fr.frontier_enabled() is False
        off_file.unlink()
        back_on = fr.frontier_enabled() is True
        same_table = all(pf.switch_on("GSDX_FRONTIER") == fr.frontier_enabled() for _ in (0,))
    finally:
        if off_file.exists():
            off_file.unlink()
        if old is None:
            os.environ.pop("GSDX_FRONTIER", None)
        else:
            os.environ["GSDX_FRONTIER"] = old
    return not bad and file_forces_off and back_on and same_table, (
        f"table_rows={len(table)} mismatches={bad} file_forces_off={file_forces_off} back_on={back_on}")


def gate_unit_derive():
    fr = need("gate_unit")
    if fr is None:
        return False, ABSENT
    log, base = build("derive", [("ob-u", cv.OUTCOME, "unit"), ("ob-i", cv.REGRESSION, "integration"),
                                 ("ob-r", cv.REALITY, "in_game"), ("ob-l", cv.EVIDENCE, "live"),
                                 ("ob-e", cv.EVIDENCE, "")])
    try:
        st = gc.project(log)
        u = fr.gate_unit(obligation(log, "ob-u"), st)
        i = fr.gate_unit(obligation(log, "ob-i"), st)
        r = fr.gate_unit(obligation(log, "ob-r"), st)
        lv = fr.gate_unit(obligation(log, "ob-l"), st)
        e = fr.gate_unit(obligation(log, "ob-e"), st)   # empty class on a non-reality plane runs as "unit" (sweep.py:365)
        ok = (u["resources"] == [] and i["resources"] == ["integration-env"]
              and r["resources"] == ["reality-env"] and lv["resources"] == ["reality-env"]
              and e["resources"] == []
              and u["writes"] == ["run:ob-u"] and "tools/gate.py" in u["reads"] and "tree:*" in u["reads"]
              and u["kind"] == "gate" and u["obligation"] == "ob-u")
        # a declared causal path replaces the whole-tree read token
        o = obligation(log, "ob-u")
        payload = {"v": 1, "claim_id": pf.claim_id(o), "obligation": "ob-u", "combine": "AND",
                   "elements": [{"oracle": "unit", "command": "python tools/gate.py", "gate_pin": [list(p) for p in PIN],
                                 "causal_paths": ["src/a"], "env_deps": [], "freshness_class": "unit",
                                 "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}]}
        pf.append_pcc(log, gc.project(log), pf.CONTRACT, payload, "founder")
        cp = fr.gate_unit(obligation(log, "ob-u"), gc.project(log))
        ok = ok and "src/a" in cp["reads"] and "tree:*" not in cp["reads"]
        return ok, f"unit={u['resources']} integ={i['resources']} reality={r['resources']} empty_class={e['resources']} causal_reads={cp['reads']}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_undeclared():
    fr = need("gate_unit", "independent_units")
    if fr is None:
        return False, ABSENT
    log, base = build("undecl", [("ob-1", cv.OUTCOME, "unit"), ("ob-2", cv.EVIDENCE, "unit"),
                                 ("ob-n", cv.REALITY, "in_game")])
    try:
        st = gc.project(log)
        u1, u2 = (fr.gate_unit(obligation(log, x), st) for x in ("ob-1", "ob-2"))
        # the log refuses an unknown class at accept time, so the unreadable case is built directly
        w = fr.gate_unit(dataclasses.replace(obligation(log, "ob-1"), gate_class="weird"), st)
        # reality plane with no class (a legacy row the sweep refuses to dispatch): undeclared
        n = fr.gate_unit(dataclasses.replace(obligation(log, "ob-n"), gate_class=""), st)
        control = fr.independent_units(u1, u2) is True
        refused = (w["reads"] is None and n["writes"] is None
                   and not fr.independent_units(w, u1) and not fr.independent_units(u1, w)
                   and not fr.independent_units(w, w) and not fr.independent_units(n, u2))
        return control and refused, f"declared_pair_independent={control} undeclared_refused={refused}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_indep():
    fr = need("independent_units")
    if fr is None:
        return False, ABSENT

    def mk(r=(), w=(), x=()):
        return {"reads": list(r), "writes": list(w), "resources": list(x)}

    cases = {
        "disjoint-control": (mk(["a"], ["run:1"]), mk(["b"], ["run:2"]), True),
        "shared-write": (mk([], ["f"]), mk([], ["f"]), False),
        "write-read": (mk([], ["f"]), mk(["f"], ["g"]), False),
        "read-write": (mk(["f"], ["g"]), mk([], ["f"]), False),
        "shared-reads-only": (mk(["f"], ["x"]), mk(["f"], ["y"]), True),
    }
    bad = [k for k, (a, b, want) in cases.items() if fr.independent_units(a, b) is not want]
    sym = [k for k, (a, b, want) in cases.items() if fr.independent_units(b, a) is not want]
    return not bad and not sym, f"cases={len(cases)} wrong={bad} asymmetric={sym}"


def gate_resource():
    """RED item 3: a resource collision must never be admitted as independent."""
    fr = need("gate_unit", "independent_units")
    if fr is None:
        return False, ABSENT
    log, base = build("res", [("i1", cv.OUTCOME, "integration"), ("i2", cv.EVIDENCE, "integration"),
                              ("u1", cv.REGRESSION, "unit"), ("r1", cv.REALITY, "in_game"),
                              ("r2", cv.UCR_CIF_LEARNING, "live")])
    try:
        st = gc.project(log)
        g = {x: fr.gate_unit(obligation(log, x), st) for x in ("i1", "i2", "u1", "r1", "r2")}
        collide_i = not fr.independent_units(g["i1"], g["i2"])
        collide_r = not fr.independent_units(g["r1"], g["r2"])
        ok_mix = fr.independent_units(g["i1"], g["u1"]) and fr.independent_units(g["i1"], g["r1"])
        return collide_i and collide_r and ok_mix, (
            f"integration_pair_refused={collide_i} reality_pair_refused={collide_r} cross_class_control_admitted={ok_mix}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_frontiers():
    fr = need("compile_frontier")
    if fr is None:
        return False, ABSENT
    log, base = build("fronts", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit"),
                                 ("ob-c", cv.REGRESSION, "unit"), ("ob-d", cv.UCR_CIF_LEARNING, "unit")])
    try:
        st = gc.project(log)
        v = mcl.Verdict("tools/gate.py", 0, "ok", OLD_TREE, st.revision, "unit", PIN)
        cv.satisfy(log, st, "ob-d", v, "t")                       # proven at another tree: invalidated here
        first = fr.compile_frontier(ctx_for(log))
        open_gate_epoch(log, "ob-a")
        second = fr.compile_frontier(ctx_for(log))
        ok = (set(ids(first.execution)) == {"ob-a", "ob-b", "ob-c", "ob-d"}
              and set(ids(second.execution)) == {"ob-b", "ob-c", "ob-d"}
              and "ob-d" in first.invalidation and "ob-a" not in first.invalidation
              and set(first.expectation) == {"ob-a", "ob-b", "ob-c", "ob-d"}
              and len(first.proof) >= 1)
        return ok, f"exec_before={ids(first.execution)} exec_after_open={ids(second.execution)} invalidation={list(first.invalidation)} proof_items={len(first.proof)}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_graph():
    fr = need("compile_frontier")
    if fr is None:
        return False, ABSENT
    log, base = build("graph", [("i1", cv.OUTCOME, "integration"), ("i2", cv.EVIDENCE, "integration"),
                                ("u1", cv.REGRESSION, "unit")])
    try:
        f = fr.compile_frontier(ctx_for(log))
        kinds = {(a, b, k) for a, b, k in f.edges}
        has = lambda a, b, k: (a, b, k) in kinds  # noqa: E731
        res_edges = [e for e in f.edges if e[2].startswith("resource:")]
        gate_gate = [e for e in f.edges if e[0].startswith("gate:") and e[1].startswith("gate:")]
        ok = (has("gate:i1", "barrier", "gate->barrier") and has("gate:u1", "barrier", "gate->barrier")
              and has("barrier", "judge", "barrier->judge")
              and len(res_edges) == 1 and res_edges[0][2] == "resource:integration-env"
              and {res_edges[0][0], res_edges[0][1]} == {"gate:i1", "gate:i2"}
              and len(gate_gate) == 1)          # no obligation->obligation edge is invented
        return ok, f"edges={len(f.edges)} resource_edges={res_edges} gate_gate_edges={len(gate_gate)}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


GATES = [
    ("V-FRONTIER-HERMETIC", gate_hermetic),
    ("V-FRONTIER-SWITCH", gate_switch),
    ("V-FRONTIER-UNIT-DERIVE", gate_unit_derive),
    ("V-FRONTIER-UNDECLARED", gate_undeclared),
    ("V-FRONTIER-INDEP", gate_indep),
    ("V-FRONTIER-RESOURCE", gate_resource),
    ("V-FRONTIER-FRONTIERS", gate_frontiers),
    ("V-FRONTIER-GRAPH", gate_graph),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_FRONTIER_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
