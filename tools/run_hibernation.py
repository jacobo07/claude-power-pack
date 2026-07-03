#!/usr/bin/env python3
"""run_hibernation.py -- FASE A orchestrator: scan -> enrich -> plan -> hibernate.

Reads a raw scan_panes.ps1 JSON array, enriches it (idle/anchor via the
transcript), plans with the Resource Governor, and -- only with --live -- executes
the hibernate targets (CO-07 store -> wake flag -> kill). DRY BY DEFAULT: without
--live it prints the plan and performs NO side effects (no flags, no kills), so it
is always safe to preview. Fail-open: any error leaves every process alive.

Daemon usage (Owner-installed Scheduled Task, ~every 5 min):
    powershell -NoProfile -File tools\\scan_panes.ps1 > %TEMP%\\pp_scan.json
    python tools\\run_hibernation.py --from-scan %TEMP%\\pp_scan.json --live

Never-hibernate invariants (foreground / loop / hot / unknown-idle / no-anchor /
no-sid / non-wakeable) are enforced by process_governor.decide -- this file only
composes. The active pane is protected structurally: it is never idle, so it never
clears the idle>threshold gate.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import process_governor as pg  # noqa: E402
from modules.cognitive_os import hibernate_runner as hr  # noqa: E402


def run(raw, *, flag_dir, idle_min: float = pg.IDLE_THRESHOLD_MIN,
        live: bool = False, proj_base=None, now: datetime | None = None,
        hibernate_fn=None, kill_fn=None):
    """Compose enrich -> plan -> (optional) execute. DRY (live=False) returns the
    plan with an empty run list and touches nothing. Returns (plan, runs)."""
    panes = pg.enrich_panes(raw, now=now, proj_base=proj_base)
    gp = pg.plan(panes, idle_threshold_min=idle_min)
    runs = []
    if live:
        runs = hr.run_plan(gp, flag_dir=flag_dir, hibernate_fn=hibernate_fn,
                           kill_fn=kill_fn, now=now)
    return gp, runs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--from-scan", required=True,
                    help="path to a raw scan_panes.ps1 JSON array")
    ap.add_argument("--flag-dir", default=os.environ.get("TEMP", "."))
    ap.add_argument("--idle-min", type=float, default=pg.IDLE_THRESHOLD_MIN)
    ap.add_argument("--live", action="store_true",
                    help="actually hibernate (store+flag+kill); default is DRY")
    ap.add_argument("--proj-base", default=None)
    args = ap.parse_args(argv)

    try:
        raw = json.loads(Path(args.from_scan).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        print(f"# scan read failed ({exc}) -- nothing done (fail-open)")
        return 0

    gp, runs = run(raw, flag_dir=args.flag_dir, idle_min=args.idle_min,
                   live=args.live, proj_base=args.proj_base)
    print(pg.format_plan(gp))
    for rn in runs:
        print(f"  {rn.verdict:12} pid={rn.pid} killed={rn.killed} -- {rn.reason}")
    mode = "LIVE" if args.live else "DRY (preview only -- pass --live to act)"
    done = sum(1 for r in runs if r.ok)
    print(f"# {mode}: {done}/{len(runs)} hibernated, "
          f"~{sum(r.reclaim_mb for r in runs if r.ok):.0f}MB reclaimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
