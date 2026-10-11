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


# ---------------------------------------------------------------- 03-02 gates

T0 = 1_700_000_000.0


def _iso(offset_s: float) -> str:
    import datetime as dt  # noqa: PLC0415
    return dt.datetime.fromtimestamp(T0 + offset_s, dt.timezone.utc).isoformat()


def syn_state(runs: list):
    """A projection stand-in with real epoch events at controlled timestamps.

    runs: (obligation, gate class, outcome, start s, duration s)."""
    from types import SimpleNamespace as NS  # noqa: PLC0415
    events = []
    seq = 0
    for n, (oid, cls, outcome, start, dur) in enumerate(runs):
        eid = f"ep-{n}"
        seq += 1
        events.append(NS(seq=seq, type=ep.DISPATCHING, ts=_iso(start), data={
            "epoch_id": eid, "revision": "r", "provider": "gate", "identity": {}, "info_key": f"k{n}",
            "hypothesis": "initial", "fence": n + 1,
            "spec": {"obligation": oid, "tree_hash": TREE, "gate": {"id": oid, "class": cls}}}))
        seq += 1
        events.append(NS(seq=seq, type=ep.RUNNING, ts=_iso(start), data={"epoch_id": eid, "handle": {}}))
        seq += 1
        events.append(NS(seq=seq, type=ep.ENDED, ts=_iso(start + dur), data={"epoch_id": eid, "outcome": outcome}))
    return NS(goal_id="syn", events=events, budget={})


def unit_of(oid: str, reads=("tools/gate.py",), resources=()):
    return {"id": f"gate:{oid}", "kind": "gate", "obligation": oid, "gate_class": "unit",
            "reads": list(reads), "writes": [f"run:{oid}"], "resources": list(resources)}


def gate_prior():
    fr = need("duration_prior")
    if fr is None:
        return False, ABSENT
    st = syn_state([("ob-a", "unit", "completed", 0, 10), ("ob-a", "unit", "failed", 100, 20),
                    ("ob-a", "unit", "completed", 200, 30), ("ob-a", "unit", "lost", 300, 999),
                    ("ob-a", "unit", "cancelled", 400, 777), ("ob-d", "unit", "completed", 500, 100)])
    own = fr.duration_prior(st, "ob-a", "unit")                # median 10,20,30; lost/cancelled are no measurement
    cls = fr.duration_prior(st, "ob-b", "unit")                # no history: class median of 10,20,30,100
    none = fr.duration_prior(st, "ob-c", "integration")        # nothing measured anywhere
    ok = own == 20.0 and cls == 25.0 and none is None
    return ok, f"own={own} class_fallback={cls} unknown={none}"


def gate_order():
    fr = need("order_units")
    if fr is None:
        return False, ABSENT
    u = {k: unit_of(k) for k in "abcd"}

    def sig(duration, contrib, risk, gain):
        return {"duration": duration, "contrib": contrib, "risk": risk, "gain": gain}

    sigs = {"gate:a": sig(5.0, 10.0, 0.1, 0.9),      # longest path, low risk
            "gate:b": sig(5.0, 3.0, 0.9, 0.9),       # short path, high risk
            "gate:c": sig(5.0, 3.0, 0.9, 0.1),       # ties b on risk, loses on gain
            "gate:d": sig(5.0, 3.0, 0.9, 0.1)}       # ties c exactly: legacy order decides
    got = [x["obligation"] for x in fr.order_units([u["d"], u["c"], u["b"], u["a"]], sigs)]
    # contribution beats risk (a first); risk ties fall to gain (b before c,d); exact tie keeps input order (d before c)
    ok = got == ["a", "b", "d", "c"]
    unknown_first = [x["obligation"] for x in fr.order_units(
        [u["a"], u["b"]], {"gate:a": sig(5.0, 10.0, 0.1, 0.9), "gate:b": sig(None, 0.0, None, None)})]
    return ok and unknown_first == ["b", "a"], f"order={got} unknown_duration_first={unknown_first}"


