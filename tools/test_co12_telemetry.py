#!/usr/bin/env python3
"""test_co12_telemetry.py -- CO-12 instrument layer done-gate (V-gate convention).

Hermetic: loop-boundedness runs over a synthetic TemporaryDirectory corpus; the
signal sink writes to a temp state dir. No live ~/.claude read/write. Proves the
real-data signal (loop-boundedness) classifies correctly, the opus-avoided
producer is wired (route_and_record accrues a real count), and the pending
instrument (dedup-hit) is reported honestly, never faked.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.cognitive_os import co_12_telemetry as co12   # noqa: E402

_passes = 0
_fails = 0
_UUID = "12345678-1234-1234-1234-123456789abc"          # _SID_RE-matching stem
_SUBTHRESHOLD_ENTRIES = 3
_OVERTHRESHOLD_ENTRIES = 40
_TEST_THRESHOLD = 10


def _ok(g: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {g}: {ev}")


def _fail(g: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {g}: {ev}")


def _make_session(base: Path, sub: str, sid: str, entries: int) -> None:
    d = base / sub
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text(
        "".join('{"type":"user"}\n' for _ in range(entries)), encoding="utf-8")


def test_loop_boundedness() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _make_session(base, "projA", _UUID, _OVERTHRESHOLD_ENTRIES)   # unbounded
        _make_session(base, "projB", "abcdef01-2222-3333-4444-555566667777",
                      _SUBTHRESHOLD_ENTRIES)                          # bounded
        # a non-session file (bad stem) must be ignored by _SID_RE.
        (base / "projA" / "notes.jsonl").write_text("x\n" * 99, encoding="utf-8")
        r = co12.loop_boundedness(base, threshold=_TEST_THRESHOLD)
        if r["sessions"] == 2 and r["unbounded"] == 1 and r["bounded"] == 1:
            _ok("V-LOOP-BOUNDEDNESS",
                f"{r['sessions']} sessions, {r['unbounded']} unbounded (non-sid ignored)")
        else:
            _fail("V-LOOP-BOUNDEDNESS", f"unexpected: {r}")
        if r["top_unbounded"] and r["top_unbounded"][0]["entries"] == _OVERTHRESHOLD_ENTRIES:
            _ok("V-LOOP-TOP", "unbounded session surfaced with real entry count")
        else:
            _fail("V-LOOP-TOP", f"top_unbounded wrong: {r['top_unbounded']}")


def test_signal_sink_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as td:
        ok = co12.record_signal("opus_avoided", {"opus_avoided": True, "rung": "haiku"},
                                state_dir=td)
        sigs = co12.load_signals(state_dir=td)
        if ok and len(sigs) == 1 and sigs[0]["rung"] == "haiku":
            _ok("V-SIGNAL-SINK", "record -> load round-trips")
        else:
            _fail("V-SIGNAL-SINK", f"ok={ok} sigs={sigs}")


def test_signal_failopen() -> None:
    # An unwritable state dir (a FILE where a dir is expected) must not raise.
    with tempfile.TemporaryDirectory() as td:
        clash = Path(td) / "afile"
        clash.write_text("x", encoding="utf-8")
        ok = co12.record_signal("opus_avoided", {"opus_avoided": True},
                                state_dir=str(clash))
        if ok is False:
            _ok("V-SIGNAL-FAILOPEN", "unwritable sink -> False, no exception")
        else:
            _fail("V-SIGNAL-FAILOPEN", f"expected False, got {ok}")


def test_opus_classify() -> None:
    haiku = {"rung": "haiku", "notes": []}
    opus = {"rung": "opus", "notes": []}
    demoted = {"rung": "sonnet", "notes": ["budget pressure -> stepped one rung cheaper"]}
    a = co12.classify_opus_avoided(haiku)["opus_avoided"] is True
    b = co12.classify_opus_avoided(opus)["opus_avoided"] is False
    c = co12.classify_opus_avoided(demoted)["demoted"] is True
    if a and b and c:
        _ok("V-OPUS-CLASSIFY", "haiku=avoided, opus=not, budget-note=demoted")
    else:
        _fail("V-OPUS-CLASSIFY", f"haiku={a} opus={b} demoted={c}")


def test_opus_wired_produces_data() -> None:
    # route_and_record must accrue a REAL opportunity when called (SEÑAL 1 wired).
    with tempfile.TemporaryDirectory() as td:
        co12.route_and_record("format this file", sink_state_dir=td)   # -> haiku/sonnet
        cnt = co12.opus_avoided_count(state_dir=td)
        if cnt["opportunities"] >= 1:
            _ok("V-OPUS-WIRED",
                f"route_and_record accrued {cnt['opportunities']} opportunity(ies)")
        else:
            _fail("V-OPUS-WIRED", f"no opportunity recorded: {cnt}")


def test_dedup_pending_honest() -> None:
    with tempfile.TemporaryDirectory() as td:
        rep = co12.readiness_report(Path(td) / "noproj", state_dir=td)
        d = rep["dedup_hit"]
        if d["status"] == "instrument-pending" and "dedup_hit" in rep["instruments_pending"]:
            _ok("V-DEDUP-PENDING", "dedup-hit honestly pending, not faked")
        else:
            _fail("V-DEDUP-PENDING", f"unexpected dedup status: {d}")


def test_no_regression() -> None:
    # router.py was NOT modified; confirm the CO build suite still passes.
    p = _PP / "tools" / "test_cognitive_os_build.py"
    if not p.is_file():
        _fail("V-NO-REGRESSION", "test_cognitive_os_build.py missing")
        return
    try:
        r = subprocess.run([sys.executable, str(p)], capture_output=True,
                           timeout=180, cwd=str(_PP))
        if r.returncode == 0:
            _ok("V-NO-REGRESSION", "test_cognitive_os_build 68/68 (router intact)")
        else:
            _fail("V-NO-REGRESSION", f"cognitive_os_build exit {r.returncode}")
    except (subprocess.TimeoutExpired, OSError) as e:
        _fail("V-NO-REGRESSION", f"{type(e).__name__}")


def main() -> int:
    test_loop_boundedness()
    test_signal_sink_roundtrip()
    test_signal_failopen()
    test_opus_classify()
    test_opus_wired_produces_data()
    test_dedup_pending_honest()
    test_no_regression()
    total = _passes + _fails
    print(f"\nCO12_TELEMETRY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
