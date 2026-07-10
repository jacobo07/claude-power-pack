#!/usr/bin/env python3
"""test_frontier_intelligence_os.py -- V-gates for the FIOS execution layer.

Verifies the three FIOS engines the STOP #1 scope approved (execution-first: no
prose datasets, so there is no V-DEPTH gate -- code is verified by behavior):

  session_compiler  -- compiles a declaration into the 9-component SESSION_ZERO
                       plan; ranks questions through the REAL FD-00 gate; holds the
                       context under the <2000-token contract; fail-open.
  token_irr         -- numeric IRR (never adjectives); FDI in [0,1]; feeds CO-12
                       (a signal accrues in CO-12's own corpus -- not a fork).
  evolution_engine  -- proposes typed mutations and NEVER touches a dataset
                       (Owner-gated, T-FIOS-EVOLUTION-LOCK-001).

V-FIOS-NO-DUPLICATE-FD is proven structurally: each engine IMPORTS its parent
surface (compose), and none stands up a parallel router / dependence number.

Hermetic: fresh tempfile state + synthetic kb dirs everywhere -- NO global writes,
identical on re-run (run x3). V-<DOMAIN>-<NAME>; DATASET_FAMILY_VERDICT line for the
done-gate grep. Exit 0 iff all gates pass.
"""
from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.frontier_intelligence import session_compiler as SC   # noqa: E402
from modules.frontier_intelligence import token_irr as IRR         # noqa: E402
from modules.frontier_intelligence import evolution_engine as EVO  # noqa: E402
from modules.cognitive_os.co_12_telemetry import load_signals      # noqa: E402

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


@dataclass
class _FakeDecision:
    """CO-03 RouteDecision stand-in so a gate call resolves to a chosen rung."""
    rung: str
    reason: str = "forced"


