#!/usr/bin/env python3
"""V-FAN-* / V-QUOTA-* gates: causal fan-out ledger (C2) + provider quota adapter (C1b).

Hermetic fixtures only; no model call. Every class assertion has a contrasting
control, and the unknown branches are asserted reachable, not just defaulted."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fanout_ledger as fl  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
PRICES = {"claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_write_5m": 5.0,
                              "cache_write_1h": 8.0, "cache_read": 0.2}}
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def user(pid, h, sess, origin=None, source=None, agent=None):
    o = {"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": sess, "uuid": f"u{h}"}
    if origin:
        o["origin"] = {"kind": origin}
    if source:
        o["promptSource"] = source
    if agent:
        o["agentId"] = agent
    return json.dumps(o) + "\n"


def asst(mid, h, sess, cr=1000, spawn=None, quota=None, agent=None, model="claude-opus-5-5"):
    content = []
    if spawn:
        tuid, stype, mreq = spawn
        inp = {"subagent_type": stype, "prompt": "x"}
        if mreq:
            inp["model"] = mreq
        content.append({"type": "tool_use", "id": tuid, "name": "Agent", "input": inp})
    o = {"type": "assistant", "timestamp": iso(h), "sessionId": sess, "requestId": "r" + mid,
         "message": {"id": mid, "model": model, "content": content,
                     "usage": {"input_tokens": 1, "cache_read_input_tokens": cr,
                               "cache_creation_input_tokens": 0, "output_tokens": 5}}}
    if quota:
        o["quotaLimits"] = quota
    if agent:
        o["agentId"] = agent
    return json.dumps(o) + "\n"


def rejected(reset_h):
    return {"status": "rejected", "rateLimitType": "seven_day", "resetsAt": T0 + reset_h * 3600,
            "overageDisabledReason": "org_level_disabled"}


def build(root: Path):
    p = root / "C--proj-a"
    (p / "S1" / "subagents").mkdir(parents=True)
    (p / "S1.jsonl").write_text(
        user("P1", 1, "S1", origin="human", source="typed")
        + asst("m1", 1.1, "S1", spawn=("tu1", "gsd-executor", None))
        + asst("m2", 1.2, "S1", spawn=("tu2", "Explore", "sonnet"))
        + user("P2", 2, "S1", origin="task-notification")
        + asst("m3", 2.1, "S1")
        + user("P0", 0.5, "S1")                                   # no origin -> UNKNOWN
        + asst("m0", 0.6, "S1")
        + json.dumps({"type": "assistant", "timestamp": iso(3), "sessionId": "S1",
                      "message": {"model": "<synthetic>", "usage": {"output_tokens": 0}},
                      "quotaLimits": rejected(100)}) + "\n",
        encoding="utf-8")
    sub = p / "S1" / "subagents" / "agent-a1.jsonl"
    sub.write_text(user("P1", 1.15, "S1", agent="a1") + asst("s1", 1.16, "S1", agent="a1")
                   + asst("s2", 1.17, "S1", agent="a1"), encoding="utf-8")
    (p / "S1" / "subagents" / "agent-a1.meta.json").write_text(
        json.dumps({"agentType": "gsd-executor", "toolUseId": "tu1", "spawnDepth": 1}),
        encoding="utf-8")
    orphan = p / "S1" / "subagents" / "agent-zz.jsonl"           # no meta.json
    orphan.write_text(asst("s9", 1.5, "S1", agent="zz"), encoding="utf-8")
    m = root / "C--mission"
    m.mkdir()
    (m / "M1.jsonl").write_text(
        json.dumps({"type": "custom-title", "customTitle": "m-abc123-e1", "sessionId": "M1"}) + "\n"
        + user("PM", 4, "M1", origin="sdk", source="sdk") + asst("mm1", 4.1, "M1")
        + json.dumps({"type": "assistant", "timestamp": iso(4.2), "sessionId": "M1",
                      "message": {"model": "<synthetic>", "usage": {"output_tokens": 0}},
                      "quotaLimits": dict(rejected(50), overageDisabledReason="out_of_credits")})
        + "\n", encoding="utf-8")
    return p / "S1.jsonl"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "projects"
        main_fp = build(root)
        con = ux.connect(Path(td) / "ix.sqlite")
        r = ux.refresh(con, root, deadline_s=30)
        ok("V-FAN-REFRESH", r["status"] == "OK", json.dumps(r))
        w = ux.window(con, T0, T0 + 10 * 3600, PRICES)
        ok("V-FAN-DEDUP-PRESERVED", w["calls"] == 8 and w["subagent_calls"] == 3,
           f"calls={w['calls']} sub={w['subagent_calls']} (synthetic quota rows are not calls)")

        t1 = fl.prompt_tree(con, "P1")
        kids = {c["tool_use_id"]: c for c in t1["spawns"]}
        ok("V-FAN-HUMAN-TREE", t1["root"] == "HUMAN" and t1["parent"]["calls"] == 2
           and kids["tu1"]["calls"] == 2 and kids["tu1"]["transcript"] == "FOUND"
           and t1["total"]["calls"] == 4,
           f"root={t1['root']} parent={t1['parent']['calls']} child={kids['tu1']['calls']} total={t1['total']['calls']}")
        ok("V-FAN-MODEL-REQUESTED", kids["tu1"]["model_requested"] == "inherit"
           and kids["tu2"]["model_requested"] == "sonnet" and kids["tu2"]["transcript"] == "NOT_INDEXED",
           f"tu1={kids['tu1']['model_requested']} tu2={kids['tu2']['model_requested']}/{kids['tu2']['transcript']}")

        rows = fl.load_calls(con, T0, T0 + 10 * 3600, PRICES)
        by_k = {r["k"]: r for r in rows}
        ok("V-FAN-CONTINUATION", by_k["m3|rm3"]["root"] == "CONTINUATION"
           and by_k["m1|rm1"]["root"] == "HUMAN", "P2 task-notification vs P1 typed")
        ok("V-FAN-MISSION", by_k["mm1|rmm1"]["root"] == "MISSION",
           f"mission title -> {by_k['mm1|rmm1']['root']} (origin sdk would have said SDK)")
        ok("V-FAN-UNKNOWN-TYPED", by_k["m0|rm0"]["root"] == "UNKNOWN"
           and by_k["s9|rs9"]["root"] == "UNKNOWN" and by_k["s9|rs9"]["linked"] is False
           and by_k["s1|rs1"]["linked"] is True,
           "no-origin prompt and meta-less subagent stay UNKNOWN; linked control holds")
        tm = fl.prompt_tree(con, "PM")
        ok("V-FAN-PROMPT-TREE-MISSION", tm["root"] == "MISSION" and t1["root"] == "HUMAN",
           f"prompt PM tree -> {tm['root']} (must agree with load_calls/top; P1 control HUMAN)")
        ok("V-FAN-CLASSIFY-SDK", fl.classify_root("sdk", "sdk", None, None) == "SDK"
           and fl.classify_root(None, "system", None, None) == "SYSTEM"
           and fl.classify_root(None, None, None, None) == "UNKNOWN", "SDK / SYSTEM / UNKNOWN reachable")

        s = fl.summary(con, T0, T0 + 10 * 3600)
        ok("V-FAN-SUMMARY", s["by_root_class"]["HUMAN"]["calls"] == 4
           and s["subagent_links"] == {"linked": 2, "unlinked": 1, "depth": {1: 2, None: 1}}
           and "inherit -> claude-opus-5-5" in s["subagent_model_policy"]
           and s["by_workflow"]["GSD:executor"]["calls"] == 2,
           json.dumps({k: s[k] for k in ("subagent_links", "subagent_model_policy")}, default=str)[:200])
        ok("V-FAN-PROMPT-FANOUT", s["human_prompt_fanout"]["max_calls"] == 4,
           f"{s['human_prompt_fanout']}")

        # Incremental: a call appended with no new user line belongs to the prompt
        # persisted from the previous pass; a new user line switches it (control).
        with open(main_fp, "a", encoding="utf-8") as fh:
            fh.write(asst("m4", 2.5, "S1"))
        ux.refresh(con, root, deadline_s=30)
        with open(main_fp, "a", encoding="utf-8") as fh:
            fh.write(user("P3", 5, "S1", origin="human") + asst("m5", 5.1, "S1"))
        ux.refresh(con, root, deadline_s=30)
        pids = dict(con.execute("SELECT k, prompt_id FROM calls WHERE k IN ('m4|rm4','m5|rm5')"))
        ok("V-FAN-INCREMENTAL-PROMPT", pids == {"m4|rm4": "P0", "m5|rm5": "P3"},
           f"{pids} (P0 was the last prompt line before the append)")

        # C1b provider adapter.
        q = ux.quota_status(con, T0 + 10 * 3600)
        ok("V-QUOTA-ADAPTER", q["signal"] == "PRESENT" and q["weekly_windows"] == 2
           and len(q["rejected_now"]) == 2,
           f"windows={list(q['windows'])} rejected_now={q['rejected_now']}")
        q0 = ux.quota_status(con, T0 - 30 * 86400)
        ok("V-QUOTA-NO-SIGNAL", q0["signal"] == "NO_SIGNAL", "no rows -> NO_SIGNAL, never 'fine'")
        line = ux.advisory_line({"state": "NORMAL", "reasons": [], "provider": q})
        quiet = ux.advisory_line({"state": "NORMAL", "reasons": [], "provider": q0})
        ok("V-QUOTA-ADVISORY", line and "RECHAZADA" in line and quiet is None, f"{line}")
        con.close()

        # Schema migration from a v1 index: columns added, offsets reset, version 2.
        v1 = Path(td) / "v1.sqlite"
        c1 = sqlite3.connect(str(v1))
        c1.executescript("CREATE TABLE files(path TEXT PRIMARY KEY, offset INTEGER, size INTEGER,"
                         " mtime_ns INTEGER, is_sub INTEGER, entrypoint TEXT);"
                         "CREATE TABLE calls(k TEXT PRIMARY KEY, file TEXT, ts REAL, model TEXT,"
                         " is_sub INTEGER, entrypoint TEXT, inp INTEGER, cw INTEGER, cw5 INTEGER,"
                         " cw1 INTEGER, cr INTEGER, out INTEGER);"
                         "INSERT INTO files VALUES('x', 500, 500, 1, 0, 'cli');")
        c1.commit()
        c1.close()
        c2 = ux.connect(v1)
        cols = {r[1] for r in c2.execute("PRAGMA table_info(calls)")}
        off = c2.execute("SELECT offset, size FROM files WHERE path='x'").fetchone()
        ver = c2.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()[0]
        ok("V-FAN-SCHEMA-MIGRATION", {"session", "prompt_id", "agent_id"} <= cols
           and off == (0, -1) and ver == "2", f"offset/size={off} version={ver}")
        c2.close()

        # A session whose parent transcript was indexed from ANOTHER project dir (a
        # copied/forked session): a subagent call belongs to the dir that holds its own
        # transcript, never to whichever spawn copy the index kept (real: 8b2c7516).
        r2 = Path(td) / "projects2"
        (r2 / "C--own" / "S2" / "subagents").mkdir(parents=True)
        (r2 / "C--copy").mkdir()
        (r2 / "C--copy" / "S2.jsonl").write_text(
            user("Q1", 1, "S2", origin="human", source="typed")
            + asst("q1", 1.1, "S2", spawn=("tu9", "Explore", None)), encoding="utf-8")
        sd = r2 / "C--own" / "S2" / "subagents"
        (sd / "agent-b1.jsonl").write_text(asst("qs1", 1.2, "S2", agent="b1"), encoding="utf-8")
        (sd / "agent-b1.meta.json").write_text(
            json.dumps({"agentType": "Explore", "toolUseId": "tu9", "spawnDepth": 1}), encoding="utf-8")
        c3 = ux.connect(Path(td) / "ix2.sqlite")
        ux.refresh(c3, r2, deadline_s=30)
        proj = {r["k"]: r["project"] for r in fl.load_calls(c3, T0, T0 + 10 * 3600, PRICES)}
        ok("V-FAN-PROJECT-OWN-TRANSCRIPT", proj.get("qs1|rqs1") == "C--own"
           and proj.get("q1|rq1") == "C--copy", f"{proj} (parent control stays C--copy)")
        c3.close()

    total = PASS + FAIL
    print(f"FANOUT_LEDGER_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
