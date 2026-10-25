#!/usr/bin/env python
"""V-W3A-* gates: the worker card shows live mission spend. Hermetic: no transcripts are read."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="w3a-card-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def rec(**extra):
    r = {"mission_id": "m-w3atest", "epoch": 2, "cwd": TMP, "resume_command": "/gsd-autonomous",
         "note": "n"}
    r.update(extra)
    return r


def boom(_rec):
    raise RuntimeError("no transcript")


def line_ok(card):
    return any(l.startswith("LIVE SPEND (measured") and "400,000" in l and "authority 1,000,000" in l
               for l in card.splitlines())


def main() -> int:
    card = gm.render_card(rec(authority_tokens=1_000_000), spend_fn=lambda r: 400_000)
    check("V-W3A-LINE", line_ok(card))
    bad = gm.render_card(rec(authority_tokens=1_000_000), spend_fn=boom)
    check("V-W3A-UNMEASURED", "LIVE SPEND: UNMEASURED" in bad and "LIVE SPEND (measured" not in bad)
    none = gm.render_card(rec(), spend_fn=lambda r: 400_000)
    check("V-W3A-NO-AUTHORITY", "LIVE SPEND" not in none)
    check("V-W3A-ORDER", 0 <= card.find("LIVE SPEND") < card.find("Predecessor's note"))
    mutated = "\n".join(l for l in card.splitlines() if not l.startswith("LIVE SPEND"))
    check("V-W3A-MUTATION-RED", line_ok(card) and not line_ok(mutated))
    print(f"W3A_PASS={passes}/{passes + fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
