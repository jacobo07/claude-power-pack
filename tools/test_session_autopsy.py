#!/usr/bin/env python3
"""V-AUTOPSY gates for tools/session_autopsy.py (context rent of one session).

Synthetic fixture built here; one read-only positive control on the real
incident transcript reports SKIP (never PASS) when that file is absent.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
passes = fails = skips = 0


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def call(i, ts, cc, cr, out, model="claude-opus-5-5", ttl="1h", lines=1):
    br = {"ephemeral_5m_input_tokens": cc if ttl == "5m" else 0,
          "ephemeral_1h_input_tokens": cc if ttl == "1h" else 0}
    usage = {"input_tokens": 0, "cache_creation_input_tokens": cc,
             "cache_read_input_tokens": cr, "output_tokens": out, "cache_creation": br}
    obj = {"type": "assistant", "timestamp": ts, "requestId": f"r{i}",
           "message": {"id": f"m{i}", "model": model, "usage": usage, "content": []}}
    return [json.dumps(obj)] * lines  # one call may span several lines


# floor 100k at call 1 (all written), growth to 300k, then a 2h idle gap forces a rewrite
FIX = (call(1, "2026-09-27T10:00:00Z", 100_000, 0, 100, lines=3)
       + call(2, "2026-09-27T10:01:00Z", 100_000, 100_000, 100)
       + call(3, "2026-09-27T10:02:00Z", 100_000, 200_000, 100, lines=2)
       + call(4, "2026-09-27T12:30:00Z", 300_000, 0, 100))  # >1h gap: cache expired, full rewrite


def main() -> int:
    sa = _load("session_autopsy")
    prices = {"claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_write_5m": 5.0,
                                  "cache_write_1h": 8.0, "cache_read": 0.2}}
    with tempfile.TemporaryDirectory() as td:
        fp = Path(td) / "s.jsonl"
        fp.write_text("\n".join(FIX) + "\n", encoding="utf-8")
        r = sa.autopsy(fp, prices=prices)

        check("V-AUTOPSY-CALLS-DEDUP", r["calls"] == 4 and r["usage_lines"] == 7,
              f"calls={r['calls']} lines={r['usage_lines']}")
        check("V-AUTOPSY-FLOOR", r["floor_tokens"] == 100_000, f"floor={r['floor_tokens']:,}")
        # resident: 100k, 200k, 300k, 300k -> total 900k; growth above floor 0+100+200+200 = 500k
        check("V-AUTOPSY-RESIDENT", r["resident_total"] == 900_000 and r["resident_max"] == 300_000,
              f"total={r['resident_total']:,} max={r['resident_max']:,}")
        check("V-AUTOPSY-GROWTH", r["growth_above_floor_tokens"] == 500_000,
              f"growth={r['growth_above_floor_tokens']:,}")
        check("V-AUTOPSY-TTL-GAP", r["gaps_over_ttl"] == 1 and r["rewrite_after_gap_tokens"] == 300_000,
              f"gaps={r['gaps_over_ttl']} rewrite={r['rewrite_after_gap_tokens']:,}")
        # cost: writes 600k@8 = 4.80; reads 300k@0.2 = 0.06; output 400@20 = 0.008
        c = r["cost_usd"]
        check("V-AUTOPSY-COST-1H-WRITES", abs(c["cache_write"] - 4.80) < 1e-9, f"write={c['cache_write']}")
        check("V-AUTOPSY-COST-READS-BILLED", abs(c["cache_read"] - 0.06) < 1e-9, f"read={c['cache_read']}")
        check("V-AUTOPSY-COST-NONNEG", all(v >= 0 for v in c.values() if v is not None),
              f"{c}")
        check("V-AUTOPSY-BOUND-LABELLED", r["fresh_epoch_saving_bound"]["kind"] == "UPPER_BOUND",
              f"{r['fresh_epoch_saving_bound']}")

        # an unpriced model is UNKNOWN, never a default rate and never zero
        fp2 = Path(td) / "u.jsonl"
        fp2.write_text("\n".join(call(1, "2026-09-27T10:00:00Z", 10, 10, 10, model="claude-new-9")) + "\n",
                       encoding="utf-8")
        u = sa.autopsy(fp2, prices=prices)
        check("V-AUTOPSY-UNPRICED-UNKNOWN", u["cost_usd"]["total"] is None and u["unpriced_calls"] == 1,
              f"total={u['cost_usd']['total']} unpriced={u['unpriced_calls']}")

        # growth attribution: which content made the session grow (chars, a token ESTIMATE)
        def tu(tid, name, **inp):
            return json.dumps({"type": "assistant", "message": {"id": f"a{tid}", "content": [
                {"type": "tool_use", "id": tid, "name": name, "input": inp}]}})

        def tr(tid, text, side=False):
            return json.dumps({"type": "user", "isSidechain": side, "message": {"content": [
                {"type": "tool_result", "tool_use_id": tid, "content": text}]}})

        G = [json.dumps({"type": "user", "message": {"content": "p" * 10}}),
             tu("t1", "Read", file_path="a.py"), tr("t1", "x" * 100),
             tu("t2", "Read", file_path="a.py"), tr("t2", "x" * 100),        # unchanged re-read
             tu("t2b", "Read", file_path="a.py", offset=50, limit=10), tr("t2b", "x" * 5),  # other page
             tu("t3", "Edit", file_path="a.py"), tr("t3", "ok"),
             tu("t4", "Read", file_path="a.py"), tr("t4", "y" * 100),        # re-read after edit
             tu("t5", "PowerShell", command="ls"), tr("t5", "z" * 40),
             tr("t5", "z" * 40),                                             # duplicated line
             tr("t9", "s" * 999, side=True),                                  # subagent sidechain
             json.dumps({"type": "assistant", "message": {"id": "m9", "content": [
                 {"type": "text", "text": "t" * 7}, {"type": "thinking", "thinking": "k" * 3}]}})]
        fp3 = Path(td) / "g.jsonl"
        fp3.write_text("\n".join(G) + "\n", encoding="utf-8")
        g = sa.growth_sources(fp3)
        check("V-AUTOPSY-GROWTH-KINDS",
              g["by_kind"] == {"tool_result": 347, "user_text": 10, "assistant_text": 7, "thinking": 3},
              f"{g['by_kind']}")
        check("V-AUTOPSY-GROWTH-BY-TOOL",
              g["by_tool"] == {"Read": 305, "PowerShell": 40, "Edit": 2}, f"{g['by_tool']}")
        rd = g["read"]
        check("V-AUTOPSY-REREAD-UNCHANGED",
              rd["calls"] == 4 and rd["reread_unchanged"] == 1 and rd["reread_unchanged_chars"] == 100
              and rd["reread_after_edit"] == 1,
              f"{rd}")
        check("V-AUTOPSY-GROWTH-LABELLED", g["unit"] == "chars (token ESTIMATE ~chars/4)", g["unit"])

    real = (Path.home() / ".claude" / "projects"
            / "C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects"
            / "04b41ed7-58a3-450c-b5b1-3e8732f5dbc4.jsonl")
    if real.is_file():
        r = sa.autopsy(real)
        check("V-AUTOPSY-REAL-INCIDENT",
              r["calls"] == 326 and r["floor_tokens"] > 150_000 and r["cost_usd"]["total"] is not None,
              f"calls={r['calls']} floor={r['floor_tokens']:,} usd={r['cost_usd']['total']}")
    else:
        global skips
        skips += 1
        print("  [SKIP] V-AUTOPSY-REAL-INCIDENT: incident transcript not on this host")

    print(f"AUTOPSY_PASS={passes}/{passes + fails}  skipped={skips}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
