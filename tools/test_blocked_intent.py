#!/usr/bin/env python
"""V-BI-* gates: a BLOCKED worker's "host needs:" text becomes a typed intent (A2).

Strings 1-4 are the real host-needs texts recorded on the TB-FULL missions on 2026-10-18; the command ask is a
constructed control (the 4.6 h block's own text was not kept). Each refusal has a paired control where the
fact exists and the other answer is given. The mutation drill makes a decision lose to a command."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="blocked-intent-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocked_intent as bi  # noqa: E402
import gsd_mission as gm  # noqa: E402

NOW = 1_800_000_000.0
alive = lambda pid: True   # noqa: E731


class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def supervised_block(mid, needs):
    """A RUNNING background mission whose host row says blocked, supervised once with the host's ask `needs`."""
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
    hs = [{"sessionId": f"s-{mid}", "status": "waiting", "waitingFor": "owner", "state": "blocked",
           "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]
    stops, launches = [], []
    real = gm.host_job_needs
    gm.host_job_needs = lambda sid: needs
    try:
        gm.supervise(now=NOW, sessions=hs, gsd_status=lambda c, workstream=None: {"outcome": "OK", "reason": "ok"},
                     runner=lambda argv, cwd: launches.append(argv) or R("backgrounded · 9e9e9e9e · x"),
                     stop_runner=lambda argv: stops.append(argv) or R("stopped"), pid_alive=alive)
    finally:
        gm.host_job_needs = real
    return gm.load(mid)

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


SCOPE = ("Owner scope decision accepting 'components proven, composed build unproven', or a target for the five "
         "visual candidates")
IMAGES = ("Supply target images (kitten reshape, Jacobo hair) or a new offline lead; then run "
          "tools/lanes/canary_spend.py with the session id to check the token meter")
CHOOSE3 = "Choose 1 (accept with debt), 2 (give new leads or target images), or 3 (resync GSD bookkeeping only)"
CHOOSE_RUN = "Choose: run Jacobo tuning slot, close out now, or explain kitten UV-rewrite offline first"
COMMAND = "Run /gsd-autonomous in this session so I can continue"
MIXED = "Choose 1 or run /compact"
SUPPLIED = ["OWNER INPUT: the kitten target image is now at /home/kobii/missions/tb-m2/owner-refs/kitten_reference.png"]


def main() -> int:
    for gate, text in (("SCOPE", SCOPE), ("CHOOSE3", CHOOSE3), ("CHOOSE-RUN", CHOOSE_RUN)):
        check(f"V-BI-{gate}-IS-DECISION", bi.classify(text) == bi.DECISION and
              bi.intent(text)["action"] == "ESCALATE_OWNER")
    check("V-BI-IMAGES-IS-RESOURCE", bi.classify(IMAGES) == bi.RESOURCE)
    check("V-BI-IMAGES-UNSUPPLIED-ESCALATES", bi.intent(IMAGES, [])["action"] == "ESCALATE_OWNER")
    check("V-BI-IMAGES-SUPPLIED-REPOINTS", bi.intent(IMAGES, SUPPLIED)["action"] == "REPOINT",
          "same ask, files already given: the control of the refusal above")
    c = bi.intent(COMMAND)
    check("V-BI-COMMAND-GETS-STANDING-ANSWER", c["kind"] == bi.COMMAND and c["action"] == "ANSWER_STANDING"
          and "no one will run a command" in c["answer"])
    check("V-BI-DECISION-OUTRANKS-COMMAND", bi.classify(MIXED) == bi.DECISION)
    # real: m-66ebaaa0324e, 2026-09-28; a login gate holds the host, no standing answer opens it
    LOGIN = "login required — run /login"
    check("V-BI-LOGIN-IS-HOST-GATE-NOT-COMMAND", bi.classify(LOGIN) == bi.HOST_GATE
          and bi.intent(LOGIN)["action"] == "ESCALATE_OWNER" and bi.intent(LOGIN)["answer"] is None)
    check("V-BI-EMPTY-IS-UNKNOWN-ESCALATES", bi.classify("") == bi.UNKNOWN and bi.classify(None) == bi.UNKNOWN
          and bi.intent(None)["action"] == "ESCALATE_OWNER")
    check("V-BI-NEVER-ANSWERS-A-DECISION", all(bi.intent(t, SUPPLIED)["answer"] is None for t in (SCOPE, CHOOSE3, CHOOSE_RUN)))
    # supervise end to end: the ask is typed on the record and the ledger; only a command ask is answered
    rd = supervised_block("m-bi", CHOOSE3)
    check("V-BI-SUPERVISE-TYPES-A-DECISION", rd["state"] == gm.BLOCKED
          and (rd.get("blocked_intent") or {}).get("kind") == bi.DECISION
          and (rd.get("blocked_intent") or {}).get("action") == "ESCALATE_OWNER", str(rd.get("blocked_intent"))[:120])
    check("V-BI-SUPERVISE-LEDGERS-IT", any(e.get("event") == "blocked_intent" and e.get("kind") == bi.DECISION
                                           for e in gm.lr.ledger_events("m-bi")))
    check("V-BI-SUPERVISE-NEVER-ANSWERS-A-DECISION", not (rd.get("directives") or []) and not rd.get("wake_expect"),
          "no directive, no wake stamp")
    rc = supervised_block("m-bc", COMMAND)
    check("V-BI-SUPERVISE-ANSWERS-A-COMMAND", (rc.get("blocked_intent") or {}).get("action") == "ANSWER_STANDING"
          and any("no one will run a command" in d for d in (rc.get("directives") or [])),
          str(rc.get("directives"))[:120])
    real = bi._DECISION
    bi._DECISION = re.compile(r"(?!)")
    try:
        mutant_ok = bi.classify(MIXED) == bi.DECISION
    finally:
        bi._DECISION = real
    check("V-BI-MUTATION-RED", not mutant_ok, "decision regex off: a mixed ask is answered as a command")
    print(f"BI_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
