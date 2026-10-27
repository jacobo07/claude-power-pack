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
    lines.append("Verbs: `econ status`, `econ detach`, `subelo 70M` (Owner raise: programme += N, successor lease), "
                 "`subelo 70M <goal>` (any goal, any pane, no size limit); `/clear` = fresh session.")
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


RAISE_MAX = 1_000_000_000_000  # arithmetic guard only (Owner 2026-10-20: "la cantidad que quiera"); no budget policy
RECOVERY = "recovery"          # GoalLedger's reserve key for the recovery pool


def _open_successor(led, g, cur, amount: int, key: str, approval_uuid: str | None = None):
    """programme += amount, then a successor lease at (amount + the current lease's unspent remainder),
    reserves carried over.

    Shared by the pane-bound raise and the goal-addressed raise. Returns (error | None, lease_open row,
    programme before, new cap). The envelope is validated BEFORE the programme row is written: a refused
    raise leaves the ledger untouched. Idempotent per `key` (programme row tag + lease succession id)."""
    base = f"owner-econ-raise:{key}"
    # The approving transcript entry uuid rides in the programme row's source when the caller knows it, so the
    # authority lineage is not recovered from transcript text later (ctx-rent-a2 had a 60M row without it).
    tag = f"{base}:approval:{approval_uuid}" if approval_uuid else base
    src = g["programme_source"]
    done = src == tag or src == base or str(src).startswith(base + ":approval:")  # a previous attempt wrote the row
    # A lease cap is that lease's own budget (`used` reads the current lease once a successor exists, and
    # _auto_succeed sizes a successor by its tranche). `cur.cap + amount` asked for the spent cap again:
    # need - room was then cap - executable whatever amount was typed (gsdx-factory-2, 2026-10-22).
    old_prog = int(g["programme"]) - (amount if done else 0)
    new_cap = amount + max(0, int(cur["cap"]) - int(g["used"]))
    rv = cur["reserves"]
    carry = {k: int(v) for k, v in rv.items() if k != RECOVERY and int(v) > 0}
    rec_left = int(rv.get(RECOVERY, 0)) - cur.get("rsettled", 0)
    if rec_left > 0:
        carry[RECOVERY] = rec_left
    room = led._executable(g) + (0 if done else amount)
    reserved = sum(carry.values())
    # An overdrawn goal absorbs its deficit first: the successor holds what the programme holds after the raise,
    # never more. Unclamped, need exceeded room for EVERY amount once executable < 0 (gsdx-factory-2 2026-10-23).
    new_cap = min(new_cap, room - reserved)
    if new_cap <= 0:
        return ({"reason": f"AUTHORITY_REQUIRED: the programme would hold {room:,} after +{amount:,}, which leaves no "
                           f"room for a successor beyond reserves {reserved:,}; type more than "
                           f"{amount - room + reserved:,}"}, None, old_prog, new_cap)
    if not done:
        pr = led.set_programme(old_prog + amount, tag, inside_agent=False)
        if not pr.get("ok"):
            return ({"reason": str(pr.get("reason"))}, None, old_prog, new_cap)
    lo = led.lease_open(key, new_cap, prev_lease=cur["id"], reserves=carry)
    if not lo.get("ok"):
        return ({"reason": str(lo.get("reason")), "programme": old_prog + amount}, None, old_prog, new_cap)
    return None, lo, old_prog, new_cap


def _bootstrap_envelope(led, g, cur, amount: int, key: str, approval_uuid: str | None = None):
    """The Owner's typed raise on a goal that holds no envelope here (ccr-a2 2026-10-27: declared on another host,
    only settled spend on this one). The typed amount is the whole new headroom and what the goal already spent
    stays spent: programme = settled + open + other leases' reserves + amount, then a successor lease of `amount`.

    Same return shape as _open_successor. Only the raise verbs reach this: lease_open and set_programme called
    from anywhere else keep refusing an envelope-less goal. Idempotent per `key` for a crash between the two
    writes: the programme row is skipped once present and lease_open is keyed by succession id."""
    base = f"owner-econ-raise:{key}:bootstrap"
    tag = f"{base}:approval:{approval_uuid}" if approval_uuid else base
    if g["programme"] is None:
        other = sum(led._committed_reserves(ls) for ls in g["leases"] if not ls["closed"] and ls is not cur)
        programme = sum(g["marks"].values()) + g["open"] + other + amount
        pr = led.set_programme(programme, tag, inside_agent=False)
        if not pr.get("ok"):
            return ({"reason": str(pr.get("reason"))}, None, programme - amount, 0)
    else:
        programme = int(g["programme"])
    lo = led.lease_open(f"{key}:bootstrap", amount, prev_lease=cur["id"])
    if not lo.get("ok"):
        return ({"reason": str(lo.get("reason")), "programme": programme}, None, programme - amount, 0)
    return None, lo, programme - amount, amount


def _opener(g, cur):
    """Which writer opens the successor: the bootstrap when the goal has no envelope or no lease cap, or when THIS
    lease's own bootstrap already wrote its programme row and died before the lease (the row's tag names the lease it
    was written against). Without the replay arm that retry takes the ordinary path and raises a second time."""
    replay = f":{cur['id']}:bootstrap" in str(g["programme_source"] or "")
    return _bootstrap_envelope if g["programme"] is None or cur["cap"] is None or replay else _open_successor


