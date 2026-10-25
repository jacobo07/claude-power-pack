#!/usr/bin/env python
"""V-W3C-* gates: MARGINAL_GAIN_LOW -- spend rises, no new commit, the same note restated (KSEIP T1).

Pure-verdict cases, a mutation that must go red, and the supervisor wiring (hold, kill switch).
Hermetic: state in a temp dir before import."""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="w3c-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ.pop("GSD_MARGINAL_GAIN", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
M = 1_000_000


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def s(head, spent, note="n"):
    return {"head": head, "spent": spent, "note_sha": note}


LOW = [s("h", M), s("h", 2 * M), s("h", 3 * M)]
j = gm.judge_marginal_gain

check("V-W3C-LOW", j(LOW) == "MARGINAL_GAIN_LOW", j(LOW))
commit = LOW[:2] + [s("h2", 3 * M)]
check("V-W3C-NEW-COMMIT", j(commit) == "GAINING", j(commit))
note = LOW[:2] + [s("h", 3 * M, "other")]
check("V-W3C-NEW-NOTE", j(note) == "GAINING", j(note))
flat = [s("h", M), s("h", M), s("h", M)]
check("V-W3C-FLAT-SPEND", j(flat) == "GAINING", j(flat))
unm = [s("h", M), s("h", None), s("h", 3 * M)]
check("V-W3C-UNMEASURED", j(unm) == "UNKNOWN" and j(LOW[:2]) == "UNKNOWN" and j([]) == "UNKNOWN",
      f"{j(unm)} {j(LOW[:2])}")


def mutant(samples, window=2):
    """A judge that ignores head: the new-commit case must now read LOW (i.e. the gate goes red)."""
    tail = samples[-(window + 1):]
    if len(tail) < window + 1:
        return "UNKNOWN"
    rises = all(tail[i + 1]["spent"] > tail[i]["spent"] for i in range(window))
    same_note = all(x["note_sha"] == tail[0]["note_sha"] for x in tail)
    return "MARGINAL_GAIN_LOW" if rises and same_note else "GAINING"


real = gm.judge_marginal_gain
gm.judge_marginal_gain = mutant
red = gm.judge_marginal_gain(commit) != "GAINING"   # the NEW-COMMIT assertion would FAIL
gm.judge_marginal_gain = real
judge_red = red and j(commit) == "GAINING"

# --- supervisor wiring ---------------------------------------------------------------------
class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


launches = []
bg = {"session_id": "b-1", "pid": 5151, "kind": "background"}
gone = lambda pid: False   # noqa: E731


def launch_run(argv, cwd):
    launches.append(argv)
    return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")


def stop_run(argv):
    return R("stopped")


gsd_ok = lambda c, workstream=None: {"outcome": "OK", "reason": "ok"}   # noqa: E731
empty_sha = hashlib.sha256(b"").hexdigest()
gm.progress_fingerprint = lambda work_dir: None
import mission_spend  # noqa: E402
SPEND = [4 * M]
HEAD = ["abc"]
mission_spend.processed_tokens = lambda rec: SPEND[0]
gm._git_facts = lambda cwd: {"head": HEAD[0]}


def seeded(mid):
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING,
                  epoch=1, owner={**bg, "session_id": f"s-{mid}"},
                  gain_samples=[s("abc", M, empty_sha), s("abc", 2 * M, empty_sha)])
    return [{"sessionId": f"s-{mid}", "status": "idle", "state": "working", "kind": "background",
             "id": f"s-{mid}"[:8], "pid": 999}]


try:
    hs = seeded("m-w3c-hold")
    n0 = len(launches)
    rows = gm.supervise(now=NOW, sessions=hs, gsd_status=gsd_ok, runner=launch_run, stop_runner=stop_run,
                        pid_alive=gone, fingerprint=lambda d: "B")
    held = gm.load("m-w3c-hold")
    row = next((r for r in rows if r["mission_id"] == "m-w3c-hold"), {})
    check("V-W3C-WIRED-HELD", "marginal_gain_low" in str(row.get("held")) and held["epoch"] == 1
          and len(launches) == n0 and held["state"] != gm.HALTED, str(row))
    os.environ["GSD_MARGINAL_GAIN"] = "off"
    hs = seeded("m-w3c-off")
    gm.supervise(now=NOW, sessions=hs, gsd_status=gsd_ok, runner=launch_run, stop_runner=stop_run,
                 pid_alive=gone, fingerprint=lambda d: "B")
    off = gm.load("m-w3c-off")
    check("V-W3C-WIRED-KILL-SWITCH-RELAYS", off["epoch"] == 2 and len(off.get("gain_samples") or []) == 3,
          f"epoch={off['epoch']} samples={len(off.get('gain_samples') or [])}")
    os.environ.pop("GSD_MARGINAL_GAIN", None)

    def sup(mid, hs):
        return gm.supervise(now=NOW, sessions=hs, gsd_status=gsd_ok, runner=launch_run,
                            stop_runner=stop_run, pid_alive=gone, fingerprint=lambda d: "B")

    def held_rows(mid):
        return [r for r in gm.lr.ledger_events(mid) if r.get("event") == "relay_held"
                and "marginal_gain_low" in str(r.get("reason"))]

    # MEDIUM-1: a path that is NOT launch_worker (the hold) keeps the samples on the record.
    SPEND[0] = 4 * M
    hs = seeded("m-w3c-persist")
    sup("m-w3c-persist", hs)
    p = gm.load("m-w3c-persist")
    check("V-W3C-PERSIST-NON-LAUNCH", p["epoch"] == 1 and len(p.get("gain_samples") or []) == 3,
          f"epoch={p['epoch']} samples={len(p.get('gain_samples') or [])}")
    # LOW-1: identical held pass -> still one row; a changed window -> a second row.
    SPEND[0] = 5 * M
    sup("m-w3c-persist", hs)
    check("V-W3C-HELD-ONE-ROW", len(held_rows("m-w3c-persist")) == 1, f"rows={len(held_rows('m-w3c-persist'))}")
    HEAD[0] = "def"
    # the window moves to another head and holds again (a GAINING pass would relay, so seed it directly)
    gm._persist_gain("m-w3c-persist", 1, [s("def", M, empty_sha), s("def", 2 * M, empty_sha)],
                     gm.load("m-w3c-persist").get("gain_hold"))
    SPEND[0] = 6 * M
    sup("m-w3c-persist", hs)
    n = len(held_rows("m-w3c-persist"))
    check("V-W3C-HELD-CHANGED-ROW", n == 2, f"rows={n}")
    HEAD[0] = "abc"

    # LOW-3: the REAL gate path on a head-blind mutant goes red (held), and the restore relays again.
    HEAD[0] = "new"
    SPEND[0] = 4 * M
    gm.judge_marginal_gain = mutant
    try:
        hs = seeded("m-w3c-mut")
        n0 = len(launches)
        sup("m-w3c-mut", hs)
        mut_held = gm.load("m-w3c-mut")["epoch"] == 1 and len(launches) == n0
    finally:
        gm.judge_marginal_gain = real
    hs = seeded("m-w3c-mut2")
    sup("m-w3c-mut2", hs)
    real_relays = gm.load("m-w3c-mut2")["epoch"] == 2
    check("V-W3C-MUTATION-RED", judge_red and mut_held and real_relays and gm.judge_marginal_gain is real,
          f"judge_red={judge_red} mutant_held={mut_held} real_relays={real_relays}")
except Exception as exc:  # noqa: BLE001
    check("V-W3C-WIRED", False, f"{exc.__class__.__name__}: {exc}")

print(f"W3C_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
