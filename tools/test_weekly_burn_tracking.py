#!/usr/bin/env python3
"""test_weekly_burn_tracking.py -- V-gates for the Weekly-Burn dashboard (D5).

Hermetic: every gate builds a tmp ~/.claude/projects tree with synthetic
transcripts and drives the REAL functions (token_ground_truth.window_output,
cost_gate.weekly_burn, repo_coordinator.parallel_burn) against it -- real code
on hermetic data, no production mocks. Deterministic `now` so windows do not
depend on the wall clock.

Run: python tools/test_weekly_burn_tracking.py   (exit 0 == all gates pass)
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from tools.token_ground_truth import window_output, analyze  # noqa: E402
from modules.wrapper.cost_gate import (  # noqa: E402
    weekly_burn, HIST_DAILY_OUTPUT_AVG, WEEKLY_OUTPUT_LIMIT_EST)
from modules.wrapper.repo_coordinator import parallel_burn  # noqa: E402

NOW = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
_passes = 0
_fails = 0


def _ok(gate, ev):
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {ev}")


def _fail(gate, diag):
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diag}")


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _tree(cwd, turns):
    """turns: list of (sid, minutes_ago, output_tokens, user_text|None).
    Writes synthetic transcripts under a fresh tmp proj_base; returns its path."""
    base = Path(tempfile.mkdtemp())
    enc = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    d = base / enc
    d.mkdir(parents=True)
    rows_by_sid: dict[str, list] = {}
    for sid, mago, out, utext in turns:
        ts = _iso(NOW - timedelta(minutes=mago))
        rows = rows_by_sid.setdefault(sid, [])
        if utext is not None:
            rows.append({"timestamp": ts,
                         "message": {"role": "user", "content": utext}})
        rows.append({"timestamp": ts, "message": {
            "role": "assistant", "model": "claude-opus-4-8",
            "usage": {"input_tokens": 10, "output_tokens": out,
                      "cache_read_input_tokens": 100,
                      "cache_creation_input_tokens": 0}}})
    for sid, rows in rows_by_sid.items():
        (d / f"{sid}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return base


CWD = r"C:\fake\repo\TUA-X"


def gate_weekly_burn_real():
    # one turn 60min ago, 25M output -> window_output(24h) must sum it (real read)
    base = _tree(CWD, [("s1", 60, 25_000_000, None)])
    got = window_output(24, proj_base=base, now=NOW)
    if got == 25_000_000:
        _ok("V-WEEKLY-BURN-REAL", f"window_output read {got:,} from disk")
    else:
        _fail("V-WEEKLY-BURN-REAL", f"expected 25,000,000 got {got}")
    # a turn 8 days old must NOT count in the 24h window
    base2 = _tree(CWD, [("s1", 60, 5_000_000, None),
                        ("s2", 60 * 24 * 8, 9_000_000, None)])
    got2 = window_output(24, proj_base=base2, now=NOW)
    if got2 == 5_000_000:
        _ok("V-WEEKLY-BURN-REAL-WINDOW", f"24h window excluded 8d-old turn ({got2:,})")
    else:
        _fail("V-WEEKLY-BURN-REAL-WINDOW", f"expected 5,000,000 got {got2}")


def gate_projection_accurate():
    base = _tree(CWD, [("s1", 60, 25_000_000, None)])
    wb = weekly_burn(proj_base=base, now=NOW)
    expect = WEEKLY_OUTPUT_LIMIT_EST / 25_000_000
    if wb.days_left is not None and abs(wb.days_left - expect) < 0.01:
        _ok("V-PROJECTION-ACCURATE",
            f"days_left={wb.days_left:.2f} == limit/burn24 ({expect:.2f})")
    else:
        _fail("V-PROJECTION-ACCURATE",
              f"days_left={wb.days_left} expected {expect:.2f}")


def gate_advisory_fires_high():
    base = _tree(CWD, [("s1", 60, 25_000_000, None)])  # 25M > 1.5*13.5M=20.25M
    wb = weekly_burn(proj_base=base, now=NOW)
    if wb.elevated and wb.line and "elevado" in wb.line:
        _ok("V-ADVISORY-FIRES-HIGH-BURN",
            f"factor={wb.rate_factor:.2f} fired")
    else:
        _fail("V-ADVISORY-FIRES-HIGH-BURN",
              f"elevated={wb.elevated} line={wb.line!r}")


def gate_advisory_silent_normal():
    base = _tree(CWD, [("s1", 60, 9_000_000, None)])  # 9M < 20.25M
    wb = weekly_burn(proj_base=base, now=NOW)
    if not wb.elevated and wb.line is None:
        _ok("V-ADVISORY-SILENT-NORMAL",
            f"factor={wb.rate_factor:.2f} silent")
    else:
        _fail("V-ADVISORY-SILENT-NORMAL",
              f"elevated={wb.elevated} line={wb.line!r}")


def gate_parallel_fires():
    big = "EXECUTION MODE " + "X" * 9000
    base = _tree(CWD, [("p1", 10, 5000, big), ("p2", 12, 5000, big)])
    pb = parallel_burn(CWD, proj_base=base, now=NOW)
    if pb.burning and pb.panes == 2 and pb.warning:
        _ok("V-PARALLEL-DETECTOR-FIRES", f"{pb.panes} panes, warning set")
    else:
        _fail("V-PARALLEL-DETECTOR-FIRES",
              f"burning={pb.burning} panes={pb.panes}")


def gate_parallel_silent():
    big = "EXECUTION MODE " + "X" * 9000
    base = _tree(CWD, [("p1", 10, 5000, big)])  # only 1 pane
    pb = parallel_burn(CWD, proj_base=base, now=NOW)
    if not pb.burning and pb.warning is None:
        _ok("V-PARALLEL-DETECTOR-SILENT", f"1 pane -> quiet ({pb.source})")
    else:
        _fail("V-PARALLEL-DETECTOR-SILENT",
              f"burning={pb.burning} warning={pb.warning!r}")


def gate_ukdl_rules_present():
    f = _PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
    try:
        text = f.read_text(encoding="utf-8")
    except OSError as e:
        _fail("V-UKDL-RULES-PRESENT", f"unreadable: {e}")
        return
    a = "PR-MODE-SELECTION-001" in text
    b = "T-PARALLEL-PANES-BURN-001" in text
    if a and b:
        _ok("V-UKDL-RULES-PRESENT", "both rule IDs sealed in vault")
    else:
        _fail("V-UKDL-RULES-PRESENT", f"PR={a} T={b}")


def gate_fail_open():
    # nonexistent proj_base must yield silence, never raise
    bad = Path(tempfile.gettempdir()) / "definitely_not_a_proj_base_xyz123"
    try:
        wb = weekly_burn(proj_base=bad, now=NOW)
        pb = parallel_burn(CWD, proj_base=bad, now=NOW)
    except Exception as e:  # noqa: BLE001
        _fail("V-FAIL-OPEN", f"raised {type(e).__name__}: {e}")
        return
    if wb.line is None and not pb.burning:
        _ok("V-FAIL-OPEN", "missing data -> silent, no raise")
    else:
        _fail("V-FAIL-OPEN", f"wb.line={wb.line!r} pb.burning={pb.burning}")


def gate_baseline_intact():
    # the canonical analyze() must still work after the window_output addition
    base = _tree(CWD, [("s1", 60, 1_000_000, None)])
    try:
        data = analyze(proj_base=base, now=NOW.replace(tzinfo=None))
    except Exception as e:  # noqa: BLE001
        _fail("V-BASELINE-INTACT", f"analyze raised {e}")
        return
    if isinstance(data, dict) and "lifetime" in data and "sessions" in data:
        _ok("V-BASELINE-INTACT", "token_ground_truth.analyze intact")
    else:
        _fail("V-BASELINE-INTACT", f"unexpected shape: {list(data)[:5]}")


def main():
    print("== test_weekly_burn_tracking ==")
    gate_weekly_burn_real()
    gate_projection_accurate()
    gate_advisory_fires_high()
    gate_advisory_silent_normal()
    gate_parallel_fires()
    gate_parallel_silent()
    gate_ukdl_rules_present()
    gate_fail_open()
    gate_baseline_intact()
    total = _passes + _fails
    print(f"WEEKLY_BURN_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
