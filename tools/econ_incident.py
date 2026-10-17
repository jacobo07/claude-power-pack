"""Economic incident receipts (mission-authority programme A2, 2026-10-15).

A cost hold used to be a ledger row nobody read: m-ce2bacd4cbb0 spent 83.8M of a 45M authority and the overrun was
found by a person asking for status. Every cost hold now leaves a receipt a reader can act on without the transcript:
`<state>/economic-incidents/<mission>-<ts>.json` plus one line in `index.jsonl`, and `open_incidents()` feeds
`gsd_mission.py status`, so the next status read shows the incident before anything else.

The receipt never decides anything: the hold already stopped new work (hooks/lib/mission_gate.js denies every tool
call of a cost-held worker). It records what was spent, against which authority, why, and the next safe action.
UNKNOWN stays UNKNOWN: an unmeasurable spend is written as null with the error, never as 0.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

LEVELS = (
    ("MISSION_AUTHORITY", re.compile(r"cost breaker \(mission authority\)")),
    ("PHASE_LEASE", re.compile(r"cost breaker \(phase lease\)")),
    ("STALL", re.compile(r"since the work tree last changed")),
    ("DEFAULT_CEILING", re.compile(r"default policy ceiling")),   # before ESTIMATE_RATIO: its text also says "x estimate"
    ("ESTIMATE_RATIO", re.compile(r"x estimate")),
)


def state_dir() -> Path:
    return Path(os.environ.get("GSD_LONG_RUN_STATE_DIR") or Path.home() / ".claude" / "state")


def incident_dir() -> Path:
    return state_dir() / "economic-incidents"


def classify(reason: str) -> str:
    for level, rx in LEVELS:
        if rx.search(reason or ""):
            return level
    return "OWNER_HOLD_COST"


def _next_action(level: str) -> str:
    if level == "MISSION_AUTHORITY":
        return ("closeout only; reforecast the residual from measured cost, then ask the Owner for new authority "
                "or keep the mission parked")
    if level == "PHASE_LEASE":
        return "closeout only; reforecast the phase from measured cost before any release"
    if level == "STALL":
        return "inspect why spend outran progress; recompile the work unit before any release"
    if level == "DEFAULT_CEILING":
        return ("the default allowance is spent and no Owner authority exists; declare authority with "
                "`gsd_mission.py authority --tokens N`, then release, or keep the mission parked")
    return "explain the variance against the estimate and recompute the remaining work before release"


def record(rec: dict, reason: str, now: float | None = None, spent: int | None = None, measure=None) -> dict:
    """Write the receipt for a cost hold just set on `rec`. Returns the receipt. Never raises to the caller's
    hold path: a write failure is returned in the receipt's `error`, and the hold itself stands."""
    now = time.time() if now is None else now
    mid = str(rec.get("mission_id") or "unknown")
    level = classify(reason)
    err = None
    if spent is None:
        try:
            if measure is None:
                import mission_spend as ms
                measure = ms.processed_tokens
            spent = measure(rec)
        except Exception as exc:  # noqa: BLE001 -- recorded in the receipt, never silent
            err = f"{type(exc).__name__}: {exc}"[:300]
            spent = None
    auth = rec.get("authority_tokens")
    est = rec.get("token_estimate")
    receipt = {
        "schema": "economic-incident/1",
        "mission_id": mid,
        "goal": rec.get("goal"),
        "workstream": rec.get("workstream"),
        "level": level,
        "reason": (reason or "")[:1000],
        "at": now,
        "at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "authority_tokens": int(auth) if auth else None,
        "token_estimate": int(est) if est else None,
        "authority_kind": ("OWNER" if auth else "DEFAULT_POLICY" if rec.get("token_estimate_src") == "auto"
                           else "OPERATOR_ESTIMATE"),
        "spent": spent,
        "spent_error": err,
        "overshoot": (spent - int(auth)) if (spent is not None and auth) else None,
        "epoch": rec.get("epoch"),
        "worker": (rec.get("owner") or {}).get("session_id"),
        "head": (rec.get("binding") or {}).get("head"),
        "action_taken": "owner hold (kind=cost): relay refused; in-turn tool calls of the worker and its subagents denied",
        "next_safe_action": _next_action(level),
        "acknowledged": False,
    }
    try:
        d = incident_dir()
        d.mkdir(parents=True, exist_ok=True)
        name = f"{mid}-{int(now)}.json"
        tmp = d / (name + f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
        os.replace(tmp, d / name)
        with open(d / "index.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"file": name, "mission_id": mid, "level": level, "at": now, "spent": spent,
                                 "authority_tokens": receipt["authority_tokens"]}, separators=(",", ":")) + "\n")
        receipt["file"] = str(d / name)
    except OSError as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return receipt


def acknowledge(path: str) -> dict:
    p = Path(path)
    r = json.loads(p.read_text(encoding="utf-8"))
    r["acknowledged"] = True
    r["acknowledged_at"] = time.time()
    tmp = p.with_suffix(p.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(r, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return r


def open_incidents(limit: int = 20) -> list[dict]:
    """Unacknowledged receipts, newest first. An unreadable receipt is listed as such, never skipped."""
    d = incident_dir()
    out = []
    if not d.is_dir():
        return out
    for p in sorted(d.glob("m-*.json"), key=lambda q: q.stat().st_mtime, reverse=True):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            out.append({"file": str(p), "error": f"unreadable: {type(exc).__name__}"})
            continue
        if not r.get("acknowledged"):
            r["file"] = str(p)
            out.append(r)
        if len(out) >= limit:
            break
    return out


def status_lines(limit: int = 5) -> list[str]:
    lines = []
    for r in open_incidents(limit):
        if r.get("error"):
            lines.append(f"ECONOMIC INCIDENT (unreadable): {r['file']}")
            continue
        sp = "UNKNOWN" if r.get("spent") is None else f"{r['spent']:,}"
        au = "-" if r.get("authority_tokens") is None else f"{r['authority_tokens']:,}"
        lines.append(f"ECONOMIC INCIDENT {r['level']} {r['mission_id']} spent {sp} / authority {au} at {r['at_iso']}: "
                     f"{r['next_safe_action']} [{r['file']}]")
    return lines


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="economic incident receipts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("ack")
    a.add_argument("file")
    args = ap.parse_args()
    if args.cmd == "list":
        print("\n".join(status_lines(50)) or "no open economic incidents")
    else:
        print(json.dumps(acknowledge(args.file), indent=1))
