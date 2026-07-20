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
try:  # pytest is optional -- this file also runs standalone via main().
    import pytest

    @pytest.fixture
    def tmp(tmp_path: Path) -> Path:
        """Supply the empty temp dir that main() passes positionally.

        Without this the gates below are collected by pytest (they match
        test_*) but error at setup on a missing fixture, so they had never
        actually run under pytest.
        """
        return tmp_path

except ImportError:  # pragma: no cover - standalone execution path
    pass


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


# --------------------------------------------------------------------------
# CO-09 -- loop & subagent budget
# --------------------------------------------------------------------------
def test_co09_loop_budget() -> None:
    from types import SimpleNamespace
    from modules.cognitive_os import loop_budget as L

    # V-LOOP-UNCAPPED: an uncapped loop is refused outright (the #1 rule).
    v = L.admit_loop(L.LoopBudget(max_iterations=None))
    if v.verdict == "refuse" and any("uncapped" in r for r in v.reasons):
        _ok("V-LOOP-UNCAPPED", "no max_iterations -> refuse")
    else:
        _fail("V-LOOP-UNCAPPED", f"expected refuse, got {v.verdict}")

    # V-LOOP-CEILING: projected context breaches 60% before the cap -> refuse.
    b = L.LoopBudget(max_iterations=10, start_context_pct=50, per_iter_context_pct=5,
                     checkpoint=True, resume_plan=True, stop_gates=["x"])
    v = L.admit_loop(b)
    if (v.verdict == "refuse" and v.projected_context_pct == 100
            and any("max_iterations" in s for s in v.satisfy)):
        _ok("V-LOOP-CEILING",
            f"proj {v.projected_context_pct:.0f}% -> refuse w/ lower-cap satisfy")
    else:
        _fail("V-LOOP-CEILING", f"got {v.verdict}/{v.projected_context_pct}")

    # V-LOOP-ADMIT: a complete, bounded, under-ceiling loop -> proceed.
    b = L.LoopBudget(max_iterations=5, start_context_pct=40, per_iter_context_pct=2,
                     checkpoint=True, resume_plan=True, stop_gates=["converged"])
    v = L.admit_loop(b)
    if v.verdict == "proceed":
        _ok("V-LOOP-ADMIT",
            f"bounded under-ceiling loop ({v.projected_context_pct:.0f}%) -> proceed")
    else:
        _fail("V-LOOP-ADMIT", f"expected proceed, got {v.verdict} {v.reasons}")

    # V-LOOP-KILL-COST: cost > 2x budget -> kill (HR-COST-002).
    st = L.LoopState(cost_so_far_tokens=250, current_context_pct=10,
                     per_iter_context_pct=1)
    k = L.kill_check(st, L.LoopBudget(max_iterations=10, budget_tokens=100))
    if k.kill and any("HR-COST-002" in r for r in k.reasons):
        _ok("V-LOOP-KILL-COST", "cost 250 > 2x100 -> kill")
    else:
        _fail("V-LOOP-KILL-COST", f"expected kill, got {k.kill}")

    # V-LOOP-KILL-FAILS: 2 consecutive failures -> kill (Rule 12).
    st = L.LoopState(consecutive_failures=2, current_context_pct=10,
                     per_iter_context_pct=1)
    k = L.kill_check(st, L.LoopBudget(max_iterations=10, budget_tokens=10_000))
    if k.kill and any("consecutive" in r for r in k.reasons):
        _ok("V-LOOP-KILL-FAILS", "2 consecutive failures -> kill")
    else:
        _fail("V-LOOP-KILL-FAILS", f"expected kill, got {k.kill}/{k.reasons}")

    # V-LOOP-KILL-CONTINUE: under all limits -> no kill.
    st = L.LoopState(cost_so_far_tokens=50, current_context_pct=20,
                     per_iter_context_pct=2, consecutive_failures=0)
    k = L.kill_check(st, L.LoopBudget(max_iterations=10, budget_tokens=10_000))
    if not k.kill:
        _ok("V-LOOP-KILL-CONTINUE", "under all limits -> continue")
    else:
        _fail("V-LOOP-KILL-CONTINUE", f"expected continue, got kill {k.reasons}")

    # V-SUBAGENT-ROUTE: real NANO task -> Haiku; Opus-on-NANO refused+corrected.
    v = L.admit_subagent("fix the import formatting", budget_remaining_tokens=100000)
    haiku_ok = "haiku" in v.model.lower()
    fake = lambda d: SimpleNamespace(  # noqa: E731
        model="claude-opus-4-8", route_class=SimpleNamespace(value="nano"))
    v2 = L.admit_subagent("trivial rename", budget_remaining_tokens=100000,
                          route_fn=fake)
    if haiku_ok and v2.verdict == "refuse" and "haiku" in v2.model.lower():
        _ok("V-SUBAGENT-ROUTE",
            "NANO->Haiku; Opus-on-NANO refused+corrected (HR-COST-001)")
    else:
        _fail("V-SUBAGENT-ROUTE", f"got {v.model} / {v2.verdict}:{v2.model}")

    # V-SUBAGENT-ATTRIBUTE: subagent cost adds to the parent (blind-spot fix).
    if L.attribute_subagent_cost(1000, 500) == 1500:
        _ok("V-SUBAGENT-ATTRIBUTE", "subagent 500 attributed to parent 1000 -> 1500")
    else:
        _fail("V-SUBAGENT-ATTRIBUTE", "attribution wrong")


