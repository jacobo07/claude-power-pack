#!/usr/bin/env python3
"""test_hibernation.py -- V-gates for Transparent Process Hibernation (FASE A).

Hermetic: every test uses tmp dirs + an explicit ``now`` (no global writes, no
wall-clock dependency), so the suite is stable under rapid re-runs.

Run:  python tools/test_hibernation.py    (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import process_governor as pg  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


NOW = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _pane(**kw) -> pg.PaneProc:
    """A clean, hibernatable baseline pane; override fields per test."""
    base = dict(pid=1000, wrapper_pid=900, sid="s-abcdef12", cwd="C:/repo",
                ws_mb=250.0, idle_min=30.0, is_foreground=False, is_loop=False,
                wrapper_kind="ps1", has_anchor=True)
    base.update(kw)
    return pg.PaneProc(**base)


# --- SPRINT 1: Resource Governor decision gates ------------------------------

def test_governor_hibernates_clean_idle():
    # Arrange
    pane = _pane(idle_min=30.0, ws_mb=250.0)
    # Act
    d = pg.decide(pane)
    # Assert
    if d.verdict == pg.HIBERNATE and d.reclaim_mb == 250.0 and d.wakeable:
        _ok("V-GOVERNOR-HIBERNATES",
            f"clean idle pane -> hibernate, reclaim {d.reclaim_mb}MB")
    else:
        _fail("V-GOVERNOR-HIBERNATES", f"got {d.verdict} reclaim={d.reclaim_mb}")


def test_governor_respects_foreground():
    d = pg.decide(_pane(is_foreground=True))
    if d.verdict == pg.KEEP and any("foreground" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-ACTIVE", "foreground pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-ACTIVE", f"got {d.verdict} {d.reasons}")


def test_governor_respects_loop():
    d = pg.decide(_pane(is_loop=True))
    if d.verdict == pg.KEEP and any("/loop" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-LOOP", "loop pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-LOOP", f"got {d.verdict} {d.reasons}")


def test_governor_respects_hot():
    # A pane active 2min ago is under the 15min threshold -> hot -> keep.
    d = pg.decide(_pane(idle_min=2.0))
    if d.verdict == pg.KEEP and any("hot" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-HOT", "recently-active pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-HOT", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_unknown_idle():
    d = pg.decide(_pane(idle_min=None))
    if d.verdict == pg.KEEP and any("unknown" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-UNKNOWN", "unknown idle -> fail-safe keep")
    else:
        _fail("V-GOVERNOR-KEEPS-UNKNOWN", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_no_anchor():
    d = pg.decide(_pane(has_anchor=False))
    if d.verdict == pg.KEEP and any("anchor" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-NOANCHOR", "no anchor -> keep (would REFUSE)")
    else:
        _fail("V-GOVERNOR-KEEPS-NOANCHOR", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_raw_pane():
    d = pg.decide(_pane(wrapper_kind="none"))
    if d.verdict == pg.KEEP and any("reap deferred" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-RAW", "non-wakeable pane kept (no reap in FASE A)")
    else:
        _fail("V-GOVERNOR-KEEPS-RAW", f"got {d.verdict} {d.reasons}")


def test_plan_aggregates_reclaim():
    # Arrange: 2 hibernatable + 1 foreground kept
    panes = [_pane(pid=1, ws_mb=200.0), _pane(pid=2, ws_mb=300.0),
             _pane(pid=3, is_foreground=True, ws_mb=999.0)]
    # Act
    gp = pg.plan(panes)
    # Assert
    if (gp.hibernate_count == 2 and gp.keep_count == 1
            and gp.reclaim_mb == 500.0):
        _ok("V-GOVERNOR-PLAN-RECLAIM",
            f"2 hibernate / 1 keep, reclaim {gp.reclaim_mb}MB (foreground excluded)")
    else:
        _fail("V-GOVERNOR-PLAN-RECLAIM",
              f"hib={gp.hibernate_count} keep={gp.keep_count} rec={gp.reclaim_mb}")


def test_idle_age_reader():
    # Arrange: a synthetic transcript whose last turn is 40min before NOW
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / "sess.jsonl"
        old = (NOW - timedelta(minutes=40)).isoformat()
        recent = (NOW - timedelta(minutes=40)).isoformat()
        tp.write_text(
            json.dumps({"timestamp": old, "type": "user"}) + "\n"
            + json.dumps({"timestamp": recent, "type": "assistant"}) + "\n",
            encoding="utf-8")
        # Act
        age = pg.last_turn_age_min(tp, now=NOW)
        # Assert
        if age is not None and abs(age - 40.0) < 0.5:
            _ok("V-IDLE-AGE-READER", f"read last-turn age = {age:.1f}min")
        else:
            _fail("V-IDLE-AGE-READER", f"expected ~40, got {age}")


def test_idle_age_reader_missing():
    age = pg.last_turn_age_min("C:/nonexistent/nope.jsonl", now=NOW)
    if age is None:
        _ok("V-IDLE-AGE-MISSING", "missing transcript -> None (unknown)")
    else:
        _fail("V-IDLE-AGE-MISSING", f"expected None, got {age}")


def main() -> int:
    print("== Transparent Process Hibernation -- FASE A V-gates ==")
    print("- SPRINT 1: Resource Governor")
    for fn in (test_governor_hibernates_clean_idle,
               test_governor_respects_foreground,
               test_governor_respects_loop,
               test_governor_respects_hot,
               test_governor_keeps_unknown_idle,
               test_governor_keeps_no_anchor,
               test_governor_keeps_raw_pane,
               test_plan_aggregates_reclaim,
               test_idle_age_reader,
               test_idle_age_reader_missing):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _fail(fn.__name__, f"raised {exc!r}")
    total = _passes + _fails
    print(f"HIBERNATION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
