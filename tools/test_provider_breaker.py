"""V-BREAKER gates for tools/provider_breaker.py (+ its call site in gsd_mission).
    python tools/test_provider_breaker.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import provider_breaker as pb  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def outcomes(table):
    return lambda sid: table.get(sid, {"class": None})


def main() -> int:
    at = NOW - 60
    ok = {"class": None, "at": at}
    tr = {"class": pb.TRANSIENT, "text": "API Error: 529 overloaded", "at": at}

    gate("V-BREAKER-MODEL-ANSWERED", pb.decide("m", "w3", NOW, workers=["w3"], outcome=outcomes({"w3": ok}),
                                               cleared_at=0) is None, "real turn -> no hold")

    q_text = "You've hit your weekly limit · resets 8pm (Europe/Madrid)"
    h = pb.decide("m", "w1", NOW, workers=["w1"], cleared_at=0,
                  outcome=outcomes({"w1": {"class": pb.QUOTA, "text": q_text, "at": at}}))
    ref = gm.quota_hold(q_text, at, NOW)
    gate("V-BREAKER-QUOTA-CONTRACT-KEPT", h is not None and ref is not None and h["until"] == ref["until"]
         and h["class"] == pb.QUOTA, f"breaker until={h and h['until']} quota_hold until={ref and ref['until']}")

    # The incident (m-d82c7cb6b87e, 2026-09-28) through the REAL hold_for: refusal row 13:51:35Z
    # "resets 4pm (Europe/Madrid)" = 14:00Z, the host appended rows until 14:52Z (mtime), the sweep
    # asked at 17:48Z. Both detectors must anchor on the row: either one on the mtime holds 24 h.
    sess = "You've hit your session limit · resets 4pm (Europe/Madrid)"
    tdir = Path(tempfile.mkdtemp())
    tp = tdir / "w-q.jsonl"
    tp.write_text("\n".join(json.dumps(r) for r in (
        {"type": "assistant", "timestamp": "2026-09-28T13:51:35.565Z",
         "message": {"model": "<synthetic>", "content": [{"type": "text", "text": sess}]}},
        {"type": "system", "timestamp": "2026-09-28T13:51:35.654Z"}, {"type": "cost-state"})) + "\n",
        encoding="utf-8")
    os.utime(tp, (1790607120.0, 1790607120.0))
    o = pb.worker_outcome("w-q", find=lambda sid: tp)
    gate("V-BREAKER-OUTCOME-AT-IS-ROW-TIME", o.get("at") == 1790603495.565, f"at={o.get('at')}")
    saved_find = gm.lr.find_transcript
    gm.lr.find_transcript = lambda sid: tp if sid == "w-q" else None
    try:
        after = pb.hold_for({"mission_id": "m-q-anchor", "owner": {"session_id": "w-q"}}, 1790617680.0)
        before = pb.hold_for({"mission_id": "m-q-anchor", "owner": {"session_id": "w-q"}}, 1790603555.0)
    finally:
        gm.lr.find_transcript = saved_find
    gate("V-BREAKER-QUOTA-ANCHOR-RELEASES", after is None, f"17:48Z -> {after}")
    gate("V-BREAKER-QUOTA-ANCHOR-CONTROL-HOLDS", before is not None and before.get("until") == 1790604000.0,
         f"13:52Z -> {before and before.get('until')}")

    h = pb.decide("m", "w1", NOW, workers=["w1"], cleared_at=0,
                  outcome=outcomes({"w1": {"class": pb.AUTH, "text": "Invalid API key · Please run /login", "at": at}}))
    gate("V-BREAKER-AUTH-QUARANTINE", h and h["quarantine"] and h["until"] is None, h and h["reason"][:60])

    h = pb.decide("m", "w2", NOW, workers=["w0", "w1", "w2"], cleared_at=0,
                  outcome=outcomes({"w0": ok, "w1": ok, "w2": tr}))
    gate("V-BREAKER-BACKOFF-1", h and h["streak"] == 1 and h["until"] == at + 300, f"streak={h and h['streak']}")

    h = pb.decide("m", "w3", NOW, workers=["w0", "w1", "w2", "w3"], cleared_at=0,
                  outcome=outcomes({"w0": ok, "w1": tr, "w2": tr, "w3": tr}))
    gate("V-BREAKER-BACKOFF-3", h and h["streak"] == 3 and h["until"] == at + 1200 and not h["quarantine"],
         f"streak={h and h['streak']} wait={h and h['until'] - at}")

    h = pb.decide("m", "w1", NOW + 400, workers=["w0", "w1"], cleared_at=0, outcome=outcomes({"w0": ok, "w1": tr}))
    gate("V-BREAKER-BACKOFF-EXPIRES", h is None, "300 s backoff, 400 s later -> relaunch allowed")

    four = {"w1": tr, "w2": {**tr, "class": pb.NO_REPLY}, "w3": tr, "w4": tr}
    h = pb.decide("m", "w4", NOW, workers=["w1", "w2", "w3", "w4"], cleared_at=0, outcome=outcomes(four))
    gate("V-BREAKER-STREAK-QUARANTINE", h and h["quarantine"] and h["streak"] == 4, h and h["reason"][:70])

    h = pb.decide("m", "w4", NOW, workers=["w1", "w2", "w3", "w4"], cleared_at=at + 1, outcome=outcomes(four))
    gate("V-BREAKER-OPERATOR-CLEAR", h is None, "clear newer than the evidence -> released")
    h = pb.decide("m", "w4", NOW, workers=["w1", "w2", "w3", "w4"], cleared_at=at - 1, outcome=outcomes(four))
    gate("V-BREAKER-STALE-CLEAR", h and h["quarantine"], "clear OLDER than the evidence -> still quarantined")

    # Regla 12: the same NON-transient failure twice quarantines at 2; a known transient keeps 4.
    nr = {"class": pb.NO_REPLY, "text": "worker produced no assistant reply", "at": at}
    unk = {"class": pb.TRANSIENT, "text": "Error: tool schema rejected (req 4f9a2c1b7e)", "at": at}

    def two(a, b):
        return pb.decide("m", "w2", NOW, workers=["w0", "w1", "w2"], cleared_at=0,
                         outcome=outcomes({"w0": ok, "w1": a, "w2": b}))

    h = two(nr, nr)
    gate("V-BREAKER-IDENTICAL-NO-REPLY-2", h and h["quarantine"] and h["streak"] == 2 and "Regla 12" in h["reason"],
         h and h["reason"][:80])
    h = two(unk, unk)
    gate("V-BREAKER-IDENTICAL-HOST-TEXT-2", h and h["quarantine"], h and h["reason"][:80])
    h = two({**unk, "text": "Error: tool schema rejected (req 99aa00bbcc)"}, unk)
    gate("V-BREAKER-IDENTICAL-IDS-COLLAPSED", h and h["quarantine"], "request ids differ -> still identical")
    h = two(tr, tr)
    gate("V-BREAKER-KNOWN-TRANSIENT-2-BACKS-OFF", h and not h["quarantine"] and h["until"] == at + 600,
         f"q={h and h['quarantine']} wait={h and h['until'] and h['until'] - at}")
    h = two(nr, unk)
    gate("V-BREAKER-DIFFERENT-FAILURES-2-BACKS-OFF", h and not h["quarantine"], f"q={h and h['quarantine']}")
    h = two(ok, nr)
    gate("V-BREAKER-SINGLE-NO-REPLY-BACKS-OFF", h and not h["quarantine"] and h["streak"] == 1,
         f"q={h and h['quarantine']} streak={h and h['streak']}")
    h = pb.decide("m", "w2", NOW, workers=["w0", "w1", "w2"], cleared_at=at + 1,
                  outcome=outcomes({"w0": ok, "w1": nr, "w2": nr}))
    gate("V-BREAKER-IDENTICAL-OPERATOR-CLEAR", h is None, "clear newer than the evidence -> released")
    os.environ["CPP_BREAKER_IDENTICAL"] = "off"
    try:
        h = two(nr, nr)
    finally:
        os.environ.pop("CPP_BREAKER_IDENTICAL", None)
    gate("V-BREAKER-IDENTICAL-KILL-SWITCH", h and not h["quarantine"], "CPP_BREAKER_IDENTICAL=off -> backoff")

    # P4 tool-failure signal: read from the worker's own rows; a model turn after N identical tool errors.
    def tool_rows(results, end_text="BLOCKED: cannot proceed"):
        rows = []
        for i, (name, text, err) in enumerate(results):
            rows.append({"type": "assistant", "message": {"model": "claude-opus-5-5", "content": [
                {"type": "tool_use", "id": f"t{i}", "name": name, "input": {}}]}})
            rows.append({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": f"t{i}", "is_error": err, "content": text}]}})
        rows.append({"type": "assistant", "message": {"model": "claude-opus-5-5",
                                                      "content": [{"type": "text", "text": end_text}]}})
        return rows

    miss = ("Bash", "Exit code 1: no such file tools/x_17.py", True)
    tf = pb.tool_failure(tool_rows([miss, ("Bash", "Exit code 1: no such file tools/x_18.py", True)]))
    gate("V-BREAKER-TOOLFAIL-DETECTED", tf and tf["class"] == pb.TOOL_FAILURE and tf["text"].startswith("Bash:"), tf)
    gate("V-BREAKER-TOOLFAIL-SUCCESS-AFTER-NOT", pb.tool_failure(tool_rows([miss, miss, ("Bash", "ok", False)])) is None,
         "errors then a success -> not stuck")
    gate("V-BREAKER-TOOLFAIL-DIFFERENT-ERRORS-NOT",
         pb.tool_failure(tool_rows([miss, ("Bash", "Permission denied", True)])) is None, "two different errors")
    gate("V-BREAKER-TOOLFAIL-OTHER-TOOL-NOT",
         pb.tool_failure(tool_rows([miss, ("Read", miss[1], True)])) is None, "same text, different tool")
    gate("V-BREAKER-TOOLFAIL-ONE-ERROR-NOT", pb.tool_failure(tool_rows([("Read", "ok", False), miss])) is None,
         "one error is not a streak")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wt.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in tool_rows([miss, miss])) + "\n", encoding="utf-8")
        o = pb.worker_outcome("wt", find=lambda sid: p)
    gate("V-BREAKER-TOOLFAIL-THROUGH-WORKER-OUTCOME", o.get("class") == pb.TOOL_FAILURE and o.get("at"), o)

    tfo = {"class": pb.TOOL_FAILURE, "text": "Bash: Exit code 1: no such file tools/x_17.py", "at": at}
    h = two(ok, tfo)
    gate("V-BREAKER-TOOLFAIL-ONE-WORKER-NO-HOLD", h is None, f"one stuck worker -> {h}")
    h = two({**tfo, "text": "Bash: Exit code 1: no such file tools/x_99.py"}, tfo)
    gate("V-BREAKER-TOOLFAIL-TWO-WORKERS-QUARANTINE", h and h["quarantine"] and h["class"] == pb.TOOL_FAILURE
         and "Regla 12" in h["reason"], h and h["reason"][:90])
    h = two({**tfo, "text": "Edit: old_string not found"}, tfo)
    gate("V-BREAKER-TOOLFAIL-DIFFERENT-WORKERS-NO-HOLD", h is None, f"different failures -> {h}")
    tmo = {**tfo, "text": "Bash: Command timed out after 2m"}
    h = two(tmo, tmo)
    gate("V-BREAKER-TOOLFAIL-TIMEOUT-STILL-COUNTS", h and h["quarantine"],
         "a tool timing out identically twice is not a provider transient")
    os.environ["CPP_BREAKER_TOOL_FAILURE"] = "off"
    try:
        off = pb.tool_failure(tool_rows([miss, miss]))
    finally:
        os.environ.pop("CPP_BREAKER_TOOL_FAILURE", None)
    gate("V-BREAKER-TOOLFAIL-KILL-SWITCH", off is None, "CPP_BREAKER_TOOL_FAILURE=off -> no signal")

    # P4 external effect: the LAST tool call is an effect whose outcome is not on the record.
    marker = "PROBE" + "MARK" + "0" * 6          # assembled at runtime: no credential-shaped literal in the file
    hdr = "X-Probe: " + marker

    def effect_rows(name, inp, result=None):
        rows = [{"type": "assistant", "timestamp": "2026-11-20T10:00:00Z", "message": {
            "model": "claude-opus-5-5", "content": [{"type": "tool_use", "id": "e1", "name": name, "input": inp}]}}]
        if result is not None:
            rows.append({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "e1", "is_error": result[0], "content": result[1]}]}})
        return rows

    e = pb.effect_unconfirmed(effect_rows("Bash", {"command": "git push origin main"}))
    gate("V-BREAKER-EFFECT-NO-RESULT", e and e["class"] == pb.EFFECT_UNCONFIRMED and "git push" in e["text"]
         and e.get("at"), e)
    e = pb.effect_unconfirmed(effect_rows("Bash", {"command": "git push origin main"}, (False, "Everything up-to-date")))
    gate("V-BREAKER-EFFECT-RETURNED-CONTROL", e is None, "the push returned: outcome on the record")
    e = pb.effect_unconfirmed(effect_rows("PowerShell", {"command": "git push"},
                                          (True, "[Request interrupted by user for tool use]")))
    gate("V-BREAKER-EFFECT-INTERRUPTED", e and "interrupted" in e["text"], e)
    e = pb.effect_unconfirmed(effect_rows("Bash", {"command": "git push"}, (True, "rejected: non-fast-forward")))
    gate("V-BREAKER-EFFECT-FAILED-IS-KNOWN", e is None, "an error result is a known outcome, not an unknown one")
    e = pb.effect_unconfirmed(effect_rows("Bash", {"command": "pytest -q"}))
    gate("V-BREAKER-EFFECT-LOCAL-CONTROL", e is None, "a local command with no result is not an external effect")
    e = pb.effect_unconfirmed(effect_rows("Bash", {"command": f"curl -H '{hdr}' -X POST https://api.example/x"}))
    gate("V-BREAKER-EFFECT-HTTP-WRITE-REDACTED", e and "http write" in e["text"] and marker not in str(e), e)
    e = pb.effect_unconfirmed(effect_rows("mcp__claude_ai_Gmail__send_message", {"to": "x"}))
    gate("V-BREAKER-EFFECT-MCP-SEND", e and e["text"].endswith("send_message (no result)"), e)
    e = pb.effect_unconfirmed(effect_rows("mcp__claude_ai_Gmail__search_threads", {"q": "x"}))
    gate("V-BREAKER-EFFECT-MCP-READ-CONTROL", e is None, "an MCP read is not an effect")
    later = effect_rows("Bash", {"command": "git push"}) + [{"type": "assistant", "message": {
        "model": "claude-opus-5-5", "content": [{"type": "tool_use", "id": "e2", "name": "Read", "input": {}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "e2", "content": "x"}]}}]
    gate("V-BREAKER-EFFECT-ONLY-LAST-CALL", pb.effect_unconfirmed(later) is None, "a later call returned")

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "we.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in effect_rows("Bash", {"command": "vercel --prod"})) + "\n",
                     encoding="utf-8")
        o = pb.worker_outcome("we", find=lambda sid: p)
    gate("V-BREAKER-EFFECT-THROUGH-WORKER-OUTCOME", o.get("class") == pb.EFFECT_UNCONFIRMED, o)
    eo = {"class": pb.EFFECT_UNCONFIRMED, "text": "Bash: git push (no result)", "at": at}
    h = two(ok, eo)
    gate("V-BREAKER-EFFECT-QUARANTINES-AT-ONCE", h and h["quarantine"] and h["until"] is None
         and "never confirmed" in h["reason"], h and h["reason"][:90])
    h = pb.decide("m", "w2", NOW, workers=["w0", "w1", "w2"], cleared_at=at + 1,
                  outcome=outcomes({"w0": ok, "w1": ok, "w2": eo}))
    gate("V-BREAKER-EFFECT-CLEAR-RECONCILES", h is None, "operator clear after the evidence -> released")
    os.environ["CPP_BREAKER_EFFECT"] = "off"
    try:
        off = pb.effect_unconfirmed(effect_rows("Bash", {"command": "git push"}))
    finally:
        os.environ.pop("CPP_BREAKER_EFFECT", None)
    gate("V-BREAKER-EFFECT-KILL-SWITCH", off is None, "CPP_BREAKER_EFFECT=off -> no park")

    # Review fixes (pp-code-reviewer 2026-11-21).
    # F1: a tool_result is untrusted; only the tool and a digest leave tool_failure.
    leak = ("Bash", f"Exit code 22: curl failed, sent {hdr}", True)
    tf = pb.tool_failure(tool_rows([leak, leak]))
    gate("V-BREAKER-TOOLFAIL-RESULT-REDACTED", tf and marker not in str(tf) and tf["text"].startswith("Bash: repeated"), tf)
    other = ("Bash", "Exit code 1: permission denied on /srv/x", True)
    ta, tb = pb.tool_failure(tool_rows([miss, miss])), pb.tool_failure(tool_rows([other, other]))
    gate("V-BREAKER-TOOLFAIL-DIGEST-DISTINGUISHES", ta and tb and ta["text"] != tb["text"],
         f"{ta and ta['text']} vs {tb and tb['text']}")
    h = two({**ta, "at": at}, {**tb, "at": at})
    gate("V-BREAKER-TOOLFAIL-DIGESTS-DIFFER-NO-HOLD", h is None, f"different errors through the digest -> {h}")
    h = two({**ta, "at": at}, {**pb.tool_failure(tool_rows([("Bash", miss[1].replace("17", "91"), True)] * 2)), "at": at})
    gate("V-BREAKER-TOOLFAIL-DIGESTS-SAME-QUARANTINE", h and h["quarantine"], "numbers collapse before the digest")
    # F2: provider transients the regex missed back off, never quarantine at 2.
    conn = {"class": pb.TRANSIENT, "text": "API Error: Connection error.", "at": at}
    h = two(conn, conn)
    gate("V-BREAKER-CONNECTION-ERROR-BACKS-OFF", h and not h["quarantine"], f"q={h and h['quarantine']}")
    missed = [t for t in ("fetch failed", "connect ECONNREFUSED 1.2.3.4", "getaddrinfo ENOTFOUND api", "EAI_AGAIN",
                          "Unable to connect to API", "Internal server error", "no capacity available")
              if not pb.KNOWN_TRANSIENT_RE.search(t)]
    gate("V-BREAKER-TRANSIENT-ALTERNATIVES", not missed, f"unmatched: {missed}")
    # F3: tool failures never feed the provider streak.
    stuck = {f"w{i}": {"class": pb.TOOL_FAILURE, "text": f"Bash: repeated error {c * 12}", "at": at}
             for i, c in zip(range(1, 5), "ghij")}
    h = pb.decide("m", "w4", NOW, workers=["w1", "w2", "w3", "w4"], cleared_at=0, outcome=outcomes(stuck))
    gate("V-BREAKER-TOOLFAIL-FOUR-DIFFERENT-NO-HOLD", h is None, f"4 different stuck workers -> {h}")
    # F4: a bare exit code and a hook/user refusal are not a stuck tool; a real error is (DETECTED above).
    gate("V-BREAKER-TOOLFAIL-BARE-EXIT-CODE-NOT",
         pb.tool_failure(tool_rows([("Bash", "Exit code 1", True), ("Bash", "Exit code 2", True)])) is None,
         "grep with no match twice")
    hook = ("Bash", "PreToolUse:Bash hook error: Blocked by a PreToolUse gate (exit 2)", True)
    gate("V-BREAKER-TOOLFAIL-HOOK-BLOCK-NOT", pb.tool_failure(tool_rows([hook, hook])) is None, "policy, not a tool")
    # F5: only the host's interrupt marker is an unknown outcome.
    kb = pb.effect_unconfirmed(effect_rows("Bash", {"command": "ssh host 'python x.py'"},
                                           (True, "Traceback ... KeyboardInterrupt")))
    gate("V-BREAKER-EFFECT-REMOTE-KEYBOARDINTERRUPT-KNOWN", kb is None, kb)
    rj = pb.effect_unconfirmed(effect_rows("Bash", {"command": "git push"}, (True, "The user doesn't want to proceed "
                                                                            "with this tool use. The tool use was rejected")))
    gate("V-BREAKER-EFFECT-USER-REJECTED-KNOWN", rj is None, "a rejected push never ran")
    # F6: coverage either side.
    for gname, cmd in (("V-BREAKER-EFFECT-GIT-C-PUSH", "& 'C:\\Program Files\\Git\\cmd\\git.exe' -C repo push origin x"),
                       ("V-BREAKER-EFFECT-GH-API-POST", "gh api repos/o/r/issues -X POST -f title=t")):
        e = pb.effect_unconfirmed(effect_rows("PowerShell", {"command": cmd}))
        gate(gname, e and e["class"] == pb.EFFECT_UNCONFIRMED, e)
    gate("V-BREAKER-EFFECT-MCP-PREFIX-WORD-CONTROL",
         pb.effect_unconfirmed(effect_rows("mcp__x__sendgrid_lookup", {})) is None, "'sendgrid' is not 'send'")

    # Transcript reading: only HOST-written replies count. A model that quotes the refusal is a model.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)

        def tx(name, model, text):
            p = d / f"{name}.jsonl"
            p.write_text(json.dumps({"type": "user", "message": {"content": "go"}}) + "\n" + json.dumps(
                {"type": "assistant", "message": {"model": model, "content": [{"type": "text", "text": text}]}}) + "\n",
                encoding="utf-8")
            return p

        paths = {"synth": tx("synth", "<synthetic>", q_text),
                 "quoted": tx("quoted", "claude-opus-5-5", "The log says: You've hit your weekly limit · resets 8pm"),
                 "empty": d / "empty.jsonl"}
        paths["empty"].write_text(json.dumps({"type": "user", "message": {"content": "go"}}) + "\n", encoding="utf-8")
        s = pb.worker_outcome("synth", find=paths.get)
        m = pb.worker_outcome("quoted", find=paths.get)
        e = pb.worker_outcome("empty", find=paths.get)
        n = pb.worker_outcome("missing", find=paths.get)
    gate("V-BREAKER-SYNTHETIC-ONLY", s["class"] == pb.QUOTA and m["class"] is None,
         f"host refusal -> {s['class']}; model quoting it -> {m['class']}")
    gate("V-BREAKER-NO-REPLY", e["class"] == pb.NO_REPLY, e["class"])
    gate("V-BREAKER-UNKNOWN-IS-NOT-A-CLASS", n["class"] is None and "unknown" in n, n)

    os.environ["CPP_PROVIDER_BREAKER"] = "off"
    try:
        saved = gm.quota_hold_from_transcript
        gm.quota_hold_from_transcript = lambda sid, now: None
        h = pb.hold_for({"mission_id": "m", "owner": {"session_id": "w1"}}, NOW)
    finally:
        gm.quota_hold_from_transcript = saved
        os.environ.pop("CPP_PROVIDER_BREAKER", None)
    gate("V-BREAKER-KILL-SWITCH", h is None, "CPP_PROVIDER_BREAKER=off -> quota_hold only")

    # One quota detector: hold_for asks gsd_mission's quota owner first (its test seam included).
    saved = gm.quota_hold_from_transcript
    gm.quota_hold_from_transcript = lambda sid, now: {"until": now + 5, "reason": "q"}
    try:
        h = pb.hold_for({"mission_id": "m", "owner": {"session_id": "w1"}}, NOW)
    finally:
        gm.quota_hold_from_transcript = saved
    gate("V-BREAKER-QUOTA-OWNER-FIRST", h and h["class"] == pb.QUOTA and h["reason"] == "q", h)

    rows = []
    saved_pb, saved_app = sys.modules.get("provider_breaker"), gm.lr.ledger_append
    sys.modules["provider_breaker"] = None  # import fails -> fallback path
    gm.lr.ledger_append = lambda mid, ev, **f: rows.append(ev) or True
    try:
        h = gm.provider_hold({"mission_id": "m", "owner": {"session_id": "nobody"}}, NOW)
    finally:
        sys.modules["provider_breaker"] = saved_pb
        gm.lr.ledger_append = saved_app
    gate("V-BREAKER-UNAVAILABLE-IS-VISIBLE", "provider_breaker_unavailable" in rows,
         f"fallback ledger rows={rows} hold={h}")

    print(f"BREAKER_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