# --------------------------------------------------------------------------
# CO-00 -- effective-context estimate + 60% ceiling bands
# --------------------------------------------------------------------------
def test_co00_context() -> None:
    from modules.cognitive_os import context as C

    # V-CTX-BAND: the four bands + honest unknown.
    if (C.band_of(30) == C.GREEN and C.band_of(50) == C.AMBER
            and C.band_of(58) == C.RED and C.band_of(72) == C.BREACH
            and C.band_of(None) == C.UNKNOWN):
        _ok("V-CTX-BAND", "30 GREEN / 50 AMBER / 58 RED / 72 BREACH / None UNKNOWN")
    else:
        _fail("V-CTX-BAND", "band edges wrong")

    now = 1_000_000.0
    # V-CTX-FRESH-BRIDGE: a fresh statusline bridge is the high-confidence primary.
    est = C.effective_context(
        "s1", "C:/r", now=now,
        bridge_fn=lambda sid, td: {"used_pct": 58, "timestamp": now - 10})
    if (est.pct == 58 and est.band == C.RED and est.source == "statusline"
            and est.confidence == "high"):
        _ok("V-CTX-FRESH-BRIDGE", "fresh bridge 58% -> RED (statusline/high)")
    else:
        _fail("V-CTX-FRESH-BRIDGE", f"got {est}")

    # V-CTX-STALE-FALLBACK: a stale bridge is NOT trusted -> jsonl, flagged stale.
    est = C.effective_context(
        "s1", "C:/r", now=now,
        bridge_fn=lambda sid, td: {"used_pct": 58, "timestamp": now - 5000},
        jsonl_fn=lambda sid, cwd, pb: 20.0)
    if (est.source == "jsonl" and est.band == C.AMBER and est.stale
            and est.confidence == "low" and est.pct is None):
        _ok("V-CTX-STALE-FALLBACK",
            "stale bridge -> jsonl 20MB AMBER, stale flagged, pct unknown")
    else:
        _fail("V-CTX-STALE-FALLBACK", f"got {est}")

    # V-CTX-UNKNOWN-HONEST: no signal -> UNKNOWN, never a fabricated GREEN.
    est = C.effective_context("s1", "C:/r", now=now,
                              bridge_fn=lambda sid, td: None,
                              jsonl_fn=lambda sid, cwd, pb: None)
    if est.band == C.UNKNOWN:
        _ok("V-CTX-UNKNOWN-HONEST", "no signal -> UNKNOWN (not GREEN)")
    else:
        _fail("V-CTX-UNKNOWN-HONEST", f"expected UNKNOWN, got {est.band}")

    # V-CTX-FAILOPEN: an exploding sensor -> UNKNOWN (fail-open, never fabricate).
    def _boom(*a, **k):
        raise RuntimeError("sensor down")
    est = C.effective_context("s1", "C:/r", now=now, bridge_fn=_boom)
    if est.band == C.UNKNOWN:
        _ok("V-CTX-FAILOPEN", "sensor error -> UNKNOWN")
    else:
        _fail("V-CTX-FAILOPEN", f"expected UNKNOWN, got {est.band}")

    # V-CTX-RESUME-ADVISE: RED/BREACH resume target -> advisory; GREEN -> none.
    red = lambda s, c, **k: C.ContextEstimate(58, C.RED, "statusline", "high")  # noqa: E731
    grn = lambda s, c, **k: C.ContextEstimate(20, C.GREEN, "statusline", "high")  # noqa: E731
    a = C.resume_advisory("s1", "C:/r", estimate_fn=red)
    a2 = C.resume_advisory("s1", "C:/r", estimate_fn=grn)
    if a.advise and a.message and "ceiling" in a.message.lower() and not a2.advise:
        _ok("V-CTX-RESUME-ADVISE", "RED resume -> advise; GREEN -> silent")
    else:
        _fail("V-CTX-RESUME-ADVISE", f"got advise={a.advise}/{a2.advise}")

    # V-PRELAUNCH-RESUME-GATE: prelaunch surfaces the resume_gate field.
    from modules.wrapper import prelaunch
    out = prelaunch.run(str(_PP_ROOT))
    if "resume_gate" in out and "band" in out["resume_gate"]:
        _ok("V-PRELAUNCH-RESUME-GATE",
            f"prelaunch emits resume_gate.band={out['resume_gate']['band']}")
    else:
        _fail("V-PRELAUNCH-RESUME-GATE", f"no resume_gate: {list(out)}")


