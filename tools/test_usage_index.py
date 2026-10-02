#!/usr/bin/env python3
"""V-UIX-* gates for tools/usage_index.py (C1, cognitive-control-plane-2026-10-02).

Hermetic: every fixture lives in a temp dir; no model call, no real transcript.
Each refusal is paired with the control in which the same instrument fires."""
from __future__ import annotations

import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import tis_observed as tis  # noqa: E402
import token_ground_truth as tgt  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
PRICES = {"claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_write_5m": 5.0,
                              "cache_write_1h": 8.0, "cache_read": 0.2},
          "claude-sonnet-5": {"input": 2.0, "output": 10.0, "cache_write_5m": 2.5,
                              "cache_write_1h": 4.0, "cache_read": 0.2}}


def ok(gate, cond, ev):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {gate}: {ev}")
    else:
        FAIL += 1
        print(f"  FAIL {gate}: {ev}")


def ts(h):  # hours after 2026-10-01T00:00Z
    return datetime.fromtimestamp(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
                                  + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def line(mid, req, h, out, cr=1000, model="claude-opus-5-5", cw=0, cc=None, ep=None):
    u = {"input_tokens": 1, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw,
         "output_tokens": out}
    if cc:
        u["cache_creation"] = cc
    o = {"type": "assistant", "timestamp": ts(h), "requestId": req,
         "message": {"id": mid, "model": model, "usage": u}}
    if ep:
        o["entrypoint"] = ep
    return json.dumps(o) + "\n"


def build(root: Path):
    p1 = root / "C--proj-a"
    (p1 / "s1" / "subagents").mkdir(parents=True)
    main = p1 / "s1.jsonl"
    main.write_text(
        json.dumps({"type": "user", "entrypoint": "cli", "timestamp": ts(0)}) + "\n"
        + line("m1", "r1", 1, 5) + line("m1", "r1", 1, 50)          # streamed: 5 then 50
        + line("m2", "r2", 2, 10, cw=300, cc={"ephemeral_5m_input_tokens": 100,
                                              "ephemeral_1h_input_tokens": 200})
        + json.dumps({"timestamp": ts(2), "message": {"model": "<synthetic>",
                                                      "usage": {"output_tokens": 0}}}) + "\n"
        + json.dumps({"timestamp": ts(3), "message": {"model": "claude-opus-5-5",
                                                      "usage": {"output_tokens": 7}}}) + "\n",
        encoding="utf-8")
    sub = p1 / "s1" / "subagents" / "agent-x.jsonl"
    sub.write_text(line("m3", "r3", 2.5, 20, model="claude-sonnet-5-5"), encoding="utf-8")
    p2 = root / "C--proj-b"       # the same session file under a second project dir
    p2.mkdir()
    (p2 / "s1.jsonl").write_text(line("m1", "r1", 1, 50), encoding="utf-8")
    return main, sub


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "projects"
        main_fp, sub_fp = build(root)
        db = Path(td) / "ix.sqlite"
        con = ux.connect(db)

        # V-UIX-PARSE-AGREES: the incremental reader and the reference reader
        # return the same identity calls with the same final usage.
        full, _, _, _ = tis._calls_in(main_fp)
        inc, end, ep = tis.calls_from(main_fp, 0)
        ident = lambda cs: {c["key"]: c["usage"].get("output_tokens")
                            for c in cs if c["key"][0] not in ("line", "off")}
        ok("V-UIX-PARSE-AGREES", ident(full) == ident(inc) and ident(inc) == {("m1", "r1"): 50, ("m2", "r2"): 10},
           f"reference={ident(full)} incremental={ident(inc)} entrypoint={ep}")
        ok("V-UIX-IDLESS-KEPT", len(full) == len(inc) == 3,
           f"identity-less call counted once by both readers ({len(full)} vs {len(inc)})")

        # V-UIX-PARTIAL-LINE: an unterminated trailing line is not consumed.
        with open(main_fp, "a", encoding="utf-8") as fh:
            fh.write(line("m4", "r4", 4, 9).rstrip("\n"))
        c2, end2, _ = tis.calls_from(main_fp, end)
        ok("V-UIX-PARTIAL-LINE", c2 == [] and end2 == end,
           f"half-written line left for the next pass (offset {end2} == {end})")
        with open(main_fp, "a", encoding="utf-8") as fh:
            fh.write("\n")
        c3, end3, _ = tis.calls_from(main_fp, end)
        ok("V-UIX-PARTIAL-LINE-CONTROL", [c["key"] for c in c3] == [("m4", "r4")] and end3 > end,
           "the same line is read once it is complete")

        # Index + dedup across files and streaming.
        r = ux.refresh(con, root, deadline_s=30)
        w = ux.window(con, ux._epoch(ts(0)), ux._epoch(ts(10)), PRICES)
        ok("V-UIX-REFRESH-OK", r["status"] == "OK" and r["files_read"] == 3, json.dumps(r))
        ok("V-UIX-DEDUP", w["calls"] == 5 and w["output"] == 50 + 10 + 7 + 9 + 20,
           f"calls={w['calls']} output={w['output']} (m1 once across 2 dirs, stream max 50)")
        ok("V-UIX-SUBAGENT-COUNTED", w["subagent_calls"] == 1, f"subagent_calls={w['subagent_calls']}")

        # Two paths: the index window equals token_ground_truth.window_usage.
        now = datetime.fromtimestamp(ux._epoch(ts(10)), timezone.utc)
        g = tgt.window_usage(10, root, now)
        ok("V-UIX-EQ-GROUND-TRUTH",
           g is not None and (g["calls"], g["output_tokens"], g["cache_read_input_tokens"],
                              g["subagent_calls"]) == (w["calls"], w["output"], w["cache_read"],
                                                       w["subagent_calls"]),
           f"ground_truth={g and (g['calls'], g['output_tokens'], g['cache_read_input_tokens'])} "
           f"index={(w['calls'], w['output'], w['cache_read'])}")

        # Pricing: TTL split used; family fallback labelled; unknown model never priced as zero.
        m2_usd = (1 * 4 + 100 * 5 + 200 * 8 + 1000 * 0.2 + 10 * 20) / 1e6
        w2 = ux.window(con, ux._epoch(ts(1.5)), ux._epoch(ts(2.2)), PRICES)
        ok("V-UIX-PRICE-SPLIT", abs(w2["usd"] - m2_usd) < 1e-12, f"usd={w2['usd']:.9f} expected={m2_usd:.9f}")
        ok("V-UIX-PRICE-FAMILY", w["fallbacks"].get("claude-sonnet-5-5") == "family:claude-sonnet-5",
           f"fallbacks={w['fallbacks']}")
        w3 = ux.window(con, ux._epoch(ts(0)), ux._epoch(ts(10)), {"claude-opus-5-5": PRICES["claude-opus-5-5"]})
        ok("V-UIX-UNPRICED-TYPED", w3["unpriced_calls"] == 1, f"unpriced_calls={w3['unpriced_calls']}")

        # Incremental: an appended streamed copy updates in place, count unchanged.
        with open(main_fp, "a", encoding="utf-8") as fh:
            fh.write(line("m4", "r4", 4, 99))
        r2 = ux.refresh(con, root, deadline_s=30)
        w4 = ux.window(con, ux._epoch(ts(0)), ux._epoch(ts(10)), PRICES)
        ok("V-UIX-INCREMENTAL", r2["files_read"] == 1 and w4["calls"] == 5 and w4["output"] == w["output"] + 90,
           f"files_read={r2['files_read']} calls={w4['calls']} output={w4['output']}")

        # Deadline: an exhausted budget is PARTIAL and the alarm says MONITOR_FAILURE;
        # control: a completed refresh does not.
        with open(sub_fp, "a", encoding="utf-8") as fh:
            fh.write(line("m5", "r5", 5, 1))
        r3 = ux.refresh(con, root, deadline_s=0)
        a_bad = ux.assess(con, time.time(), allowance_usd=1.0, anchor=ux._epoch(ts(-24)),
                          prices=PRICES, refresh_status=dict(r3, at=time.time()))
        ok("V-UIX-DEADLINE-TYPED", r3["status"] == "PARTIAL" and r3["pending"] == 1
           and a_bad["state"] == ux.MONITOR_FAILURE, f"refresh={r3['status']} assess={a_bad['state']}")
        r4 = ux.refresh(con, root, deadline_s=30)
        a_ok = ux.assess(con, time.time(), allowance_usd=None, anchor=ux._epoch(ts(-24)),
                         prices=PRICES, refresh_status=dict(r4, at=time.time()))
        ok("V-UIX-DEADLINE-CONTROL", r4["status"] == "OK" and a_ok["state"] != ux.MONITOR_FAILURE,
           f"refresh={r4['status']} assess={a_ok['state']}")
        a_stale = ux.assess(con, time.time(), allowance_usd=None, anchor=ux._epoch(ts(-24)),
                            prices=PRICES, refresh_status={"status": "OK", "at": time.time() - 3 * 86400})
        ok("V-UIX-STALE-TYPED", a_stale["state"] == ux.MONITOR_FAILURE, f"{a_stale['reasons']}")
        ok("V-UIX-NO-CALIBRATION-UNKNOWN", a_ok["estimated_pct"] is None
           and any("UNKNOWN" in r for r in a_ok["reasons"]), f"{a_ok['reasons']}")

        # States: the same week of usage judged against shrinking allowances walks
        # NORMAL -> ELEVATED -> CONSTRAINED -> CRITICAL (each a separate branch).
        at = ux._epoch(ts(5.5))
        anchor = ux._epoch(ts(-24))
        okst = {"status": "OK", "at": at}
        wk = ux.window(con, anchor, at, PRICES)["usd"]
        seen = {}
        # All fixture usage falls in the last 6 h, so rate = wk/6 per hour and
        # hours-to-exhaust = (k-1)*6 for an allowance of k*wk (138 h to reset):
        # k=1000 projected 2 % -> NORMAL; k=10 projected 240 %, 54 h left -> ELEVATED;
        # k=4 -> 18 h left -> CONSTRAINED; k=1.1 -> 91 % used -> CRITICAL.
        for name, allowance in (("NORMAL", wk * 1000), ("ELEVATED", wk * 10),
                                ("CONSTRAINED", wk * 4), ("CRITICAL", wk * 1.1)):
            seen[name] = ux.assess(con, at, allowance_usd=allowance, anchor=anchor,
                                   prices=PRICES, refresh_status=okst)["state"]
        ok("V-UIX-STATES", seen == {k: k for k in seen}, json.dumps(seen))
        line_n = ux.advisory_line({"state": "NORMAL", "reasons": []})
        line_c = ux.advisory_line(ux.assess(con, at, allowance_usd=wk * 1.1, anchor=anchor,
                                            prices=PRICES, refresh_status=okst))
        ok("V-UIX-ADVISORY", line_n is None and line_c and "CRITICAL" in line_c, f"{line_c}")

        # Holdout reads only 'calibration' readings to fit (G6): a holdout reading
        # cannot move the allowance.
        cfg = Path(td) / "readings.json"
        cfg.write_text(json.dumps({"reset_anchor": ts(-24), "readings": [
            {"at": ts(2.2), "fraction": 0.5, "use": "calibration"},
            {"at": ts(5.5), "fraction": 0.99, "use": "holdout"}]}), encoding="utf-8")
        orig_file, orig_prices = ux.METER_FILE, ux.load_prices
        ux.METER_FILE, ux.load_prices = cfg, (lambda: PRICES)
        try:
            ux.load_readings.__defaults__ = (cfg,)
            h = ux.holdout(con)
            expect = ux.window(con, anchor, ux._epoch(ts(2.2)), PRICES)["usd"] / 0.5
            ok("V-UIX-HOLDOUT-FROZEN", abs(h["allowance_usd_est"] - round(expect, 2)) < 0.01
               and h["results"][0]["owner_pct"] == 99.0,
               f"allowance={h['allowance_usd_est']} from the calibration reading only")
        finally:
            ux.METER_FILE, ux.load_prices = orig_file, orig_prices
            ux.load_readings.__defaults__ = (orig_file,)
            con.close()

    # Wiring: cost_gate (the launch-advisory path) carries the estate state.
    from modules.wrapper import cost_gate as cg
    healthy = dict(burn_fn=lambda **k: None, assess_fn=lambda c, s: {"state": "HEALTHY"})
    crit = cg.cost_gate(r"C:\x", estate_fn=lambda: {"state": "CRITICAL", "estimated_pct": 91.0,
                                                    "reasons": ["r"], "rate_6h": {}}, **healthy)
    norm = cg.cost_gate(r"C:\x", estate_fn=lambda: {"state": "NORMAL", "reasons": []}, **healthy)

    def boom():
        raise RuntimeError("index locked")
    loud = cg.cost_gate(r"C:\x", estate_fn=boom, **healthy)
    ok("V-UIX-COSTGATE-WIRED", any("CRITICAL" in ln for ln in crit.lines) and norm.lines == [],
       f"critical={crit.lines} normal={norm.lines}")
    ok("V-UIX-COSTGATE-FAILURE-LOUD", any("FAILED" in ln and "UNKNOWN" in ln for ln in loud.lines),
       f"{loud.lines}")
    import inspect
    src = inspect.getsource(cg.cost_gate)
    ok("V-UIX-OLD-ALARM-UNWIRED", "weekly_burn(" not in src, "cost_gate no longer calls weekly_burn")

    total = PASS + FAIL
    print(f"USAGE_INDEX_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
