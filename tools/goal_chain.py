"""Chain-tick hook for dgl (W3): turn a stopped unit into one atomic succession.

The live chain driver (gsdx_chain.py) is not edited; the tick (vault/programs/dgl/dgl_chain_tick.ps1) writes its last
decision row to a file and calls `goal_chain.py react --row FILE [--plan FILE]`. Only rows whose action is in TRIGGERS
act: `stopped_without_done` (a worker ended without its receipt) and `refuse_envelope` (the budget halt). A plan
file carries the succession arguments and the process-probe evidence (old_sid, dead, measured); without a plan the
hook does nothing, so an armed tick that has no plan can never spend or claim. Wiring beyond the tick is W4.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal_succession as gs  # noqa: E402

TRIGGERS = ("stopped_without_done", "refuse_envelope")
PLAN_KEYS = ("goal", "succession_id", "prev_lease", "cap", "reserves", "workspace", "expect_gen", "new_sid")


def dead_evidence(root, goal: str, sid: str | None, *, measured) -> bool:
    """A SessionEnd wake row (hooks/goal_session_end.js) is `dead` evidence ONLY together with a measured spend."""
    if not sid or not isinstance(measured, int) or isinstance(measured, bool) or measured < 0:
        return False
    p = Path(root) / goal / "ended.jsonl"
    if not p.exists():
        return False
    for line in p.read_bytes().split(b"\n"):
        try:
            if line.strip() and json.loads(line).get("sid") == sid:
                return True
        except ValueError:
            continue
    return False


def react(row: dict, plan_path, *, root=None) -> dict:
    action = (row or {}).get("action")
    if action not in TRIGGERS:
        return {"acted": False, "reason": f"action {action!r} is not a stop"}
    p = Path(plan_path) if plan_path else None
    if p is None or not p.exists():
        return {"acted": False, "reason": "no succession plan: nothing is spent or claimed"}
    plan = json.loads(p.read_text(encoding="utf-8-sig"))
    missing = [k for k in PLAN_KEYS if k not in plan]
    if missing:
        return {"acted": False, "reason": f"succession plan lacks {missing}"}
    base = Path(root) if root else gs._goal_root()
    dead = bool(plan.get("dead", False)) or dead_evidence(base, plan["goal"], plan.get("old_sid"),
                                                          measured=plan.get("measured"))
    out = gs.succeed(**{k: plan[k] for k in PLAN_KEYS}, root=root, old_sid=plan.get("old_sid"),
                     dead=dead, measured=plan.get("measured"))
    return {"acted": True, "trigger": action, "succession": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="goal_chain")
    ap.add_argument("cmd", choices=["react"])
    ap.add_argument("--row", required=True, help="file holding the tick's decision row (JSON)")
    ap.add_argument("--plan")
    a = ap.parse_args(argv)
    row = json.loads(Path(a.row).read_text(encoding="utf-8-sig"))
    out = react(row, a.plan)
    print(json.dumps(out, sort_keys=True))
    return 0 if not out["acted"] or out["succession"]["ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
