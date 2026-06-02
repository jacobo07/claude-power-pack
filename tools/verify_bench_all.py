"""verify_bench_all.py -- verify_spp BENCHMARKS_OK probe.

Runs `python tools/bench_all.py --quick --json` and asserts that the
quick-mode results fit within 1.5x of the SCS C26 targets. The 1.5x
band accounts for T-WIN-AV-001 cold-scan variance (300-700 ms can
land on any Python subprocess spawn on Windows).

This probe is wired into `tools/verify_spp.py` as the BENCHMARKS_OK
row. It exits 0 on PASS (all quick benchmarks within 1.5x target) and
exits 1 with the failing list otherwise.

Empirical contract: the quick suite must complete in < 60 s wall time.
This probe inherits the 60 s budget assigned by verify_spp.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]

QUICK_TARGETS = {
    "tco_gate_ms": 270,
    "tis_report_ms": 225,
    "osa_dispatcher_ms": 300,
    "proactive_dispatch_ms": 30,
    "anti_patterns_ms": 120,
    "ceps_record_ms": 38,
    "session_hub_ms": 300,
    "never_again_ms": 30,
}


def main() -> int:
    try:
        r = subprocess.run(
            [sys.executable, str(PP / "tools" / "bench_all.py"),
             "--quick", "--json"],
            capture_output=True,
            text=True,
            timeout=55,
            cwd=str(PP),
        )
    except subprocess.TimeoutExpired:
        print("BENCHMARKS_OK: TIMEOUT -- bench_all --quick > 55 s wall")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"BENCHMARKS_OK: subprocess error -- "
              f"{type(exc).__name__}: {exc}")
        return 1

    out = r.stdout.strip()
    if not out:
        print(f"BENCHMARKS_OK: empty stdout from bench_all "
              f"(rc={r.returncode}; stderr head: "
              f"{r.stderr.strip()[:200]})")
        return 1

    # bench_all --json prints progress lines THEN a JSON object THEN a
    # closing "bench_all exit rc=..." trailer. Find the first open-brace
    # that begins a complete JSON object and raw_decode from there.
    decoder = json.JSONDecoder()
    payload = None
    for i, ch in enumerate(out):
        if ch != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(out[i:])
            break
        except json.JSONDecodeError:
            continue
    if payload is None:
        print("BENCHMARKS_OK: no parseable JSON in bench_all stdout")
        return 1

    results = payload.get("results", {})
    fails = []
    checked = 0
    for name, target in QUICK_TARGETS.items():
        value = results.get(name)
        if not isinstance(value, (int, float)):
            continue
        checked += 1
        if value > target:
            fails.append(f"{name}: {value:.0f}>{target}")

    if checked == 0:
        print(f"BENCHMARKS_OK: no quick-mode benchmarks found "
              f"in bench_all JSON")
        return 1

    if fails:
        head = ", ".join(fails[:3])
        more = f" (+{len(fails)-3} more)" if len(fails) > 3 else ""
        print(f"BENCHMARKS_OK: {len(fails)}/{checked} over 1.5x "
              f"target: {head}{more}")
        return 1

    print(f"BENCHMARKS_OK: {checked}/{len(QUICK_TARGETS)} quick "
          f"benchmarks within 1.5x SCS C26 targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
