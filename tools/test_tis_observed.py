#!/usr/bin/env python3
"""V-TISOBS gates for tools/tis_observed.py (observed usage from transcripts).

Every fixture is synthetic and built here; no real transcript is read.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tis_observed as T  # noqa: E402

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  [PASS] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  [FAIL] {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def line(mid, rid, inp, cc, cr, out, model="claude-opus-5-5", thinking=None):
    usage = {"input_tokens": inp, "cache_creation_input_tokens": cc,
             "cache_read_input_tokens": cr, "output_tokens": out}
    if thinking is not None:
        usage["output_tokens_details"] = {"thinking_tokens": thinking}
    msg = {"model": model, "usage": usage}
    if mid is not None:
        msg["id"] = mid
    obj = {"type": "assistant", "message": msg}
    if rid is not None:
        obj["requestId"] = rid
    return json.dumps(obj)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "proj"
        proj.mkdir()
        # Session A: call m1 streamed as 3 content-block lines (identical usage),
        # call m2 once, one synthetic notice, one malformed line, one user line.
        a = proj / "sessA.jsonl"
        a.write_text("\n".join([
            json.dumps({"type": "user", "message": {"content": "hi"}}),
            line("m1", "r1", 2, 100000, 0, 10, thinking=4),
            line("m1", "r1", 2, 100000, 0, 10, thinking=4),
            line("m1", "r1", 2, 100000, 0, 10, thinking=4),
            "{not json",
            line("m2", "r2", 5, 1000, 100000, 20),
            line("s1", "r3", 0, 0, 0, 0, model=T.SYNTHETIC_MODEL),
        ]) + "\n", encoding="utf-8")
        # Subagent transcript for session A.
        sub = proj / "sessA" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-x.jsonl").write_text(
            line("g1", "q1", 1, 500, 0, 3) + "\n" + line("g1", "q1", 1, 500, 0, 3) + "\n",
            encoding="utf-8")
        # Session B: BOM written as raw bytes (json/Python writers never emit one),
        # plus a call with no identity at all.
        b = proj / "sessB.jsonl"
        b.write_bytes(b"\xef\xbb\xbf" + (line(None, None, 7, 0, 0, 1) + "\n").encode())
        # Session C: parses, holds no real call.
        c = proj / "sessC.jsonl"
        c.write_text(json.dumps({"type": "user", "message": {"content": "x"}}) + "\n",
                     encoding="utf-8")

        sa = T.read_session(a)
        check("V-TISOBS-DEDUPE", sa.calls == 2,
              f"3 streamed lines of m1 + m2 -> calls={sa.calls} (expected 2)")
        check("V-TISOBS-DEDUPE-TOTALS",
              sa.cache_creation_tokens == 101000 and sa.output_tokens == 30,
              f"cc={sa.cache_creation_tokens} out={sa.output_tokens}")
        check("V-TISOBS-SYNTHETIC-EXCLUDED",
              sa.synthetic_skipped == 1 and T.SYNTHETIC_MODEL not in sa.models,
              f"synthetic_skipped={sa.synthetic_skipped} models={sa.models}")
        check("V-TISOBS-BADLINE-COUNTED", sa.bad_lines == 1,
              f"bad_lines={sa.bad_lines}")
        check("V-TISOBS-FIRST-CALL", sa.first_call_context == 100002,
              f"first_call_context={sa.first_call_context}")
        # m1 read 0 of its 100002-token prefix from cache; m2's read is not first.
        check("V-TISOBS-FIRST-CALL-READ", sa.first_call_cache_read == 0,
              f"first_call_cache_read={sa.first_call_cache_read} (m2's 100000 read must not leak in)")
        check("V-TISOBS-THINKING", sa.thinking_tokens == 4,
              f"thinking={sa.thinking_tokens} (dedupe must not multiply it)")
        check("V-TISOBS-SUBAGENT",
              sa.subagent_files == 1 and sa.subagent_calls == 1
              and sa.subagent_context_tokens == 501,
              f"files={sa.subagent_files} calls={sa.subagent_calls} "
              f"ctx={sa.subagent_context_tokens}")
        sa_nosub = T.read_session(a, include_subagents=False)
        check("V-TISOBS-SUBAGENT-CONTROL", sa_nosub.subagent_calls == 0,
              f"no-subagents run -> subagent_calls={sa_nosub.subagent_calls}")

        sb = T.read_session(b)
        check("V-TISOBS-BOM", sb.state == "MEASURED" and sb.input_tokens == 7,
              f"state={sb.state} input={sb.input_tokens}")

        sc = T.read_session(c)
        check("V-TISOBS-MEASURED-ZERO",
              sc.state == "MEASURED_ZERO" and sc.first_call_context is None,
              f"state={sc.state}")

        sd = T.read_session(proj / "missing.jsonl")
        check("V-TISOBS-UNMEASURED", sd.state == "UNMEASURED" and sd.error,
              f"state={sd.state} error={sd.error[:40]}")
        check("V-TISOBS-STATES-DISTINCT",
              len({sa.state, sc.state, sd.state}) == 3,
              "MEASURED / MEASURED_ZERO / UNMEASURED all distinct")

        summ = T.summarize(T.scan([proj]))
        check("V-TISOBS-SUMMARY",
              summ["sessions"] == 3 and summ["calls"] == 3
              and summ["duplicate_usage_lines_collapsed"] == 2
              and summ["by_state"] == {"MEASURED": 2, "MEASURED_ZERO": 1}
              and summ["source"] == "observed",
              f"{ {k: summ[k] for k in ('sessions', 'calls', 'by_state', 'duplicate_usage_lines_collapsed')} }")

        # Prefix rides in every call: A = 100002 x 2, B = 7 x 1, over 201014.
        share = summ["startup_prefix_share_estimate"]
        check("V-TISOBS-PREFIX-CALL-WEIGHTED",
              share is not None and abs(share - 0.995) < 1e-4,
              f"startup_prefix_share_estimate={share} (expected 0.995, "
              f"a once-per-session ratio would read 0.4975)")

        # Wrong key once hit an existing EMPTY dir and exited 0 with 0 sessions.
        check("V-TISOBS-PROJECT-KEY",
              T.project_key(Path(r"C:\Users\User\.claude\skills\claude-power-pack"))
              == "C--Users-User--claude-skills-claude-power-pack",
              "the '.' of '.claude' becomes '-'")
        empty = Path(td) / "empty"
        empty.mkdir()
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as buf_e:
            rc_empty = T.main(["--project-dir", str(empty)])
        check("V-TISOBS-EMPTY-DIR-REFUSES",
              rc_empty == 2 and "UNMEASURED" in buf_e.getvalue(),
              f"empty dir -> rc={rc_empty}")
        with contextlib.redirect_stdout(io.StringIO()) as buf_p:
            rc_proj = T.main(["--project-dir", str(proj)])
        check("V-TISOBS-EMPTY-DIR-CONTROL",
              rc_proj == 0 and '"sessions": 3' in buf_p.getvalue(),
              f"populated dir -> rc={rc_proj}")

        # iter_calls: entrypoint + ts carried per call, subagents included.
        e = proj / "sessE.jsonl"
        e.write_text("\n".join([
            json.dumps({"type": "user", "entrypoint": "sdk-cli", "message": {"content": "x"}}),
            json.dumps({"type": "assistant", "timestamp": "2026-09-27T10:00:00Z",
                        "requestId": "rq", "message": {"id": "me", "model": "claude-opus-5-5",
                        "usage": {"input_tokens": 1, "output_tokens": 1}}}),
        ]) + "\n", encoding="utf-8")
        calls = [c for c in T.iter_calls([proj]) if c["session_id"] == "sessE"]
        check("V-TISOBS-ITER-ENTRYPOINT",
              len(calls) == 1 and calls[0]["entrypoint"] == "sdk-cli"
              and calls[0]["ts"] == "2026-09-27T10:00:00Z",
              f"{[(c['entrypoint'], c['ts']) for c in calls]}")
        n_sub = sum(1 for c in T.iter_calls([proj]) if c["session_id"] == "sessA")
        check("V-TISOBS-ITER-SUBAGENTS", n_sub == 3,
              f"sessA calls incl. subagent = {n_sub} (expected 2 + 1)")
        import os, time
        old = time.time() - 30 * 86400
        os.utime(e, (old, old))
        pruned = [c for c in T.iter_calls([proj], modified_since=time.time() - 86400)
                  if c["session_id"] == "sessE"]
        check("V-TISOBS-ITER-MTIME-PRUNE", pruned == [],
              "file untouched for 30d is skipped under a 1d window")

        shp = Path(td) / "shared"
        shp.mkdir()
        (shp / "s.jsonl").write_text("\n".join([
            json.dumps({"type": "user", "entrypoint": "sdk-cli", "message": {"content": "x"}}),
            line("f1", "q1", 0, 50, 50, 1),   # first call: 50 of 100 already cached
            line("f2", "q2", 0, 0, 100, 1),
        ]) + "\n", encoding="utf-8")
        shared = T.summarize(T.scan([shp]))["startup_shared_share_median"]
        check("V-TISOBS-SHARED-SHARE", shared == {"sdk-cli": 0.5},
              f"{shared} (first call only, keyed by entrypoint)")

        prices = {"input": 4.0, "output": 20.0, "cache_write_5m": 5.0,
                  "cache_write_1h": 8.0, "cache_read": 0.2}
        split = {"input_tokens": 1_000_000, "output_tokens": 1_000_000,
                 "cache_read_input_tokens": 1_000_000,
                 "cache_creation_input_tokens": 2_000_000,
                 "cache_creation": {"ephemeral_5m_input_tokens": 1_000_000,
                                    "ephemeral_1h_input_tokens": 1_000_000}}
        usd, assumed = T.cost_usd(split, prices)
        check("V-TISOBS-COST-SPLIT", abs(usd - 37.2) < 1e-9 and assumed is False,
              f"4 + 20 + 0.2 + 5 + 8 = 37.2 -> {usd} assumed={assumed}")
        nosplit = {k: v for k, v in split.items() if k != "cache_creation"}
        usd2, assumed2 = T.cost_usd(nosplit, prices)
        check("V-TISOBS-COST-TTL-ASSUMED", abs(usd2 - 34.2) < 1e-9 and assumed2 is True,
              f"no breakdown -> all writes at 5m: {usd2} assumed={assumed2}")
        usd3, _ = T.cost_usd(split, None)
        check("V-TISOBS-COST-UNPRICED-IS-NONE", usd3 is None,
              "a model with no price returns None, never 0.0")

    print(f"TISOBS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
