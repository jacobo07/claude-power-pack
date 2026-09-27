#!/usr/bin/env python3
"""V-* gates for TCO (Compact Gate + Model Router + cost-projection).

Isolated tmpdir per test so the live vault/token_logs/ is never touched.
Each V-* prints PASS/FAIL with a one-line diagnostic, then a final
TCO_PASS=N/M summary. Exit 0 iff all gates PASS."""
from __future__ import annotations
import json
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

        # ---- V-COMPACT-CONTEXT-SINGLE: 5 calls of 10k each ----
        # Cumulative SUM would be 50k = 25%; new MAX-of-recent proxy
        # uses max(input_tokens) = 10k = 5% (the correct context proxy).
        # Sealed 2026-05-28 after the cumulative-sum bug fix.
        ctx_sid = "tco-test-context-single"
        for _ in range(5):
            _make_event(logs, in_tok=10000, out_tok=0, session_id=ctx_sid)
        state = gate.check_compact_gate(ctx_sid)
        if (state["session_pct_estimate"] <= 10
                and state["context_max_single_input"] == 10000
                and state["session_calls"] == 5
                and not state["should_compact"]):
            _ok("V-COMPACT-CONTEXT-SINGLE",
                f"pct={state['session_pct_estimate']}% "
                f"max_single={state['context_max_single_input']}")
        else:
            _fail("V-COMPACT-CONTEXT-SINGLE",
                  f"expected pct<=10 & max_single=10000 & calls=5 & no-compact, "
                  f"got state={state}")

        # ---- V-COMPACT-CONTEXT-REAL: 1 call of 170k -> ~85% ----
        # One large input call IS a real context-full scenario.
        # New proxy must reflect this (170k/200k = 85%).
        real_sid = "tco-test-context-real"
        _make_event(logs, in_tok=170000, out_tok=0, session_id=real_sid)
        state = gate.check_compact_gate(real_sid)
        if (80 <= state["session_pct_estimate"] <= 90
                and state["context_max_single_input"] == 170000
                and state["should_compact"]
                and "WARN" in state["recommendation"]):
            _ok("V-COMPACT-CONTEXT-REAL",
                f"pct={state['session_pct_estimate']}% "
                f"max_single={state['context_max_single_input']}")
        else:
            _fail("V-COMPACT-CONTEXT-REAL",
                  f"expected pct in [80,90] & max_single=170000 & WARN, "
                  f"got state={state}")

        # ---- V-TCO-MEASURED-*: transcript usage is the source when the session is known ----
        # 2026-09-27: the TIS log held no model usage (JIT prompt-size estimates) under a
        # never-rotated sidecar id. Driven under a synthetic home so the real transcript
        # of whoever runs this suite is never read.
        import json as _json, os as _os
        fake_home = tmp / "home"
        tsid = "0123abcd-0000-4000-8000-00000000abcd"
        proj = fake_home / ".claude" / "projects" / "p"
        proj.mkdir(parents=True)

        def _asst(mid, ctx, out=10, ts="2026-09-27T10:00:00Z"):
            return _json.dumps({"type": "assistant", "timestamp": ts, "message": {
                "id": mid, "usage": {"input_tokens": 1, "cache_creation_input_tokens": 0,
                                     "cache_read_input_tokens": ctx - 1, "output_tokens": out}}})
        (proj / f"{tsid}.jsonl").write_text("\n".join([
            _asst("m1", 189_000), _asst("m1", 189_000),  # same message twice: count once
            _asst("m2", 250_000), _asst("m3", 300_000, ts="2026-09-27T10:05:00Z")]),
            encoding="utf-8")
        saved = {k: _os.environ.get(k) for k in ("USERPROFILE", "HOME", "CPP_CONTEXT_WINDOW")}
        _os.environ["USERPROFILE"] = _os.environ["HOME"] = str(fake_home)
        _os.environ.pop("CPP_CONTEXT_WINDOW", None)
        try:
            state = gate.check_compact_gate(tsid)
            if (state.get("source", "").startswith("transcript") and state["session_calls"] == 3
                    and state["context_first_call"] == 189_000 and state["context_last_call"] == 300_000):
                _ok("V-TCO-MEASURED-SOURCE-DEDUP", f"calls=3 last={state['context_last_call']}")
            else:
                _fail("V-TCO-MEASURED-SOURCE-DEDUP", f"state={state}")
            # no settings.json in the fake home: the 1 M window is inferred from a >200 k call
            if state.get("context_window") == 1_000_000 and state["session_pct_estimate"] == 30:
                _ok("V-TCO-MEASURED-WINDOW-FROM-EVIDENCE", "300k / 1M = 30%")
            else:
                _fail("V-TCO-MEASURED-WINDOW-FROM-EVIDENCE", f"state={state}")
            _os.environ["CPP_CONTEXT_WINDOW"] = "400000"
            state = gate.check_compact_gate(tsid)
            if state["session_pct_estimate"] == 75 and state["should_compact"]:
                _ok("V-TCO-MEASURED-OVERRIDE-WARNS", "300k / 400k = 75% -> WARN")
            else:
                _fail("V-TCO-MEASURED-OVERRIDE-WARNS", f"state={state}")
            # an 8-char TIS sidecar id names no transcript: the proxy path answers, labelled
            state = gate.check_compact_gate(sid)
            if state.get("source", "").startswith("tis-proxy"):
                _ok("V-TCO-SHORT-ID-FALLS-BACK-LABELLED", state["source"])
            else:
                _fail("V-TCO-SHORT-ID-FALLS-BACK-LABELLED", f"source={state.get('source')}")
        finally:
            for k, v in saved.items():
                if v is None:
                    _os.environ.pop(k, None)
                else:
                    _os.environ[k] = v

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
        # A timeout is the INSTRUMENT failing, not a verdict on the gate: measured 2026-09-27 the
        # whole-suite run took 148.9 s once and overran 180 s twice on a loaded host, and the
        # uncaught TimeoutExpired then hid every result above it. Still red, but named.
        try:
            pyt = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
                capture_output=True, text=True, cwd=str(ROOT), timeout=180,
            )
        except subprocess.TimeoutExpired:
            pyt = None
        if pyt is None:
            _fail("V-BASELINE-INTACT",
                  "UNJUDGED: pytest tests/ exceeded 180 s -- host load, not a verdict on TCO")
        else:
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
    print(f"TCO_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