def raise_goal(goal: str, amount: int, approval_uuid: str | None = None) -> dict:
    """Owner raise addressed to a GOAL, from any pane (`subelo 70M <goal>`, or a neutral pane whose cwd lies under
    the goal's root). Same money path as raise_capital (programme += amount, successor lease), but no pane is
    unfenced: the tombstoned panes of that goal stay fenced and a fresh session (`/clear`) binds to the successor."""
    if not isinstance(amount, int) or isinstance(amount, bool) or not 0 < amount <= RAISE_MAX:
        return {"ok": False, "reason": f"amount must be 1..{RAISE_MAX:,} tokens, got {amount!r}"}
    if ms.read_index().get(goal) is None:
        return {"ok": False, "goal": goal, "reason": f"goal {goal} is not declared on this host; unknown is never admitted"}
    led = ms._goal_ledger(goal)
    g = _fold(goal)
    cur = g["leases"][-1]
    open_successor = _opener(g, cur)
    err, lo, old_prog, new_cap = open_successor(led, g, cur, amount, f"owner-raise:goal:{goal}:{cur['id']}", approval_uuid)
    if err:
        return {"ok": False, "goal": goal, **err}
    return {"ok": True, "goal": goal, "applied": bool(lo.get("applied")), "from_lease": cur["id"],
            "lease": lo.get("lease"), "programme_old": old_prog, "programme_new": old_prog + amount,
            "cap_old": int(cur["cap"] or 0), "cap_new": new_cap, "reason": ""}


def raise_capital(sid: str, amount: int, short: bool = False, approval_uuid: str | None = None) -> dict:
    """Owner raise: programme += amount, then a successor lease at (amount + unspent remainder).

    Reached only from the Owner's typed `subelo N` (hooks/econ_admission.js). A crossed cap is not raised in
    place: the money lands in a SUCCESSOR lease, and the blocked pane's tombstone is lifted (journal op
    "untomb", tied to that lease) so the pane can run the rollover (/kclear) against it. Idempotent per
    (session, lease): the lease_open succession id and the programme row's source tag carry the same key; a
    pane whose own successor already exists is just unfenced (`resumed`), with no new money. `short` = the caller saw "next call does not fit" with no tombstone/exhaustion."""
    if not isinstance(amount, int) or isinstance(amount, bool) or not 0 < amount <= RAISE_MAX:
        return {"ok": False, "reason": f"amount must be 1..{RAISE_MAX:,} tokens, got {amount!r}"}
    rec = ms.read_binding(sid)
    if not rec or rec.get("goal") in (None, "", "none"):
        return {"ok": True, "session": sid, "applied": False, "reason": "not bound to a goal; nothing blocks this pane"}
    goal = rec["goal"]
    if ms.read_index().get(goal) is None:
        return {"ok": False, "session": sid, "goal": goal,
                "reason": f"goal {goal} is not declared on this host; unknown is never admitted"}
    led = ms._goal_ledger(goal)
    g = _fold(goal)
    cur = g["leases"][-1]
    tomb = g["tombs"].get(sid)
    if tomb and tomb.get("lease") != cur["id"]:
        # A successor already exists. If THIS pane's own raise opened it (an earlier build, or a crash before the
        # untomb), finish the job: lift the fence now, writing no money. Anyone else's successor stays theirs.
        if str(cur.get("succession_id") or "").startswith(f"owner-raise:{sid}:"):
            ut = led.untombstone(sid, cur["id"], "owner-econ-raise (resume)")
            return {"ok": bool(ut.get("ok")), "session": sid, "goal": goal, "applied": bool(ut.get("ok")),
                    "resumed": True, "lease": cur["id"], "cap_new": cur["cap"], "reason": str(ut.get("reason") or "")}
        return {"ok": True, "session": sid, "goal": goal, "applied": False, "lease": cur["id"], "cap": cur["cap"],
                "reason": f"successor lease {cur['id']} is already open and was not opened by this pane"}
    if not (tomb or g["exhausted_now"] or short):
        return {"ok": True, "session": sid, "goal": goal, "applied": False,
                "reason": "this session is not blocked; nothing raised"}
    open_successor = _opener(g, cur)
    key = f"owner-raise:{sid}:{cur['id']}"
    err, lo, old_prog, new_cap = open_successor(led, g, cur, amount, key, approval_uuid)
    if err:
        return {"ok": False, "session": sid, "goal": goal, **err}
    if tomb:                                       # the pane spends against the lease it just got
        ut = led.untombstone(sid, lo.get("lease"), "owner-econ-raise")
        if not ut.get("ok"):
            return {"ok": False, "session": sid, "goal": goal, "reason": f"lease opened but fence not lifted: {ut.get('reason')}"}
    return {"ok": True, "session": sid, "goal": goal, "applied": bool(lo.get("applied")), "from_lease": cur["id"],
            "lease": lo.get("lease"), "programme_old": old_prog, "programme_new": old_prog + amount,
            "cap_old": int(cur["cap"] or 0), "cap_new": new_cap, "reason": ""}


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
    r = sub.add_parser("raise")
    r.add_argument("--session")
    r.add_argument("--goal")
    r.add_argument("--amount", required=True, type=int)
    r.add_argument("--short", action="store_true")
    r.add_argument("--approval-uuid", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "raise" and a.goal:
        out = raise_goal(a.goal, a.amount, a.approval_uuid)
        print(json.dumps(out, sort_keys=True, default=str))
        return 0 if out.get("ok") else 3
    if not a.session or not ms._SID_RE.match(a.session):
        print(json.dumps({"ok": False, "reason": f"invalid session id: {a.session!r}"}))
        return 3
    if a.cmd == "status":
        st = status(a.session)
        print(render(st) if a.text else json.dumps(st, sort_keys=True, default=str))
        return 0
    if a.cmd == "raise":
        out = raise_capital(a.session, a.amount, a.short, a.approval_uuid)
        print(json.dumps(out, sort_keys=True, default=str))
        return 0 if out.get("ok") else 3
    out = detach(a.session, a.reason)
    print(json.dumps(out, sort_keys=True, default=str))
    return 0 if out.get("ok") else 3


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(_main(sys.argv[1:]))
