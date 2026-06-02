#!/usr/bin/env python3
"""PP Full Health Report -- fast operational smoke of the 7 governance engines.

Distinct from ``tools/verify_spp.py`` (the heavy 23-row subprocess
umbrella) and ``tools/verify_integration_wiring.py`` (the hook
activation gate). This is a sub-second, in-process check that each
governance ENGINE answers correctly on a canonical input -- the
operational heartbeat an Owner runs right after registering hooks or
before a long session.

Each engine is exercised through its real public API on a known input
with a defensible expected outcome (no synthesised composite score):

  1. Secret Firewall   scan_text() flags a clearly-fake real-shape key
  2. Cascade Prevention detect('deploy', tests_passed=False) -> block
  3. Output Contracts   is_done('code', {}) rejects an empty context
  4. One-Shot Compiler  compile_contract('...', 'M') has a real budget
  5. Cost Collapse      route('format imports') -> NANO
  6. Backlog Autopilot  what_now() recommends the only actionable P0
  7. CPC-OS Registry    PaneRegistry.load() returns a usable registry

Exit 0 iff all 7 engines operational; 1 otherwise.

Usage:
  python tools/pp_health_report.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))


def _secret_firewall() -> tuple[bool, str]:
    from modules.secret_firewall.detector import scan_text, is_critical
    # Clearly-fake but real-shape key per HR-SECRET-005. Built by
    # concatenation so the literal never appears contiguously in source
    # (avoids self-tripping the Secret Firewall on this very file).
    fake = "sk-ant-" + "A" * 50
    hits = scan_text(fake)
    ok = is_critical(hits)
    return ok, f"{len(hits)} hit(s), critical={ok} on synthetic key"


def _cascade_prevention() -> tuple[bool, str]:
    from modules.cascade_prevention.engine import detect
    hits = detect("deploy", {"is_deploy": True, "tests_passed": False})
    blockers = [h for h in hits if getattr(h, "should_block", False)]
    return bool(blockers), (
        f"{len(blockers)} blocker(s) on deploy with tests_passed=False"
    )


def _output_contracts() -> tuple[bool, str]:
    from modules.output_contracts.validator import is_done, get_contract
    if get_contract("code") is None:
        return False, "code contract file missing"
    done, oqs = is_done("code", {})  # empty context must be rejected
    return (not done), f"empty context rejected (done={done}, oqs={oqs})"


def _one_shot() -> tuple[bool, str]:
    from modules.one_shot.compiler import compile_contract
    contract = compile_contract("Fix a defect", "M")
    return contract.budget_usd > 0, f"M-size budget_usd={contract.budget_usd}"


def _cost_collapse() -> tuple[bool, str]:
    from modules.cost_collapse.router import route, RouteClass
    result = route("format imports")
    ok = result.route_class == RouteClass.NANO
    return ok, f"'format imports' -> {result.route_class.name}"


def _backlog_autopilot() -> tuple[bool, str]:
    from modules.backlog_autopilot.engine import BacklogItem, what_now
    item = BacklogItem("A", "Fix critical issue", 0, "S", "Critical", ())
    result = what_now([item])
    rec_id = result.recommended.id if result.recommended else None
    return rec_id == "A", f"recommended={rec_id}"


def _cpc_os() -> tuple[bool, str]:
    from modules.cpc_os.registry import PaneRegistry
    registry = PaneRegistry.load()
    active = len(registry.get_active_panes())
    return registry is not None, f"registry loaded, {active} active pane(s)"


CHECKS = [
    ("Secret Firewall", _secret_firewall),
    ("Cascade Prevention", _cascade_prevention),
    ("Output Contracts", _output_contracts),
    ("One-Shot Compiler", _one_shot),
    ("Cost Collapse", _cost_collapse),
    ("Backlog Autopilot", _backlog_autopilot),
    ("CPC-OS Registry", _cpc_os),
]


def main() -> int:
    print("=" * 60)
    print("PP HEALTH REPORT -- 7 governance engines")
    print(f"  PP root: {PP}")
    print("=" * 60)
    ok_count = 0
    for name, fn in CHECKS:
        try:
            ok, evidence = fn()
        except Exception as exc:  # noqa: BLE001 -- report, never crash
            ok, evidence = False, f"{type(exc).__name__}: {exc}"
        if ok:
            ok_count += 1
        tag = "OK  " if ok else "FAIL"
        print(f"  [{tag}] {name:<22s} {evidence}")
    print("=" * 60)
    print(f"  HEALTH: {ok_count}/{len(CHECKS)} engines operational")
    print("=" * 60)
    return 0 if ok_count == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
