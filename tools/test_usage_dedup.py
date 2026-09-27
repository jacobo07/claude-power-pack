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
