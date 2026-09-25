#!/usr/bin/env python3
"""V-TRACE-* gates for modules/trace_context (UWCP assimilation R5).

The propagation case crosses a real process boundary: a child interpreter reads
TRACEPARENT from its own environment, so the gate measures the carrier, not a dict.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.trace_context import (AttributeRejected, SpanWriter, TraceContext, child_env,  # noqa: E402
                                   from_env, new_span_id, new_trace_id, parse_traceparent,
                                   span_record)

passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def main() -> int:
    t, s = new_trace_id(), new_span_id()
    check("V-TRACE-ID-FORMAT", len(t) == 32 and len(s) == 16 and t == t.lower()
          and int(t, 16) and int(s, 16), "ids are lowercase hex, 32/16 digits, non-zero", f"{t} {s}")
    good = f"00-{t}-{s}-01"
    ctx = parse_traceparent(good)
    check("V-TRACE-ROUNDTRIP", ctx is not None and ctx.traceparent() == good and ctx.sampled,
          "a valid header parses and re-serialises byte-identically", f"{ctx}")
    bad = {
        "uppercase": good.upper(),
        "zero-trace": f"00-{'0' * 32}-{s}-01",
        "zero-span": f"00-{t}-{'0' * 16}-01",
        "version-ff": f"ff-{t}-{s}-01",
        "v00-extra-field": good + "-extra",
        "short": f"00-{t[:30]}-{s}-01",
        "empty": "",
        "none": None,
    }
    rejected = {k: parse_traceparent(v) is None for k, v in bad.items()}
    check("V-TRACE-STRICT", all(rejected.values()), "every malformed header is refused",
          f"accepted: {[k for k, v in rejected.items() if not v]}")
    future = parse_traceparent(f"01-{t}-{s}-01-futurefield")
    check("V-TRACE-FORWARD-COMPAT", future is not None,
          "a higher version with extra fields is still read (spec forward compatibility)", "refused")

    inh = from_env({"TRACEPARENT": "garbage"})
    check("V-TRACE-INVALID-INHERITED", inh.finding and inh.context.trace_id != t
          and parse_traceparent(inh.context.traceparent()) is not None,
          "an unusable inherited header starts a new trace AND records a finding", f"{inh}")
    clean = from_env({})
    check("V-TRACE-ABSENT-INHERITED", clean.finding == "" and clean.context.trace_id,
          "no inherited header: a new trace with no finding (absence is not an error)", f"{clean}")

    # real process boundary
    child_span = new_span_id()
    env = child_env({**__import__("os").environ}, TraceContext(t, s, True, "k=v"), child_span)
    code = ("import sys,json;sys.path.insert(0,sys.argv[1]);from modules.trace_context import from_env;"
            "i=from_env();print(json.dumps([i.context.trace_id,i.context.span_id,i.context.tracestate,i.finding]))")
    out = subprocess.run([sys.executable, "-c", code, str(ROOT)], env=env, capture_output=True,
                         text=True, timeout=60).stdout.strip()
    got = json.loads(out) if out else None
    check("V-TRACE-CHILD-PROCESS", got == [t, child_span, "k=v", ""],
          "a child process inherits the trace, sees its parent span and the tracestate",
          f"child saw {got}")

    try:
        span_record("x", t, s, "", 1, 2, "h", {"model": "qwen"})
        check("V-TRACE-ATTR-PINNED", False, "", "an unpinned attribute name was accepted")
    except AttributeRejected:
        rec = span_record("epoch", t, s, "", 1, 2, "h",
                          {"gen_ai.request.model": "qwen3-coder", "uwcp.epoch_id": "ep-1"})
        check("V-TRACE-ATTR-PINNED", rec["attributes"]["gen_ai.request.model"] == "qwen3-coder",
              "only pinned gen_ai.* / uwcp.* / error.type names are accepted", "")
    try:
        span_record("x", t, s, "", 5, 4, "h")
        check("V-TRACE-TIME-ORDER", False, "", "a span ending before it starts was accepted")
    except AttributeRejected:
        check("V-TRACE-TIME-ORDER", True, "a span ending before it starts is refused", "")

    d = Path(tempfile.mkdtemp())
    w = SpanWriter(d / "spans.jsonl")
    w.emit(span_record("a", t, s, "", 1, 2, "h"))
    blocked = d / "is_a_dir"
    blocked.mkdir()
    w2 = SpanWriter(blocked)
    try:
        ok = w2.emit({"x": 1})
    except Exception as exc:               # the defect under test, reported as a verdict
        ok, w2.last_error = None, f"RAISED {type(exc).__name__}"
    check("V-TRACE-EMIT-NEVER-RAISES", w.emitted == 1 and not ok and w2.failures == 1
          and w2.last_error, "a write failure is counted and returned, never raised", f"{w2.last_error}")
    line = json.loads((d / "spans.jsonl").read_text(encoding="utf-8").splitlines()[0])
    check("V-TRACE-OTLP-SHAPE", {"traceId", "spanId", "parentSpanId", "name", "startTimeUnixNano",
                                  "endTimeUnixNano", "attributes"} <= set(line),
          "records carry OTLP JSON span field names", f"{sorted(line)}")

    print(f"TRACE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
