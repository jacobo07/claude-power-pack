#!/usr/bin/env python3
"""M4 -- CEPS edge-case test suite (S+++ coverage).

Six V-gates beyond the closed-loop / full-cycle baseline:

  V-NIT1-MAXCHARS       prevention_rule output <= 300 chars
  V-NIT3-IDEMPOTENT     from_verify_fail dedup on re-run
  V-EDGE-LONG-ROOT      600-char root_cause accepted; 601 rejected
  V-EDGE-INVALID-CAT    invalid category -> None (fail-open)
  V-EDGE-FTS-PUNCT      propagate survives quotes/punct in prompt
  V-EDGE-LONG-PROMPT    LT regex fires on >500-token prompt

All paths isolated to a tmpdir; production CEPS state never mutated.
Exit 0 = all PASS. Exit 1 = any FAIL.
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import ceps  # noqa: E402
import jit_skill_loader as jit  # noqa: E402


def _isolate(tmp: Path) -> None:
    ceps.EVENTS_PATH = tmp / "events.jsonl"
    ceps.DB_PATH = tmp / "patterns.db"
    ceps.LESSONS_PATH = tmp / "session_lessons.md"
    ceps.UKDL_PATH = tmp / "ukdl.md"
    ceps.DRAFTS_DIR = tmp / "drafts"


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def v_nit1_maxchars(tmp: Path) -> bool:
    """The schema declares max_chars=300 on prevention_rule. Verify the
    rendered rule never exceeds that even when the subsystem identifier
    is unusually long."""
    long_sub = "x" * 400
    ev = ceps.record_error(
        category="regression",
        subsystem=long_sub,
        root_cause="long-subsystem regression test for M1 NIT cap",
    )
    if ev is None:
        return _step("V-NIT1-MAXCHARS", False, "record_error returned None")
    rule_len = len(ev["prevention_rule"])
    ok = rule_len <= 300
    return _step("V-NIT1-MAXCHARS", ok,
                 f"len={rule_len} (cap=300, sub={len(long_sub)})")


def v_nit3_idempotent(tmp: Path) -> bool:
    """Re-running from_verify_fail on the same stdout must NOT duplicate
    events.jsonl rows. Counts DELTA (not absolute) because earlier
    V-tests in this file may have seeded other events first."""
    stdout = (
        "  [FAIL] paths+secrets          rc=1     0.22s  WinError 2\n"
        "  [FAIL] rtk-fusion             rc=1     0.92s  no positive\n"
        "  [FAIL] drift-report           rc=1     0.15s  loose-ahead 2\n"
    )
    pre = 0
    if ceps.EVENTS_PATH.is_file():
        pre = len([l for l in
                   ceps.EVENTS_PATH.read_text(encoding="utf-8").splitlines()
                   if l.strip()])
    out1 = ceps.from_verify_fail(stdout)
    out2 = ceps.from_verify_fail(stdout)  # re-run -- should add zero
    post = len([l for l in
                ceps.EVENTS_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()])
    delta = post - pre
    ok = (len(out1) == 3 and len(out2) == 0 and delta == 3)
    return _step("V-NIT3-IDEMPOTENT", ok,
                 f"run1={len(out1)} run2={len(out2)} delta_jsonl={delta}")


def v_edge_long_root(tmp: Path) -> bool:
    """600-char root_cause accepted (boundary); 601 rejected."""
    rc_600 = "x" * 600
    rc_601 = "x" * 601
    ev1 = ceps.record_error(
        category="tooling", subsystem="boundary", root_cause=rc_600)
    ev2 = ceps.record_error(
        category="tooling", subsystem="boundary", root_cause=rc_601)
    ok = (ev1 is not None) and (ev2 is None)
    return _step("V-EDGE-LONG-ROOT", ok,
                 f"600chars={'ok' if ev1 else 'rejected'} "
                 f"601chars={'rejected' if ev2 is None else 'accepted'}")


def v_edge_invalid_cat(tmp: Path) -> bool:
    """Invalid category -> None (fail-open, never raises)."""
    ev = ceps.record_error(
        category="not-a-real-category",
        subsystem="x", root_cause="invalid category test")
    ok = ev is None
    return _step("V-EDGE-INVALID-CAT", ok,
                 f"ret={'None' if ev is None else 'event'}")


def v_edge_fts_punct(tmp: Path) -> bool:
    """propagate with prompt full of FTS5-reserved tokens / punctuation
    must not crash; returns [] or relevant patterns."""
    # Seed one event so the DB exists.
    ceps.record_error(
        category="tooling", subsystem="fts-punct",
        root_cause="quotes test punctuation injection FTS5 reserved AND OR NOT")
    crashy = '"AND" OR (NOT * ?:;) {curly} [brackets] -minus +plus'
    try:
        lines = ceps.propagate(crashy, top_k=3)
        ok = isinstance(lines, list)
    except Exception as exc:
        return _step("V-EDGE-FTS-PUNCT", False, f"raised: {type(exc).__name__}")
    return _step("V-EDGE-FTS-PUNCT", ok,
                 f"hits={len(lines)} (no crash)")


def v_edge_long_prompt() -> bool:
    """LT regex fires even when the prompt is 500+ tokens long. Uses the
    real JIT detector to confirm the trigger is not length-gated."""
    base = "I'm stuck on the rendering pipeline and need lateral thinking. "
    long_prompt = base + ("filler context word " * 250)  # ~1250 tokens
    card = jit._detect_lateral_thinking_trigger(
        long_prompt, arch_block=None, vague_block=None)
    ok = card is not None and "lateral-thinking-skill" in card
    return _step("V-EDGE-LONG-PROMPT", ok,
                 f"prompt_words={len(long_prompt.split())} "
                 f"card={'fired' if card else 'silent'}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ceps-edge-"))
    _isolate(tmp)
    print(f"[isolate] tmp={tmp}")

    results = []
    results.append(v_nit1_maxchars(tmp))
    results.append(v_nit3_idempotent(tmp))
    results.append(v_edge_long_root(tmp))
    results.append(v_edge_invalid_cat(tmp))
    results.append(v_edge_fts_punct(tmp))
    results.append(v_edge_long_prompt())  # no tmp -- pure regex test

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nEDGE_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
