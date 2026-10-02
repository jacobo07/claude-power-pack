#!/usr/bin/env python3
"""V-DISP-* gates: displacement of shadow-deferred spawns (plan s14 S3, audit ccp-s14-s3-audit).

Each guard in estate_displacement.classify has a case only it can catch, so a
build that drops the guard goes red: an async launch ack whose child is still
running (finish = child's last call, not result_ts), an equivalent in another
root, a refused launch that has child calls anyway, the spawn matching itself,
the horizon edge, precedence on a spawn that satisfies two classes, and an
unresolved root. Hermetic temp index; no model call."""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import estate_displacement as ed  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
T = 1_790_000_000.0
H = ed.LATER_HORIZON_S


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def add(con, tuid, ts, h, err=0, child=None, result_ts=None):
    """A spawn row, plus a child transcript with calls at the given times."""
    con.execute("INSERT INTO spawns(tool_use_id, ts, input_hash, is_error, result_ts) "
                "VALUES (?,?,?,?,?)", (tuid, ts, h, err, result_ts))
    if child:
        f = f"C:/x/{tuid}/subagents/agent.jsonl"
        con.execute("INSERT INTO subagents(file, tool_use_id) VALUES (?,?)", (f, tuid))
        for i, ct in enumerate(child):
            con.execute("INSERT INTO calls(k, file, ts) VALUES (?,?,?)", (f"{tuid}-{i}", f, ct))


