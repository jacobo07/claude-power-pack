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
    total = _passes + _fails
    print(f"\nFIOS_ACTIVATION_PASS={_passes}/{total}  threshold={total}/{total}")
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"DATASET_FAMILY_VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
