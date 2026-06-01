"""run_bench_passes.py -- second-pass corrections + re-measurements.

Used by the PP Benchmark Audit to:
  - Re-run verify_spp at the correct path (tools/verify_spp.py).
  - Re-measure session_start (the first orchestrator pass saw a 1105ms
    spike likely from Windows Defender; we want at least 2 datapoints
    so the audit can declare the median).
  - Re-classify benchmark 11 (monitoring): rc=1 from --once means
    "at least one project DOWN" -- a semantic signal, not a perf failure.

Output: vault/benchmarks/audit_pass2_<ISO>.json
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
PY = sys.executable


def _ms() -> float:
    return time.perf_counter() * 1000


def _run(args, *, timeout, cwd=None, input_bytes=None):
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            env=os.environ.copy(),
            cwd=str(cwd or PP),
            input=input_bytes,
        )
        return r.returncode, r.stdout.decode("utf-8", "replace"), \
               r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except Exception as exc:  # noqa: BLE001
        return -3, "", f"{type(exc).__name__}: {exc}"


def pass_verify_spp():
    t0 = _ms()
    rc, so, se = _run(
        [PY, str(PP / "tools" / "verify_spp.py")],
        timeout=90,
    )
    elapsed = _ms() - t0
    combined = so + se
    return {
        "rc": rc,
        "wall_ms": round(elapsed, 0),
        "pass_count": combined.count("PASS"),
        "fail_count": combined.count("FAIL"),
        "ok_count": combined.count(" OK "),
        "tail": "\n".join(so.strip().splitlines()[-5:])[:600],
    }


def pass_session_start_3runs():
    runs = []
    for i in range(3):
        t0 = _ms()
        rc, so, _se = _run(
            [PY, str(PP / "tools" / "measure_session_start.py"), "--json"],
            timeout=90,
        )
        wall = _ms() - t0
        try:
            data = json.loads(so)
            runs.append({
                "run": i + 1,
                "wall_ms": round(wall, 0),
                "individual_max_ms": round(
                    data.get("individual_max_ms", 0), 0),
                "total_serial_ms": round(data.get("total_serial_ms", 0), 0),
                "verdict": data.get("verdict"),
                "slow_count": len(data.get("slow_hooks", [])),
                "rc": rc,
            })
        except Exception as exc:  # noqa: BLE001
            runs.append({
                "run": i + 1,
                "wall_ms": round(wall, 0),
                "error": f"json parse: {exc}",
                "rc": rc,
            })
    maxes = [r.get("individual_max_ms") for r in runs
             if r.get("individual_max_ms") is not None]
    return {
        "runs": runs,
        "median_individual_max_ms": (round(statistics.median(maxes), 0)
                                     if maxes else None),
        "best_individual_max_ms": (min(maxes) if maxes else None),
        "worst_individual_max_ms": (max(maxes) if maxes else None),
    }


def pass_monitoring_semantic():
    t0 = _ms()
    rc, so, se = _run(
        [PY, "-m", "modules.monitoring.observe", "--once"],
        timeout=30,
    )
    wall = _ms() - t0
    lines = [l for l in so.splitlines() if l.strip()]
    return {
        "rc": rc,
        "wall_ms": round(wall, 0),
        "interpretation": (
            "rc=0 all projects UP" if rc == 0
            else "rc=1 at least one project DOWN (semantic signal, "
                 "not perf failure)" if rc == 1
            else "rc=4 no monitor configs found" if rc == 4
            else f"rc={rc} unknown exit"
        ),
        "stdout_lines": len(lines),
        "tail": "\n".join(lines[-5:])[:600],
        "stderr_head": se.strip()[:200],
    }


def main():
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_path = PP / "vault" / "benchmarks" / f"audit_pass2_{iso}.json"
    results = {
        "timestamp_iso": iso,
        "passes": {},
    }
    for name, fn in [
        ("verify_spp", pass_verify_spp),
        ("session_start_3runs", pass_session_start_3runs),
        ("monitoring_semantic", pass_monitoring_semantic),
    ]:
        print(f"[{name}] running...", flush=True)
        results["passes"][name] = fn()
        print(f"[{name}] done", flush=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
