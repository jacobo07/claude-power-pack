#!/usr/bin/env python
"""V-MAR-* gates for spec vault/specs/mission-autoresume.md (tools/mission_autoresume.py + its supervise wiring).

Origin (measured 2026-11-10, GEX44 m-f27c61b9e75c): an iteration-cap halt with Owner headroom was refused renewal
against the AUTO envelope, ledgered nowhere, told to nobody, and sat 3 h 46 min.

Real mission records and a real ledger in a temp state dir; GSD and the spend meter are the only injected parts.
Run: python tools/test_mission_autoresume.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

STATE = tempfile.mkdtemp(prefix="mar-state-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = STATE
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(STATE) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = STATE
os.environ.pop("CPP_MISSION_AUTORESUME", None)
os.environ.pop("CPP_MISSION_RENEW", None)

import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import mission_autoresume as mar  # noqa: E402
import mission_spend as ms  # noqa: E402

ITER = "turn ended and budget: iterations 12 >= max 12"
results: list[tuple[str, bool, str]] = []
SPENT = {"processed": 43_474_533}


def check(gate: str, cond: bool, msg: str) -> None:
    results.append((gate, bool(cond), msg))
    print(f"[{'PASS' if cond else 'FAIL'}] {gate}: {msg}")


# The spend meter reads worker transcripts the fixture does not have: measured 43.5M for every lineage.
ms.lineage_spend = lambda mid, all_missions=None, extra=None, root=None, cache=None: {
    "processed": SPENT["processed"], "unmeasured": [], "members": [mid]}


def _remaining(rec, all_missions=None, root=None, cache=None):
    b = rec.get("lineage_token_budget") or rec.get("token_estimate")
    return {"budget": int(b) if b else None, "spent": SPENT["processed"],
            "remaining": (int(b) - SPENT["processed"]) if b else None, "unmeasured": []}


ms.lineage_remaining = _remaining
GSD = {"outcome": "OK"}
gsd = lambda wd, workstream=None: dict(GSD)  # noqa: E731
notes: list[tuple[str, str]] = []


_delivered: set = set()


def notify(mid, key, why):
    """Same contract as mission_remedies.notify_incident: delivered once per (mission, key)."""
    if (mid, key) in _delivered:
        return None
    _delivered.add((mid, key))
    notes.append((mid, why))
    return "sent"


def halted(reason=ITER, *, auto=True, hold=None, hours_used=10.0, max_hours=72.0, extra=None) -> dict:
    cwd = tempfile.mkdtemp(prefix="mar-cwd-")
    rec = gm.create(cwd, "Execute the fixture packet", max_cycles=12, max_hours=max_hours)
    changes = dict(state=gm.HALTED, epoch=7, iterations=12, token_estimate=23_232_149,
                   authority_tokens=160_000_000, created_at=rec["created_at"] - hours_used * 3600, reason=reason)
    if auto:
        changes["token_estimate_src"] = "auto"
    if hold:
        changes["owner_hold"] = hold
    changes.update(extra or {})
    return gm.transition(rec["mission_id"], expect_epoch=0, expect_state=gm.PREPARED, event="mission_halted",
                         **changes)


def halt_at(mid) -> float:
    return mar._ts(mar._last_halt(lr.ledger_events(mid)))


def successors(mid) -> list[dict]:
    return [m for m in gm.all_missions() if m.get("renewed_from") == mid]


def run(now):
    return mar.autoresume_pass(now, gsd_status=gsd, notify=notify)


def main() -> int:
    # V-MAR-ITER-RESUMES
    a = halted()
    t = halt_at(a["mission_id"])
    rows = run(t + 360)
    s = successors(a["mission_id"])
    reserve = ms.closeout_reserve(a)
    ok = len(s) == 1 and s[0].get("lineage_token_budget") == 160_000_000 - reserve
    left = s[0].get("max_hours") if s else None
    check("V-MAR-ITER-RESUMES", ok and left is not None and 61.0 < left < 62.1
          and gm._ledger_has(a["mission_id"], "autoresume_renewed"),
          f"successors={len(s)} lineage_budget={s[0].get('lineage_token_budget') if s else None} "
          f"max_hours={left} rows={rows}")

    # V-MAR-ONCE
    run(t + 700)
    check("V-MAR-ONCE", len(successors(a["mission_id"])) == 1, f"successors={len(successors(a['mission_id']))}")

    # V-MAR-TOO-SOON
    b = halted()
    run(halt_at(b["mission_id"]) + 120)
    check("V-MAR-TOO-SOON", not successors(b["mission_id"]), "2 min after the halt: nothing")

    # V-MAR-TOO-OLD
    n0 = len(notes)
    run(halt_at(b["mission_id"]) + 25 * 3600)
    check("V-MAR-TOO-OLD", not successors(b["mission_id"]) and len(notes) == n0, "25 h after: nothing, no notice")

    # V-MAR-WALL
    c = halted("turn ended and budget: older than 72.0 h")
    n0 = len(notes)
    run(halt_at(c["mission_id"]) + 360)
    check("V-MAR-WALL", not successors(c["mission_id"]) and gm._ledger_has(c["mission_id"], "autoresume_refused")
          and len(notes) == n0 + 1, f"notes+{len(notes) - n0}")

    # V-MAR-OWNER-HOLD
    d = halted(hold={"reason": "Owner: CERRAR", "kind": "owner"})
    n0 = len(notes)
    run(halt_at(d["mission_id"]) + 360)
    check("V-MAR-OWNER-HOLD", not successors(d["mission_id"]) and len(notes) == n0 + 1, notes[-1][1][:90])

    # V-MAR-OWNER-ENVELOPE: an envelope the Owner/operator set is never raised
    e = halted(auto=False)
    run(halt_at(e["mission_id"]) + 360)
    ref = [x for x in lr.ledger_events(e["mission_id"]) if x.get("event") == "autoresume_refused"]
    check("V-MAR-OWNER-ENVELOPE", not successors(e["mission_id"]) and ref and "lineage budget" in ref[-1]["reason"],
          ref[-1]["reason"][:100] if ref else "no refusal row")

    # V-MAR-GSD-DONE
    GSD["outcome"] = "ALL_COMPLETE"
    f = halted()
    run(halt_at(f["mission_id"]) + 360)
    GSD["outcome"] = "OK"
    check("V-MAR-GSD-DONE", not successors(f["mission_id"]), "GSD ALL_COMPLETE: no successor")

    # V-MAR-SUPERSEDED: another live mission holds the goal -> no successor, no notice, on any pass
    k = halted()
    n0 = len(notes)
    orig_why = gm._renewal_why_not
    gm._renewal_why_not = lambda *a, **kw: "singleflight: m-x is a live attempt of this goal"
    try:
        run(halt_at(k["mission_id"]) + 360)
        run(halt_at(k["mission_id"]) + 720)
    finally:
        gm._renewal_why_not = orig_why
    check("V-MAR-SUPERSEDED", not successors(k["mission_id"]) and len(notes) == n0
          and gm._ledger_has(k["mission_id"], "autoresume_refused"), f"notes+{len(notes) - n0}")

    # V-MAR-V2-NO-CAPSULE (review HIGH): the halt handed on no capsule; the record's OWN key must not be used
    v2 = {"rollover_protocol": gm.CAPSULE_V2, "permission_mode": "bypassPermissions"}
    p = halted(extra={**v2, "capsule_key": "cap-predecessor-retired",
                      "continuity": {"kind": "none", "reason": "no renewal: lineage budget exhausted"}})
    run(halt_at(p["mission_id"]) + 360)
    check("V-MAR-V2-NO-CAPSULE", not successors(p["mission_id"])
          and gm._ledger_has(p["mission_id"], "autoresume_refused"), "v2 without a handed-on capsule: refused")

    # V-MAR-V2-CAPSULE: the key the halt handed on is the one the successor certifies
    q = halted(extra={**v2, "continuity": {"kind": "inherited", "capsule_key": "cap-handed-on"}})
    run(halt_at(q["mission_id"]) + 360)
    sq = successors(q["mission_id"])
    check("V-MAR-V2-CAPSULE", len(sq) == 1 and sq[0].get("capsule_key") == "cap-handed-on"
          and sq[0].get("rollover_protocol") == gm.CAPSULE_V2,
          f"successors={len(sq)} capsule_key={sq[0].get('capsule_key') if sq else None}")

    # V-MAR-TRANSIENT (review LOW): GSD did not answer -> no decision ledgered, re-decided on the next pass
    GSD["outcome"] = "UNAVAILABLE"
    r_ = halted()
    run(halt_at(r_["mission_id"]) + 360)
    first = (successors(r_["mission_id"]), gm._ledger_has(r_["mission_id"], "autoresume_refused"))
    GSD["outcome"] = "OK"
    run(halt_at(r_["mission_id"]) + 660)
    check("V-MAR-TRANSIENT", first == ([], False) and len(successors(r_["mission_id"])) == 1,
          f"first={first} then successors={len(successors(r_['mission_id']))}")

    # V-MAR-WALL-SPENT
    g = halted(hours_used=71.9)
    run(halt_at(g["mission_id"]) + 360)
    check("V-MAR-WALL-SPENT", not successors(g["mission_id"]) and gm._ledger_has(g["mission_id"], "autoresume_refused"),
          "6 min of wall left: refused")

    # V-MAR-OFF
    h = halted()
    os.environ["CPP_MISSION_AUTORESUME"] = "off"
    rows = run(halt_at(h["mission_id"]) + 360)
    os.environ.pop("CPP_MISSION_AUTORESUME")
    check("V-MAR-OFF", rows == [] and not successors(h["mission_id"]), "kill switch: nothing")

    # V-MAR-WIRED: the real supervise() reaches the pass (h is the only fresh decidable fixture; GSD stays injected)
    orig = mar.autoresume_pass
    seen = []
    mar.autoresume_pass = lambda *a, **k: seen.append(1) or orig(halt_at(h["mission_id"]) + 360, gsd_status=gsd,
                                                                    notify=notify)
    try:
        gm.supervise(sessions=[], pid_alive=lambda pid: False, gsd_status=gsd)
    except TypeError:
        gm.supervise()
    finally:
        mar.autoresume_pass = orig
    check("V-MAR-WIRED", seen == [1] and len(successors(h["mission_id"])) == 1,
          f"pass calls={len(seen)} successors={len(successors(h['mission_id']))}")

    bad = [g_ for g_, ok_, _ in results if not ok_]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed" + (f"; FAILED {bad}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
