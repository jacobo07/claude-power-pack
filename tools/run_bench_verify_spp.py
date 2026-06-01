"""run_bench_verify_spp.py -- verify_spp.py timing with 300s budget."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
PY = sys.executable

t0 = time.perf_counter()
try:
    r = subprocess.run(
        [PY, str(PP / "tools" / "verify_spp.py")],
        capture_output=True,
        timeout=300,
        env=os.environ.copy(),
        cwd=str(PP),
    )
    rc = r.returncode
    so = r.stdout.decode("utf-8", "replace")
    se = r.stderr.decode("utf-8", "replace")
    timed_out = False
except subprocess.TimeoutExpired as exc:
    rc = -1
    so = (exc.stdout or b"").decode("utf-8", "replace")
    se = (exc.stderr or b"").decode("utf-8", "replace")
    timed_out = True

wall_ms = round((time.perf_counter() - t0) * 1000, 0)
combined = so + se
pass_count = combined.count("PASS")
fail_count = combined.count("FAIL")
ok_count = combined.count(" OK ")

iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
out_path = PP / "vault" / "benchmarks" / f"audit_verify_spp_{iso}.json"
payload = {
    "timestamp_iso": iso,
    "rc": rc,
    "timed_out": timed_out,
    "wall_ms": wall_ms,
    "pass_count": pass_count,
    "fail_count": fail_count,
    "ok_count": ok_count,
    "stdout_tail": "\n".join(so.strip().splitlines()[-15:])[:1500],
    "stderr_head": se.strip()[:400],
}
out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"rc={rc} wall_ms={wall_ms} pass={pass_count} fail={fail_count}")
print(f"wrote {out_path}")
