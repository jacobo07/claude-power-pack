"""run_all_benchmarks.py -- one-shot orchestrator for the PP Benchmark Audit.

Runs the 15 benchmarks defined in the EXECUTION MODE prompt and dumps a
single JSON to vault/benchmarks/audit_run_<ISO>.json. Each benchmark
records a measured wall-time value or an error string -- empty/speculative
entries are not produced.
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

TIMEOUTS = {
    "session_start": 90,
    "jit_loader_cold": 15,
    "uqf_scan": 60,
    "verify_spp": 90,
    "pytest": 180,
    "vgate": 60,
    "tco_gate": 15,
    "tis_report": 15,
    "osa_dispatcher": 15,
    "proactive": 15,
    "monitoring": 30,
    "anti_patterns": 15,
    "ceps": 15,
    "hub_invoke": 10,
    "never_again": 15,
}


def _ms() -> float:
    return time.perf_counter() * 1000


def _run(args, *, timeout, env=None, cwd=None, input_bytes=None):
    """Returns (rc, stdout, stderr). Never raises."""
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            cwd=str(cwd or PP),
            input=input_bytes,
        )
        return r.returncode, r.stdout.decode("utf-8", "replace"), \
               r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout}s"
    except FileNotFoundError as exc:
        return -2, "", f"FileNotFoundError: {exc}"
    except Exception as exc:  # noqa: BLE001
        return -3, "", f"{type(exc).__name__}: {exc}"


def bench_session_start():
    rc, so, se = _run(
        [PY, str(PP / "tools" / "measure_session_start.py"), "--json"],
        timeout=TIMEOUTS["session_start"],
    )
    if rc != 0 and not so.strip():
        return {"ok": False, "error": se.strip()[:200] or f"rc={rc}"}
    try:
        data = json.loads(so)
        return {
            "ok": True,
            "individual_max_ms": data.get("individual_max_ms"),
            "total_serial_ms": data.get("total_serial_ms"),
            "verdict": data.get("verdict"),
            "hook_count": data.get("hook_count"),
            "slow_hooks": len(data.get("slow_hooks", [])),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"json parse: {exc}",
                "raw_head": so[:200]}


def bench_jit_cold():
    runs = []
    for _ in range(5):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        t0 = _ms()
        rc, _so, se = _run(
            [PY, "-c",
             f"import sys; sys.path.insert(0, r'{PP}'); "
             "import tools.jit_skill_loader"],
            timeout=TIMEOUTS["jit_loader_cold"],
            env=env,
        )
        ms = _ms() - t0
        if rc != 0:
            return {"ok": False, "error": se.strip()[:200] or f"rc={rc}",
                    "runs_completed": len(runs)}
        runs.append(ms)
    return {
        "ok": True,
        "runs_ms": [round(r, 1) for r in runs],
        "avg_ms": round(statistics.mean(runs), 1),
        "min_ms": round(min(runs), 1),
        "max_ms": round(max(runs), 1),
        "stdev_ms": round(statistics.stdev(runs), 1) if len(runs) > 1 else 0,
    }


def bench_uqf_scan():
    target = PP / "tools" / "uqf_audit.py"
    if not target.is_file():
        alts = list((PP / "modules" / "uqf").glob("*.py"))
        return {"ok": False, "error": "uqf_audit.py missing",
                "alt_module_files": len(alts)}
    rc, so, se = _run(
        [PY, str(target), "--scan-all"],
        timeout=TIMEOUTS["uqf_scan"],
    )
    return {
        "ok": rc == 0,
        "rc": rc,
        "stdout_lines": len([l for l in so.splitlines() if l.strip()]),
        "stderr_head": se.strip()[:200] if rc != 0 else "",
    }


def bench_verify_spp():
    target = PP / "verify_spp.py"
    if not target.is_file():
        return {"ok": False, "error": "verify_spp.py missing"}
    rc, so, se = _run(
        [PY, str(target)],
        timeout=TIMEOUTS["verify_spp"],
    )
    combined = so + se
    return {
        "ok": rc == 0,
        "rc": rc,
        "pass_lines": combined.count("PASS"),
        "fail_lines": combined.count("FAIL"),
        "ok_lines": combined.count(" OK "),
        "stdout_tail": "\n".join(so.strip().splitlines()[-3:]),
    }


def bench_pytest():
    tests = PP / "tests"
    if not tests.is_dir():
        return {"ok": False, "error": "tests/ dir missing"}
    rc, so, se = _run(
        [PY, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
        timeout=TIMEOUTS["pytest"],
    )
    last = (so.strip().splitlines() or [""])[-1]
    return {
        "ok": rc == 0,
        "rc": rc,
        "summary": last[:140],
    }


def bench_vgate_suites():
    suites = sorted((PP / "tools").glob("test_*.py"))
    results = []
    for s in suites:
        t0 = _ms()
        rc, so, se = _run(
            [PY, str(s)],
            timeout=TIMEOUTS["vgate"],
        )
        ms = _ms() - t0
        combined = so + se
        if rc == 0 and ("PASS" in combined or "OK" in combined
                        or "passed" in combined.lower()):
            verdict = "PASS"
        elif rc == 0:
            verdict = "OK"
        elif "FAIL" in combined or "failed" in combined.lower():
            verdict = "FAIL"
        else:
            verdict = f"ERR(rc={rc})"
        results.append({
            "suite": s.name,
            "ms": round(ms, 0),
            "verdict": verdict,
        })
    return {
        "ok": True,
        "count": len(results),
        "passed": sum(1 for r in results if r["verdict"] == "PASS"),
        "failed": sum(1 for r in results if r["verdict"] not in
                      ("PASS", "OK")),
        "total_ms": round(sum(r["ms"] for r in results), 0),
        "suites": results,
    }


def bench_tco_gate():
    target = PP / "tools" / "tco_compact_gate.py"
    if not target.is_file():
        return {"ok": False, "error": "tco_compact_gate.py missing"}
    rc, so, se = _run(
        [PY, str(target)],
        timeout=TIMEOUTS["tco_gate"],
    )
    line = next((l for l in so.splitlines() if l.strip()), "")
    return {
        "ok": rc == 0,
        "rc": rc,
        "head": line[:160],
    }


def bench_tis_report():
    target = PP / "tools" / "tis_report.py"
    if not target.is_file():
        return {"ok": False, "error": "tis_report.py missing"}
    rc, so, se = _run(
        [PY, str(target), "--summary"],
        timeout=TIMEOUTS["tis_report"],
    )
    return {
        "ok": rc == 0,
        "rc": rc,
        "stdout_lines": len([l for l in so.splitlines() if l.strip()]),
        "head": (so.strip().splitlines() or [""])[0][:160],
    }


def bench_osa_dispatcher():
    target = PP / "modules" / "osa" / "dispatcher.py"
    if not target.is_file():
        return {"ok": False, "error": "modules/osa/dispatcher.py missing"}
    rc, so, se = _run(
        [PY, str(target), "--check"],
        timeout=TIMEOUTS["osa_dispatcher"],
    )
    return {
        "ok": rc == 0,
        "rc": rc,
        "head": (so.strip().splitlines() or [""])[0][:160],
        "stderr_head": se.strip()[:160],
    }


def bench_proactive():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP}');"
        "t0 = time.perf_counter();"
        "from modules.pp_agents.proactive_dispatcher import dispatch;"
        "ctx = {'project':'bench','last_written_code':'',"
        "'last_written_file':'','current_error':'',"
        "'session_had_errors': False,'errors_fixed':0};"
        "r = dispatch(ctx);"
        "print(json.dumps({'advisories': len(r), "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run(
        [PY, "-c", script],
        timeout=TIMEOUTS["proactive"],
    )
    if rc != 0:
        return {"ok": False, "error": se.strip()[:200] or f"rc={rc}"}
    try:
        inner = json.loads(so.strip().splitlines()[-1])
        return {"ok": True, **inner}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"json parse: {exc}",
                "raw_head": so[:200]}


def bench_monitoring():
    mod = PP / "modules" / "monitoring" / "observe.py"
    if not mod.is_file():
        alt = list((PP / "modules" / "monitoring").glob("*.py"))
        if not alt:
            return {"ok": False, "error": "modules/monitoring/observe.py "
                                          "missing"}
    rc, so, se = _run(
        [PY, "-m", "modules.monitoring.observe", "--once"],
        timeout=TIMEOUTS["monitoring"],
    )
    lines = [l for l in so.splitlines() if l.strip()]
    return {
        "ok": rc == 0,
        "rc": rc,
        "stdout_lines": len(lines),
        "head": lines[0][:160] if lines else "",
        "stderr_head": se.strip()[:160] if rc != 0 else "",
    }


def bench_anti_patterns():
    sample = PP / "tools" / "ceps.py"
    if not sample.is_file():
        cands = list((PP / "tools").glob("*.py"))
        sample = cands[0] if cands else None
    if not sample:
        return {"ok": False, "error": "no scan target found"}
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP}');"
        "t0 = time.perf_counter();"
        "from modules.uqf.anti_patterns import run_all;"
        f"code = open(r'{sample}', encoding='utf-8').read();"
        "hits = run_all(code);"
        "total = sum(len(v) for v in hits.values());"
        "print(json.dumps({'total_hits': total, "
        "'categories': len(hits), "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1), "
        f"'target': r'{sample.name}'}}))"
    )
    rc, so, se = _run(
        [PY, "-c", script],
        timeout=TIMEOUTS["anti_patterns"],
    )
    if rc != 0:
        return {"ok": False, "error": se.strip()[:200] or f"rc={rc}"}
    try:
        return {"ok": True, **json.loads(so.strip().splitlines()[-1])}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"json parse: {exc}",
                "raw_head": so[:200]}


def bench_ceps():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP}');"
        "t0 = time.perf_counter();"
        "from tools.ceps import record_error;"
        "record_error('benchmark_test', 'bench', 'perf test', True);"
        "print(json.dumps({"
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run(
        [PY, "-c", script],
        timeout=TIMEOUTS["ceps"],
    )
    if rc != 0:
        return {"ok": False, "error": se.strip()[:200] or f"rc={rc}"}
    try:
        return {"ok": True, **json.loads(so.strip().splitlines()[-1])}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"json parse: {exc}",
                "raw_head": so[:200]}


def bench_hub_invoke():
    hub = PP / "hooks" / "session_start_hub.js"
    if not hub.is_file():
        return {"ok": False, "error": "hooks/session_start_hub.js missing"}
    rc, so, se = _run(
        ["node", str(hub)],
        timeout=TIMEOUTS["hub_invoke"],
        input_bytes=b"{}",
    )
    payload = None
    try:
        payload = json.loads(so.strip())
    except Exception:  # noqa: BLE001
        payload = None
    return {
        "ok": rc == 0,
        "rc": rc,
        "stdout_bytes": len(so),
        "stdout_json_valid": payload is not None,
        "emit_additional_context": bool(payload and
                                        "additionalContext" in payload),
    }


def bench_never_again():
    script = (
        f"import sys, json, time;"
        f"sys.path.insert(0, r'{PP}');"
        "t0 = time.perf_counter();"
        "from modules.osa.never_again import top_recurring;"
        "rows = top_recurring(10);"
        "print(json.dumps({'rows': len(rows), "
        "'inner_ms': round((time.perf_counter()-t0)*1000, 1)}))"
    )
    rc, so, se = _run(
        [PY, "-c", script],
        timeout=TIMEOUTS["never_again"],
    )
    if rc != 0:
        return {"ok": False, "error": se.strip()[:200] or f"rc={rc}"}
    try:
        return {"ok": True, **json.loads(so.strip().splitlines()[-1])}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"json parse: {exc}",
                "raw_head": so[:200]}


BENCHMARKS = [
    ("1_session_start", bench_session_start),
    ("2_jit_loader_cold", bench_jit_cold),
    ("3_uqf_scan", bench_uqf_scan),
    ("4_verify_spp", bench_verify_spp),
    ("5_pytest", bench_pytest),
    ("6_vgate_suites", bench_vgate_suites),
    ("7_tco_gate", bench_tco_gate),
    ("8_tis_report", bench_tis_report),
    ("9_osa_dispatcher", bench_osa_dispatcher),
    ("10_proactive", bench_proactive),
    ("11_monitoring", bench_monitoring),
    ("12_anti_patterns", bench_anti_patterns),
    ("13_ceps", bench_ceps),
    ("14_hub_invoke", bench_hub_invoke),
    ("15_never_again", bench_never_again),
]


def main():
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_path = PP / "vault" / "benchmarks" / f"audit_run_{iso}.json"
    results = {
        "timestamp_iso": iso,
        "host_os": os.name,
        "python_version": sys.version.split()[0],
        "pp_path": str(PP),
        "benchmarks": {},
    }

    for name, fn in BENCHMARKS:
        print(f"[{name}] running...", flush=True)
        t0 = _ms()
        try:
            payload = fn()
        except Exception as exc:  # noqa: BLE001
            payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        outer_ms = round(_ms() - t0, 0)
        payload["outer_ms"] = outer_ms
        results["benchmarks"][name] = payload
        verdict = "ok" if payload.get("ok") else "ERR"
        print(f"[{name}] {verdict}  outer_ms={outer_ms}", flush=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
