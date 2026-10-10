#!/usr/bin/env python
"""V-RR-* gates for tools/rollover_replay.py (plan ccp-s16). Hermetic: a fixture rollover ledger
and fixture transcripts, resolved through an injected lookup. No model call, no real ledger.

Each gate pins a fault met while measuring the real ledger on 2026-10-03: the certified-resume row
names the PREDECESSOR (a reader that trusts it measures the wrong session), torn concurrent
appends, commits written late in long PowerShell lines, and too few samples read as a number."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover_replay as rr  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def call(mid, ctx, tools=(), ts="2026-10-01T12:00:00Z"):
    """One assistant line: `ctx` resident tokens, optional tool uses (name, input)."""
    content = [{"type": "tool_use", "name": n, "input": i} for n, i in tools]
    return json.dumps({"type": "assistant", "timestamp": ts, "requestId": f"r-{mid}",
                       "message": {"id": f"m-{mid}", "model": "claude-opus-5-5", "content": content,
                                   "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
                                             "cache_read_input_tokens": ctx - 10, "output_tokens": 5}}})


def transcript(d: Path, name: str, lines: list[str]) -> Path:
    p = d / f"{name}.jsonl"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="rr-"))
    commit = ("PowerShell", {"command": "$g='C:\\Program Files\\Git\\cmd\\git.exe'; & $g -C $r commit -q -F m.txt -- a.py"})
    paths = {
        # predecessor P1 (floor 300k) -> successor S1 (floor 120k, first mutation at call 3)
        "P1": transcript(d, "P1", [call("p1a", 300_000), call("p1b", 310_000)]),
        "S1": transcript(d, "S1", [call("s1a", 120_000, [("Read", {"file_path": "x"})]),
                                   call("s1a", 120_000),                       # duplicate line, same call
                                   call("s1b", 125_000, [("Grep", {"pattern": "y"})]),
                                   call("s1c", 130_000, [("Edit", {"file_path": "x"})])]),
        "S2": transcript(d, "S2", [call("s2a", 140_000), call("s2b", 150_000, [commit])]),
        "S3": transcript(d, "S3", [call("s3a", 110_000, [("Read", {"file_path": "x"})])]),   # never mutates
        "S4": transcript(d, "S4", [call("s4a", 900_000, [("Edit", {"file_path": "x"})])]),   # FAILED resume
    }
    led = d / "rollover-ledger.jsonl"
    rows = [
        {"event": "successor_claimed", "session_id": "P1", "claimant": "S1"},
        {"event": "resume_certified", "session_id": "P1", "wrong": []},
        {"event": "successor_claimed", "session_id": "P2", "claimant": "S2"},
        {"event": "resume_certified", "session_id": "P2", "wrong": []},
        {"event": "successor_claimed", "session_id": "P3", "claimant": "S3"},
        {"event": "resume_certified", "session_id": "P3", "wrong": []},
        {"event": "successor_claimed", "session_id": "P4", "claimant": "S4"},
        {"event": "resume_failed", "session_id": "P4", "wrong": [{"key": "head"}]},
        {"event": "resume_certified", "session_id": "P9", "wrong": []},       # certified, no claim row
    ]
    led.write_text("\n".join(json.dumps(r) for r in rows[:3]) + "\n" + 'hars": 805}\n' +
                   "\n".join(json.dumps(r) for r in rows[3:]) + "\n", encoding="utf-8")

    parsed, torn = rr.read_ledger(led)
    ok("V-RR-TORN-COUNTED", torn == 1 and len(parsed) == len(rows), f"torn={torn} rows={len(parsed)}")

    res = rr.fresh_cost(led, find=paths.get, min_samples=1)
    by = {s["successor"]: s for s in res["samples"]}
    ok("V-RR-SUCCESSOR-NOT-PREDECESSOR", by.get("S1", {}).get("first_ctx") == 120_000,
       f"S1 first_ctx={by.get('S1', {}).get('first_ctx')} (predecessor floor is 300000)")
    ok("V-RR-ONE-CALL-ONCE", by.get("S1", {}).get("calls_to_first_mutation") == 3,
       f"S1 calls_to_first_mutation={by.get('S1', {}).get('calls_to_first_mutation')}")
    ok("V-RR-COMMIT-IS-MUTATION", by.get("S2", {}).get("calls_to_first_mutation") == 2,
       f"S2={by.get('S2', {}).get('calls_to_first_mutation')}")
    ok("V-RR-NO-MUTATION-IS-NOT-ZERO", by.get("S3", {}).get("calls_to_first_mutation") is None
       and res["no_mutation"] == 1, f"S3={by.get('S3')} no_mutation={res['no_mutation']}")
    ok("V-RR-FAILED-RESUME-EXCLUDED", "S4" not in by, str(sorted(by)))
    ok("V-RR-CERTIFIED-WITHOUT-CLAIM-REPORTED", res["missing_claim"] == ["P9"], str(res["missing_claim"]))
    ok("V-RR-DISTRIBUTION", res["first_ctx"]["n"] == 3 and res["first_ctx"]["p50"] == 120_000,
       str(res["first_ctx"]))

    few = rr.fresh_cost(led, find=paths.get, min_samples=5)
    ok("V-RR-FEW-SAMPLES-INSUFFICIENT", few["verdict"] == "INSUFFICIENT_EVIDENCE"
       and few["first_ctx"].get("p50") is None, f"{few['verdict']} {few['first_ctx']}")
    ok("V-RR-ENOUGH-SAMPLES-MEASURED", res["verdict"] == "MEASURED", res["verdict"])   # positive control

    for cmd, want in (("git commit -m x", True), ("& $g -C $r commit -F m -- a", True),
                      ("git status --short", False), ("echo commitment; git log", False),
                      ("git -C r log --format=%s commit", False)):
        got = rr.is_commit_command(cmd)
        ok(f"V-RR-COMMIT-DETECT[{cmd[:24]}]", got is want, f"got {got}")

    ok("V-RR-DRY-RUN-NOT-COMMIT", not rr.is_commit_command("git commit --dry-run -m x"))

    # ---- C2 boundaries: a successful commit only, and only what was known at that call.
    def use(mid, tid, ctx, cmd):
        return json.dumps({"type": "assistant", "requestId": f"r-{mid}", "timestamp": "2026-10-01T12:00:00Z",
                           "message": {"id": f"m-{mid}", "model": "claude-opus-5-5",
                                       "content": [{"type": "tool_use", "id": tid, "name": "PowerShell",
                                                    "input": {"command": cmd}}],
                                       "usage": {"input_tokens": 10, "cache_read_input_tokens": ctx - 10}}})

    def result(tid, err=False):
        return json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "is_error": err, "content": "x"}]}})

    b_lines = [call("b1", 100_000), use("b2", "t-ok", 200_000, "git commit -m a"), result("t-ok"),
               use("b3", "t-hook", 300_000, "git commit -m b"), result("t-hook", err=True),
               use("b4", "t-open", 350_000, "git commit -m c"),                 # no result: unknown
               call("b5", 900_000)]
    bt = rr.session_trace(transcript(d, "B", b_lines))
    ok("V-RR-ONLY-SUCCESSFUL-COMMITS", bt["commit_calls"] == [2], str(bt["commit_calls"]))
    bnd = rr.boundaries(bt)
    trunc = rr.boundaries(rr.session_trace(transcript(d, "B2", b_lines[:3])))
    ok("V-RR-BOUNDARY-NO-FUTURE", bnd == trunc and bnd[0]["resident"] == 200_000,
       f"full={bnd} truncated={trunc}")

    # ---- prior: ended-before-T only, own capsule chain and rolled sessions out (censored, counted).
    T = 1_790_000_000.0
    for name, n in (("E1", 50), ("E2", 50), ("LATE", 50), ("ROLLED", 50), ("CHAIN", 50)):
        transcript(d, name, [use(f"{name}{k}", f"{name}t{k}", 100_000, "git commit -m x") if k == 10
                             else call(f"{name}{k}", 100_000) for k in range(n)] +
                   [result(f"{name}t10")])
    sessions = [("E1", d / "E1.jsonl", T - 100), ("E2", d / "E2.jsonl", T - 200),
                ("LATE", d / "LATE.jsonl", T + 100), ("ROLLED", d / "ROLLED.jsonl", T - 100),
                ("CHAIN", d / "CHAIN.jsonl", T - 100)]
    chain = rr.capsule_chain([{"event": "successor_claimed", "session_id": "ROOT", "claimant": "CHAIN"}], "ROOT")
    pri = rr.Prior(sessions, chain, rolled={"ROLLED"}).at(T)
    ok("V-RR-PRIOR-ENDED-BEFORE-T", pri["values"] == [39, 39] and pri["sessions"] == 2,
       f"values={pri['values']} sessions={pri['sessions']}")
    ok("V-RR-PRIOR-CENSORED-COUNTED", pri["censored_excluded"] == 1, str(pri))

    # ---- judge: every verdict is rollover.decide; both poles reachable (audit G11).
    price = rr.price_at("claude-opus-5-5", T)
    ok("V-RR-PRICED", price.get("state") == "OK", str(price))
    big = {"call": 50, "ts": T, "model": "claude-opus-5-5", "floor": 130_000, "resident": 600_000}
    many = {"values": [200] * 10, "sessions": 5, "censored_excluded": 0}
    few_left = {"values": [1] * 10, "sessions": 5, "censored_excluded": 0}
    j = rr.judge(big, 4000, many, [0.0])
    ok("V-RR-POSITIVE-CONTROL-WOULD", j["prior"]["verdict"] == "WOULD_ROLLOVER", str(j["prior"]))
    j = rr.judge(big, 4000, few_left, [0.0])
    ok("V-RR-SHORT-HORIZON-CONTINUE", j["prior"]["verdict"] == "CONTINUE", str(j["prior"]))
    small = {**big, "resident": 200_000}
    j = rr.judge(small, 4000, many, [0.0])
    ok("V-RR-GROWTH-GATE-IS-DECIDES", j["prior"]["verdict"] == "CONTINUE" and "growth" in j["reason"], j["reason"])
    j = rr.judge(big, 4000, {"values": [200] * 3, "sessions": 1, "censored_excluded": 0}, [0.0])
    ok("V-RR-FEW-PRIOR-INSUFFICIENT", j["prior"]["verdict"] == "INSUFFICIENT_EVIDENCE", str(j["prior"]))
    # rehydration flips a borderline horizon: C=0 says WOULD, a large C says no -> not a clean verdict
    edge = {"values": [int(rr.judge(big, 4000, many, [0.0])["breakeven_calls"]) + 2] * 10,
            "sessions": 5, "censored_excluded": 0}
    j = rr.judge(big, 4000, edge, [0.0, 20_000_000.0])
    ok("V-RR-REHYDRATION-COUNTS", j["prior"]["verdict"] == "WOULD_ROLLOVER"
       and j["rehydrated"] == "INSUFFICIENT_EVIDENCE", f"{j['prior']} rehydrated={j['rehydrated']}")
    ev = rr.exposure(big, 200, rr.judge(big, 4000, many, [0.0]), [0.0, 1_000_000.0])
    ok("V-RR-EXPOSURE-NOT-A-SAVING", ev and "NOT a saving" in ev["label"]
       and ev["mechanical_exposure_read_eq"][0] < ev["mechanical_exposure_read_eq"][1], str(ev))
    # the write premium a fresh epoch pays (audit fold) must be in the number, not only in the prose:
    # a mutant dropping it kept the label and the interval and passed (C5 drill m5, 2026-10-03)
    g = rr.judge(big, 4000, many, [0.0])["growth_above_fresh"]
    prem = (big["resident"] - g) * (price["write"] - price["read"]) / price["read"]
    want = [round(g * 150 - prem - 1_000_000), round(g * 150 - prem)]
    ok("V-RR-EXPOSURE-CARRIES-WRITE-PREMIUM", prem > 0 and ev and ev["mechanical_exposure_read_eq"] == want,
       f"premium={prem:.0f} want={want} got={ev and ev['mechanical_exposure_read_eq']}")

    # ---- R1 live prior: provenance, expiry, a live session's tail never counted, censoring counted.
    led2 = d / "ledger2.jsonl"
    stamped = [{**r, "ts": T - 1000} for r in rows]   # real rows carry ts; an untimed resume is never "before"
    led2.write_text("\n".join(json.dumps(r) for r in stamped + [
        {"event": "successor_claimed", "session_id": "ROLLED", "claimant": "SX", "ts": T - 1000}]) + "\n",
        encoding="utf-8")
    now = T + rr.LIVE_GUARD_S
    live = sessions + [("LIVE", d / "E1.jsonl", now - 60)]          # active a minute ago: may still run
    bp = rr.build_prior(now=now, sessions=live, ledger_path=led2, find=paths.get, min_samples=1)
    ok("V-RR-PRIOR-ARTIFACT-MEASURED", bp["basis"] == "MEASURED_PRIOR" and bp["values"] == [39, 39, 39]
       and bp["censored_excluded"] == 1 and bp["expires_at"] == now + rr.PRIOR_TTL_S
       and bp["index_newest_ts"] == now - 60, f"{bp['basis']} values={bp['values']} censored={bp['censored_excluded']}")
    ok("V-RR-PRIOR-LIVE-GUARD", bp["sessions"] == 3, f"sessions={bp['sessions']} (E1, E2, CHAIN; LATE+LIVE in guard)")
    ok("V-RR-PRIOR-REHYDRATION-UPPER-BOUND", bp["rehydration"].get("basis") == "UPPER_BOUND_P50"
       and isinstance(bp["rehydration"].get("tokens"), int), str(bp["rehydration"]))
    thin = rr.build_prior(now=now, sessions=live, ledger_path=led2, find=paths.get, min_samples=5)
    ok("V-RR-PRIOR-THIN-IS-UNKNOWN", thin["basis"] == "UNKNOWN" and thin["reason"], str(thin["reason"]))

    # ---- ctx-rent S2: the /kresume protocol (resume .. certify) is rehydration; work after it is not.
    # A certify counts only when its tool_result is not an error AND carries a success RESUME_CERTIFIED
    # line: rollover.py also prints RESUME_CERTIFIED on two exit-5 paths and a refusal on the others.
    def cres(tid, text, err=False, as_str=False):
        return json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "is_error": err,
             "content": text if as_str else [{"type": "text", "text": text}]}]}})

    CERT = "& $py tools\\rollover.py certify --from P --claimant S --goal g --branch b --head h --next n"
    OK1 = "RESUME_CERTIFIED -- the capsule is retired; continue with the first obligation."

    def succ(tag, ctxs, certify_at=None, text=OK1, err=False, cmd=CERT, edit_at=None, as_str=False):
        out = []
        for k, ctx in enumerate(ctxs, 1):
            if k == certify_at:
                out += [use(f"{tag}{k}", f"{tag}-t{k}", ctx, cmd), cres(f"{tag}-t{k}", text, err, as_str)]
            elif k == edit_at:
                out.append(call(f"{tag}{k}", ctx, [("Edit", {"file_path": "x"})]))
            else:
                out.append(call(f"{tag}{k}", ctx))
        return out

    def cert_call(tag, **kw):
        lines = succ(tag, [120_000, 125_000, 130_000, 140_000, 150_000], **kw)
        return rr.session_trace(transcript(d, tag, lines))["certify_call"]

    fresh_ok = cert_call("CD1", certify_at=3)
    already_ok = cert_call("CD2", certify_at=3, text="RESUME_CERTIFIED (already) -- authority restored.", as_str=True)
    ok("V-RR-CERTIFY-DETECT", fresh_ok == 3 and already_ok == 3, f"fresh={fresh_ok} already={already_ok}")
    refused = cert_call("CD3", certify_at=3, err=True,
                        text="REFUSED: capsule is claimed by nobody, not S; run resume first.")
    flagged = cert_call("CD4", certify_at=3, err=True, text=OK1)          # the error flag wins over the text
    ok("V-RR-CERTIFY-DETECT[refused]", refused is None and flagged is None, f"refused={refused} flagged={flagged}")
    helps = [rr.is_certify_command(f"python tools/rollover.py certify {f}") for f in ("--help", "-h")]
    helped = cert_call("CD5", certify_at=3, cmd="python tools/rollover.py certify --help", text=OK1)
    ok("V-RR-CERTIFY-DETECT[help]", not any(helps) and helped is None
       and rr.is_certify_command("python tools/rollover.py certify --from a --claimant b"),
       f"help_detected={helps} help_trace={helped}")
    echoed = cert_call("CD6", certify_at=3, cmd="echo python tools/rollover.py certify",
                       text="python tools/rollover.py certify")
    echoed_text = cert_call("CD7", certify_at=3, cmd=f"echo '{OK1}'", text=OK1)
    ok("V-RR-CERTIFY-DETECT[echo]", echoed is None and echoed_text is None,
       f"echo_command={echoed} echo_of_success_text={echoed_text}")
    exit5 = [cert_call("CD8", certify_at=3, text="RESUME_CERTIFIED, but mutation authority was NOT restored: x."),
             cert_call("CD9", certify_at=3, text="RESUME_CERTIFIED (already) -- the marker names capsule a, not b."),
             cert_call("CDA", certify_at=3, text=OK1 + " ... mutation authority was NOT restored")]
    ok("V-RR-CERTIFY-DETECT[exit5-unflagged]", exit5 == [None, None, None], f"{exit5}")

    src = Path(rr.rollover.__file__).read_text(encoding="utf-8")
    pinned = ("RESUME_CERTIFIED -- the capsule is retired", "RESUME_CERTIFIED (already) -- ",
              "authority restored", "NOT restored")
    gone = [t for t in pinned if t not in src]
    tied = [t for t in (*rr._CERTIFIED_OK[:1], "RESUME_CERTIFIED (already) -- ", "authority restored",
                        rr._CERTIFIED_NO) if t not in src]
    ok("V-RR-CERTIFY-TOKENS-PINNED", not gone and not tied, f"missing from rollover.py: {gone + tied}")

    T2 = 1_790_000_000.0
    proto_ctx = {"XA": [120_000, 125_000, 130_000, 140_000, 150_000],
                 "XB": [130_000, 135_000, 140_000, 150_000, 160_000],
                 "XC": [140_000, 145_000, 150_000, 160_000, 170_000]}
    proto_paths = {t: transcript(d, t, succ(t, c, certify_at=3, edit_at=5)) for t, c in proto_ctx.items()}
    led_p = d / "ledger-proto.jsonl"
    led_p.write_text("\n".join(json.dumps(r) for t in proto_ctx for r in (
        {"event": "successor_claimed", "session_id": f"Q{t}", "claimant": t, "ts": T2 - 1000},
        {"event": "resume_certified", "session_id": f"Q{t}", "wrong": [], "ts": T2 - 1000})) + "\n",
        encoding="utf-8")
    find_p = proto_paths.get                      # fresh_cost looks up the SUCCESSOR (claimant), never the predecessor
    fcp = rr.fresh_cost(led_p, find=find_p, min_samples=3)
    xa = next(s for s in fcp["samples"] if s["successor"] == "XA")
    bpp = rr.build_prior(now=T2 + rr.LIVE_GUARD_S, sessions=[], ledger_path=led_p, find=find_p, min_samples=3)
    reh = bpp["rehydration"]
    ok("V-RR-PROTOCOL-NOT-WORK", xa["protocol_overhead"] == 375_000 and xa["carried_before_first_mutation"] == 515_000
       and xa["calls_to_certify"] == 3 and xa["calls_to_first_mutation"] == 5
       and reh.get("basis") == "PROTOCOL_P90" and reh.get("tokens") == fcp["protocol_overhead"]["p90"] == 435_000
       and reh.get("p50") == 405_000 and reh.get("upper_bound_p50") == fcp["carried_before_first_mutation"]["p50"] == 555_000,
       f"XA protocol={xa['protocol_overhead']} carried={xa['carried_before_first_mutation']} prior={reh}")

    nc_ctx = [120_000, 125_000, 130_000, 140_000, 150_000]
    nc_paths = {"XN1": transcript(d, "XN1", succ("XN1", nc_ctx, edit_at=3)),            # never ran certify
                "XN2": transcript(d, "XN2", succ("XN2", nc_ctx, certify_at=2, err=True, edit_at=4,
                                                 text="REFUSED: no reality refresh is recorded; run resume first."))}
    led_n = d / "ledger-nocert.jsonl"
    led_n.write_text("\n".join(json.dumps(r) for t in nc_paths for r in (
        {"event": "successor_claimed", "session_id": f"Q{t}", "claimant": t, "ts": T2 - 1000},
        {"event": "resume_certified", "session_id": f"Q{t}", "wrong": [], "ts": T2 - 1000})) + "\n",
        encoding="utf-8")
    find_n = nc_paths.get
    fcn = rr.fresh_cost(led_n, find=find_n, min_samples=2)
    bpn = rr.build_prior(now=T2 + rr.LIVE_GUARD_S, sessions=[], ledger_path=led_n, find=find_n, min_samples=2)
    rn = bpn["rehydration"]
    ok("V-RR-NO-CERTIFY-NOT-ZERO", len(fcn["samples"]) == 2
       and all(s["calls_to_certify"] is None and s["protocol_overhead"] is None for s in fcn["samples"])
       and fcn["no_certify_call"] == 2 and fcn["protocol_overhead"]["n"] == 0
       and rn.get("basis") == "UPPER_BOUND_P50" and isinstance(rn.get("tokens"), int) and rn["tokens"] > 0
       and rn["tokens"] == fcn["carried_before_first_mutation"]["p50"],
       f"samples={[(s['successor'], s['calls_to_certify'], s['protocol_overhead']) for s in fcn['samples']]} "
       f"no_certify_call={fcn['no_certify_call']} prior={rn}")

    # ---- R2 re-runnable: a grown, committing session is a candidate; a flat one is not.
    grow = [call(f"G{k}", 100_000 + k * 20_000) if k != 30 else use(f"G{k}", "Gt30", 100_000 + k * 20_000,
            "git commit -m g") for k in range(40)] + [result("Gt30")]
    transcript(d, "GROW", grow)
    srch = rr.negative_search(limit=5, sessions=sessions + [("GROW", d / "GROW.jsonl", T - 50)],
                              find={"GROW": d / "GROW.jsonl"}.get, ledger_path=led2)
    ok("V-RR-SEARCH-CANDIDATES", srch["candidates"] == 1 and srch["boundaries"] == 1, str(srch))

    print(f"ROLLOVER_REPLAY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