# --------------------------------------------------------------------------
# CO-03 -- Dynamic Cognitive Router (cheapest-first cascade)
# --------------------------------------------------------------------------
def test_co03_router() -> None:
    from modules.cognitive_os import router as R

    # V-ROUTE-VAULT: a Vault hit short-circuits even an Opus-class task (zero tok).
    d = R.route("re-architect the whole platform", vault_fn=lambda t: "stored ADR-12")
    if d.rung == "vault" and d.model is None and d.cost == "zero":
        _ok("V-ROUTE-VAULT", "vault hit -> zero-token (even for an XL task)")
    else:
        _fail("V-ROUTE-VAULT", f"got {d.rung}/{d.model}")

    # V-ROUTE-ASSET: a reusable asset resolves before any model.
    d = R.route("apply the standard handler pattern", asset_fn=lambda t: "template T7")
    if d.rung == "asset" and d.model is None:
        _ok("V-ROUTE-ASSET", "asset applies -> zero-token")
    else:
        _fail("V-ROUTE-ASSET", f"got {d.rung}")

    # V-ROUTE-DETERMINISTIC: a recovery op routes to no model (real default).
    d = R.route("/compact the session now")
    if d.rung == "deterministic" and d.model is None:
        _ok("V-ROUTE-DETERMINISTIC", "/compact -> deterministic, no model")
    else:
        _fail("V-ROUTE-DETERMINISTIC", f"got {d.rung}")

    # V-ROUTE-HAIKU: a trivial NANO task -> Haiku, not Opus.
    d = R.route("fix a typo in the comment")
    if d.rung == "haiku":
        _ok("V-ROUTE-HAIKU", f"trivial task -> {d.model}")
    else:
        _fail("V-ROUTE-HAIKU", f"expected haiku, got {d.rung} ({d.reason})")

    # V-ROUTE-OPUS: an architectural task -> Opus (last resort, justified).
    d = R.route("re-architect the system from the ground up")
    if d.rung == "opus":
        _ok("V-ROUTE-OPUS", f"architectural -> {d.model}")
    else:
        _fail("V-ROUTE-OPUS", f"expected opus, got {d.rung} ({d.reason})")

    # V-ROUTE-FLOOR: task-shape floor beats a cheap keyword (no under-serving).
    # 'format' is NANO, but 'authentication/system' makes it tier-2 -> Sonnet wins.
    d = R.route("format the authentication system end to end")
    if d.rung == "sonnet" and d.tier >= 2:
        _ok("V-ROUTE-FLOOR",
            f"tier {d.tier} floor beats NANO keyword -> {d.rung} (not haiku)")
    else:
        _fail("V-ROUTE-FLOOR", f"floor not respected: {d.rung}/tier{d.tier}")

    # V-ROUTE-OPUS-NOT-DEFAULT: an unspecified task -> Sonnet, never Opus.
    d = R.route("do some work on the thing")
    if d.rung != "opus":
        _ok("V-ROUTE-OPUS-NOT-DEFAULT", f"unspecified -> {d.rung} (Opus not default)")
    else:
        _fail("V-ROUTE-OPUS-NOT-DEFAULT", "Opus chosen by default")

    # V-ROUTE-BUDGET-PRESSURE: a MACRO keyword inflates a tier-1 task to Opus;
    # under budget pressure it steps one rung cheaper (Sonnet), never below floor.
    inflated = R.route("audit this small helper")
    relieved = R.route("audit this small helper", budget_pressure=True)
    if inflated.rung == "opus" and relieved.rung == "sonnet":
        _ok("V-ROUTE-BUDGET-PRESSURE",
            "MACRO->opus; under pressure -> sonnet (one cheaper, above floor)")
    else:
        _fail("V-ROUTE-BUDGET-PRESSURE", f"got {inflated.rung}->{relieved.rung}")

    # V-ROUTE-ESCALATE: the upward path haiku->sonnet->opus, capped at opus.
    if (R.escalate(R.HAIKU) == R.SONNET and R.escalate(R.SONNET) == R.OPUS
            and R.escalate(R.OPUS) == R.OPUS):
        _ok("V-ROUTE-ESCALATE", "haiku->sonnet->opus, capped at opus")
    else:
        _fail("V-ROUTE-ESCALATE", "escalation ladder wrong")


