#!/usr/bin/env python3
"""V-* gates for TCO (Compact Gate + Model Router + cost-projection).

Isolated tmpdir per test so the live vault/token_logs/ is never touched.
Each V-* prints PASS/FAIL with a one-line diagnostic, then a final
TCO_PASS=N/M summary. Exit 0 iff all gates PASS."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT))

passes = 0
fails = 0


def _ok(name, msg=""):
    global passes
    passes += 1
    print(f"PASS  {name:30s} {msg}")


def _fail(name, msg=""):
    global fails
    fails += 1
    print(f"FAIL  {name:30s} {msg}")


def _make_event(tmp_logs: Path, in_tok: int, out_tok: int,
                model: str = "claude-opus-4-7",
                skill: str = "test-skill",
                session_id: str = "tco-test-session",
                hours_ago: float = 0.0):
    """Append a single event JSONL line to today's log in tmpdir."""
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    day = ts.date().isoformat()
    p = tmp_logs / f"{day}.jsonl"
    obj = {
        "session_id": session_id,
        "timestamp_iso": ts.isoformat(),
        "skill_name": skill,
        "model": model,
        "input_tokens": int(in_tok),
        "output_tokens": int(out_tok),
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "call_label": "test",
        "project": "tco-test",
    }
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj) + "\n")
    return p


def _isolated_tis(tmp_root: Path):
    """Point tis module at a tmp logs dir. Returns (tis_module,
    logs_dir, session_id).

    Note: Python 3 namespace packages create distinct module instances
    for `import tis` vs `from tools import tis`. The compact gate uses
    the second form first, so we MUST override both to isolate fully."""
    import importlib
    import tis as _tis
    importlib.reload(_tis)
    logs = tmp_root / "token_logs"
    logs.mkdir(parents=True, exist_ok=True)
    _tis.LOGS_DIR = logs
    _tis.SESSION_FILE = logs / ".session_id"
    try:
        from tools import tis as _tis_pkg  # namespace-package twin
        _tis_pkg.LOGS_DIR = logs
        _tis_pkg.SESSION_FILE = logs / ".session_id"
    except (ImportError, ModuleNotFoundError):
        pass
    sid = "tco-test-session"
    (logs / ".session_id").write_text(sid, encoding="utf-8")
    return _tis, logs, sid


def main():
    tmp = Path(tempfile.mkdtemp(prefix="tco-test-"))
    print(f"[isolate] tmp={tmp}")

    try:
        _tis, logs, sid = _isolated_tis(tmp)

        # Force tco_compact_gate to use isolated tis (same sys.path).
        import importlib
        import tco_compact_gate as gate
        importlib.reload(gate)

        # ---- V-COMPACT-OK: small log, well under 70% ----
        _make_event(logs, in_tok=5000, out_tok=1000, session_id=sid)
        state = gate.check_compact_gate(sid)
        if (not state["should_compact"]
                and state["session_pct_estimate"] < 70):
            _ok("V-COMPACT-OK",
                f"pct={state['session_pct_estimate']}% rec=OK")
        else:
            _fail("V-COMPACT-OK",
                  f"state={state}")

        # ---- V-COMPACT-WARN: push to >=70% ----
        # MAX_CONTEXT_TOKENS = 200_000 -> need >=140k accumulated
        _make_event(logs, in_tok=140000, out_tok=0,
                    session_id=sid)
        state = gate.check_compact_gate(sid)
        if (state["should_compact"]
                and state["session_pct_estimate"] >= 70
                and "WARN" in state["recommendation"]):
            _ok("V-COMPACT-WARN",
                f"pct={state['session_pct_estimate']}% rec=WARN")
        else:
            _fail("V-COMPACT-WARN",
                  f"state={state}")

        # ---- V-COMPACT-HARD: high pct AND governor warnings stack ----
        # Add a 3-hour-old event to trigger duration warning.
        _make_event(logs, in_tok=200, out_tok=200,
                    session_id=sid, hours_ago=3.0)
        state = gate.check_compact_gate(sid)
        if (state["should_compact"]
                and state["governor_warnings"]
                and any("duration" in w for w in state["governor_warnings"])):
            _ok("V-COMPACT-HARD",
                f"governor={len(state['governor_warnings'])} warns")
        else:
            _fail("V-COMPACT-HARD",
                  f"governor warnings missing: {state['governor_warnings']}")

        # ---- V-ROUTE-SONNET: subagent_explore -> sonnet ----
        rec = gate.load_routing("subagent_explore")
        if "sonnet" in rec:
            _ok("V-ROUTE-SONNET", f"-> {rec}")
        else:
            _fail("V-ROUTE-SONNET", f"-> {rec}")

        # ---- V-ROUTE-OPUS: arch_decision -> opus ----
        rec = gate.load_routing("arch_decision")
        if "opus" in rec:
            _ok("V-ROUTE-OPUS", f"-> {rec}")
        else:
            _fail("V-ROUTE-OPUS", f"-> {rec}")

        # ---- V-ROUTE-DEFAULT: unknown -> default opus ----
        rec = gate.load_routing("definitely_not_a_real_task_type")
        if "opus" in rec:
            _ok("V-ROUTE-DEFAULT", f"-> {rec}")
        else:
            _fail("V-ROUTE-DEFAULT", f"-> {rec}")

        # ---- V-PROJECTION: --cost-projection emits expected field ----
        proj = subprocess.run(
            [sys.executable, str(TOOLS / "tis_report.py"),
             "--cost-projection"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if (proj.returncode == 0
                and "estimated_savings_pct" in proj.stdout
                and "top_3_routing_opportunities" in proj.stdout):
            _ok("V-PROJECTION",
                f"rc=0 fields=ok")
        else:
            _fail("V-PROJECTION",
                  f"rc={proj.returncode} stdout-head={proj.stdout[:120]!r}")

        # ---- V-BASELINE-INTACT: pytest tests/ still passes ----
        pyt = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=180,
        )
        last = pyt.stdout.strip().splitlines()[-1] if pyt.stdout.strip() else ""
        if pyt.returncode == 0 and "passed" in last:
            _ok("V-BASELINE-INTACT", f"rc=0 last='{last}'")
        else:
            _fail("V-BASELINE-INTACT",
                  f"rc={pyt.returncode} last='{last}'")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = passes + fails
    print()
    print(f"TCO_PASS={passes}/{total}  threshold=8/8")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
