#!/usr/bin/env python
"""V-MCF-* gates: capsule-v2 fault matrix + chain audit (spec vault/specs/mission-capsule-rollover.md 11.6, T7).

Every row drives the REAL supervise() pass through a fault injected between two effects, then lets a clean
pass resolve it, and asserts section 5: never two workers with mutation authority, never a stopped worker
with no sealed capsule, every unknown resolving to the old epoch, the successor, or a named BLOCKED/HALTED.
The chain audit (`mission_capsule.py audit --mission`) is judged from both poles: an intact lineage reads
INTACT, the same lineage with one link removed reads BROKEN naming that link.

Hermetic by construction: the harness of tools/test_gsd_mission_capsule_v2.py is imported, which redirects
every state dir BEFORE gsd_mission / rollover load and traps rollover's import-time STATE_DIR.
"""
from __future__ import annotations

import contextlib
import io as _io
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_gsd_mission_capsule_v2 as h  # noqa: E402  (state dirs redirected at its import)

gm, mc, ro = h.gm, h.mc, h.ro
NOW, STATE, REPO = h.NOW, h.STATE, h.REPO
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(_io.StringIO()):
        return fn(*a, **k)


def certify_successor(mid_capsule_owner: str, key: str, claimant: str) -> int:
    """The successor's own two commands, through rollover (the CLI needs a real session id)."""
    quiet(ro.resume_flow, h.sealed(key), claimant, str(REPO), STATE, obligations=["execute phase 2: Wire it"])
    facts = ro.repo_facts(str(REPO))
    ans = {"goal": "STATE.md", "branch": facts.get("branch"), "head": (facts.get("head") or "")[:7],
           "next": "execute phase 2: Wire it"}
    if (h.sealed(key) or {}).get("degraded"):
        ans["dirty"] = str(len(facts.get("dirty") or []))
    rc, _ = quiet(ro.certify_flow, key, claimant, ans, STATE, mission_id=mid_capsule_owner)
    return rc


def audit_cli(mid, sd=STATE) -> int:
    return quiet(mc._cli, ["audit", "--mission", mid, "--state-dir", str(sd)])


def boom(*a, **k):
    raise OSError("injected fault")


