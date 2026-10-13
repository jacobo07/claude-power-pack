#!/usr/bin/env python3
"""Phase 5 / 05-02: bounded parallel REPLAY in the independent judge (D16).

Concurrency is proven by RENDEZVOUS, never by timing alone: a `meet` gate writes its own start marker and
waits for its peers' markers. Two gates that overlap both pass; two that run one after the other cannot
meet, so the first fails. Disjointness is read from start/end stamps the gates write themselves.

Summary line: GSDX_REPLAY_PARALLEL_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="rp-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="rp-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)
os.environ.pop("GSDX_GOAL_EPOCH", None)
os.environ.pop("GSDX_FRONTIER", None)
os.environ.pop("GSDX_REPLAY_MAX", None)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import git_state as gs          # noqa: E402
from modules.gsd_x.goal import judge as jd              # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402
from modules.gsd_x.mission import closure as mcl        # noqa: E402

try:
    from modules.gsd_x.goal import replay as rp          # noqa: E402
except ImportError:
    rp = None

REPO_ID = "8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c"
PY = f'"{sys.executable}"'
RV_SRC = '''import os, sys, time
me, mode, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
d = os.environ["RP_DIR"]
def p(n): return os.path.join(d, n)
def stamp(n): open(p(n), "w").write(repr(time.time()))
stamp(me + ".start")
if mode == "meet":
    end = time.time() + float(os.environ.get("RP_WAIT", "20"))
    while time.time() < end and not all(os.path.exists(p(x + ".start")) for x in rest):
        time.sleep(0.02)
    ok = all(os.path.exists(p(x + ".start")) for x in rest)
    stamp(me + ".end")
    sys.exit(0 if ok else 3)
if mode == "hold":
    open(p("active." + me), "w").close()
    open(p("seen." + me), "w").write(str(len([f for f in os.listdir(d) if f.startswith("active.")])))
    time.sleep(float(rest[0]) if rest else 1.0)
    os.remove(p("active." + me))
    stamp(me + ".end")
    sys.exit(0)
if mode == "fail":
    stamp(me + ".end")
    sys.exit(2)
if mode == "sleep":
    time.sleep(float(rest[0]))
    stamp(me + ".end")
    sys.exit(0)
stamp(me + ".end")
sys.exit(0)
'''

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


def _st(log):
    return gc.project(log)


def need_replay():
    return None if rp is not None else (False, "RED-first: modules.gsd_x.goal.replay absent")


class RP:
    """A tmp git repo and N satisfied obligations whose gates are `rv.py <oid> <mode> ...`.

    `gates` is a list of (oid, mode, args, gate_class). The goal is satisfied by plain verdicts (no
    certificates), so every judge call here replays.
    """

    def __init__(self, name, gates, budget=None, wait="20"):
        self.repo = Path(tempfile.mkdtemp(prefix="rp-repo-"))
        self.base = Path(tempfile.mkdtemp(prefix="rp-"))
        self.dir = self.base / "marks"
        self.dir.mkdir()
        os.environ["RP_DIR"] = str(self.dir)
        os.environ["RP_WAIT"] = wait
        (self.repo / "rv.py").write_text(RV_SRC, encoding="utf-8", newline="\n")
        (self.repo / "other.py").write_text("print('ok')\n", encoding="utf-8", newline="\n")
        for args in (("init", "-q"), ("config", "user.name", "t"), ("config", "user.email", "t@t"),
                     ("config", "core.autocrlf", "false"), ("add", "-A"), ("commit", "-q", "-m", "base")):
            rc_, out = gs._git(self.repo, *args)
            if rc_ != 0:
                raise RuntimeError(f"git {args[0]} failed: {out}")
        self.log = GoalLog(REPO_ID, name, base=self.base)
        gc.declare(self.log, "Replay parallel", ["it works"], [], {"paths": ["."]}, actor="founder")
        if budget is not None:
            gc.set_budget(self.log, _st(self.log).last_seq + 1, budget, "founder")
        for plane in cv.PLANES:
            cv.set_plane(self.log, _st(self.log), plane, plane in cv.ALWAYS,
                         "" if plane in cv.ALWAYS else "not claimed", "founder")
        self.gates = gates
        self.pins = {}
        for oid, mode, args, gate_class in gates:
            script = "other.py" if mode == "other" else "rv.py"
            pin = gs.file_pin(self.repo, [script])
            self.pins[oid] = pin
            cmd = f"{PY} {script}" if mode == "other" else f"{PY} rv.py {oid} {mode} {args}".rstrip()
            cv.accept_obligation(self.log, _st(self.log), oid, cv.OUTCOME, "do " + oid, cmd, pin,
                                 "founder", gate_class=gate_class)
        self.t1 = self.tree()
        for oid, *_rest in gates:
            st = _st(self.log)
            res = cv.satisfy(self.log, st, oid,
                             mcl.Verdict("rv.py", 0, "ok", self.t1, st.revision, "unit", self.pins[oid]),
                             "founder", source={"epoch": "ep-rp", "provider": "gate"})
            if not res.allowed:
                raise RuntimeError(f"fixture: satisfy refused: {res.reason}")

    def tree(self):
        return gs.tree_id(self.repo, ["."])

    def judge(self, timeout_s=jd.DEFAULT_GATE_TIMEOUT_S):
        return jd.judge(_st(self.log), self.tree(), self.repo, scope_paths=["."], timeout_s=timeout_s)

    def stamp(self, name):
        p = self.dir / name
        return float(p.read_text()) if p.exists() else None

    def interval(self, oid):
        return self.stamp(oid + ".start"), self.stamp(oid + ".end")

    def close(self):
        for k in ("RP_DIR", "RP_WAIT"):
            os.environ.pop(k, None)
        shutil.rmtree(self.base, ignore_errors=True)
        shutil.rmtree(self.repo, ignore_errors=True)


def with_ram(mb, fn):
    old = rp.free_ram_mb
    rp.free_ram_mb = lambda: mb
    try:
        return fn()
    finally:
        rp.free_ram_mb = old


def with_env(key, value, fn):
    old = os.environ.get(key)
    try:
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
        return fn()
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


class FakeState:
    def __init__(self, budget):
        self.budget = budget


def disjoint(a, b) -> bool:
    (sa, ea), (sb, eb) = a, b
    return None not in (sa, ea, sb, eb) and (ea <= sb or eb <= sa)


def rows(rec):
    return [(g.get("obligation"), g.get("verdict"), g.get("exit_status")) for g in rec.gates]


def gate_hermetic():
    home = Path.home()
    ok = home.resolve() == _TMP_HOME.resolve() and home.resolve() != REAL_HOME.resolve()
    return ok, f"home={home.name}"


def gate_serial_is_default():
    if (r := need_replay()):
        return r
    default_bound = with_ram(8192, lambda: rp.replay_bound(FakeState({})))
    w = RP("rp-default", [("a", "meet", "b", "unit"), ("b", "meet", "a", "unit")], wait="2")
    try:
        rec = with_ram(8192, w.judge)
        ia, ib = w.interval("a"), w.interval("b")
        ok = default_bound == 1 and disjoint(ia, ib) and rec.verdict == jd.REFUSED
        return ok, f"bound={default_bound} disjoint={disjoint(ia, ib)} verdict={rec.verdict}"
    finally:
        w.close()


def gate_overlaps_under_bound():
    if (r := need_replay()):
        return r
    w = RP("rp-overlap", [("a", "meet", "b", "unit"), ("b", "meet", "a", "unit")],
           budget={"posture": "BALANCED"}, wait="30")
    try:
        rec = with_ram(8192, w.judge)
        ok = rec.verdict == jd.PASS and rows(rec) == [("a", jd.PASS, 0), ("b", jd.PASS, 0)]
        return ok, f"verdict={rec.verdict} rows={rows(rec)}"
    finally:
        w.close()


def gate_receipt_equals_serial():
    if (r := need_replay()):
        return r
    spec = [("a", "hold", "0.3", "unit"), ("b", "fail", "", "unit"), ("c", "hold", "0.3", "unit"),
            ("d", "hold", "0.3", "unit")]
    out = {}
    for label, budget in (("serial", None), ("parallel", {"posture": "WALL_CLOCK"})):
        w = RP("rp-eq-" + label, spec, budget=budget)
        try:
            rec = with_ram(8192, w.judge)
            out[label] = (rec.verdict, rows(rec), rec.reason.split(":")[0])
        finally:
            w.close()
    ok = out["serial"][:2] == out["parallel"][:2] and out["serial"][0] == jd.REFUSED \
        and [r[0] for r in out["serial"][1]] == ["a", "b", "c", "d"]
    return ok, f"serial={out['serial'][:2]} parallel={out['parallel'][:2]}"


def gate_bound_never_exceeded():
    if (r := need_replay()):
        return r
    spec = [(x, "hold", "1.0", "unit") for x in "abcdef"]
    w = RP("rp-bound", spec, budget={"posture": "BALANCED"})
    try:
        rec = with_ram(8192, w.judge)
        seen = [int((w.dir / f"seen.{x}").read_text()) for x in "abcdef"]
        ok = rec.verdict == jd.PASS and max(seen) == 2
        return ok, f"bound=2 seen={seen} verdict={rec.verdict}"
    finally:
        w.close()


def gate_resource_serialises():
    if (r := need_replay()):
        return r
    w = RP("rp-res", [("a", "hold", "0.8", "integration"), ("b", "hold", "0.8", "integration")],
           budget={"posture": "WALL_CLOCK"})
    try:
        rec = with_ram(8192, w.judge)
        ia, ib = w.interval("a"), w.interval("b")
        return rec.verdict == jd.PASS and disjoint(ia, ib), f"disjoint={disjoint(ia, ib)} verdict={rec.verdict}"
    finally:
        w.close()


def gate_undeclared_serialises():
    if (r := need_replay()):
        return r
    live = {"now": 0, "max": 0}
    lock = threading.Lock()

    def one(item):
        with lock:
            live["now"] += 1
            live["max"] = max(live["max"], live["now"])
        time.sleep(0.15)
        with lock:
            live["now"] -= 1
        return item

    undeclared = {"reads": None, "writes": None, "resources": None}
    declared = [{"reads": [], "writes": [f"run:{i}"], "resources": []} for i in range(4)]
    got = rp.run_bounded([1, 2, 3, 4], one, 4, declared)          # control: declared units do overlap
    declared_max = live["max"]
    live.update(now=0, max=0)
    got_u = rp.run_bounded([1, 2, 3, 4], one, 4, [dict(undeclared) for _ in range(4)])
    undeclared_max = live["max"]
    ok = got == got_u == [1, 2, 3, 4] and declared_max == 4 and undeclared_max == 1
    return ok, f"declared_max={declared_max} undeclared_max={undeclared_max}"


def gate_memory_lowers():
    if (r := need_replay()):
        return r
    st = FakeState({"posture": "WALL_CLOCK"})
    got = {mb: rp.replay_bound(st, free_mb=mb) for mb in (8192, 3072, 2048, 1536, 1024, 0, None)}
    want = {8192: 4, 3072: 4, 2048: 2, 1536: 2, 1024: 1, 0: 1, None: 1}
    capped = with_env(rp.MAX_ENV, "2", lambda: rp.replay_bound(st, free_mb=8192))
    ignored = [with_env(rp.MAX_ENV, v, lambda: rp.replay_bound(st, free_mb=8192)) for v in ("0", "abc", "-3")]
    ok = got == want and capped == 2 and ignored == [4, 4, 4]
    return ok, f"bounds={got} env_cap={capped} bad_env={ignored}"


def gate_kill_switch():
    if (r := need_replay()):
        return r
    st = FakeState({"posture": "WALL_CLOCK"})
    off = with_env("GSDX_FRONTIER", "off", lambda: rp.replay_bound(st, free_mb=8192))
    on = rp.replay_bound(st, free_mb=8192)
    return off == 1 and on == 4, f"off={off} on={on}"


def gate_bool_cap_ignored():
    if (r := need_replay()):
        return r
    boolean = rp.replay_bound(FakeState({"posture": "WALL_CLOCK", "max_parallel": True}), free_mb=8192)
    lowered = rp.replay_bound(FakeState({"posture": "WALL_CLOCK", "max_parallel": 2}), free_mb=8192)
    return boolean == 4 and lowered == 2, f"bool_cap={boolean} int_cap={lowered}"


def gate_all_joined():
    if (r := need_replay()):
        return r
    finished = []

    def one(item):
        if item == 0:
            time.sleep(0.05)
            raise RuntimeError("boom")
        time.sleep(0.4)
        finished.append(item)
        return item

    units = [{"reads": [], "writes": [f"run:{i}"], "resources": []} for i in range(3)]
    raised = False
    try:
        rp.run_bounded([0, 1, 2], one, 3, units)
    except RuntimeError:
        raised = True
    return raised and sorted(finished) == [1, 2], f"raised={raised} finished_before_return={sorted(finished)}"


def gate_all_joined_judge():
    if (r := need_replay()):
        return r
    spec = [("a", "hold", "0.6", "unit"), ("b", "sleep", "30", "unit"), ("c", "hold", "0.6", "unit")]
    w = RP("rp-join", spec, budget={"posture": "WALL_CLOCK"})
    try:
        rec = with_ram(8192, lambda: w.judge(timeout_s=2.0))
        ended = [w.stamp(f"{x}.end") is not None for x in "ac"]
        ok = rec.verdict == jd.UNJUDGEABLE and all(ended) and [g["obligation"] for g in rec.gates] == ["a", "b", "c"]
        return ok, f"verdict={rec.verdict} ended={ended} ids={[g['obligation'] for g in rec.gates]}"
    finally:
        w.close()


def gate_order_kept():
    if (r := need_replay()):
        return r
    delays = {0: 0.5, 1: 0.05, 2: 0.2}

    def one(item):
        time.sleep(delays[item])
        return item * 10

    units = [{"reads": [], "writes": [f"run:{i}"], "resources": []} for i in range(3)]
    got = rp.run_bounded([0, 1, 2], one, 3, units)
    return got == [0, 10, 20], f"results={got}"


def gate_pin_refusal_in_order():
    if (r := need_replay()):
        return r
    spec = [("a", "hold", "0.2", "unit"), ("b", "other", "", "unit"), ("c", "hold", "0.2", "unit")]
    w = RP("rp-pin", spec, budget={"posture": "WALL_CLOCK"})
    try:
        (w.repo / "other.py").write_text("print('weakened')\n", encoding="utf-8", newline="\n")
        gs._git(w.repo, "add", "-A")
        gs._git(w.repo, "commit", "-q", "-m", "weaken")
        rec = with_ram(8192, w.judge)
        got = [(g["obligation"], g["verdict"]) for g in rec.gates]
        ok = got == [("a", jd.PASS), ("b", jd.REFUSED), ("c", jd.PASS)] and rec.verdict == jd.REFUSED
        return ok, f"rows={got}"
    finally:
        w.close()


GATES = [
    ("V-RP-HERMETIC-HOME", gate_hermetic),
    ("V-RP-SERIAL-IS-DEFAULT", gate_serial_is_default),
    ("V-RP-OVERLAPS-UNDER-BOUND", gate_overlaps_under_bound),
    ("V-RP-RECEIPT-EQUALS-SERIAL", gate_receipt_equals_serial),
    ("V-RP-BOUND-NEVER-EXCEEDED", gate_bound_never_exceeded),
    ("V-RP-RESOURCE-SERIALISES", gate_resource_serialises),
    ("V-RP-UNDECLARED-SERIALISES", gate_undeclared_serialises),
    ("V-RP-MEMORY-LOWERS", gate_memory_lowers),
    ("V-RP-KILL-SWITCH", gate_kill_switch),
    ("V-RP-BOOL-CAP-IGNORED", gate_bool_cap_ignored),
    ("V-RP-ALL-JOINED", gate_all_joined),
    ("V-RP-ALL-JOINED-JUDGE", gate_all_joined_judge),
    ("V-RP-ORDER-KEPT", gate_order_kept),
    ("V-RP-PIN-REFUSAL-IN-ORDER", gate_pin_refusal_in_order),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_REPLAY_PARALLEL_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
