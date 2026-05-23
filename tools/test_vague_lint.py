#!/usr/bin/env python3
"""V-VAGUE-1/2 + V-CLEAN-1/2 + V-TIMING gates for the JIT loader's
vague-prompt lint signal (Owner spec 2026-05-23).

Run: `python tools/test_vague_lint.py` from the PP repo root.
Exit 0 = all gates pass. Exit 1 = any gate fails (prints which).
"""
from __future__ import annotations
import sys
import time
import tempfile
from pathlib import Path

# Import the module under test by path (no need to install PP as pkg)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jit_skill_loader import run, _detect_vague_prompt, VAGUE_LINT_MESSAGE

SIGNAL_PREFIX = "[vague-prompt-lint]"


def _ctx(result: dict) -> str:
    return result.get("additionalContext") or ""


def _clean_cwd() -> str:
    """Tmpdir guaranteed free of pyproject/package.json/.specify (per L6
    in session_lessons — otherwise auto-detectors fire and confound)."""
    td = tempfile.mkdtemp(prefix="jit-vague-test-")
    return td


def gate_v_vague_1() -> tuple[bool, str]:
    """V-VAGUE-1: "fix the auth bug" (4 tokens, "the bug") -> signal."""
    cwd = _clean_cwd()
    r = run({"prompt": "fix the auth bug", "cwd": cwd})
    ctx = _ctx(r)
    ok = SIGNAL_PREFIX in ctx
    return ok, f"V-VAGUE-1 ctx_len={len(ctx)} signal={'yes' if ok else 'NO'}"


def gate_v_vague_2() -> tuple[bool, str]:
    """V-VAGUE-2: "hazlo más rápido" (3 tokens, enclitic 'lo') -> signal."""
    cwd = _clean_cwd()
    r = run({"prompt": "hazlo más rápido", "cwd": cwd})
    ctx = _ctx(r)
    ok = SIGNAL_PREFIX in ctx
    return ok, f"V-VAGUE-2 ctx_len={len(ctx)} signal={'yes' if ok else 'NO'}"


def gate_v_clean_1() -> tuple[bool, str]:
    """V-CLEAN-1: concrete file+line -> NO signal."""
    cwd = _clean_cwd()
    p = "fix the null pointer in PlayerManager.java line 42"
    r = run({"prompt": p, "cwd": cwd})
    ctx = _ctx(r)
    ok = SIGNAL_PREFIX not in ctx
    return ok, f"V-CLEAN-1 ctx_len={len(ctx)} signal_absent={'yes' if ok else 'NO'}"


def gate_v_clean_2() -> tuple[bool, str]:
    """V-CLEAN-2: prompt >30 tokens (any content) -> NO signal."""
    cwd = _clean_cwd()
    p = (
        "fix the bug that happens when the user clicks the button and then "
        "the modal opens but it does not close again when they click "
        "outside and also the focus trap stops working after a tab key "
        "press in firefox specifically not chrome"
    )
    assert len(p.split()) >= 30, f"test fixture too short: {len(p.split())}"
    r = run({"prompt": p, "cwd": cwd})
    ctx = _ctx(r)
    ok = SIGNAL_PREFIX not in ctx
    return ok, (
        f"V-CLEAN-2 tokens={len(p.split())} ctx_len={len(ctx)} "
        f"signal_absent={'yes' if ok else 'NO'}"
    )


def gate_v_timing() -> tuple[bool, str]:
    """V-TIMING: 10 runs of V-VAGUE-1 each must be <100ms."""
    cwd = _clean_cwd()
    over_budget: list[float] = []
    durations: list[float] = []
    for _ in range(10):
        t0 = time.perf_counter()
        run({"prompt": "fix the auth bug", "cwd": cwd})
        dt = (time.perf_counter() - t0) * 1000.0
        durations.append(dt)
        if dt >= 100.0:
            over_budget.append(dt)
    p95 = sorted(durations)[int(len(durations) * 0.95) - 1]
    ok = not over_budget
    return ok, (
        f"V-TIMING n=10 max={max(durations):.1f}ms p95={p95:.1f}ms "
        f"over_100ms={len(over_budget)} {'PASS' if ok else 'FAIL'}"
    )


def gate_disable_env() -> tuple[bool, str]:
    """Bonus: CLAUDEPP_VAGUE_LINT_DISABLE=1 short-circuits."""
    import os
    os.environ["CLAUDEPP_VAGUE_LINT_DISABLE"] = "1"
    try:
        cwd = _clean_cwd()
        r = run({"prompt": "fix the auth bug", "cwd": cwd})
        ctx = _ctx(r)
        ok = SIGNAL_PREFIX not in ctx
        return ok, f"DISABLE-ENV signal_absent={'yes' if ok else 'NO'}"
    finally:
        os.environ.pop("CLAUDEPP_VAGUE_LINT_DISABLE", None)


def main() -> int:
    gates = [
        ("V-VAGUE-1", gate_v_vague_1),
        ("V-VAGUE-2", gate_v_vague_2),
        ("V-CLEAN-1", gate_v_clean_1),
        ("V-CLEAN-2", gate_v_clean_2),
        ("V-TIMING",  gate_v_timing),
        ("DISABLE-ENV", gate_disable_env),
    ]
    failed = []
    for name, fn in gates:
        ok, msg = fn()
        print(f"{'PASS' if ok else 'FAIL'}  {msg}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        return 1
    print("\nAll gates PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
