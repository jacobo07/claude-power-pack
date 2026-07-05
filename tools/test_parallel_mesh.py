#!/usr/bin/env python3
"""test_parallel_mesh.py -- Parallel Cognitive Mesh done-gates. Hermetic
(tmp state dirs, injected gather_fn/head_fn/scan_fn/burn_fn/cheap_fn, fixed
clock), re-runnable. Grows one sprint at a time.

Sprint 1 (PM-02): scope-gate recalibration of CO-08's blunt same-repo cap.
Sprint 2 (PM-03): shared findings bus + redundancy tax.
Sprint 3 (PM-01): repo shared brain + PM-01/02/03 coexistence.
Sprint 4 (PM-04): budget auction + concurrency modes + opus singleton.
Sprint 5 (PM-05): speculative prefetch (cheap + idle + net-positive).
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import scheduler as S       # noqa: E402
from modules.parallel_mesh import pm_02_intent as PM2  # noqa: E402
from modules.parallel_mesh import pm_03_bus as PM3     # noqa: E402
from modules.parallel_mesh import pm_01_brain as PM1   # noqa: E402
from modules.parallel_mesh import pm_04_auction as PM4  # noqa: E402
from modules.parallel_mesh import pm_05_prefetch as PM5  # noqa: E402

_p = 0
_f = 0


def _ok(gate, ev):
    global _p
    _p += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, diag):
    global _f
    _f += 1
    print(f"  FAIL {gate}: {diag}")


CWD = "/repo/tua-x"
REPO = CWD
ENC = S._enc(CWD)
NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)


def _hot(*sids):
    return [{"sid": s, "encs": [ENC]} for s in sids]


def _gather(hot):
    def g(**kw):
        ex = kw.get("exclude_sid")
        return [h for h in hot if h["sid"] != ex]
    return g


def sprint1():
    print("[PM-02 -- scope-gate recalibration]")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/x.py"], now=NOW)
        v = PM2.scope_gated_admit(CWD, "B", ["modules/y.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "proceed":
            _ok("V-PM02-INTENT-ALLOWED",
                "2 disjoint declared same-repo panes admitted simultaneously")
        else:
            _fail("V-PM02-INTENT-ALLOWED",
                  f"expected proceed, got {v.verdict}: {v.reasons}")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/x.py"], now=NOW)
        v = PM2.scope_gated_admit(CWD, "B", ["modules/x.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any("collides" in r for r in v.reasons):
            _ok("V-PM02-COLLISION-REFUSED",
                f"overlapping scope refused with resolution: {v.reasons[0]}")
        else:
            _fail("V-PM02-COLLISION-REFUSED",
                  f"expected refuse-on-collision, got {v.verdict}: {v.reasons}")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)  # A intentionally NOT declared
        v = PM2.scope_gated_admit(CWD, "B", ["modules/y.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any(
                "non-overlap cannot be proven" in r for r in v.reasons):
            _ok("V-PM02-UNKNOWNSCOPE-REFUSED",
                "undeclared incumbent blocks a declared pane (disjoint unprovable)")
        else:
            _fail("V-PM02-UNKNOWNSCOPE-REFUSED",
                  f"expected refuse-unknown, got {v.verdict}: {v.reasons}")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        v = PM2.scope_gated_admit(CWD, "C", None, registry=reg, now=NOW,
                                  gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any("blunt cap" in r for r in v.reasons):
            _ok("V-SCHEDULER-FAILSAFE",
                "undeclared same-repo pane hits the sealed blunt cap")
        else:
            _fail("V-SCHEDULER-FAILSAFE",
                  f"expected blunt-cap refuse, got {v.verdict}: {v.reasons}")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["a.py"], now=NOW)
        fresh = reg.active(CWD, now=NOW)
        stale = reg.active(CWD, now=NOW + timedelta(minutes=200))
        if len(fresh) == 1 and fresh[0].sid == "A" and not stale:
            _ok("V-PM02-REGISTRY-ROUNDTRIP",
                "intent persisted+read fresh; expired beyond the 120min window")
        else:
            _fail("V-PM02-REGISTRY-ROUNDTRIP",
                  f"fresh={[i.sid for i in fresh]} stale={[i.sid for i in stale]}")

    v0 = S.decide(_hot("A"), CWD, is_new=True)
    v1 = S.decide([], CWD, is_new=True)
    if v0.verdict == "refuse" and v1.verdict == "proceed":
        _ok("V-BASELINE-INTACT",
            "decide(declared=None) unchanged: 1-incumbent refuse / empty proceed")
    else:
        _fail("V-BASELINE-INTACT",
              f"sealed behavior drifted: {v0.verdict}/{v1.verdict}")


def sprint2():
    print("[PM-03 -- shared findings bus + redundancy tax]")

    with tempfile.TemporaryDirectory() as td:
        bus = PM3.FindingsBus(state_dir=td)
        bus.publish(REPO, "optimize loops in tua-x", "batch the io calls",
                    sid="A", now=NOW)
        tax = PM3.RedundancyTax(bus=bus)
        calls = []

        def _reason():
            calls.append(1)
            return "SHOULD-NOT-RUN"

        claim, reused, _ = tax.reason_or_reuse(
            REPO, "optimize loops in tua-x", _reason, sid="B", now=NOW)
        if reused and not calls and claim == "batch the io calls":
            _ok("V-PM03-REDUNDANCY-TAX",
                "bus hit reused A's finding; reason_fn never ran (0 new tokens)")
        else:
            _fail("V-PM03-REDUNDANCY-TAX",
                  f"reused={reused} calls={len(calls)} claim={claim!r}")

    with tempfile.TemporaryDirectory() as td:
        tax = PM3.RedundancyTax(bus=PM3.FindingsBus(state_dir=td))
        calls = []

        def _reason():
            calls.append(1)
            return "derived answer"

        claim, reused, _ = tax.reason_or_reuse(
            REPO, "fresh topic", _reason, sid="A", now=NOW)
        hit, _, _ = tax.consult(REPO, "fresh topic")
        if (not reused) and len(calls) == 1 and claim == "derived answer" and hit:
            _ok("V-PM03-MISS-REASONS",
                "miss reasoned once and published; a subsequent consult hits")
        else:
            _fail("V-PM03-MISS-REASONS",
                  f"reused={reused} calls={len(calls)} hit={hit} claim={claim!r}")

    with tempfile.TemporaryDirectory() as td:
        PM3.FindingsBus(state_dir=td).publish(REPO, "t", "c", sid="A", now=NOW)
        reloaded = PM3.FindingsBus(state_dir=td).load(REPO)
        if len(reloaded) == 1 and reloaded[0].claim == "c":
            _ok("V-PM03-BUS-PERSISTS",
                "finding persisted on disk across bus instances (survives sessions)")
        else:
            _fail("V-PM03-BUS-PERSISTS", f"reloaded={[f.claim for f in reloaded]}")

    with tempfile.TemporaryDirectory() as td:
        bus = PM3.FindingsBus(state_dir=td)
        bus.publish(REPO, "T", "same claim", sid="A", now=NOW)
        bus.publish(REPO, "T", "same claim", sid="B", now=NOW)
        n = len(bus.load(REPO))
        if n == 1:
            _ok("V-PM03-DEDUP",
                "identical finding published twice stored once (bus is not a log)")
        else:
            _fail("V-PM03-DEDUP", f"expected 1 stored, got {n}")

    with tempfile.TemporaryDirectory() as td:
        n = PM3.publish_session_findings(REPO, [
            {"topic": "a", "claim": "c1"},
            {"topic": "b", "claim": "c2"},
            {"topic": "", "claim": "skip-me"},
        ], sid="A", now=NOW, state_dir=td)
        loaded = PM3.FindingsBus(state_dir=td).load(REPO)
        if n == 2 and len(loaded) == 2:
            _ok("V-PM03-PUBLISH-ON-SESSION-END",
                "Cross-Pane Commit published 2 findings; malformed entry skipped")
        else:
            _fail("V-PM03-PUBLISH-ON-SESSION-END",
                  f"published={n} loaded={len(loaded)}")

    with tempfile.TemporaryDirectory() as td:
        sid = "sess-drain-1"
        PM3.stage_finding(REPO, sid, "dead fn foo", "foo() is unreferenced",
                          evidence="grep -rn foo", state_dir=td)
        PM3.stage_finding(REPO, sid, "real sig bar", "bar(x, y) not bar(x)",
                          state_dir=td)
        PM3.stage_finding(REPO, sid, "", "skip-me", state_dir=td)  # guarded out
        n = PM3.drain_staging_findings(REPO, sid, now=NOW, state_dir=td)
        loaded = PM3.FindingsBus(state_dir=td).load(REPO)
        again = PM3.drain_staging_findings(REPO, sid, now=NOW, state_dir=td)
        staging = PM3._staging_path(REPO, sid, td)
        if n == 2 and len(loaded) == 2 and again == 0 and not staging.exists():
            _ok("V-PM03-STAGE-DRAIN",
                "staged 3 (1 guarded) -> drained 2 to bus, staging cleared, re-drain=0")
        else:
            _fail("V-PM03-STAGE-DRAIN",
                  f"n={n} loaded={len(loaded)} again={again} "
                  f"staging={staging.exists()}")


def sprint3():
    print("[PM-01 -- repo shared brain + coexistence]")

    with tempfile.TemporaryDirectory() as td:
        store = PM1.BrainStore(state_dir=td)
        scans = []

        def _scan():
            scans.append(1)
            return "repo: modules/, tools/. decisions: jsonl bus. traps: bash-bridge."

        cons = PM1.RepoBrainConsumer(store=store, head_fn=lambda r: "H1")
        b1, g1 = cons.get_or_generate(REPO, _scan, now=NOW)
        b2, g2 = cons.get_or_generate(REPO, _scan, now=NOW)
        b3, g3 = cons.get_or_generate(REPO, _scan, now=NOW)
        if len(scans) == 1 and g1 and not g2 and not g3:
            _ok("V-PM01-BRAIN-GENERATED-ONCE",
                "3 same-repo panes -> exactly 1 repo scan (first generates)")
        else:
            _fail("V-PM01-BRAIN-GENERATED-ONCE",
                  f"scans={len(scans)} g=({g1},{g2},{g3})")
        if (not g2) and b2.content == b1.content and b3.content == b1.content:
            _ok("V-PM01-CONSUMERS-USE-BRAIN",
                "panes 2+3 consumed the existing brain (identical content, no rescan)")
        else:
            _fail("V-PM01-CONSUMERS-USE-BRAIN",
                  f"g2={g2} content_match={b2.content == b1.content}")

    with tempfile.TemporaryDirectory() as td:
        store = PM1.BrainStore(state_dir=td)
        scans = []

        def _scan():
            scans.append(1)
            return f"scan-{len(scans)}"

        c1 = PM1.RepoBrainConsumer(store=store, head_fn=lambda r: "H1")
        _b1, g1 = c1.get_or_generate(REPO, _scan, now=NOW)
        c2 = PM1.RepoBrainConsumer(store=store, head_fn=lambda r: "H2")
        b2, g2 = c2.get_or_generate(REPO, _scan, now=NOW)
        if g1 and g2 and len(scans) == 2 and b2.head == "H2":
            _ok("V-PM01-STALE-ON-COMMIT",
                "new commit (H1->H2) marked brain stale -> regenerated at new head")
        else:
            _fail("V-PM01-STALE-ON-COMMIT",
                  f"g=({g1},{g2}) scans={len(scans)} head={b2.head}")

    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        brainstore = PM1.BrainStore(state_dir=td)
        bus = PM3.FindingsBus(state_dir=td)
        scans = []

        def _scan():
            scans.append(1)
            return "repo brief"

        reg.declare("A", REPO, ["modules/x.py"], now=NOW)
        consA = PM1.RepoBrainConsumer(store=brainstore, head_fn=lambda r: "H1")
        _bA, gA = consA.get_or_generate(REPO, _scan, now=NOW)
        bus.publish(REPO, "loop opt", "batch io", sid="A", now=NOW)

        admit = PM2.scope_gated_admit(REPO, "B", ["modules/y.py"], registry=reg,
                                      now=NOW, gather_fn=_gather(_hot("A")))
        consB = PM1.RepoBrainConsumer(store=brainstore, head_fn=lambda r: "H1")
        _bB, gB = consB.get_or_generate(REPO, _scan, now=NOW)
        hitB, fB, _ = PM3.RedundancyTax(bus=bus).consult(REPO, "loop opt")

        if (admit.verdict == "proceed" and gA and not gB and len(scans) == 1
                and hitB and fB is not None and fB.claim == "batch io"):
            _ok("V-PM01-COEXISTS-PM02-PM03",
                "2-pane flow: B admitted, consumed brain (1 scan total), found A's finding")
        else:
            _fail("V-PM01-COEXISTS-PM02-PM03",
                  f"admit={admit.verdict} gA={gA} gB={gB} scans={len(scans)} "
                  f"hitB={hitB}")


def sprint4():
    print("[PM-04 -- budget auction + concurrency modes]")

    mv = PM4.current_mode(burn_fn=lambda: 0.8)
    g = PM4.budget_gate(mv, model="opus", roi=1.0)
    if mv.mode == PM4.GREEN and not g.lines and g.suggested_model == "opus" \
            and not g.blocks:
        _ok("V-PM04-GREEN-NO-FRICTION",
            "Green (0.8x burn): Opus admitted with no advisory, no friction")
    else:
        _fail("V-PM04-GREEN-NO-FRICTION",
              f"mode={mv.mode} lines={g.lines} suggested={g.suggested_model}")

    mv = PM4.current_mode(burn_fn=lambda: 1.3)
    g = PM4.budget_gate(mv, model="opus", roi=1.0, roi_justified=False)
    if mv.mode == PM4.YELLOW and any("Opus requested without ROI" in ln
                                     for ln in g.lines) \
            and g.suggested_model == "sonnet":
        _ok("V-PM04-YELLOW-OPUS-ADVISORY",
            "Yellow (1.3x): unjustified Opus -> advisory + Sonnet suggested")
    else:
        _fail("V-PM04-YELLOW-OPUS-ADVISORY",
              f"mode={mv.mode} lines={g.lines} suggested={g.suggested_model}")

    mv = PM4.current_mode(burn_fn=lambda: 2.5)
    g = PM4.budget_gate(mv, model="sonnet")
    if mv.mode == PM4.BLACK and any("/compact" in ln for ln in g.lines):
        _ok("V-PM04-BLACK-COMPACT-ADVISORY",
            "Black (2.5x): /compact-or-kclear advisory before a new heavy prompt")
    else:
        _fail("V-PM04-BLACK-COMPACT-ADVISORY",
              f"mode={mv.mode} lines={g.lines}")

    mv = PM4.current_mode(burn_fn=lambda: 1.3)
    g = PM4.budget_gate(mv, model="opus", opus_incumbents=1, roi_justified=False,
                        repo=REPO)
    if any("Opus Singleton" in ln for ln in g.lines):
        _ok("V-PM04-OPUS-SINGLETON-ADVISORY",
            "2nd Opus-heavy pane same repo (Yellow) -> Opus Singleton advisory")
    else:
        _fail("V-PM04-OPUS-SINGLETON-ADVISORY", f"lines={g.lines}")

    mv = PM4.current_mode(burn_fn=lambda: 3.0)
    g = PM4.budget_gate(mv, model="opus", opus_incumbents=2, roi_justified=False)
    if mv.mode == PM4.BLACK and g.blocks is False and g.lines:
        _ok("V-PM04-FAILOPEN-OWNER-OVERRIDE",
            "Black + unjustified Opus: advisories present but blocks=False (fail-open)")
    else:
        _fail("V-PM04-FAILOPEN-OWNER-OVERRIDE",
              f"mode={mv.mode} blocks={g.blocks} lines={len(g.lines)}")

    with tempfile.TemporaryDirectory() as empty:
        real = PM4.current_mode(proj_base=empty)
        inj = PM4.current_mode(burn_fn=lambda: 1.7)
        if real.mode == PM4.GREEN \
                and (real.source == "real" or real.source.startswith("failopen-green")) \
                and inj.mode == PM4.RED and inj.source == "real" and inj.factor == 1.7:
            _ok("V-PM04-READS-REAL-BURN",
                f"real cost_gate path ran ({real.source}); injected 1.7x -> RED")
        else:
            _fail("V-PM04-READS-REAL-BURN",
                  f"real=({real.mode},{real.source}) inj=({inj.mode},{inj.factor})")


def sprint5():
    print("[PM-05 -- speculative prefetch (cheap + idle + net-positive)]")

    # V-PM05-CHEAP-ONLY: an Opus-tier prefetch is refused (routing violation).
    eng = PM5.SpeculativePrefetch()
    calls = []
    r = eng.prefetch(REPO, "index", lambda: calls.append(1) or "asset",
                     mode=PM4.GREEN, hot_count=0, tier="opus")
    if (not r.ran) and "cheap-only" in r.reason and not calls:
        _ok("V-PM05-CHEAP-ONLY", "Opus-tier prefetch refused; producer never ran")
    else:
        _fail("V-PM05-CHEAP-ONLY", f"ran={r.ran} reason={r.reason} calls={len(calls)}")

    # V-PM05-GREEN-ONLY: non-Green mode -> no prefetch.
    eng = PM5.SpeculativePrefetch()
    r = eng.prefetch(REPO, "index", lambda: "asset", mode=PM4.YELLOW, hot_count=0)
    if (not r.ran) and "GREEN" in r.reason:
        _ok("V-PM05-GREEN-ONLY", "Yellow mode -> prefetch suspended (idle-only)")
    else:
        _fail("V-PM05-GREEN-ONLY", f"ran={r.ran} reason={r.reason}")

    # V-PM05-IDLE-ONLY: a hot pane -> fail-stop even in Green.
    eng = PM5.SpeculativePrefetch()
    r = eng.prefetch(REPO, "index", lambda: "asset", mode=PM4.GREEN, hot_count=1)
    if (not r.ran) and "fail-stop" in r.reason:
        _ok("V-PM05-IDLE-ONLY", "a hot pane -> fail-stop (no prefetch while active)")
    else:
        _fail("V-PM05-IDLE-ONLY", f"ran={r.ran} reason={r.reason}")

    # V-PM05-NET-POSITIVE-DISABLE: a net-negative class is auto-disabled.
    ledger = PM5.NetPositiveLedger()
    for _ in range(3):
        ledger.record_prefetch("depmap", spent=10)   # 30 spent, 0 saved
    eng = PM5.SpeculativePrefetch(ledger=ledger)
    r = eng.prefetch(REPO, "depmap", lambda: "asset", mode=PM4.GREEN, hot_count=0)
    if (not r.ran) and "net-negative" in r.reason:
        _ok("V-PM05-NET-POSITIVE-DISABLE",
            "class costing more than it saves auto-disabled")
    else:
        _fail("V-PM05-NET-POSITIVE-DISABLE", f"ran={r.ran} reason={r.reason}")

    # V-PM05-RUNS-WHEN-IDLE: all gates pass -> the cheap producer runs once.
    eng = PM5.SpeculativePrefetch()
    calls = []
    r = eng.prefetch(REPO, "index", lambda: calls.append(1) or "<index>",
                     mode=PM4.GREEN, hot_count=0, tier="deterministic")
    if r.ran and r.asset == "<index>" and len(calls) == 1:
        _ok("V-PM05-RUNS-WHEN-IDLE",
            "green + idle + cheap + net-positive -> prefetch ran once")
    else:
        _fail("V-PM05-RUNS-WHEN-IDLE",
              f"ran={r.ran} asset={r.asset!r} calls={len(calls)}")


def sprint6():
    print("[CO-08 -- intent-gate wired into the live launch path (prelaunch._gate)]")
    import os
    from modules.wrapper import prelaunch as PRE

    # V-CO08-DIFFERENT-REPO-FREE (pure): a hot pane on a DIFFERENT repo never
    # counts toward this repo's same-repo cap.
    other = [{"sid": "X", "encs": [S._enc("/repo/other")]}]
    d = S.decide(other, CWD, is_new=True, declared=("modules/x.py",), hot_scopes={})
    if d.verdict == "proceed" and d.same_repo_count == 0:
        _ok("V-CO08-DIFFERENT-REPO-FREE",
            "hot incumbent on a different repo -> no same-repo restriction")
    else:
        _fail("V-CO08-DIFFERENT-REPO-FREE",
              f"verdict={d.verdict} same_repo={d.same_repo_count}")

    def _run_gate(scope_env, sid_env, **kw):
        prev = (os.environ.get("PP_PANE_SCOPE"), os.environ.get("PP_PANE_SID"))
        try:
            for k, val in (("PP_PANE_SCOPE", scope_env), ("PP_PANE_SID", sid_env)):
                if val is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = val
            return PRE._gate(CWD, now=NOW, **kw)
        finally:
            for k, val in (("PP_PANE_SCOPE", prev[0]), ("PP_PANE_SID", prev[1])):
                if val is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = val

    # V-CO08-NOINTENT-CAPPED: no PP_PANE_SCOPE -> blunt cap; a same-repo hot refuses.
    g = _run_gate(None, None, gather_fn=_gather(_hot("A")))
    if g["verdict"] == "refuse" and any("blunt cap" in r for r in g["reasons"]):
        _ok("V-CO08-NOINTENT-CAPPED",
            "undeclared launch + 1 same-repo hot -> blunt SAME_REPO_CAP refuses")
    else:
        _fail("V-CO08-NOINTENT-CAPPED",
              f"verdict={g['verdict']} reasons={g['reasons']}")

    # V-CO08-INTENT-ALLOWED: declared disjoint scope -> live gate admits a 2nd
    # same-repo pane alongside an incumbent with a NON-overlapping intent.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/y.py"], now=NOW)
        g = _run_gate("modules/x.py", "B", gather_fn=_gather(_hot("A")), registry=reg)
        if g["verdict"] == "proceed":
            _ok("V-CO08-INTENT-ALLOWED",
                "declared disjoint scope -> live gate admits 2nd same-repo pane")
        else:
            _fail("V-CO08-INTENT-ALLOWED",
                  f"verdict={g['verdict']} reasons={g['reasons']}")

    # V-CO08-INTENT-COLLISION: declared OVERLAPPING scope -> live gate refuses.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/x.py"], now=NOW)
        g = _run_gate("modules/x.py", "B", gather_fn=_gather(_hot("A")), registry=reg)
        if g["verdict"] == "refuse" and any("collides" in r for r in g["reasons"]):
            _ok("V-CO08-INTENT-COLLISION",
                "declared overlapping scope -> live gate refuses (collision)")
        else:
            _fail("V-CO08-INTENT-COLLISION",
                  f"verdict={g['verdict']} reasons={g['reasons']}")


def sprint7():
    print("[CO-08 -- launch-scope recall (kclaude auto-export source)]")

    # V-SCOPE-RESOLVED-FROM-INTENT: a pane's OWN declared intent for (cwd, sid)
    # is recalled as the comma-joined PP_PANE_SCOPE the launcher exports on resume.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("S1", CWD, ["modules/x.py", "tools/y.py"], now=NOW)
        scope = PM2.resolve_launch_scope(CWD, "S1", now=NOW, state_dir=td)
        if scope == "modules/x.py,tools/y.py":
            _ok("V-SCOPE-RESOLVED-FROM-INTENT",
                f"declared (cwd,sid) intent recalled as PP_PANE_SCOPE={scope!r}")
        else:
            _fail("V-SCOPE-RESOLVED-FROM-INTENT", f"got {scope!r}")

    # V-SCOPE-EMPTY-WITHOUT-INTENT: unknown sid AND missing sid both -> '' ->
    # launcher exports nothing -> CO-08 blunt SAME_REPO_CAP failsafe applies.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("S1", CWD, ["modules/x.py"], now=NOW)
        no_entry = PM2.resolve_launch_scope(CWD, "S2", now=NOW, state_dir=td)
        no_sid = PM2.resolve_launch_scope(CWD, None, now=NOW, state_dir=td)
        if no_entry == "" and no_sid == "":
            _ok("V-SCOPE-EMPTY-WITHOUT-INTENT",
                "unknown sid and missing sid both -> '' (failsafe direction)")
        else:
            _fail("V-SCOPE-EMPTY-WITHOUT-INTENT",
                  f"no_entry={no_entry!r} no_sid={no_sid!r}")

    # V-SCOPE-FAILOPEN-STALE: an intent older than the 120min window -> '' (a
    # pane no longer hot must not re-export a phantom scope); missing state -> ''.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("S1", CWD, ["modules/x.py"], now=NOW)
        stale = PM2.resolve_launch_scope(CWD, "S1",
                                         now=NOW + timedelta(minutes=200),
                                         state_dir=td)
        missing = PM2.resolve_launch_scope(CWD, "S1", now=NOW,
                                           state_dir=str(Path(td) / "nope"))
        if stale == "" and missing == "":
            _ok("V-SCOPE-FAILOPEN-STALE",
                "stale (>120min) and missing state both fail-open to ''")
        else:
            _fail("V-SCOPE-FAILOPEN-STALE", f"stale={stale!r} missing={missing!r}")


def main():
    sprint1()
    sprint2()
    sprint3()
    sprint4()
    sprint5()
    sprint6()
    sprint7()
    total = _p + _f
    print(f"PARALLEL_MESH_PASS={_p}/{total}  threshold={total}/{total}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
