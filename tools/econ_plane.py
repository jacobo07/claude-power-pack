"""Economic recovery / egress plane (econ-contain, vault/plans/econ-containment-2026-10-10.md).

The mechanism that gets a session out of an exhausted goal must not depend on that goal's remaining
authority. This module is that mechanism, and it is model-free: every answer is folded from the
GoalLedger journal and the session's binding records, so asking "what happened / what next" after a
goal hit its cap costs no model boundary when it is reached from hooks/econ_admission.js (an Owner
message `econ status` / `econ detach`), and one small shell call when reached from a tool.

Verbs:
  status  --session SID [--text]   binding + ledger + the next legal transition (read-only)
  detach  --session SID --reason R the session leaves its goal: settle the measured truth since the
                                   binding, close its holds, tombstone it on that goal, and write the
                                   next binding generation {goal:"none", fenced:[goal]}. The goal's
                                   workspace stays fenced for this session (goal_binding.fenceFor), so
                                   a detach can never continue that goal's work unaccounted.

Recovery never edits product paths and never reserves spend. Origin: ctx-same-pane, 2026-10-10 --
two panes bound by cwd to a 16M goal reached 18,072,474 used+reserved; d5063bac was bound 50 minutes
after the cap was crossed and every escape probe (cd, another shell) bought ~200K to be refused.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402


def _fold(goal: str) -> dict:
    led = ms._goal_ledger(goal)
    with led._lock:
        return led._gfold(led._read())


def _measured_since(sid: str, since: str | None) -> int | None:
    """The session's processed tokens from its binding on: the same window the guard measures."""
    tp = ms.find_transcript(sid)
    if tp is None:
        return None
    return int(ms.session_tokens(tp, since)["tokens"])


def status(sid: str) -> dict:
    rec = ms.read_binding(sid)
    out: dict = {"ok": True, "session": sid, "binding": rec, "goal": None, "state": "NEUTRAL",
                 "next": "No goal pays for this session; nothing is fenced by its binding."}
    if not rec or rec.get("goal") in (None, "", "none"):
        if rec and rec.get("fenced"):
            out["next"] = (f"Detached (generation {rec.get('gen', 1)}). Fenced workspaces: "
                           f"{', '.join(rec['fenced'])}; reads there stay free, changes are refused.")
        return out
    goal = rec["goal"]
    out["goal"] = goal
    entry = ms.read_index().get(goal)
    if entry is None:
        out.update(state="UNKNOWN", next=f"goal {goal} is not declared on this host; unknown is never admitted.")
        return out
    g = _fold(goal)
    cur = g["leases"][-1]
    other = sum(sum(ls["reserves"].values()) for ls in g["leases"] if not ls["closed"])
    executable = None if g["programme"] is None else g["programme"] - sum(g["marks"].values()) - g["open"] - other
    out["ledger"] = {"cap": g["cap"], "used": g["used"], "settled": sum(g["marks"].values()), "open": g["open"],
                     "lease": cur["id"], "programme": g["programme"], "executable": executable,
                     "exhausted": g["exhausted_now"], "tombstoned": sid in g["tombs"],
                     "session_mark": g["marks"].get(sid, 0)}
    if sid in g["tombs"]:
        out["state"] = "TOMBSTONED"
    elif g["exhausted_now"]:
        out["state"] = "EXHAUSTED"
    else:
        out["state"] = "ACTIVE"
        out["next"] = "Admitted: the goal still holds at least one call."
        return out
    if executable is not None and executable > 0:
        out["next"] = (f"SUCCESSOR AVAILABLE: the programme still holds {executable:,}. A fresh session (/clear) "
                       "binds to the successor lease once it is opened; this session stays fenced.")
    else:
        out["next"] = (f"WAITING_OWNER_CAPITAL: goal {goal} is spent and no programme authority remains. "
                       "One decision: approve a successor lease, or close the goal. Nothing runs meanwhile. "
                       "`econ detach` frees this pane for other work now.")
    return out


def render(st: dict) -> str:
    """The deterministic status text shown in place of a model reply."""
    lines = [f"ECONOMIC STATUS -- session {st['session'][:8]}: {st['state']}"]
    rec = st.get("binding") or {}
    if rec:
        lines.append(f"binding: goal={rec.get('goal')} gen={rec.get('gen', 1)} source={rec.get('source')}"
                     + (f" fenced={','.join(rec['fenced'])}" if rec.get("fenced") else ""))
    led = st.get("ledger")
    if led:
        cap = led["cap"] or 0
        lines.append(f"goal {st['goal']}: used {led['used']:,} of cap {cap:,} (settled {led['settled']:,}, "
                     f"reserved {led['open']:,}, lease {led['lease']})")
        if led["programme"] is not None:
            lines.append(f"programme {led['programme']:,}, executable {led['executable']:,}")
        lines.append("unknown in-flight: whatever this session spent since its last settle is settled on detach "
                     "from its transcript, never assumed zero.")
    lines.append(f"next: {st['next']}")
    lines.append("The cap is never raised by this plane. Verbs: `econ status`, `econ detach`; `/clear` = fresh session.")
    return "\n".join(lines)


def detach(sid: str, reason: str) -> dict:
    rec = ms.read_binding(sid)
    if not rec or rec.get("goal") in (None, "", "none"):
        return {"ok": True, "session": sid, "applied": False, "reason": "not bound to a goal"}
    goal = rec["goal"]
    out: dict = {"ok": True, "session": sid, "from": goal, "applied": True}
    if ms.read_index().get(goal) is not None:
        led = ms._goal_ledger(goal)
        mark = _fold(goal)["marks"].get(sid, 0)
        measured = _measured_since(sid, rec.get("since_ts"))
        # Unknown spend is not zero: no transcript -> settle at the known mark and say so.
        out["measured"] = measured
        out["settle"] = led.settle_stopped(sid, max(mark, measured or 0), f"econ-detach: {reason}")
        out["tombstone"] = led.tombstone(sid, f"detached: {reason}")
        if measured is None:
            out["warning"] = "no transcript found: settled at the last known mark; the gap stays UNKNOWN"
    new = ms.supersede_binding(sid, "none", "econ-detach", reason)
    if new is None:
        return {**out, "ok": False, "reason": "the next binding generation could not be written (raced?)"}
    out["binding"] = new
    return out


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="econ_plane")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--session", required=True)
    s.add_argument("--text", action="store_true")
    d = sub.add_parser("detach")
    d.add_argument("--session", required=True)
    d.add_argument("--reason", default="owner-request")
    a = ap.parse_args(argv)
    if not ms._SID_RE.match(a.session):
        print(json.dumps({"ok": False, "reason": f"invalid session id: {a.session!r}"}))
        return 3
    if a.cmd == "status":
        st = status(a.session)
        print(render(st) if a.text else json.dumps(st, sort_keys=True, default=str))
        return 0
    out = detach(a.session, a.reason)
    print(json.dumps(out, sort_keys=True, default=str))
    return 0 if out.get("ok") else 3


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(_main(sys.argv[1:]))