# --------------------------------------------------------------------------
# CO-05 -- Zero Token Layer & asset registry
# --------------------------------------------------------------------------
def test_co05_registry(tmp: Path) -> None:
    from modules.cognitive_os import registry as G

    reg = tmp / "asset_registry.jsonl"
    src = tmp / "source.txt"
    src.write_text("original", encoding="utf-8")
    anchor = {"type": "file", "path": str(src), "hash": G.file_hash(src)}

    # V-ASSET-VERIFY-GATE: store only the VERIFIED and recurrence>=3.
    s_unver = G.store_asset("a1", "knowledge", "x", verified=False,
                            recurrence=5, registry_path=reg)
    s_low = G.store_asset("a2", "knowledge", "x", verified=True,
                          recurrence=2, registry_path=reg)
    s_ok = G.store_asset(
        "git-path-pivot", "knowledge",
        "use C:/Program Files/Git/cmd/git.exe",
        applicability=["git path", "powershell git"], anchor=anchor,
        verified=True, recurrence=3, registry_path=reg)
    if (not s_unver) and (not s_low) and s_ok:
        _ok("V-ASSET-VERIFY-GATE",
            "unverified + sub-threshold rejected; verified 3+ stored")
    else:
        _fail("V-ASSET-VERIFY-GATE", f"got {s_unver}/{s_low}/{s_ok}")

    # V-ASSET-LOOKUP-ZERO: a fresh matching asset resolves at zero new tokens.
    hit = G.vault_resolver("how to fix the powershell git path", registry_path=reg)
    miss = G.vault_resolver("something totally unrelated", registry_path=reg)
    if hit and "git.exe" in hit and miss is None:
        _ok("V-ASSET-LOOKUP-ZERO", "fresh match -> content; non-match -> miss")
    else:
        _fail("V-ASSET-LOOKUP-ZERO", f"hit={hit!r} miss={miss!r}")

    # V-ASSET-STALE-NOT-SERVED: change the source -> anchor mismatch -> not served.
    src.write_text("CHANGED", encoding="utf-8")
    stale = G.vault_resolver("how to fix the powershell git path", registry_path=reg)
    if stale is None:
        _ok("V-ASSET-STALE-NOT-SERVED",
            "source changed -> stale asset not served blind")
    else:
        _fail("V-ASSET-STALE-NOT-SERVED", f"served stale: {stale!r}")

    # V-ASSET-ROUTER-DEFAULT: route() defaults to the registry; an empty/irrelevant
    # registry simply misses and the cascade still routes to a model.
    from modules.cognitive_os import router as R
    d = R.route("fix a typo")
    if d.rung == "haiku":
        _ok("V-ASSET-ROUTER-DEFAULT", "empty registry -> miss -> model (haiku)")
    else:
        _fail("V-ASSET-ROUTER-DEFAULT", f"unexpected rung {d.rung}")


