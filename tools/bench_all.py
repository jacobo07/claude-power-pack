"""PP Benchmark Suite -- tools/bench_all.py

Unified runner for the 15 baseline benchmarks + N1-N7 extension probes.
Writes results to vault/benchmarks/ledger.json (last 50 runs) and
compares against the prior run for regression detection.

Usage:
    python tools/bench_all.py            # full run
    python tools/bench_all.py --quick    # only fast benchmarks (<5s)
    python tools/bench_all.py --compare  # show delta vs previous run
    python tools/bench_all.py --json     # emit JSON to stdout
    python tools/bench_all.py --label X  # tag this entry with a label

Each benchmark returns a dict of measured metrics. Primary metric is the
key whose name matches the benchmark; secondary metrics (min/max/stdev,
pass-count etc) are recorded but not gated against TARGETS.

Reality contract: every benchmark issues a real subprocess or function
call. Failures are recorded honestly (error field per benchmark).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]
PY = sys.executable
LEDGER_PATH = PP_PATH / "vault" / "benchmarks" / "ledger.json"
LEDGER_KEEP = 50

REGRESSION_PCT = 1.15  # 15% slower than prior run = regression

TARGETS = {
    "session_start_worst_ms": 200,
    "session_start_total_ms": 350,
    "jit_cold_start_avg_ms": 80,
    "pytest_total_ms": 8000,
    "verify_spp_ms": 15000,
    "vgate_total_ms": 25000,
    "uqf_scan_ms": 1500,
    "tco_gate_ms": 180,
    "tis_report_ms": 150,
    "osa_dispatcher_ms": 200,
    "proactive_dispatch_ms": 20,
    "monitoring_once_ms": 2000,
    "anti_patterns_ms": 80,
    "ceps_record_ms": 25,
    "session_hub_ms": 200,
    "never_again_ms": 20,
    # RAM Optimization Sprint (2026-06-04): PP-overhead footprint in MB.
    # Forensics measured steady-state node+python at ~12 MB; the 300 MB
    # target is the SCS C34 ceiling. claude.exe RAM (claude_ws_mb /
    # claude_private_mb) is recorded as context but NOT gated -- it is
    # native and not PP-controllable.
    "ram_footprint_mb": 300,
}


def _ms() -> float:
    return time.perf_counter() * 1000


def _run(args, *, timeout, env=None, input_bytes=None):
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            cwd=str(PP_PATH),
            input=input_bytes,
        )
        return (
            r.returncode,
            r.stdout.decode("utf-8", "replace"),
            r.stderr.decode("utf-8", "replace"),
        )
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except FileNotFoundError as exc:
        return -2, "", f"FileNotFoundError: {exc}"
    except Exception as exc:  # noqa: BLE001
        return -3, "", f"{type(exc).__name__}: {exc}"


def bench_session_start():
    rc, so, se = _run(
        [PY, str(PP_PATH / "tools" / "measure_session_start.py"), "--json"],
        timeout=90,
    )
    if rc not in (0, 1) or not so.strip():
        return {"session_start_error": (se or f"rc={rc}").strip()[:120]}
    try:
        data = json.loads(so)
        return {
            "session_start_worst_ms": data.get("individual_max_ms"),
            "session_start_total_ms": data.get("total_serial_ms"),
            "session_start_verdict": data.get("verdict"),
            "session_start_hook_count": data.get("hook_count"),
            "session_start_slow": len(data.get("slow_hooks", [])),
        }
    except Exception as exc:  # noqa: BLE001
        return {"session_start_error": f"parse: {exc}"}


def bench_jit_cold_start(n: int = 5):
    runs = []
    for _ in range(n):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        t0 = _ms()
        rc, _so, se = _run(
            [PY, "-c",
             f"import sys; sys.path.insert(0, r'{PP_PATH}'); "
             "import tools.jit_skill_loader"],
            timeout=15,
            env=env,
        )
        ms = _ms() - t0
        if rc != 0:
            return {"jit_cold_start_error":
                    (se or f"rc={rc}").strip()[:120]}
        runs.append(ms)
    return {
        "jit_cold_start_avg_ms": round(statistics.mean(runs), 1),
        "jit_cold_start_min_ms": round(min(runs), 1),
        "jit_cold_start_max_ms": round(max(runs), 1),
        "jit_cold_start_stdev": round(
            statistics.stdev(runs), 1) if len(runs) > 1 else 0,
    }


def bench_uqf_scan():
    target = PP_PATH / "tools" / "uqf_audit.py"
    if not target.is_file():
        return {"uqf_scan_error": "uqf_audit.py missing"}
    t0 = _ms()
    rc, so, se = _run([PY, str(target), "--scan-all"], timeout=60)
    return {
        "uqf_scan_ms": round(_ms() - t0, 1),
        "uqf_scan_rc": rc,
        "uqf_scan_lines": len([l for l in so.splitlines() if l.strip()]),
    }


def bench_verify_spp():
    target = PP_PATH / "tools" / "verify_spp.py"
    if not target.is_file():
        return {"verify_spp_error": "tools/verify_spp.py missing"}
    t0 = _ms()
    rc, so, _se = _run([PY, str(target)], timeout=300)
    combined = so
    return {
        "verify_spp_ms": round(_ms() - t0, 1),
        "verify_spp_rc": rc,
        "verify_spp_pass": combined.count("PASS"),
        "verify_spp_fail": combined.count("STRICT FAIL"),
    }


def bench_pytest():
    tests = PP_PATH / "tests"
    if not tests.is_dir():
        return {"pytest_error": "tests/ dir missing"}
    t0 = _ms()
    rc, so, _se = _run(
        [PY, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
        timeout=180,
    )
    last = (so.strip().splitlines() or [""])[-1]
    return {
        "pytest_total_ms": round(_ms() - t0, 1),
        "pytest_rc": rc,
        "pytest_summary": last[:120],
    }


def _run_suite(suite: Path):
    t0 = _ms()
    rc, so, se = _run([PY, str(suite)], timeout=60)
    return {
        "suite": suite.name,
        "ms": round(_ms() - t0, 0),
        "rc": rc,
        "verdict": "PASS" if rc == 0 else f"FAIL(rc={rc})",
    }


def bench_vgate_suites():
    suites = sorted((PP_PATH / "tools").glob("test_*.py"))
    if not suites:
        return {"vgate_error": "no test_*.py found in tools/"}
    t0 = _ms()
    results = []
    # Parallel execution per S1.2 doctrine.
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(_run_suite, s): s for s in suites}
        for fut in as_completed(futures):
            results.append(fut.result())
    total_ms = round(_ms() - t0, 1)
    passes = sum(1 for r in results if r["rc"] == 0)
    return {
        "vgate_total_ms": total_ms,
        "vgate_count": len(results),
        "vgate_passes": passes,
        "vgate_fails": len(results) - passes,
        "vgate_suites": results,
    }


def bench_tco_gate():
    target = PP_PATH / "tools" / "tco_compact_gate.py"
    if not target.is_file():
        return {"tco_gate_error": "tco_compact_gate.py missing"}
    t0 = _ms()
    rc, so, _se = _run([PY, str(target)], timeout=15)
    return {
        "tco_gate_ms": round(_ms() - t0, 1),
        "tco_gate_rc": rc,
        "tco_gate_head": (so.strip().splitlines() or [""])[0][:120],
    }


def bench_tis_report():
    target = PP_PATH / "tools" / "tis_report.py"
    if not target.is_file():
        return {"tis_report_error": "tis_report.py missing"}
    t0 = _ms()
    rc, so, _se = _run([PY, str(target), "--summary"], timeout=15)
    return {
        "tis_report_ms": round(_ms() - t0, 1),
        "tis_report_rc": rc,
        "tis_report_lines": len([l for l in so.splitlines() if l.strip()]),
    }


def bench_osa_dispatcher():
    target = PP_PATH / "modules" / "osa" / "dispatcher.py"
    if not target.is_file():
        return {"osa_dispatcher_error":
                "modules/osa/dispatcher.py missing"}
    t0 = _ms()
    rc, so, _se = _run([PY, str(target), "--check"], timeout=15)
    return {
        "osa_dispatcher_ms": round(_ms() - t0, 1),
        "osa_dispatcher_rc": rc,
    }


def bench_proactive_dispatch():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP_PATH}');"
        "from modules.pp_agents.proactive_dispatcher import dispatch;"
        "t0 = time.perf_counter();"
        "ctx = {'project':'bench','last_written_code':'',"
        "'last_written_file':'','current_error':'',"
        "'session_had_errors': False,'errors_fixed':0};"
        "r = dispatch(ctx);"
        "print(json.dumps({'advisories': len(r), "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run([PY, "-c", script], timeout=15)
    if rc != 0:
        return {"proactive_dispatch_error":
                (se or f"rc={rc}").strip()[:120]}
    try:
        payload = json.loads(so.strip().splitlines()[-1])
        return {
            "proactive_dispatch_ms": payload["inner_ms"],
            "proactive_dispatch_advisories": payload["advisories"],
        }
    except Exception as exc:  # noqa: BLE001
        return {"proactive_dispatch_error": f"parse: {exc}"}


def bench_monitoring():
    t0 = _ms()
    rc, _so, _se = _run(
        [PY, "-m", "modules.monitoring.observe", "--once"],
        timeout=30,
    )
    return {
        "monitoring_once_ms": round(_ms() - t0, 1),
        "monitoring_rc": rc,
    }


def bench_anti_patterns():
    sample = PP_PATH / "tools" / "ceps.py"
    if not sample.is_file():
        return {"anti_patterns_error": "tools/ceps.py missing"}
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP_PATH}');"
        "from modules.uqf.anti_patterns import run_all;"
        f"code = open(r'{sample}', encoding='utf-8').read();"
        "t0 = time.perf_counter();"
        "hits = run_all(code);"
        "total = sum(len(v) for v in hits.values());"
        "print(json.dumps({'total_hits': total, "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run([PY, "-c", script], timeout=15)
    if rc != 0:
        return {"anti_patterns_error":
                (se or f"rc={rc}").strip()[:120]}
    try:
        payload = json.loads(so.strip().splitlines()[-1])
        return {
            "anti_patterns_ms": payload["inner_ms"],
            "anti_patterns_hits": payload["total_hits"],
        }
    except Exception as exc:  # noqa: BLE001
        return {"anti_patterns_error": f"parse: {exc}"}


def bench_ceps_record():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP_PATH}');"
        "from tools.ceps import record_error;"
        "t0 = time.perf_counter();"
        "record_error('bench_all', 'bench', 'perf', True);"
        "print(json.dumps({"
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run([PY, "-c", script], timeout=15)
    if rc != 0:
        return {"ceps_record_error": (se or f"rc={rc}").strip()[:120]}
    try:
        payload = json.loads(so.strip().splitlines()[-1])
        return {"ceps_record_ms": payload["inner_ms"]}
    except Exception as exc:  # noqa: BLE001
        return {"ceps_record_error": f"parse: {exc}"}


def bench_session_hub_direct():
    hub = PP_PATH / "hooks" / "session_start_hub.js"
    if not hub.is_file():
        return {"session_hub_error":
                "hooks/session_start_hub.js missing"}
    t0 = _ms()
    rc, so, _se = _run(
        ["node", str(hub)],
        timeout=10,
        input_bytes=b"{}",
    )
    return {
        "session_hub_ms": round(_ms() - t0, 1),
        "session_hub_rc": rc,
        "session_hub_stdout_bytes": len(so),
    }


def bench_never_again():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP_PATH}');"
        "from modules.osa.never_again import top_recurring;"
        "t0 = time.perf_counter();"
        "rows = top_recurring(10);"
        "print(json.dumps({'rows': len(rows), "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run([PY, "-c", script], timeout=15)
    if rc != 0:
        return {"never_again_error":
                (se or f"rc={rc}").strip()[:120]}
    try:
        payload = json.loads(so.strip().splitlines()[-1])
        return {
            "never_again_ms": payload["inner_ms"],
            "never_again_rows": payload["rows"],
        }
    except Exception as exc:  # noqa: BLE001
        return {"never_again_error": f"parse: {exc}"}


# PowerShell measurement (NO Get-CimInstance -- it hung twice under
# -NonInteractive on this host, sealed 2026-06-04). Get-Process only.
_PS_RAM = (
    "$ErrorActionPreference='SilentlyContinue';"
    "function S($n){$p=Get-Process $n -ErrorAction SilentlyContinue;"
    "if($p){[math]::Round((($p|Measure-Object WorkingSet64 -Sum).Sum)/1MB,1)}"
    "else{0}}"
    "$node=S 'node'; $py=S 'python';"
    "$c=Get-Process claude -ErrorAction SilentlyContinue;"
    "$cws=if($c){[math]::Round((($c|Measure-Object WorkingSet64 -Sum)"
    ".Sum)/1MB,1)}else{0};"
    "$cpv=if($c){[math]::Round((($c|Measure-Object PrivateMemorySize64 -Sum)"
    ".Sum)/1MB,1)}else{0};"
    "ConvertTo-Json -Compress @{pp_overhead_mb=($node+$py);node_mb=$node;"
    "python_mb=$py;claude_ws_mb=$cws;claude_private_mb=$cpv}"
)


def bench_ram_footprint():
    """Measure the PP RAM footprint (node hooks + python) and record
    claude.exe RAM as ungated context. Reality contract: real Get-Process
    sample; honest error if no PowerShell. ``ram_footprint_mb`` is the
    gated PP-overhead number (SCS C34 ceiling 300 MB)."""
    so = ""
    for exe in ("powershell.exe", "powershell", "pwsh"):
        rc, so, se = _run(
            [exe, "-NoProfile", "-NonInteractive", "-Command", _PS_RAM],
            timeout=20,
        )
        if rc == 0 and so.strip():
            break
    else:
        return {"ram_footprint_error":
                "no powershell / measurement failed"}
    try:
        data = json.loads(so.strip().lstrip("﻿").splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        return {"ram_footprint_error": f"parse: {exc}"}
    pp = data.get("pp_overhead_mb")
    return {
        "ram_footprint_mb": pp,            # gated: node + python overhead
        "ram_node_mb": data.get("node_mb"),
        "ram_python_mb": data.get("python_mb"),
        "claude_ws_mb": data.get("claude_ws_mb"),         # ungated context
        "claude_private_mb": data.get("claude_private_mb"),
    }


ALL_BENCHES = [
    ("ram_footprint", bench_ram_footprint),
    ("session_start", bench_session_start),
    ("jit_cold_start", bench_jit_cold_start),
    ("uqf_scan", bench_uqf_scan),
    ("verify_spp", bench_verify_spp),
    ("pytest", bench_pytest),
    ("vgate_suites", bench_vgate_suites),
    ("tco_gate", bench_tco_gate),
    ("tis_report", bench_tis_report),
    ("osa_dispatcher", bench_osa_dispatcher),
    ("proactive_dispatch", bench_proactive_dispatch),
    ("monitoring", bench_monitoring),
    ("anti_patterns", bench_anti_patterns),
    ("ceps_record", bench_ceps_record),
    ("session_hub_direct", bench_session_hub_direct),
    ("never_again", bench_never_again),
]

QUICK_NAMES = {
    "ram_footprint",
    "tco_gate", "tis_report", "osa_dispatcher", "proactive_dispatch",
    "anti_patterns", "ceps_record", "session_hub_direct", "never_again",
}


def load_ledger():
    if not LEDGER_PATH.is_file():
        return []
    try:
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_ledger(entry):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    history = load_ledger()
    history.append(entry)
    LEDGER_PATH.write_text(
        json.dumps(history[-LEDGER_KEEP:], indent=2),
        encoding="utf-8",
    )


def status_for(name, ms):
    target = TARGETS.get(name)
    if target is None or ms is None or not isinstance(ms, (int, float)):
        return "--"
    if ms <= target:
        return "OK"
    if ms <= target * 1.3:
        return "WARN"
    return "FAIL"


def render_table(results, prev=None):
    lines = []
    lines.append("=" * 78)
    lines.append("PP BENCHMARK SUITE")
    header = f"{'Metric':<28} {'ms':>10} {'target':>10} {'status':>8}"
    if prev:
        header += f"  {'delta_vs_prev':>16}"
    lines.append(header)
    lines.append("-" * 78)
    at_target = 0
    counted = 0
    for name, target in TARGETS.items():
        ms = results.get(name)
        if not isinstance(ms, (int, float)):
            continue
        counted += 1
        st = status_for(name, ms)
        if st == "OK":
            at_target += 1
        delta = ""
        if prev and name in prev:
            prev_ms = prev.get(name)
            if isinstance(prev_ms, (int, float)) and prev_ms > 0:
                pct = ((prev_ms - ms) / prev_ms) * 100
                delta = f"  {prev_ms:>5.0f}->{ms:>5.0f}  {pct:+5.1f}%"
        lines.append(
            f"{name:<28} {ms:>10.0f} {target:>10} {st:>8}{delta}")
    lines.append("=" * 78)
    lines.append(f"AT TARGET: {at_target}/{counted}")
    lines.append("=" * 78)
    return "\n".join(lines)


def detect_regressions(curr, prev):
    out = []
    if not prev:
        return out
    for name in TARGETS:
        cm = curr.get(name)
        pm = prev.get(name)
        if (isinstance(cm, (int, float))
                and isinstance(pm, (int, float))
                and pm > 0
                and cm > pm * REGRESSION_PCT):
            pct = ((cm / pm) - 1.0) * 100
            out.append(
                f"{name}: {pm:.0f} -> {cm:.0f} ms (+{pct:.0f}%)")
    return out


def flatten_results(payload_dict_list):
    out = {}
    for d in payload_dict_list:
        if isinstance(d, dict):
            out.update(d)
    return out


def get_head_commit():
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(PP_PATH), timeout=5,
        )
        return r.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--quick", action="store_true",
                    help="Run only fast benchmarks (<5s each).")
    ap.add_argument("--compare", action="store_true",
                    help="Show delta vs the previous ledger entry.")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON entry on stdout.")
    ap.add_argument("--label", default=None,
                    help="Tag this ledger entry with a label.")
    args = ap.parse_args(argv)

    history = load_ledger()
    prev_results = history[-1].get("results") if history else None

    selected = [
        (name, fn) for name, fn in ALL_BENCHES
        if (not args.quick) or name in QUICK_NAMES
    ]
    print(f"Running {'quick' if args.quick else 'full'} suite "
          f"({len(selected)} benchmarks)...", flush=True)

    raw_payloads = []
    errors = {}
    for name, fn in selected:
        print(f"  [{name}] ...", end="", flush=True)
        t0 = _ms()
        try:
            payload = fn() or {}
        except Exception as exc:  # noqa: BLE001
            payload = {f"{name}_error":
                       f"{type(exc).__name__}: {exc}"}
        outer = round(_ms() - t0, 0)
        primary = TARGETS.get(name)
        primary_ms = next(
            (v for k, v in payload.items()
             if k.endswith("_ms") and isinstance(v, (int, float))),
            outer,
        )
        if any(k.endswith("_error") for k in payload):
            errors[name] = next(v for k, v in payload.items()
                                if k.endswith("_error"))
            print(f" ERROR ({outer:.0f}ms)")
        else:
            tag = "OK" if (primary is None or primary_ms <= primary) else \
                  "WARN" if primary_ms <= primary * 1.3 else "FAIL"
            print(f" {primary_ms:.0f}ms [{tag}] (outer {outer:.0f}ms)")
        payload[f"{name}_outer_ms"] = outer
        raw_payloads.append(payload)

    results = flatten_results(raw_payloads)
    entry = {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "commit": get_head_commit(),
        "label": args.label,
        "quick": args.quick,
        "results": results,
        "errors": errors,
    }
    save_ledger(entry)

    regressions = detect_regressions(results, prev_results)

    if args.json:
        print(json.dumps(entry, indent=2))
    else:
        print(render_table(results,
                           prev_results if args.compare else None))
        if errors:
            print(f"\nERRORS ({len(errors)}):")
            for name, err in errors.items():
                print(f"  {name}: {err[:140]}")
        if regressions:
            print(f"\nREGRESSIONS ({len(regressions)}):")
            for r in regressions:
                print(f"  {r}")

    at_target = sum(
        1 for name, t in TARGETS.items()
        if isinstance(results.get(name), (int, float))
        and results[name] <= t
    )
    rc = 0 if (not errors and not regressions) else 1
    print(f"\nbench_all exit rc={rc}  "
          f"at_target={at_target}/{len(TARGETS)}", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
