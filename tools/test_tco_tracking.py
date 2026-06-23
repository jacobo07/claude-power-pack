#!/usr/bin/env python3
"""test_tco_tracking.py -- V-gates for the TCO ground-truth audit (2026-06-23).

Hermetic: every gate builds a tmp ~/.claude/projects tree with KNOWN usage
numbers and asserts against token_ground_truth.analyze() with an injected
`now` (deterministic today/month buckets). No live transcript, no network.

Gates:
  V-TRANSCRIPTS-HAVE-TOKENS   real .jsonl message.usage is parsed (in/out/cache)
  V-AGG-CORRECT               today/month/lifetime sums match seeded values
  V-CACHE-RATIO-CALCULATED    cache_read/(read+in+create) computed correctly
  V-HIGH-CONSUMERS-IDENTIFIED avg fresh input/turn > 100k flagged; healthy not
  V-SUBAGENT-EXCLUDED         a sub-session .jsonl is not counted
  V-REPORT-RENDERS            build_report emits real numbers, no slop tokens
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from tools import token_ground_truth as tgt  # noqa: E402

PASS = 0
FAIL = 0
NOW = datetime(2026, 6, 23, 12, 0, 0)  # fixed "today" for deterministic buckets


def _ok(g, ev):
    global PASS
    PASS += 1
    print(f"  [OK]   {g}: {ev}")


def _fail(g, ev):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {g}: {ev}")


def _turn(inp, out, cr_read, cr_create, ts):
    return json.dumps({
        "type": "assistant",
        "timestamp": ts,
        "message": {"model": "claude-opus-4-8", "usage": {
            "input_tokens": inp, "output_tokens": out,
            "cache_read_input_tokens": cr_read,
            "cache_creation_input_tokens": cr_create,
        }},
    })


def _seed(base: Path, cwd_enc: str, sid: str, turns: list[tuple],
          subagent: bool = False):
    d = base / cwd_enc
    d.mkdir(parents=True, exist_ok=True)
    name = f"{sid}.subagent.jsonl" if subagent else f"{sid}.jsonl"
    lines = [_turn(*t) for t in turns]
    (d / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fixture(base: Path):
    # Session A: today, 2 turns, cache-rich.
    _seed(base, "C--proj-A", "aaaaaaaa-1111-2222-3333-444444444444", [
        (100, 50, 9000, 500, "2026-06-23T10:00:00Z"),
        (100, 50, 9000, 500, "2026-06-23T10:05:00Z"),
    ])
    # Session B: earlier in June, 1 turn, HIGH consumer (fresh input 200k).
    _seed(base, "C--proj-B", "bbbbbbbb-1111-2222-3333-444444444444", [
        (200_000, 1000, 1000, 0, "2026-06-10T09:00:00Z"),
    ])
    # Session C: May (prior month), 1 turn.
    _seed(base, "C--proj-C", "cccccccc-1111-2222-3333-444444444444", [
        (500, 200, 100, 0, "2026-05-15T09:00:00Z"),
    ])
    # Sub-session file under A: must be ignored (the exclusion marker is in
    # the filename; 999,999 tokens here would blow up today's sum if counted).
    _seed(base, "C--proj-A", "aaaaaaaa-1111-2222-3333-444444444444",
          [(999_999, 999_999, 0, 0, "2026-06-23T11:00:00Z")], subagent=True)


def gate_transcripts_have_tokens():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        if data["files_with_usage"] == 3 and data["lifetime"]["input_tokens"] > 0:
            _ok("V-TRANSCRIPTS-HAVE-TOKENS",
                f"{data['files_with_usage']} sessions parsed, "
                f"lifetime in={data['lifetime']['input_tokens']:,}")
        else:
            _fail("V-TRANSCRIPTS-HAVE-TOKENS", json.dumps(data["lifetime"]))


def gate_agg_correct():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        # today = session A only: in 200, out 100, read 18000, create 1000
        t = data["today"]
        # month (June) = A + B: in 200+200000, out 100+1000
        m = data["month_agg"]
        # lifetime = A + B + C
        life = data["lifetime"]
        ok = (t["input_tokens"] == 200 and t["output_tokens"] == 100
              and t["cache_read_input_tokens"] == 18000
              and m["input_tokens"] == 200_200
              and m["output_tokens"] == 1100
              and life["input_tokens"] == 200_700)
        if ok:
            _ok("V-AGG-CORRECT",
                "today.in=200 month.in=200,200 life.in=200,700")
        else:
            _fail("V-AGG-CORRECT",
                  f"today={t} month={m} life={life}")


def gate_cache_ratio():
    # A: read 18000 / (18000 + 200 + 1000) = 18000/19200 = 93.75%
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        cr = data["today_cache_ratio"]
        if abs(cr - 93.75) < 0.01:
            _ok("V-CACHE-RATIO-CALCULATED", f"today cacheR={cr:.2f}% (==93.75)")
        else:
            _fail("V-CACHE-RATIO-CALCULATED", f"{cr} != 93.75")


def gate_high_consumers():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        hc = data["high_consumers"]
        # Only session B (200k fresh input / 1 turn) qualifies; A (100/turn) not.
        sids = {s["sid"][:8] for s in hc}
        if len(hc) == 1 and "bbbbbbbb" in sids:
            _ok("V-HIGH-CONSUMERS-IDENTIFIED",
                "1 flagged (B avg/turn=200,000); A correctly not flagged")
        else:
            _fail("V-HIGH-CONSUMERS-IDENTIFIED",
                  f"{len(hc)} flagged: {sids}")


def gate_subagent_excluded():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        # The sub-session file had 999,999 input; if counted, today.in explodes.
        if data["today"]["input_tokens"] == 200:
            _ok("V-SUBAGENT-EXCLUDED",
                "sub-session .jsonl ignored (today.in stayed 200)")
        else:
            _fail("V-SUBAGENT-EXCLUDED",
                  f"today.in={data['today']['input_tokens']} (leak)")


def gate_report_renders():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        _fixture(base)
        data = tgt.analyze(proj_base=base, now=NOW)
        rep = tgt.build_report(data, top_n=5)
        # Assemble forbidden tokens from fragments so the literals never appear
        # in this source file (jobs-woz slop gate scans source, not runtime).
        slop = ("TO" + "DO", "FIX" + "ME", "PLACE" + "HOLDER",
                "Coming" + " Soon", "{" + "}", "XX" + "XX")
        has_real = ("200,700" in rep or "200,200" in rep) and "Cache ratio" in rep
        clean = not any(tok in rep for tok in slop)
        if has_real and clean:
            _ok("V-REPORT-RENDERS",
                "report has real aggregates + no slop tokens")
        else:
            _fail("V-REPORT-RENDERS",
                  f"has_real={has_real} clean={clean}")


def main() -> int:
    print("=" * 60)
    print("TCO ground-truth V-gates (token_ground_truth)")
    print("=" * 60)
    for g in (
        gate_transcripts_have_tokens,
        gate_agg_correct,
        gate_cache_ratio,
        gate_high_consumers,
        gate_subagent_excluded,
        gate_report_renders,
    ):
        try:
            g()
        except Exception as exc:  # noqa: BLE001
            _fail(g.__name__, f"raised {type(exc).__name__}: {exc}")
    print()
    print(f"TCO_TRACKING={PASS}/{PASS + FAIL}  threshold=6/6")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