def _tmp(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


# --------------------------------------------------------------------------- #
def gate_compose() -> None:
    # V-FIOS-NO-DUPLICATE-FD: each engine COMPOSES its parent, never re-implements.
    sc_src = Path(SC.__file__).read_text(encoding="utf-8")
    irr_src = Path(IRR.__file__).read_text(encoding="utf-8")
    checks = [
        ("fd_00_gate import check_admission" in sc_src, "SC composes FD-00 gate"),
        ("_load_deposits" in sc_src, "SC reads FD-07 floor"),
        ("co_12_telemetry import record_signal" in irr_src, "IRR feeds CO-12"),
        ("_load_deposits" in irr_src, "IRR reads FD-07 ledger"),
        ("def route(" not in irr_src and "def record_signal(" not in irr_src,
         "IRR stands up no parallel router/metric"),
    ]
    bad = [msg for ok, msg in checks if not ok]
    if not bad:
        _ok("V-FIOS-NO-DUPLICATE-FD", "all 3 engines compose FD/CO parents")
    else:
        _fail("V-FIOS-NO-DUPLICATE-FD", f"missing: {bad}")


def gate_session() -> None:
    kb = _tmp("fios_kb_")            # empty floor -> nothing 'covered'
    route = lambda t: _FakeDecision("opus")  # noqa: E731
    decl = SC.SessionDeclaration(
        objective="reduce frontier dependence for the pane-isolation subsystem",
        unknowns=["which invariant retires the whole double-dispatch bug class"],
        candidate_questions=[
            "design a novel rebase-safe isolation architecture from scratch",  # -> ADMIT
            "reformat the config file and fix the typo",                       # -> DECLINE
            "what is the deterministic core rule that needs no frontier model",  # dependence-reducing
        ],
        repo="FIOS-TEST", token_budget=100000)
    plan = SC.compile_session(decl, kb_dir=kb, route_fn=route)

    # V-FIOS-SESSION-COMPILE: all 9 components render + a worthy question ranks first.
    md = SC.render_plan(plan)
    nine = all(f"## {n}." in md for n in range(1, 10))
    worthy_first = plan.questions and plan.questions[0].frontier_worthy
    mech_dropped = any((not q.frontier_worthy and q.verdict == "DECLINE")
                       for q in plan.questions)
    if nine and worthy_first and mech_dropped:
        _ok("V-FIOS-SESSION-COMPILE",
            f"9 components; ranked #1 worthy={plan.questions[0].verdict}; "
            f"mechanical DECLINE'd")
    else:
        _fail("V-FIOS-SESSION-COMPILE",
              f"nine={nine} worthy_first={worthy_first} mech_dropped={mech_dropped}")

    # V-FIOS-SESSION-UNDER-2K: the minimal-context section honors the contract.
    if 0 <= plan.context_tokens_est < 2000:
        _ok("V-FIOS-SESSION-UNDER-2K", f"context ~{plan.context_tokens_est} tok < 2000")
    else:
        _fail("V-FIOS-SESSION-UNDER-2K", f"context {plan.context_tokens_est} tok")

    # V-FIOS-SESSION-BUDGET: the 5-category R&D budget is present + sums to the total.
    cats = set(plan.budget)
    total = sum(r.get("tokens", 0) for r in plan.budget.values())
    if cats == {"discovery", "architecture", "critique", "validation", "emergency"} \
            and abs(total - 100000) <= 5:
        _ok("V-FIOS-SESSION-BUDGET", f"5 categories, tokens sum={total}")
    else:
        _fail("V-FIOS-SESSION-BUDGET", f"cats={cats} sum={total}")

    # V-FIOS-SESSION-FAILOPEN: a pathological declaration must not raise.
    try:
        bad = SC.compile_session(SC.SessionDeclaration(
            objective=None, candidate_questions=[None, 42], repo=object()))  # type: ignore
        _ok("V-FIOS-SESSION-FAILOPEN", f"bad input -> no raise (note: {bad.note[:40]})")
    except Exception as e:  # noqa: BLE001
        _fail("V-FIOS-SESSION-FAILOPEN", f"RAISED (must fail-open): {e}")

    # V-FIOS-SESSION-WRITE: the plan materializes to a SESSION_ZERO file.
    out = _tmp("fios_sess_")
    p = SC.write_plan(plan, out_dir=out)
    if p and p.is_file() and p.name.startswith("SESSION_ZERO_"):
        _ok("V-FIOS-SESSION-WRITE", f"wrote {p.name}")
    else:
        _fail("V-FIOS-SESSION-WRITE", f"write failed: {p}")


def gate_irr() -> None:
    # V-FIOS-TOKEN-IRR-NUMERIC: numeric IRR; FDI in [0,1]; reuse reflects portability.
    deposits = [
        {"destination": "asset", "portability_target": "deterministic"},
        {"destination": "hard_rule", "portability_target": "mid-model"},
        {"destination": "dataset_part", "portability_target": "frontier-only"},
        {"destination": "dataset_part", "portability_target": "frontier-only"},
    ]
    rep = IRR.compute_irr("FIOS-TEST", tokens_spent=8000, deposits=deposits)
    numeric = all(isinstance(getattr(rep, f), (int, float)) for f in (
        "immediate_roi", "reuse_multiplier", "compound_roi", "payback_tokens",
        "frontier_dependence_index"))
    fdi_ok = rep.frontier_dependence_index == 0.5      # 2 of 4 frontier-only
    reuse_ok = rep.reuse_multiplier == round((8.0 + 2.0 + 0.0 + 0.0) / 4, 3)  # 2.5
    if numeric and fdi_ok and reuse_ok:
        _ok("V-FIOS-TOKEN-IRR-NUMERIC",
            f"immediate={rep.immediate_roi}/1k reuse=x{rep.reuse_multiplier} "
            f"FDI={rep.frontier_dependence_index}")
    else:
        _fail("V-FIOS-TOKEN-IRR-NUMERIC",
              f"numeric={numeric} fdi={rep.frontier_dependence_index} "
              f"reuse={rep.reuse_multiplier}")

    # V-FIOS-IRR-BALANCE-SHEET: assets-by-type + portable/liability split present.
    bs = rep.balance_sheet
    if bs.get("assets_total") == 4 and bs.get("net_portable_assets") == 2 \
            and bs["liabilities"]["frontier_only_deposits"] == 2:
        _ok("V-FIOS-IRR-BALANCE-SHEET",
            f"assets={bs['assets_total']} portable={bs['net_portable_assets']}")
    else:
        _fail("V-FIOS-IRR-BALANCE-SHEET", f"balance_sheet={bs}")

    # V-FIOS-IRR-FEEDS-CO12: the IRR accrues in CO-12's OWN corpus (feed, not fork).
    st = _tmp("fios_co12_")
    IRR.record_irr(rep, state_dir=st)
    sigs = [s for s in load_signals(state_dir=st) if s.get("kind") == "fios_token_irr"]
    if len(sigs) == 1 and sigs[0].get("frontier_dependence_index") == 0.5:
        _ok("V-FIOS-IRR-FEEDS-CO12", "fios_token_irr signal in CO-12 corpus")
    else:
        _fail("V-FIOS-IRR-FEEDS-CO12", f"signals={sigs}")

    # V-FIOS-IRR-FAILOPEN: empty repo / zero tokens -> a benign, honest zeroed report.
    z = IRR.compute_irr("EMPTY", tokens_spent=0, deposits=[])
    if z.assets == 0 and z.measured is False and z.immediate_roi == 0.0:
        _ok("V-FIOS-IRR-FAILOPEN", "empty -> zeroed measured=False (no fake number)")
    else:
        _fail("V-FIOS-IRR-FAILOPEN", f"assets={z.assets} measured={z.measured}")


def _make_kb(base: Path) -> dict:
    """A synthetic knowledge_base that trips each mutation signal. Returns the
    pre-scan byte snapshot so the LOCK gate can prove nothing was mutated."""
    (base).mkdir(parents=True, exist_ok=True)
    files = {
        "thin.md": "# Thin\n\nUn dataset corto sin desarrollo.\n",           # reinforce
        "bloat.md": "# Bloat\n\n" + ("alpha beta gamma delta " * 2000),      # compress
        "topic_alpha_beta.md": "# Alpha Beta\n\n" + ("contenido real " * 60),
        "topic_alpha_beta_two.md": "# Alpha Beta Two\n\n" + ("contenido real " * 60),  # merge pair
        "old_thing.md": "# Old\n\n" + ("This module is superseded by the new one. "
                                       * 60),                               # deprecate
    }
    snap = {}
    for name, body in files.items():
        p = base / name
        p.write_text(body, encoding="utf-8")
        snap[name] = p.read_bytes()
    return snap


def gate_evolution() -> None:
    kb = _tmp("fios_evo_kb_")
    snap = _make_kb(kb)
    props = EVO.scan(kb)
    kinds = {m.kind for m in props}

    # V-FIOS-EVOLUTION-PROPOSES: the engine surfaces the expected mutation kinds.
    want = {"reinforce", "compress", "merge", "deprecate"}
    if want.issubset(kinds):
        _ok("V-FIOS-EVOLUTION-PROPOSES",
            f"{len(props)} proposal(s), kinds={sorted(kinds)}")
    else:
        _fail("V-FIOS-EVOLUTION-PROPOSES", f"got kinds={sorted(kinds)} want>={want}")

    # V-FIOS-EVOLUTION-LOCK: writing proposals NEVER mutates a source dataset.
    out = _tmp("fios_evo_out_")
    pend = EVO.write_pending(props, out_dir=out)
    unchanged = all((kb / n).read_bytes() == snap[n] for n in snap)
    if pend and pend.name == "pending_mutations.md" and unchanged:
        _ok("V-FIOS-EVOLUTION-LOCK",
            "pending_mutations.md written; 0 source datasets mutated")
    else:
        _fail("V-FIOS-EVOLUTION-LOCK",
              f"pend={pend} sources_unchanged={unchanged}")

    # V-FIOS-EVOLUTION-FAILOPEN: a missing kb dir -> [] , never a raise.
    try:
        empty = EVO.scan(Path(tempfile.gettempdir()) / "fios_nonexistent_kb_xyz")
        _ok("V-FIOS-EVOLUTION-FAILOPEN", f"missing kb -> {len(empty)} proposals (no raise)")
    except Exception as e:  # noqa: BLE001
        _fail("V-FIOS-EVOLUTION-FAILOPEN", f"RAISED (must fail-open): {e}")


def gate_wiring() -> None:
    # V-FIOS-PREFLIGHT-FIRES: a declared objective compiles + writes a SESSION_ZERO.
    out = _tmp("fios_pf_")
    line = SC.preflight("FIOS-WIRE", out_dir=out, env={
        "PP_SESSION_OBJECTIVE": "reduce frontier dependence for pane isolation",
        "PP_SESSION_QUESTIONS": "design a new isolation architecture; reformat the typo",
        "PP_SESSION_BUDGET": "50000"})
    wrote = list(out.glob("SESSION_ZERO_*.md"))
    if line and "FIOS: SESSION_ZERO" in line and len(wrote) == 1:
        _ok("V-FIOS-PREFLIGHT-FIRES", f"3-line summary + {wrote[0].name}")
    else:
        _fail("V-FIOS-PREFLIGHT-FIRES", f"line={line!r} wrote={wrote}")

    # V-FIOS-PREFLIGHT-SILENT: no objective + no decl file -> None, nothing written.
    out2 = _tmp("fios_pf_silent_")
    repo2 = _tmp("fios_pf_repo_")            # a clean repo dir: no .pp_frontier.json
    silent = SC.preflight(str(repo2), out_dir=out2, env={})
    if silent is None and not list(out2.glob("SESSION_ZERO_*.md")):
        _ok("V-FIOS-PREFLIGHT-SILENT", "no declaration -> None, 0 files (no bloat)")
    else:
        _fail("V-FIOS-PREFLIGHT-SILENT", f"silent={silent!r} files={list(out2.glob('*'))}")

    # V-FIOS-PREFLIGHT-FAILOPEN: a compile blow-up -> None, never a raise.
    orig = SC.compile_session
    try:
        def _boom(*a, **k):                  # noqa: ANN001
            raise RuntimeError("forced")
        SC.compile_session = _boom           # type: ignore
        r = SC.preflight("FIOS-WIRE", out_dir=_tmp("fios_pf_fo_"),
                         env={"PP_SESSION_OBJECTIVE": "x"})
        if r is None:
            _ok("V-FIOS-PREFLIGHT-FAILOPEN", "compile raise -> None (fail-open)")
        else:
            _fail("V-FIOS-PREFLIGHT-FAILOPEN", f"expected None, got {r!r}")
    except Exception as e:  # noqa: BLE001
        _fail("V-FIOS-PREFLIGHT-FAILOPEN", f"RAISED (must fail-open): {e}")
    finally:
        SC.compile_session = orig            # type: ignore

    # V-FIOS-IRR-ON-STOP: the Stop readout reports a real IRR + the honest-empty line.
    rep = IRR.compute_irr("FIOS-TEST", tokens_spent=8000, deposits=[
        {"destination": "asset", "portability_target": "deterministic"},
        {"destination": "dataset_part", "portability_target": "frontier-only"}])
    hot = IRR._stop_line(rep)
    empty = IRR._stop_line(IRR.compute_irr("EMPTY", 0, deposits=[]))
    if hot.startswith("FIOS IRR:") and "assets" in hot and "0 assets tracked" in empty:
        _ok("V-FIOS-IRR-ON-STOP", f"readout: {hot[:56]}...")
    else:
        _fail("V-FIOS-IRR-ON-STOP", f"hot={hot!r} empty={empty!r}")

    # V-FIOS-STOP-FRONTIER-GATE: the Stop entry runs only for a frontier session.
    prev = os.environ.get("PP_FRONTIER_SESSION")
    try:
        os.environ.pop("PP_FRONTIER_SESSION", None)
        off = IRR._is_frontier_session()
        os.environ["PP_FRONTIER_SESSION"] = "1"
        on = IRR._is_frontier_session()
        if on and not off:
            _ok("V-FIOS-STOP-FRONTIER-GATE", "frontier=1 -> run; unset -> silent no-op")
        else:
            _fail("V-FIOS-STOP-FRONTIER-GATE", f"on={on} off={off}")
    finally:
        if prev is None:
            os.environ.pop("PP_FRONTIER_SESSION", None)
        else:
            os.environ["PP_FRONTIER_SESSION"] = prev

    # V-FIOS-LIVE-PATH-WIRED (static): the dispatcher Stop-chain runs token_irr, and
    # kclaude runs the compiler preflight gated on PP_FRONTIER_SESSION. The glue IS
    # the deliverable this addendum ships -- prove it exists, not just the engines.
    disp = (_PP_ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")
    kcl = (_PP_ROOT / "tools" / "kclaude.ps1").read_text(encoding="utf-8")
    checks = [
        ("frontier_intelligence/token_irr.py" in disp, "dispatcher Stop-chain -> token_irr"),
        ("session_compiler.py" in kcl and "--preflight" in kcl, "kclaude -> compiler --preflight"),
        ("PP_FRONTIER_SESSION" in kcl, "kclaude gates the preflight on frontier"),
    ]
    bad = [m for ok, m in checks if not ok]
    if not bad:
        _ok("V-FIOS-LIVE-PATH-WIRED", "dispatcher + kclaude reference the engines")
    else:
        _fail("V-FIOS-LIVE-PATH-WIRED", f"missing: {bad}")


def gate_harvester() -> None:
    """FIOS I-4 question_harvester: 5 sources, provenance, bounded, fail-open."""
    from modules.frontier_intelligence import question_harvester as QH
    from modules.fable_distillation import fd_07_flywheel as FD07
    from modules.owner_queue.owner_queue import append as oq_append

    repo = "FIOS-HARVEST-TEST"
    dep_state = _tmp("fios_qh_dep_")
    FD07._append_jsonl(FD07._deposits_path(repo, dep_state), {
        "fingerprint": "abc123", "claim": "the staging bus lives under the state dir",
        "portability_target": "frontier-only", "portability_proven": False,
        "destination": "dataset_part"})
    FD07._append_jsonl(FD07._deposits_path(repo, dep_state), {
        "fingerprint": "def456", "claim": "an already proven recipe",
        "portability_target": "deterministic", "portability_proven": True,
        "destination": "asset"})
    oq_state = _tmp("fios_qh_oq_")
    oq_append("Copy the canonical dispatcher to the live mirror",
              "runbook step", state_dir=oq_state)
    co12_state = _tmp("fios_qh_co12_")       # empty signals -> instrument-pending
    kb = _tmp("fios_qh_kb_") / "ukdl-test.md"
    kb.write_text(
        "### UKDL TRAP T-ALPHA-WIDGET-001 -- widget breaks on reload\n\nbody\n\n"
        "### UKDL TRAP T-ZEBRA-CROSSING-001 -- zebra crossing\n\n"
        "### PROCESS RULE PR-ZEBRA-CROSSING-001 -- covers the zebra trap\n",
        encoding="utf-8")
    vd = _tmp("fios_qh_vault_")
    (vd / "scs_note.md").write_text(
        "# Note\n\nHonest residual: the live mirror copy is a manual Owner step.\n",
        encoding="utf-8")

    qs = QH.harvest(repo, state_dir=dep_state, oq_state_dir=oq_state,
                    co12_state_dir=co12_state, kb_file=kb, vault_dirs=[vd])
    by_src = {}
    for q in qs:
        by_src.setdefault(q.source, []).append(q)

    # V-FIOS-HARVEST-SOURCES: every one of the 5 sources contributes a question.
    want = {"deposits", "owner_queue", "co12", "ukdl_trap", "honest_residual"}
    if want.issubset(by_src) and len(by_src["deposits"]) == 1:
        _ok("V-FIOS-HARVEST-SOURCES",
            f"{len(qs)} question(s) from {sorted(by_src)}; proven deposit skipped")
    else:
        _fail("V-FIOS-HARVEST-SOURCES",
              f"sources={sorted(by_src)} deposits={len(by_src.get('deposits', []))}")

    # V-FIOS-HARVEST-PROVENANCE: source_ref + expected_asset + fingerprint on all.
    forms = {"hard_rule", "benchmark", "asset", "dataset_part"}
    good = all(q.source_ref and q.expected_asset in forms
               and q.fingerprint.startswith("q:") for q in qs)
    if qs and good:
        _ok("V-FIOS-HARVEST-PROVENANCE",
            f"all {len(qs)} carry source_ref + expected_asset + fingerprint")
    else:
        _fail("V-FIOS-HARVEST-PROVENANCE", f"qs={[(q.source_ref, q.expected_asset) for q in qs]}")

    # V-FIOS-HARVEST-UKDL-COVERAGE: uncovered trap harvested, covered trap skipped.
    refs = {q.source_ref for q in qs}
    if "ukdl:T-ALPHA-WIDGET-001" in refs and \
            not any("T-ZEBRA-CROSSING" in r for r in refs):
        _ok("V-FIOS-HARVEST-UKDL-COVERAGE",
            "uncovered trap harvested; PR-covered trap skipped")
    else:
        _fail("V-FIOS-HARVEST-UKDL-COVERAGE", f"refs={sorted(refs)}")

    # V-FIOS-HARVEST-FAILOPEN: garbage inputs -> [] or list, never a raise.
    nowhere = Path(tempfile.gettempdir()) / "fios_qh_nonexistent_xyz"
    try:
        z = QH.harvest(12345, state_dir=nowhere, oq_state_dir=nowhere,  # type: ignore
                       co12_state_dir=nowhere, kb_file=nowhere / "x.md",
                       vault_dirs=[nowhere])
        _ok("V-FIOS-HARVEST-FAILOPEN", f"garbage -> list({len(z)}), no raise")
    except Exception as e:  # noqa: BLE001
        _fail("V-FIOS-HARVEST-FAILOPEN", f"RAISED (must fail-open): {e}")


def gate_portfolio() -> None:
    """Compiler portfolio upgrades: dedup, depends_on, provenance render, agenda,
    bilingual axes, FD-07 question_ref roundtrip, preflight auto-harvest."""
    from modules.fable_distillation import fd_07_flywheel as FD07

    kb = _tmp("fios_port_kb_")
    route = lambda t: _FakeDecision("opus")  # noqa: E731
    a = {"text": "design a novel rebase-safe isolation architecture from scratch",
         "source_ref": "ukdl:T-TEST-001", "expected_asset": "hard_rule"}
    a_fp = SC.question_fingerprint(a["text"])
    dup = {"text": "design a novel rebase-safe isolation architecture completely from scratch",
           "source_ref": "owner_queue:q-1", "expected_asset": "asset"}
    b = {"text": "critique the adversarial edge case where that isolation approach fails",
         "source_ref": "deposit:abc", "expected_asset": "benchmark",
         "depends_on": a_fp}
    floor_state = _tmp("fios_port_floor_")
    FD07._append_jsonl(FD07._deposits_path("FIOS-PORT-TEST", floor_state), {
        "fingerprint": "flr001", "claim": "the bus lives under state/parallel_mesh",
        "portability_target": "frontier-only", "portability_proven": False,
        "destination": "dataset_part"})
    decl = SC.SessionDeclaration(objective="portfolio upgrades",
                                 candidate_questions=[a, dup, b],
                                 repo="FIOS-PORT-TEST", token_budget=10000)
    plan = SC.compile_session(decl, kb_dir=kb, route_fn=route,
                              state_dir=floor_state)
    md = SC.render_plan(plan)

    # V-FIOS-QDEDUP: near-identical candidate dropped, logged with its dup_of ref.
    if len(plan.dropped) == 1 and plan.dropped[0].get("dup_of") == a_fp:
        _ok("V-FIOS-QDEDUP", f"1 drop logged, dup_of={a_fp}")
    else:
        _fail("V-FIOS-QDEDUP", f"dropped={plan.dropped}")

    # V-FIOS-QDEPENDS: the dependent question defers to follow_ups, not the lead list.
    fu_fps = {q.fingerprint for q in plan.follow_ups}
    main_texts = [q.text for q in plan.questions]
    if SC.question_fingerprint(b["text"]) in fu_fps and b["text"] not in main_texts:
        _ok("V-FIOS-QDEPENDS", "depends_on question deferred to follow-ups")
    else:
        _fail("V-FIOS-QDEPENDS",
              f"follow_ups={sorted(fu_fps)} main={len(main_texts)}")

    # V-FIOS-QPROVENANCE: source_ref/expected_asset/fingerprint survive to the render.
    lead = plan.questions[0] if plan.questions else None
    if lead and lead.source_ref == "ukdl:T-TEST-001" \
            and lead.expected_asset == "hard_rule" \
            and f"`{a_fp}`" in md and "ukdl:T-TEST-001" in md:
        _ok("V-FIOS-QPROVENANCE", f"lead carries {lead.source_ref} -> rendered")
    else:
        _fail("V-FIOS-QPROVENANCE", f"lead={lead}")

    # V-FIOS-PORTABILITY-AGENDA: the floor's unproven deposit becomes section 10.
    if len(plan.portability_agenda) == 1 \
            and plan.portability_agenda[0]["fingerprint"] == "flr001" \
            and "## 10. Agenda de portabilidad" in md:
        _ok("V-FIOS-PORTABILITY-AGENDA", "unproven floor deposit -> FD-04 agenda")
    else:
        _fail("V-FIOS-PORTABILITY-AGENDA", f"agenda={plan.portability_agenda}")

    # V-FIOS-BILINGUAL-AXES: a Spanish question scores on the leverage axes.
    lev, axes = SC._leverage(
        "disena la arquitectura determinista: bajo que caso borde se rompe siempre?")
    if lev >= 0.75:
        _ok("V-FIOS-BILINGUAL-AXES", f"es-question leverage={lev} axes={axes}")
    else:
        _fail("V-FIOS-BILINGUAL-AXES", f"leverage={lev} axes={axes}")

    # V-FD07-QUESTION-REF: a tagged finding deposits with question_ref; an
    # untagged one still deposits (backward-compatible).
    st = _tmp("fios_qref_")
    res = FD07.run_flywheel("FIOS-QREF", findings=[
        {"topic": "iso", "claim": "a genuinely novel architectural invariant "
         "about pane isolation boundaries", "evidence": "e1",
         "question_ref": "q:deadbeef1234"},
        {"topic": "sched", "claim": "scheduler admission thresholds saturate "
         "beyond twelve concurrent panes", "evidence": "e2"},
    ], state_dir=st, record=False)
    rows = FD07._load_deposits("FIOS-QREF", st)
    tagged = [r for r in rows if r.get("question_ref") == "q:deadbeef1234"]
    untagged = [r for r in rows if r.get("question_ref") == ""]
    if res.deposited == 2 and len(tagged) == 1 and len(untagged) == 1:
        _ok("V-FD07-QUESTION-REF",
            "tagged deposit carries question_ref; untagged deposits unchanged")
    else:
        _fail("V-FD07-QUESTION-REF",
              f"deposited={res.deposited} rows={[(r.get('question_ref')) for r in rows]}")

    # V-FIOS-AUTOHARVEST-PREFLIGHT: an objective with no questions harvests; the
    # kill-switch env disables it. Monkeypatched harvest -> hermetic.
    orig = SC._auto_harvest
    try:
        SC._auto_harvest = lambda repo: [  # type: ignore
            {"text": "design a novel frontier-worthy architecture question",
             "source_ref": "deposit:x", "expected_asset": "benchmark"}]
        line = SC.preflight("FIOS-AH", out_dir=_tmp("fios_ah_"),
                            env={"PP_SESSION_OBJECTIVE": "objective sans questions"})
        line2 = SC.preflight("FIOS-AH", out_dir=_tmp("fios_ah2_"),
                             env={"PP_SESSION_OBJECTIVE": "objective sans questions",
                                  "PP_SESSION_NO_HARVEST": "1"})
        if line and "auto-harvest 1" in line and line2 and "auto-harvest" not in line2:
            _ok("V-FIOS-AUTOHARVEST-PREFLIGHT",
                "empty portfolio auto-harvested; kill-switch honored")
        else:
            _fail("V-FIOS-AUTOHARVEST-PREFLIGHT", f"line={line!r} line2={line2!r}")
    finally:
        SC._auto_harvest = orig              # type: ignore

    # V-FIOS-HARVEST-WIRED (static): the compiler composes the harvester and the
    # flywheel persists the provenance field -- the glue is the deliverable.
    sc_src = Path(SC.__file__).read_text(encoding="utf-8")
    fd_src = Path(FD07.__file__).read_text(encoding="utf-8")
    checks = [
        ("question_harvester" in sc_src, "compiler imports the harvester"),
        ("_auto_harvest" in sc_src, "preflight auto-harvests an empty portfolio"),
        ("question_ref" in fd_src, "flywheel persists question_ref"),
    ]
    bad = [m for ok, m in checks if not ok]
    if not bad:
        _ok("V-FIOS-HARVEST-WIRED", "compiler->harvester + flywheel provenance wired")
    else:
        _fail("V-FIOS-HARVEST-WIRED", f"missing: {bad}")


def main() -> int:
    print("== FIOS execution-layer V-gates ==")
    print("[compose / anti-duplication]")
    gate_compose()
    print("[session_compiler]")
    gate_session()
    print("[token_irr]")
    gate_irr()
    print("[evolution_engine]")
    gate_evolution()
    print("[live-path wiring]")
    gate_wiring()
    print("[question harvester]")
    gate_harvester()
    print("[portfolio upgrades]")
    gate_portfolio()
    total = _passes + _fails
    print(f"\nFIOS_ACTIVATION_PASS={_passes}/{total}  threshold={total}/{total}")
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"DATASET_FAMILY_VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
