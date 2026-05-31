#!/usr/bin/env python3
"""bench_jit_loader.py -- cold-start microbench for jit_skill_loader.

Measures three things the perceived /kclear first-prompt lag actually
depends on:
    1. Python cold-start + jit_skill_loader import time (5 runs).
    2. End-to-end run(empty-prompt) time -- what UserPromptSubmit pays.
    3. ``python -X importtime`` breakdown -- which submodules are heavy.

Output: vault/benchmarks/jit_loader_pre_fix.json on first run; if that
file already exists, the new run is treated as a post-fix sample and
written to jit_loader_post_fix.json, with a delta block printed at the
end.

Pure stdlib. Sub-process calls (the only honest way to measure cold
start) -- ``time.perf_counter()`` in-process would only capture the
warm-cache case.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = PP_ROOT / "vault" / "benchmarks"
PRE = BENCH_DIR / "jit_loader_pre_fix.json"
POST = BENCH_DIR / "jit_loader_post_fix.json"

JIT = PP_ROOT / "tools" / "jit_skill_loader.py"


def _import_only_ms(n: int = 5) -> list[int]:
    """Spawn N subprocesses; each only imports the module + exits."""
    code = (
        "import time, sys; "
        f"sys.path.insert(0, r'{PP_ROOT}'); "
        "t = time.perf_counter(); "
        "import tools.jit_skill_loader as _jit; "
        "print(int((time.perf_counter() - t) * 1000))"
    )
    times: list[int] = []
    for i in range(n):
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        try:
            ms = int(proc.stdout.strip().splitlines()[-1])
            times.append(ms)
            print(f"  import run {i + 1}: {ms} ms")
        except Exception:
            print(f"  import run {i + 1}: ERROR ({proc.stderr[:80]!r})")
    return times


def _end_to_end_ms(n: int = 3) -> list[int]:
    """Spawn the script the way the real UserPromptSubmit hook does.

    Includes interpreter start + 3-second stdin budget short-circuited
    by closing stdin immediately (no payload), so what we measure is the
    real cold-start + run() with no Apollo trigger -- the same path the
    first prompt of a new pane pays.
    """
    times: list[int] = []
    for i in range(n):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(JIT)],
            input=b"{}",
            capture_output=True,
            timeout=15,
        )
        ms = int((time.perf_counter() - t0) * 1000)
        if proc.returncode == 0:
            times.append(ms)
            print(f"  end-to-end run {i + 1}: {ms} ms "
                  f"(stdout {len(proc.stdout)} B)")
        else:
            print(f"  end-to-end run {i + 1}: rc={proc.returncode} "
                  f"err={proc.stderr[:80]!r}")
    return times


def _importtime_breakdown() -> list[tuple[int, str]]:
    """Run python -X importtime and return [(microseconds, module), ...]."""
    code = (
        "import sys; "
        f"sys.path.insert(0, r'{PP_ROOT}'); "
        "import tools.jit_skill_loader"
    )
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", code],
        capture_output=True, text=True, timeout=30,
    )
    rows: list[tuple[int, str]] = []
    for line in proc.stderr.splitlines():
        # Format: "import time: self [us] | cumulative | imported module"
        if "|" not in line or "self " in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        try:
            self_us = int(parts[0].split(":")[-1].strip())
            name = parts[2].strip()
            rows.append((self_us, name))
        except (ValueError, IndexError):
            continue
    rows.sort(reverse=True)
    return rows


def _delta_vs(prev_path: Path, fresh: dict) -> str | None:
    if not prev_path.is_file():
        return None
    try:
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    msg = []
    for key, label in (("import_ms", "import"), ("end_to_end_ms", "e2e")):
        p_arr = prev.get(key) or []
        f_arr = fresh.get(key) or []
        if not p_arr or not f_arr:
            continue
        p_avg = statistics.mean(p_arr)
        f_avg = statistics.mean(f_arr)
        delta_pct = ((p_avg - f_avg) / p_avg) * 100 if p_avg else 0
        msg.append(
            f"  {label:8s}: pre avg={p_avg:.0f} ms  post avg={f_avg:.0f} ms  "
            f"gain={delta_pct:+.1f}%"
        )
    return "\n".join(msg) if msg else None


def main() -> int:
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    print("=== jit_skill_loader benchmark ===\n")
    print("Phase 1: import-only cold start (5 runs)")
    import_ms = _import_only_ms(5)
    print()

    print("Phase 2: end-to-end UserPromptSubmit equivalent (3 runs)")
    e2e_ms = _end_to_end_ms(3)
    print()

    print("Phase 3: -X importtime breakdown (top 15 self-time)")
    profile = _importtime_breakdown()[:15]
    for us, name in profile:
        bar = "#" * min(40, us // 1000)
        print(f"  {us:8d} us  {bar:40s}  {name}")
    print()

    payload = {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "import_ms": import_ms,
        "import_ms_stats": {
            "min": min(import_ms) if import_ms else None,
            "avg": statistics.mean(import_ms) if import_ms else None,
            "max": max(import_ms) if import_ms else None,
        },
        "end_to_end_ms": e2e_ms,
        "end_to_end_ms_stats": {
            "min": min(e2e_ms) if e2e_ms else None,
            "avg": statistics.mean(e2e_ms) if e2e_ms else None,
            "max": max(e2e_ms) if e2e_ms else None,
        },
        "top_imports": [{"us": us, "name": name} for us, name in profile],
    }

    out = POST if PRE.is_file() else PRE
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved -> {out}")

    if out == POST:
        delta = _delta_vs(PRE, payload)
        if delta:
            print("\n=== DELTA vs pre_fix ===")
            print(delta)
            # End-to-end is the metric the user feels (full subprocess
            # wall = Python startup + run() + decorators). Import-only
            # is shown for completeness but rarely moves -- the imports
            # were never the bottleneck (see jit_loader_lazy_plan.md).
            avg_pre = statistics.mean(
                json.loads(PRE.read_text(encoding="utf-8"))
                .get("end_to_end_ms") or [0])
            avg_post = statistics.mean(e2e_ms) if e2e_ms else 0
            if avg_pre:
                gain = ((avg_pre - avg_post) / avg_pre) * 100
                if gain >= 20:
                    print(f"\nTARGET MET: end-to-end gain "
                          f"{gain:+.1f}% (>=20%)")
                else:
                    print(f"\nTARGET NOT MET: end-to-end gain "
                          f"{gain:+.1f}% (need >=20%); inspect "
                          f"top_imports for next pivot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