# --------------------------------------------------------------------------
# CO-02 -- Economics Governor & violation registry
# --------------------------------------------------------------------------
def test_co02_governor(tmp: Path) -> None:
    from datetime import datetime, timezone, timedelta
    from modules.cognitive_os import governor as G

    LIMIT = 100
    # V-GOV-BANDS: 50% GREEN / 75% AMBER / 95% RED.
    if (G.band_of(50, LIMIT) == G.GREEN and G.band_of(75, LIMIT) == G.AMBER
            and G.band_of(95, LIMIT) == G.RED):
        _ok("V-GOV-BANDS", "50% GREEN / 75% AMBER / 95% RED")
    else:
        _fail("V-GOV-BANDS", "band edges wrong")

    # V-GOV-ADMIT-GREEN: small op, low spend -> ADMIT.
    v = G.admit(10, week_spent=20, week_limit=LIMIT)
    if v.verdict == G.ADMIT and v.band == G.GREEN:
        _ok("V-GOV-ADMIT-GREEN", "GREEN + fits -> ADMIT")
    else:
        _fail("V-GOV-ADMIT-GREEN", f"got {v.verdict}/{v.band}")

    # V-GOV-DOWNGRADE: AMBER band -> prefer ADMIT-DOWNGRADED over refuse.
    v = G.admit(5, week_spent=75, week_limit=LIMIT, can_downgrade=True)
    if v.verdict == G.DOWNGRADED:
        _ok("V-GOV-DOWNGRADE", f"AMBER -> {v.verdict} (cheaper form admitted)")
    else:
        _fail("V-GOV-DOWNGRADE", f"got {v.verdict}")

    # V-GOV-REFUSE-MINVIABLE: even minimum-viable breaches -> REFUSE, no bypass.
    v = G.admit(50, week_spent=95, week_limit=LIMIT, min_viable=20)
    if v.verdict == G.REFUSE and any("bypass" in s.lower() for s in v.satisfy):
        _ok("V-GOV-REFUSE-MINVIABLE", "min-viable breaches -> REFUSE (no bypass)")
    else:
        _fail("V-GOV-REFUSE-MINVIABLE", f"got {v.verdict} {v.satisfy}")

    # V-GOV-REFUSE-NODOWNGRADE: full op breaches + cannot downgrade -> REFUSE.
    v = G.admit(50, week_spent=80, week_limit=LIMIT, can_downgrade=False)
    if v.verdict == G.REFUSE:
        _ok("V-GOV-REFUSE-NODOWNGRADE", "breach + no downgrade -> REFUSE")
    else:
        _fail("V-GOV-REFUSE-NODOWNGRADE", f"got {v.verdict}")

    # V-GOV-VIOLATION-REGISTRY: durable breach record + window filter + un_gated.
    vp = tmp / "violations.jsonl"
    now = datetime.now(timezone.utc)
    G.record_violation("week", op_class="ultra", model="opus", projected=100,
                       actual=180, wu=2, disposition="downgrade-ignored",
                       un_gated=True, now=now, registry_path=vp)
    G.record_violation("session", projected=10, actual=12,
                       now=now - timedelta(hours=48), registry_path=vp)
    recent = G.read_violations(since=now - timedelta(hours=24), registry_path=vp)
    if (len(recent) == 1 and recent[0]["un_gated"] is True
            and recent[0]["tier"] == "week"):
        _ok("V-GOV-VIOLATION-REGISTRY",
            "breach recorded; window filter + un_gated flag preserved")
    else:
        _fail("V-GOV-VIOLATION-REGISTRY", f"got {recent}")