def gate_failure_first():
    fr = need("failure_risk")
    if fr is None:
        return False, ABSENT
    st = syn_state([("ob-f", "unit", "failed", 0, 5), ("ob-f", "unit", "completed", 10, 5),
                    ("ob-f", "unit", "failed", 20, 5), ("ob-p", "unit", "completed", 30, 5),
                    ("ob-p", "unit", "completed", 40, 5)])
    solo = [unit_of("ob-f", reads=("a",)), unit_of("ob-p", reads=("b",)), unit_of("ob-n", reads=("c",))]
    rf = fr.failure_risk(st, "ob-f", solo)
    rp = fr.failure_risk(st, "ob-p", solo)
    rn = fr.failure_risk(st, "ob-n", solo)
    shared = [unit_of("ob-f", reads=("a", "tree:*")), unit_of("ob-p", reads=("a", "tree:*")),
              unit_of("ob-n", reads=("tree:*",))]
    rf_shared = fr.failure_risk(st, "ob-f", shared)           # one other unit shares read "a"; tree:* alone is no sharing
    ok = (abs(rf - 2 / 3) < 1e-9 and rp == 0.0 and rn is None and abs(rf_shared - 2 * (2 / 3)) < 1e-9)
    return ok, f"failing={rf} passing={rp} no_history={rn} shared_read_multiplier={rf_shared}"


def gate_infogain():
    fr = need("info_gain")
    if fr is None:
        return False, ABSENT
    half = syn_state([("h", "unit", "completed", 0, 10), ("h", "unit", "failed", 20, 10)])
    sure = syn_state([("s", "unit", "completed", 0, 10), ("s", "unit", "completed", 20, 10)])
    quick = syn_state([("q", "unit", "completed", 0, 5), ("q", "unit", "failed", 20, 5)])
    zero = syn_state([("z", "unit", "completed", 0, 0), ("z", "unit", "failed", 20, 0)])
    g_half, g_sure, g_quick = fr.info_gain(half, "h", "unit"), fr.info_gain(sure, "s", "unit"), fr.info_gain(quick, "q", "unit")
    none_hist = fr.info_gain(half, "other", "integration")
    none_zero = fr.info_gain(zero, "z", "unit")
    ok = (abs(g_half - 0.1) < 1e-9 and g_sure == 0.0 and abs(g_quick - 0.2) < 1e-9
          and none_hist is None and none_zero is None)
    return ok, f"p=.5,10s={g_half} certain={g_sure} p=.5,5s={g_quick} no_history={none_hist} zero_duration={none_zero}"


def gate_critical_path():
    fr = need("critical_path")
    if fr is None:
        return False, ABSENT
    units = [unit_of("a"), unit_of("b"), unit_of("c")]
    edges = (("gate:a", "gate:b", "resource:x"), ("gate:b", "gate:c", "resource:x"))
    full = fr.critical_path(units, edges, {"gate:a": 10.0, "gate:b": 20.0, "gate:c": 5.0})
    part = fr.critical_path(units, edges, {"gate:a": 10.0, "gate:b": 20.0, "gate:c": None})
    ok = (full["length"] == 35.0 and full["nodes"] == ("gate:a", "gate:b", "gate:c")
          and full["contrib"] == {"gate:a": 35.0, "gate:b": 25.0, "gate:c": 5.0} and full["unknown"] == ()
          and part["length"] == 30.0 and part["unknown"] == ("gate:c",))
    return ok, f"full={full['length']} {full['nodes']} partial_lower_bound={part['length']} unknown={part['unknown']}"


def gate_posture():
    fr = need("posture", "bound")
    if fr is None:
        return False, ABSENT
    from types import SimpleNamespace as NS  # noqa: PLC0415

    def c(b, sb=None):
        return NS(budget=b, state=NS(budget=sb if sb is not None else {}))

    cases = [({}, "ECONOMY", 1), ({"posture": "ECONOMY"}, "ECONOMY", 1), ({"posture": "BALANCED"}, "BALANCED", 2),
             ({"posture": "WALL_CLOCK"}, "WALL_CLOCK", 4), ({"posture": "wall_clock"}, "WALL_CLOCK", 4),
             ({"posture": "TURBO"}, "ECONOMY", 1), ({"posture": 7}, "ECONOMY", 1),
             ({"posture": "WALL_CLOCK", "max_parallel": 2}, "WALL_CLOCK", 2),
             ({"posture": "BALANCED", "max_parallel": 9}, "BALANCED", 2),
             ({"posture": "WALL_CLOCK", "max_parallel": 0}, "WALL_CLOCK", 4),
             ({"posture": "WALL_CLOCK", "max_parallel": -3}, "WALL_CLOCK", 4),
             ({"posture": "WALL_CLOCK", "max_parallel": True}, "WALL_CLOCK", 4),
             ({"posture": "WALL_CLOCK", "max_parallel": "x"}, "WALL_CLOCK", 4)]
    bad = [(b, fr.posture(c(b)), fr.bound(c(b))) for b, p, n in cases if (fr.posture(c(b)), fr.bound(c(b))) != (p, n)]
    from_state = (fr.posture(c({}, {"posture": "BALANCED"})), fr.bound(c({}, {"posture": "BALANCED"}))) == ("BALANCED", 2)
    # round trip: the posture survives the real log, so a goal can declare it
    log, base = build("posture", [("ob-1", cv.OUTCOME, "unit")])
    try:
        st = gc.project(log)
        gc.set_budget(log, st.last_seq + 1, {"posture": "WALL_CLOCK", "max_parallel": 3}, "founder")
        ctx = ctx_for(log)
        trip = (fr.posture(ctx), fr.bound(ctx)) == ("WALL_CLOCK", 3)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return not bad and from_state and trip, f"cases={len(cases)} wrong={bad} state_fallback={from_state} log_round_trip={trip}"


