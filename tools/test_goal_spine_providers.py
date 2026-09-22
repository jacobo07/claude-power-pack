#!/usr/bin/env python3
"""V-gates for the worker provider's preflight and instruction.

The preflight is driven through `/cpp-gsd-long`'s OWN seam (`_TEST_GSD_STATUS`,
read by `gsd_long_run.gsd_status`), not through a mock of it, so these gates
exercise the real vocabulary -- OK / NO_PHASES / ALL_COMPLETE / UNAVAILABLE --
and would fail if that vocabulary changed under us.

The distinction that matters: UNAVAILABLE means we could not ASK, and is never
read as "no phases". They need different fixes, and a preflight that merged them
would send a human to restructure a roadmap when the real problem is a missing
node binary.

    python tools/test_goal_spine_providers.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-prov-")

from modules.goal_spine import epoch as ep_                    # noqa: E402
from modules.goal_spine import goal as gl                      # noqa: E402
from modules.goal_spine.providers import gsd_long              # noqa: E402

_n = [0]


def _goal(with_planning: bool) -> gl.Goal:
    _n[0] += 1
    root = Path(tempfile.mkdtemp(prefix="prov-root-"))
    if with_planning:
        (root / ".planning").mkdir()
    return gl.declare(str(root), f"Provider goal {_n[0]}.", ["DO-1"],
                      [{"id": "i", "text": "t"}])


def main() -> int:
    passes, fails = [], []

    def check(name, cond, ev):
        (passes if cond else fails).append(name)
        print(f"  {'OK  ' if cond else 'FAIL'} {name}  {ev}")

    # --- a root with no .planning is named before a pane is spent on it ------
    g = _goal(with_planning=False)
    os.environ["_TEST_GSD_STATUS"] = json.dumps({"outcome": "OK", "reason": "3/5 phases"})
    pf = gsd_long.preflight(g)
    check("V-PROV-NO-PLANNING-IS-NAMED",
          not pf.ok and any(".planning" in f for f in pf.findings), pf.findings[0][:80])

    # --- the four outcomes, each distinct ------------------------------------
    g = _goal(with_planning=True)
    results = {}
    for outcome, reason in (("OK", "3/5 phases complete"),
                            ("NO_PHASES", "GSD parses 0 phases from ROADMAP.md"),
                            ("ALL_COMPLETE", "5/5 phases complete"),
                            ("UNAVAILABLE", "node or gsd-tools.cjs not found")):
        os.environ["_TEST_GSD_STATUS"] = json.dumps({"outcome": outcome, "reason": reason})
        results[outcome] = gsd_long.preflight(g)
    check("V-PROV-PREFLIGHT-OK-ONLY-WHEN-GSD-HAS-WORK",
          results["OK"].ok and not results["NO_PHASES"].ok
          and not results["ALL_COMPLETE"].ok and not results["UNAVAILABLE"].ok,
          "OK passes; no-phases, all-complete and unavailable each refuse")
    check("V-PROV-COULD-NOT-ASK-IS-NOT-NO-PHASES",
          "could not ask GSD" in results["UNAVAILABLE"].findings[0]
          and "could not ask" not in results["NO_PHASES"].findings[0],
          "UNAVAILABLE and NO_PHASES do not share a sentence")
    check("V-PROV-ALL-COMPLETE-EXPLAINS-THE-REFUSAL",
          "nothing left to run" in results["ALL_COMPLETE"].findings[0]
          and "milestone" in results["ALL_COMPLETE"].findings[0],
          "an exhausted milestone names what the Goal needs instead")

    # --- the instruction is addressed to a human, and starts nothing --------
    os.environ["_TEST_GSD_STATUS"] = json.dumps({"outcome": "OK", "reason": "1/4"})
    e = ep_.prepare(g, "gsd_long", ["DO-1"], "state", command="/gsd-autonomous", cwd=g.root)
    text = gsd_long.instruction(g, e)
    check("V-PROV-INSTRUCTION-IS-CLAIM-THEN-RUN",
          e.epoch_id in text and g.root in text and "/gsd-autonomous" in text
          and "claim" in text and "does not arm" in text,
          "names the epoch, the root, the claim step, and says the spine arms nothing")

    src = Path(gsd_long.__file__).read_text(encoding="utf-8")
    check("V-PROV-WORKER-PROVIDER-WRITES-NO-MARKER",
          "gsd_autorun_marker" not in src.split('"""')[2],
          "no marker call outside the docstring that explains why there is none")

    total = len(passes) + len(fails)
    print(f"\nGOAL_PROVIDERS_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
