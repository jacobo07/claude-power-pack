#!/usr/bin/env python3
"""context_monitor.py - unified context-pressure decision for CPC-OS.

Auto-Reset Orchestrator M1 (2026-06-04). Returns ONE of three states --
HEALTHY / COMPACT_NEEDED / KCLEAR_NEEDED -- by composing the proxies that
already exist (SCS C28: compose, do not duplicate):

  * claude.exe RAM  -- tools/ram_guard.claude_ram_mb() (psutil -> PowerShell
                       Get-Process; never CIM, which hangs on this host).
  * TIS jsonl size  -- bytes of the active session transcript at
                       ~/.claude/projects/<encoded-cwd>/<sid>.jsonl, a proxy
                       for accumulated tokens (this session: 1.4 MB ~= 32%).
  * turn count      -- lines in that transcript (cheap event-count proxy).

Severity ladder (hardest wins):
  KCLEAR_NEEDED  if RAM >= CRIT_GB  OR jsonl >= KCLEAR_MB  OR turns >= KCLEAR_TURNS
  COMPACT_NEEDED if RAM >= WARN_GB  OR jsonl >= COMPACT_MB OR turns >= COMPACT_TURNS
  HEALTHY        otherwise

KCLEAR is the hard reset (fresh session) for the worst pressure; COMPACT is
the in-place summarize for moderate pressure. RAM is the primary trigger per
the reality contract ("la RAM sube > threshold"); jsonl/turns are secondary
signals so a heavy session with modest RAM still trips.

Thresholds are env-tunable. RAM thresholds default to ram_guard's
(PP_RAM_WARN_GB=20 / PP_RAM_CRIT_GB=28). A None RAM reading (no measurement)
simply drops the RAM signal -- the jsonl/turn proxies still decide.

Importable: assess(cwd, session_id) -> dict. CLI: python -m
modules.cpc_os.context_monitor [--json] [--cwd PATH] [--session-id SID].
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]

# State constants.
HEALTHY = "HEALTHY"
COMPACT_NEEDED = "COMPACT_NEEDED"
KCLEAR_NEEDED = "KCLEAR_NEEDED"

# Thresholds (env-tunable). RAM defaults mirror ram_guard.
WARN_GB = float(os.environ.get("PP_RAM_WARN_GB", "20"))
CRIT_GB = float(os.environ.get("PP_RAM_CRIT_GB", "28"))
# Thresholds softened 2026-06-05 (Owner: "less aggressive"). jsonl/turns are
# SECONDARY proxies; RAM (WARN/CRIT GB above) stays the primary OOM trigger.
# A Claude Code transcript embeds full tool outputs, so a multi-MB jsonl is
# normal -- the old 4/6 MB + 1200/2400-line gates tripped on healthy sessions.
COMPACT_MB = float(os.environ.get("PP_CTX_COMPACT_MB", "16"))
KCLEAR_MB = float(os.environ.get("PP_CTX_KCLEAR_MB", "24"))
COMPACT_TURNS = int(os.environ.get("PP_CTX_COMPACT_TURNS", "6000"))
KCLEAR_TURNS = int(os.environ.get("PP_CTX_KCLEAR_TURNS", "12000"))

_BYTES_PER_MB = 1024 * 1024


def claude_ram_gb() -> float | None:
    """claude.exe RAM in GB via ram_guard (None if unmeasurable)."""
    try:
        sys.path.insert(0, str(_PP_ROOT))
        from tools.ram_guard import claude_ram_mb  # type: ignore
        mb = claude_ram_mb()
        return None if mb is None else round(mb / 1024, 2)
    except Exception:  # noqa: BLE001
        return None


def _active_transcript(cwd: str | None, session_id: str | None) -> Path | None:
    """Resolve the active session transcript. Prefer the exact
    <encoded-cwd>/<session_id>.jsonl; else the most-recent .jsonl in that
    project dir. Reuses snapshot.py's encoder (SCS C28)."""
    try:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.snapshot import (  # type: ignore
            _encode_project_dir, PROJECTS_DIR,
        )
    except Exception:  # noqa: BLE001
        return None
    cwd = cwd or os.getcwd()
    proj = PROJECTS_DIR / _encode_project_dir(cwd)
    if not proj.is_dir():
        return None
    if session_id:
        exact = proj / f"{session_id}.jsonl"
        if exact.is_file():
            return exact
    try:
        cands = sorted(proj.glob("*.jsonl"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        return cands[0] if cands else None
    except OSError:
        return None


def _transcript_signals(path: Path | None) -> tuple[float | None, int | None]:
    """(jsonl_mb, turns) for the transcript, or (None, None)."""
    if path is None:
        return None, None
    try:
        size_mb = round(path.stat().st_size / _BYTES_PER_MB, 2)
    except OSError:
        return None, None
    turns = None
    try:
        with path.open("rb") as fh:
            turns = sum(1 for _ in fh)
    except OSError:
        turns = None
    return size_mb, turns


def evaluate(ram_gb: float | None,
             jsonl_mb: float | None,
             turns: int | None,
             *,
             warn_gb: float = WARN_GB, crit_gb: float = CRIT_GB,
             compact_mb: float = COMPACT_MB, kclear_mb: float = KCLEAR_MB,
             compact_turns: int = COMPACT_TURNS,
             kclear_turns: int = KCLEAR_TURNS) -> dict:
    """Pure decision function -- the unit-testable core. Returns dict with
    state, tripped (list of proxy reasons), and the raw signals."""
    kclear_reasons: list[str] = []
    compact_reasons: list[str] = []

    if ram_gb is not None:
        if ram_gb >= crit_gb:
            kclear_reasons.append(f"ram {ram_gb}GB>={crit_gb}GB")
        elif ram_gb >= warn_gb:
            compact_reasons.append(f"ram {ram_gb}GB>={warn_gb}GB")
    if jsonl_mb is not None:
        if jsonl_mb >= kclear_mb:
            kclear_reasons.append(f"jsonl {jsonl_mb}MB>={kclear_mb}MB")
        elif jsonl_mb >= compact_mb:
            compact_reasons.append(f"jsonl {jsonl_mb}MB>={compact_mb}MB")
    if turns is not None:
        if turns >= kclear_turns:
            kclear_reasons.append(f"turns {turns}>={kclear_turns}")
        elif turns >= compact_turns:
            compact_reasons.append(f"turns {turns}>={compact_turns}")

    if kclear_reasons:
        state, tripped = KCLEAR_NEEDED, kclear_reasons
    elif compact_reasons:
        state, tripped = COMPACT_NEEDED, compact_reasons
    else:
        state, tripped = HEALTHY, []

    return {
        "state": state,
        "tripped": tripped,
        "signals": {
            "ram_gb": ram_gb, "jsonl_mb": jsonl_mb, "turns": turns,
        },
        "thresholds": {
            "warn_gb": warn_gb, "crit_gb": crit_gb,
            "compact_mb": compact_mb, "kclear_mb": kclear_mb,
            "compact_turns": compact_turns, "kclear_turns": kclear_turns,
        },
    }


def assess(cwd: str | None = None, session_id: str | None = None) -> dict:
    """Gather live signals for the current session and decide. The I/O
    boundary -- evaluate() is the pure core tests exercise."""
    ram_gb = claude_ram_gb()
    transcript = _active_transcript(cwd, session_id)
    jsonl_mb, turns = _transcript_signals(transcript)
    out = evaluate(ram_gb, jsonl_mb, turns)
    out["transcript"] = str(transcript) if transcript else None
    out["cwd"] = cwd or os.getcwd()
    out["session_id"] = session_id
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args(argv)
    decision = assess(cwd=args.cwd, session_id=args.session_id)
    if args.json:
        print(json.dumps(decision))
    else:
        sig = decision["signals"]
        print(f"{decision['state']}  ram={sig['ram_gb']}GB "
              f"jsonl={sig['jsonl_mb']}MB turns={sig['turns']}"
              + (f"  [{', '.join(decision['tripped'])}]"
                 if decision["tripped"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
