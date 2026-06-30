#!/usr/bin/env python3
"""repo_coordinator.py -- W4: warn before opening a second pane on the same repo.

Before launching claude in a cwd, check whether that cwd already has an ACTIVE
session (a transcript-verified pane_map candidate touched within `max_age_hours`,
default 2h). If so, surface a warning so the Owner can resume the existing
conversation (default S) instead of fragmenting work across two panes.

Reuses W2's anchor logic via `auto_resumer.list_candidates` -- same
transcript-on-disk guarantee (a pane_map sid whose `<sid>.jsonl` is gone is
never offered). This module returns DATA + a formatted warning + the default
resume arg; the interactive S/n (and numeric pick for multiples) lives in the
orchestrator (W6, kclaude.ps1), so this stays pure and hermetically testable.

Fail-open: ANY error / no pane_map -> CoordDecision(active=False) so the launch
proceeds as a fresh session.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.wrapper import auto_resumer  # noqa: E402


@dataclass
class CoordDecision:
    active: bool                       # is there a recent active session here?
    warning: str | None                # ready-to-print prompt, or None
    default_resume: str | None         # "--resume <sid>" applied if Owner hits S
    candidates: list = field(default_factory=list)   # active candidates [{...}]
    source: str = ""                   # active | multiple | none | error


def _parse_iso(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _age_minutes(last_activity, now: datetime):
    d = _parse_iso(last_activity)
    if d is None:
        return None
    return max(0.0, (now - d).total_seconds() / 60.0)


def coordinate(cwd: str, *, state_dir=None, proj_base=None,
               max_age_hours: float = 2.0, now: datetime | None = None,
               list_fn=None) -> CoordDecision:
    """Decide whether to warn about an existing active session on `cwd`."""
    try:
        now = now or datetime.now(timezone.utc)
        cands = (list_fn or auto_resumer.list_candidates)(
            cwd, state_dir, proj_base)
        max_min = max_age_hours * 60.0
        active = []
        for c in cands:
            age = _age_minutes(c.get("lastActivity"), now)
            if age is not None and age <= max_min:
                c = {**c, "_age_min": age}
                active.append(c)
        if not active:
            return CoordDecision(False, None, None, [], "none")

        active.sort(key=lambda c: c["_age_min"])  # most recent first
        repo = Path(cwd).name or cwd
        if len(active) == 1:
            c = active[0]
            warning = (f"PP: sesion activa de {repo} "
                       f"(hace {c['_age_min']:.0f}m). Resumir? [S/n]")
            return CoordDecision(True, warning,
                                 f"--resume {c['session_id']}", active, "active")
        # multiple active sessions on the same cwd -> numbered choice
        lines = [f"PP: {len(active)} sesiones activas de {repo}:"]
        for i, c in enumerate(active, 1):
            topic = c.get("topic") or c["session_id"][:8]
            lines.append(f"  {i}. {topic} (hace {c['_age_min']:.0f}m)")
        lines.append("Elige numero para resumir, o n para nueva sesion [1]:")
        warning = "\n".join(lines)
        return CoordDecision(True, warning,
                             f"--resume {active[0]['session_id']}",
                             active, "multiple")
    except Exception:  # noqa: BLE001 -- fail-open: never block the launch
        return CoordDecision(False, None, None, [], "error")


# --- Parallel-panes burn detector (D2, Weekly-Burn-RCA 2026-06-30) -----------
# coordinate() (above) warns about a second pane only to offer RESUME. The 48h
# burn forensic showed the costly pattern is different: 2+ panes on the SAME
# repo each firing large structured prompts (EXECUTION MODE / ULTRA-PLAN, >8k
# chars) within a short window -> multiplied output with little extra progress
# (each pane rebuilds similar context). This detector surfaces THAT pattern.

LARGE_PROMPT_CHARS = 8000     # EXECUTION/ULTRA-PLAN prompts measured 8k-18k chars
PARALLEL_WINDOW_MIN = 60.0    # "short window" = within the last hour
MIN_PARALLEL_PANES = 2        # the pattern needs >=2 panes burning at once


@dataclass
class ParallelBurnDecision:
    burning: bool                      # parallel large-prompt pattern detected?
    warning: str | None                # ready-to-print advisory, or None
    panes: int = 0                     # panes with a recent large prompt
    session_ids: list = field(default_factory=list)
    source: str = ""                   # burning | quiet | none | error


def _user_text(entry) -> str | None:
    msg = entry.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "user":
        return None
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = [b.get("text", "") for b in c
                 if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(parts)
    return None


def _has_recent_large_prompt(path: Path, now: datetime,
                             window_min: float, large_chars: int) -> bool:
    """True iff the transcript holds a user prompt >large_chars whose own
    timestamp is within the last window_min. Tool-result echoes (content blocks
    without a text type, or starting with '<') are not human prompts."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ut = _user_text(e)
        if not ut or len(ut) <= large_chars or ut.lstrip().startswith("<"):
            continue
        age = _age_minutes(e.get("timestamp"), now)
        if age is not None and age <= window_min:
            return True
    return False


def parallel_burn(cwd: str, *, state_dir=None, proj_base=None,
                  now: datetime | None = None,
                  window_min: float = PARALLEL_WINDOW_MIN,
                  large_chars: int = LARGE_PROMPT_CHARS,
                  min_panes: int = MIN_PARALLEL_PANES,
                  list_fn=None) -> ParallelBurnDecision:
    """Detect 2+ same-repo panes each firing large prompts in a short window."""
    try:
        now = now or datetime.now(timezone.utc)
        base = Path(proj_base) if proj_base else (
            Path.home() / ".claude" / "projects")
        cwd_enc = __import__("re").sub(r"[^a-zA-Z0-9]", "-", cwd or "")
        cands = (list_fn or auto_resumer.list_candidates)(
            cwd, state_dir, proj_base)
        hot = []
        for c in cands:
            sid = c.get("session_id")
            if not sid:
                continue
            path = base / cwd_enc / f"{sid}.jsonl"
            if _has_recent_large_prompt(path, now, window_min, large_chars):
                hot.append(sid)
        if len(hot) < min_panes:
            return ParallelBurnDecision(
                False, None, len(hot), hot,
                "quiet" if cands else "none")
        repo = Path(cwd).name or cwd
        warning = (
            f"⚠ PP: {len(hot)} paneles de {repo} lanzando prompts grandes "
            f"(>{large_chars // 1000}k) en paralelo (<{window_min:.0f}min). "
            f"Este es el patron del burn de 48h reciente -- multiplica el output "
            f"sin multiplicar el progreso. Considera consolidar en un pane o "
            f"espaciar los prompts.")
        return ParallelBurnDecision(True, warning, len(hot), hot, "burning")
    except Exception:  # noqa: BLE001 -- fail-open: never block the launch
        return ParallelBurnDecision(False, None, 0, [], "error")


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--max-age-hours", type=float, default=2.0)
    args = ap.parse_args(argv)
    cwd = args.cwd or os.getcwd()
    d = coordinate(cwd, max_age_hours=args.max_age_hours)
    if d.warning:
        print(d.warning)
        print(f"# default_resume={d.default_resume}")
    else:
        print(f"# no active session ({d.source}) -- launch fresh")
    pb = parallel_burn(cwd)
    if pb.warning:
        print(pb.warning)
    else:
        print(f"# no parallel burn ({pb.source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
