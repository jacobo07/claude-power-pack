"""Pre-budget Owner router (OCP Phase 3). Pure and read-only: classifies a whole Owner message with the closed
capital grammar and binds it to a target goal. It never calls a model, never touches the network, and never
writes a ledger row: Phase 3 answers "NOT APPLIED"; the receipt and the apply step belong to Phase 4.

Target rule: an explicit valid, existing goal wins; otherwise exactly one open authority boundary; two or more
is CONFLICTED. The cwd and the session binding never select a target.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from modules.provider_routing import capital_grammar as cg
from modules.provider_routing.ledger import GoalLedger

TYPED = "TYPED_CONTROL_OPERATION"
CLARIFY = "DETERMINISTIC_CLARIFICATION"
INVALID = "INVALID"
CONFLICTED = "CONFLICTED"
NOT_CONTROL = "NOT_CONTROL"

GOAL_RE = re.compile(r"^(?!\.+$)[A-Za-z0-9._-]{1,128}$")
SID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def goals_root() -> Path:
    state = os.environ.get("GSD_LONG_RUN_STATE_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "state")
    return Path(state) / "goal-budget"


def _goals(root: Path) -> list[str]:
    try:
        return sorted(p.name for p in root.iterdir() if p.is_dir() and GOAL_RE.match(p.name))
    except OSError:
        return []


def open_boundaries(root: Path) -> list[str]:
    """Goals whose lineage holds an authority_required row that no lease satisfies and whose headroom is
    unknown or short. An unreadable ledger is a candidate: UNKNOWN is never skipped."""
    out = []
    for goal in _goals(root):
        try:
            led = GoalLedger(root / goal, goal)
            lin = led.lineage()
            opened = {ls.get("succession_id") for ls in lin["leases"]}
            pend = [a for a in lin["authority_required"] if a.get("succession_id") not in opened
                    and (a.get("executable") is None or a["executable"] < a.get("need", 0))]
        except Exception:  # noqa: BLE001 -- unreadable means unknown, and unknown is a candidate
            out.append(goal)
            continue
        if pend:
            out.append(goal)
    return out


def _fingerprint(session_id, prompt, event) -> str:
    ts = (event or {}).get("timestamp") or ""
    return hashlib.sha256(f"{session_id}\n{prompt}\n{ts}".encode("utf-8", "replace")).hexdigest()


def _principal(session_id, event) -> str:
    ok = isinstance(session_id, str) and SID_RE.match(session_id) \
        and (event or {}).get("hook_event_name") == "UserPromptSubmit"
    return "owner" if ok else "unknown"


def _out(outcome, intent, principal, goal, source, cands, fp, reply):
    return {"outcome": outcome, "intent": intent, "principal": principal,
            "target": {"goal": goal, "source": source, "candidates": cands},
            "fingerprint": fp, "reply": reply, "applied": False}


def _say(intent, goal) -> str:
    op, v = intent["op"], intent.get("value")
    what = {"ADD": f"ADD +{v:,}" if v else "ADD", "SET": f"SET total {v:,}" if v else "SET",
            "STOP": "STOP", "KEEP": "KEEP"}[op]
    return (f"OWNER CONTROL (0 model tokens): {what} for goal {goal}. NOT APPLIED: this message was classified "
            "and bound, but capital changes are not enabled on this path yet.")


def route(prompt, session_id, event=None, goals_dir=None) -> dict:
    fp = _fingerprint(session_id, prompt, event)
    principal = _principal(session_id, event)
    intent = cg.parse_intent(prompt)
    if intent is None or principal != "owner":
        return _out(NOT_CONTROL, intent, principal, None, None, [], fp, "")
    root = Path(goals_dir) if goals_dir else goals_root()
    if intent["op"] == "INVALID":
        return _out(INVALID, intent, principal, None, None, [], fp,
                    f"OWNER CONTROL (0 model tokens): not understood: {intent['reason']}. Nothing applied.")
    if intent["op"] == "CLARIFY":
        return _out(CLARIFY, intent, principal, None, None, [], fp,
                    "OWNER CONTROL (0 model tokens): add or set? Reply `" + "` or `".join(
                        c.replace("ADD +", "subelo por ").replace("SET total ", "subelo a ")
                        for c in intent["choices"]) + "`. Nothing applied.")
    explicit = intent.get("goal")
    if explicit:
        if explicit in _goals(root):
            return _out(TYPED, intent, principal, explicit, "explicit", [explicit], fp, _say(intent, explicit))
        return _out(INVALID, intent, principal, None, None, [], fp,
                    f"OWNER CONTROL (0 model tokens): goal {explicit} does not exist. Nothing applied.")
    cands = open_boundaries(root)
    if len(cands) == 1:
        return _out(TYPED, intent, principal, cands[0], "single_open_boundary", cands, fp, _say(intent, cands[0]))
    if len(cands) > 1:
        return _out(CONFLICTED, intent, principal, None, None, cands, fp,
                    "OWNER CONTROL (0 model tokens): " + str(len(cands)) + " goals are waiting on capital ("
                    + ", ".join(cands) + "). Name one: `modify <goal> to <total>`. Nothing applied.")
    if intent["op"] in ("KEEP", "STOP"):
        return _out(NOT_CONTROL, intent, principal, None, None, [], fp, "")
    return _out(CLARIFY, intent, principal, None, None, [], fp,
                "OWNER CONTROL (0 model tokens): no goal is waiting on capital; use "
                "`modify <goal> to <total>`. Nothing applied.")
