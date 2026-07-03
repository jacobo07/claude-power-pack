#!/usr/bin/env python3
"""hibernate_one.py -- hibernate ONE pane by pid (targeted; tests + manual use).

Unlike run_hibernation.py (which scans + governs the whole board), this acts on a
single designated pane -- for the controlled live proof and for an Owner who wants
to manually sleep a specific pane. It resolves sid/cwd from the pane's beacon
(%TEMP%\\kclaude-pane-<wrapperpid>.sid) unless given explicitly, REFUSES if there is
no resume anchor (never kill a pane that cannot rehydrate), then runs the real
CO-07 store -> wake flag -> kill via hibernate_runner.

    python tools\\hibernate_one.py --pid <claude_pid> --wrapper-pid <kclaude_pid>
    # add --dry to preview (store+flag, pretend-kill); default is a REAL kill.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import process_governor as pg  # noqa: E402
from modules.cognitive_os import hibernate_runner as hr  # noqa: E402


def _resolve_from_beacon(wrapper_pid: int, flag_dir: str):
    beacon = Path(flag_dir) / f"kclaude-pane-{wrapper_pid}.sid"
    if not beacon.is_file():
        return None, None
    try:
        b = json.loads(beacon.read_text(encoding="utf-8-sig"))
        return b.get("sid"), b.get("cwd")
    except (ValueError, OSError):
        return None, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--pid", type=int, required=True, help="the claude.exe pid")
    ap.add_argument("--wrapper-pid", type=int, required=True,
                    help="parent kclaude.ps1 pid (the wake-flag key)")
    ap.add_argument("--sid", default=None)
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--flag-dir", default=os.environ.get("TEMP", "."))
    ap.add_argument("--dry", action="store_true",
                    help="store+flag but pretend-kill (preview); default REAL kill")
    args = ap.parse_args(argv)

    sid, cwd = args.sid, args.cwd
    if not sid or not cwd:
        b_sid, b_cwd = _resolve_from_beacon(args.wrapper_pid, args.flag_dir)
        sid = sid or b_sid
        cwd = cwd or b_cwd
    if not sid:
        print(json.dumps({"verdict": "REFUSED",
                          "reason": "no sid (pass --sid or ensure a beacon exists)"}))
        return 2

    base = Path.home() / ".claude" / "projects"
    tp = str(base / pg._enc(cwd) / f"{sid}.jsonl") if cwd else None
    has_anchor = pg.anchor_exists(sid, cwd, tp)
    if not has_anchor:
        print(json.dumps({"verdict": "REFUSED", "sid": sid,
                          "reason": "no resume anchor -- refusing (would not rehydrate)"}))
        return 3

    pane = pg.PaneProc(pid=args.pid, wrapper_pid=args.wrapper_pid, sid=sid, cwd=cwd,
                       ws_mb=0.0, idle_min=999.0, wrapper_kind="ps1",
                       has_anchor=True, transcript_path=tp)
    kill_fn = (lambda _pid: True) if args.dry else None
    run = hr.hibernate_pane(pane, flag_dir=args.flag_dir, kill_fn=kill_fn)
    print(json.dumps({"verdict": run.verdict, "ok": run.ok, "killed": run.killed,
                      "sid": sid, "archive_id": run.archive_id,
                      "flag": run.flag_path, "reason": run.reason,
                      "dry": args.dry}))
    return 0 if run.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
