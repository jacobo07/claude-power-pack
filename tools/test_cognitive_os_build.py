#!/usr/bin/env python3
"""test_cognitive_os_build.py -- empirical done-gates for the Cognitive OS build.

One V-gate per implemented behavior, derived from each dataset's verifiable
contract. Hermetic: hot-session lists are injected (pure decide()) and the real
gather/prelaunch paths run against a tmp transcript tree, so the suite is
re-runnable with no dependence on the live ~/.claude/projects state.

Run: python tools/test_cognitive_os_build.py    (exit 0 == all gates PASS)

Gate naming: V-<DOMAIN>-<CASE> (PP testing doctrine, grep-able done-gate).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

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


# --------------------------------------------------------------------------
# CO-08 -- hard hot-session cap
# --------------------------------------------------------------------------
def test_co08_cap() -> None:
    from modules.cognitive_os import scheduler as S

    CWD = "C:/Users/User/.claude/skills/claude-power-pack"
    OTHER = "C:/Users/User/Apps/somethingelse"

    # V-CAP-UNDER: 1 hot session on a DIFFERENT repo, new pane here -> proceed.
    v = S.decide([{"cwd": OTHER, "sid": "a"}], CWD, is_new=True,
                 cap=2, same_repo_cap=1)
    if v.verdict == "proceed":
        _ok("V-CAP-UNDER", f"1 hot (other repo) -> {v.verdict}")
    else:
        _fail("V-CAP-UNDER", f"expected proceed, got {v.verdict} ({v.reasons})")

    # V-CAP-GLOBAL: 2 hot sessions (both other repos) -> new pane refused.
    v = S.decide([{"cwd": OTHER, "sid": "a"},
                  {"cwd": "C:/x/y", "sid": "b"}], CWD, is_new=True,
                 cap=2, same_repo_cap=1)
    if v.verdict == "refuse" and any("global cap" in r for r in v.reasons):
        _ok("V-CAP-GLOBAL", f"2 hot + new -> refuse; satisfy={len(v.satisfy)}")
    else:
        _fail("V-CAP-GLOBAL", f"expected global refuse, got {v.verdict} {v.reasons}")

    # V-CAP-SAME-REPO: 1 hot session on the SAME repo -> 2nd pane refused.
    v = S.decide([{"cwd": CWD, "sid": "live"}], CWD, is_new=True,
                 cap=2, same_repo_cap=1)
    if v.verdict == "refuse" and any("same-repo" in r for r in v.reasons):
        has_resume = any("resume" in s for s in v.satisfy)
        if has_resume:
            _ok("V-CAP-SAME-REPO", "same-repo 2nd pane -> refuse w/ resume satisfy")
        else:
            _fail("V-CAP-SAME-REPO", f"refuse but no resume satisfy: {v.satisfy}")
    else:
        _fail("V-CAP-SAME-REPO", f"expected same-repo refuse, got {v.verdict}")

    # V-CAP-RESUME: resuming (is_new=False) consumes no slot -> proceed even
    # when same-repo + over cap.
    v = S.decide([{"cwd": CWD, "sid": "live"},
                  {"cwd": OTHER, "sid": "b"}], CWD, is_new=False,
                 cap=2, same_repo_cap=1)
    if v.verdict == "proceed":
        _ok("V-CAP-RESUME", "resume over cap -> proceed (no new slot)")
    else:
        _fail("V-CAP-RESUME", f"expected proceed on resume, got {v.verdict}")

    # V-CAP-FAILOPEN: admit() with a gather that raises -> proceed (never block).
    def _boom(**kw):
        raise RuntimeError("disk on fire")
    v = S.admit(CWD, is_new=True, gather_fn=_boom)
    if v.verdict == "proceed" and v.source == "error":
        _ok("V-CAP-FAILOPEN", "gather error -> proceed (fail-open)")
    else:
        _fail("V-CAP-FAILOPEN", f"expected fail-open proceed, got {v.verdict}/{v.source}")


# --------------------------------------------------------------------------
# CO-08 -- real gather against a tmp transcript tree (hermetic I/O)
# --------------------------------------------------------------------------
def test_co08_gather(tmp: Path) -> None:
    import os
    from datetime import datetime, timezone, timedelta
    from modules.cognitive_os import scheduler as S

    now = datetime.now(timezone.utc)
    def iso(mins_ago):
        return (now - timedelta(minutes=mins_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    base = tmp / "projects"
    # fresh session: real turn 10min ago, in repo A -> HOT
    a = base / "C--repoA"
    a.mkdir(parents=True)
    (a / "fresh000.jsonl").write_text(
        json.dumps({"timestamp": iso(10), "message": {"role": "user"}}) + "\n",
        encoding="utf-8")
    # stale session: turn 5h ago + mtime 5h ago, repo B -> NOT hot
    b = base / "C--repoB"
    b.mkdir(parents=True)
    stale = b / "stale000.jsonl"
    stale.write_text(json.dumps({"timestamp": iso(300)}) + "\n", encoding="utf-8")
    old = time.time() - 5 * 3600
    os.utime(stale, (old, old))
    # subagent transcript -> excluded even if recent
    (a / "subagent-xyz.jsonl").write_text(
        json.dumps({"timestamp": iso(1)}) + "\n", encoding="utf-8")
    # SAME sid under TWO project dirs (a session spanning working dirs) -> ONE entry
    (a / "multi111.jsonl").write_text(
        json.dumps({"timestamp": iso(2)}) + "\n", encoding="utf-8")
    c = base / "C--repoC"
    c.mkdir(parents=True)
    (c / "multi111.jsonl").write_text(
        json.dumps({"timestamp": iso(3)}) + "\n", encoding="utf-8")

    hot = S.gather_hot_sessions(proj_base=base, window_min=120)
    sids = sorted(h["sid"] for h in hot)
    if sids == ["fresh000", "multi111"]:
        _ok("V-CAP-GATHER-REAL",
            f"only real-recent, non-subagent, deduped sids: {sids}")
    else:
        _fail("V-CAP-GATHER-REAL", f"expected [fresh000, multi111], got {sids}")

    multi = next((h for h in hot if h["sid"] == "multi111"), None)
    if multi and sorted(multi["encs"]) == ["C--repoA", "C--repoC"]:
        _ok("V-CAP-GATHER-DEDUP",
            f"multi-dir session = ONE entry, encs={sorted(multi['encs'])}")
    else:
        _fail("V-CAP-GATHER-DEDUP", f"dedup/encs wrong: {multi}")


# --------------------------------------------------------------------------
# Integration -- prelaunch surfaces the gate field
# --------------------------------------------------------------------------
def test_prelaunch_gate() -> None:
    from modules.wrapper import prelaunch
    out = prelaunch.run(str(_PP_ROOT))
    if isinstance(out, dict) and "gate" in out and "verdict" in out["gate"]:
        _ok("V-PRELAUNCH-GATE",
            f"run() emits gate.verdict={out['gate']['verdict']}")
    else:
        _fail("V-PRELAUNCH-GATE", f"no gate field in prelaunch output: {list(out)}")


# --------------------------------------------------------------------------
# CO-01 -- Work-Units-per-MTok economics
# --------------------------------------------------------------------------
def test_co01_economics(tmp: Path) -> None:
    from datetime import datetime, timezone, timedelta
    from modules.cognitive_os import economics as E

    # V-WU-CREDITED: a Work Unit requires a FULLY-passed gate (fail -> 0).
    if E.credited_wu(8, 8) == 8 and E.credited_wu(7, 8) == 0 and E.credited_wu(0, 0) == 0:
        _ok("V-WU-CREDITED", "8/8->8, 7/8->0 (failed gate earns nothing), 0/0->0")
    else:
        _fail("V-WU-CREDITED", f"crediting wrong: {E.credited_wu(7, 8)}")

    # V-WU-TRUECOST: denominator = output + cache-creation, excludes cache-read.
    agg = {"input_tokens": 100, "output_tokens": 500,
           "cache_creation_input_tokens": 50, "cache_read_input_tokens": 9000}
    if E.true_cost_tokens(agg) == 550:
        _ok("V-WU-TRUECOST", "true cost = output+cache_create (cache-read free)")
    else:
        _fail("V-WU-TRUECOST", f"expected 550, got {E.true_cost_tokens(agg)}")

    # V-WU-RATIO: 10 WU over 2M tokens = 5.0; zero denominator -> None.
    if E.wu_per_mtok(10, 2_000_000) == 5.0 and E.wu_per_mtok(5, 0) is None:
        _ok("V-WU-RATIO", "10 WU / 2MTok = 5.0; div-by-zero -> None (honest)")
    else:
        _fail("V-WU-RATIO", f"ratio wrong: {E.wu_per_mtok(10, 2_000_000)}")

    # V-WU-COSTVEC-HONEST: unmeasured dims are None (unknown), never zeroed.
    cv = E.cost_vector(agg)
    if cv["risk"] is None and cv["recovery"] is None and cv["token"] == 550:
        _ok("V-WU-COSTVEC-HONEST", "risk/recovery = None (not faked); token real")
    else:
        _fail("V-WU-COSTVEC-HONEST", f"cost vector dishonest: {cv}")

    # V-WU-LEDGER: record + read round-trip with window filtering.
    led = tmp / "wu_ledger.jsonl"
    now = datetime.now(timezone.utc)
    E.record_work_units("gateA", 4, 4, now=now, ledger_path=led)          # +4
    E.record_work_units("gateB", 3, 5, now=now, ledger_path=led)          # +0 (failed)
    E.record_work_units("old", 9, 9, now=now - timedelta(hours=48), ledger_path=led)  # out of window
    wu, n = E.read_work_units(since=now - timedelta(hours=24), now=now, ledger_path=led)
    if wu == 4 and n == 2:
        _ok("V-WU-LEDGER", f"in-window WU={wu} from {n} recent records (old excluded)")
    else:
        _fail("V-WU-LEDGER", f"expected (4,2), got ({wu},{n})")

    # V-WU-REPORT: join ledger to an injected token window -> ratio + confidence.
    def fake_analyze(proj_base=None, since=None):
        return {"today": {"output_tokens": 800_000,
                          "cache_creation_input_tokens": 200_000,
                          "input_tokens": 0, "cache_read_input_tokens": 0}}
    r = E.economics_report(ledger_path=led, window_hours=24, now=now,
                           analyze_fn=fake_analyze)
    # 4 WU over 1.0M true-cost tokens = 4.0 WU/MTok; 2 records < 3 -> low conf.
    if r.wu_per_mtok == 4.0 and r.confidence == "low":
        _ok("V-WU-REPORT", f"WU/MTok={r.wu_per_mtok} conf={r.confidence} (sparse-honest)")
    else:
        _fail("V-WU-REPORT", f"expected 4.0/low, got {r.wu_per_mtok}/{r.confidence}")


def main() -> int:
    import tempfile
    print("== Cognitive OS build done-gates ==")
    print("[CO-08 cap -- pure decisions]")
    test_co08_cap()
    print("[CO-08 cap -- real gather]")
    with tempfile.TemporaryDirectory() as td:
        test_co08_gather(Path(td))
    print("[CO-01 economics -- WU/MTok]")
    with tempfile.TemporaryDirectory() as td:
        test_co01_economics(Path(td))
    print("[integration -- prelaunch gate]")
    test_prelaunch_gate()
    total = _passes + _fails
    print(f"\nCOGNITIVE_OS_BUILD_PASS={_passes}/{total}  threshold={total}/{total}")
    # Live loop (CO-01): this suite IS a done-gate; record its OWN verdict into
    # the real WU ledger so the metric is fed by real certified work, not mocks.
    try:
        from modules.cognitive_os.economics import record_work_units
        record_work_units("cognitive_os_build", _passes, total)
    except Exception:  # noqa: BLE001 -- logging must never fail the gate
        pass
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
