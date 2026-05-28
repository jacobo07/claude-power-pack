#!/usr/bin/env python3
"""V-* gates for OSA (throttle + never_again + gpu_eyes + dispatcher
+ TCO context-proxy cross-checks).

Isolated tmpdir per test where possible. Live vault/osa/ is never
mutated by these tests. Each V-* prints PASS/FAIL with a one-line
diagnostic, then a final OSA_PASS=N/M summary. Exit 0 iff all gates
PASS.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

passes = 0
fails = 0


def _ok(name: str, msg: str = "") -> None:
    global passes
    passes += 1
    print(f"PASS  {name:32s} {msg}")


def _fail(name: str, msg: str = "") -> None:
    global fails
    fails += 1
    print(f"FAIL  {name:32s} {msg}")


def _isolate_osa(tmp: Path) -> tuple:
    """Reload modules.osa.{throttle, never_again, dispatcher} with
    storage redirected into tmp/. Returns (throttle, never_again,
    dispatcher) module references."""
    osa_dir = tmp / "vault" / "osa"
    osa_dir.mkdir(parents=True, exist_ok=True)
    kb_dir = tmp / "vault" / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    ceps_dir = tmp / "vault" / "ceps"
    ceps_dir.mkdir(parents=True, exist_ok=True)
    tok_dir = tmp / "vault" / "token_logs"
    tok_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "throttle": {
            "max_daily_calls": 150,
            "cooldown_minutes": 30,
            "cache_ttl_minutes": 60,
        },
        "triggers": {
            "T3_error_cluster_threshold": 3,
            "T4_session_timer_minutes": 120,
        },
        "gpu_eyes": {
            "host": "0.0.0.0",  # always unreachable
            "ssh_user": "root",
            "ssh_timeout_sec": 1,
            "display": ":98",
            "screen_geometry": "1920x1080x24",
            "graceful_degradation": True,
        },
    }
    (osa_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8")

    # Touch session_id with NOW so T4 does not fire (we test sleepy state)
    (tok_dir / ".session_id").write_text("osa-test-session", encoding="utf-8")
    # Adjust mtime to now (default behavior)

    import modules.osa.throttle as t
    importlib.reload(t)
    t.CONFIG_PATH = osa_dir / "config.json"
    t.BUDGET_DIR = osa_dir

    import modules.osa.never_again as n
    importlib.reload(n)
    n.LOG_PATH = osa_dir / "never_again_log.jsonl"
    n.SESSION_LESSONS = kb_dir / "session_lessons.md"
    n.UKDL_PATH = kb_dir / "ukdl-universal.md"

    import modules.osa.gpu_eyes as g
    importlib.reload(g)
    g.CONFIG_PATH = osa_dir / "config.json"

    import modules.osa.dispatcher as d
    importlib.reload(d)
    d.OSA_CFG = osa_dir / "config.json"
    d.OMNI_CFG = tmp / "modules" / "omnicapture" / "config.json"
    d.CEPS_EVENTS = ceps_dir / "events.jsonl"
    d.DEPLOYS_DIR = tmp / "vault" / "deploys"
    d.ROLLBACKS_DIR = tmp / "vault" / "rollbacks"
    d.SESSION_ID_FILE = tok_dir / ".session_id"

    return t, n, g, d


def _isolated_tis(tmp: Path) -> tuple:
    """Point tis at a tmp logs dir for the TCO cross-checks."""
    import tools.tis as _tis_pkg
    import tis as _tis
    importlib.reload(_tis)
    logs = tmp / "token_logs"
    logs.mkdir(parents=True, exist_ok=True)
    _tis.LOGS_DIR = logs
    _tis.SESSION_FILE = logs / ".session_id"
    try:
        _tis_pkg.LOGS_DIR = logs
        _tis_pkg.SESSION_FILE = logs / ".session_id"
    except Exception:
        pass
    sid = "osa-tco-session"
    (logs / ".session_id").write_text(sid, encoding="utf-8")
    return _tis, logs, sid


def _make_tis_event(logs: Path, in_tok: int, out_tok: int, sid: str) -> None:
    ts = datetime.now(timezone.utc)
    day = ts.date().isoformat()
    p = logs / f"{day}.jsonl"
    row = {
        "session_id": sid,
        "timestamp_iso": ts.isoformat(),
        "skill_name": "test",
        "model": "claude-opus-4-7",
        "input_tokens": int(in_tok),
        "output_tokens": int(out_tok),
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "call_label": "test",
        "project": "osa-test",
    }
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="osa-test-"))
    print(f"[isolate] tmp={tmp}")

    try:
        throttle, never_again, gpu_eyes, dispatcher = _isolate_osa(tmp)

        # ---- V-OSA-CONFIG ----
        cfg = throttle._load_throttle_config()
        if cfg["max_daily_calls"] == 150 and cfg["cooldown_minutes"] == 30:
            _ok("V-OSA-CONFIG",
                f"max_daily={cfg['max_daily_calls']} cooldown={cfg['cooldown_minutes']}min")
        else:
            _fail("V-OSA-CONFIG", f"got {cfg!r}")

        # ---- V-OSA-THROTTLE-GO ----
        throttle.reset_today()
        result = throttle.check("v-test-go")
        if result == "GO":
            _ok("V-OSA-THROTTLE-GO", "cold state -> GO")
        else:
            _fail("V-OSA-THROTTLE-GO", f"got {result!r}")

        # ---- V-OSA-THROTTLE-CACHE ----
        throttle.consume("v-test-cache", "test summary")
        result = throttle.check("v-test-cache")
        if result.startswith("CACHE_HIT"):
            _ok("V-OSA-THROTTLE-CACHE", f"-> {result}")
        else:
            _fail("V-OSA-THROTTLE-CACHE", f"got {result!r}")

        # ---- V-OSA-THROTTLE-BUDGET ----
        # Force calls=150 and verify BUDGET_EXHAUSTED
        b = throttle._load_budget()
        b["calls"] = 150
        b["cache"] = {}  # clear cache to force budget check
        throttle._save_budget(b)
        result = throttle.check("v-test-budget")
        if result == "BUDGET_EXHAUSTED":
            _ok("V-OSA-THROTTLE-BUDGET", "-> BUDGET_EXHAUSTED")
        else:
            _fail("V-OSA-THROTTLE-BUDGET", f"got {result!r}")

        # ---- V-OSA-THROTTLE-CONFIG: change max via config, verify ----
        # Set max=2, consume 2 -> exhausted
        # Write modified config
        cfg_path = tmp / "vault" / "osa" / "config.json"
        new_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        new_cfg["throttle"]["max_daily_calls"] = 2
        cfg_path.write_text(json.dumps(new_cfg, indent=2), encoding="utf-8")
        throttle.reset_today()
        throttle.consume("v-test-cfg")
        throttle.consume("v-test-cfg")
        # Need to clear cache to test budget gate (consume sets cache)
        b = throttle._load_budget()
        b["cache"] = {}
        throttle._save_budget(b)
        result = throttle.check("brand-new-project")
        if result == "BUDGET_EXHAUSTED":
            _ok("V-OSA-THROTTLE-CONFIG",
                "config.json max=2 -> exhausts at 2 calls")
        else:
            _fail("V-OSA-THROTTLE-CONFIG", f"got {result!r}")
        # restore config max
        new_cfg["throttle"]["max_daily_calls"] = 150
        cfg_path.write_text(json.dumps(new_cfg, indent=2), encoding="utf-8")
        throttle.reset_today()

        # ---- V-OSA-NEVER-INJECT ----
        entry = never_again.inject(
            issue="OSA test injection alpha",
            root_cause="root alpha",
            fix="fix alpha",
            recognizer="recognizer alpha",
            severity="MEDIUM",
        )
        log_rows = never_again._read_log()
        if entry.recurrence == 1 and len(log_rows) == 1:
            _ok("V-OSA-NEVER-INJECT", f"jsonl rows={len(log_rows)}")
        else:
            _fail("V-OSA-NEVER-INJECT",
                  f"recurrence={entry.recurrence} rows={len(log_rows)}")

        # ---- V-OSA-NEVER-RECUR ----
        entry2 = never_again.inject(
            issue="OSA test injection alpha",
            root_cause="same root cause",
            fix="same fix",
            recognizer="same recognizer",
        )
        log_rows = never_again._read_log()
        if entry2.recurrence == 2 and len(log_rows) == 1:
            _ok("V-OSA-NEVER-RECUR",
                f"recurrence={entry2.recurrence} jsonl rows={len(log_rows)}")
        else:
            _fail("V-OSA-NEVER-RECUR",
                  f"recurrence={entry2.recurrence} rows={len(log_rows)}")

        # ---- V-OSA-GPU-SKIP ----
        # host=0.0.0.0 is configured to be unreachable -> SKIPPED
        result = gpu_eyes.run_visual_qa("test-project", "test-intent")
        if (result.get("status") in {"SKIPPED", "CAPTURE_FAILED"}
                and result.get("visual_qa_passed") is None
                and result.get("screenshot") is None):
            _ok("V-OSA-GPU-SKIP",
                f"status={result['status']} passed={result['visual_qa_passed']}")
        else:
            _fail("V-OSA-GPU-SKIP", f"got {result!r}")

        # ---- V-OSA-DISPATCHER-SLEEP ----
        # Fresh session_id (mtime=now) + no CEPS events + no receipts
        # -> all triggers off -> sleepy
        throttle.reset_today()
        active, reason, payload = dispatcher.should_activate("test-project")
        if not active and reason == "sleepy":
            _ok("V-OSA-DISPATCHER-SLEEP", f"reason={reason}")
        else:
            _fail("V-OSA-DISPATCHER-SLEEP",
                  f"active={active} reason={reason}")

        # ---- V-OSA-DISPATCHER-T3 ----
        # Write 3 distinct CEPS events with NOW timestamps -> T3 fires
        ceps_path = dispatcher.CEPS_EVENTS
        ceps_path.parent.mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now(timezone.utc).isoformat()
        with ceps_path.open("w", encoding="utf-8") as fh:
            for cat, sub in [("compile", "x"), ("runtime", "y"), ("net", "z")]:
                fh.write(json.dumps({
                    "timestamp_iso": now_iso,
                    "category": cat,
                    "subsystem": sub,
                }) + "\n")
        triggers = dispatcher.evaluate_triggers()
        t3 = triggers["T3_ERROR_CLUSTER"]
        if t3["fired"] and t3["distinct_count"] >= 3:
            _ok("V-OSA-DISPATCHER-T3",
                f"distinct={t3['distinct_count']} threshold={t3['threshold']}")
        else:
            _fail("V-OSA-DISPATCHER-T3", f"got {t3!r}")

        # ---- V-OSA-DISPATCHER-PROJ ----
        proj = dispatcher._resolve_project()
        if proj and isinstance(proj, str) and proj.strip():
            _ok("V-OSA-DISPATCHER-PROJ", f"resolved={proj!r}")
        else:
            _fail("V-OSA-DISPATCHER-PROJ", f"got {proj!r}")

        # ---- V-OSA-NONBLOCKING ----
        # fire_async must return immediately even if dispatcher work is heavy.
        import time
        t0 = time.monotonic()
        dispatcher.fire_async("test-project", "test-hook")
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        if elapsed_ms < 200:
            _ok("V-OSA-NONBLOCKING", f"returned in {elapsed_ms}ms")
        else:
            _fail("V-OSA-NONBLOCKING", f"blocked {elapsed_ms}ms")

        # ---- V-TCO-CONTEXT-SINGLE (cross-check) ----
        _tis, logs, sid = _isolated_tis(tmp / "tco-single")
        import tco_compact_gate as gate
        importlib.reload(gate)
        for _ in range(5):
            _make_tis_event(logs, in_tok=10000, out_tok=0, sid=sid)
        state = gate.check_compact_gate(sid)
        if (state["session_pct_estimate"] <= 10
                and state["context_max_single_input"] == 10000
                and not state["should_compact"]):
            _ok("V-TCO-CONTEXT-SINGLE",
                f"pct={state['session_pct_estimate']}% max_single=10000")
        else:
            _fail("V-TCO-CONTEXT-SINGLE", f"state={state}")

        # ---- V-TCO-CONTEXT-REAL (cross-check) ----
        _tis2, logs2, sid2 = _isolated_tis(tmp / "tco-real")
        importlib.reload(gate)
        _make_tis_event(logs2, in_tok=170000, out_tok=0, sid=sid2)
        state = gate.check_compact_gate(sid2)
        if (80 <= state["session_pct_estimate"] <= 90
                and state["context_max_single_input"] == 170000
                and state["should_compact"]):
            _ok("V-TCO-CONTEXT-REAL",
                f"pct={state['session_pct_estimate']}% max_single=170000")
        else:
            _fail("V-TCO-CONTEXT-REAL", f"state={state}")

        # ---- V-BASELINE-INTACT ----
        pyt = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=240,
        )
        last = (pyt.stdout.strip().splitlines() or [""])[-1]
        if pyt.returncode == 0 and "passed" in last:
            _ok("V-BASELINE-INTACT", f"rc=0 last='{last}'")
        else:
            _fail("V-BASELINE-INTACT",
                  f"rc={pyt.returncode} last='{last}'")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = passes + fails
    print()
    print(f"OSA_PASS={passes}/{total}  threshold=15/15")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
