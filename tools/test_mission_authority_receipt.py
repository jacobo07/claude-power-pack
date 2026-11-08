#!/usr/bin/env python
"""V-AR-* gates for T1 F2/F3 (vault/plans/t1-incident-compiled-certification-20261023.md section 64-70).

Measured 2026-10-23 (m-260aa89142c8): the 80M authority was written after an Owner "a" typed in another pane, on an
option that quoted a 06:41Z snapshot (50.3M) while live spend was ~141M. The ceiling arrived below spend and tripped
2m21s later, and its provenance existed only as a free-text reason. These gates pin: the CLI refuses an act with no
owner turn; an owner turn resolves to exactly one typed user message; a replay is a no-op; a stale seq conflicts; a
ceiling with no room above live spend is refused unless recognised; topology and status show live spend and lineage.
Every refusal has a paired admitted control. Hermetic: temp state and projects dirs.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-authority-receipt-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

NOW = 1_800_000_000.0
M = 1_000_000
OWNER = "15f5057c-0000-4000-8000-00000000c0de"
TS = "2026-10-23T09:36:51.123Z"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def transcript(sid: str, rows: list[dict]) -> None:
    d = Path(TMP) / "projects" / "C--proj"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def user(ts: str, content, **kw) -> dict:
    return {"type": "user", "timestamp": ts, "uuid": f"u-{ts}-{len(str(content))}",
            "message": {"role": "user", "content": content}, **kw}


def mission(mid: str, authority: int | None = 56 * M) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    extra = {"authority_tokens": authority} if authority else {}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, max_hours=100.0, owner=owner, **extra)


def refused(fn) -> str:
    try:
        fn()
    except gm.MissionError as exc:
        return str(exc)
    return ""


def main() -> int:
    transcript(OWNER, [
        user(TS, "a"),
        user("2026-10-23T09:40:00.000Z", [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]),
        user("2026-10-23T09:41:00.000Z", "<task-notification>agent done</task-notification>"),
        user("2026-10-23T09:42:00.000Z", "y", isSidechain=True),
        user("2026-10-23T09:43:00.000Z", "y", isMeta=True),
        user("2026-10-23T09:44:10.000Z", "one"),
        user("2026-10-23T09:44:20.000Z", "two"),
    ])
    spent = {"v": 141 * M}
    meter = lambda r: spent["v"]  # noqa: E731

    # 1. owner-turn resolution: exactly one typed user message.
    t = gm.verify_owner_turn(f"{OWNER}:2026-10-23T09:36:51")
    check("V-AR-TURN-RESOLVES", t["text_head"] == "a" and len(t["text_sha256"]) == 64 and t["uuid"], str(t)[:120])
    for label, ref in (("TOOL-RESULT", f"{OWNER}:2026-10-23T09:40"), ("NOTIFICATION", f"{OWNER}:2026-10-23T09:41"),
                       ("SIDECHAIN", f"{OWNER}:2026-10-23T09:42"), ("META", f"{OWNER}:2026-10-23T09:43"),
                       ("AMBIGUOUS", f"{OWNER}:2026-10-23T09:44"), ("NO-MATCH", f"{OWNER}:2026-10-23T11:00"),
                       ("SUBAGENT-SESSION", "agent-a33215aa0000:2026-10-23T09:36"),
                       ("NO-TRANSCRIPT", "deadbeef-0000-4000-8000-000000000000:2026-10-23T09:36"),
                       ("MALFORMED", "no-colon")):
        check(f"V-AR-TURN-REFUSES-{label}", bool(refused(lambda r=ref: gm.verify_owner_turn(r))), label)
    check("V-AR-CONTROL-AMBIGUOUS-RESOLVED-BY-FULL-TS",
          gm.verify_owner_turn(f"{OWNER}:2026-10-23T09:44:20")["text_head"] == "two")

    # 2. CLI: no owner turn -> refused, record untouched; with one -> set and receipted.
    rec = mission("m-ar0000000001")
    rc = gm._cli(["authority", "--mission", "m-ar0000000001", "--tokens", "200M"])
    check("V-AR-CLI-NO-RECEIPT-REJECTED", rc == 2 and gm.load("m-ar0000000001")["authority_tokens"] == 56 * M, f"rc={rc}")
    gm_spend = gm.set_authority  # the CLI path measures through mission_spend; the function path takes a meter
    out = gm_spend("m-ar0000000001", "200M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", actor="coord-pane",
                   expected_seq=rec["seq"], spent_fn=meter, now=NOW + 10)
    r = (out.get("authority_receipts") or [{}])[-1]
    check("V-AR-RECEIPT-TYPED", out["authority_tokens"] == 200 * M and r.get("prev") == 56 * M
          and r.get("new") == 200 * M and r["owner_turn"]["text_head"] == "a" and r.get("actor") == "coord-pane"
          and r.get("spent_at_set") == 141 * M and r.get("expected_seq") == rec["seq"], str(r)[:200])
    rows = [e for e in gm.lr.ledger_events("m-ar0000000001") if e.get("event") == "authority_set"]
    check("V-AR-LEDGER-CARRIES-RECEIPT", rows and (rows[-1].get("receipt") or {}).get("owner_turn"), str(rows[-1:])[:160])

    # 3. replay: same turn + same figure -> no-op; same turn + other figure -> refused.
    seq = gm.load("m-ar0000000001")["seq"]
    again = gm_spend("m-ar0000000001", "200M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter)
    check("V-AR-REPLAY-IDEMPOTENT", again["seq"] == seq and len(again["authority_receipts"]) == 1,
          f"seq {seq}->{again['seq']}")
    check("V-AR-REPLAY-OTHER-FIGURE-REFUSED", "already authorized" in refused(lambda: gm_spend(
          "m-ar0000000001", "300M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter)))

    # 4. stale seq -> conflict; the right seq -> admitted.
    mission("m-ar0000000002")
    stale = gm.load("m-ar0000000002")["seq"] - 1
    check("V-AR-STALE-SEQ-CONFLICT", bool(refused(lambda: gm_spend(
          "m-ar0000000002", "200M", owner_turn=f"{OWNER}:2026-10-23T09:44:10", expected_seq=stale, spent_fn=meter))),
          "a record that moved since the decision conflicts")
    ok = gm_spend("m-ar0000000002", "200M", owner_turn=f"{OWNER}:2026-10-23T09:44:10",
                  expected_seq=gm.load("m-ar0000000002")["seq"], spent_fn=meter)
    check("V-AR-CONTROL-CURRENT-SEQ-ADMITTED", ok["authority_tokens"] == 200 * M)

    # 5. I3: the T1 80M on a live 141M is refused; recognised overrun and a feasible ceiling are admitted.
    mission("m-ar0000000003")
    why = refused(lambda: gm_spend("m-ar0000000003", "80M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter))
    check("V-AR-CEILING-BELOW-SPEND-REFUSED", "live spend 141,000,000" in why and
          gm.load("m-ar0000000003")["authority_tokens"] == 56 * M, why[:140])
    check("V-AR-CEILING-INSIDE-RESERVE-REFUSED", bool(refused(lambda: gm_spend(
          "m-ar0000000003", "141.5M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter))),
          "141.5M - 1M reserve <= 141M")
    rec3 = gm_spend("m-ar0000000003", "80M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter,
                    recognize_overrun=True)
    check("V-AR-RECOGNIZED-OVERRUN-ADMITTED", rec3["authority_tokens"] == 80 * M
          and rec3["authority_receipts"][-1]["recognize_overrun"] is True)
    mission("m-ar0000000004")
    check("V-AR-CONTROL-FEASIBLE-CEILING-ADMITTED", gm_spend("m-ar0000000004", "150M",
          owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=meter)["authority_tokens"] == 150 * M)

    def boom(_r):
        raise OSError("meter down")
    mission("m-ar0000000005")
    un = gm_spend("m-ar0000000005", "10M", owner_turn=f"{OWNER}:2026-10-23T09:36:51", spent_fn=boom)
    check("V-AR-UNMEASURED-ADMITTED-AND-NAMED", un["authority_tokens"] == 10 * M
          and un["authority_receipts"][-1]["spent_at_set"] is None)

    # 6. F3: live spend with its time; topology carries the lineage; the Owner packet labels its snapshot.
    ls = gm.live_spend(gm.load("m-ar0000000004"), measure=meter)
    check("V-AR-LIVE-SPEND-TIMED", ls["processed"] == 141 * M and ls["measured_at"].endswith("Z")
          and ls["room_after_reserve"] == 150 * M - 1 * M - 141 * M, str(ls))
    check("V-AR-LIVE-SPEND-UNMEASURED-NAMED", gm.live_spend(gm.load("m-ar0000000004"), measure=boom)["processed"] is None)
    lin = gm.authority_lineage(gm.load("m-ar0000000001"))
    check("V-AR-LINEAGE", lin["tokens"] == 200 * M and lin["receipts"] and any(x.get("owner_turn") for x in lin["set_rows"]),
          str(lin)[:160])
    src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
    check("V-AR-PACKET-LABELS-SNAPSHOT", "the hold's snapshot, not live" in src and "--owner-turn <SESSION>:<TIMESTAMP>" in src)

    # 7. programmatic callers (topup, Decision Plane) keep working without an owner turn.
    mission("m-ar0000000006")
    check("V-AR-CONTROL-PROGRAMMATIC-CALLER", gm_spend("m-ar0000000006", "300M", reason="mission-auto-topup",
          spent_fn=meter)["authority_tokens"] == 300 * M)

    print(f"AUTHORITY_RECEIPT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
