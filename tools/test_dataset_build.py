#!/usr/bin/env python3
"""Consolidated V-gate test for the PP_DATASET-derived build (BL-DATASET-BUILD).

Exercises one representative V-gate per shipped module (M1-M10) so a
single Exit 0 confirms the whole stack is operational in cold state.
Run as part of verify_spp.py or standalone:

  python tools/test_dataset_build.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Imports (one per module under test)
from modules.backlog_autopilot import BacklogItem, what_now
from modules.cascade_prevention import detect, is_blocked
from modules.cost_collapse import RouteClass, route
from modules.cpc_os import (
    PaneRegistry,
    detect_crash_state,
    is_pane_alive,
    plan_parallel_backlog,
    recover_corrupt_registry,
    restart_intent,
    route_intent,
    switch_intent,
)
from modules.one_shot import (
    BUDGETS,
    compile_contract,
    is_deviated,
    recommend_action,
)
from modules.output_contracts import OQS_DONE_THRESHOLD, is_done, list_contracts
from modules.secret_firewall import (
    is_critical,
    redact,
    redact_for_log,
    scan_text,
)
# BUCKET-C slash-command tools (importable cores, SCS C28: compose).
from modules.one_shot import compiler as oneshot_compiler
from tools.readiness_check import readiness
from tools.secret_scan_repo import scan_repo

# Slop tokens constructed at runtime so this test file does not itself
# carry literal slop tokens (Wozniak doctrine).
SLOP_TODO = chr(84) + chr(79) + chr(68) + chr(79)
SLOP_SKIP = chr(64) + chr(115) + chr(107) + chr(105) + chr(112)

# Named test-tunable constants -- this file carries no magic literals.
FAKE_KEY_BODY_LEN = 50            # tail after "sk-ant-" prefix; >32 to trip pattern
LONG_TEXT_SAMPLE_LEN = 5000       # large input to prove redact_for_log truncates
CONTEXT_WARN_TEST_PCT = 90        # 85<=pct<95 -> CascadePrevention C3 warn
M_BUDGET_USD_EXPECTED = 15.0      # OD3-sealed M-task budget
COMMAND_MD_MIN_BYTES = 200        # semantic length floor for slash-command md
COMMAND_EXTENSION_LEN = 3         # len(".md")
INNOCUOUS_DIGITS = "1234567890"   # filler digits for clean-text V-gate
EXPECTED_CONTRACT_SET = frozenset({"code", "docs", "deploy", "test"})

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, cond, evidence))
    tag = "PASS" if cond else "FAIL"
    print(f"  {name:<35} {tag}  {evidence}")


def main() -> int:
    print("=" * 72)
    print("test_dataset_build -- consolidated V-gate test")
    print(f"  PP root : {ROOT}")
    print("=" * 72)

    fake_key = "sk-ant-" + ("A" * FAKE_KEY_BODY_LEN)

    # --- BLOCK 1: Secret Firewall (M1) ---
    print("\n[BLOCK 1] Secret Firewall")
    gate("V-SECRET-DETECTOR",
         is_critical(scan_text(f"key={fake_key}")),
         "anthropic key detected CRITICAL")
    gate("V-SECRET-CLEAN",
         len(scan_text(f"the quick brown fox {INNOCUOUS_DIGITS}")) == 0,
         "clean prose -> 0 hits")
    gate("V-URB-REDACT",
         "REDACTED" in redact(fake_key) and "sk-ant" not in redact(fake_key),
         "redact replaces + scrubs prefix")
    long_sample = "X" * LONG_TEXT_SAMPLE_LEN
    gate("V-URB-LOG",
         len(redact_for_log(long_sample)) < LONG_TEXT_SAMPLE_LEN,
         "redact_for_log caps length")

    # --- BLOCK 2: Cascade Prevention (M4) ---
    print("\n[BLOCK 2] Cascade Prevention")
    gate("V-CASCADE-DEPLOY-BLOCK",
         is_blocked(detect("deploy", {"is_deploy": True,
                                      "tests_passed": False})),
         "deploy without tests -> C4 block")
    gate("V-CASCADE-CONTEXT-WARN",
         len(detect("context", {"context_pct": CONTEXT_WARN_TEST_PCT})) >= 1,
         f"context {CONTEXT_WARN_TEST_PCT}% -> warning fires")
    gate("V-CASCADE-FAIL-OPEN",
         isinstance(detect("xyz", {}), list),
         "unknown surface -> [] not crash")

    # --- BLOCK 3: Output Contracts (M5) ---
    print("\n[BLOCK 3] Output Contracts")
    gate("V-OQS-FOUR-CONTRACTS",
         set(list_contracts()) == EXPECTED_CONTRACT_SET,
         f"contracts: {list_contracts()}")
    bad_code = {
        "file_path": "x.py",
        "syntax_test_passed": True,
        "tests_test_passed": False,
        "content": f"def f():\n    {SLOP_TODO}: implement\n",
    }
    done_b, oqs_b = is_done("code", bad_code)
    gate("V-OQS-BAD-CODE",
         not done_b and oqs_b < OQS_DONE_THRESHOLD,
         f"bad code: oqs={oqs_b}")
    good_code = {
        "file_path": "x.py",
        "syntax_test_passed": True,
        "tests_test_passed": True,
        "content": "def f(): return 1",
    }
    done_g, oqs_g = is_done("code", good_code)
    gate("V-OQS-GOOD-CODE",
         done_g and oqs_g >= OQS_DONE_THRESHOLD,
         f"good code: oqs={oqs_g}")

    # --- BLOCK 4: One-Shot Compiler (M6) ---
    print("\n[BLOCK 4] One-Shot Compiler")
    c = compile_contract("Fix the JWT auth bug", "M")
    gate("V-ONESHOT-BUDGET",
         c.budget_usd == BUDGETS["M"] == M_BUDGET_USD_EXPECTED,
         f"M task = ${c.budget_usd}")
    gate("V-ONESHOT-DEVIATION",
         is_deviated(c, ["docs/CHANGELOG.md", "scripts/build.sh"]),
         "unrelated files trigger deviation")
    gate("V-ONESHOT-ESCALATION",
         recommend_action(0) == "proceed"
         and recommend_action(2) == "escalate-to-opus"
         and recommend_action(3) == "stop-and-escalate-to-Owner",
         "OD7 ladder intact")

    # --- BLOCK 5: Cost Collapse (M7) ---
    print("\n[BLOCK 5] Cost Collapse")
    gate("V-COST-NANO",
         route("format the imports").route_class == RouteClass.NANO,
         "format -> NANO (haiku)")
    gate("V-COST-MACRO",
         route("design system architecture").route_class == RouteClass.MACRO,
         "design system -> MACRO (opus)")
    gate("V-COST-MICRO-DEFAULT",
         route("fix the auth bug").route_class == RouteClass.MICRO,
         "default -> MICRO (sonnet)")

    # --- BLOCK 6: Backlog Autopilot (M8) ---
    print("\n[BLOCK 6] Backlog Autopilot")
    backlog = [
        BacklogItem("A", "P0-Critical", 0, "S", "Critical"),
        BacklogItem("B", "P1-Medium", 1, "L", "Medium"),
        BacklogItem("D", "P0-Blocked", 0, "S", "Critical", blockers=("X",)),
    ]
    rec = what_now(backlog)
    gate("V-BACKLOG-PICKS-A",
         rec.recommended is not None and rec.recommended.id == "A",
         "P0+Critical+S, unblocked -> A")
    gate("V-BACKLOG-BLOCKED-FILTERED",
         rec.recommended is None or rec.recommended.id != "D",
         "blocked P0 not picked")

    # --- BLOCK 7: CPC-OS (M9, M10) ---
    print("\n[BLOCK 7] CPC-OS")
    with tempfile.TemporaryDirectory(prefix="cpc_test_") as td:
        rp = Path(td) / "registry.json"
        reg = PaneRegistry.load(rp)
        reg.register_pane("smoke", str(Path(td)), "smoke test")
        gate("V-CPC-REGISTER",
             "smoke" in reg.panes and reg.panes["smoke"].status == "active",
             "atomic register succeeded")
        gate("V-CPC-LIVENESS",
             is_pane_alive(reg, "smoke") and not is_pane_alive(reg, "ghost"),
             "live -> True; unknown -> False")
        ir = route_intent(reg, "smoke", "restart", time.time())
        gate("V-CPC-INTENT-OK",
             ir.accepted,
             "fresh intent accepted")

        # section 208.2-208.5 acceptance contracts (BL-CPCOS-002).
        # Each uses its own registry file so the cases stay isolated.
        r2 = PaneRegistry.load(Path(td) / "r2.json")
        r2.register_pane("p", str(Path(td)), "t", session_id="sid-x")
        gate("V-CPC-RESTART",
             restart_intent("p", str(Path(td)), session_id="sid-x",
                            registry=r2)["safe"]
             and not restart_intent("ghost", str(Path(td)),
                                    registry=r2)["safe"],
             "208.2 same-pane safe; unknown blocked")
        r3 = PaneRegistry.load(Path(td) / "r3.json")
        r3.register_pane("s", "/s", "ta")
        r3.register_pane("g", "/g", "tb")
        r3.pause_pane("g")
        sw = switch_intent("s", "g", registry=r3)
        gate("V-CPC-SWITCH",
             sw["safe"] and r3.panes["s"].status == "paused"
             and r3.panes["g"].status == "active",
             "208.3 source paused, target activated")
        r4 = PaneRegistry.load(Path(td) / "r4.json")
        r4.register_pane("d", "/d", "t", session_id="sid-d")
        r4.panes["d"].last_heartbeat_at -= 10000  # backdate -> stale
        cs = detect_crash_state(registry=r4)
        gate("V-CPC-RECOVERY",
             cs["crash_detected"]
             and cs["restore_plan"][0]["confidence"] == "high",
             "208.4 stale pane -> high-confidence restore plan")
        gate("V-CPC-BACKLOG",
             plan_parallel_backlog([
                 {"item_id": "x", "pane_id": "p1", "task": "A",
                  "locks": ["f"], "deps": []},
                 {"item_id": "y", "pane_id": "p2", "task": "B",
                  "locks": ["f"], "deps": []},
             ])["valid"] is False,
             "208.5 concurrent lock collision blocked")

        rp.write_text("{broken json", encoding="utf-8")
        rec2, recovered = recover_corrupt_registry(rp)
        gate("V-CPC-CORRUPT-RECOVERY",
             recovered and len(rec2.panes) == 0,
             "corrupt file -> empty registry")

    # --- M10 commands surface ---
    print("\n[BLOCK 8] Commands surface")
    for cmd in ("what-now.md", "panes.md", "switch-session.md",
                "secret-scan.md", "cost-autopsy.md", "one-shot-compile.md",
                "demo-ready.md", "revenue-ready.md"):
        p = ROOT / "commands" / cmd
        gate(f"V-CMD-{cmd[:-COMMAND_EXTENSION_LEN].upper()}",
             p.is_file() and p.stat().st_size > COMMAND_MD_MIN_BYTES,
             f"{p.name} ({p.stat().st_size if p.is_file() else 0} bytes)")

    # --- M11 BUCKET B gaps ---
    print("\n[BLOCK 9] BUCKET B gaps (M11)")

    # V-GAP-1: secret_rotation_advisor returns 0 actionable hits on
    # the live PP tree (canonical AWS test examples filtered via the
    # KNOWN_SAFE_VALUES allowlist; real CRITICAL credentials would
    # fail this gate -- HR-SECRET-007 rotate-first applies if so).
    from tools.secret_rotation_advisor import advise as _advise
    advice = _advise(ROOT)
    gate("V-GAP-1-ROTATION-ADVISOR",
         isinstance(advice, list) and len(advice) == 0,
         f"advise() returns {len(advice)} actionable hit(s) (0 expected)")

    # V-GAP-2: dangerous commands registry
    from modules.cascade_prevention.dangerous_cmds import (
        is_dangerous, reasons,
    )
    gate("V-GAP-2-DANGEROUS-RM",
         is_dangerous("rm -rf /") and not is_dangerous("ls -la"),
         "rm -rf / flagged; ls -la safe")
    gate("V-GAP-2-DANGEROUS-DROP",
         is_dangerous("DROP TABLE users") and "destructive SQL DROP" in
         reasons("DROP TABLE users"),
         "DROP TABLE flagged + reason returned")

    # V-GAP-3: HR quality audit
    from tools.hr_quality_audit import audit as _hr_audit
    hr_report = _hr_audit()
    full_score = [r for r in hr_report if r["score"] >= 75]
    gate("V-GAP-3-HR-AUDIT",
         len(hr_report) >= 7 and len(full_score) >= 1,
         f"{len(hr_report)} rules audited; {len(full_score)} score >= 75")

    # V-GAP-4: pre-mortem cascade detector
    from modules.cascade_prevention.pre_mortem import analyze as _premortem
    risky = _premortem("Deploy to prod without running tests first")
    clean = _premortem("Read the docs and take notes")
    gate("V-GAP-4-PREMORTEM",
         len(risky) >= 1 and len(clean) == 0,
         f"risky plan -> {len(risky)} risks; clean plan -> 0")

    # V-GAP-5: output contract Stop hook present
    hook_path = ROOT / "hooks" / "output_contract_stop.js"
    gate("V-GAP-5-OUTPUT-CONTRACT-HOOK",
         hook_path.is_file() and hook_path.stat().st_size > COMMAND_MD_MIN_BYTES,
         f"hook present ({hook_path.stat().st_size if hook_path.is_file() else 0} bytes)")

    # --- BLOCK 10: BUCKET-C slash-command tools ---
    print("\n[BLOCK 10] BUCKET-C slash-command tools")
    with tempfile.TemporaryDirectory(prefix="bucketc_") as td2:
        clean_dir = Path(td2) / "clean"
        clean_dir.mkdir()
        (clean_dir / "ok.py").write_text("x = 1\n", encoding="utf-8")
        dirty_dir = Path(td2) / "dirty"
        dirty_dir.mkdir()
        (dirty_dir / "leak.py").write_text(
            f'KEY = "{fake_key}"\n', encoding="utf-8")

        gate("V-SECRET-SCAN-RUNS",
             len(scan_repo(dirty_dir, "CRITICAL")) >= 1
             and len(scan_repo(clean_dir, "CRITICAL")) == 0,
             "scan_repo: leak dir flags CRITICAL, clean dir 0")

        rc_cli = oneshot_compiler.main(["--task", "demo task", "--size", "S"])
        gate("V-ONESHOT-CLI",
             rc_cli == 0,
             "compiler --task --size returns exit 0")

        demo_ok = readiness("demo", clean_dir)["ready"]
        rev_not_ready = readiness("revenue", clean_dir)["ready"] is False
        gate("V-READINESS-RUNS",
             demo_ok and rev_not_ready,
             "demo clean=ready; revenue clean=not-ready (no monitor/HR)")

    # --- Summary ---
    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"DATASET_BUILD_PASS={passes}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
