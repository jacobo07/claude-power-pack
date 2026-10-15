#!/usr/bin/env python3
"""V-RLEASE-* gates for resource leases in modules/lease/store.py (ccr-v5 phase 3, plan 03-02).

Every refusal gate carries an admitted control, so a store that refused everything fails the
controls. Mutants are exact text replacements on TEMP COPIES of store.py (each replacement is
asserted to change the text); the loaded production file is never mutated. Exit 0 pass, 1 fail,
2 INCONCLUSIVE (never a pass).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from modules.lease import (ACTIVE, EXPIRED, QUEUE_WAIT_EXCEEDED, RELEASED, RESERVED,  # noqa: E402
                           JournalCorrupt, LeaseStore, resource_id)
import modules.lease.store as store_mod  # noqa: E402

T0 = 1_800_000_000.0
P = "vault/knowledge_base/ukdl-universal.md"
STORE_SRC = ROOT / "modules" / "lease" / "store.py"
PRE_SHA = ROOT / "vault" / "programs" / "ccr" / "v5" / "phase3" / "lease-pre.sha"

passes = fails = inconclusive = 0


def _ok(gate, msg):
    global passes
    passes += 1
    print(f"  PASS {gate}: {msg}")


def _fail(gate, msg):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {msg}")


def _inc(gate, msg):
    global inconclusive
    inconclusive += 1
    print(f"  INCONCLUSIVE {gate}: {msg}")


def check(gate, cond, good, bad):
    (_ok if cond else _fail)(gate, good if cond else bad)


class Clock:
    def __init__(self, t=T0):
        self.t = t

    def __call__(self):
        return self.t


def fresh(clock=None, min_ttl=10.0, mod=None, host="h"):
    d = Path(tempfile.mkdtemp(prefix="rlease-"))
    cls = (mod or store_mod).LeaseStore
    return cls(d, min_ttl_s=min_ttl, clock=clock or Clock(), host=host), d


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def acq(s, paths, holder="A", lid="L1", base=None, intent="merge ccr/v5", ttl=60, **kw):
    paths = [paths] if isinstance(paths, str) else list(paths)
    if base is None:
        base = {p: "rev-" + p for p in paths}
    return s.acquire_resources(paths, holder, ttl, lid, intent, base, **kw)


def lines(d):
    return (d / store_mod.JOURNAL).read_text(encoding="utf-8").splitlines() \
        if (d / store_mod.JOURNAL).exists() else []


def wait_row():
    return {
        "wait_id": "w-1", "kind": "WAIT_ON_RESOURCE", "state": "OPEN", "goal": "ccr", "wu": "P3-merge",
        "opened_at": T0, "timeout_at": T0 + 3600.0, "live_head_at_open": "77e1cbf0",
        "resources": [{"path": P, "writer": {"verdict": "LIVE"}}],
        "expected_event": ["COMMIT", "LEASE_RELEASE", "WRITER_DEAD"],
        "resume_action": {"kind": "land_worktree", "strategy": "merge", "worktree": "wt/ccr-v5",
                          "live": "main", "branch": "ccr/v5"},
        "validation": {"tests": ["python tools/test_lease.py"], "rollback": "any_red", "baseline_red": []},
    }


# --------------------------------------------------------------------------- Task 1 gates

def g_id_normalized():
    same = {resource_id(x) for x in
            ("A/B/c.md", "a\\b\\c.md", "./a/b/c.md", "a//b///c.md", ".\\a\\.\\B\\C.MD", "a/b/./c.md")}
    refused, missed = 0, []
    bad = ["/etc/passwd", "\\\\srv\\share\\x", "C:/x.md", "c:\\x.md", "a/../b", "../a", "a/b:stream",
           "a/b./c", "a/b /c", "a/b.", "a\x00b", "", ".", "./", "...", None, 5]
    for b in bad:
        try:
            resource_id(b)
            missed.append(repr(b))
        except ValueError:
            refused += 1
    distinct = len({resource_id(x) for x in ("a/b.md", "a/c.md", "a/b/c.md", "ab/c.md", "a/bc.md")}) == 5
    check("V-RLEASE-ID-NORMALIZED", len(same) == 1 and not missed and distinct,
          f"6 spellings -> {same}; {refused} unkeyable paths refused; 5 distinct files stay distinct",
          f"same={same} admitted={missed} distinct={distinct}")


def g_records_meta():
    s, d = fresh()
    r = acq(s, P, writer={"pid": 4242, "session": "sess-1", "cwd": "C:/x"})
    st = s.resource_status([P])[P]
    rec = json.loads(lines(d)[0])
    lease = s._fold(s.records())[0]["L1"]
    want = {"intent": "merge ccr/v5", "base": {P.lower(): "rev-" + P},
            "writer": {"pid": 4242, "session": "sess-1", "cwd": "C:/x"}}
    check("V-RLEASE-ACQUIRE-RECORDS-META",
          r.ok and rec["op"] == "grant" and rec["meta"] == want and lease.meta == want
          and st["intent"] == want["intent"] and st["base"] == "rev-" + P and st["writer"] == want["writer"]
          and st["free"] is False and st["state"] == RESERVED and st["holder"] == "A",
          "grant record, folded Lease.meta and resource_status all carry intent, base and writer",
          f"r={r} rec={rec} lease_meta={lease.meta} st={st}")


def g_exclusive():
    s, _ = fresh()
    a = acq(s, "Vault/KB/x.md", "A", "L1")
    b = acq(s, "vault\\kb\\X.md", "B", "L2")
    c = acq(s, "./vault/kb/x.md", "A", "L3")
    ok_other = acq(s, "vault/kb/y.md", "B", "L4")
    check("V-RLEASE-EXCLUSIVE-BY-RESOURCE-NOT-REQUESTER",
          a.ok and not b.ok and b.reason == "held" and "res:vault/kb/x.md" in b.state
          and not c.ok and c.reason == "held" and ok_other.ok,
          "other holder (other spelling) and same holder (new lease id) both HELD; unrelated path admitted",
          f"a={a} b={b} c={c} other={ok_other}")


def g_all_or_nothing():
    s, d = fresh()
    acq(s, "b.md", "A", "L1")
    n0 = len(lines(d))
    r = acq(s, ["a.md", "b.md", "c.md"], "B", "L2")
    n1 = len(lines(d))
    s2, d2 = fresh()
    r2 = acq(s2, ["a.md", "b.md", "c.md"], "B", "L2")
    # fences are per class generations (each starts at 1); distinctness is by class key
    check("V-RLEASE-ALL-OR-NOTHING-MULTI",
          not r.ok and r.reason == "held" and n0 == n1 and r2.ok
          and sorted(r2.fences) == ["res:a.md", "res:b.md", "res:c.md"]
          and all(isinstance(v, int) and v >= 1 for v in r2.fences.values()),
          "one busy path of three refuses all, journal unchanged; control grants all three with a fence each",
          f"r={r} n0={n0} n1={n1} r2={r2}")


def g_no_base():
    s, _ = fresh()
    bad = {
        "missing key": acq(s, "a.md", lid="N1", base={"other.md": "r"}),
        "empty string": acq(s, "a.md", lid="N2", base={"a.md": ""}),
        "blank string": acq(s, "a.md", lid="N3", base={"a.md": "   "}),
        "non-string": acq(s, "a.md", lid="N4", base={"a.md": 7}),
        "none": acq(s, "a.md", lid="N5", base={"a.md": None}),
        "wrong container": s.acquire_resources(["a.md"], "A", 60, "N6", "i", ["a.md"]),
        "no mapping": s.acquire_resources(["a.md"], "A", 60, "N7", "i", None),
        "one of two missing": acq(s, ["a.md", "b.md"], lid="N8", base={"a.md": "r"}),
    }
    miss = [k for k, v in bad.items() if v.ok or v.reason != "no_base"]
    ctl = acq(s, "a.md", lid="N9", base={"A.MD": "r1"})
    absent = acq(s, "z.md", lid="N10", base={"z.md": "absent"})
    check("V-RLEASE-REFUSES-NO-BASE", not miss and ctl.ok and absent.ok,
          "8 shapes of missing base all refused no_base; complete base and the literal 'absent' admitted",
          f"miss={miss} ctl={ctl} absent={absent}")


def g_no_intent():
    s, _ = fresh()
    cases = {"missing": None, "empty": "", "blank": "  \t", "over-length": "x" * 201, "non-string": 5}
    bad = {k: acq(s, "a.md", lid=f"I{i}", intent=v) for i, (k, v) in enumerate(cases.items())}
    miss = [k for k, v in bad.items() if v.ok or v.reason != "no_intent"]
    ctl = acq(s, "a.md", lid="I9", intent="x" * 200)
    check("V-RLEASE-REFUSES-NO-INTENT", not miss and ctl.ok,
          "5 shapes of missing intent refused no_intent; a 200-char intent admitted",
          f"miss={miss} ctl={ctl}")


def g_tracer():
    mr = load(TOOLS / "mission_recovery.py", "mission_recovery_rl")
    clock = Clock()
    s, _ = fresh(clock)
    r = acq(s, P, "A", "LT", writer={"session": "writer-a"})
    disp = s.dispatch("LT", "A", r.fences)

    def evidence(dirty, writer="LIVE"):
        st = s.resource_status([P])[P]
        return {P: {"dirty": dirty, "committed_since_open": False,
                    "lease": {"free": st["free"], "state": st["state"], "holder": st["holder"]},
                    "writer": writer}, "other_paths": 3}

    row = wait_row()
    held = mr.wait_decision(row, evidence(True), clock())
    held_clean = mr.wait_decision(row, evidence(False), clock())      # control: clean but still leased
    rel = s.release("LT", "A", r.fences)
    after = mr.wait_decision(row, evidence(False), clock())
    check("V-RLEASE-TRACER-LEASE-TO-WAIT-DECISION",
          r.ok and disp.ok and rel.ok and held["action"] == "WAIT"
          and held_clean["action"] != "RESUME" and after["action"] == "RESUME"
          and after["event"] == "LEASE_RELEASE",
          "held+dirty -> WAIT; clean-but-leased never RESUME; after release -> RESUME(LEASE_RELEASE)",
          f"held={held} held_clean={held_clean} after={after} disp={disp} rel={rel}")


GATES_T1 = [g_id_normalized, g_records_meta, g_exclusive, g_all_or_nothing, g_no_base, g_no_intent,
            g_tracer]
GATES_T2: list = []


def main() -> int:
    for g in GATES_T1 + GATES_T2:
        g()
    total = passes + fails + inconclusive
    print(f"RLEASE_PASS={passes}/{total}")
    if fails:
        return 1
    return 2 if inconclusive else 0


if __name__ == "__main__":
    sys.exit(main())
