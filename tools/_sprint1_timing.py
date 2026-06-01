"""PASO 0 -- empirical timing of Sprint 1 quick-win tools.
Determines wiring mechanism by real cold-run latency. Analytical harness (one-shot).
Heavy miners (miner_v2, sovereign_miner) are NOT executed: audit already classes them F,
and the global Background-Process-Hygiene rule forbids spawning orphan-prone distillers to "time" them.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
PY = sys.executable

# (name, argv-after-python, sess_start_sensible)
TOOLS = [
    ("cache_hint_apply",    ["tools/cache_hint_apply.py", "--quiet", "--as-json"], True),
    ("check_hook_status",   ["tools/check_hook_status.py"], False),
    ("compound_audit",      ["tools/compound_audit.py"], False),
    ("drift_report",        ["tools/drift_report.py"], True),
    ("lazarus_orphan_purge",["tools/lazarus_orphan_purge.py", "--json"], True),
    ("resume_reindex",      ["tools/resume_reindex.py"], True),
    ("session-snapshot",    ["tools/session-snapshot.py"], False),
    ("vault_summarize",     ["tools/vault_summarize.py", "--check"], False),
    ("jit_ref_correlate",   ["tools/jit_ref_correlate.py"], False),
    ("normalize_paths",     ["tools/normalize_paths.py", "--check"], False),
    ("oracle_heartbeat",    ["tools/oracle_heartbeat.py", "--pid"], False),
]
SKIPPED_HEAVY = ["miner_v2", "sovereign_miner"]

def classify(ms):
    if ms is None:
        return "ERROR"
    if ms < 200:
        return "HOOK-OK"
    if ms < 1000:
        return "WARN(B-signal)"
    return "DAEMON-ONLY(F)"

results = []
print("=== SPRINT 1 TIMING (real cold runs) ===")
for name, argv, sess in TOOLS:
    t0 = time.perf_counter()
    rc = None
    err = None
    try:
        r = subprocess.run([PY] + argv, capture_output=True, text=True,
                           timeout=12, cwd=str(PP))
        rc = r.returncode
        ms = (time.perf_counter() - t0) * 1000
    except subprocess.TimeoutExpired:
        ms = 12000.0
        err = "timeout>12s"
    except Exception as e:  # noqa: BLE001 - harness must never crash
        ms = None
        err = str(e)[:80]
    verdict = classify(ms)
    results.append({"name": name, "ms": None if ms is None else round(ms, 1),
                    "rc": rc, "verdict": verdict, "sess_start": sess, "err": err})
    msd = "  err" if ms is None else f"{ms:6.0f}ms"
    print(f"{msd}  {verdict:16s}  rc={rc}  {name}{'  ['+err+']' if err else ''}")

for name in SKIPPED_HEAVY:
    results.append({"name": name, "ms": None, "rc": None,
                    "verdict": "DAEMON-ONLY(F) [not-run: orphan-risk]",
                    "sess_start": False, "err": "skipped per hygiene rule"})
    print(f"  skip  DAEMON-ONLY(F)   {name}  [audit-classified F; not executed]")

hook_safe = sorted([r["name"] for r in results if r["verdict"] == "HOOK-OK"])
warn = sorted([r["name"] for r in results if r["verdict"].startswith("WARN")])
daemon = sorted([r["name"] for r in results if r["verdict"].startswith("DAEMON")])
err = sorted([r["name"] for r in results if r["verdict"] == "ERROR"])

print("\nHOOK-OK (<200ms)    :", hook_safe)
print("WARN 200-1000 (B)   :", warn)
print("DAEMON >1s (F)      :", daemon)
print("ERROR               :", err)

ISO = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
outdir = PP / "vault" / "benchmarks"
outdir.mkdir(parents=True, exist_ok=True)
outp = outdir / f"sprint1_timing_{ISO}.json"
outp.write_text(json.dumps({
    "generated": datetime.now(timezone.utc).isoformat(),
    "results": results,
    "buckets": {"hook_safe": hook_safe, "warn_b": warn, "daemon_f": daemon, "error": err},
}, indent=2), encoding="utf-8")
print("\nSaved:", outp)
