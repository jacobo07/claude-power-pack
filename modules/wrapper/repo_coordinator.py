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


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--max-age-hours", type=float, default=2.0)
    args = ap.parse_args(argv)
    d = coordinate(args.cwd or os.getcwd(), max_age_hours=args.max_age_hours)
    if d.warning:
        print(d.warning)
        print(f"# default_resume={d.default_resume}")
    else:
        print(f"# no active session ({d.source}) -- launch fresh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
