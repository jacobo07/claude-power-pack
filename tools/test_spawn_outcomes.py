#!/usr/bin/env python3
"""V-SPOUT-* gates: a requested spawn is not an executed one (plan s12 commit 4, audit G4).

The index records the parent's tool_result for every Agent/Task tool_use
(spawns.result_ts / is_error / result_head); fanout_ledger.spawn_outcome turns
those facts plus the subagent link into REQUESTED / RAN / HOOK_BLOCKED /
FAILED_TO_START / FAILED / RETURNED. HOOK_BLOCKED is decided by a declared
marker set, and every guard marker is pinned to the live guard source so a
reworded guard turns this gate red instead of silently reclassifying its
denials as FAILED_TO_START. Hermetic; no model call."""
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
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
SESS = "S1"


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(mid, h, spawns=()):
    content = [{"type": "tool_use", "id": s, "name": "Agent",
                "input": {"subagent_type": "Explore", "prompt": "x"}} for s in spawns]
    return json.dumps({"type": "assistant", "timestamp": iso(h), "sessionId": SESS,
                       "requestId": "r" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "content": content,
                                   "usage": {"input_tokens": 1, "cache_read_input_tokens": 100,
                                             "cache_creation_input_tokens": 0,
                                             "output_tokens": 5}}}) + "\n"


def human(pid, h):
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": SESS,
                       "origin": {"kind": "human"}}) + "\n"


def result(tuid, h, text, is_error, pid="P1", as_list=False):
    """A tool_result line as the harness writes it: a user line that ALSO carries
    the promptId (so the result must be read before the promptId branch)."""
    body = [{"type": "text", "text": text}] if as_list else text
    c = {"type": "tool_result", "tool_use_id": tuid, "content": body}
    if is_error:
        c["is_error"] = True
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": SESS,
                       "message": {"role": "user", "content": [c]},
                       "toolUseResult": ("Error: " + text) if is_error else text}) + "\n"


def subagent(proj: Path, tuid: str, mid: str, h: float) -> None:
    d = proj / "C--p" / SESS / "subagents"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"agent-{tuid}.jsonl").write_text(asst(mid, h), encoding="utf-8")
    (d / f"agent-{tuid}.meta.json").write_text(
        json.dumps({"agentType": "Explore", "toolUseId": tuid, "spawnDepth": 1}), encoding="utf-8")


