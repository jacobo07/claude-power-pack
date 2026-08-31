#!/usr/bin/env python3
"""Stop hook — refresh the cross-project baseline at every session close.

Spec: vault/specs/cross-project-baseline.md (Owner chose option B, 2026-08-31:
"eso deberia pasar globalmente aunque no les de esa orden en el prompt,
SIEMPRE").

Why a dedicated entry point rather than `ceps.py promote` in the chain: the
dispatcher runs `spawnSync(step.exe, [abs])` — script path only, no argv. Adding
argv support would change a runner shared by six chains to serve one caller.

Why Stop rather than SessionStart: promotion reads the events THIS session just
wrote, so running it at close means the next session in ANY project — this one
or another — starts with a current baseline. That is the whole point: the
learning has to be waiting when you arrive, not assembled when you leave.

Cost is bounded and small: one read of vault/ceps/events.jsonl (~68 KB) and one
atomic write of a file that currently holds four records. It is safe to run
always, which is what "SIEMPRE" requires.

Fail-open ABSOLUTE: any error is logged to the receipt and swallowed. A hook
that stalls or breaks session close is worse than a stale baseline.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "tools"))

_RECEIPT = Path(os.path.expanduser("~")) / ".claude" / "state" / "ceps"


def _log(payload: dict) -> None:
    """One-line receipt. Without it a fail-open path leaves no trace, and this
    repo has an 80-day precedent of exactly that going unnoticed."""
    try:
        _RECEIPT.mkdir(parents=True, exist_ok=True)
        payload["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(_RECEIPT / "promote.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break Stop


def main() -> int:
    try:
        sys.stdin.read()  # drain the Stop JSON; nothing here needs its fields
    except (OSError, ValueError):
        pass

    try:
        import ceps  # imported inside the guard: a broken import must not raise
        res = ceps.promote_patterns()
        _log(res if isinstance(res, dict) else {"ok": False, "res": str(res)})
    except Exception as exc:  # noqa: BLE001 -- fail-open is the contract
        _log({"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    try:
        sys.stdout.write("{}")
    except OSError:
        pass
    return 0  # ALWAYS 0 — this hook never blocks session close


if __name__ == "__main__":
    sys.exit(main())
