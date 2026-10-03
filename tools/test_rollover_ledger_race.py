#!/usr/bin/env python
"""V-LEDGER-RACE-* gates: rollover.ledger under concurrent writers (plan ccp-s16 §16.1 W1).

Measured 2026-10-03: 6 fragments in the live rollover ledger, each the tail of a longer row that a
concurrent writer overwrote (Windows append = seek-to-end + write, not atomic). One fragment is one
lost event; an equal-or-longer overwrite leaves no trace, so the gate counts LOST ROWS by identity,
not torn lines. The control drives the old open("a") shape through the same harness and must lose
rows: a harness that cannot see loss would pass any writer."""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

WRITERS, ROWS = 6, 150
PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _pad(wid: int, i: int) -> str:
    return "x" * (600 + (wid * 37 + i * 13) % 300)       # rows of different lengths, as in the ledger


def _writer(state: str, wid: int, start: float, shape: str) -> None:
    sys.path.insert(0, str(HERE))
    import rollover
    while time.time() < start:
        pass
    for i in range(ROWS):
        if shape == "old":
            row = json.dumps({"ts": "t", "event": "race", "w": wid, "i": i, "pad": _pad(wid, i)}) + "\n"
            with open(Path(state) / "rollover-ledger.jsonl", "a", encoding="utf-8") as fh:
                fh.write(row)
        else:
            rollover.ledger("race", Path(state), w=wid, i=i, pad=_pad(wid, i))


def _run(shape: str) -> dict:
    state = tempfile.mkdtemp(prefix=f"ledger-race-{shape}-")
    start = time.time() + 1.5
    ps = [mp.Process(target=_writer, args=(state, w, start, shape)) for w in range(WRITERS)]
    for p in ps:
        p.start()
    for p in ps:
        p.join(120)
    seen, torn = set(), 0
    path = Path(state) / "rollover-ledger.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        try:
            r = json.loads(line)
            seen.add((r["w"], r["i"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            torn += 1
    return {"expected": WRITERS * ROWS, "lost": WRITERS * ROWS - len(seen), "torn": torn,
            "exit": [p.exitcode for p in ps], "state": state}


def main() -> int:
    ctl = _run("old")
    ok("V-LEDGER-RACE-CONTROL-OLD-SHAPE-LOSES", ctl["lost"] > 0, str(ctl))     # the harness can see loss
    new = _run("ledger")
    ok("V-LEDGER-RACE-NO-LOST-ROWS", new["lost"] == 0 and all(c == 0 for c in new["exit"]), str(new))
    ok("V-LEDGER-RACE-NO-TORN-LINES", new["torn"] == 0, str(new))

    # A row that cannot get the lock is dropped AND reported, never written unlocked (Owner Q4).
    import os
    import rollover
    state = Path(tempfile.mkdtemp(prefix="ledger-busy-"))
    holder = os.open(state / "rollover-ledger.lock", os.O_RDWR | os.O_CREAT)
    held = rollover._lock_try(holder)
    saved, rollover.LEDGER_LOCK_TIMEOUT_S = rollover.LEDGER_LOCK_TIMEOUT_S, 0.2
    try:
        wrote = rollover.ledger("busy", state, x=1)
    finally:
        rollover.LEDGER_LOCK_TIMEOUT_S = saved
        os.close(holder)
    fails = list((state / "ledger-failures").glob("*.json")) if (state / "ledger-failures").is_dir() else []
    ok("V-LEDGER-LOCK-BUSY-REPORTED", held and wrote is False and len(fails) == 1
       and not (state / "rollover-ledger.jsonl").exists(), f"held={held} wrote={wrote} failures={len(fails)}")
    wrote_free = rollover.ledger("free", state, x=2)
    rows = (state / "rollover-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    ok("V-LEDGER-WRITES-WHEN-FREE", wrote_free is True and len(rows) == 1 and '"event": "free"' in rows[-1],
       f"wrote={wrote_free} rows={len(rows)}")   # one row: the busy one was never written

    # The gate reads the capsule_sealed row, so a seal whose row was dropped must not say SAFE_TO_FORGET.
    import contextlib
    import io
    saved_dir, saved_ledger = rollover.STATE_DIR, rollover.ledger
    rollover.STATE_DIR = Path(tempfile.mkdtemp(prefix="ledger-seal-"))
    rollover.ledger = lambda *a, **k: False
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = rollover.main(["seal", "--session", "race-seal", "--cwd", str(rollover.STATE_DIR)])
    finally:
        rollover.STATE_DIR, rollover.ledger = saved_dir, saved_ledger
    text = buf.getvalue()
    ok("V-LEDGER-SEAL-UNRECORDED-IS-UNKNOWN", rc == 3 and "seal record was not written" in text
       and "SAFE_TO_FORGET" not in text, f"rc={rc} out={text[-160:]!r}")
    print(f"LEDGER_RACE_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
