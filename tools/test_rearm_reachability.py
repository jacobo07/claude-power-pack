#!/usr/bin/env python
"""V-REARM-* -- a rearm threshold nobody can reach silently bricks the session.

INCIDENT (2026-09-19, session de7f3c91). To force a deliberate crossing the wall
was narrowed to snapshot 20 / advisory 25 / **rearm 15**. valid_thresholds()
accepted it: the ordering rule (rearm < snapshot <= advisory, all 5..95) holds.

But the rearm band is where the post-compaction resume lives -- the watchdog
only looks for a compaction boundary when `used_pct < rearm_pct`. Measured over
the 180 real-session readings in ~/.claude/logs/context-watchdog.log:

    min = 15.0     p05 = 19.0     p10 = 22.0     median = 35.0
    readings strictly below 15  ->  0
    readings strictly below 30  ->  59

So `rearm: 15` is unreachable, and with tier 2 already debounced by its own
crossing the session could neither compact again nor ever resume. The contrast
is the proof rather than the story: 37cfb187 ran `rearm: 30`, 59/180 readings
fall under it, and it resumed and confirmed. Two sessions, differing precisely
on rearm reachability, with exactly the outcomes that predicts.

The knowledge already existed -- context-watchdog.py says in a COMMENT that "a
rearm below ~28 would never be reached after a compaction" -- and a comment is
not a constraint. This gate makes it one.

Note the floor is deliberately checked in the SHARED validator, so the writer
refuses loudly (ValueError) and the watchdog's reader falls back to production
constants rather than honouring a config that would brick the run.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

# No bytecode, ever. A mutation drill replaces "28" with "50" -- identical
# length -- and restores within the same mtime second, so CPython's
# (mtime, size) check passes and the gate executes a .pyc compiled from the
# MUTANT while the source on disk is correct. Measured 2026-09-19: the source
# read REARM_FLOOR_PCT = 28 and the gate reported 50, turning a clean restore
# into a phantom 6/8 regression that a git diff flatly contradicted.
sys.dont_write_bytecode = True

STATE = tempfile.mkdtemp(prefix="rearm-state-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = STATE

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

# Measurements this gate defends.
OBSERVED_POST_COMPACT_PCT = 20.0   # de7f3c91 heartbeat, 12:11:36, right after its boundary
P10_OF_REAL_READINGS = 22.0        # 180 readings, ~/.claude/logs/context-watchdog.log
BRICKED = (20.0, 25.0, 15.0)       # de7f3c91 -- accepted, and fatal
WORKED = (35.0, 40.0, 30.0)        # 37cfb187 -- accepted, and resumed
PRODUCTION = (60.0, 70.0, 45.0)    # the shipped constants

_passes = 0
_fails = 0


def _ok(gate, ev):
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, diag):
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _load(path, name):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    wd = _load(WATCHDOG, "_rearm_ctxwd")
    lr = _load(ROOT / "tools" / "gsd_long_run.py", "_rearm_lr")
    v = wd.valid_thresholds

    floor = getattr(wd, "REARM_FLOOR_PCT", None)
    if floor is None:
        _fail("V-REARM-FLOOR-EXISTS",
              "context-watchdog has no REARM_FLOOR_PCT; the reachability rule lives only in a "
              "comment, which is what let rearm=15 through")
    else:
        _ok("V-REARM-FLOOR-EXISTS", f"REARM_FLOOR_PCT={floor}")
        if floor > OBSERVED_POST_COMPACT_PCT and floor > P10_OF_REAL_READINGS:
            _ok("V-REARM-FLOOR-CLEARS-MEASUREMENT",
                f"{floor} clears the observed post-compact {OBSERVED_POST_COMPACT_PCT} "
                f"and the p10 {P10_OF_REAL_READINGS}")
        else:
            _fail("V-REARM-FLOOR-CLEARS-MEASUREMENT",
                  f"{floor} does not clear post-compact {OBSERVED_POST_COMPACT_PCT} / "
                  f"p10 {P10_OF_REAL_READINGS}; a resume could still be unreachable")

    # --- the exact config that bricked de7f3c91 -----------------------------
    if v(*BRICKED) is None:
        _ok("V-REARM-REJECTS-UNREACHABLE", f"{BRICKED} refused (rearm 15: 0 of 180 readings below it)")
    else:
        _fail("V-REARM-REJECTS-UNREACHABLE",
              f"{BRICKED} still accepted -> the session can cross once and then never "
              "compact or resume again")

    # --- negative controls: a floor that rejects everything is not a fix ----
    if v(*WORKED) is not None:
        _ok("V-REARM-ACCEPTS-KNOWN-GOOD", f"{WORKED} accepted (37cfb187 resumed on it)")
    else:
        _fail("V-REARM-ACCEPTS-KNOWN-GOOD",
              f"{WORKED} refused, but this configuration demonstrably completed a cycle")

    if v(*PRODUCTION) is not None:
        _ok("V-REARM-ACCEPTS-PRODUCTION", f"{PRODUCTION} accepted")
    else:
        _fail("V-REARM-ACCEPTS-PRODUCTION",
              f"{PRODUCTION} refused -- the shipped defaults must stay legal")

    # --- the ordering rule must survive the addition ------------------------
    if v(40.0, 35.0, 30.0) is None and v(30.0, 40.0, 35.0) is None:
        _ok("V-REARM-ORDERING-INTACT", "advisory<snapshot and rearm>=snapshot still refused")
    else:
        _fail("V-REARM-ORDERING-INTACT",
              "the floor replaced the ordering rule instead of adding to it")

    # --- the writer refuses loudly -----------------------------------------
    try:
        lr.write_thresholds("rearm-gate-probe", "20,25,15", "drill")
        _fail("V-REARM-WRITER-REFUSES", "write_thresholds accepted the bricking spec silently")
    except ValueError as exc:
        # Deliberately NOT satisfied by the echoed spec: `refused '20,25,15'`
        # already contains "15", so matching that would pass for a message that
        # explains nothing. The refusal has to name the REASON.
        if "reach" in str(exc).lower() or "floor" in str(exc).lower():
            _ok("V-REARM-WRITER-REFUSES", f"ValueError names the problem: {str(exc)[:90]}")
        else:
            _fail("V-REARM-WRITER-REFUSES",
                  f"raised, but the message does not say why: {str(exc)[:120]}")
    except Exception as exc:
        _fail("V-REARM-WRITER-REFUSES", f"wrong exception type {exc.__class__.__name__}")

    # --- and a bricking file already on disk is not honoured ----------------
    sid = "rearm-onfile-probe"
    Path(STATE).mkdir(parents=True, exist_ok=True)
    (Path(STATE) / f"ctxwd-thresholds-{sid}.json").write_text(
        json.dumps({"session_id": sid, "snapshot": 20.0, "advisory": 25.0, "rearm": 15.0}),
        encoding="utf-8")
    got = wd._thresholds(sid)
    if got == (wd.THRESHOLD_SNAPSHOT_PCT, wd.THRESHOLD_ADVISORY_PCT, wd.THRESHOLD_REARM_PCT):
        _ok("V-REARM-READER-FALLS-BACK",
            f"a bricking file on disk is ignored; reader returned production {got}")
    else:
        _fail("V-REARM-READER-FALLS-BACK",
              f"reader honoured {got} from a file that would make the resume unreachable")

    total = _passes + _fails
    print(f"\nREARM_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
