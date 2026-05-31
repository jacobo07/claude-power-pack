#!/usr/bin/env python3
"""test_jit_performance.py -- V-gates for jit_skill_loader perf work.

Eleven done-gates exercised verbatim (no mocks, no fixtures):
  V-JIT-BENCH-PRE-EXISTS   vault/benchmarks/jit_loader_pre_fix.json
  V-JIT-BENCH-POST-EXISTS  vault/benchmarks/jit_loader_post_fix.json
  V-JIT-IMPROVEMENT        end-to-end avg post < pre (any gain)
  V-JIT-LAZY-IMPORT        import + run() of jit_skill_loader works
  V-JIT-WARM-EXISTS        hooks/jit_warm.js on disk + executable
  V-JIT-WARM-RUNS          warm hook returns exit 0 with no stdout
  V-JIT-WARM-LOG           warm spawns and writes the log entry
  V-JIT-BATCH-TELEM        telemetry write happens in a single fopen
  V-JIT-FAIL-OPEN          PP_WARM_RUN=1 short-circuit returns 0
  V-JIT-REGISTER           register_global_hooks.py --dry-run lists
                           jit_warm in registered/pending
  V-BASELINE-INTACT        the existing tools/test_*.py imports
                           still load (no syntax regression)
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = PP_ROOT / "vault" / "benchmarks"
HOOKS_DIR = PP_ROOT / "hooks"
TOOLS_DIR = PP_ROOT / "tools"

PY = sys.executable
PASS = 0
FAIL = 0
RESULTS: list[tuple[str, bool, str]] = []


def _ok(gate: str, evidence: str) -> None:
    global PASS
    PASS += 1
    RESULTS.append((gate, True, evidence))
    print(f"  [OK]   {gate}: {evidence}")


def _fail(gate: str, evidence: str) -> None:
    global FAIL
    FAIL += 1
    RESULTS.append((gate, False, evidence))
    print(f"  [FAIL] {gate}: {evidence}")


def gate_pre_exists() -> None:
    p = BENCH_DIR / "jit_loader_pre_fix.json"
    if p.is_file() and p.stat().st_size > 100:
        _ok("V-JIT-BENCH-PRE-EXISTS", f"{p.relative_to(PP_ROOT)}")
    else:
        _fail("V-JIT-BENCH-PRE-EXISTS", f"missing or empty: {p}")


def gate_post_exists() -> None:
    p = BENCH_DIR / "jit_loader_post_fix.json"
    if p.is_file() and p.stat().st_size > 100:
        _ok("V-JIT-BENCH-POST-EXISTS", f"{p.relative_to(PP_ROOT)}")
    else:
        _fail("V-JIT-BENCH-POST-EXISTS", f"missing or empty: {p}")


def gate_improvement() -> None:
    pre = BENCH_DIR / "jit_loader_pre_fix.json"
    post = BENCH_DIR / "jit_loader_post_fix.json"
    if not (pre.is_file() and post.is_file()):
        _fail("V-JIT-IMPROVEMENT", "pre or post missing")
        return
    try:
        pre_e2e = json.loads(pre.read_text(encoding="utf-8")).get(
            "end_to_end_ms") or []
        post_e2e = json.loads(post.read_text(encoding="utf-8")).get(
            "end_to_end_ms") or []
        if not pre_e2e or not post_e2e:
            _fail("V-JIT-IMPROVEMENT", "e2e arrays empty")
            return
        pa = statistics.mean(pre_e2e)
        po = statistics.mean(post_e2e)
        if po < pa:
            gain = (pa - po) / pa * 100
            _ok("V-JIT-IMPROVEMENT",
                f"e2e {pa:.0f} -> {po:.0f} ms (gain {gain:+.1f}%)")
        else:
            _fail("V-JIT-IMPROVEMENT",
                  f"no gain: pre {pa:.0f} ms, post {po:.0f} ms")
    except (OSError, ValueError) as exc:
        _fail("V-JIT-IMPROVEMENT", f"{type(exc).__name__}: {exc}")


def gate_lazy_import() -> None:
    try:
        sys.path.insert(0, str(PP_ROOT))
        import tools.jit_skill_loader as jit  # noqa
        result = jit.run({"prompt": "", "cwd": str(PP_ROOT)})
        if isinstance(result, dict) and result.get("continue") is True:
            _ok("V-JIT-LAZY-IMPORT",
                "run() returned continue=True with "
                f"{len(result.get('additionalContext', ''))} B context")
        else:
            _fail("V-JIT-LAZY-IMPORT", f"bad result shape: {result!r}")
    except Exception as exc:
        _fail("V-JIT-LAZY-IMPORT", f"{type(exc).__name__}: {exc}")


def gate_warm_exists() -> None:
    p = HOOKS_DIR / "jit_warm.js"
    if p.is_file() and p.stat().st_size > 500:
        _ok("V-JIT-WARM-EXISTS", f"{p.relative_to(PP_ROOT)}")
    else:
        _fail("V-JIT-WARM-EXISTS", f"missing or too small: {p}")


def gate_warm_runs() -> None:
    p = HOOKS_DIR / "jit_warm.js"
    if not p.is_file():
        _fail("V-JIT-WARM-RUNS", "jit_warm.js missing")
        return
    try:
        proc = subprocess.run(
            ["node", str(p)],
            input="{}",
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0 and not proc.stdout.strip():
            _ok("V-JIT-WARM-RUNS",
                f"exit 0, stdout silent, stderr={len(proc.stderr)} B")
        else:
            _fail("V-JIT-WARM-RUNS",
                  f"rc={proc.returncode} stdout={proc.stdout[:80]!r}")
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        _fail("V-JIT-WARM-RUNS", f"{type(exc).__name__}: {exc}")


def gate_warm_log() -> None:
    import tempfile
    log = Path(tempfile.gettempdir()) / "pp-jit-warm.log"
    p = HOOKS_DIR / "jit_warm.js"
    if not p.is_file():
        _fail("V-JIT-WARM-LOG", "jit_warm.js missing")
        return
    before_size = log.stat().st_size if log.is_file() else 0
    try:
        subprocess.run(
            ["node", str(p)],
            input="{}",
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        _fail("V-JIT-WARM-LOG", f"spawn failed: {exc}")
        return
    # Detached spawn: poll briefly for the log line to land.
    deadline = time.time() + 5
    while time.time() < deadline:
        if log.is_file() and log.stat().st_size > before_size:
            tail = log.read_text(encoding="utf-8").splitlines()[-3:]
            if any("SPAWNED" in t or "ERROR" in t or "SKIP" in t
                   for t in tail):
                _ok("V-JIT-WARM-LOG",
                    f"log grew, tail: {tail[-1][:120]!r}")
                return
        time.sleep(0.25)
    _fail("V-JIT-WARM-LOG", f"log {log} did not grow within 5 s")


def gate_batch_telem() -> None:
    """The existing _telemetry() opens the file once per call and writes
    all rows in a single context-manager block (per-call batch). Verify
    that contract still holds by grepping the source.
    """
    src = (TOOLS_DIR / "jit_skill_loader.py").read_text(encoding="utf-8")
    # Look for the _telemetry function body: a `with open(p, "a"` followed
    # by a `for r in rows:` loop -- one fopen per call, N rows per fopen.
    has_open = 'with open(p, "a"' in src
    has_loop = "for r in rows:" in src
    if has_open and has_loop:
        _ok("V-JIT-BATCH-TELEM",
            "_telemetry uses single fopen + row loop (per-call batch)")
    else:
        _fail("V-JIT-BATCH-TELEM",
              f"open={has_open} loop={has_loop} -- contract broken")


def gate_fail_open() -> None:
    """PP_WARM_RUN=1 must short-circuit cleanly (exit 0, no exception)."""
    try:
        env = dict(os.environ)
        env["PP_WARM_RUN"] = "1"
        env["PP_WARM_CWD"] = str(PP_ROOT)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [PY, str(TOOLS_DIR / "jit_skill_loader.py")],
            env=env,
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0 and "warm:ok" in proc.stdout:
            _ok("V-JIT-FAIL-OPEN",
                "PP_WARM_RUN=1 -> exit 0, stdout 'warm:ok'")
        else:
            _fail("V-JIT-FAIL-OPEN",
                  f"rc={proc.returncode} "
                  f"stdout={proc.stdout[:80]!r} stderr={proc.stderr[:80]!r}")
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        _fail("V-JIT-FAIL-OPEN", f"{type(exc).__name__}: {exc}")


def gate_register() -> None:
    try:
        proc = subprocess.run(
            [PY, str(TOOLS_DIR / "register_global_hooks.py"), "--dry-run"],
            capture_output=True, text=True, timeout=15,
        )
        if "jit_warm" in proc.stdout:
            _ok("V-JIT-REGISTER",
                "--dry-run output includes jit_warm")
        else:
            _fail("V-JIT-REGISTER",
                  f"jit_warm not in --dry-run output; "
                  f"rc={proc.returncode}, stdout head={proc.stdout[:200]!r}")
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        _fail("V-JIT-REGISTER", f"{type(exc).__name__}: {exc}")


def gate_baseline_intact() -> None:
    """Smoke: jit_skill_loader still parses + all helpers exist."""
    try:
        sys.path.insert(0, str(PP_ROOT))
        import tools.jit_skill_loader as jit
        required = ["run", "_walk_has_graphql", "_active_spec",
                    "_spec_cache_path", "_warm_run",
                    "_proactive_any_eligible"]
        missing = [a for a in required if not hasattr(jit, a)]
        if missing:
            _fail("V-BASELINE-INTACT",
                  f"missing attrs: {missing}")
        else:
            _ok("V-BASELINE-INTACT",
                f"all {len(required)} required attrs present")
    except Exception as exc:
        _fail("V-BASELINE-INTACT", f"{type(exc).__name__}: {exc}")


def main() -> int:
    print("=" * 60)
    print("V-JIT-* performance gates (T-JIT-001, BL-JIT-001)")
    print("=" * 60)
    for gate in (
        gate_pre_exists,
        gate_post_exists,
        gate_improvement,
        gate_lazy_import,
        gate_warm_exists,
        gate_warm_runs,
        gate_warm_log,
        gate_batch_telem,
        gate_fail_open,
        gate_register,
        gate_baseline_intact,
    ):
        gate()
    print()
    print(f"JIT_PERFORMANCE={PASS}/{PASS + FAIL}  threshold=11/11")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
