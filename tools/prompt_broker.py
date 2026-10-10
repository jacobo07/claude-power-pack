#!/usr/bin/env python
"""Prompt Broker (oic-v1 S3): a suspended background worker becomes a machine-readable request.

The host already says why a background job stopped (~/.claude/jobs/<short id>/state.json: `needs`,
`detail`, `tempo`); gsd_mission reads it (host_job_needs) but every shape becomes WAITING_HUMAN and
the Owner has to open the session to find out. This module classifies that text, writes one suspension
record per worker, and routes ONLY genuine human boundaries to the Owner decision queue, each with its
Proof of Human Necessity. Everything else gets a named machine resolution.

Classes:
  MECHANICAL                 the runtime can resolve it (run the command the worker asked the Owner to run,
                             rotate to a fresh session, fix a known setup dialog by preflight)
  EVENT_WAIT                 a timed event resolves it (rate limit reset); never a human question
  CAPITAL                    new token/money authority (Owner), unless goal_declare shows it is unprivileged
  HOST_HUMAN_PRESENCE        the host needs a person (login, an unknown setup dialog after preflight)
  GENUINE_HUMAN_BOUNDARY     judgment or an external account only the Owner holds
  OPAQUE_INTERACTIVE_BLOCKER the host says blocked but says nothing: an incident, never safe
  UNKNOWN_HIGH_RISK          text we cannot classify: safe stop + Owner packet

Read-only on missions and host state. Writes only ~/.claude/state/oic/suspensions.jsonl (and Owner
decisions through modules/owner_queue/decisions when --route is given). Kill switch: CPP_OIC=off.

    python tools/prompt_broker.py scan            # classify every live mission, print a table
    python tools/prompt_broker.py scan --record   # also append suspension records
    python tools/prompt_broker.py scan --record --route   # also queue genuine decisions
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MECHANICAL, EVENT_WAIT, CAPITAL = "MECHANICAL", "EVENT_WAIT", "CAPITAL"
PRESENCE, HUMAN, OPAQUE, UNKNOWN = ("HOST_HUMAN_PRESENCE", "GENUINE_HUMAN_BOUNDARY",
                                    "OPAQUE_INTERACTIVE_BLOCKER", "UNKNOWN_HIGH_RISK")

# Ordered: the first matching rule wins. Each rule names the machine resolution, so a MECHANICAL verdict
# always says what the runtime will do instead of asking.
RULES = [
    (re.compile(r"startup dialog|continue setup", re.I), MECHANICAL,
     "preflight: launch the worker with --strict-mcp-config (no project MCP prompt) after a measured bisect; "
     "if the host still shows a dialog -> one presence action"),
    (re.compile(r"weekly limit|rate.?limit|usage limit|resets? (at|on|in)\b", re.I), EVENT_WAIT,
     "wait for the reset; budget clock paused; resume the same session after reset"),
    (re.compile(r"context wall|start a new session|new session in", re.I), MECHANICAL,
     "rotate: the supervisor launches a fresh session with the rehydration card (Ralph relay)"),
    (re.compile(r"\brun\s+`[^`]+`", re.I), MECHANICAL,
     "the supervisor runs the quoted command itself and resumes the worker with its output"),
    (re.compile(r"login required|log ?in|authenticat|credential|api key", re.I), PRESENCE,
     "one Owner presence action (login); no new authority implied"),
    (re.compile(r"ad account|payment method|meta dataset|stripe|bank|legal|contract", re.I), HUMAN,
     "Owner decision with proof (external account)"),
    (re.compile(r"budget|\bcap\b|goal id|new goal|spend", re.I), CAPITAL,
     "capital packet; mechanical only if mission_spend.goal_declare accepts it unprivileged"),
    (re.compile(r"\breply\b|\baccept\b|\bapprove|human_needed|verification", re.I), HUMAN,
     "Owner decision with proof"),
]


def classify(needs: str | None, detail: str | None) -> dict:
    text = " ".join(x for x in (needs, detail) if x).strip()
    if not text:
        return {"class": OPAQUE, "resolution": "incident: host blocked with no reason; safe stop", "text": ""}
    for rx, cls, res in RULES:
        if rx.search(text):
            out = {"class": cls, "resolution": res, "text": text[:300]}
            if cls == EVENT_WAIT:
                m = re.search(r"resets?\s+(?:at|on)?\s*([A-Z][a-z]{2}\s+\d{1,2}[^·|]*)", text)
                out["reset"] = m.group(1).strip() if m else None
            if cls == MECHANICAL:
                m = re.search(r"\brun\s+`([^`]+)`", text)
                out["command"] = m.group(1) if m else None
            return out
    return {"class": UNKNOWN, "resolution": "safe stop + Owner packet", "text": text[:300]}


def _jobs_dir() -> Path:
    return Path(os.environ.get("CPP_CLAUDE_JOBS_DIR") or Path.home() / ".claude" / "jobs")


def _state_dir() -> Path:
    return Path(os.environ.get("GSD_LONG_RUN_STATE_DIR") or Path.home() / ".claude" / "state")


def live_missions() -> list[dict]:
    out = []
    for p in sorted(_state_dir().glob("gsd-mission-m-*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if r.get("state") in ("HALTED", "COMPLETED"):
            continue
        owner = r.get("owner") or {}
        out.append({"mission_id": r.get("mission_id") or p.stem.replace("gsd-mission-", ""),
                    "state": r.get("state"), "session_id": owner.get("session_id"), "cwd": r.get("cwd"),
                    "workstream": r.get("workstream")})
    return out


def job_state(session_id: str | None) -> dict:
    if not session_id:
        return {}
    try:
        d = json.loads((_jobs_dir() / str(session_id)[:8] / "state.json").read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def suspension(m: dict, now: float | None = None) -> dict | None:
    st = job_state(m["session_id"])
    blocked = st.get("state") == "blocked" or st.get("tempo") == "blocked" or bool(st.get("needs"))
    if not blocked:
        return None
    v = classify(st.get("needs"), st.get("detail"))
    return {"ts": now or time.time(), "mission_id": m["mission_id"], "session": (m["session_id"] or "")[:8],
            "cwd": m["cwd"], "workstream": m["workstream"], "host_state": st.get("state"),
            "host_updated": st.get("updatedAt"), **v}


def proof_for(s: dict) -> dict | None:
    """A Proof of Human Necessity for classes that may reach the Owner; None for the rest."""
    if s["class"] not in (CAPITAL, HUMAN, PRESENCE, UNKNOWN, OPAQUE):
        return None
    human = {CAPITAL: "capital", HUMAN: "preference", PRESENCE: "physical_presence",
             UNKNOWN: "new_scope", OPAQUE: "new_scope"}[s["class"]]
    return {"requested_decision": f"{s['mission_id']}: {s['text'][:160] or 'host blocked with no reason'}",
            "human_authority": human,
            "why_not_authority": "no authority grant covers this mission's request",
            "why_not_machinery": f"broker class {s['class']}: {s['resolution']}",
            "why_not_event_wait": "no timed event resolves it",
            "why_not_independent_work": "the worker is suspended on it; other missions continue",
            "blocks": s["mission_id"]}


def _record(rows: list[dict]) -> None:
    p = _state_dir() / "oic" / "suspensions.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def scan(record: bool = False, route: bool = False) -> list[dict]:
    rows = [s for s in (suspension(m) for m in live_missions()) if s]
    if record:
        _record(rows)
    if route:
        from modules.owner_queue import decisions
        for s in rows:
            pf = proof_for(s)
            if pf:
                s["routed"] = decisions.ask(f"mission-block:{s['mission_id']}:{s['class']}", pf,
                                            asker="prompt_broker")["status"]
    return rows


def main(argv=None) -> int:
    if os.environ.get("CPP_OIC", "").lower() == "off":
        print("CPP_OIC=off: prompt broker disabled")
        return 0
    ap = argparse.ArgumentParser(prog="prompt_broker")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scan")
    sc.add_argument("--record", action="store_true")
    sc.add_argument("--route", action="store_true")
    sc.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = scan(record=a.record, route=a.route)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['mission_id']} {r['session']} {r['class']:<26} | {r['text'][:70]} | -> {r['resolution'][:60]}")
        counts: dict[str, int] = {}
        for r in rows:
            counts[r["class"]] = counts.get(r["class"], 0) + 1
        print("TOTAL", len(rows), counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