# --------------------------------------------------------------------------
# CO-04 -- Context Virtual Memory (tiers)
# --------------------------------------------------------------------------
def test_co04_memory() -> None:
    from modules.cognitive_os import memory as M

    # V-MEM-TIER-OF: kinds map to the right tier; unknown -> EXTERNAL.
    if (M.tier_of("skill-full") == M.HOT and M.tier_of("vault-asset") == M.WARM
            and M.tier_of("transcript") == M.COLD and M.tier_of("web") == M.EXTERNAL
            and M.tier_of("???") == M.EXTERNAL):
        _ok("V-MEM-TIER-OF", "skill-full HOT / vault WARM / transcript COLD / web EXTERNAL")
    else:
        _fail("V-MEM-TIER-OF", "tier map wrong")

    # V-MEM-EXTERNAL-UNTRUSTED: EXTERNAL tier is untrusted until validated.
    ext = M.MemoryItem("e1", "web")
    if M.is_external_untrusted(ext) and M.TIER_TRUST[M.EXTERNAL] == "untrusted":
        _ok("V-MEM-EXTERNAL-UNTRUSTED", "EXTERNAL untrusted until validated")
    else:
        _fail("V-MEM-EXTERNAL-UNTRUSTED", "external trust wrong")

    # V-MEM-PAGE-IN-MIN: minimum depth (discovery default; never full unasked).
    if M.page_in_depth(None) == "discovery" and M.page_in_depth("summary") == "summary":
        _ok("V-MEM-PAGE-IN-MIN", "page-in defaults to the cheapest depth")
    else:
        _fail("V-MEM-PAGE-IN-MIN", "page-in depth wrong")

    # V-MEM-DEMOTE-LOSSLESS: HOT->WARM pointer; original content not destroyed.
    hot = M.MemoryItem("x", "skill-full")
    d = M.demote(hot)
    if d.tier == M.WARM and d.depth == "summary" and hot.tier == M.HOT:
        _ok("V-MEM-DEMOTE-LOSSLESS", "demote HOT->WARM pointer (lossless)")
    else:
        _fail("V-MEM-DEMOTE-LOSSLESS", f"got {d.tier}/{d.depth}, orig {hot.tier}")

    # V-MEM-COST-ORDER + working set: HOT costs most; cheaper tier preferred.
    ws = M.working_set([M.MemoryItem("a", "skill-full", in_working_set=True),
                        M.MemoryItem("b", "vault-asset")])
    if (M.cheaper_tier_preferred(M.HOT, M.WARM) == M.WARM
            and len(ws) == 1 and ws[0].id == "a"):
        _ok("V-MEM-COST-ORDER", "WARM cheaper than HOT; working_set filters")
    else:
        _fail("V-MEM-COST-ORDER", "cost order / working set wrong")


# --------------------------------------------------------------------------
# CO-06 -- Cognitive Garbage Collector (policy)
# --------------------------------------------------------------------------
def test_co06_gc() -> None:
    from datetime import datetime, timezone, timedelta
    from modules.cognitive_os import gc as GC

    CT = 10
    stale = GC.GCItem("stale", last_ref_turn=0, hot_since_turn=0, depth="full")
    fresh = GC.GCItem("fresh", last_ref_turn=CT, hot_since_turn=CT, depth="discovery")
    pinned = GC.GCItem("pin", last_ref_turn=0, hot_since_turn=0, in_working_set=True)
    hardrule = GC.GCItem("hr", kind="hard-rule", last_ref_turn=0, hot_since_turn=0)
    items = [stale, fresh, pinned, hardrule]

    # V-GC-PIN-WORKING-SET: pinned + hard-rule items are never candidates.
    amber = GC.eviction_candidates(items, current_turn=CT, band="AMBER")
    amber_ids = {i.id for i in amber}
    if "pin" not in amber_ids and "hr" not in amber_ids and "stale" in amber_ids:
        _ok("V-GC-PIN-WORKING-SET", "working-set + hard-rule pinned; stale evicted")
    else:
        _fail("V-GC-PIN-WORKING-SET", f"amber={amber_ids}")

    # V-GC-GRADUATED: RED evicts more than AMBER (a fresh off-WS item joins).
    red = GC.eviction_candidates(items, current_turn=CT, band="RED")
    if len(red) > len(amber) and "fresh" in {i.id for i in red}:
        _ok("V-GC-GRADUATED", f"AMBER {len(amber)} < RED {len(red)} candidates")
    else:
        _fail("V-GC-GRADUATED", f"amber={len(amber)} red={len(red)}")

    # V-GC-NEVER-TRANSCRIPT: a .jsonl is categorically excluded from pruning,
    # even when 0-retrieval and very old (Session Safety Contract).
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=400)).isoformat()
    assets = [
        {"key": "t", "path": "x/sess.jsonl", "retrievals": 0, "stored_ts": old},
        {"key": "dead", "path": "x/note.md", "retrievals": 0, "stored_ts": old},
        {"key": "used", "path": "x/u.md", "retrievals": 5, "stored_ts": old},
        {"key": "hr", "kind": "hard-rule", "retrievals": 0, "stored_ts": old},
    ]
    pruned = {a["key"] for a in GC.prune_candidates(assets, now=now, retention_days=30)}
    if "t" not in pruned and "used" not in pruned and "hr" not in pruned and "dead" in pruned:
        _ok("V-GC-NEVER-TRANSCRIPT",
            "transcript + used + hard-rule kept; only dead derived asset pruned")
    else:
        _fail("V-GC-NEVER-TRANSCRIPT", f"pruned={pruned}")

    if GC.is_transcript("a/b.jsonl") and not GC.is_transcript("a/b.md"):
        _ok("V-GC-TRANSCRIPT-GUARD", ".jsonl detected, .md not")
    else:
        _fail("V-GC-TRANSCRIPT-GUARD", "transcript guard wrong")


