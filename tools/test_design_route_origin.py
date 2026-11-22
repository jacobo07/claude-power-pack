#!/usr/bin/env python3
"""V-DRO-*: the design route classifies what the Owner wrote, never machine-originated turns.

Incident (measured 2026-11-22 over ~/.claude/state/design_route/prompts.jsonl, 106 live routes): ~54 fired on text no
human typed -- subagent hand-backs (39), compaction-summary reminders (13), a skill body, a task notification -- and
ALL 44 `motion` routes were among them. Because the latest visual prompt sets the session's kinds, a hand-back that
said "trailer" re-routed a web session to motion: the Stop gate then demanded motion-promo and stopped judging app
source. Both poles through the real entrypoint (tools/design_route_prompt.py), hermetic state dir.
Run: python tools/test_design_route_origin.py   (exit 0 = all pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "tools" / "design_route_prompt.py"
STATE = os.path.join(tempfile.mkdtemp(prefix="v-dro-"), "state")
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-38s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:300]))


def route(sid: str, prompt: str):
    env = dict(os.environ, CPP_DESIGN_STATE_DIR=STATE, PYTHONIOENCODING="cp1252")
    r = subprocess.run([sys.executable, str(PROMPT)], input=json.dumps({"session_id": sid, "prompt": prompt}).encode(),
                       capture_output=True, env=env, timeout=60)
    return json.loads(r.stdout) if r.stdout.strip() else None


def kinds(sid: str) -> list:
    p = Path(STATE, sid + ".json")
    return json.loads(p.read_text(encoding="utf-8")).get("kinds", []) if p.exists() else []


HANDBACK = ('Another Claude session sent a message: <agent-message from="a1b2"> [Subagent hand-back] The text of the '
            'promo video is ready; the trailer cut runs 30 s.</agent-message>')
# The bytes the hook REALLY receives (captured live 2026-11-22, prompts.jsonl head of ts 1795369643): the payload starts at
# <agent-message>; "Another Claude session sent a message:" exists only in the transcript's rendering, so a fixture
# copied from the transcript (HANDBACK above) passed while every live hand-back routed (ts 1795368968).
HANDBACK_LIVE = ('<agent-message from="a246da8953f1d2d1f">\n[Subagent hand-back] The text below is the final report of a '
                 'subagent this session delegated to. The report follows:\n  Probe report: the landing page hero, the logo '
                 'wordmark, the promo trailer and the dashboard chart were all checked.\n</agent-message>')
SUMMARY = ("This session is being continued from a previous conversation that ran out of context. The summary below "
           "covers a launch film and a product video.")
REMINDER_ONLY = "<system-reminder>\n<tools-used-before-summary>Bash</tools-used-before-summary>\n</system-reminder>"
TASK = "<task-notification> <task-id>x</task-id> landing page render finished </task-notification>"
SKILL = "Base directory for this skill: C:\\skills\\design-taste-frontend  # Anti-Slop landing pages and dashboards"


def main() -> int:
    # positive pole: the Owner's own words still route, typed, pasted, or behind a leading reminder
    ok("V-DRO-OWNER-TYPED-ROUTES", route("o1", "hazme una landing page para un estudio de yoga") is not None
       and "web" in kinds("o1"), kinds("o1"))
    ok("V-DRO-OWNER-MOTION-ROUTES", route("o2", "quiero un video promo de 30 segundos") is not None
       and "motion" in kinds("o2"), kinds("o2"))
    ok("V-DRO-OWNER-PASTE-ROUTES", route("o3", '  <pasted_content id="x1">MISION: redisena la landing page</pasted_content>')
       is not None and "web" in kinds("o3"), kinds("o3"))
    ok("V-DRO-REMINDER-THEN-OWNER-ROUTES",
       route("o4", REMINDER_ONLY + "\nmejora el dashboard de la clinica") is not None and kinds("o4"), kinds("o4"))

    # negative pole: machine turns are silent AND leave the session's kinds untouched
    route("w1", "hazme una landing page para una cafeteria")
    before = kinds("w1")
    route("w1", HANDBACK)   # read the kinds right after the hand-back: a later machine turn must not mask a flip
    after_handback = kinds("w1")
    ok("V-DRO-MACHINE-KEEPS-SESSION-KINDS", before == ["web"] and after_handback == before, (before, after_handback))
    route("w3", "hazme una landing page para una panaderia")
    route("w3", HANDBACK_LIVE)
    ok("V-DRO-LIVE-HANDBACK-KEEPS-KINDS", kinds("w3") == ["web"], kinds("w3"))
    silent = [name for name, text in (("handback", HANDBACK), ("handback_live", HANDBACK_LIVE), ("summary", SUMMARY), ("reminder", REMINDER_ONLY),
                                      ("task", TASK), ("skill", SKILL)) if route("w2", text) is not None]
    ok("V-DRO-MACHINE-TURNS-SILENT", not silent, silent)

    failed = [n for n, c in RESULTS if not c]
    print("V-DRO: %d passed, %d failed" % (len(RESULTS) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
