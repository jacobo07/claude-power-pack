#!/usr/bin/env python3
"""The seam the hook calls: a UserPromptSubmit payload in, an advisory out.

Reads the harness payload as JSON on stdin, classifies, records the judgement,
and prints the advisory to stdout. Prints NOTHING when the answer adds nothing
to what the constant string already says -- a hook that speaks on every prompt
to say "LIGHT, same as the default" is noise, and noise is what gets a gate
switched off.

Exit codes are about THIS process, never about the prompt:
    0  ran; stdout is the advisory (possibly empty)
    0  ran; could not judge -- still 0, because a tier engine must never cost
       the user their prompt

There is deliberately no non-zero path. Fail-open is the whole contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.gsd_x import heartbeat, tier  # noqa: E402

# THE TOWER'S HAND-OVER. Until 2026-09-24 the capsule reached the prompt path as
# one evidence token, so 215 inherited lessons changed nothing the model could
# read. This hands the bounded lessons over as text, through the owner that
# already injects on this event (spec §7: one effect, one owner).
#
# Offered on the first MAX_OFFERS prompts of a session, not once: this chain
# runs under a deadline that abandons stdout (G-3), and a child cannot observe
# whether its text arrived. Marking "delivered" after one attempt would let one
# abandoned run cost the whole session its inheritance.
MAX_OFFERS = 3


def _tower_dir() -> Path:
    d = Path.home() / ".claude" / "state" / "tower"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _record_offer(sid: str, repo: str, state: str, offered: int) -> None:
    """Spec §8 consumption telemetry, the `offered` rung. Symmetric on purpose:
    an offer of zero is recorded too, or this ledger could only ever answer yes."""
    try:
        import time as _t
        with (_tower_dir() / "consumption.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _t.time(), "sid": sid, "repo": repo,
                                 "capsule_state": state, "offered": offered}) + "\n")
    except Exception:                                   # noqa: BLE001
        pass


def inherited_block(payload: dict) -> str:
    """The Tower lessons for this repo, or "" -- never raises."""
    try:
        import os
        from modules.tower import capsule
        sid = str(payload.get("session_id") or payload.get("sessionId") or "")
        repo = str(payload.get("cwd") or os.getcwd())
        if not sid:
            return ""
        counter = _tower_dir() / "offers" / ("%s.count" % "".join(
            c if c.isalnum() or c == "-" else "_" for c in sid))
        counter.parent.mkdir(parents=True, exist_ok=True)
        done = int(counter.read_text().strip() or 0) if counter.exists() else 0
        if done >= MAX_OFFERS:
            return ""
        state = capsule.read(repo).get("state", "UNKNOWN")
        items = capsule.lessons(repo)
        counter.write_text(str(done + 1))
        _record_offer(sid, repo, state, len(items))
        if not items:
            return ""
        lines = ["Tower baseline -- lessons INHERITED from across the estate "
                 "(unverified; ranked by kind, NOT by relevance to this prompt). "
                 "Apply where they fit; ignore where they do not:"]
        for it in items:
            lines.append("- [%s/%s] %s" % (it.get("origin"), it.get("destination"),
                                          it.get("claim")))
        return "\n".join(lines)
    except Exception:                                   # noqa: BLE001
        return ""


def advisory(v: "tier.TierVerdict") -> str:
    """The text the model sees. Empty when there is nothing worth saying."""
    if v.abstained:
        return (
            "ExecutionOS Lite tier: NOT MEASURED. Capability contracts matched "
            "this prompt but could not be evaluated from a prompt alone — "
            + "; ".join(v.missing)
            + ". Treat the tier as unestablished rather than LIGHT; gather the "
              "named facts or classify it yourself, and say which you did."
        )
    if v.by_floor:
        return ""          # identical to the standing default; say nothing
    drivers = ", ".join(f"{cid} ({verd})" for cid, verd in v.drivers[:4])
    return (
        f"ExecutionOS Lite tier: {v.tier} — MEASURED, not self-assessed. "
        f"Driven by: {drivers}. "
        "This overrides the 'Default LIGHT' in the standing reminder for this "
        "prompt. Source: modules.gsd_x.tier over capability_runtime."
    )


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:                                   # noqa: BLE001
        pass

    prompt = ""
    payload: dict = {}
    try:
        payload = json.loads(raw) if raw.strip() else {}
        # The harness spells it `prompt`; accept the two other spellings seen
        # across hosts rather than returning silence on a rename.
        for key in ("prompt", "user_prompt", "userPrompt"):
            if isinstance(payload.get(key), str) and payload[key].strip():
                prompt = payload[key]
                break
    except Exception:                                   # noqa: BLE001
        prompt = ""

    if not prompt.strip():
        # Nothing to judge. Recorded anyway: a run that saw no prompt is a fact
        # about delivery, and it must be distinguishable from a run that judged
        # and found nothing.
        heartbeat.record("NO_PROMPT", by_floor=True, abstained=False,
                         informative=False, reason="empty or unparsable payload")
        return 0

    v = tier.classify_prompt(prompt)
    heartbeat.record(v.tier, by_floor=v.by_floor, abstained=v.abstained,
                     informative=v.informative, reason=v.reason)

    # Independent of the tier: a floor-LIGHT prompt still inherits the estate.
    parts = [p for p in (advisory(v),
                         inherited_block(payload if isinstance(payload, dict) else {}))
             if p]
    if parts:
        sys.stdout.write("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
