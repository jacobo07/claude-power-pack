#!/usr/bin/env python3
"""turn_counter.py -- W1: pre-launch context-pressure advisory for kclaude.

At wrapper launch time there is no session_id yet, so we assess the most-recent
transcript for the cwd (context_monitor picks it when session_id is None) and,
if it is under pressure, surface an advisory BEFORE claude launches so the Owner
can /compact or /kclear on resume.

COMPOSES `modules.cpc_os.context_monitor` -- the authoritative pressure trip
(SCS C28; UKDL T-RAM-DEDUP-001). We do NOT hardcode thresholds: context_monitor
owns them (COMPACT 16 MB / 6000 turns, KCLEAR 24 MB / 12000 turns, RAM 20/28 GB,
softened 2026-06-05). The prompt's 800/1500-turn suggestion is intentionally
NOT used -- a second threshold source would re-create the very drift the prior
audit removed.

Gaming mode: a co-resident Minecraft JVM (javaw.exe) means a RAM-contended host;
halve the effective thresholds (via ram_guard.minecraft_active) so the advisory
fires earlier.

Fail-open: ANY error -> None (no advisory; the wrapper still launches claude).
`assess_fn` / `gaming` are injectable so the done-gate is hermetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]


def _gaming_active() -> bool:
    """True when a Minecraft JVM is co-resident. Fail-safe: error -> False."""
    try:
        if str(_PP_ROOT) not in sys.path:
            sys.path.insert(0, str(_PP_ROOT))
        from tools.ram_guard import minecraft_active  # type: ignore
        return bool(minecraft_active())
    except Exception:  # noqa: BLE001
        return False


def _format(state: str, sig: dict, gaming: bool, tripped) -> str:
    label = "KCLEAR" if state == "KCLEAR_NEEDED" else "COMPACT"
    ram = sig.get("ram_gb")
    jsonl = sig.get("jsonl_mb")
    turns = sig.get("turns")
    why = ", ".join(tripped) if tripped else "threshold crossed"
    g = " [GAMING: halved thresholds, Minecraft JVM active]" if gaming else ""
    action = ("/kclear (checkpoint + reset)" if state == "KCLEAR_NEEDED"
              else "/compact (in-place summarize)")
    return (f"[kclaude turn-guard] Context pressure: {label}{g}. "
            f"Last session for this repo -- ram={ram}GB jsonl={jsonl}MB "
            f"turns={turns} ({why}). Consider {action} after resuming.")


def check(cwd: str, session_id: str | None = None,
          gaming: bool | None = None, assess_fn=None) -> str | None:
    """Return a pressure advisory string for the cwd's latest transcript, or
    None when healthy / unmeasurable. Fail-open: never raises.

    assess_fn(cwd, session_id) -> decision dict (injectable for tests).
    """
    try:
        if assess_fn is None:
            if str(_PP_ROOT) not in sys.path:
                sys.path.insert(0, str(_PP_ROOT))
            from modules.cpc_os.context_monitor import assess as assess_fn  # type: ignore
        decision = assess_fn(cwd, session_id)
    except Exception:  # noqa: BLE001
        return None

    if not isinstance(decision, dict):
        return None
    state = decision.get("state", "HEALTHY")
    sig = decision.get("signals", {}) or {}
    tripped = decision.get("tripped")

    if gaming is None:
        gaming = _gaming_active()

    # Gaming: if HEALTHY at normal thresholds, re-evaluate at halved thresholds
    # using the signals already gathered (no second I/O pass).
    if gaming and state == "HEALTHY":
        try:
            if str(_PP_ROOT) not in sys.path:
                sys.path.insert(0, str(_PP_ROOT))
            from modules.cpc_os.context_monitor import (  # type: ignore
                evaluate, COMPACT_MB, KCLEAR_MB, COMPACT_TURNS, KCLEAR_TURNS,
                WARN_GB, CRIT_GB,
            )
            decision = evaluate(
                sig.get("ram_gb"), sig.get("jsonl_mb"), sig.get("turns"),
                warn_gb=WARN_GB / 2, crit_gb=CRIT_GB / 2,
                compact_mb=COMPACT_MB / 2, kclear_mb=KCLEAR_MB / 2,
                compact_turns=COMPACT_TURNS // 2, kclear_turns=KCLEAR_TURNS // 2,
            )
            state = decision.get("state", "HEALTHY")
            sig = decision.get("signals", {}) or sig
            tripped = decision.get("tripped")
        except Exception:  # noqa: BLE001
            pass

    if state == "HEALTHY":
        return None
    return _format(state, sig, gaming, tripped)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args(argv)
    import os
    advisory = check(args.cwd or os.getcwd(), args.session_id)
    if advisory:
        print(advisory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
