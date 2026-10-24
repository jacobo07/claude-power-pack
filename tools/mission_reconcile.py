"""Terminal reconciliation (flow-compression S5, FC-07): a worker that stops is not a mission that ended.

reconcile(rec) classifies a stopped mission as RECOVERED_DONE, CONTINUATION, FAILED or AMBIGUOUS from the single
resolved receipt and the ledger lineage. dispose() partitions the hours of every HALTED / ORPHANED mission on THIS
host's ledger by that classification. Both are pure readers: no transition, no authority, no write (FC-06, FC-10).
DONE is reachable only through receipt_judge.is_done on the one resolved path (never a worker success, never a
closed non-DONE status, never an unmeasured read).

    python3 tools/mission_reconcile.py dispose [--json] [--now EPOCH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_judge as rj  # noqa: E402

RECOVERED_DONE = "RECOVERED_DONE"
CONTINUATION = "CONTINUATION"
FAILED = "FAILED"
AMBIGUOUS = "AMBIGUOUS"
MAX_HOPS = 8
_DEAD_END = ("HALTED", "ORPHANED")


def _out(outcome: str, reason: str, **evidence) -> dict:
    return {"outcome": outcome, "reason": reason, "evidence": evidence}


def _ambiguous(reason: str, **ev) -> dict:
    return _out(AMBIGUOUS, reason, **ev)


def _successor_id(mid: str, rows: list[dict], rec: dict) -> tuple[str | None, str | None]:
    """The successor a ledger row or the AMR record names for `mid`: (id, how). Only fields verified in the repo."""
    for e in rows:
        if e.get("event") == "mission_renewed" and e.get("successor"):
            return e["successor"], "mission_renewed"
        if e.get("event") == "mission_superseded" and e.get("superseded_by"):
            return e["superseded_by"], "mission_superseded"
    return None, None


def _amr_successor(rec: dict, by_pkt: dict) -> str | None:
    pkt = (rec.get("amr") or {}).get("packet")
    return by_pkt.get(os.path.normcase(os.path.abspath(pkt))) if pkt else None


def _lineage(rec: dict, rows_of, by_id: dict, by_pkt: dict) -> dict:
    """Follow successors from `rec`. Returns {kind: none|tail|ambiguous|failed, ...}."""
    visited = {rec["mission_id"]}
    cur, hops, trail = rec, 0, []
    while True:
        sid, how = _successor_id(cur["mission_id"], rows_of(cur["mission_id"]), cur)
        if sid is None:
            sid = _amr_successor(cur, by_pkt)
            how = "amr_packet" if sid else None
        if sid is None:
            return {"kind": "none" if hops == 0 else "tail", "tail": cur, "hops": hops, "trail": trail}
        hops += 1
        if hops > MAX_HOPS:
            return {"kind": "ambiguous", "why": f"successor chain deeper than {MAX_HOPS}", "trail": trail}
        if sid in visited:
            return {"kind": "ambiguous", "why": f"successor cycle at {sid}", "trail": trail}
        nxt = by_id.get(sid)
        if nxt is None:
            return {"kind": "ambiguous", "why": f"successor {sid} has no readable record", "trail": trail}
        visited.add(sid)
        trail.append({"id": sid, "via": how, "state": nxt.get("state")})
        cur = nxt


def _indexes(missions: list[dict]) -> tuple[dict, dict]:
    by_id = {m["mission_id"]: m for m in missions}
    by_pkt = {}
    for m in missions:
        p = (m.get("wu_packet") or {}).get("path")
        if p:
            by_pkt[os.path.normcase(os.path.abspath(p))] = m["mission_id"]
    return by_id, by_pkt


def reconcile(rec: dict, *, events: list[dict] | None = None, now: float | None = None, programs_dir=None,
              missions: list[dict] | None = None) -> dict:
    """Classify a stopped mission. Read-only; every external read failure is AMBIGUOUS, never DONE, never raised."""
    try:
        import gsd_mission as gm
        import gsd_long_run as lr
        mid = rec["mission_id"]
        pkt = (rec.get("wu_packet") or {}).get("path")
        if not pkt:
            return _ambiguous("no wu_packet: no receipt contract")
        res = gm.resolve_receipt(pkt, rec, programs_dir)
        ev = {"resolver": res}
        if res["conflict"]:
            return _ambiguous("conflicting receipts", **ev)
        if events is None:
            events = lr.ledger_events()
        mine = [e for e in events if e.get("mission_id") == mid or e.get("session_id") == mid]
        status = res["status"]
        if res["present"] and status == "DONE" and rj.is_done(res["path"]):
            if Path(res["path"]).stat().st_mtime >= float(rec.get("created_at") or 0):
                return _out(RECOVERED_DONE, f"closed DONE receipt via {res['source']}", **ev)
            return _ambiguous("DONE receipt older than the mission (stale)", **ev)
        if res["present"] and rj.is_closed(res["path"]):
            return _out(FAILED, f"worker verdict {status}, not DONE", status=status, **ev)
        if missions is None:
            missions = gm.all_missions()
        by_id, by_pkt = _indexes(missions)
        by_mid: dict = {}
        for e in events:
            by_mid.setdefault(e.get("mission_id") or e.get("session_id"), []).append(e)
        lin = _lineage(rec, lambda m: by_mid.get(m, []), by_id, by_pkt)
        if lin["kind"] == "ambiguous":
            return _ambiguous(lin["why"], successors=lin["trail"], **ev)
        if lin["kind"] == "tail":
            tail = lin["tail"]
            info = {"tail": tail["mission_id"], "tail_state": tail.get("state"), "hops": lin["hops"],
                    "successors": lin["trail"]}
            if tail.get("state") in _DEAD_END:
                return _out(FAILED, "lineage ends in a terminal dead end", **info, **ev)
            return _out(CONTINUATION, f"continues as {tail['mission_id']}", **info, **ev)
        if rec.get("state") in ("HALTED", "ORPHANED"):
            why = next((e.get("reason") for e in reversed(mine) if e.get("reason") and e.get("state") in _DEAD_END),
                       None)
            if why:
                return _out(FAILED, f"terminal with recorded reason: {str(why)[:200]}", **ev)
        return _ambiguous("no closed DONE receipt", **ev)
    except Exception as exc:  # noqa: BLE001 -- an unreadable input is AMBIGUOUS, never DONE and never raised
        return _ambiguous(f"{type(exc).__name__}: {str(exc)[:160]}")


# ---------------------------------------------------------------------------------------------------- dispose
BUCKETS = ("recovered_done_h", "idle_to_successor_h", "tombstone_h", "stranded_h", "unknown_h")
_QUOTED = ("The 149 h figure is LAPTOP-ONLY and NOT measured here: its definition is not recoverable from any "
           "readable source. The laptop coordinator reruns this same command on its own ledger and compares "
           "idle_to_successor_h + tombstone_h.")


def _union(intervals: list[tuple[float, float]]) -> float:
    total, end = 0.0, None
    for a, b in sorted(i for i in intervals if i[1] > i[0]):
        if end is None or a > end:
            total += b - a
            end = b
        elif b > end:
            total += b - end
            end = b
    return total


def dispose(events: list[dict] | None = None, now: float | None = None, programs_dir=None,
            missions: list[dict] | None = None) -> dict:
    import time
    import gsd_epoch as ge
    import gsd_long_run as lr
    import gsd_mission as gm
    now = time.time() if now is None else float(now)
    events = lr.ledger_events() if events is None else events
    missions = gm.all_missions() if missions is None else missions
    rows_by: dict = {}
    for e in events:
        k = e.get("mission_id") or e.get("session_id")
        rows_by.setdefault(k, []).append(e)

    def t_of(e):
        return ge._ts(e.get("ts"))

    def first_ts(mid):
        ts = [t for t in (t_of(e) for e in rows_by.get(mid, [])) if t is not None]
        return min(ts) if ts else None

    per, intervals = [], []
    tot = {b: 0.0 for b in BUCKETS}
    unmeasured = []
    for m in missions:
        mid = m["mission_id"]
        t0 = first_ts(mid)
        term = [t for t in (t_of(e) for e in rows_by.get(mid, []) if ge.is_terminal_row(e)) if t is not None]
        t_end = min(term) if term else None
        if t0 is not None:
            intervals.append((t0, t_end if t_end is not None else now))
        if m.get("state") not in ("HALTED", "ORPHANED"):
            continue
        if t_end is None:
            unmeasured.append({"id": mid, "state": m.get("state"), "hours_since_first_row":
                               None if t0 is None else round((now - t0) / 3600, 3)})
            continue
        r = reconcile(m, events=events, now=now, programs_dir=programs_dir, missions=missions)
        span = max(0.0, now - t_end)
        h = {b: 0.0 for b in BUCKETS}
        succ = None
        if r["outcome"] == RECOVERED_DONE:
            h["recovered_done_h"] = span
        elif r["outcome"] == CONTINUATION:
            succ = (r["evidence"].get("successors") or [{}])[0].get("id")
            s0 = first_ts(succ) if succ else None
            idle = min(span, max(0.0, (s0 - t_end))) if s0 is not None else span
            h["idle_to_successor_h"], h["tombstone_h"] = idle, span - idle
        elif r["outcome"] == FAILED:
            h["stranded_h"] = span
        else:
            h["unknown_h"] = span
        for b in BUCKETS:
            tot[b] += h[b]
        per.append({"id": mid, "state": m.get("state"), "outcome": r["outcome"], "reason": r["reason"][:120],
                    "successor": succ, **{b: round(h[b] / 3600, 4) for b in BUCKETS}})
    # open-terminal-epoch audit (the defect measured in the plan)
    term_ids, open_ids = 0, []
    for m in missions:
        if m.get("state") in gm.TERMINAL:
            eps = ge.epochs(m["mission_id"], events)
            if eps:
                term_ids += 1
                if eps[-1]["end"] is None:
                    open_ids.append(m["mission_id"])
    pk, disagree = 0, []
    for m in missions:
        p = (m.get("wu_packet") or {}).get("path")
        if not p:
            continue
        pk += 1
        legacy = str(gm.stem_receipt(p))
        try:
            res = gm.resolve_receipt(p, m, programs_dir)
        except Exception:  # noqa: BLE001
            disagree.append(m["mission_id"])
            continue
        if not os.path.exists(legacy) and res["present"] and os.path.realpath(res["path"]) != os.path.realpath(legacy) \
                and res["source"] == "STEM":
            disagree.append(m["mission_id"])
    return {
        "now": now,
        "missions": len(missions),
        "buckets_h": {b: round(tot[b] / 3600, 4) for b in BUCKETS},
        "per_mission": per,
        "unmeasured": unmeasured,
        "summed_mission_h": round(sum(b - a for a, b in intervals) / 3600, 4),
        "union_wall_h": round(_union(intervals) / 3600, 4),
        "open_terminal_epochs": {"terminal_with_epochs": term_ids, "last_epoch_open": len(open_ids), "ids": open_ids},
        "resolver_audit": {"packet_bearing": pk, "stem_absent_but_resolved_elsewhere": len(disagree), "ids": disagree},
        "quoted_not_measured": _QUOTED,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mission_reconcile")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dispose", help="partition HALTED/ORPHANED hours by successor check (read-only)")
    d.add_argument("--json", action="store_true")
    d.add_argument("--now", type=float, default=None)
    a = ap.parse_args(argv)
    try:
        rep = dispose(now=a.now)
    except Exception as exc:  # noqa: BLE001 -- never a silent empty result
        print(f"dispose failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(json.dumps({k: v for k, v in rep.items() if k != "per_mission"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