def main() -> int:
    # ===================== chain audit, both poles =====================
    h.wipe()
    h.mission("m-a1", note="phase 2 half done: wire the gate next")
    h.run(h.host("m-a1"))                                   # seal -> authorize -> stop -> arm -> spawn
    succ = "9e9e9e9e-0000-4000-8000-0000000000a1"
    gm.ack_session(succ, now=NOW + 10)
    res = mc.audit_mission("m-a1", STATE)
    states = {x["link"].split(" ")[0]: x["state"] for x in res["links"]}
    check("V-MCF-AUDIT-OPEN-NOT-BROKEN", res["verdict"] == "INTACT" and "OPEN" in states.values(),
          f"{res['verdict']} {states}")
    rc = certify_successor("m-a1", "mission-m-a1-e1", succ)
    res = mc.audit_mission("m-a1", STATE)
    ok_links = [x["link"] for x in res["links"] if x["state"] == "OK"]
    check("V-MCF-AUDIT-INTACT-ROTATION",
          rc == 0 and res["verdict"] == "INTACT" and any(l.startswith("certified") for l in ok_links)
          and any(l.startswith("marker lifted") for l in ok_links) and audit_cli("m-a1") == 0,
          f"rc={rc} {res['verdict']} ok={ok_links}")
    # the same lineage with its seal row removed: BROKEN, naming the seal
    broken_sd = h.TMP / "audit-broken"
    shutil.rmtree(broken_sd, ignore_errors=True)
    broken_sd.mkdir()
    rows = (STATE / "rollover-ledger.jsonl").read_text(encoding="utf-8").splitlines()
    (broken_sd / "rollover-ledger.jsonl").write_text(
        "\n".join(r for r in rows if not ('"capsule_sealed"' in r and "mission-m-a1-e1" in r)) + "\n", encoding="utf-8")
    res = mc.audit_mission("m-a1", broken_sd)
    check("V-MCF-AUDIT-BROKEN-NAMES-LINK",
          res["verdict"] == "BROKEN" and (res.get("first_broken") or {}).get("link", "").startswith("sealed")
          and audit_cli("m-a1", broken_sd) == 1, str(res.get("first_broken")))
    check("V-MCF-AUDIT-UNREADABLE", audit_cli("m-nonexistent") == 2)
    # a v2 mission whose ledger shows nothing judged nothing: UNREADABLE, never INTACT; twin = real ledger
    def _ledger_raises(_m):
        raise OSError("injected: ledger unreadable")
    blind = mc.audit_mission("m-a1", STATE, events=lambda _m: [])
    raised = mc.audit_mission("m-a1", STATE, events=_ledger_raises)
    seen = mc.audit_mission("m-a1", STATE)
    check("V-MCF-AUDIT-BLIND-LEDGER-UNREADABLE",
          blind["verdict"] == "UNREADABLE" and raised["verdict"] == "UNREADABLE" and seen["verdict"] == "INTACT",
          f"blind={blind.get('reason')} raised={raised.get('reason')} seen={seen['verdict']}")
    h.mission("m-aleg", v2=False, note="n")
    res = mc.audit_mission("m-aleg", STATE)
    check("V-MCF-AUDIT-LEGACY-SKIPPED", res["verdict"] == "INTACT"
          and [x["state"] for x in res["links"]] == ["SKIPPED"], str(res["links"]))
    res = mc.audit_mission("m-aleg", STATE, events=lambda _m: [])
    check("V-MCF-AUDIT-BLIND-LEGACY-STILL-SKIPPED", res["verdict"] == "INTACT", str(res.get("reason")))

    # halt -> renewal lineage audited from the renewal (handoff), and a refused halt
    h.wipe()
    h.mission("m-ah", note="n", **h.SPENT)
    r = h.row_of(h.halt_run(h.host("m-ah", name="m-ah-e1")), "m-ah")
    nid = r.get("renewed_as")
    res = mc.audit_mission(nid, STATE) if nid else {"verdict": "NONE", "links": []}
    check("V-MCF-AUDIT-HALT-LINEAGE", res["verdict"] == "INTACT" and res.get("lineage") == ["m-ah", nid]
          and any(x["link"].startswith("halt handoff renewed") and x["state"] == "OK" for x in res["links"]),
          f"{res['verdict']} lineage={res.get('lineage')}")
    rec = gm.load("m-ah")
    gm.transition("m-ah", expect_epoch=rec["epoch"], expect_state=gm.HALTED, event="t", now=NOW,
                  continuity={**rec["continuity"], "capsule_key": "mission-m-ah-e9"})
    res = mc.audit_mission("m-ah", STATE)
    check("V-MCF-AUDIT-HALT-KEY-MISMATCH-BROKEN", res["verdict"] == "BROKEN"
          and "renewed with" in (res.get("first_broken") or {}).get("link", ""), str(res.get("first_broken")))

    # ===================== crash boundaries =====================
    # C2: authorized, the stop raises -> next pass REUSES the authorization (G3): one seal, one launch
    h.wipe()
    h.mission("m-c2", note="n")
    n_l = len(h.launches)
    rows = gm.supervise(now=NOW, sessions=h.host("m-c2"), gsd_status=h.GSD_OK, runner=h.launch_run,
                        stop_runner=boom, pid_alive=h.gone, capsule_io=h.io())
    mid_rec = gm.load("m-c2")
    seals_1 = sum(1 for e in json.loads("[" + ",".join((STATE / "rollover-ledger.jsonl").read_text(
        encoding="utf-8").splitlines()) + "]") if e.get("event") == "capsule_sealed" and e.get("session_id") == "mission-m-c2-e1")
    h.run(h.host("m-c2"), now=NOW + 60)
    seals_2 = sum(1 for line in (STATE / "rollover-ledger.jsonl").read_text(encoding="utf-8").splitlines()
                  if '"capsule_sealed"' in line and "mission-m-c2-e1" in line)
    check("V-MCF-C2-STOP-FAILS-AUTH-REUSED",
          (mid_rec.get("capsule_stop_authorized") or {}).get("epoch") == 1 and len(h.launches) == n_l + 1
          and seals_1 == seals_2 == 1 and "error" in h.row_of(rows, "m-c2"),
          f"seals={seals_1}->{seals_2} launches={len(h.launches) - n_l}")

    # C3: stopped, the arm raises -> nothing spawned; the next pass arms, THEN spawns
    h.wipe()
    h.mission("m-c3", note="n")
    real_arm = mc.arm_successor
    mc.arm_successor = boom
    n_l = len(h.launches)
    try:
        h.run(h.host("m-c3"))
    finally:
        mc.arm_successor = real_arm
    no_spawn = len(h.launches) == n_l
    h.run(h.host("m-c3", state="stopped", status=None), now=NOW + 60)
    mk = h.armed_at_spawn[-1] if len(h.launches) == n_l + 1 else None
    check("V-MCF-C3-ARM-FAILS-THEN-ARMED-BEFORE-SPAWN",
          no_spawn and mk is not None and mk.get("capsule_key") == "mission-m-c3-e1" and mk.get("worker") == "m-c3-e2",
          f"no_spawn={no_spawn} mk={mk}")

    # C6: the HALTED write loses its CAS after the hand-off seal -> nothing stopped; next pass halts once
    h.wipe()
    h.mission("m-c6", note="n", **h.SPENT)
    real_tr = gm.transition
    fired = []

    def flaky(mid, **kw):
        if kw.get("event") == "mission_halted" and not fired:
            fired.append(1)
            raise gm.CasConflict("injected: another supervisor moved the record")
        return real_tr(mid, **kw)

    gm.transition = flaky
    n_s = len(h.stops)
    try:
        h.halt_run(h.host("m-c6", name="m-c6-e1"))
    finally:
        gm.transition = real_tr
    stopped_in_fault = len(h.stops) - n_s
    h.halt_run(h.host("m-c6", name="m-c6-e1"), now=NOW + 60)
    rec = gm.load("m-c6")
    check("V-MCF-C6-HALT-CAS-NOTHING-STOPPED",
          stopped_in_fault == 0 and rec["state"] == gm.HALTED and (rec.get("continuity") or {}).get("kind") == "handoff"
          and len(h.stops) == n_s + 1, f"stops_in_fault={stopped_in_fault} total={len(h.stops) - n_s} {rec['state']}")

    # C7: HALTED, the recovery seal raises -> `refused`, never a silent `recovery` with no key and no renewal
    h.wipe()
    h.mission("m-c7", note="n", **h.SPENT)
    real_compile = mc.compile_mission_capsule

    def compile_fail_recovery(rec, **kw):
        if kw.get("origin") == "recovery":
            raise OSError("injected: disk full")
        return real_compile(rec, **kw)

    mc.compile_mission_capsule = compile_fail_recovery
    try:
        r = h.row_of(h.halt_run(h.host("m-c7", name="m-c7-e1", status="busy")), "m-c7")
    finally:
        mc.compile_mission_capsule = real_compile
    cont = gm.load("m-c7").get("continuity") or {}
    check("V-MCF-C7-RECOVERY-RAISES-REFUSED",
          cont.get("kind") == "refused" and "raised" in cont.get("reason", "") and not r.get("renewed_as")
          and "renewal_refused_no_capsule" in h.events("m-c7"), f"cont={cont} renewed={r.get('renewed_as')}")

    # C10: the deadline stop raises -> not counted; the next pass stops and counts once
    h.wipe()
    key = "mission-m-c10-e1"
    succ = "9e9e9e9e-0000-4000-8000-000000000c10"
    h.mission("m-c10", epoch=2, capsule_key=key, capsule_acked_at=NOW)
    rec = gm.load("m-c10")
    gm.transition("m-c10", expect_epoch=2, expect_state=rec["state"], event="t", now=NOW,
                  owner={"session_id": succ, "pid": 999, "kind": "background"})
    ro.precert_arm("m-c10", {"worker": "m-c10-e2", "epoch": 2, "capsule_key": key, "cwd": str(REPO),
                             "resume_cmd": "/gsd-autonomous"}, STATE)
    srow = [{"sessionId": succ, "status": "busy", "state": "working", "kind": "background", "id": "9e9e9e9e",
             "pid": 999, "name": "m-c10-e2"}]
    gm.supervise(now=NOW + gm.CAPSULE_CERTIFY_DEADLINE_S + 1, sessions=srow, gsd_status=h.GSD_OK,
                 runner=h.launch_run, stop_runner=boom, pid_alive=h.gone, capsule_io=h.io())
    first = (gm.load("m-c10").get("capsule_attempts") or {}).get(key)
    h.run(srow, now=NOW + gm.CAPSULE_CERTIFY_DEADLINE_S + 60)
    second = (gm.load("m-c10").get("capsule_attempts") or {}).get(key)
    check("V-MCF-C10-DEADLINE-STOP-FAILS-NOT-COUNTED", first is None and second == 1,
          f"after fault={first} after clean={second}")

    # C11: the note request's stop raises -> asked flag already set; the next turn end falls back at once
    h.wipe()
    h.mission("m-c11")
    gm.supervise(now=NOW, sessions=h.host("m-c11"), gsd_status=h.GSD_OK, runner=h.launch_run,
                 stop_runner=boom, pid_alive=h.gone, capsule_io=h.io())
    asked = (gm.load("m-c11").get("capsule_note_asked") or {}).get("epoch")
    n_l = len(h.launches)
    h.run(h.host("m-c11"), now=NOW + 60)
    rec = gm.load("m-c11")
    check("V-MCF-C11-NOTE-STOP-FAILS-FALLBACK",
          asked == 1 and (rec.get("capsule_stop_authorized") or {}).get("origin") == "supervisor_fallback"
          and len(h.launches) == n_l + 1, f"asked={asked} auth={rec.get('capsule_stop_authorized')}")

    # C12 (T6 gap): a failed same-session continuation, then a replace -> sealed for THIS epoch via the
    # resumed session; never armed with the previous, already-certified key. Legacy twin unaffected.
    for gate, v2 in (("V-MCF-C12-CONTINUATION-FAILED-SEALS-EPOCH", True),
                     ("V-MCF-C12-CONTROL-LEGACY", False)):
        h.wipe()
        mid = "m-c12" if v2 else "m-c12l"
        h.mission(mid, v2=v2, epoch=2, **({"capsule_key": f"mission-{mid}-e1"} if v2 else {}))
        rec = gm.load(mid)
        sid = rec["owner"]["session_id"]
        gm.transition(mid, expect_epoch=2, expect_state=rec["state"], event="t", now=NOW, state=gm.LAUNCHING,
                      owner=None, previous_owner=rec["owner"],
                      pending={"kind": "turn_continuation", "epoch": 2, "bg_id": sid[:8], "session_id": sid,
                               "deadline": NOW, "failed": "resume refused (rc=1)"})
        if v2:
            side = ro.capsule_path(f"mission-{mid}-e1", STATE).with_suffix(".certified")
            side.parent.mkdir(parents=True, exist_ok=True)
            side.write_text("2026-10-05T00:00:00Z", encoding="utf-8")
        n_l = len(h.launches)
        rows = h.run(h.host(mid, state="stopped", status=None), now=NOW + 60)
        mk = h.armed_at_spawn[-1] if len(h.launches) == n_l + 1 else None
        if v2:
            check(gate, mk is not None and mk.get("capsule_key") == f"mission-{mid}-e2"
                  and (gm.load(mid).get("capsule_stop_authorized") or {}).get("origin") == "recovery",
                  f"mk={mk} row={h.row_of(rows, mid).get('action')}/{h.row_of(rows, mid).get('held')}")
        else:
            check(gate, len(h.launches) == n_l + 1 and ro.precert_read(mid, STATE) is None
                  and not gm.load(mid).get("capsule_key"), f"launches={len(h.launches) - n_l}")

    trap_hits = list(h.TRAP.rglob("*")) if h.TRAP.exists() else []
    check("V-MCF-TRAP-UNTOUCHED", not trap_hits, str(trap_hits[:3]))
    print(f"MCF_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
