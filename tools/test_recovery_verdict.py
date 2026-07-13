#!/usr/bin/env python3
"""V-gates for tools/recovery_verdict.py -- the surface that makes the arbiter judge.

Every gate here is written against a symptom the Owner actually reported, because a
verdict tool that cannot detect the failures we have already lived through is theater.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import recovery_verdict as RV  # noqa: E402  (tools/ is on the path)
from modules.session_resilience import acceptance  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[OK] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diag}")


def _pane(repo: str, sid: str, live: bool = True) -> dict:
    return {"repo": repo, "cwd": f"C:/repos/{repo}", "sessionId": sid, "live": live}


def _map(panes: list[dict]) -> dict:
    return {"panes": panes}


def main() -> int:
    # The workspace as it stood before the interruption: two repos, four live panes.
    before = _map([
        _pane("power-pack", "sid-1"), _pane("power-pack", "sid-2"),
        _pane("power-pack", "sid-3"), _pane("tua-x", "sid-4"),
    ])
    ref = RV.to_description(RV._live_only(before))

    # V-RV-FULL: a complete restore is RECOVERED.
    full = RV.to_description(RV._live_only(before))
    d, _, _ = RV.verdict(ref, full)
    if d.verdict == acceptance.RECOVERED and d.allow_complete:
        _ok("V-RV-FULL", "identical topology -> RECOVERED, completion allowed")
    else:
        _fail("V-RV-FULL", f"{d.verdict} / allow_complete={d.allow_complete}")

    # V-RV-PANE-COLLAPSE: the reported symptom -- three panes come back on ONE session.
    # The pane count can even look right while every pane shares a conversation.
    collapsed = RV.to_description(RV._live_only(_map([
        _pane("power-pack", "sid-1"), _pane("power-pack", "sid-1"),
        _pane("power-pack", "sid-1"), _pane("tua-x", "sid-4"),
    ])))
    d, _, _ = RV.verdict(ref, collapsed)
    if d.verdict != acceptance.RECOVERED and not d.allow_complete:
        _ok("V-RV-PANE-COLLAPSE", f"panes collapsed onto one session -> {d.verdict}, held")
    else:
        _fail("V-RV-PANE-COLLAPSE", "N-panes-on-one-session was accepted as a full recovery")

    # V-RV-MISSING-WINDOW: a whole repo window never came back.
    lost_window = RV.to_description(RV._live_only(_map([
        _pane("power-pack", "sid-1"), _pane("power-pack", "sid-2"),
        _pane("power-pack", "sid-3"),
    ])))
    d, _, _ = RV.verdict(ref, lost_window)
    summary = RV.summarize(ref, lost_window)
    if d.verdict != acceptance.RECOVERED and "tua-x" in summary["windows"]:
        _ok("V-RV-MISSING-WINDOW", f"windows: {summary['windows']}")
    else:
        _fail("V-RV-MISSING-WINDOW", f"a lost window was not reported ({d.verdict})")

    # V-RV-DEAD-PANE-NOT-CREDITED: a pane listed but NOT live must not count as restored.
    # The map is not the territory: crediting a dead pane is exactly the fake recovery
    # this tool exists to prevent.
    dead = RV.to_description(RV._live_only(_map([
        _pane("power-pack", "sid-1"), _pane("power-pack", "sid-2"),
        _pane("power-pack", "sid-3", live=False), _pane("tua-x", "sid-4"),
    ])))
    d, _, _ = RV.verdict(ref, dead)
    if d.verdict != acceptance.RECOVERED:
        _ok("V-RV-DEAD-PANE-NOT-CREDITED", "a listed-but-dead pane did not count as recovered")
    else:
        _fail("V-RV-DEAD-PANE-NOT-CREDITED", "a dead pane was credited as a recovery")

    # V-RV-UNWITNESSED-NOT-PASSED: the four dimensions pane_map cannot see must be
    # EXCLUDED, never silently scored as passing.
    d, card, _ = RV.verdict(ref, full)
    unseen = {"editor_tabs", "editor_order", "focus", "scroll"}
    if not (unseen & set(card.dimensions)):
        _ok("V-RV-UNWITNESSED-NOT-PASSED",
            f"scored only {sorted(card.dimensions)}; {sorted(unseen)} excluded, not passed")
    else:
        _fail("V-RV-UNWITNESSED-NOT-PASSED",
              "a dimension pane_map cannot witness was scored anyway")

    total = _passes + _fails
    print(f"RECOVERY_VERDICT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
