#!/usr/bin/env python3
"""V-CAPTURE gates -- the capture layer records what it observes.

Covers vault/specs/capture-layer-liveness.md. Run:

    python tools/test_capture_liveness.py

Hermetic by restore: the hook gates drive the REAL hook against the REAL
sinks, because a capture path mocked at its own boundary proves nothing
about the path that runs in production (Mistake #17). Every byte written
during the run is rolled back before exit, so the corpus is unchanged and
repeat runs are identical (feedback_hermetic_test_global_writes_time_window).
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from tools import capture_liveness as cl  # noqa: E402
from tools import ceps  # noqa: E402

NODE = r"C:\Program Files\nodejs\node.exe"
HOOK = PP / "hooks" / "bug-hunter-ceps-bridge.js"
EVENTS = PP / "vault" / "ceps" / "events.jsonl"
FIRES = PP / "vault" / "ceps" / "fires.jsonl"
REJECTIONS = PP / "vault" / "ceps" / "rejections.jsonl"
LESSONS = PP / "vault" / "knowledge_base" / "session_lessons.md"
UKDL = PP / "vault" / "knowledge_base" / "ukdl-universal.md"
DB = PP / "vault" / "ceps" / "patterns.db"

MUTATED = (EVENTS, FIRES, REJECTIONS, LESSONS, UKDL)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, evidence: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {evidence}")


# ---------------------------------------------------------------------------
# Snapshot / restore
# ---------------------------------------------------------------------------

def snapshot() -> dict:
    state = {"files": {}, "db_ids": set()}
    for path in MUTATED:
        state["files"][path] = (
            path.read_bytes() if path.is_file() else None)
    if DB.is_file():
        conn = sqlite3.connect(DB)
        try:
            state["db_ids"] = {
                row[0] for row in
                conn.execute("select id from ceps_patterns_fts")}
        finally:
            conn.close()
    return state


def restore(state: dict) -> None:
    for path, blob in state["files"].items():
        if blob is None:
            if path.is_file():
                path.unlink()
        else:
            path.write_bytes(blob)
    if DB.is_file() and state["db_ids"]:
        conn = sqlite3.connect(DB)
        try:
            current = {row[0] for row in
                       conn.execute("select id from ceps_patterns_fts")}
            for stale in current - state["db_ids"]:
                conn.execute(
                    "delete from ceps_patterns_fts where id = ?", (stale,))
            conn.commit()
        finally:
            conn.close()


def _lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.is_file() else 0


# ---------------------------------------------------------------------------
# V-CAPTURE-01/02/06/07 -- the real hook against the real sinks
# ---------------------------------------------------------------------------

def drive(gate: str, payload: dict, expect_category: str) -> None:
    before_events, before_fires = _lines(EVENTS), _lines(FIRES)
    proc = subprocess.run(
        [NODE, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, timeout=90)
    if proc.returncode != 0:
        _fail(gate, f"hook exit={proc.returncode} stderr={proc.stderr[:160]}")
        return
    if _lines(EVENTS) != before_events + 1:
        _fail(gate, f"events {before_events}->{_lines(EVENTS)}, expected +1; "
                    f"stderr={proc.stderr[:160]}")
        return
    if _lines(FIRES) != before_fires + 1:
        _fail(gate, f"fires {before_fires}->{_lines(FIRES)}, expected +1")
        return
    row = json.loads(EVENTS.read_text(encoding="utf-8").splitlines()[-1])
    if row["category"] != expect_category:
        _fail(gate, f"category={row['category']}, expected {expect_category}")
        return
    _ok(gate, f"{row['category']}/{row['subsystem']}")


def gates_hook() -> None:
    drive("V-CAPTURE-01", {
        "tool_name": "Bash",
        "tool_input": {"command": "python scripts/build.py --all"},
        "tool_response": {
            "stderr": "Traceback (most recent call last):\n"
                      '  File "C:\\repo\\build.py", line 42, in <module>\n'
                      "ValueError: bad config"},
    }, "tooling")

    drive("V-CAPTURE-02", {
        "tool_name": "PowerShell",
        "tool_input": {"command": "& 'C:\\Python312\\python.exe' -m pytest tests/"},
        "tool_response": {
            "output": "=== 3 failed, 12 passed ===\nAssertionError: expected 200"},
    }, "regression")

    drive("V-CAPTURE-06", {
        "tool_name": "Read",
        "tool_input": {"file_path": "C:\\repo\\big.log"},
        "tool_response": {"output": "[Tool result missing due to internal error]"},
    }, "integration")

    # Measure what the filter REJECTS, not only what it accepts.
    before = _lines(EVENTS)
    subprocess.run([NODE, str(HOOK)], input=json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "git status"},
        "tool_response": {"output": "On branch main\nnothing to commit, clean"},
    }), capture_output=True, text=True, timeout=90)
    if _lines(EVENTS) == before:
        _ok("V-CAPTURE-07", "clean output recorded nothing")
    else:
        _fail("V-CAPTURE-07", "clean output produced a false capture")


# ---------------------------------------------------------------------------
# V-CAPTURE-03 -- signature convergence
# ---------------------------------------------------------------------------

def gates_signature() -> None:
    same_mechanism = [
        ("FileNotFoundError: cannot open C:\\Users\\User\\repo\\alpha.py line 42",
         "FileNotFoundError: cannot open C:\\Users\\User\\other\\beta.py line 918"),
        ("Traceback (most recent call last) at /home/x/a/b.py, pid 3312",
         "Traceback (most recent call last) at /home/y/c/d.py, pid 7"),
        ("segfault at 0x7ffde4a1 on 2026-08-14T10:00:00Z",
         "segfault at 0x00ab12ff on 2026-01-02T23:59:59Z"),
    ]
    for first, second in same_mechanism:
        sig_a = ceps.pattern_signature(first)
        sig_b = ceps.pattern_signature(second)
        label = first.split(":")[0][:36]
        if sig_a == sig_b:
            _ok("V-CAPTURE-03", f"{label} converged to {sig_a}")
        else:
            _fail("V-CAPTURE-03", f"{label} split: {sig_a} != {sig_b}")

    if (ceps.pattern_signature("PermissionError: access denied on /etc/x")
            != ceps.pattern_signature("ImportError: no module named requests")):
        _ok("V-CAPTURE-03b", "unrelated mechanisms stay distinct")
    else:
        _fail("V-CAPTURE-03b", "over-masked: unrelated errors collapsed")


# ---------------------------------------------------------------------------
# V-CAPTURE-04 -- rejection ledger
# ---------------------------------------------------------------------------

def gates_ledger() -> None:
    before = _lines(REJECTIONS)
    result = ceps.record_error(
        category="tooling", subsystem="v-capture-04",
        root_cause="V-CAPTURE-04 ledger probe", confidence="low",
        scope="session")
    rows = REJECTIONS.read_text(encoding="utf-8").splitlines() \
        if REJECTIONS.is_file() else []
    if result is None and len(rows) == before + 1 and \
            "invalid scope=session" in json.loads(rows[-1]).get("reason", ""):
        _ok("V-CAPTURE-04", "invalid call rejected AND logged")
    else:
        _fail("V-CAPTURE-04",
              f"return={result!r} ledger {before}->{len(rows)}")


# ---------------------------------------------------------------------------
# V-CAPTURE-05 -- the gate itself, replayed against history
# ---------------------------------------------------------------------------

def _fixture_rows(path: Path, count: int) -> None:
    stamp = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    path.write_text(
        "".join(json.dumps({"ts": stamp, "n": i}) + "\n" for i in range(count)),
        encoding="utf-8")


def _scenario(gate, fires_n, records_n, wired, expect_verdict, expect_exit):
    tmp = Path(tempfile.mkdtemp())
    fires, sink, rej = tmp / "f.jsonl", tmp / "e.jsonl", tmp / "r.jsonl"
    _fixture_rows(fires, fires_n)
    _fixture_rows(sink, records_n)
    _fixture_rows(rej, 0)

    saved_producers, saved_markers = cl.PRODUCERS, cl.registered_markers
    cl.PRODUCERS = [{
        "name": "fixture", "trigger": cl.AUTOMATIC, "hook_marker": "fixture.js",
        "fires": fires, "sink": sink, "rejections": rej, "note": "fixture",
    }]
    cl.registered_markers = lambda: ({"/hooks/fixture.js"} if wired else set())
    try:
        report = cl.evaluate(window_days=7)
    finally:
        cl.PRODUCERS, cl.registered_markers = saved_producers, saved_markers

    verdict = report["producers"][0]["verdict"]
    if verdict == expect_verdict and report["exit_code"] == expect_exit:
        _ok(gate, f"{verdict} exit={report['exit_code']}")
    else:
        _fail(gate, f"{verdict} exit={report['exit_code']}, expected "
                    f"{expect_verdict}/{expect_exit}")


def gates_liveness() -> None:
    # The measured 2026-05-26..08-14 condition: 63 fires, empty corpus.
    _scenario("V-CAPTURE-05", 63, 0, True, "FIRES-WITHOUT-RECORDS", 1)
    _scenario("V-CAPTURE-05b", 63, 63, True, "OK", 0)
    # An unwired producer fires zero times forever; divergence alone passes it.
    _scenario("V-CAPTURE-05c", 0, 0, False, "UNWIRED", 1)
    _scenario("V-CAPTURE-05d", 0, 0, True, "OK", 0)


def main() -> int:
    if not Path(NODE).is_file():
        print(f"FAIL V-CAPTURE-00: node not found at {NODE}")
        return 1
    state = snapshot()
    try:
        gates_signature()
        gates_ledger()
        gates_hook()
        gates_liveness()
    finally:
        restore(state)

    total = _passes + _fails
    print(f"CAPTURE_PASS={_passes}/{total}  threshold={total}/{total}")
    if _fails == 0:
        # Restore must leave the corpus byte-identical, or the next run
        # measures this run instead of the system.
        residue = [p.name for p, blob in state["files"].items()
                   if (p.read_bytes() if p.is_file() else None) != blob]
        if residue:
            print(f"FAIL V-CAPTURE-08: restore left residue in {residue}")
            return 1
        print("PASS V-CAPTURE-08: corpus restored byte-identical")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
