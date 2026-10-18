#!/usr/bin/env python
"""V-DP-* gates for tools/decision_plane.py (spec vault/plans/decision-plane-master-plan-2026-10-17.md).

Hermetic: the state dir is a temp dir. Every refusal has a paired control that must come out the other way,
so a gate that refuses everything (or admits everything) cannot go green.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="decision-plane-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_CONTINUATION", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_plane as dp  # noqa: E402
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None   # hermetic: never run git in TMP
NOW = 1_800_000_000.0

passes = fails = 0
M = "m-dptest000001"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def refused(fn, exc=dp.DecisionError):
    try:
        fn()
    except exc as e:
        return str(e)
    return None


def spec(did="B", **over):
    s = {
        "id": did, "class": "PRODUCT", "question": "TB-FULL forecast exceeds the hard ceiling: which authority?",
        "dimensions": [{"name": "capital", "kind": "capital"},
                       {"name": "scope", "kind": "enum", "allowed": ["UNCHANGED", "REDUCED", "REORDERED"]},
                       {"name": "efficiency", "kind": "enum", "allowed": ["CONTINUE_OPTIMIZATION", "OFF"]}],
        "options": [
            {"token": "R-200", "params": {"capital": {"ceiling": 200_000_000, "unit": "processed_tokens"},
                                          "scope": "UNCHANGED", "efficiency": "CONTINUE_OPTIMIZATION"}},
            {"token": "R-REFC", "params": {"capital": {"ceiling": 120_000_000, "unit": "processed_tokens"},
                                           "scope": "UNCHANGED", "efficiency": "CONTINUE_OPTIMIZATION"}}],
        "recommendation": {"token": "R-200", "note": "evidence, not authority"},
        "evidence": {"central_scenario": 196_000_000, "ceiling": 120_000_000, "settled": 11_170_000},
        "consumers": ["m-7e268fc1a6d9"], "wake_policy": "WAKE_EXISTING_EXECUTOR",
    }
    s.update(over)
    return s


def main() -> int:
    # --- Closure Gate: complete option set is shown, an option missing a parameter blocks the whole decision
    d = dp.create(M, spec())
    check("V-DP-COMPLETE-IS-READY", d["status"] == dp.READY and d["problems"] == [], d["problems"])
    s = spec("B2")
    del s["options"][0]["params"]["capital"]["ceiling"]
    d2 = dp.create(M, s)
    check("V-DP-OPTION-WITHOUT-CEILING-IS-INCOMPLETE", d2["status"] == dp.OPEN
          and any("ceiling" in p for p in d2["problems"]), d2["problems"])
    check("V-DP-INCOMPLETE-CANNOT-BE-SHOWN", refused(lambda: dp.surface(M, "B2")) is not None)
    s = spec("B3")
    s["options"][0]["params"]["capital"] = {"ceiling": 200_000_000}
    check("V-DP-AMOUNT-WITHOUT-UNIT-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    s = spec("B4")
    del s["options"][1]["params"]["efficiency"]
    check("V-DP-MISSING-DIMENSION-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    s = spec("B5")
    s["options"][0]["params"]["scope"] = "WHATEVER"
    check("V-DP-VALUE-OUTSIDE-ENUM-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    check("V-DP-RECOMMENDATION-MUST-BE-AN-OPTION",
          dp.create(M, spec("B6", recommendation={"token": "NOPE"}))["status"] == dp.OPEN)
    check("V-DP-NO-CONSUMER-IS-INCOMPLETE", dp.create(M, spec("B7", consumers=[]))["status"] == dp.OPEN)
    check("V-DP-DUPLICATE-ID-REFUSED", refused(lambda: dp.create(M, spec())) is not None)

    # --- Dangling decision: an unknown id is a hard failure, never recovered from prose
    check("V-DP-DANGLING-ID-IS-HARD-FAILURE", refused(lambda: dp.get(M, "ghost"), dp.DanglingDecision) is not None)
    check("V-DP-DANGLING-ON-OTHER-MISSION", refused(lambda: dp.get("m-other00001", "B"), dp.DanglingDecision)
          is not None)

    # --- Surface carries options and a recommendation that is NOT a selection
    sh = dp.surface(M, "B")
    check("V-DP-SURFACE-SHOWS-TOKENS", sh["valid_tokens"] == ["R-200", "R-REFC"] and sh["recommendation"]["token"]
          == "R-200", sh["valid_tokens"])
    check("V-DP-RECOMMENDATION-IS-NOT-RESOLUTION", dp.get(M, "B")["status"] == dp.READY
          and dp.unresolved(M).count("B") == 1)

    # --- Providerless selection: unambiguous maps, ambiguous/empty refuse and list valid tokens
    dec = dp.get(M, "B")
    check("V-DP-SHORT-TOKEN-MAPS", dp.parse_choice(dec, "aprobar DP-1 + B=R-200")[0] == "R-200")
    check("V-DP-CASE-INSENSITIVE", dp.parse_choice(dec, "r-refc")[0] == "R-REFC")
    check("V-DP-BOTH-TOKENS-AMBIGUOUS", dp.parse_choice(dec, "R-200 or R-REFC")[0] is None)
    check("V-DP-NO-TOKEN-AMBIGUOUS", dp.parse_choice(dec, "a")[0] is None)
    msg = refused(lambda: dp.resolve(M, "B", "tal vez"))
    check("V-DP-AMBIGUOUS-LISTS-VALID-TOKENS", msg is not None and "R-200" in msg and "R-REFC" in msg, msg)
    check("V-DP-AMBIGUOUS-DID-NOT-RESOLVE", dp.get(M, "B")["status"] == dp.READY)

    # --- Receipt: typed, hashed, durable, idempotent
    out = dp.resolve(M, "B", "aprobar DP-1 + B=R-200", evidence_now=spec()["evidence"], now=1_800_000_000.0)
    r = out["receipt"]
    check("V-DP-RECEIPT-TYPED", out["recorded"] and r["token"] == "R-200"
          and r["params"]["capital"] == {"ceiling": 200_000_000, "unit": "processed_tokens"}
          and r["params"]["efficiency"] == "CONTINUE_OPTIMIZATION" and len(r["sha"]) == 16, r)
    again = dp.resolve(M, "B", "R-200")
    check("V-DP-REPLAY-IS-NOOP", not again["recorded"] and again["receipt"]["sha"] == r["sha"])
    rows = [json.loads(x) for x in dp.store_path(M).read_text(encoding="utf-8").splitlines()]
    check("V-DP-REPLAY-WROTE-NOTHING", sum(1 for x in rows if x["ev"] == "resolved") == 1)
    check("V-DP-OTHER-CHOICE-AFTER-RESOLVE-REFUSED", refused(lambda: dp.resolve(M, "B", "R-REFC")) is not None)
    check("V-DP-DURABLE-ACROSS-RELOAD", dp.get(M, "B")["receipt"]["sha"] == r["sha"]
          and "B" not in dp.unresolved(M))
    check("V-DP-EFFICIENCY-SURVIVES-CAPITAL", r["params"]["efficiency"] == "CONTINUE_OPTIMIZATION")

    # --- Staleness: evidence changed between packet and answer -> invalidated, nothing applied
    dp.create(M, spec("S1"))
    stale = copy.deepcopy(spec()["evidence"])
    stale["central_scenario"] = 250_000_000
    check("V-DP-STALE-EVIDENCE-REFUSED", refused(lambda: dp.resolve(M, "S1", "R-200", evidence_now=stale)) is not None)
    check("V-DP-STALE-IS-INVALIDATED", dp.get(M, "S1")["status"] == dp.INVALIDATED
          and "receipt" not in dp.get(M, "S1"))
    dp.create(M, spec("S2"))
    ok = dp.resolve(M, "S2", "R-200", evidence_now=spec()["evidence"])
    check("V-DP-FRESH-EVIDENCE-ADMITTED", ok["recorded"])

    # --- Supersession and unreadable store
    dp.create(M, spec("S3"))
    dp.create(M, spec("S4"))
    dp.supersede(M, "S3", "S4")
    check("V-DP-SUPERSEDED", dp.get(M, "S3")["status"] == dp.SUPERSEDED and "S3" not in dp.unresolved(M)
          and "S4" in dp.unresolved(M))
    bad = "m-dptest000002"
    dp.create(bad, spec())
    with open(dp.store_path(bad), "a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    check("V-DP-CORRUPT-STORE-IS-NOT-EMPTY", refused(lambda: dp.get(bad, "B")) is not None)

    # --- The CLI reaches the same code: create from file, show, resolve, replay
    cli_m = "m-dptest000003"
    f = Path(TMP) / "b.json"
    f.write_text(json.dumps(spec()), encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, str(Path(dp.__file__)), *a], capture_output=True,  # noqa: E731
                                    text=True, timeout=60)
    c1 = run("create", "--mission", cli_m, "--file", str(f))
    c2 = run("show", "--mission", cli_m, "--decision", "B")
    c3 = run("resolve", "--mission", cli_m, "--decision", "B", "--choice", "R-200")
    c4 = run("resolve", "--mission", cli_m, "--decision", "B", "--choice", "R-200")
    c5 = run("show", "--mission", cli_m, "--decision", "ghost")
    check("V-DP-CLI-ROUNDTRIP", c1.returncode == 0 and c2.returncode == 0 and "R-200" in c2.stdout
          and c3.returncode == 0 and "recorded=True" in c3.stdout and "recorded=False" in c4.stdout,
          (c1.stdout, c3.stdout, c4.stdout))
    check("V-DP-CLI-DANGLING-EXITS-NONZERO", c5.returncode == 2 and "no durable contract" in c5.stderr, c5.stderr)

    # --- A capital decision is resolved only by an Owner-typed transcript entry after the anchor was displayed
    cm = "m-dptest000004"
    cap = dp.create(cm, spec("C1", **{"class": "CAPITAL"}))
    check("V-DP-CAPITAL-REFUSES-PLAIN-TEXT", cap["status"] == dp.READY
          and refused(lambda: dp.resolve(cm, "C1", "R-200")) is not None and dp.get(cm, "C1")["status"] == dp.READY)
    check("V-DP-CAPITAL-REFUSES-AUTHORITY-WITHOUT-UUID",
          refused(lambda: dp.resolve(cm, "C1", "R-200", authority={"note": "trust me"})) is not None)
    anc = dp.anchor(dp.get(cm, "C1"))

    def tr(rows):
        p = Path(TMP) / f"t{len(os.listdir(TMP))}.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return p

    asst = {"type": "assistant", "uuid": "a1", "message": {"content": [{"type": "text", "text": f"options {anc}"}]}}
    typed = {"type": "user", "uuid": "u1", "timestamp": "2026-10-17T22:00:00Z", "origin": {"kind": "human"},
             "promptSource": "typed", "message": {"content": "R-200"}}
    forged = [{**typed, "uuid": "u2", "origin": {"kind": "agent"}}, {**typed, "uuid": "u3", "promptSource": None},
              {**typed, "uuid": "u4", "message": {"content": [{"type": "text", "text": "R-200"}]}},
              {"type": "assistant", "uuid": "a2", "message": {"content": [{"type": "text", "text": "R-200"}]}}]
    check("V-DP-NOT-OWNER-TYPED-IS-IGNORED", refused(lambda: dp.resolve_from_transcript(cm, "C1",
          tr([asst, *forged]))) is not None and dp.get(cm, "C1")["status"] == dp.READY)
    check("V-DP-ANSWER-BEFORE-ANCHOR-IS-IGNORED", refused(lambda: dp.resolve_from_transcript(cm, "C1",
          tr([typed, asst]))) is not None)
    check("V-DP-ANCHOR-NEVER-DISPLAYED-IS-IGNORED", refused(lambda: dp.resolve_from_transcript(cm, "C1",
          tr([{**asst, "message": {"content": [{"type": "text", "text": "no anchor"}]}}, typed]))) is not None)
    ok = dp.resolve_from_transcript(cm, "C1", tr([asst, *forged, typed]))
    check("V-DP-OWNER-TYPED-RESOLVES-CAPITAL", ok["recorded"] and ok["receipt"]["authority"]["uuid"] == "u1"
          and ok["receipt"]["token"] == "R-200", ok["receipt"].get("authority"))
    check("V-DP-CAPITAL-REPLAY-IS-NOOP", not dp.resolve_from_transcript(cm, "C1", tr([asst, typed]))["recorded"])

    # --- delivery: the consumer verifies, applies, wakes; it fails closed and is idempotent
    cid = "m-dptest000005"
    gm.create(TMP, "/gsd-autonomous", mission_id=cid, now=NOW)
    sid = "dec5dec5-0000-0000-0000-000000000000"
    gm.transition(cid, expect_epoch=0, expect_state=gm.PREPARED, event="t", state=gm.RUNNING, epoch=1,
                  owner={"session_id": sid, "kind": "background", "epoch": 1}, now=NOW)
    base = spec("B", **{"class": "CAPITAL", "consumers": [cid]})
    base["evidence"]["old_trip"] = 120_000_000
    for o in base["options"]:
        o["label"] = o["token"] + " label"
    base["options"][0]["params"]["capital"]["ceiling"] = 120_000_000          # R-REFC-like: ceiling unchanged
    base["options"][1]["params"]["capital"]["ceiling"] = 250_000_000          # a raise
    src = "m-dptest000006"
    dp.create(src, {**base, "id": "B"})
    sd = dp.get(src, "B")
    u = {"type": "user", "uuid": "uo", "timestamp": "t", "origin": {"kind": "human"}, "promptSource": "typed"}
    tp = Path(TMP) / "own.jsonl"
    tp.write_text("\n".join(json.dumps(x) for x in [
        {"type": "assistant", "uuid": "ao", "message": {"content": [{"type": "text", "text": dp.anchor(sd)}]}},
        {**u, "message": {"content": "R-200"}}]) + "\n", encoding="utf-8")
    dp.resolve_from_transcript(src, "B", tp)
    bundle = dp.export_bundle(src, "B")
    # rebind to the consumer mission (the test shares one state dir; production is two hosts)
    for r in bundle["rows"]:
        if r["ev"] == "created":
            r["object"]["mission"] = cid
        else:
            r["receipt"]["mission"] = cid
            body = {k: r["receipt"].get(k) for k in ("decision", "mission", "token", "params", "evidence_fp",
                                                      "consumers", "authority")}
            r["receipt"]["sha"] = dp._receipt_sha(body)
    calls = {"run": [], "stop": []}

    def drun(argv, cwd):
        calls["run"].append(argv)
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": f"backgrounded · {sid[:8]} · {cid}-e1"})()

    live = [{"sessionId": sid, "id": sid[:8], "status": "idle", "kind": "background", "pid": 4242, "name": "x"}]
    kw = dict(sessions=live, runner=drun, stop_runner=lambda a: calls["stop"].append(a), pid_alive=lambda p: False,
              host_fetch=lambda: [], now=NOW)
    check("V-DP-BUNDLE-VERIFIES", dp.verify_bundle(bundle)[1]["token"] == "R-200")
    bad = json.loads(json.dumps(bundle))
    bad["rows"][1]["receipt"]["params"]["capital"]["ceiling"] = 999_000_000
    check("V-DP-TAMPERED-PARAMS-REFUSED", refused(lambda: dp.verify_bundle(bad)) is not None)
    bad = json.loads(json.dumps(bundle))
    bad["rows"][1]["receipt"]["sha"] = "0" * 16
    check("V-DP-TAMPERED-SHA-REFUSED", refused(lambda: dp.verify_bundle(bad)) is not None)
    bad = json.loads(json.dumps(bundle))
    bad["rows"][1]["receipt"]["authority"] = None
    check("V-DP-CAPITAL-BUNDLE-WITHOUT-AUTHORITY-REFUSED", refused(lambda: dp.verify_bundle(bad)) is not None)
    out = dp.consume_bundle(bundle, **kw)
    check("V-DP-CONSUME-RECORDS-AND-WAKES", out["recorded"] and out["woke"][cid].get("ok") and calls["stop"]
          and calls["stop"][0][-1] == sid[:8] and calls["run"][0][1:4] == ["--bg", "--resume", sid]
          and "OWNER DECISION B" in calls["run"][0][-1] and out["receipt"]["sha"] in calls["run"][0][-1],
          (out["woke"], calls["run"][:1]))
    check("V-DP-CONSUME-VIEW-NAMES-THE-UNCHANGED-CEILING", "120,000,000" in calls["run"][0][-1]
          and "efficiency policy CONTINUE_OPTIMIZATION" in calls["run"][0][-1])
    check("V-DP-DECISION-REACHES-LAUNCH-CARD", any("OWNER DECISION B" in d for d in gm.load(cid)["directives"]))
    again = dp.consume_bundle(bundle, **kw)
    check("V-DP-CONSUME-REPLAY-IS-NOOP", not again["recorded"] and len(calls["run"]) == 1)
    raised = json.loads(json.dumps(bundle))
    rc2 = "m-dptest000007"
    dp.create(rc2, {**base, "id": "R", "consumers": [cid]})
    tp2 = Path(TMP) / "own2.jsonl"
    tp2.write_text("\n".join(json.dumps(x) for x in [
        {"type": "assistant", "uuid": "ao", "message": {"content": [{"type": "text",
                                                                    "text": dp.anchor(dp.get(rc2, "R"))}]}},
        {**u, "message": {"content": "R-REFC"}}]) + "\n", encoding="utf-8")
    dp.resolve_from_transcript(rc2, "R", tp2)
    rb = dp.export_bundle(rc2, "R")
    check("V-DP-CEILING-CHANGE-FAILS-CLOSED", refused(lambda: dp.consume_bundle(rb, **kw)) is not None
          and len(calls["run"]) == 1)
    check("V-DP-FAILED-CLOSED-WROTE-NOTHING", dp.get(rc2, "R")["status"] == dp.RESOLVED and len(calls["run"]) == 1)

    # --- D6: a raised CUMULATIVE ceiling becomes the consumer's own breaker envelope
    pred1, pred2 = "m-dppred00001", "m-dppred00002"

    def raised_bundle(src_id: str, consumer: str, ceiling: int, meters: dict | None):
        d = json.loads(json.dumps(base))
        d.update({"id": "D", "consumers": [consumer]})
        d["options"][0]["params"]["capital"]["ceiling"] = ceiling      # the option the text "R-200" selects
        if meters is not None:
            d["evidence"]["meters"] = meters
        dp.create(src_id, d)
        tpx = Path(TMP) / f"{src_id}.jsonl"
        tpx.write_text("\n".join(json.dumps(x) for x in [
            {"type": "assistant", "uuid": "ao", "message": {"content": [{"type": "text",
                                                                        "text": dp.anchor(dp.get(src_id, "D"))}]}},
            {**u, "message": {"content": "R-200"}}]) + "\n", encoding="utf-8")
        dp.resolve_from_transcript(src_id, "D", tpx)
        b = dp.export_bundle(src_id, "D")
        for r in b["rows"]:
            if r["ev"] == "created":
                r["object"]["mission"] = consumer + "-view"
            else:
                r["receipt"]["mission"] = consumer + "-view"
                body = {k: r["receipt"].get(k) for k in ("decision", "mission", "token", "params", "evidence_fp",
                                                          "consumers", "authority")}
                r["receipt"]["sha"] = dp._receipt_sha(body)
        return b

    c3 = "m-dptest000008"
    gm.create(TMP, "/gsd-autonomous", mission_id=c3, now=NOW)
    meters = {pred1: 46_780_899, pred2: 2_959_145, c3: 21_000_000}
    got = dp.consume_bundle(raised_bundle("m-dptest000009", c3, 210_000_000, meters), wake=False)
    want = (210_000_000 - 46_780_899 - 2_959_145) // 2
    check("V-DP-D6-CEILING-BECOMES-ENVELOPE", got["applied"] and got["applied"]["token_estimate"] == want
          and gm.load(c3)["token_estimate"] == want, got.get("applied"))
    check("V-DP-D6-EXCLUDES-THE-CONSUMER-OWN-METER", got["applied"]["predecessors"] == 46_780_899 + 2_959_145)
    c4 = "m-dptest000010"
    gm.create(TMP, "/gsd-autonomous", mission_id=c4, now=NOW)
    check("V-DP-D6-WITHOUT-METERS-REFUSED", refused(lambda: dp.consume_bundle(
        raised_bundle("m-dptest000011", c4, 210_000_000, None), wake=False)) is not None
          and gm.load(c4).get("token_estimate") is None)
    c5 = "m-dptest000012"
    gm.create(TMP, "/gsd-autonomous", mission_id=c5, now=NOW)
    check("V-DP-D6-CEILING-BELOW-PREDECESSORS-REFUSED", refused(lambda: dp.consume_bundle(
        raised_bundle("m-dptest000013", c5, 49_000_000, meters), wake=False)) is not None
          and gm.load(c5).get("token_estimate") is None)

    # fresh meter: a predecessor's cost_mark lags its transcripts (2026-10-18: mark 46.8M, measured 51.3M), so the
    # budget must come from the larger of snapshot, mark and a fresh read
    import mission_spend as ms
    p6, c6 = "m-dppred00003", "m-dptest000014"
    gm.create(TMP, "/gsd-autonomous", mission_id=p6, now=NOW)
    gm.create(TMP, "/gsd-autonomous", mission_id=c6, now=NOW)
    real = ms.processed_tokens
    ms.processed_tokens = lambda rec, *a, **k: 51_303_727 if rec.get("mission_id") == p6 else None
    try:
        got6 = dp.consume_bundle(raised_bundle("m-dptest000015", c6, 210_000_000, {p6: 46_780_899}), wake=False)
    finally:
        ms.processed_tokens = real
    check("V-DP-D6-FRESH-METER-BEATS-STALE-SNAPSHOT", got6["applied"]["predecessors"] == 51_303_727
          and gm.load(c6)["token_estimate"] == (210_000_000 - 51_303_727) // 2, got6.get("applied"))

    print(f"DP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