# --------------------------------------------------------------------------
# CO-07 -- Session Hibernation (store-then-destroy)
# --------------------------------------------------------------------------
def test_co07_hibernation(tmp: Path) -> None:
    import json as _json
    from modules.cognitive_os import hibernation as H

    reg = tmp / "hibernation.jsonl"
    yes = lambda *a, **k: True   # noqa: E731
    no = lambda *a, **k: False   # noqa: E731

    # V-HIB-STORE-THEN-DESTROY: a verified anchor -> stored, slot may free.
    r = H.hibernate("s1", str(tmp), task="design", registry_path=reg,
                    anchor_exists_fn=yes)
    if r.ok and r.verdict == "HIBERNATED" and r.hot_slot_freed:
        _ok("V-HIB-STORE-THEN-DESTROY", "stored+verified -> hot slot may free")
    else:
        _fail("V-HIB-STORE-THEN-DESTROY", f"got {r.verdict}/{r.ok}")
    archive_id = r.archive_id

    # V-HIB-REFUSE-NO-ANCHOR: missing anchor -> REFUSED, session stays HOT.
    r2 = H.hibernate("s2", str(tmp), registry_path=reg, anchor_exists_fn=no)
    if (not r2.ok) and r2.verdict == "REFUSED" and not r2.hot_slot_freed:
        _ok("V-HIB-REFUSE-NO-ANCHOR", "no anchor -> stays HOT (never lose a session)")
    else:
        _fail("V-HIB-REFUSE-NO-ANCHOR", f"got {r2.verdict}/{r2.ok}")

    # V-HIB-RESTORE-RECOVERED: restore (cwd=tmp exists) -> RECOVERED, state intact.
    rr = H.restore(archive_id, registry_path=reg, anchor_exists_fn=yes)
    if rr.verdict == "RECOVERED" and rr.state and rr.state["sid"] == "s1":
        _ok("V-HIB-RESTORE-RECOVERED", "integrity-verified restore -> RECOVERED")
    else:
        _fail("V-HIB-RESTORE-RECOVERED", f"got {rr.verdict} {rr.state}")

    # V-HIB-ANCHOR-GONE: anchor vanished at restore -> FAILED (never silent).
    rg = H.restore(archive_id, registry_path=reg, anchor_exists_fn=no)
    if rg.verdict == "FAILED" and "transcript" in rg.missing:
        _ok("V-HIB-ANCHOR-GONE", "anchor gone -> FAILED, not a false RECOVERED")
    else:
        _fail("V-HIB-ANCHOR-GONE", f"got {rg.verdict}")

    # V-HIB-PARTIAL-CWD: cwd moved under the archive -> PARTIAL (enumerated).
    rp = H.hibernate("s3", "C:/gone/nowhere", registry_path=reg, anchor_exists_fn=yes)
    pr = H.restore(rp.archive_id, registry_path=reg, anchor_exists_fn=yes)
    if pr.verdict == "PARTIAL" and "cwd" in pr.missing:
        _ok("V-HIB-PARTIAL-CWD", "moved cwd -> PARTIAL (missing enumerated)")
    else:
        _fail("V-HIB-PARTIAL-CWD", f"got {pr.verdict}/{pr.missing}")

    # V-HIB-CORRUPT-DETECTED: a tampered archive blob -> FAILED integrity.
    bad = tmp / "bad.jsonl"
    bad.write_text(_json.dumps({"archive_id": "bad@1", "sid": "z",
                                "cwd": str(tmp), "blob": "@@not-valid@@",
                                "anchor_hash": "deadbeef"}) + "\n", encoding="utf-8")
    rc = H.restore("bad@1", registry_path=bad, anchor_exists_fn=yes)
    if rc.verdict == "FAILED" and "integrity" in rc.missing:
        _ok("V-HIB-CORRUPT-DETECTED",
            "tampered archive -> FAILED, never restored wrong")
    else:
        _fail("V-HIB-CORRUPT-DETECTED", f"got {rc.verdict}")


