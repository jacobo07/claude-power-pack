#!/usr/bin/env python
"""V-CO12-RACE-* gates: co_12_telemetry.record_signal under concurrent writers (ACV C5 commit 1).

Measured 2026-10-03: the live CO-12 signals.jsonl held 7 unparseable fragments in 22,002 rows,
written concurrently by six producers (fios, fd, akos, cdio, sqi...). record_signal appended with
open("a") + one write -- the shape T-TORN-APPEND-CONCURRENT-JSONL-001 measured OVERWRITING rows on
Windows (append = seek-to-end + write). One fragment is one lost event and an equal-or-longer
overwrite leaves no trace, so the gate counts LOST ROWS by identity, not torn lines. The control
drives the old shape through the same harness and must lose rows: a harness that cannot see loss
would pass any writer. Template: tools/test_rollover_ledger_race.py."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WRITERS, ROWS = 6, 150
PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _pad(wid: int, i: int) -> str:
    return "x" * (600 + (wid * 37 + i * 13) % 300)       # rows of different lengths


def _writer(state: str, wid: int, start: float, shape: str) -> None:
    sys.path.insert(0, str(ROOT))
    from modules.cognitive_os import co_12_telemetry as co12
    while time.time() < start:
        pass
    for i in range(ROWS):
        if shape == "old":
            row = json.dumps({"kind": "race", "ts": "t", "w": wid, "i": i, "pad": _pad(wid, i)}) + "\n"
            with (Path(state) / "signals.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(row)
        else:
            co12.record_signal("race", {"w": wid, "i": i, "pad": _pad(wid, i)}, state_dir=state)


def _run(shape: str) -> dict:
    state = tempfile.mkdtemp(prefix=f"co12-race-{shape}-")
    start = time.time() + 1.5
    ps = [mp.Process(target=_writer, args=(state, w, start, shape)) for w in range(WRITERS)]
    for p in ps:
        p.start()
    for p in ps:
        p.join(120)
    seen, torn = set(), 0
    path = Path(state) / "signals.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        try:
            r = json.loads(line)
            seen.add((r["w"], r["i"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            torn += 1
    return {"expected": WRITERS * ROWS, "lost": WRITERS * ROWS - len(seen), "torn": torn,
            "exit": [p.exitcode for p in ps]}


def main() -> int:
    from modules.cognitive_os import co_12_telemetry as co12
    ctl = _run("old")
    ok("V-CO12-RACE-CONTROL-OLD-SHAPE-LOSES", ctl["lost"] > 0, str(ctl))      # the harness can see loss
    new = _run("record_signal")
    ok("V-CO12-RACE-NO-LOST-ROWS", new["lost"] == 0 and all(c == 0 for c in new["exit"]), str(new))
    ok("V-CO12-RACE-NO-TORN-LINES", new["torn"] == 0, str(new))

    # A row that cannot get the lock is dropped (False), never written unlocked; the bool contract
    # and never-raise are unchanged, and nothing is printed (hook callers may parse stderr).
    state = Path(tempfile.mkdtemp(prefix="co12-busy-"))
    holder = os.open(state / "signals.lock", os.O_RDWR | os.O_CREAT)
    held = co12._lock_try(holder) if hasattr(co12, "_lock_try") else False
    saved = getattr(co12, "SIGNAL_LOCK_TIMEOUT_S", None)
    co12.SIGNAL_LOCK_TIMEOUT_S = 0.2
    try:
        wrote = co12.record_signal("busy", {"x": 1}, state_dir=state)
    finally:
        if saved is not None:
            co12.SIGNAL_LOCK_TIMEOUT_S = saved
        os.close(holder)
    ok("V-CO12-LOCK-BUSY-DROPS", held and wrote is False and not (state / "signals.jsonl").exists(),
       f"held={held} wrote={wrote}")
    wrote_free = co12.record_signal("free", {"x": 2}, state_dir=state)
    rows = co12.load_signals(state_dir=state)
    ok("V-CO12-WRITES-WHEN-FREE", wrote_free is True and [r["kind"] for r in rows] == ["free"],
       f"wrote={wrote_free} rows={[r.get('kind') for r in rows]}")
    print(f"CO12_RACE_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
