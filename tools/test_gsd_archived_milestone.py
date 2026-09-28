#!/usr/bin/env python
"""V-ARCH-* gates for gsd_long_run.archived_milestone_complete (2026-09-28).

An archived, finished GSD milestone parses to 0 phases, and gsd_status read that as NO_PHASES,
so a finished mission could only end on budget (live: m-916e905e23d4). Completion now needs
positive evidence from GSD's own state.json; every other shape stays NO_PHASES."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

passes = fails = 0
MS = "v1 Demo"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def project(state) -> Path:
    d = Path(tempfile.mkdtemp(prefix="arch-"))
    (d / ".planning").mkdir()
    if state is not None:
        (d / ".planning" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return d


def main() -> int:
    done = {"milestone": MS, "phases": [{"number": "1", "status": "complete"},
                                        {"number": "2", "status": "complete"}]}
    a = lr.archived_milestone_complete
    check("V-ARCH-COMPLETE-SAME-MILESTONE", (a(project(done), MS) or "").startswith("milestone"),
          str(a(project(done), MS)))
    check("V-ARCH-OTHER-MILESTONE-STAYS-NO-PHASES", a(project(done), "v2 Next") is None)
    part = {"milestone": MS, "phases": [{"status": "complete"}, {"status": "in_progress"}]}
    check("V-ARCH-INCOMPLETE-PHASE-STAYS-NO-PHASES", a(project(part), MS) is None)
    check("V-ARCH-EMPTY-PHASES-STAYS-NO-PHASES", a(project({"milestone": MS, "phases": []}), MS) is None)
    check("V-ARCH-NO-STATE-FILE-STAYS-NO-PHASES", a(project(None), MS) is None)
    check("V-ARCH-WORKSTREAM-NOT-JUDGED", a(project(done), MS, workstream="ws1") is None)
    check("V-ARCH-NO-MILESTONE-NOT-JUDGED", a(project(done), None) is None)
    bad = project(None)
    (bad / ".planning" / "state.json").write_text("{not json", encoding="utf-8")
    check("V-ARCH-UNREADABLE-STAYS-NO-PHASES", a(bad, MS) is None)
    print(f"ARCH_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
