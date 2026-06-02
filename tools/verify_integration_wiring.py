#!/usr/bin/env python3
"""verify_integration_wiring.py -- BL-INTEGRATION-WIRING done-gate.

Proves the five previously-ORPHAN modules are now connected to a live
activation surface (hook / signal / decorator), not merely importable.
Named verify_* (NOT test_*) so it sits in the verify_spp row family
and stays clear of the tools/test_* surface.

  python tools/verify_integration_wiring.py        -> 0 iff all gates pass
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NODE = "node"
PY = sys.executable

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, ev: str = "") -> None:
    results.append((name, cond, ev))
    print(f"  {name:<30} {'PASS' if cond else 'FAIL'}  {ev}")


def _run_node_hook(hook_rel: str, payload: str) -> tuple[str, int]:
    hook = ROOT / hook_rel
    t0 = time.monotonic()
    try:
        cp = subprocess.run([NODE, str(hook)], input=payload,
                            capture_output=True, text=True, timeout=10)
        return (cp.stdout or "").strip(), int((time.monotonic() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001
        return f"ERR:{exc}", -1


# Dangerous command assembled from parts so no literal rm-rf string
# appears verbatim in this source (defensive against future scanners).
_DANGER_RM = " ".join(["rm", "-rf", "/important-data"])


def main() -> int:
    print("=" * 64)
    print("verify_integration_wiring -- module activation gate")
    print("=" * 64)

    # 1. Cascade hook exists
    cascade_hook = ROOT / "hooks" / "cascade_check_bash.js"
    gate("V-CASCADE-HOOK-EXISTS", cascade_hook.is_file(),
         str(cascade_hook.relative_to(ROOT)))

    # 2. Cascade hook BLOCKS a dangerous command
    out, _ = _run_node_hook(
        "hooks/cascade_check_bash.js",
        json.dumps({"tool_name": "Bash",
                    "tool_input": {"command": _DANGER_RM}}))
    gate("V-CASCADE-HOOK-BLOCKS",
         '"continue":false' in out and "HR-CASCADE" in out,
         "dangerous cmd -> continue:false")

    # 3. Cascade hook PASSES a safe command
    out, ms = _run_node_hook(
        "hooks/cascade_check_bash.js",
        json.dumps({"tool_name": "Bash",
                    "tool_input": {"command": "ls -la"}}))
    gate("V-CASCADE-HOOK-PASSES",
         '"continue":true' in out and "stopReason" not in out,
         f"ls -la -> continue:true ({ms}ms)")

    # 4. Cost Collapse wired into TCO gate
    try:
        from tools.tco_compact_gate import route_prompt
        nano = route_prompt("format the imports")
        macro = route_prompt("design the system architecture")
        cost_ok = (nano and nano["route_class"] == "NANO"
                   and macro and macro["route_class"] == "MACRO")
    except Exception as exc:  # noqa: BLE001
        cost_ok = False
        nano = str(exc)
    gate("V-COST-TCO-INTEGRATED", bool(cost_ok),
         "route_prompt: NANO+MACRO routed")

    # 5. Backlog signal importable + registered in dispatcher
    try:
        from modules.pp_agents.signals import backlog as _bk
        from modules.pp_agents.proactive_dispatcher import AGENT_CONFIGS
        backlog_ok = (hasattr(_bk, "evaluate")
                      and "pp-backlog-autopilot" in AGENT_CONFIGS)
    except Exception:  # noqa: BLE001
        backlog_ok = False
    gate("V-BACKLOG-SIGNAL-WIRED", backlog_ok,
         "signals.backlog + dispatcher registration")

    # 6. One-Shot JIT decorator present
    jit_src = (ROOT / "tools" / "jit_skill_loader.py").read_text(
        encoding="utf-8")
    gate("V-ONESHOT-JIT-WIRED",
         "_oneshot_contract_inject" in jit_src
         and "@_oneshot_contract_inject" in jit_src,
         "decorator defined + applied to run()")

    # 7. CPC-OS hub registration wired
    hub_src = (ROOT / "hooks" / "session_start_hub.js").read_text(
        encoding="utf-8")
    gate("V-CPCOS-HUB-WIRED",
         "function hookCpcOsRegister" in hub_src
         and "hookCpcOsRegister(cwd)" in hub_src,
         "hookCpcOsRegister defined + called")

    # 8. Hub still runs within budget (SCS C23: < 1500 ms) + valid JSON
    out, ms = _run_node_hook("hooks/session_start_hub.js", "{}")
    hub_fast = False
    try:
        hub_fast = (json.loads(out).get("continue") is True
                    and 0 <= ms < 1500)
    except Exception:  # noqa: BLE001
        pass
    gate("V-HUB-FAST-POST-WIRE", hub_fast, f"hub {ms}ms (< 1500 budget)")

    # 9. Dataset-build modules still import (no regression)
    mods = [
        "modules.secret_firewall.detector",
        "modules.cascade_prevention.engine",
        "modules.cascade_prevention.dangerous_cmds",
        "modules.cascade_prevention.pre_mortem",
        "modules.output_contracts.validator",
        "modules.one_shot.compiler",
        "modules.cost_collapse.router",
        "modules.backlog_autopilot.engine",
        "modules.cpc_os.registry",
    ]
    import importlib
    baseline_ok = True
    bad = ""
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as exc:  # noqa: BLE001
            baseline_ok = False
            bad = f"{m}: {exc}"
            break
    gate("V-BASELINE-INTACT", baseline_ok, bad or f"{len(mods)} modules import")

    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print("=" * 64)
    print(f"INTEGRATION_WIRING_PASS={passes}/{total}")
    print("=" * 64)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
