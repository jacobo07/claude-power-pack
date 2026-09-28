"""V-BRIDGE gates: modules/external_assimilation/node_bridge.py + lib/adapters/genesis-suite.js.

Every outcome is driven from a real input, and each outcome is proven distinguishable from
the others (a bridge that answered OK to everything would fail V-BRIDGE-SUBJECT-INVALID).
    python tools/test_genesis_bridge.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

passes = fails = 0


def gate(name: str, cond: bool, evidence: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {name}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {name}: {evidence}")


def main() -> int:
    r = nb.call("contextBudget", "normalize", [5, {"comfortable": 0, "stressed": 10, "critical": 20}],
                package="context-budget")
    gate("V-BRIDGE-OK-CALL", r.ok and r.value == 0.25, f"{r.outcome} {r.value!r}")

    # validateGraph REPORTS {ok:false} (measured); the constructor is what throws on bad input.
    r = nb.call("planning", "createPlanGraph", [{"nodes": "not-a-list"}])
    gate("V-BRIDGE-SUBJECT-INVALID", r.outcome == nb.SUBJECT_INVALID and "bounded array" in r.error,
         f"{r.outcome} {r.error[:80]}")
    r = nb.call("planning", "validateGraph", ["not-a-list"])
    gate("V-BRIDGE-VERDICT-NOT-THROW", r.ok and r.value.get("ok") is False, f"{r.outcome} {r.value!r}"[:120])

    r = nb.call("prompts", "TASK_CONTRACT_KEYS")
    gate("V-BRIDGE-OK-CONSTANT", r.ok and isinstance(r.value, list) and len(r.value) > 0, f"{r.outcome} {r.value!r}"[:120])

    r = nb.call("noSuchModule", "x")
    gate("V-BRIDGE-UNKNOWN-EXPORT", r.outcome == nb.BRIDGE_FAILED, f"{r.outcome} {r.error}")

    r = nb.call("contextBudget", "normalize", [1], package="context-budget", timeout=0.001)
    gate("V-BRIDGE-TIMEOUT", r.outcome == nb.BRIDGE_FAILED and "timeout" in r.error, f"{r.outcome} {r.error}")

    old = os.environ.get("CPP_NODE_EXE")
    try:
        os.environ["CPP_NODE_EXE"] = str(ROOT / "no-such-node.exe")
        r = nb.call("prompts", "LIMITS")
        gate("V-BRIDGE-NO-NODE", r.outcome == nb.BRIDGE_FAILED and "not found" in r.error, f"{r.outcome} {r.error}")
        os.environ["CPP_NODE_EXE"] = sys.executable  # a real process that cannot speak the adapter's JSON
        r = nb.call("prompts", "LIMITS")
        gate("V-BRIDGE-UNREADABLE", r.outcome == nb.UNREADABLE, f"{r.outcome} {r.error}")
    finally:
        if old is None:
            os.environ.pop("CPP_NODE_EXE", None)
        else:
            os.environ["CPP_NODE_EXE"] = old

    # Engine range: the VPS measured v22.22.2 on 2026-09-28, below genesis ^22.23.2.
    probe = ("const {engineOk}=require(process.argv[1]);const R='^22.23.2 || ^24.14.0';"
             "console.log([engineOk(R,'v22.22.2'),engineOk(R,'v22.23.2'),engineOk(R,'v24.15.0'),engineOk(R,'v23.1.0')].join(','))")
    out = subprocess.run([nb.node_exe() or "node", "-e", probe, str(nb.ADAPTER)], capture_output=True, text=True).stdout.strip()
    gate("V-BRIDGE-ENGINE-RANGE", out == "false,true,true,false", f"engineOk(vps,min,host,23) -> {out}")

    print(f"BRIDGE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
