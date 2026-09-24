"""V-TINH-* -- every build feeds the Tower, and every repo receives it.

C1 (capture): a repo's landed commits reach the PM-03 bus with nobody running
`--stage`, only the repo's own commits reach it, and the FD-07 cap bounds NEW
work instead of starving the tail behind an already-deposited head.

Hermetic: every bus, ledger and learnings dir lives under a temp root. The real
~/.claude/state is never read or written.

Run: python tools/test_tower_inheritance.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.parallel_mesh import pm_03_bus as pm  # noqa: E402
from modules.fable_distillation import fd_07_flywheel as fd  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate: str, cond: bool, evidence: str, diagnostic: str) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-36s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-36s %s" % (gate, diagnostic))


LEARNING = """# Session Delta -- synthetic -- 2026-09-24

## What Worked

- Landed `ce52726 World producers put the eye on the ground: Pos is eye height`
- Landed `549fa37 Recover stranded commits: seven proven units that never came home`
- Uncommitted (not landed) `.claude/cache/learnings/x.md`

## What Failed

- 9 OWNER_QUEUE residual(s) still pending:
  - Activate recovery graceful-beacon  (SCS C83)
"""


def _claim(i: int) -> str:
    return "alpha%d bravo%d charlie%d delta%d echo%d foxtrot%d" % ((i,) * 6)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="tower_inheritance_gate_")
    try:
        print("V-TINH gates (C1 capture)")
        repo = os.path.join(tmp, "repo")
        learn = os.path.join(repo, ".claude", "cache", "learnings")
        os.makedirs(learn)
        with open(os.path.join(learn, "2026-09-24_aaaa.md"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(LEARNING)
        bus_dir = os.path.join(tmp, "bus")

        n = pm.harvest_session_deltas(repo, state_dir=bus_dir)
        got = pm.FindingsBus(state_dir=bus_dir).load(repo)
        claims = [f.claim for f in got]
        _check("V-TINH-HARVEST-LANDED", n == 2 and len(got) == 2,
               "2 landed commits published without --stage",
               "expected 2, harvested=%d bus=%d" % (n, len(got)))
        _check("V-TINH-HARVEST-REPO-ONLY",
               not any("OWNER_QUEUE" in c or "beacon" in c or "Uncommitted" in c
                       for c in claims),
               "no PP residual and no uncommitted path on the bus",
               "foreign lines leaked onto the bus: %s" % claims)
        _check("V-TINH-HARVEST-CAUSAL-COMMIT",
               all(f.evidence.startswith("commit ") for f in got)
               and any("ce52726" in f.evidence for f in got),
               "evidence names the causal commit",
               "evidence lost the commit: %s" % [f.evidence for f in got])

        again = pm.harvest_session_deltas(repo, state_dir=bus_dir)
        _check("V-TINH-HARVEST-IDEMPOTENT",
               again == 0 and len(pm.FindingsBus(state_dir=bus_dir).load(repo)) == 2,
               "second harvest appends nothing",
               "re-harvest appended %d" % again)

        bare = os.path.join(tmp, "bare")
        os.makedirs(bare)
        _check("V-TINH-HARVEST-NO-DIR",
               pm.harvest_session_deltas(bare, state_dir=bus_dir) == 0
               and not os.path.exists(pm.FindingsBus(state_dir=bus_dir).path_for(bare)),
               "no learnings dir -> 0 and no bus file created",
               "a repo with nothing to harvest grew a bus file")

        # --- THE LINK: the Stop path harvests by itself -----------------------
        # No findings injected: run_flywheel reads through _session_findings,
        # the path the Stop hook takes. Only the bus's default root is moved,
        # so the real ~/.claude/state is untouched.
        from pathlib import Path
        real_default = pm._default_state_dir
        link_bus = os.path.join(tmp, "link_bus")
        pm._default_state_dir = lambda: Path(link_bus)
        try:
            res_link = fd.run_flywheel(repo, sid="gate",
                                       state_dir=os.path.join(tmp, "link_led"),
                                       record=False)
        finally:
            pm._default_state_dir = real_default
        _check("V-TINH-FD07-HARVESTS-ITSELF", res_link.deposited == 2,
               "Stop path deposited the 2 landed commits with nothing staged",
               "fd_07 did not harvest: deposited=%d note=%r"
               % (res_link.deposited, res_link.note))

        # --- the cap bounds NEW work, not history ----------------------------
        led = os.path.join(tmp, "ledger")
        head = [{"topic": "t", "claim": _claim(i)} for i in range(30)]
        fd.run_flywheel(repo, findings=head, state_dir=led, record=False,
                        max_findings=30)
        tail = head + [{"topic": "t", "claim": _claim(100 + i)} for i in range(3)]
        res = fd.run_flywheel(repo, findings=tail, state_dir=led, record=False,
                              max_findings=25)
        _check("V-TINH-CAP-REACHES-TAIL",
               res.deposited == 3 and res.dup == 30 and not res.truncated,
               "3 new tail findings deposited behind 30 known ones (cap 25)",
               "tail starved: deposited=%d dup=%d truncated=%s"
               % (res.deposited, res.dup, res.truncated))

        # Positive control: the cap still bounds genuinely NEW work.
        led2 = os.path.join(tmp, "ledger2")
        fresh = [{"topic": "t", "claim": _claim(200 + i)} for i in range(30)]
        res2 = fd.run_flywheel(repo, findings=fresh, state_dir=led2, record=False,
                               max_findings=25)
        _check("V-TINH-CAP-STILL-BOUNDS-NEW",
               res2.truncated and res2.deposited == 25 and "5 finding" in res2.note,
               "30 new -> 25 deposited, 5 deferred and said so",
               "cap no longer bounds new work: deposited=%d note=%r"
               % (res2.deposited, res2.note))

        print()
        print("TOWER_INHERITANCE_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