def gate_classes():
    fr = need("class_bound", "WORKER_CLASSES")
    if fr is None:
        return False, ABSENT
    from types import SimpleNamespace as NS  # noqa: PLC0415
    ctx = NS(budget={"posture": "WALL_CLOCK"}, state=NS(budget={}))
    got = {k: fr.class_bound(k, ctx) for k in fr.WORKER_CLASSES}
    try:
        fr.class_bound("wizard", ctx)
        refused = False
    except ValueError:
        refused = True
    ok = (set(got) == {"cognitive", "deterministic", "environment", "reviewer", "speculative"}
          and got["deterministic"] == 4 and all(got[k] == 1 for k in got if k != "deterministic") and refused)
    return ok, f"bounds={got} unknown_class_refused={refused}"


def gate_compile_orders():
    """compile_frontier applies the measured order and exposes the signals and the bound."""
    fr = need("compile_frontier")
    if fr is None:
        return False, ABSENT
    log, base = build("orders", [("ob-1", cv.OUTCOME, "unit"), ("ob-2", cv.EVIDENCE, "unit")],)
    try:
        st = gc.project(log)
        gc.set_budget(log, st.last_seq + 1, {"posture": "BALANCED"}, "founder")
        f = fr.compile_frontier(ctx_for(log))
        legacy_order = ids(f.execution) == ["ob-1", "ob-2"]      # no history: legacy insertion order is kept
        ok = (legacy_order and f.posture == "BALANCED" and f.bound == 2
              and set(f.signals) == {"gate:ob-1", "gate:ob-2"} and f.critical_path["length"] == 0.0
              and f.critical_path["unknown"] == ("gate:ob-1", "gate:ob-2"))
        return ok, f"order={ids(f.execution)} posture={f.posture} bound={f.bound} unknown_durations={f.critical_path['unknown']}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------- 03-03 gates
# `ep.begin` refuses a second open epoch until 03-04, so these fixtures append the DISPATCHING and
# RUNNING events directly, exactly the shape begin / mark_running write, with the unit in the spec.

import contextlib  # noqa: E402
import inspect  # noqa: E402
import uuid  # noqa: E402


@contextlib.contextmanager
def switch(value):
    old = os.environ.get(pf.FRONTIER_SWITCH)
    if value is None:
        os.environ.pop(pf.FRONTIER_SWITCH, None)
    else:
        os.environ[pf.FRONTIER_SWITCH] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(pf.FRONTIER_SWITCH, None)
        else:
            os.environ[pf.FRONTIER_SWITCH] = old


def raw_epoch(log, oid, with_unit=True, running=True, gate_class="unit", unit=None):
    """An open gate epoch for `oid` whose spec carries the stored unit, written as begin would."""
    fr = load_frontier()
    st = gc.project(log)
    o = cv.project_convergence(st).obligations[oid]
    spec = {"obligation": oid, "tree_hash": TREE, "plane": o.plane,
            "gate": {"id": oid, "command": [], "class": gate_class, "files": []}}
    if with_unit:
        spec["unit"] = unit if unit is not None else fr.stored_unit(fr.gate_unit(o, st))
    eid = f"ep-{uuid.uuid4().hex[:12]}"
    fence = max((e.fence for e in ep.project_epochs(st).values()), default=0) + 1
    log.append(st.last_seq + 1, ep.DISPATCHING,
               {"epoch_id": eid, "revision": st.revision, "provider": "gate",
                "identity": {"run_token": uuid.uuid4().hex, "epoch_id": eid, "fence": fence,
                             "goal_id": st.goal_id},
                "info_key": f"key-{oid}", "hypothesis": "initial", "spec": spec, "fence": fence}, "t")
    if running:
        ep.mark_running(log, gc.project(log), eid, {"pid": 1}, "t")
    return eid


def set_posture(log, posture_name, **extra):
    st = gc.project(log)
    gc.set_budget(log, st.last_seq + 1, {"posture": posture_name, **extra}, "founder")


def obs(**by_epoch):
    return {eid: ep.Observation(state) for eid, state in by_epoch.items()}


