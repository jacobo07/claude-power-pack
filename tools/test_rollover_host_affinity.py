"""V-RHA-* gates: `/kresume` adopts its OWN predecessor's capsule, not a sibling pane's.

Measured 2026-09-30 (614697c1): this pane's predecessor sealed f3099e7b at 19:00, a sibling
pane in the same repo sealed 9e694f9a at 19:11, and `rollover.py resume` -- newest capsule for
the directory -- claimed the sibling's. That both hands the successor the wrong task and locks
the sibling's real successor out (exit 5). `/clear` keeps the claude process, so the seal now
records it (host_identity: CLAUDE_PID + the registry's procStart) and resume prefers a capsule
sealed by its own process, falling back to newest-here exactly as before.

Everything runs against a temp state dir and a temp sessions registry; nothing live is read.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover  # noqa: E402

passes = fails = 0
CWD = r"C:\p\ProjA"
ME = {"pid": 8996, "proc_start": "134352635952515984"}


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def capsule(sid, host=None):
    cap = {"schema": rollover.SCHEMA, "session_id": sid, "cwd": CWD, "session_cwd": CWD,
           "repo": {"root": CWD, "branch": "main", "head": "abcdef1234"},
           "goal": {"state": "OK", "path": CWD + r"\GOAL.md"}, "obligations": [f"next for {sid}"]}
    if host is not None:
        cap["host"] = host
    return cap


def state(*caps_oldest_first):
    d = Path(tempfile.mkdtemp(prefix="rha_"))
    (d / "capsules").mkdir()
    t = time.time() - 600
    for i, cap in enumerate(caps_oldest_first):
        p = d / "capsules" / f"{cap['session_id']}.json"
        p.write_text(json.dumps(cap), encoding="utf-8")
        os.utime(p, (t + i * 60, t + i * 60))   # later argument = newer seal
    return d


def pick(d, host):
    got = rollover.newest_capsule(CWD, state_dir=d, exclude="succ", host=host)
    return got and got["session_id"]


def main():
    # Arrange: own predecessor sealed first, a sibling pane sealed later in the same repo.
    sibling = {"pid": 4242, "proc_start": "999"}
    d = state(capsule("own-pred", ME), capsule("sibling", sibling))
    check("V-RHA-PREFERS-OWN-HOST", pick(d, ME) == "own-pred", f"picked={pick(d, ME)}")
    # Control: without a host the old rule (newest) still holds -- the preference is what moved it.
    check("V-RHA-CONTROL-NO-HOST-NEWEST", pick(d, None) == "sibling", f"picked={pick(d, None)}")

    stranger = {"pid": 1, "proc_start": "1"}
    check("V-RHA-FALLBACK-NEWEST", pick(d, stranger) == "sibling", f"picked={pick(d, stranger)}")

    recycled = {"pid": ME["pid"], "proc_start": "different-start"}
    check("V-RHA-RECYCLED-PID-NOT-MATCHED", pick(d, recycled) == "sibling", f"picked={pick(d, recycled)}")

    legacy = state(capsule("old-a"), capsule("old-b"))
    check("V-RHA-LEGACY-CAPSULES-NEWEST", pick(legacy, ME) == "old-b", f"picked={pick(legacy, ME)}")

    # An own-host capsule that cannot be certified is not adopted over a resumable sibling.
    broken = capsule("own-broken", ME)
    broken["obligations"] = []
    d2 = state(broken, capsule("sibling2", sibling))
    check("V-RHA-UNRESUMABLE-OWN-SKIPPED", pick(d2, ME) == "sibling2", f"picked={pick(d2, ME)}")

    # host_identity reads CLAUDE_PID + the registry's procStart, and refuses anything partial.
    reg = Path(tempfile.mkdtemp(prefix="rha_reg_"))
    (reg / "8996.json").write_text(json.dumps({"pid": 8996, "procStart": ME["proc_start"]}), encoding="utf-8")
    (reg / "77.json").write_text(json.dumps({"pid": 77}), encoding="utf-8")
    (reg / "78.json").write_text(json.dumps({"pid": 5, "procStart": "x"}), encoding="utf-8")
    saved = {k: os.environ.get(k) for k in ("CLAUDE_PID", "CPP_CLAUDE_SESSIONS_DIR")}
    try:
        os.environ["CPP_CLAUDE_SESSIONS_DIR"] = str(reg)
        results = {}
        for pid in ("8996", "77", "78", "404", ""):
            os.environ["CLAUDE_PID"] = pid
            results[pid] = rollover.host_identity()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    check("V-RHA-IDENTITY-READS-REGISTRY", results["8996"] == ME, f"got={results['8996']}")
    check("V-RHA-IDENTITY-PARTIAL-IS-NONE",
          all(results[p] is None for p in ("77", "78", "404", "")), f"got={results}")

    # The seal records it.
    os.environ["CLAUDE_PID"], os.environ["CPP_CLAUDE_SESSIONS_DIR"] = "8996", str(reg)
    try:
        cap = rollover.compile_capsule("sealer", str(reg), None, goal=None, next_items=["x"])
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    check("V-RHA-SEAL-RECORDS-HOST", cap.get("host") == ME, f"host={cap.get('host')}")

    # End to end through the CLI, the way /kresume runs it.
    env = dict(os.environ, CPP_ROLLOVER_STATE_DIR=str(d), CLAUDE_PID="8996",
               CPP_CLAUDE_SESSIONS_DIR=str(reg), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(HERE / "rollover.py"), "resume", "--cwd", CWD,
                        "--claimant", "succ"], env=env, capture_output=True, text=True, timeout=120)
    first = (r.stdout.splitlines() or [""])[0]
    check("V-RHA-CLI-RESUME-CLAIMS-OWN", r.returncode == 0 and "own-pred" in first
          and (d / "capsules" / "own-pred.claim").exists()
          and not (d / "capsules" / "sibling.claim").exists(),
          f"rc={r.returncode} first={first!r} err={r.stderr[-200:]!r}")

    total = passes + fails
    print(f"RHA_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
