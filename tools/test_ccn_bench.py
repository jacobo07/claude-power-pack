#!/usr/bin/env python3
"""V-CCN-BENCH gates for tools/ccn_bench.py: pricing, message-id dedupe, grading, CAF verdicts."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ccn_bench as b  # noqa: E402

passes = fails = 0


def check(name, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print("PASS %s: %s" % (name, ev))
    else:
        fails += 1
        print("FAIL %s: %s" % (name, ev))


def rec(mid, **u):
    return {"message": {"role": "assistant", "id": mid, "usage": u,
                        "content": [{"type": "tool_use", "name": "Read"}]}}


def write(recs):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for r in recs:
        f.write(json.dumps(r) + "\n")
    f.close()
    return f.name


u = {"input_tokens": 1000000, "cache_read_input_tokens": 1000000, "output_tokens": 1000000,
     "cache_creation_input_tokens": 2000000, "cache_creation": {"ephemeral_1h_input_tokens": 1000000, "ephemeral_5m_input_tokens": 1000000}}
check("V-CCN-BENCH-PRICE", abs(b.price(u) - (3 + 0.3 + 6 + 3.75 + 15)) < 1e-9, "price=%.4f expected 28.05" % b.price(u))
check("V-CCN-BENCH-PRICE-NOBREAKDOWN", abs(b.price({"cache_creation_input_tokens": 1000000}) - 3.75) < 1e-9, "bare write priced as 5m")

p = write([rec("m1", input_tokens=10, output_tokens=1), rec("m1", input_tokens=10, output_tokens=50),
           rec("m2", input_tokens=5, output_tokens=7), {"type": "user", "message": {"role": "user"}}])
t = b.transcript_cost(p)
check("V-CCN-BENCH-DEDUPE", t["calls"] == 2 and t["output"] == 57 and t["fresh_input"] == 15,
      "two ids, last usage per id wins: calls=%d output=%d fresh=%d (expect 2/57/15)" % (t["calls"], t["output"], t["fresh_input"]))
# mutant: summing every record instead of one per id must differ
naive = sum(r["message"]["usage"].get("output_tokens", 0) for r in b.ccn_census.records(p) if r["message"].get("role") == "assistant")
check("V-CCN-BENCH-DEDUPE-MUTANT", naive == 58 and naive != t["output"], "no-dedupe output=%d differs from %d" % (naive, t["output"]))

q = {"all_of": ["3(\\.0)?", "\\b50\\b"]}
check("V-CCN-BENCH-GRADE-POS", b.grade(q, "DUP 3.0 and MIN_EVENTS = 50"), "all patterns present passes")
check("V-CCN-BENCH-GRADE-NEG", not b.grade(q, "DUP 3.0 only") and not b.grade(q, ""), "a missing pattern or empty answer fails")


def rows(seq, p4, reps=2):
    out = []
    for rep in range(reps):
        for m, c in (("seq", seq[rep]), ("P4", p4[rep])):
            for i in range(4):
                out.append({"mode": m, "repeat": rep + 1, "qid": "Q%d" % i, "cost_usd": c / 4, "cache_write": 1, "cache_read": 1,
                            "fresh_input": 1, "output": 1, "calls": 1, "tool_calls": 1, "wall_s": 10, "passed": True, "rc": 0})
    return out


r = b.analyze(rows([2.0, 2.2], [2.05, 2.15]))
check("V-CCN-BENCH-VERDICT-NEUTRAL", r["verdict"]["P4"] == "NEUTRAL", "CAF=%s noise=%s -> %s" % (r["caf"]["P4"], r["caf_by_repeat"]["P4"]["noise"], r["verdict"]["P4"]))
r = b.analyze(rows([2.0, 2.0], [2.6, 2.62]))
check("V-CCN-BENCH-VERDICT-AMPLIFIED", r["verdict"]["P4"] == "AMPLIFIED", "CAF=%s -> %s" % (r["caf"]["P4"], r["verdict"]["P4"]))
r = b.analyze(rows([2.0, 2.0], [1.5, 1.52]))
check("V-CCN-BENCH-VERDICT-REDUCED", r["verdict"]["P4"] == "REDUCED", "CAF=%s -> %s" % (r["caf"]["P4"], r["verdict"]["P4"]))
r = b.analyze(rows([2.0], [2.0], reps=1))
check("V-CCN-BENCH-VERDICT-ONEREPEAT", str(r["verdict"]["P4"]).startswith("UNJUDGED"), "one repeat gives no noise band -> %s" % r["verdict"]["P4"])
r = b.analyze([x for x in rows([2.0, 2.0], [2.0, 2.0]) if x["mode"] != "seq"])
check("V-CCN-BENCH-NOBASELINE", str(r["verdict"]).startswith("UNJUDGED"), "no seq baseline -> %s" % r["verdict"])

print("CCN_BENCH_PASS=%d/%d" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
