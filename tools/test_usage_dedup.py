#!/usr/bin/env python3
"""V-DEDUP gates: every transcript usage reader counts one API call once.

Claude Code writes one transcript line per content block and repeats the
call's usage verbatim on each. Measured 2026-09-27 on KobiiSports session
04b41ed7: 814 usage lines = 327 calls; summing lines reported 326 M cache
reads for a session that had 132 M. tools/tis_observed.py is the reference
reader; these gates hold the other readers to it.

Synthetic fixtures are built here. One positive control reads the real
incident transcript when present and reports SKIP (never PASS) when absent.
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


def skip(gate, why):
    global skips
    skips += 1
    print(f"  [SKIP] {gate}: {why}")


def line(mid, rid, cc, cr, out, block, model="claude-opus-5-5"):
    usage = {"input_tokens": 1, "cache_creation_input_tokens": cc,
             "cache_read_input_tokens": cr, "output_tokens": out}
    msg = {"model": model, "usage": usage, "content": [block]}
    if mid is not None:
        msg["id"] = mid
    obj = {"type": "assistant", "timestamp": "2026-09-27T10:00:00Z", "message": msg}
    if rid is not None:
        obj["requestId"] = rid
    return json.dumps(obj)


def tool(name, path=None):
    blk = {"type": "tool_use", "name": name, "input": {}}
    if path:
        blk["input"]["file_path"] = path
    return blk


FIXTURE = [
    json.dumps({"type": "user", "message": {"content": "go"}}),
    # call m1 = one API response written as three content-block lines
    line("m1", "r1", 1000, 100_000, 50, {"type": "thinking", "thinking": ""}),
    line("m1", "r1", 1000, 100_000, 50, tool("Read", "a.py")),
    line("m1", "r1", 1000, 100_000, 50, tool("Grep")),
    # call m2 = one line
    line("m2", "r2", 0, 101_000, 20, {"type": "text", "text": "done"}),
    # a line with no identity at all counts once, as-is (tis_observed contract)
    line(None, None, 0, 7, 1, {"type": "text", "text": "x"}),
]
EXPECT_CALLS = 3
EXPECT_CR = 100_000 + 101_000 + 7
EXPECT_CC = 1000


def main() -> int:
    tis = _load("tis_observed")
    gt = _load("token_ground_truth")
    corpus = _load("token_corpus_audit")

    with tempfile.TemporaryDirectory() as td:
        fp = Path(td) / "sess.jsonl"
        fp.write_text("\n".join(FIXTURE) + "\n", encoding="utf-8")

        ref = tis.read_session(fp, include_subagents=False)
        check("V-DEDUP-REFERENCE", ref.calls == EXPECT_CALLS and ref.cache_read_tokens == EXPECT_CR,
              f"tis_observed calls={ref.calls} cr={ref.cache_read_tokens}")

        g = gt.parse_session(fp)
        check("V-DEDUP-GT-CALLS", g["turns"] == EXPECT_CALLS, f"turns={g['turns']} want {EXPECT_CALLS}")
        check("V-DEDUP-GT-CACHE-READ", g["agg"]["cache_read_input_tokens"] == EXPECT_CR,
              f"cr={g['agg']['cache_read_input_tokens']:,} want {EXPECT_CR:,}")
        check("V-DEDUP-GT-CACHE-WRITE", g["agg"]["cache_creation_input_tokens"] == EXPECT_CC,
              f"cc={g['agg']['cache_creation_input_tokens']:,} want {EXPECT_CC:,}")

        c = corpus.parse_turns(fp)
        crd = sum(t["cache_read_input_tokens"] for t in c["turns"])
        check("V-DEDUP-CORPUS-CALLS", c["n_turns"] == EXPECT_CALLS, f"n_turns={c['n_turns']}")
        check("V-DEDUP-CORPUS-CACHE-READ", crd == EXPECT_CR, f"cr={crd:,} want {EXPECT_CR:,}")
        m1 = c["turns"][0]
        # content signals live on sibling lines of ONE call and must be merged, not dropped
        check("V-DEDUP-CORPUS-MERGES-TOOLS", sorted(m1["tool_names"]) == ["Grep", "Read"],
              f"m1 tool_names={m1['tool_names']}")

    # Streaming: one call's lines do NOT always repeat usage verbatim. output_tokens
    # grows across them (measured 2026-10-02: 5,825 of 23,933 calls; first-copy
    # output 12.7 M vs last-copy 19.1 M). Last copy wins, so every reader must land
    # on the final count. The weekly-burn reader (window_output) is held here too:
    # it summed every line and skipped subagent transcripts.
    from datetime import datetime, timezone
    now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
    stream = [line("s1", "q1", 500, 9_000, 3, {"type": "thinking", "thinking": ""}),
              line("s1", "q1", 500, 9_000, 400, {"type": "text", "text": "ok"})]
    sub = [line("a1", "qa", 0, 5_000, 70, {"type": "text", "text": "sub"})]
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "proj"
        (proj / "sess" / "subagents").mkdir(parents=True)
        (proj / "sess.jsonl").write_text("\n".join(stream) + "\n", encoding="utf-8")
        (proj / "sess" / "subagents" / "agent-a1.jsonl").write_text("\n".join(sub) + "\n", encoding="utf-8")
        fp = proj / "sess.jsonl"
        check("V-DEDUP-STREAM-REFERENCE", tis.read_session(fp, include_subagents=False).output_tokens == 400,
              f"tis_observed out={tis.read_session(fp, include_subagents=False).output_tokens} want 400")
        check("V-DEDUP-STREAM-GT", gt.parse_session(fp)["agg"]["output_tokens"] == 400,
              f"ground_truth out={gt.parse_session(fp)['agg']['output_tokens']} want 400")
        check("V-DEDUP-STREAM-CORPUS", corpus.parse_turns(fp)["turns"][0]["output_tokens"] == 400,
              f"corpus out={corpus.parse_turns(fp)['turns'][0]['output_tokens']} want 400")
        w = gt.window_output(24, proj_base=td, now=now)
        check("V-DEDUP-WINDOW-OUTPUT", w == 400 + 70,
              f"window_output={w} want {400 + 70} (last copy of s1 + subagent a1)")
        u = gt.window_usage(24, proj_base=td, now=now)
        check("V-DEDUP-WINDOW-USAGE",
              u is not None and u["calls"] == 2 and u["cache_read_input_tokens"] == 14_000
              and u["subagent_calls"] == 1 and u["output_tokens"] == 470,
              f"window_usage={u}")
        # The same session file can exist under two project dirs (measured
        # 2026-10-02: 3,044 calls in two files, +12.7 % if summed per file).
        # An estate reader dedupes across files, not only within one.
        (Path(td) / "proj2").mkdir()
        (Path(td) / "proj2" / "sess.jsonl").write_text("\n".join(stream) + "\n", encoding="utf-8")
        u2 = gt.window_usage(24, proj_base=td, now=now)
        check("V-DEDUP-WINDOW-CROSS-FILE", u2 is not None and u2["calls"] == 2 and u2["output_tokens"] == 470,
              f"session copied into a second project dir -> calls={u2 and u2['calls']} want 2")
        early = gt.window_usage(1, proj_base=td, now=now)
        check("V-DEDUP-WINDOW-EMPTY-IS-NONE", early is None,
              f"window with no call -> {early} (unmeasured is None, never 0)")

    # Positive control on the real incident, read-only. Its value is that a
    # synthetic fixture cannot carry a shape the author did not imagine.
    real = (Path.home() / ".claude" / "projects"
            / "C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects"
            / "04b41ed7-58a3-450c-b5b1-3e8732f5dbc4.jsonl")
    if real.is_file():
        r = tis.read_session(real, include_subagents=False)
        g = gt.parse_session(real)
        check("V-DEDUP-REAL-PARITY",
              g["turns"] == r.calls and g["agg"]["cache_read_input_tokens"] == r.cache_read_tokens,
              f"ground_truth turns={g['turns']} cr={g['agg']['cache_read_input_tokens']:,} | "
              f"tis_observed calls={r.calls} cr={r.cache_read_tokens:,} (lines={r.usage_lines})")
    else:
        skip("V-DEDUP-REAL-PARITY", "incident transcript not on this host")

    print(f"DEDUP_PASS={passes}/{passes + fails}  skipped={skips}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