def wait_scenario(name, specs, running_class="unit", posture_name="WALL_CLOCK", **budget):
    """One running epoch for the first obligation; the rest are ungated and wait their turn."""
    log, base = build(name, specs)
    set_posture(log, posture_name, **budget)
    eid = raw_epoch(log, specs[0][0], gate_class=running_class)
    return log, base, eid


def gate_global_wait():
    """RED 1: legacy idles on a running sibling while an independent gate waits."""
    log, base, eid = wait_scenario("gwait", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    clog, cbase, ceid = wait_scenario("gwait-c", [("ob-a", cv.OUTCOME, "integration"),
                                                  ("ob-b", cv.EVIDENCE, "integration")],
                                      running_class="integration")
    try:
        with switch("off"):
            legacy = rc.decide(ctx_for(log, observations=obs(**{eid: "running"})))
        with switch("on"):
            d = rc.decide(ctx_for(log, observations=obs(**{eid: "running"})))
            control = rc.decide(ctx_for(clog, observations=obs(**{ceid: "running"})))
        ok = (legacy.kind == rc.WAIT and d.kind == rc.NEXT_EPOCH
              and d.spec.get("obligation") == "ob-b" and bool(d.spec.get("unit"))
              and d.provider == "gate" and d.info_key and control.kind == rc.WAIT)
        return ok, f"legacy={legacy.kind} frontier={d.kind}:{d.spec.get('obligation')} control_conflict={control.kind}"
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(cbase, ignore_errors=True)


def gate_legacy_equal():
    """Switch off, and switch on with the default posture: field-equal to the legacy decision."""
    if not hasattr(rc, "_decide_legacy"):
        return False, ABSENT
    seen = {"off": 0, "on": 0, "bad": []}

    def compare(ctx, label):
        for mode in ("off", "on"):
            with switch(mode):
                got, want = rc.decide(ctx), rc._decide_legacy(ctx)
            seen[mode] += 1
            if got != want:
                seen["bad"].append(f"{label}:{mode}")

    log, base = build("leq", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    try:
        compare(ctx_for(log), "fresh")
        eid = raw_epoch(log, "ob-a")
        compare(ctx_for(log, observations=obs(**{eid: "running"})), "running")
        compare(ctx_for(log, observations=obs(**{eid: "ended"})), "ended")
        compare(ctx_for(log), "unobserved")
        rows = []
        for repo, goal, n in ((  # the committed Phase 2 corpus, every log prefix
                "4a226561feb32dc7df40388410bbde2f67e83614", "g-002-router-surface", 50),
                ("1f924bcabb838f1387a2afe5729e29b61891a3b4", "g-001-smoke-runner", 123)):
            src = ROOT / "tools" / "fixtures" / "gsdx_legacy_goals" / repo / goal
            files = sorted(p for p in src.iterdir() if gl.EVENT_RE.match(p.name))
            for k in range(1, len(files) + 1):
                dst = _TMP_GOALS / repo / f"{goal}-p{k}"
                dst.mkdir(parents=True, exist_ok=True)
                for p in files[:k]:
                    shutil.copyfile(p, dst / p.name)
                st = gc.project(gl.GoalLog(repo, f"{goal}-p{k}"))
                compare(rc.Context(state=st, tree_hash=TREE, scope_hash="scope1",
                                   providers=("gate", "codex"), now=1000.0, budget=st.budget),
                        f"{goal}@{k}")
            rows.append(f"{goal}={len(files)}")
        ok = not seen["bad"] and seen["off"] == seen["on"] and seen["off"] > 170
        return ok, f"compared_off={seen['off']} compared_on={seen['on']} prefixes={rows} diffs={seen['bad'][:3]}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_signature():
    sig = inspect.signature(rc.decide)
    ok = (list(sig.parameters) == ["ctx"] and sig.parameters["ctx"].annotation in ("Context", rc.Context)
          and sig.return_annotation in ("Decision", rc.Decision))
    return ok, f"signature={sig}"


def gate_harvest_not_hidden():
    log, base, a = wait_scenario("harv", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit"),
                                          ("ob-c", cv.REGRESSION, "unit")])
    try:
        b = raw_epoch(log, "ob-b")
        o = obs(**{a: "running", b: "ended"})
        with switch("off"):
            legacy = rc.decide(ctx_for(log, observations=o))
        with switch("on"):
            d = rc.decide(ctx_for(log, observations=o))
        ok = legacy.kind == rc.WAIT and d.kind == rc.HARVEST and d.epoch_id == b
        return ok, f"legacy={legacy.kind} frontier={d.kind}:{d.epoch_id == b}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_no_starve():
    """Research P5: an obligation with an open epoch is never re-selected."""
    log, base, a = wait_scenario("starve", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    try:
        with switch("on"):
            first = rc.decide(ctx_for(log, observations=obs(**{a: "running"})))
            b = raw_epoch(log, "ob-b")
            second = rc.decide(ctx_for(log, observations=obs(**{a: "running", b: "running"}),
                                       budget={"posture": "WALL_CLOCK"}))
        ok = first.spec.get("obligation") == "ob-b" and second.kind == rc.WAIT
        return ok, f"first={first.spec.get('obligation')} second={second.kind}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _holds(name, mutate, expect_kind):
    """GLOBAL-WAIT scenario plus one stop condition: still the legacy decision, never NEXT_EPOCH."""
    log, base, a = wait_scenario(name, [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    try:
        extra = mutate(log) or {}
        o = obs(**{a: "running"})
        with switch("off"):
            legacy = rc.decide(ctx_for(log, observations=o, **extra))
        with switch("on"):
            d = rc.decide(ctx_for(log, observations=o, **extra))
        return legacy, d
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _control_next():
    log, base, a = wait_scenario("holds-ctl", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    try:
        with switch("on"):
            return rc.decide(ctx_for(log, observations=obs(**{a: "running"}))).kind
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_stop_holds():
    from modules.gsd_x.goal import intervention as iv  # noqa: PLC0415
    def pause(log):
        iv.intervene(log, gc.project(log), iv.PAUSE, "operator", reason="hold everything")
    legacy, d = _holds("stop", pause, rc.WAIT)
    control = _control_next()
    return legacy.kind == d.kind and d.kind != rc.NEXT_EPOCH and control == rc.NEXT_EPOCH, \
        f"legacy={legacy.kind} frontier={d.kind} control={control}"


def gate_budget_holds():
    legacy, d = _holds("budget", lambda log: {"budget": {"posture": "WALL_CLOCK", "max_epochs": 1}}, rc.WAIT)
    control = _control_next()
    return legacy.kind == d.kind and d.kind != rc.NEXT_EPOCH and control == rc.NEXT_EPOCH, \
        f"legacy={legacy.kind} frontier={d.kind} control={control}"


def gate_blocked_on_holds():
    legacy, d = _holds("blockedon", lambda log: {"blocked_on": "waiting for a person"}, rc.WAIT)
    control = _control_next()
    return legacy.kind == d.kind and d.kind != rc.NEXT_EPOCH and control == rc.NEXT_EPOCH, \
        f"legacy={legacy.kind} frontier={d.kind} control={control}"


def gate_closure_holds():
    """Clear closure: every obligation proven at this tree. Legacy leaves WAIT while a sibling runs."""
    log, base, a = wait_scenario("closure", [("ob-a", cv.OUTCOME, "unit")])
    try:
        st = gc.project(log)
        v = mcl.Verdict("tools/gate.py", 0, "ok", TREE, st.revision, "unit", PIN)
        cv.satisfy(log, st, "ob-a", v, "t")
        raw_b = raw_epoch(log, "ob-a")      # a second open epoch beside the first
        o = obs(**{a: "running", raw_b: "running"})
        with switch("off"):
            legacy = rc.decide(ctx_for(log, observations=o))
        with switch("on"):
            d = rc.decide(ctx_for(log, observations=o))
        return legacy.kind == d.kind == rc.WAIT, f"legacy={legacy.kind} frontier={d.kind}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_wait_only_empty():
    log, base, a = wait_scenario("wempty", [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit")])
    elog, ebase, ea = wait_scenario("wempty2", [("ob-a", cv.OUTCOME, "unit")])
    try:
        with switch("on"):
            nonempty = rc.decide(ctx_for(log, observations=obs(**{a: "running"})))
            empty = rc.decide(ctx_for(elog, observations=obs(**{ea: "running"})))
        return nonempty.kind != rc.WAIT and empty.kind == rc.WAIT, f"nonempty={nonempty.kind} empty={empty.kind}"
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(ebase, ignore_errors=True)


# ---------------------------------------------------------------- 03-04 gates
# The write authority (epoch.begin) and the real sweep. Every gate here is a real subprocess that
# the test awaits: nothing started is left running when the suite returns.

import subprocess  # noqa: E402
import time  # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}
SWEEP_REPO = "7d" * 20


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="frontier-repo-"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=GIT_ENV)
    # Slow enough that the whole dispatch pass finishes while every gate is still running: a gate that
    # ends first would be harvested instead of letting the pass start the next one, by design.
    (d / "gate.py").write_text("import sys, time\ntime.sleep(6)\nprint('1 passed')\nsys.exit(0)\n",
                               encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=GIT_ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=GIT_ENV)
    return d


def sweep_goal_for(name, n, posture_name, repo, **budget):
    """A goal with `n` independent trivial gates (`python gate.py`) and the given posture."""
    from modules.gsd_x.goal import git_state as gs  # noqa: PLC0415
    base = Path(tempfile.mkdtemp(prefix="frontier-sweep-"))
    log = gl.GoalLog(SWEEP_REPO, name, base=base)
    gc.declare(log, f"sweep {name}", ["it works"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        cv.set_plane(log, gc.project(log), plane, plane in cv.ALWAYS or plane == cv.REALITY,
                     "" if plane in cv.ALWAYS or plane == cv.REALITY else "not claimed", "t")
    pin = gs.file_pin(repo, ["gate.py"])
    planes = [cv.OUTCOME, cv.EVIDENCE, cv.REGRESSION, cv.UCR_CIF_LEARNING, cv.REALITY]
    for i in range(n):
        gate_class = "in_game" if planes[i] == cv.REALITY else "unit"
        cv.accept_obligation(log, gc.project(log), f"ob-{i}", planes[i], "do it",
                             f'"{sys.executable}" gate.py', pin, "t", gate_class=gate_class)
    set_posture(log, posture_name, **budget)
    return log, base


def open_count(log) -> int:
    return len([e for e in ep.project_epochs(gc.project(log)).values() if e.state != "ended"])


def drain(log, repo, run_dir, limit_s=120.0) -> list:
    """Sweep until nothing is open and nothing is left to run, or the bound passes. Awaits every gate."""
    seen = []
    deadline = time.time() + limit_s
    while time.time() < deadline:
        acted = sw.sweep_goal(log, repo, providers=("gate",), run_dir=run_dir)
        seen.extend(acted)
        if open_count(log) == 0 and not any("dispatched" in a or "harvested" in a for a in acted):
            return seen
        time.sleep(0.4)
    seen.append("DRAIN TIMEOUT")
    return seen


def three_obligation_log(name):
    return build(name, [("ob-a", cv.OUTCOME, "unit"), ("ob-b", cv.EVIDENCE, "unit"),
                        ("ob-c", cv.REGRESSION, "unit")])


def try_begin(log, oid, unit=None, key=None):
    st = gc.project(log)
    o = cv.project_convergence(st).obligations[oid]
    spec = {"obligation": oid, "tree_hash": TREE, "gate": {"id": oid, "command": [], "class": "unit",
                                                           "files": []}}
    try:
        e = ep.begin(log, st, "gate", spec, key or f"k-{oid}-{uuid.uuid4().hex[:6]}", "initial", "t",
                     unit=unit)
        return e, ""
    except ep.EpochError as exc:
        return None, str(exc)


def derived_unit(log, oid):
    fr = load_frontier()
    st = gc.project(log)
    return fr.stored_unit(fr.gate_unit(cv.project_convergence(st).obligations[oid], st))


def gate_begin_refuses():
    fr = need("stored_unit")
    if fr is None:
        return False, ABSENT
    log, base = three_obligation_log("brefuse")
    try:
        raw_epoch(log, "ob-a")
        before = (len(gc.project(log).events), max(e.fence for e in ep.project_epochs(gc.project(log)).values()))
        with switch("on"):
            no_unit = try_begin(log, "ob-b")
            with_unit_off = None
            with switch("off"):
                with_unit_off = try_begin(log, "ob-b", unit=derived_unit(log, "ob-b"))
        raw_epoch(log, "ob-c", with_unit=False, running=False)       # an open epoch with no stored unit
        with switch("on"):
            unitless_open = try_begin(log, "ob-b", unit=derived_unit(log, "ob-b"))
        after = (len(gc.project(log).events) - 1,           # minus the ob-c epoch appended above
                 max(e.fence for e in ep.project_epochs(gc.project(log)).values()) - 1)
        refused = [no_unit[0], with_unit_off[0], unitless_open[0]]
        ok = all(r is None for r in refused) and after == before
        return ok, f"no_unit='{no_unit[1][:40]}' switch_off='{with_unit_off[1][:40]}' open_without_unit='{unitless_open[1][:40]}' log_and_fence_unchanged={after == before}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_unsafe_writes():
    """RED 2: the authority refuses an unsafe pair whatever the reconciler said."""
    fr = need("stored_unit")
    if fr is None:
        return False, ABSENT
    cases = {}
    for label, held in (
            ("overlapping-writes", {"id": "gate:ob-a", "kind": "gate", "obligation": "ob-a",
                                    "gate_class": "unit", "reads": ["x"], "writes": ["run:ob-b"],
                                    "resources": []}),
            ("read-after-write", {"id": "gate:ob-a", "kind": "gate", "obligation": "ob-a",
                                  "gate_class": "unit", "reads": ["x"], "writes": ["tools/gate.py"],
                                  "resources": []}),
            ("undeclared-sets", {"id": "gate:ob-a", "kind": "gate", "obligation": "ob-a",
                                 "gate_class": "unit", "reads": None, "writes": None,
                                 "resources": None})):
        log, base = three_obligation_log(f"unsafe-{label}")
        try:
            raw_epoch(log, "ob-a", unit=held)
            with switch("on"):
                e, msg = try_begin(log, "ob-b", unit=derived_unit(log, "ob-b"))
            cases[label] = (e is None, "not independent" in msg)
        finally:
            shutil.rmtree(base, ignore_errors=True)
    ok = all(refused and named for refused, named in cases.values())
    return ok, f"cases={cases}"


def gate_begin_derives():
    """A forged disjoint unit for a conflicting obligation is refused: the authority derives, not trusts."""
    fr = need("stored_unit")
    if fr is None:
        return False, ABSENT
    log, base = build("bderive", [("ob-a", cv.OUTCOME, "integration"), ("ob-b", cv.EVIDENCE, "integration")])
    try:
        raw_epoch(log, "ob-a")
        forged = {"id": "gate:ob-b", "kind": "gate", "obligation": "ob-b", "gate_class": "unit",
                  "reads": ["elsewhere"], "writes": ["run:elsewhere"], "resources": []}
        with switch("on"):
            e1, m1 = try_begin(log, "ob-b", unit=forged)
            e2, m2 = try_begin(log, "ob-b", unit=derived_unit(log, "ob-b"))
        ok = e1 is None and "does not match derived" in m1 and e2 is None and "not independent" in m2
        return ok, f"forged='{m1[:48]}' honest_but_conflicting='{m2[:40]}'"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_begin_admits():
    """The control: disjoint declared units are admitted and the fences strictly increase."""
    fr = need("stored_unit")
    if fr is None:
        return False, ABSENT
    log, base = three_obligation_log("badmit")
    try:
        got = []
        with switch("on"):
            for oid in ("ob-a", "ob-b", "ob-c"):
                e, msg = try_begin(log, oid, unit=derived_unit(log, oid))
                got.append((e.fence if e else None, msg))
        stored = [e.spec.get("unit") for e in ep.project_epochs(gc.project(log)).values()]
        ok = [g[0] for g in got] == [1, 2, 3] and all(u and u["obligation"] for u in stored)
        return ok, f"fences={[g[0] for g in got]} refusals={[g[1][:30] for g in got if g[1]]} stored_units={len(stored)}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _sweep_case(name, n, posture_name, **budget):
    repo = make_repo()
    log, base = sweep_goal_for(name, n, posture_name, repo, **budget)
    run_dir = Path(tempfile.mkdtemp(prefix="frontier-run-"))
    try:
        with switch("on"):
            first = sw.sweep_goal(log, repo, providers=("gate",), run_dir=run_dir)
            dispatched = sum(1 for a in first if "dispatched" in a)
            opened = open_count(log)
            rest = drain(log, repo, run_dir)
        satisfied = sum(1 for o in cv.project_convergence(gc.project(log)).obligations.values()
                        if o.disposition == cv.SATISFIED)
        return dispatched, opened, satisfied, "DRAIN TIMEOUT" in rest, first
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(repo, ignore_errors=True)
        shutil.rmtree(run_dir, ignore_errors=True)


def gate_sweep_n():
    if need("stored_unit") is None:
        return False, ABSENT
    wall = _sweep_case("sweep-wall", 3, "WALL_CLOCK")
    eco = _sweep_case("sweep-eco", 3, "ECONOMY")
    ok = (wall[0] == 3 and wall[1] == 3 and wall[2] == 3 and not wall[3]
          and eco[0] == 1 and eco[1] == 1 and eco[2] == 3 and not eco[3])
    return ok, f"WALL_CLOCK dispatched={wall[0]} open={wall[1]} satisfied_after_drain={wall[2]}; ECONOMY dispatched={eco[0]} open={eco[1]} satisfied_after_drain={eco[2]}"


def gate_sweep_bound():
    if need("stored_unit") is None:
        return False, ABSENT
    capped = _sweep_case("sweep-cap", 4, "WALL_CLOCK", max_parallel=2)
    five = _sweep_case("sweep-five", 5, "WALL_CLOCK")
    bal = _sweep_case("sweep-bal", 4, "BALANCED")
    ok = capped[0] == 2 and capped[1] == 2 and five[0] == 4 and five[1] == 4 and bal[0] == 2 \
        and not (capped[3] or five[3] or bal[3])
    return ok, f"max_parallel=2 -> {capped[0]}; WALL_CLOCK over 5 ready -> {five[0]} open={five[1]}; BALANCED -> {bal[0]}"


def gate_lostrace():
    """Two dispatchers decided from one stale state: exactly one begin wins, no duplicate fence."""
    if need("stored_unit") is None:
        return False, ABSENT
    log, base = three_obligation_log("race")
    try:
        stale = gc.project(log)
        spec = lambda oid: {"obligation": oid, "tree_hash": TREE,   # noqa: E731
                            "gate": {"id": oid, "command": [], "class": "unit", "files": []}}
        outcomes = []
        with switch("on"):
            for oid in ("ob-a", "ob-b"):
                try:
                    unit = derived_unit(log, oid)
                    ep.begin(log, stale, "gate", spec(oid), f"race-{oid}", "initial", "t", unit=unit)
                    outcomes.append("won")
                except (gl.LostRace, ep.EpochError) as exc:
                    outcomes.append(type(exc).__name__)
        fences = [e.fence for e in ep.project_epochs(gc.project(log)).values()]
        ok = outcomes.count("won") == 1 and len(fences) == len(set(fences)) == 1
        return ok, f"outcomes={outcomes} fences={fences}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_fence():
    """Each concurrent epoch ingests only with its own fence and run_token."""
    if need("stored_unit") is None:
        return False, ABSENT
    log, base = three_obligation_log("fence")
    try:
        a = raw_epoch(log, "ob-a")
        b = raw_epoch(log, "ob-b")
        eps = ep.project_epochs(gc.project(log))
        ea, eb = eps[a], eps[b]
        def receipt(own, other):
            return ep.Receipt(epoch_id=own.epoch_id, provider="gate", revision=own.revision,
                              fence=other.fence, goal_id=other.identity["goal_id"],
                              run_token=other.identity["run_token"])
        refused = False
        try:
            ep.ingest_receipt(log, gc.project(log), receipt(ea, eb), "t")
        except ep.ReceiptRefused:
            refused = True
        own_ok = bool(ep.ingest_receipt(log, gc.project(log), receipt(ea, ea), "t"))
        own_b = bool(ep.ingest_receipt(log, gc.project(log), receipt(eb, eb), "t"))
        ok = ea.fence != eb.fence and refused and own_ok and own_b
        return ok, f"fences={ea.fence},{eb.fence} sibling_fence_refused={refused} own_receipts_ingested={own_ok and own_b}"
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
    ("V-FRONTIER-PRIOR", gate_prior),
    ("V-FRONTIER-ORDER", gate_order),
    ("V-FRONTIER-FAILURE-FIRST", gate_failure_first),
    ("V-FRONTIER-INFOGAIN", gate_infogain),
    ("V-FRONTIER-CRITICAL-PATH", gate_critical_path),
    ("V-FRONTIER-POSTURE", gate_posture),
    ("V-FRONTIER-CLASSES", gate_classes),
    ("V-FRONTIER-COMPILE-ORDERS", gate_compile_orders),
    ("V-FRONTIER-GLOBAL-WAIT", gate_global_wait),
    ("V-FRONTIER-LEGACY-EQUAL", gate_legacy_equal),
    ("V-FRONTIER-SIGNATURE", gate_signature),
    ("V-FRONTIER-HARVEST-NOT-HIDDEN", gate_harvest_not_hidden),
    ("V-FRONTIER-NO-STARVE", gate_no_starve),
    ("V-FRONTIER-STOP-HOLDS", gate_stop_holds),
    ("V-FRONTIER-BUDGET-HOLDS", gate_budget_holds),
    ("V-FRONTIER-CLOSURE-HOLDS", gate_closure_holds),
    ("V-FRONTIER-BLOCKED-ON-HOLDS", gate_blocked_on_holds),
    ("V-FRONTIER-WAIT-ONLY-EMPTY", gate_wait_only_empty),
    ("V-FRONTIER-BEGIN-REFUSES", gate_begin_refuses),
    ("V-FRONTIER-UNSAFE-WRITES", gate_unsafe_writes),
    ("V-FRONTIER-BEGIN-DERIVES", gate_begin_derives),
    ("V-FRONTIER-BEGIN-ADMITS", gate_begin_admits),
    ("V-FRONTIER-SWEEP-N", gate_sweep_n),
    ("V-FRONTIER-SWEEP-BOUND", gate_sweep_bound),
    ("V-FRONTIER-LOSTRACE", gate_lostrace),
    ("V-FRONTIER-FENCE", gate_fence),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_FRONTIER_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
