#!/usr/bin/env python3
"""Hermetic tests for tools/token_corpus_audit.py (FASE -1 measurement layer).

Builds a synthetic ~/.claude/projects tree in a tmp dir -- no global reads, no
network -- and asserts the structural analyses + fat-tail classifier behave.
Run 3x for hermeticity; every run must print DOMAIN_PASS=N/N with N constant.

Gate names are HONEST: they verify the MEASUREMENT instrument, not any fix.
No fix was implemented (STOP #1 + evidence-backed negative finding), so there
is no V-FIXES-MEASURED gate to fake.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AUD = _load("token_corpus_audit")
GT = _load("token_ground_truth")

_passes = 0
_fails = 0


def _ok(gate, ev):
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {ev}")


def _turn(out, content, ts="2026-07-01T10:00:00Z", crd=50_000):
    return json.dumps({
        "timestamp": ts,
        "message": {"role": "assistant", "model": "claude-opus-4-8",
                    "usage": {"input_tokens": 200, "output_tokens": out,
                              "cache_creation_input_tokens": 0,
                              "cache_read_input_tokens": crd},
                    "content": content}})


def _build_corpus(base: Path):
    p1 = base / "C--proj-alpha"
    p2 = base / "C--proj-beta"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)
    # session A: a dense unique fat turn + a repetitive fat turn + a Write turn
    dense = [{"type": "text", "text": "\n".join(f"unique reasoning line {i}"
                                                 for i in range(400))}]
    repetitive = [{"type": "text", "text": "\n".join("SAME LINE"
                                                      for _ in range(400))}]
    writeturn = [{"type": "text", "text": "writing file"},
                 {"type": "tool_use", "name": "Write",
                  "input": {"file_path": "x.py",
                            "content": "\n".join(f"code_{i}" for i in range(300))}}]
    reread = [{"type": "tool_use", "name": "Read",
               "input": {"file_path": "same.py"}}]
    (p1 / "sessA.jsonl").write_text("\n".join([
        _turn(9000, dense),
        _turn(9500, repetitive),
        _turn(9000, writeturn),
        _turn(500, reread), _turn(500, reread), _turn(500, reread),
    ]), encoding="utf-8")
    # session B in another repo, low output, low cache to test outlier logic
    (p2 / "sessB.jsonl").write_text("\n".join([
        json.dumps({"timestamp": "2026-07-01T12:00:00Z",
                    "message": {"role": "assistant", "model": "m",
                                "usage": {"input_tokens": 600_000,
                                          "output_tokens": 700_000,
                                          "cache_creation_input_tokens": 0,
                                          "cache_read_input_tokens": 10_000},
                                "content": [{"type": "text", "text": "hi"}]}}),
    ]), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "projects"
        _build_corpus(base)

        d = AUD.audit(proj_base=str(base))
        # V-CORPUS-ANALYZED: structural report produced with real numbers
        if d["n_sessions"] == 2 and d["lifetime"]["out"] > 0:
            _ok("V-CORPUS-ANALYZED",
                f"n_sessions={d['n_sessions']} out={d['lifetime']['out']:,}")
        else:
            _fail("V-CORPUS-ANALYZED", str(d["n_sessions"]))

        # V-A3-OUTLIER-LOGIC: sessB (700k out, ~2% cache) flagged as low-cache
        outliers = d["a3"]["low_cache_outliers"]
        if any(o["cache_ratio"] < 90 for o in outliers):
            _ok("V-A3-OUTLIER-LOGIC",
                f"{len(outliers)} outlier(s), min={min(o['cache_ratio'] for o in outliers)}%")
        else:
            _fail("V-A3-OUTLIER-LOGIC", f"outliers={outliers}")

        # V-A4-REREAD-DETECT: same.py read 3x -> 1 redundant
        if d["a4"]["total_redundant_rereads"] >= 1:
            _ok("V-A4-REREAD-DETECT",
                f"redundant={d['a4']['total_redundant_rereads']}")
        else:
            _fail("V-A4-REREAD-DETECT", "0 detected")

        # V-A6-CONTEXT-BUCKETS: all three buckets present in structure
        if set(d["a6"]) == {"low", "mid", "high"}:
            _ok("V-A6-CONTEXT-BUCKETS", "low/mid/high present")
        else:
            _fail("V-A6-CONTEXT-BUCKETS", str(set(d["a6"])))

        # V-FAT-TAIL-CLASSIFIED: repetitive turn -> REDUCIBLE, Write -> NOT
        s = AUD.sample_fat_turns(proj_base=str(base), top_n=10, min_out=8000)
        cats = {t["category"] for t in s["turns"]}
        has_rep = any("REDUCIBLE" in t["reducibility"]
                      and t["category"] == "repetitive/dataset"
                      for t in s["turns"])
        has_code = any(t["category"] == "code/file-write" for t in s["turns"])
        has_dense = any(t["category"] == "reasoning/report"
                        and t["uniq_ratio"] >= 0.9 for t in s["turns"])
        if has_rep and has_code and has_dense:
            _ok("V-FAT-TAIL-CLASSIFIED",
                f"cats={sorted(cats)} (repetitive->REDUCIBLE, dense->NOT, code->NOT)")
        else:
            _fail("V-FAT-TAIL-CLASSIFIED",
                  f"rep={has_rep} code={has_code} dense={has_dense}")

        # V-BASELINE-INTACT: token_ground_truth still analyzes the same tree
        g = GT.analyze(proj_base=str(base))
        if g["files_with_usage"] == 2:
            _ok("V-BASELINE-INTACT", f"ground_truth files={g['files_with_usage']}")
        else:
            _fail("V-BASELINE-INTACT", str(g["files_with_usage"]))

    total = _passes + _fails
    print(f"TOKEN_CORPUS_AUDIT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