def outcomes(con) -> dict:
    return {r["tool_use_id"]: r["outcome"] for r in fl.spawn_rows(con, 0, T0 + 99 * 3600)}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "projects"
        main_fp = proj / "C--p" / f"{SESS}.jsonl"
        main_fp.parent.mkdir(parents=True)
        main_fp.write_text(
            human("P1", 1)
            + asst("m1", 1.1, spawns=("tuRET", "tuHOOK", "tuDENY", "tuERR", "tuRANERR",
                                      "tuREQ", "tuRUN", "tuLATE"))
            + result("tuRET", 1.3, "found it", False, as_list=True)
            + result("tuHOOK", 1.11, "PreToolUse:Agent hook error: AGENT-SOLO GUARD blocked "
                     "a parallel Agent dispatch on Windows.\n\nmore", True)
            + result("tuDENY", 1.12, "AGENT-SOLO GUARD blocked an IMPOSSIBLE AGENT CONTRACT.\n\nx",
                     True)
            + result("tuERR", 1.13, "Agent type 'nope' not found", True)
            + result("tuRANERR", 1.4, "agent crashed", True),
            encoding="utf-8")
        for tuid, mid in (("tuRET", "s1"), ("tuRANERR", "s2"), ("tuRUN", "s3"), ("tuLATE", "s4")):
            subagent(proj, tuid, mid, 1.2)

        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(spawns)")}
            ok("V-SPOUT-COLUMNS", {"result_ts", "is_error", "result_head"} <= cols,
               f"spawns columns: {sorted(cols)}")
            r = ux.refresh(con, proj, deadline_s=30)
            ok("V-SPOUT-REFRESH", r["status"] == "OK", json.dumps(r))
            got = outcomes(con)
            want = {"tuRET": "RETURNED", "tuHOOK": "HOOK_BLOCKED", "tuDENY": "HOOK_BLOCKED",
                    "tuERR": "FAILED_TO_START", "tuRANERR": "FAILED", "tuREQ": "REQUESTED",
                    "tuRUN": "RAN", "tuLATE": "RAN"}
            for tuid, w in want.items():
                ok(f"V-SPOUT-{w}-{tuid[2:]}", got.get(tuid) == w, f"{tuid}: {got.get(tuid)} (want {w})")
            head = con.execute("SELECT result_head FROM spawns WHERE tool_use_id='tuRET'").fetchone()[0]
            ok("V-SPOUT-LIST-BODY", head == "found it", f"list-shaped tool_result body read: {head!r}")
            p = con.execute("SELECT count(*) FROM prompts WHERE prompt_id='P1'").fetchone()[0]
            ok("V-SPOUT-PROMPT-KEPT", p == 1,
               "a tool_result line with a promptId still records the prompt")
            s = fl.summary(con, T0, T0 + 99 * 3600)
            ok("V-SPOUT-SUMMARY", s.get("spawn_outcomes", {}).get("HOOK_BLOCKED") == 2
               and sum(s.get("spawn_outcomes", {}).values()) == 8, f"{s.get('spawn_outcomes')}")
            kids = {c["tool_use_id"]: c for c in fl.prompt_tree(con, "P1")["spawns"]}
            ok("V-SPOUT-TREE", kids.get("tuHOOK", {}).get("outcome") == "HOOK_BLOCKED"
               and kids.get("tuRET", {}).get("outcome") == "RETURNED",
               "the prompt tree carries the outcome")

            # A result arriving in a LATER pass (appended bytes) is recorded.
            with main_fp.open("a", encoding="utf-8") as fh:
                fh.write(result("tuLATE", 2.0, "late answer", False))
            ux.refresh(con, proj, deadline_s=30)
            ok("V-SPOUT-APPENDED", outcomes(con).get("tuLATE") == "RETURNED",
               f"tuLATE after append: {outcomes(con).get('tuLATE')}")
            calls_before = ux.window(con, T0, T0 + 99 * 3600)["calls"]

            # Upgrade from a v2 index: result columns absent, version 2. The upgrade must
            # backfill spawns ONLY (audit G2): no file offset reset, totals unchanged.
            for c in ("result_ts", "is_error", "result_head"):
                con.execute(f"ALTER TABLE spawns DROP COLUMN {c}")
            con.execute("UPDATE meta SET v='2' WHERE k='schema_version'")
            con.commit()
            ok("V-SPOUT-V2-UNMEASURED", set(outcomes(con).values()) == {"UNMEASURED"},
               "a v2 index reports UNMEASURED, never a guessed outcome")
            offsets = dict(con.execute("SELECT path, offset FROM files"))
        finally:
            con.close()
        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            reset = [p for p, o in con.execute("SELECT path, offset FROM files") if o != offsets[p]]
            ok("V-SPOUT-CONNECT-NO-RESET", not reset,
               f"connect() on a v2 index reset {len(reset)} offsets (must be 0: no forced re-read)")
            r2 = ux.refresh(con, proj, deadline_s=30)
            final = {**want, "tuLATE": "RETURNED"}
            got2 = outcomes(con)
            ok("V-SPOUT-V3-BACKFILL", r2["status"] == "OK" and got2 == final,
               f"status={r2['status']} mismatched={ {k: v for k, v in got2.items() if v != final.get(k)} }")
            ok("V-SPOUT-V3-TOTALS", ux.window(con, T0, T0 + 99 * 3600)["calls"] == calls_before
               and r2["calls_upserted"] == 0 and r2["backfill_pending"] == 0,
               f"calls={ux.window(con, T0, T0 + 99 * 3600)['calls']} upserted={r2['calls_upserted']} "
               f"backfill_pending={r2['backfill_pending']}")
            ver = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()[0]
            ok("V-SPOUT-VERSION", ver == str(ux.SCHEMA_VERSION) == "3", f"schema_version={ver}")
        finally:
            con.close()

        # Old-index reader: a v2 table read without migration says UNMEASURED, never 0.
        legacy = sqlite3.connect(str(Path(td) / "legacy.sqlite"))
        try:
            legacy.executescript(
                "CREATE TABLE spawns(tool_use_id TEXT PRIMARY KEY, parent_k TEXT, session TEXT, "
                "ts REAL, subagent_type TEXT, model_req TEXT, prompt_id TEXT, file TEXT); "
                "CREATE TABLE subagents(file TEXT, session TEXT, agent_type TEXT, "
                "tool_use_id TEXT, depth INTEGER, model_meta TEXT);")
            legacy.execute("INSERT INTO spawns VALUES('t',NULL,NULL,?,NULL,NULL,NULL,'f')",
                           (T0 + 60,))
            rows = fl.spawn_rows(legacy, 0, T0 + 99 * 3600)
            ok("V-SPOUT-LEGACY-UNMEASURED", [r["outcome"] for r in rows] == ["UNMEASURED"],
               f"{[r['outcome'] for r in rows]}")
        finally:
            legacy.close()

    # The marker set is pinned to the guards that emit it (positive control: each
    # marker must be FOUND in some live hook source, else the gate cannot classify).
    hooks = [Path.home() / ".claude" / "hooks", HERE.parent / "hooks"]
    src = "".join(p.read_text(encoding="utf-8", errors="replace")
                  for d in hooks if d.is_dir() for p in d.glob("*.js"))
    missing = [m for m in fl.GUARD_MARKERS if m not in src]
    ok("V-SPOUT-MARKERS-LIVE", bool(fl.GUARD_MARKERS) and not missing,
       f"{len(fl.GUARD_MARKERS)} guard markers, missing from live hook source: {missing}")
    ok("V-SPOUT-HARNESS-PREFIX",
       fl.spawn_outcome(1.0, 1, "PreToolUse:Agent hook error: anything", False) == "HOOK_BLOCKED"
       and fl.spawn_outcome(1.0, 1, "Error: PreToolUse:Agent hook error: x", False) == "HOOK_BLOCKED",
       "harness prefix recognised with or without the 'Error: ' lead")

    total = PASS + FAIL
    print(f"SPAWN_OUTCOMES_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
