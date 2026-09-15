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

    text = advisory(v)
    if text:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
