#!/usr/bin/env python3
"""V-GOAL-AUTOPSY-* gates (R5): goal-autopsy is read-only and reproduces the ce-a3b incident table;
a bound session's terminal refusal / SessionEnd leaves a Fault Capsule.

    python tools/test_goal_autopsy.py
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PP))
import mission_spend as ms  # noqa: E402

HOST = socket.gethostname()
passes = fails = 0

# card section 1 (vault/plans/ce-a3b-recovery-2026-10-08.md): sid, calls, processed, pre-bind, pre-bind calls, refusals
INCIDENT = (
    ("116de5ca", 10, 1_160_335, 0, 0, 0),
    ("2494f14c", 29, 3_993_419, 629_367, 5, 2),
    ("9437261e", 4, 435_148, 0, 0, 1),
    ("f538b230", 8, 1_077_180, 797_740, 2, 1),
)
EXPECTED_TABLE = (
    "sid      calls processed   pre_bind  bound      refusals open_holds\n"
    "116de5ca 10    1,160,335   0         1,160,335  0        1\n"
    "2494f14c 29    3,993,419   629,367   3,364,052  2        0\n"
    "9437261e 4     435,148     0         435,148    1        1\n"
    "f538b230 8     1,077,180   797,740   279,440    1        0\n"
    "TOTAL    51    6,666,082   1,427,107 5,238,975  4        2\n"
)


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


class Env:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="autopsy_"))
        self.state = self.root / "state"
        self.state.mkdir()
        self.goalroot = self.root / "goalroot"
        self.goalroot.mkdir()
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.saved = {k: os.environ.get(k) for k in ("GSD_LONG_RUN_STATE_DIR", "CLAUDECODE", "CPP_GOAL")}
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(self.state)
        os.environ.pop("CLAUDECODE", None)
        os.environ.pop("CPP_GOAL", None)

    def close(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.root, ignore_errors=True)


def _row(mid, n, cwd, ts):
    u = {"input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    return json.dumps({"type": "assistant", "timestamp": ts, "uuid": "u-" + mid, "cwd": str(cwd),
                       "message": {"id": mid, "model": "claude-opus-5-5", "usage": u,
                                   "content": [{"type": "text", "text": "x"}]}}) + "\n"


def _refusal(i, cwd, ts):
    return json.dumps({"type": "user", "timestamp": ts, "uuid": f"r{i}", "cwd": str(cwd), "message": {
        "role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}",
                                     "content": "GOAL BUDGET (g) -- budget_spent"}]}}) + "\n"


def write_session(path, sid, calls, total, pre, pre_calls, refusals, inside, outside):
    parts, ts = [], 0
    nb = calls - pre_calls
    for i in range(calls):
        if i < pre_calls:
            n, cwd = pre // pre_calls, outside
            if i == pre_calls - 1:
                n = pre - (pre // pre_calls) * (pre_calls - 1)
        else:
            k = i - pre_calls
            n, cwd = (total - pre) // nb, inside
            if k == nb - 1:
                n = (total - pre) - ((total - pre) // nb) * (nb - 1)
        ts += 1
        parts.append(_row(f"{sid}-{i}", n, cwd, f"2099-01-01T00:{ts:02d}:00.000Z"))
    for j in range(refusals):
        parts.append(_refusal(j, inside, f"2099-01-01T01:{j:02d}:00.000Z"))
    path.write_text("".join(parts), encoding="utf-8")


def build_incident(e):
    ms.goal_declare("g", 50_000_000, "test", [str(e.goalroot)], None, 1, owner=True)
    proj = e.root / "projects" / "p"
    proj.mkdir(parents=True)
    for sid, calls, total, pre, pre_calls, refusals in INCIDENT:
        write_session(proj / f"{sid}.jsonl", sid, calls, total, pre, pre_calls, refusals, e.goalroot, e.outside)
    for sid in ("116de5ca", "9437261e"):          # the two workers keep an open lease; the panes settled
        ms.goal_renew("g", sid, 0, 1000, HOST)
    for sid in ("2494f14c", "f538b230"):
        ms.goal_renew("g", sid, 0, 1000, HOST)
        ms.goal_renew("g", sid, 1, 1000, HOST)    # renew settles + re-leases; close it by settling explicitly
    led = ms._goal_ledger("g")
    with led._lock:
        recs = led._read()
        g = led._gfold(recs)
        for sid in ("2494f14c", "f538b230"):
            closes = sorted(r for r, v in g["res"].items() if v["sid"] == sid and v["state"] in ("RESERVED", "LEAKED"))
            led._append(recs, {"op": "settle", "sid": sid, "measured": 5, "closes": closes})
    return e.root / "projects"


def _autopsy(*a, **k):
    try:
        return ms.goal_autopsy(*a, **k)
    except AttributeError:
        return {"ok": False, "reason": "goal_autopsy is not implemented", "sessions": []}


def _table(out):
    try:
        return ms.autopsy_table(out)
    except AttributeError:
        return ""


def g_autopsy():
    e = Env()
    try:
        projects = build_incident(e)
        jr = ms._goal_ledger("g").journal
        before = jr.read_bytes()
        # (a) inspectable from an UNBOUND session (cwd outside every root), zero rows added
        os.chdir(e.outside)
        out = _autopsy("g", projects=projects)
        check("V-GOAL-AUTOPSY-READONLY", jr.read_bytes() == before and out.get("ok", False),
              f"autopsy ok={out.get('ok')} journal bytes unchanged ({len(before)})")
        # control: the same call on an undeclared goal is refused (not an empty success)
        bad = _autopsy("nope", projects=projects)
        check("V-GOAL-AUTOPSY-UNDECLARED", not bad.get("ok", False), f"undeclared goal -> {bad.get('reason', '')[:50]}")
        # (c) the incident table, byte-identical
        tbl = _table(out)
        check("V-GOAL-AUTOPSY-INCIDENT", tbl == EXPECTED_TABLE, "incident table byte-identical" if tbl == EXPECTED_TABLE
              else "table differs:\n" + tbl)
        check("V-GOAL-AUTOPSY-SPLIT", out.get("workers_processed") == 1_595_483 and out.get("panes_processed") == 5_070_599
              and out.get("pre_bind_processed") == 1_427_107,
              f"workers {out.get('workers_processed')} panes {out.get('panes_processed')} retro {out.get('pre_bind_processed')}")
        check("V-GOAL-AUTOPSY-GIT", isinstance(out.get("git"), dict) and {"head", "dirty"} <= set(out["git"]),
              f"git {out.get('git')}")
        # deterministic: two runs, identical text
        check("V-GOAL-AUTOPSY-DETERMINISTIC", _table(_autopsy("g", projects=projects)) == tbl and tbl != "", "second run identical")
    finally:
        os.chdir(PP)
        e.close()


def _fault(*a, **k):
    try:
        return ms.goal_fault_capsule(*a, **k)
    except AttributeError:
        return {"verdict": "NOT_IMPLEMENTED"}


def g_fault():
    e = Env()
    try:
        build_incident(e)
        sd = e.root / "rollover"
        tx = e.root / "projects" / "p" / "9437261e.jsonl"
        kw = dict(sd=sd, transcript=str(tx), ask=lambda wd, ws: (None, "test"),
                  children={"verdict": "NONE", "pending": [], "unconsumed": []})
        # (b) a killed bound worker (SessionEnd while bound) leaves a capsule
        r = _fault("g", "9437261e", str(e.goalroot), "SessionEnd", **kw)
        files = [p for p in sd.rglob("*") if p.is_file() and "9437261e" in (p.name + p.read_text(errors="replace"))] \
            if sd.exists() else []
        check("V-GOAL-AUTOPSY-FAULT-SESSIONEND", bool(r) and r.get("key") and bool(files),
              f"bound SessionEnd -> key {r and r.get('key')} files {len(files)}")
        # a terminal goal refusal writes one too, with the reason in the note
        r2 = _fault("g", "116de5ca", str(e.goalroot), "refused: budget_spent", **kw)
        check("V-GOAL-AUTOPSY-FAULT-REFUSAL", bool(r2) and r2.get("key") and r2.get("key") != (r or {}).get("key"),
              f"bound refusal -> key {r2 and r2.get('key')}")
        # control: an UNBOUND session (cwd outside every root) leaves nothing
        n = len(list(sd.rglob("*")))
        r3 = _fault("g", "f538b230", str(e.outside), "SessionEnd", **kw)
        check("V-GOAL-AUTOPSY-FAULT-UNBOUND", r3 is None and len(list(sd.rglob("*"))) == n,
              f"unbound -> {r3}, files {n} -> {len(list(sd.rglob('*')))}")
        # no new capsule format: it is a mission capsule (kind mission, rollover-capsule-v2)
        cap = next((json.loads(p.read_text()) for p in sd.rglob("*.json")
                    if '"rollover-capsule-v2"' in p.read_text(errors="replace")), {})
        check("V-GOAL-AUTOPSY-FAULT-FORMAT", cap.get("kind") == "mission" and cap.get("schema") == "rollover-capsule-v2",
              f"kind {cap.get('kind')} schema {cap.get('schema')}")
    finally:
        e.close()


def main():
    for g in (g_autopsy, g_fault):
        try:
            g()
        except Exception as ex:
            check(f"V-GOAL-AUTOPSY-{g.__name__}", False, f"crashed: {type(ex).__name__}: {ex}")
    print(f"AUTOPSY_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