def row(tuid, ts, h, root="R", calls=3, cr=300):
    return {"tool_use_id": tuid, "ts": ts, "input_hash": h, "prompt": root,
            "subtree_calls": calls, "subtree_cache_read": cr}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        con = ux.connect(Path(td) / "i.sqlite")
        # judged spawns are all at T; peers vary one property each
        add(con, "reuse_peer", T - 100, "hR", child=[T - 90, T - 10])           # finished before T
        add(con, "active_peer", T - 100, "hA", child=[T - 90, T + 50],          # async ack <= T,
            result_ts=T - 99)                                                   # child still running
        add(con, "later_peer", T + 60, "hL", child=[T + 70])
        add(con, "far_peer", T + H + 60, "hF", child=[T + H + 70])
        add(con, "xroot_peer", T - 100, "hX", child=[T - 90, T - 10])           # other root
        add(con, "refused_peer", T - 100, "hE", err=1, child=[T - 90, T - 10])  # refused launch
        add(con, "prec_a", T - 100, "hP", child=[T - 90, T - 10])               # REUSABLE ...
        add(con, "prec_b", T + 60, "hP", child=[T + 70])                        # ... and RAN_LATER
        add(con, "noroot_peer", T - 100, "hN", child=[T - 90, T - 10])
        add(con, "simul_peer", T, "hS", child=[T + 1, T + 40])     # a DISTINCT spawn, same instant
        for tuid, h in (("j_reuse", "hR"), ("j_active", "hA"), ("j_later", "hL"),
                        ("j_far", "hF"), ("j_xroot", "hX"), ("j_refused", "hE"),
                        ("j_prec", "hP"), ("j_self", "hS"), ("j_nohash", None),
                        ("j_noroot", "hN"), ("j_allowed", "hR")):
            add(con, tuid, T, h, child=[T + 5, T + 9])
        con.commit()

        universe = [row("reuse_peer", T - 100, "hR"), row("active_peer", T - 100, "hA"),
                    row("later_peer", T + 60, "hL"), row("far_peer", T + H + 60, "hF"),
                    row("xroot_peer", T - 100, "hX", root="OTHER"),
                    row("refused_peer", T - 100, "hE"), row("prec_a", T - 100, "hP"),
                    row("prec_b", T + 60, "hP"), row("noroot_peer", T - 100, "hN", root=None),
                    row("simul_peer", T, "hS")]
        judged = [row("j_reuse", T, "hR", cr=1000), row("j_active", T, "hA"),
                  row("j_later", T, "hL", cr=7000), row("j_far", T, "hF"),
                  row("j_xroot", T, "hX"), row("j_refused", T, "hE"), row("j_prec", T, "hP"),
                  row("j_self", T, "hS"), row("j_nohash", T, None),
                  row("j_noroot", T, "hN", root=None), row("j_allowed", T, "hR", cr=99999),
                  row("j_notrans", T, "hZ", calls=None, cr=None)]
        universe += judged
        verdict = {r["tool_use_id"]: "WOULD_DEFER" for r in judged}
        verdict["j_allowed"] = "ALLOW"
        res = ed.displacement(con, judged, verdict, universe)
        got = {r["tool_use_id"]: r["class"] for r in res["spawns"]}

        expect = {"j_reuse": ed.REUSABLE, "j_active": ed.ACTIVE, "j_later": ed.RAN_LATER,
                  "j_far": ed.UNKNOWN, "j_xroot": ed.UNKNOWN, "j_refused": ed.UNKNOWN,
                  "j_prec": ed.REUSABLE, "j_self": ed.UNKNOWN, "j_nohash": ed.NO_HASH,
                  "j_noroot": ed.UNKNOWN, "j_notrans": ed.UNKNOWN}
        for tuid, gate in (("j_reuse", "V-DISP-REUSABLE"),
                           ("j_active", "V-DISP-ACK-IS-NOT-FINISH"),
                           ("j_later", "V-DISP-RAN-LATER"), ("j_far", "V-DISP-HORIZON"),
                           ("j_xroot", "V-DISP-SAME-ROOT"), ("j_refused", "V-DISP-REFUSED-LAUNCH"),
                           ("j_prec", "V-DISP-PRECEDENCE"), ("j_self", "V-DISP-SIMULTANEOUS"),
                           ("j_nohash", "V-DISP-NO-HASH"), ("j_noroot", "V-DISP-UNRESOLVED-ROOT")):
            ok(gate, got.get(tuid) == expect[tuid], f"{tuid}: {got.get(tuid)} (want {expect[tuid]})")

        ok("V-DISP-ALLOW-EXCLUDED", "j_allowed" not in got and res["judged_not_allowed"] == 11,
           f"judged_not_allowed={res['judged_not_allowed']}")
        upper = res["possible_saving_cache_read"]["upper"]
        ok("V-DISP-MOVED-NOT-SAVED", res["moved_not_saved_cache_read"] == 7000
           and upper == sum(r["subtree_cache_read"] or 0 for r in judged
                            if r["tool_use_id"] not in ("j_allowed", "j_later")),
           f"moved={res['moved_not_saved_cache_read']} possible_upper={upper}")
        ok("V-DISP-NO-TRANSCRIPT-COUNTED", res["no_transcript"] == 1, f"{res['no_transcript']}")
        ok("V-DISP-NEVER-ASSERTED", not {"ELIMINATED", "CONSUMED"} & set(got.values())
           and res["never_asserted"] == ["ELIMINATED", "CONSUMED"], str(res["never_asserted"]))
        con.close()                       # Windows cannot remove an open sqlite file

    # Read-only by construction: the same scan V-SPV2-NO-WRITE-SQL applies to estate_shadow.
    src = (HERE / "estate_displacement.py").read_text(encoding="utf-8")
    bad = re.findall(r"\b(INSERT|UPDATE|DELETE|REPLACE INTO|ALTER|DROP|CREATE)\b\s|executescript",
                     src, re.I)
    ok("V-DISP-NO-WRITE-SQL", not bad, f"write-SQL tokens: {bad}")

    # Hindsight stays retrospective: the live decider never imports it, and replay_v2
    # hands it no receipt object, only a fresh verdict map built after receipts are final.
    sched = (HERE.parent / "modules" / "cognitive_os" / "scheduler.py").read_text(encoding="utf-8")
    es = (HERE / "estate_shadow.py").read_text(encoding="utf-8")
    call = re.search(r"ed\.displacement\(([^)]*)\)", es)
    after = es.find("reconstructed = ") < es.find("ed.displacement(")
    ok("V-DISP-RETROSPECTIVE-ONLY", "estate_displacement" not in sched and call is not None
       and "receipts" not in call.group(1) and after,
       f"scheduler imports it: {'estate_displacement' in sched}; call args: "
       f"{call.group(1) if call else None}; after receipts final: {after}")

    print(f"DISPLACEMENT_PASS={PASS}/{PASS + FAIL}  threshold={PASS + FAIL}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
