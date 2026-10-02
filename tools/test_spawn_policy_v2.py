#!/usr/bin/env python3
"""V-SPV2-* gates: decide_spawn v2 challenger + policy receipts (plan s12 c8, s13 c8/c8c).

Pure rules first (each driven from both poles), then receipts (reproduced from the
receipt alone, with a tamper control proving reproduction is sensitive), then the
equivalence key on a real index, then replay_v2 over a baseline + judged window,
then ledger independence: the replay must leave the index bytes untouched and the
replay source must hold no write SQL. Hermetic; no model call."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import estate_shadow as es  # noqa: E402
import usage_index as ux  # noqa: E402
from modules.cognitive_os import scheduler as S  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
BANDS = {"p90": {"active_sessions": 2, "active_subagents": 2, "calls_per_h": 100},
         "p99": {"active_sessions": 5, "active_subagents": 5, "calls_per_h": 500},
         "prompt_spawns_p90": 3, "root_calls_p90": 50}
CALM = {"active_sessions": 1, "active_subagents": 0, "calls_per_h": 10}
HOT = {"active_sessions": 9, "active_subagents": 9, "calls_per_h": 900}


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def v2(prio, load=CALM, ordinal=1, eq=0, spend=0):
    return S.decide_spawn_v2(prio, load, ordinal, BANDS, equivalent_active=eq,
                             root_calls_before=spend)


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def spawn_line(mid, h, tuid, prompt="look", sess="S1"):
    return json.dumps({"type": "assistant", "timestamp": iso(h), "sessionId": sess,
                       "requestId": "r" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "content": [
                           {"type": "tool_use", "id": tuid, "name": "Agent",
                            "input": {"subagent_type": "Explore", "prompt": prompt}}],
                           "usage": {"input_tokens": 1, "cache_read_input_tokens": 10,
                                     "cache_creation_input_tokens": 0, "output_tokens": 1}}}) + "\n"


def result_line(h, tuid):
    return json.dumps({"type": "user", "timestamp": iso(h), "sessionId": "S1",
                       "message": {"role": "user", "content": [
                           {"type": "tool_result", "tool_use_id": tuid, "content": "done"}]}}) + "\n"


def mission_prompt(pid, h):
    """A CONTINUATION root (priority NORMAL): judged by v2, never protected."""
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": "S1",
                       "origin": {"kind": "task-notification"}}) + "\n"


def main() -> int:
    # -- pure rules ------------------------------------------------------------
    ok("V-SPV2-PROTECTED-DUP", v2(S.PRIO_INTERACTIVE, eq=2).verdict == S.SPAWN_ALLOW,
       "an interactive spawn is allowed even with an equivalent running")
    ok("V-SPV2-UNKNOWN-NOT-LOAD", v2(S.PRIO_UNKNOWN, load=HOT, spend=999).verdict == S.SPAWN_ALLOW
       and S.decide_spawn(S.PRIO_BACKGROUND, HOT, 1, BANDS).verdict == S.SPAWN_WOULD_DEFER,
       "UNKNOWN root under hot load: v2 ALLOW where v1 (as BACKGROUND) defers")
    ok("V-SPV2-PRIORITY-UNKNOWN", S.spawn_priority_v2("UNKNOWN", "Explore") == S.PRIO_UNKNOWN
       and S.spawn_priority_v2("MISSION", "Explore") == S.PRIO_BACKGROUND
       and S.spawn_priority_v2("UNKNOWN", "gsd-verifier") == S.PRIO_VERIFY,
       "UNKNOWN splits from BACKGROUND; verifiers stay protected")
    ok("V-SPV2-REJECT-DUP", v2(S.PRIO_BACKGROUND, eq=1).verdict == S.SPAWN_WOULD_REJECT
       and v2(S.PRIO_NORMAL, eq=1).verdict == S.SPAWN_WOULD_REJECT,
       "a non-protected exact duplicate of a running spawn is WOULD_REJECT")
    ok("V-SPV2-NO-DUP-ALLOW", v2(S.PRIO_BACKGROUND, eq=0).verdict == S.SPAWN_ALLOW,
       "control: same spawn, nothing equivalent running, calm estate -> ALLOW")
    ok("V-SPV2-SPEND-DEFER", v2(S.PRIO_BACKGROUND, spend=51).verdict == S.SPAWN_WOULD_DEFER
       and v2(S.PRIO_BACKGROUND, spend=50).verdict == S.SPAWN_ALLOW,
       "BACKGROUND root above the spend envelope defers; at the envelope it does not")
    ok("V-SPV2-SPEND-NORMAL", v2(S.PRIO_NORMAL, spend=999).verdict == S.SPAWN_ALLOW,
       "root spend gates BACKGROUND only")
    unm = S.decide_spawn_v2(S.PRIO_BACKGROUND, CALM, 1, BANDS, equivalent_active=None,
                            root_calls_before=None)
    ok("V-SPV2-UNMEASURED", unm.verdict == S.SPAWN_ALLOW, "unmeasured inputs never trigger")

    # -- receipts --------------------------------------------------------------
    feats = {"load": HOT, "prompt_spawns": 1, "equivalent_active": 0, "root_calls_before": 3}
    v = S.decide_spawn_v2(S.PRIO_BACKGROUND, HOT, 1, BANDS, equivalent_active=0, root_calls_before=3)
    r = S.spawn_receipt({"tool_use_id": "tuX"}, feats, BANDS, v, "REPLAY")
    ok("V-SPV2-RECEIPT-FIELDS", all(r.get(k) for k in ("receipt_id", "policy", "bands_digest",
                                                        "verdict", "reasons", "floors_checked",
                                                        "evidence_class", "deopt", "features")),
       f"receipt keys: {sorted(r)}")
    ok("V-SPV2-RECEIPT-REPRODUCES", S.replay_receipt(r).verdict == r["verdict"] == S.SPAWN_WOULD_DEFER,
       "the verdict is re-derived from the receipt alone")
    tampered = json.loads(json.dumps(r))
    tampered["features"]["load"] = CALM
    ok("V-SPV2-RECEIPT-SENSITIVE", S.replay_receipt(tampered).verdict != r["verdict"],
       "control: changing a recorded input changes the re-derived verdict")
    ok("V-SPV2-DEOPT", "void" in r["deopt"] and "none" in S.spawn_receipt(
        {"tool_use_id": "y"}, feats, BANDS, S.SpawnVerdict(S.SPAWN_ALLOW, "NORMAL"), "REPLAY")["deopt"],
       "a non-ALLOW receipt states what voids it")
    ok("V-SPV2-HASH-EXACT", ux.spawn_input_hash({"subagent_type": "Explore", "prompt": "a"})
       == ux.spawn_input_hash({"subagent_type": "Explore", "prompt": "a", "model": "x"})
       != ux.spawn_input_hash({"subagent_type": "Explore", "prompt": "a "}),
       "equivalence = type + exact prompt; model ignored; one extra space is NOT equivalent")

    # -- discrimination: a challenger that only hits advancing work is REJECTED ----
    ok("V-SPV2-REC-NO-CHANGE", es.recommend(0, {})["verdict"] == "NO_CHANGE", "no changed verdict")
    ok("V-SPV2-REC-REJECT", es.recommend(5, {"ADVANCED": 4, "ADVANCED_LATER": 1})["verdict"]
       == "REJECT", "every changed verdict hit a root that advanced")
    ok("V-SPV2-REC-CHALLENGER", es.recommend(5, {"ADVANCED": 4, "UNSETTLED": 1})["verdict"]
       == "CHALLENGER", "one changed verdict hit unsettled work: still a candidate")
    ok("V-SPV2-REC-UNJUDGED", es.recommend(3, {"UNJUDGED": 3})["verdict"] == "CHALLENGER",
       "unjudged roots never upgrade to REJECT (absence is not evidence)")

    # -- equivalence + replay on a real index -------------------------------------
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "projects" / "C--p"
        proj.mkdir(parents=True)
        lines = [mission_prompt("PB", 0.5)]
        for i in range(4):                                  # baseline spawns, hours 1..4
            lines += [spawn_line(f"b{i}", 1 + i, f"tuB{i}", prompt=f"base {i}"),
                      result_line(1.01 + i, f"tuB{i}")]
        lines += [mission_prompt("PJ", 10.5),
                  spawn_line("j1", 11.0, "tuJ1", prompt="same"),        # running, no result yet
                  spawn_line("j2", 11.2, "tuJ2", prompt="same"),        # duplicate of a running one
                  result_line(11.5, "tuJ1"),
                  spawn_line("j3", 12.0, "tuJ3", prompt="same")]        # j1 returned; j2 has no result
        (proj / "S1.jsonl").write_text("".join(lines), encoding="utf-8")
        db = Path(td) / "ix.sqlite"
        con = ux.connect(db)
        ux.refresh(con, proj.parent, deadline_s=30)
        eq = es.Equivalents(con)
        h = con.execute("SELECT input_hash FROM spawns WHERE tool_use_id='tuJ2'").fetchone()[0]
        ok("V-SPV2-EQ-RUNNING", eq.active(h, T0 + 11.2 * 3600, "tuJ2") == 1,
           "j2 sees j1 running (no result at 11.2 h)")
        ok("V-SPV2-EQ-RETURNED", eq.active(h, T0 + 12.0 * 3600, "tuJ3") == 1,
           "j3 at 12 h: j1 returned (not counted), j2 never returned and is within the bound")
        ok("V-SPV2-EQ-FUTURE-BLIND", eq.active(h, T0 + 11.0 * 3600, "tuJ1") == 0,
           "j1 does not see j2/j3, which start later (no future data)")
        con.close()

        before = hashlib.sha256(db.read_bytes()).hexdigest()
        con = ux.connect(db)
        res = es.replay_v2(con, T0, T0 + 10 * 3600, T0 + 10 * 3600, T0 + 20 * 3600)
        con.close()
        after = hashlib.sha256(db.read_bytes()).hexdigest()
        ok("V-SPV2-REPLAY-RUNS", res["judged"]["spawns"] == 3 and res["receipts"]["total"] == 3,
           f"judged={res['judged']} receipts={res['receipts']}")
        ok("V-SPV2-REPLAY-REPRODUCED", res["receipts"]["reproduced_from_receipt_alone"] == 3,
           f"{res['receipts']}")
        rej = [r for r in res["_receipts"] if r["verdict"] == S.SPAWN_WOULD_REJECT]
        ok("V-SPV2-REPLAY-REJECTS-DUP", {r["subject"]["tool_use_id"] for r in rej} == {"tuJ2", "tuJ3"},
           f"WOULD_REJECT: {[r['subject']['tool_use_id'] for r in rej]}")
        ok("V-SPV2-RECOMMENDATION", res["recommendation"]["verdict"] == "CHALLENGER"
           and res["meta_overhead"]["model_calls"] == 0,
           f"{res['recommendation']} overhead={res['meta_overhead']}")
        ok("V-SPV2-LEDGER-UNTOUCHED", before == after,
           "c8c: a replay leaves the index bytes identical (the optimizer never writes its ledger)")

    src = (HERE / "estate_shadow.py").read_text(encoding="utf-8")
    # CREATE + executescript: the c9 drill wrote a table through CREATE and this gate saw nothing
    writes = re.findall(r"(?i)\b(INSERT|UPDATE|DELETE|REPLACE INTO|ALTER|DROP|CREATE)\b\s"
                        r"|\bexecutescript\b", src)
    ok("V-SPV2-NO-WRITE-SQL", not writes, f"write verbs in estate_shadow.py: {writes}")

    total = PASS + FAIL
    print(f"SPAWN_POLICY_V2_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
