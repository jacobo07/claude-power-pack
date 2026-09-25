#!/usr/bin/env python3
"""UWCP Golden 08 on REAL data (LOCAL_REALITY): FP-028's negative knowledge survives.

Declares the KSR P2-W25 FP-028 investigation as a durable Workstream (goal log
under ~/.claude/state/gsd-x, never inside the KSR repo -- this touches no KSR
file) and records its hypotheses from the committed evidence file, quoting it and
citing it by path and section. Then a SEPARATE process, holding nothing but the
goal log, compiles the successor brief; the check is that the brief carries both
refuted hypotheses with their refutations, the established fact, and the open
question -- i.e. a successor would not re-walk the ruled-out paths.

Idempotent: re-running adopts the existing goal and records only what is missing.
Evidence class: LOCAL_REALITY (real evidence, real goal store, this host). The
remote and model-substitution halves of Golden 08/11 are owed in S6.

    python tools/uwcp_golden08_fp028.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import evidence as ev     # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402

WT = Path(os.environ.get("UWCP_FP028_WT", r"C:\Users\User\AppData\Local\Temp\ksr_p2w25\parent"))
EVID = ".ksr_vault/evidence/P2_W25_FP028_SEQUENCER_STATIC_20260924.md"
GOAL = "ksr-p2w25-fp028"
ACTOR = "uwcp-golden08-import"

INTENT = ("P2 W25 -- FP-028, static: the card sequencer at card+0x64, and who starts it. "
          f"(Imported verbatim from the title of {EVID}; status there: INTERIM.)")
ACCEPTANCE = ["Identify which of the 12 callers of 0x801F5E54 is on the GameSelect card path, "
              "by a static trace (evidence section 4.1)"]
CONSTRAINTS = ["Static first: any runtime spend waits for HOPPER_100 to release the GEX44 "
               "lease (Owner decision 2026-09-24, Option A; evidence line 65)",
               "Never commit, transport or overwrite the foreign uncommitted edit in "
               "tools/keos/autopilot.py (RESUME:14-15)"]
SCOPE = {"paths": ["tools/frontend_re/fp028", ".ksr_vault/evidence"]}

HYPOTHESES = [
    ("H-FP028-PLAYPAIR",
     "The framework play pair 0x80277984/0x802779DC is reached through our card's +0x94 owner",
     ev.REJECTED, [], [f"{EVID}#3 (absent from vtable 0x806BF618; 21 vtables each, virtual only)"]),
    ("H-FP028-VT74",
     "One of the card-range vt[0x74] request sites 0x801F5954/0x801FB060/0x802297AC is the "
     "card's own request path",
     ev.REJECTED, [], [f"{EVID}#3 (each sits in vtable 0x806B6284/0x806B67CC/0x806B821C, "
                       "none is 0x806BF5A0)"]),
    ("H-FP028-STARTER-REQUESTS",
     "0x801F5E54 requests state card+0xFC on the sequencer at card+0x64 that the guard reads",
     ev.ESTABLISHED, [f"{EVID}#2 (disassembly 801f5e90..801f5e98, capstone 5.0.7)"], []),
    ("H-FP028-GAMESELECT-CALLER",
     "One of the 12 callers of 0x801F5E54 starts the card sequencer on the GameSelect path",
     ev.OPEN, [], []),
]


def main() -> int:
    if not (WT / EVID).is_file():
        print(f"HARNESS-FAILED: evidence file not found at {WT / EVID}")
        return 2
    repo = gl.repo_id(WT)
    lg = gl.GoalLog(repo, GOAL)
    if not lg.exists():
        gc.declare(lg, INTENT, ACCEPTANCE, CONSTRAINTS, SCOPE, actor=ACTOR)
        print(f"declared goal {GOAL} in repo {repo[:12]}")
    else:
        print(f"adopted existing goal {GOAL} (seq {gc.project(lg).last_seq})")
    for hid, text, status, sup, con in HYPOTHESES:
        have = ev.project_hypotheses(gc.project(lg)).get(hid)
        if have is None or have.status != status:
            ev.record(lg, gc.project(lg), hid, text, status, ACTOR,
                      supporting=sup, contradicting=con)
            print(f"recorded {hid} -> {status}")

    # The successor: a fresh interpreter that knows only the goal id and repo id.
    probe = (
        "import sys; sys.path.insert(0, r'%s');"
        "from modules.gsd_x.goal import log as gl, contract as gc, brief as b;"
        "s = gc.project(gl.GoalLog('%s', '%s'));"
        "print(b.compile_brief(s, [], r'%s', 'continue the static trace'))"
    ) % (ROOT, repo, GOAL, WT)
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                         timeout=120, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    brief = out.stdout
    checks = {
        "V-UWCP-G08-BRIEF-COMPILED": out.returncode == 0 and len(brief) > 200,
        "V-UWCP-G08-REJECTED-PLAYPAIR": "[H-FP028-PLAYPAIR]" in brief and "0x806BF618" in brief,
        "V-UWCP-G08-REJECTED-VT74": "[H-FP028-VT74]" in brief and "0x806BF5A0" in brief,
        "V-UWCP-G08-DO-NOT-RETRY": "do NOT retry" in brief,
        "V-UWCP-G08-ESTABLISHED": "[H-FP028-STARTER-REQUESTS]" in brief.split("## Established")[-1],
        "V-UWCP-G08-CONSTRAINTS": "HOPPER_100" in brief and "autopilot.py" in brief,
        "V-UWCP-G08-SIZE": 0 < len(brief.encode("utf-8")) < 16_000,
    }
    for g, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'} {g}")
    if out.returncode != 0:
        print(out.stderr[-800:])
    print(f"brief bytes={len(brief.encode('utf-8'))}")
    passed = sum(checks.values())
    print(f"UWCP_GOLDEN08_FP028_PASS={passed}/{len(checks)}  (LOCAL_REALITY)")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
