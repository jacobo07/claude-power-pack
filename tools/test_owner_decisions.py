#!/usr/bin/env python
"""V-OD-* gates for Owner decisions with a Proof of Human Necessity (modules/owner_queue/decisions.py).

Hermetic (temp dirs set before import). Each refusal has a control in which a complete, human proof is
queued, so a module that refuses everything cannot go green.
Mutation drill: DECISIONS_DRILL_DIR = a tree holding a mutated modules/owner_queue/decisions.py.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="owner-decisions-test-")
os.environ["CPP_OWNER_DECISIONS_DIR"] = TMP
os.environ["CPP_AUTHORITY_DIR"] = TMP
os.environ["CPP_AUTONOMY_RECEIPTS"] = str(Path(TMP) / "decisions-audit.jsonl")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.environ.get("DECISIONS_DRILL_DIR") or str(ROOT))
from modules.owner_queue import decisions as od  # noqa: E402
from modules.autonomy_gate import grants  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def incidents() -> list[str]:
    p = Path(TMP) / "owner-interface-incidents.jsonl"
    return [json.loads(x)["kind"] for x in p.read_text(encoding="utf-8").splitlines()] if p.is_file() else []


PROOF = {"requested_decision": "Raise the ukai goal cap by 3M tokens?",
         "human_authority": "capital",
         "why_not_authority": "no grant carries capital for ukai",
         "why_not_machinery": "a cap raise needs mission_spend --owner, which agents cannot call",
         "why_not_event_wait": "no event refills a spent cap",
         "why_not_independent_work": "ukai has no other runnable unit",
         "blocks": "m-2f45a4047992"}

r = od.ask("capital:ukai:+3M", PROOF, asker="sweep", options=["raise 3M", "stop"], safe_default="stop", now=NOW)
check("V-OD-HUMAN-QUEUED-CONTROL", r["status"] == "queued", str(r))
r2 = od.ask("capital:ukai:+3M", PROOF, asker="pane-2", now=NOW + 5)
check("V-OD-DEDUP-SUBSCRIBES", r2["status"] == "subscribed" and r2["id"] == r["id"], str(r2))
check("V-OD-ONE-PENDING-PER-KEY", len(od.pending()) == 1 and od.load()[r["id"]]["subscribers"] == ["sweep", "pane-2"])

bad = dict(PROOF, why_not_event_wait="")
r = od.ask("capital:x", bad, asker="w", now=NOW)
check("V-OD-MISSING-PROOF-REFUSED", r["status"] == "refused" and r["incident"] == "MISSING_PROOF", str(r))
r = od.ask("open-session:33e4114b", dict(PROOF, human_authority="mechanical"), asker="sweep", now=NOW)
check("V-OD-MECHANICAL-REFUSED", r["status"] == "refused" and r["incident"] == "MECHANICAL_OWNER_ESCALATION", str(r))
check("V-OD-REFUSALS-NEVER-QUEUED", len(od.pending()) == 1)

# A question already covered by a live grant is redundant; with no grant the same question is queued.
SHA = "a" * 40
gid = grants.grant({"programme": "t", "level": 3, "provenance": {"reply": "y"}, "effects": ["pr.merge"],
                    "targets": {"pr": "545", "head_sha": SHA}, "expires_at": NOW + 3600}, now=NOW)
mk = dict(PROOF, requested_decision="Merge #545?", human_authority="irreversible", blocks="release-545")
r = od.ask("merge:545", mk, asker="release_tx", effect="pr.merge", target={"pr": "545", "head_sha": SHA}, now=NOW)
check("V-OD-REDUNDANT-PROMPT-REFUSED", r["status"] == "refused" and r["incident"] == "REDUNDANT_OWNER_PROMPT", str(r))
r = od.ask("merge:545:new-sha", mk, asker="release_tx", effect="pr.merge",
           target={"pr": "545", "head_sha": "b" * 40}, now=NOW)
check("V-OD-CHANGED-SHA-GOES-TO-OWNER-CONTROL", r["status"] == "queued", str(r))
check("V-OD-INCIDENTS-RECORDED",
      incidents() == ["MISSING_PROOF", "MECHANICAL_OWNER_ESCALATION", "REDUNDANT_OWNER_PROMPT"], str(incidents()))

# Decision cache: an answered question is reused, never re-asked; a withdrawn one is asked again.
check("V-OD-DECIDE", od.decide("capital:ukai:+3M", "raise 3M", now=NOW + 60))
r = od.ask("capital:ukai:+3M", PROOF, asker="pane-3", now=NOW + 70)
check("V-OD-ANSWER-REUSED", r["status"] == "answered" and r["answer"] == "raise 3M", str(r))
od.withdraw("capital:ukai:+3M", "cap changed by another route", now=NOW + 80)
r = od.ask("capital:ukai:+3M", PROOF, asker="pane-3", now=NOW + 90)
check("V-OD-WITHDRAWN-REASKED", r["status"] == "queued", str(r))

# Decision parallelism: only the declared closure is blocked.
check("V-OD-BLOCKS-ONLY-CLOSURE",
      od.blocked("m-2f45a4047992") and not od.blocked("m-c74a2125495b") and od.blocked("release-545"),
      f"{od.blocked('m-2f45a4047992')} / {od.blocked('m-c74a2125495b')}")

check("V-OD-SEPARATE-NAMESPACE", not (Path(TMP) / "OWNER_QUEUE.jsonl").exists()
      and (Path(TMP) / "OWNER_DECISIONS.jsonl").is_file())

print(f"OWNER_DECISIONS_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
