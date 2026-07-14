#!/usr/bin/env python3
"""SessionStart gate: detect the interruption, pin the reference, judge the restore.

This is the live surface that turns three orphan modules into a working loop.
`power_beacon.classify_startup`, `epoch` and `reentry` were reachable by no hook,
command or task -- so no interruption was ever detected and no restore was ever
judged, which is precisely why an incomplete one was accepted in silence.

Run at SessionStart (synchronously -- its output is the point). It:
  1. detects whether startup crossed an interruption (two-signal rule);
  2. pins the last topology recorded while the session was alive (idempotent --
     the other N panes starting beside this one reuse the same pin);
  3. scores what actually came back against that pin;
  4. prints ONE line for the Owner when panes are missing, and nothing at all
     when there is nothing to say.

Silence is the common path: a normal session start prints nothing and exits 0.

KNOWN LIMITATION (declared, not hidden). The boot-crossing signal proves an
interruption for the reboot and OOM-reboot cases. An application-level kill that
does NOT reboot the machine (Cursor OOM-killed, host survives) is only detectable
via a MEASURED zero live-terminal count, and this gate has no trustworthy way to
measure that at startup: pane_map's `live` flags are recomputed by a 5-minute task
from transcript recency, so right after a cold start they still describe the dead
panes. Rather than pass a fabricated count -- which would either miss real crashes
or fire on every new pane opened beside live ones -- the gate leaves it UNMEASURED,
and `epoch.detect_interruption` never reads an unmeasured count as zero. A caller
that CAN measure it honestly may pass --live-terminals; `/recovery-verdict` remains
the manual path for that case.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.session_resilience import epoch  # noqa: E402

STATE_DIR = Path.home() / ".claude" / "state"


def banner(state_dir: Path) -> str:
    """The Owner-facing line, or '' when there is nothing to report."""
    import tools.recovery_verdict as rv

    rv.STATE_DIR = state_dir
    rv.HISTORY_DIR = state_dir / epoch.HISTORY_DIRNAME

    ep = epoch.read_epoch(state_dir)
    if not ep or ep.get("status") != epoch.OPEN:
        return ""

    ref = epoch.reference_path(state_dir, ep)
    if ref is None:
        return ("[recovery] An interruption at " + str(ep.get("interrupted_at"))
                + " is open, but the topology pinned before it is not on disk -- "
                "the restore CANNOT be judged (HELD). Nothing is being claimed as "
                "recovered.")

    obs = state_dir / "pane_map.json"
    if not obs.is_file():
        return ""
    try:
        reference = rv.to_description(rv._live_only(rv._read_json(ref)))
        observed = rv.to_description(rv._live_only(rv._read_json(obs)))
    except (OSError, ValueError):
        return ""

    decision, _card, missing = rv.verdict(reference, observed)
    summary = rv.summarize(reference, observed)
    epoch.record_verdict(state_dir, decision.verdict, missing)

    if decision.verdict == "RECOVERED":
        return ""  # the board is back; saying so every time is noise

    dims = "; ".join(f"{k}: {summary[k]}" for k in sorted(summary))
    return (
        f"[recovery] {decision.verdict} -- this workspace was interrupted at "
        f"{ep.get('interrupted_at')} and did not come back whole. Scored against the "
        f"topology pinned before the interruption ({ep.get('reference_file')}): {dims}. "
        f"Run `/lazarus all` to relaunch the missing panes, `python tools/recovery_verdict.py` "
        f"for the full receipt, or `python modules/session_resilience/epoch.py --dismiss` "
        f"if you do not want them back."
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SessionStart recovery gate")
    ap.add_argument("--state-dir", default=str(STATE_DIR))
    ap.add_argument("--live-terminals", type=int, default=None,
                    help="pass ONLY a real measurement; unmeasured is never zero")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    state = Path(a.state_dir)

    try:
        det = epoch.detect_interruption(state, live_terminal_count=a.live_terminals)
        if det.get("interrupted"):
            epoch.open_epoch(state, det)
        line = banner(state)
    except Exception as exc:  # noqa: BLE001 -- a SessionStart gate never blocks a session
        if a.json:
            print(json.dumps({"error": f"{exc.__class__.__name__}: {exc}"}))
        return 0

    if a.json:
        print(json.dumps({"interrupted": det.get("interrupted"),
                          "signals": det.get("signals"), "banner": line}, default=str))
    elif line:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
