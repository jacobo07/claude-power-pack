#!/usr/bin/env python3
"""V-gates for modules/capability_runtime (CPP-APIR Option A).

Proves the three modules do what the audit authorized: a contract that
enforces four HR-APA rules, an applicability engine whose blocking verdicts
are gates rather than score thresholds, and a derivative registry that
refuses a rename-only specialization.

Run: python tools/test_capability_runtime.py    (exit 0 = all gates pass)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, Cost, FailureRisk, Maturity, Risk,
    load_contracts, save_contract,
)
from modules.capability_runtime.applicability import (  # noqa: E402
    MissionContext, Verdict, compile_stack, evaluate,
)
from modules.capability_runtime.derivatives import (  # noqa: E402
    derive, is_stale, lineage, save_derivative, load_derivatives,
)

_passes, _fails = 0, 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _expect_raises(gate: str, rule: str, fn) -> None:
    try:
        fn()
    except ContractError as exc:
        if rule in str(exc):
            _ok(gate, f"rejected with {rule}")
        else:
            _fail(gate, f"raised, but not {rule}: {exc}")
    except Exception as exc:  # noqa: BLE001
        _fail(gate, f"wrong exception type: {type(exc).__name__}: {exc}")
    else:
        _fail(gate, f"accepted an input that violates {rule}")


def _c(**kw) -> CapabilityContract:
    base = dict(id="c", name="C", owner="o", triggers=["t"], consumers=["x"])
    base.update(kw)
    return CapabilityContract(**base)


# --- contract validation -----------------------------------------------------
def test_contract_rules() -> None:
    print("\n[contract] executable HR-APA rules")
    _expect_raises("V-CAPRT-HR006-TRIGGER", "HR-APA-006",
                   lambda: _c(triggers=[]))
    _expect_raises("V-CAPRT-HR006-CONSUMER", "HR-APA-006",
                   lambda: _c(consumers=[]))
    _expect_raises("V-CAPRT-HR018-OWNER", "HR-APA-018",
                   lambda: _c(owner="   "))
    _expect_raises("V-CAPRT-HR009-REVERSIBLE", "HR-APA-009",
                   lambda: _c(write_surfaces=["vault/x"], rollback="", kill_switch=""))

    c = _c(write_surfaces=["vault/x"], rollback="git revert", kill_switch="CAP_OFF=1")
    _ok("V-CAPRT-HR009-SATISFIED",
        f"write surface accepted with rollback+kill_switch ({c.id})")

    esc = _c(risk_class=Risk.ARCHITECTURE_CHANGING)
    if esc.escalates and not _c().escalates:
        _ok("V-CAPRT-HR010-ESCALATES",
            "architecture_changing escalates; reversible does not")
    else:
        _fail("V-CAPRT-HR010-ESCALATES", "escalation flag is not risk-sensitive")

    if CapabilityContract(id="s", name="S", owner="o", triggers=["t"],
                          consumers=["x"], risk_class="local",
                          maturity="proven").risk_class is Risk.LOCAL:
        _ok("V-CAPRT-COERCE", "plain strings from JSON coerce to enums")
    else:
        _fail("V-CAPRT-COERCE", "string coercion did not produce an enum")


# --- applicability -----------------------------------------------------------
ARCH = _c(id="arch_truth", name="Architectural Reality", owner="setup_os",
          triggers=["architecture", "refactor"], anti_triggers=["typo"],
          consumers=["sdd_os"], scope=["architecture reconstruction"],
          non_scope=["model selection"], failure_risk_if_omitted=FailureRisk.CRITICAL,
          expected_leverage=Cost.HIGH, maturity=Maturity.MATURE,
          activation_cost=Cost.MEDIUM, context_cost=Cost.LOW,
          operational_cost=Cost.LOW, risk_class=Risk.ARCHITECTURE_CHANGING,
          version="1.0.0")

LINT = _c(id="lint_pass", name="Lint", owner="uqf", triggers=["lint"],
          consumers=["done_gate"], failure_risk_if_omitted=FailureRisk.NONE,
          expected_leverage=Cost.LOW, maturity=Maturity.EXPERIMENTAL,
          activation_cost=Cost.HIGH, context_cost=Cost.HIGH,
          operational_cost=Cost.HIGH)

K8S = _c(id="k8s", name="K8s", owner="deployment", triggers=["kubernetes"],
         consumers=["deployment"], failure_risk_if_omitted=FailureRisk.NONE,
         expected_leverage=Cost.LOW, maturity=Maturity.EXPERIMENTAL,
         activation_cost=Cost.HIGH, context_cost=Cost.HIGH,
         operational_cost=Cost.HIGH)


def _verdict(c, **ctx_kw) -> Verdict:
    return evaluate(c, MissionContext(**ctx_kw)).verdict


def test_gates() -> None:
    print("\n[applicability] blocking gates precede scoring")
    cases = [
        ("V-CAPRT-GATE-ANTITRIGGER", Verdict.NOT_APPLICABLE,
         dict(description="fix a typo in the architecture docs")),
        ("V-CAPRT-GATE-OWNER", Verdict.BLOCKED_BY_UNRESOLVED_OWNER,
         dict(description="refactor the architecture",
              resolved_owners=["someone_else"])),
        ("V-CAPRT-GATE-DUPLICATE", Verdict.REJECTED_AS_DUPLICATE,
         dict(description="refactor the architecture",
              held_scopes=["architecture reconstruction"])),
    ]
    for gate, want, kw in cases:
        got = _verdict(ARCH, **kw)
        (_ok(gate, f"-> {got.value}") if got is want
         else _fail(gate, f"expected {want.value}, got {got.value}"))

    need_ev = _c(id="hw", name="HW", owner="o", triggers=["boot"],
                 consumers=["x"], required_evidence=["hardware_boot_log"])
    got = _verdict(need_ev, description="boot the device")
    (_ok("V-CAPRT-GATE-EVIDENCE", f"-> {got.value}")
     if got is Verdict.BLOCKED_BY_MISSING_EVIDENCE
     else _fail("V-CAPRT-GATE-EVIDENCE", f"got {got.value}"))

    got = _verdict(need_ev, description="boot the device",
                   available_evidence=["hardware_boot_log"])
    (_ok("V-CAPRT-GATE-EVIDENCE-MET", f"evidence present -> {got.value}")
     if got is not Verdict.BLOCKED_BY_MISSING_EVIDENCE
     else _fail("V-CAPRT-GATE-EVIDENCE-MET", "still blocked with evidence present"))

    rt = _c(id="wii", name="Wii", owner="o", triggers=["build"],
            consumers=["x"], compatible_runtimes=["powerpc"])
    got = _verdict(rt, description="build it", runtime="browser")
    (_ok("V-CAPRT-GATE-INSUFFICIENT", f"-> {got.value}")
     if got is Verdict.CAPABILITY_INSUFFICIENT
     else _fail("V-CAPRT-GATE-INSUFFICIENT", f"got {got.value}"))

    pre = _c(id="p", name="P", owner="o", triggers=["ship"], consumers=["x"],
             prerequisites=["tests_green"])
    got = _verdict(pre, description="ship it")
    (_ok("V-CAPRT-GATE-PREREQ", f"-> {got.value}")
     if got is Verdict.CAPABILITY_INSUFFICIENT
     else _fail("V-CAPRT-GATE-PREREQ", f"got {got.value}"))

    # A blocked capability that would otherwise score MANDATORY stays blocked:
    # the gate is not a score threshold.
    a = evaluate(ARCH, MissionContext(description="refactor the architecture",
                                      held_scopes=["architecture reconstruction"]))
    (_ok("V-CAPRT-GATE-BEATS-SCORE", f"score={a.score} yet {a.verdict.value}")
     if a.blocked and a.score == 0.0
     else _fail("V-CAPRT-GATE-BEATS-SCORE", "a high scorer escaped its gate"))


def test_scoring() -> None:
    print("\n[applicability] scored verdicts")
    checks = [
        ("V-CAPRT-VERDICT-MANDATORY", ARCH, "refactor the architecture",
         Verdict.MANDATORY),
        ("V-CAPRT-VERDICT-ONTRIGGER", LINT, "lint the file",
         Verdict.AVAILABLE_ON_TRIGGER),
        ("V-CAPRT-VERDICT-NOTAPPLICABLE", K8S, "lint the file",
         Verdict.NOT_APPLICABLE),
    ]
    for gate, c, mission, want in checks:
        a = evaluate(c, MissionContext(description=mission))
        (_ok(gate, f"{c.id} -> {a.verdict.value} (score={a.score})")
         if a.verdict is want
         else _fail(gate, f"{c.id} expected {want.value}, got "
                          f"{a.verdict.value} (score={a.score})"))


def test_stack() -> None:
    print("\n[applicability] HR-APA-005 minimum sufficient activation")
    stack = compile_stack(
        MissionContext(description="refactor the architecture and lint"),
        contracts=[ARCH, LINT, K8S])
    if stack["activate"] == ["arch_truth"] and stack["dormant"] == ["lint_pass"]:
        _ok("V-CAPRT-HR005-MINIMAL",
            f"activate={stack['activate']} dormant={stack['dormant']} "
            "(HR-APA-014: dormant is reported, not loaded)")
    else:
        _fail("V-CAPRT-HR005-MINIMAL", f"unexpected stack: {stack['activate']} / "
                                       f"{stack['dormant']}")
    if stack["escalate"] == ["arch_truth"]:
        _ok("V-CAPRT-HR010-SURFACED", "architecture-changing activation escalates")
    else:
        _fail("V-CAPRT-HR010-SURFACED", f"escalate={stack['escalate']}")


# --- derivatives -------------------------------------------------------------
def test_derivatives() -> None:
    print("\n[derivatives] HR-APA-016 / HR-APA-017 enforcement")
    _expect_raises("V-CAPRT-HR016-RENAME-ONLY", "HR-APA-016",
                   lambda: derive(ARCH, "proj_a", {"name": "Renamed Reality"}))

    child, rec = derive(ARCH, "proj_a",
                        {"required_evidence": ["boot_log"],
                         "triggers": ["architecture", "refactor", "lifecycle"]},
                        upgrade_path="re-derive on kernel minor bump")
    if child.parent == "arch_truth" and rec.overridden and child.id.endswith("@proj_a"):
        _ok("V-CAPRT-HR004-DERIVATIVE",
            f"{child.id} parent={child.parent} overridden={rec.overridden}")
    else:
        _fail("V-CAPRT-HR004-DERIVATIVE", f"weak record: {rec.to_dict()}")

    _expect_raises(
        "V-CAPRT-HR017-WEAKEN", "HR-APA-017",
        lambda: derive(ARCH, "proj_b", {"non_scope": []}))

    _, rec_ok = derive(ARCH, "proj_b", {"non_scope": []},
                       approved_override="Owner")
    (_ok("V-CAPRT-HR017-APPROVED", f"approved by {rec_ok.approved_override!r}")
     if rec_ok.approved_override == "Owner"
     else _fail("V-CAPRT-HR017-APPROVED", "override not recorded"))

    moved = _c(id="arch_truth", name="Architectural Reality", owner="setup_os",
               triggers=["architecture"], consumers=["sdd_os"], version="2.0.0")
    if is_stale(rec, moved) and not is_stale(rec, ARCH):
        _ok("V-CAPRT-STALE", "stale vs parent 2.0.0, current vs 1.0.0")
    else:
        _fail("V-CAPRT-STALE", "staleness is not version-sensitive")

    chain = lineage(child.id, records=[rec])
    (_ok("V-CAPRT-LINEAGE", " -> ".join(chain))
     if chain == [child.id, "arch_truth"]
     else _fail("V-CAPRT-LINEAGE", f"chain={chain}"))


def test_persistence_and_failopen() -> None:
    print("\n[io] round-trip and fail-open")
    with tempfile.TemporaryDirectory() as td:
        cdir = Path(td) / "contracts"
        save_contract(ARCH, cdir)
        (Path(cdir) / "broken.json").write_text("{not json", encoding="utf-8")
        loaded = load_contracts(cdir)
        (_ok("V-CAPRT-ROUNDTRIP",
             f"{len(loaded)} valid contract(s) loaded; malformed file skipped")
         if len(loaded) == 1 and loaded[0].id == "arch_truth"
         else _fail("V-CAPRT-ROUNDTRIP", f"loaded={[c.id for c in loaded]}"))

        ddir = Path(td) / "derivatives"
        _, rec = derive(ARCH, "proj_c", {"required_evidence": ["trace"]})
        save_derivative(rec, ddir)
        (_ok("V-CAPRT-DERIV-ROUNDTRIP", f"{load_derivatives(ddir)[0].child_id}")
         if len(load_derivatives(ddir)) == 1
         else _fail("V-CAPRT-DERIV-ROUNDTRIP", "derivative did not round-trip"))

    missing = Path(td) / "gone"
    if load_contracts(missing) == [] and load_derivatives(missing) == []:
        _ok("V-CAPRT-FAILOPEN", "absent directory yields [], never raises")
    else:
        _fail("V-CAPRT-FAILOPEN", "absent directory did not fail open")


def main() -> int:
    print("capability_runtime V-gates")
    for fn in (test_contract_rules, test_gates, test_scoring, test_stack,
               test_derivatives, test_persistence_and_failopen):
        fn()
    total = _passes + _fails
    print(f"\nCAPABILITY_RUNTIME_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
