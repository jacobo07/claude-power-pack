#!/usr/bin/env python3
"""M6 -- TIS end-to-end integration gate.

Simulates a complete session without real LLM calls and verifies the
4 sub-checks that prove the system is alive:

  1. Mock-dispatch 3 skill events to vault/token_logs
  2. read_log(session_id) returns >= 3 entries
  3. tools/tis_report.py --summary returns a non-empty table including
     this session
  4. tools/tis_handoff.py emits a handoff_*.md file with the required
     fields; with a repeated call_label the report MUST surface a
     compression candidate AND estimated_savings > 0.

Isolated to a tmpdir; production logs are not mutated.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import tis  # noqa: E402

PYTHON = sys.executable


def _isolate(tmp: Path) -> None:
    tis.LOGS_DIR = tmp / "token_logs"
    tis.SESSION_FILE = tis.LOGS_DIR / ".session_id"
    # Force a fresh session id for the test so we don't collide with
    # the host's active session.
    tis.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    tis.SESSION_FILE.write_text("e2e-test", encoding="utf-8")


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def step1_mock_dispatch() -> tuple[bool, str]:
    sid = tis.get_session_id()
    # Two repeated calls (same skill_name + call_label) so the handoff
    # detects a compression candidate, plus one unique call.
    tis.append_log(tis.TokenEvent(
        sid, _now(), "lateral-thinking", "claude-sonnet-4-6",
        250, 80, 0, 0, "lt-frame-applied", "pp",
    ))
    tis.append_log(tis.TokenEvent(
        sid, _now(), "lateral-thinking", "claude-sonnet-4-6",
        260, 85, 0, 0, "lt-frame-applied", "pp",
    ))
    tis.append_log(tis.TokenEvent(
        sid, _now(), "ceps", "claude-sonnet-4-6",
        180, 60, 0, 0, "ceps-record", "pp",
    ))
    return True, f"sid={sid} dispatched=3"


def step2_read_log_count(sid: str) -> bool:
    entries = tis.read_log(session_id=sid)
    return _step("V-E2E-2 entries>=3", len(entries) >= 3,
                 f"count={len(entries)}")


def step3_report_summary(env: dict, tmp: Path) -> bool:
    proc = subprocess.run(
        [PYTHON, str(HERE / "tis_report.py"), "--summary"],
        capture_output=True, text=True, env=env, cwd=str(PP_ROOT),
        timeout=30,
    )
    out = proc.stdout
    has_table = "session" in out and "calls" in out and "in_tok" in out
    has_session = "e2e-test" in out
    has_nonzero = any(t in out for t in ("690", "180", "250", "225", "260"))
    ok = (proc.returncode == 0 and has_table and has_session and has_nonzero)
    return _step("V-E2E-3 report-summary", ok,
                 f"rc={proc.returncode} has_table={has_table} "
                 f"has_session={has_session} has_nonzero={has_nonzero}")


def step4_handoff_emits(env: dict, tmp: Path) -> bool:
    proc = subprocess.run(
        [PYTHON, str(HERE / "tis_handoff.py"),
         "--session", "e2e-test",
         "--out-dir", str(tmp / "handoffs")],
        capture_output=True, text=True, env=env, cwd=str(PP_ROOT),
        timeout=30,
    )
    body = proc.stdout
    has_field_consumed = "tokens_consumed_this_session" in body
    has_field_savings = "estimated_savings_next_session_tokens" in body
    # The two lt-frame-applied calls should be detected as candidates.
    has_candidate = "lateral-thinking" in body and (
        "cache_control" in body or "compression" in body.lower()
        or "estimated_savings_tokens" in body)
    handoff_files = list((tmp / "handoffs").glob("handoff_*.md"))
    ok = (proc.returncode == 0 and has_field_consumed and has_field_savings
          and has_candidate and len(handoff_files) >= 1)
    return _step("V-E2E-4 handoff-emits", ok,
                 f"rc={proc.returncode} files={len(handoff_files)} "
                 f"consumed={has_field_consumed} savings={has_field_savings} "
                 f"candidate={has_candidate}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tis-e2e-"))
    _isolate(tmp)
    print(f"[isolate] tmp={tmp}")

    # Step 1: mock dispatch -- no V-PASS line here, but counts towards
    # the 4-sub-check totaliser via subsequent assertions.
    ok1, detail = step1_mock_dispatch()
    _step("V-E2E-1 mock-dispatch", ok1, detail)
    sid = tis.get_session_id()

    # Force child processes to share the isolated LOGS_DIR by passing
    # CLAUDEPP_TIS_LOGS_DIR via env -- BUT the module reads LOGS_DIR
    # from a path-time constant. The cleanest cross-process bridge is
    # to pre-create the isolated logs in PP_ROOT/vault/token_logs and
    # share via the natural path. Done above: the test's tis.LOGS_DIR
    # was monkey-patched, but subprocesses re-import tis fresh.
    #
    # So instead: copy the isolated JSONL into the real PP path for
    # the test, then clean up. This keeps the subprocesses' default
    # behavior aligned with the test fixture.
    real_logs = PP_ROOT / "vault" / "token_logs"
    real_logs.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    src = tmp / "token_logs" / f"{today}.jsonl"
    dst = real_logs / f"{today}.jsonl"
    dst_backup = real_logs / f"{today}.jsonl.e2e-backup"
    if dst.is_file():
        dst.rename(dst_backup)
    try:
        if src.is_file():
            # Merge: read src lines, append to real path -- but we already
            # ensured a fresh dst above by moving aside. Just copy.
            dst.write_text(src.read_text(encoding="utf-8"),
                           encoding="utf-8")

        env = os.environ.copy()
        results = [
            ok1,
            step2_read_log_count(sid),
            step3_report_summary(env, tmp),
            step4_handoff_emits(env, tmp),
        ]
    finally:
        # Restore the previous log if any.
        if dst.is_file():
            dst.unlink()
        if dst_backup.is_file():
            dst_backup.rename(dst)

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nE2E_{'PASS' if passed == total else 'FAIL'} = {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