# --------------------------------------------------------------------------
# CO-10 -- Enforcement Guarantee Ledger (honesty)
# --------------------------------------------------------------------------
def test_co10_guarantee_ledger() -> None:
    from modules.cognitive_os import guarantee_ledger as L

    # V-LEDGER-CLASSIFY: the cap is honestly a WRAPPER (rung-3 block) mechanism.
    e = L.classify("CO-08-cap")
    if e and e.level == L.WRAPPER and "manual" in e.residual.lower():
        _ok("V-LEDGER-CLASSIFY", "CO-08 cap = WRAPPER; residual = manual terminal")
    else:
        _fail("V-LEDGER-CLASSIFY", f"got {e}")

    # V-LEDGER-CO00-HONEST: the flagship ceiling is rung-3 block; the residual
    # names the in-turn limit -- never a claimed physical mid-turn switch.
    c = L.classify("CO-00-ceiling")
    if c and L.block_power(c.level) == 3 and "mid-generation" in c.residual:
        _ok("V-LEDGER-CO00-HONEST", "ceiling = rung-3 block; in-turn residual named")
    else:
        _fail("V-LEDGER-CO00-HONEST", f"got {c}")

    # V-LEDGER-INFLATION: a HOOK mechanism claiming WRAPPER block -> flagged.
    a = L.audit_claim("CO-03-router", L.WRAPPER)
    if a.inflated:
        _ok("V-LEDGER-INFLATION", "HOOK claiming WRAPPER block -> inflation flagged")
    else:
        _fail("V-LEDGER-INFLATION", "inflation not caught")

    # V-LEDGER-NO-INFLATION: valid claim ok; unregistered claim flagged.
    a2 = L.audit_claim("CO-08-cap", L.WRAPPER)
    a3 = L.audit_claim("CO-99-fake", L.WRAPPER)
    if (not a2.inflated) and a3.inflated:
        _ok("V-LEDGER-NO-INFLATION", "valid claim ok; unregistered claim flagged")
    else:
        _fail("V-LEDGER-NO-INFLATION", f"got {a2.inflated}/{a3.inflated}")

    # V-LEDGER-UNGATED: live sessions with no wrapper record are surfaced.
    rep = L.un_gated_sessions(["a", "b", "c"], ["a"])
    if rep.un_gated == ["b", "c"] and rep.covered == ["a"]:
        _ok("V-LEDGER-UNGATED",
            "un-gated sids surfaced (counted, never claimed governed)")
    else:
        _fail("V-LEDGER-UNGATED", f"got {rep.un_gated}")


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
    print("[CO-09 loop/subagent budget]")
    test_co09_loop_budget()
    print("[CO-00 context -- 60% ceiling]")
    test_co00_context()
    print("[CO-03 router -- cascade]")
    test_co03_router()
    print("[CO-05 registry -- zero-token assets]")
    with tempfile.TemporaryDirectory() as td:
        test_co05_registry(Path(td))
    print("[CO-02 governor -- budget envelope]")
    with tempfile.TemporaryDirectory() as td:
        test_co02_governor(Path(td))
    print("[CO-04 memory -- tiers]")
    test_co04_memory()
    print("[CO-06 gc -- eviction policy]")
    test_co06_gc()
    print("[CO-07 hibernation -- store-then-destroy]")
    with tempfile.TemporaryDirectory() as td:
        test_co07_hibernation(Path(td))
    print("[CO-10 guarantee ledger -- honesty]")
    test_co10_guarantee_ledger()
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
