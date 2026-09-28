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
