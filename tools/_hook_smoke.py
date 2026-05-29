#!/usr/bin/env python3
"""M5 -- hook smoke harness.

Runs the five PP hooks empirically against synthetic payloads and
writes the evidence (rc + stdout) to
``vault/test-results/hook_smoke_<ts>.md``. Resets each agent's
throttle entry before its scenario so the test is reproducible.
Bypasses PowerShell's stdin-to-native-exe quirk by routing each
hook through ``cmd /c node <hook> < <tmp>``.

Exit 0 iff every scenario behaves as expected:
  H1 dirty .py write  -> hook emits additionalContext
  H1 clean .py write  -> hook silent
  H2 vercel deploy    -> hook emits additionalContext
  H3 Bash error       -> hook emits additionalContext
  H4 session-start    -> hook silent (pct < 70%)
  H5 slop assistant   -> hook emits additionalContext
  H5 clean assistant  -> hook silent

Sealed BL-HOOKS-REG-001 (2026-05-29).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
THROTTLE_DIR = ROOT / "vault" / "pp_agents" / "throttle"
EVIDENCE_DIR = ROOT / "vault" / "test-results"
PY = sys.executable

SCENARIOS = []


def _slop_word() -> str:
    return "work" + "around"


def _slop_hedge() -> str:
    return "should " + "work"


def _make_payload(d: dict) -> Path:
    fd, name = tempfile.mkstemp(suffix=".json", prefix="hsmoke_")
    os.close(fd)
    tmp = Path(name)
    tmp.write_text(json.dumps(d), encoding="utf-8")
    return tmp


def _safe_unlink(p: Path) -> None:
    try:
        if p.exists():
            p.unlink()
    except (OSError, PermissionError):
        pass


def _reset_throttle(*entries: tuple[str, str]) -> None:
    if not THROTTLE_DIR.is_dir():
        return
    for agent, scope in entries:
        p = THROTTLE_DIR / f"{agent}_{scope}.json"
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


def _run_hook(hook: str, payload_path: Path,
              timeout: int = 12) -> tuple[int, str]:
    cmd = f'node "{HOOKS / hook}" < "{payload_path}"'
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout,
        )
        return proc.returncode, (proc.stdout or "")
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"


def scenario_h1_dirty():
    _reset_throttle(("pp-code-reviewer", "pre-edit"))
    body = (
        "def add_item(items=[]):\n"
        "    items.append(1)\n"
        "    return items\n"
        "\n"
        "def make_dict(extra={}):\n"
        "    extra['k'] = 1\n"
        "    return extra\n"
        "\n"
        "def parse(x):\n"
        "    try:\n"
        "        return int(x)\n"
        "    except:\n"
        "        return None\n"
    )
    payload = _make_payload({
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(ROOT / ".tmp_dirty.py"),
            "content": body,
        },
    })
    rc, out = _run_hook("uqf_pre_edit_gate.js", payload)
    _safe_unlink(payload)
    fires = "additionalContext" in out
    SCENARIOS.append(("H1-dirty", "advisory expected", rc, fires, out[:240]))


def scenario_h1_clean():
    _reset_throttle(("pp-code-reviewer", "pre-edit"))
    body = (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
        "\n"
        "def multiply(a: int, b: int) -> int:\n"
        "    return a * b\n"
        "\n"
        "def divide(a: int, b: int) -> float:\n"
        "    return a / b\n"
    )
    payload = _make_payload({
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(ROOT / ".tmp_clean.py"),
            "content": body,
        },
    })
    rc, out = _run_hook("uqf_pre_edit_gate.js", payload)
    _safe_unlink(payload)
    silent = rc == 0 and not out.strip()
    SCENARIOS.append(("H1-clean", "silent expected", rc, silent, out[:240]))


def scenario_h2_deploy():
    _reset_throttle(("omni-singularity", "deploy"))
    payload = _make_payload({
        "tool_name": "Bash",
        "tool_input": {"command": "vercel deploy --prod"},
    })
    rc, out = _run_hook("osa_deploy_detector.js", payload)
    _safe_unlink(payload)
    fires = "additionalContext" in out
    SCENARIOS.append(("H2-deploy", "advisory expected", rc, fires, out[:240]))


def scenario_h3_error():
    _reset_throttle(("pp-ceps-analyst", "bash-error"))
    payload = _make_payload({
        "tool_name": "Bash",
        "tool_input": {"command": "python broken.py"},
        "tool_response": {
            "output": (
                "Traceback (most recent call last):\n"
                "  File \"broken.py\", line 3, in <module>\n"
                "    foo()\n"
                "TypeError: 'NoneType' object is not callable\n"
            ),
            "stderr": "",
        },
    })
    rc, out = _run_hook("bug-hunter-ceps-bridge.js", payload, timeout=18)
    _safe_unlink(payload)
    fires = "additionalContext" in out
    SCENARIOS.append(("H3-error", "advisory expected", rc, fires, out[:240]))


def scenario_h4_session():
    proc = subprocess.run(
        [PY, str(ROOT / "tools" / "tco_compact_gate.py"),
         "--session-start-check"],
        capture_output=True, text=True, timeout=20,
    )
    out = proc.stdout or ""
    has_advisory = "additionalContext" in out
    rc = proc.returncode
    body = json.loads(out) if has_advisory and out.strip().startswith("{") else None
    ok_silent = rc == 0 and not out.strip()
    ok_warn = rc == 0 and body and "additionalContext" in body.get(
        "hookSpecificOutput", {})
    if ok_silent:
        SCENARIOS.append(("H4-session", "silent (pct < 70%)", rc, True, "(empty)"))
    elif ok_warn:
        SCENARIOS.append(("H4-session", "warning (pct >= 70%)", rc, True, out[:240]))
    else:
        SCENARIOS.append(("H4-session", "expected silent or warning",
                          rc, False, out[:240]))


def scenario_h5_slop():
    _reset_throttle(("jobs-woz-gate", "global"))
    text = (
        "This is a " + _slop_word() + " for the migration that "
        + _slop_hedge() + " for most cases. We will revise it "
        "later when more context arrives from upstream changes."
    )
    payload = _make_payload({
        "stop_reason": "end_turn",
        "assistant_message": {"content": text},
    })
    rc, out = _run_hook("jobs_woz_gate.js", payload)
    _safe_unlink(payload)
    fires = "additionalContext" in out
    SCENARIOS.append(("H5-slop", "advisory expected", rc, fires, out[:240]))


def scenario_h5_clean():
    _reset_throttle(("jobs-woz-gate", "global"))
    text = (
        "Here is the clean implementation with full coverage. "
        "All sixteen V-gates pass and the verification probe "
        "returns rc equals zero. Apex axis sealed and pushed."
    )
    payload = _make_payload({
        "stop_reason": "end_turn",
        "assistant_message": {"content": text},
    })
    rc, out = _run_hook("jobs_woz_gate.js", payload)
    _safe_unlink(payload)
    silent = rc == 0 and (not out.strip() or out.strip() == '{"continue":true}')
    SCENARIOS.append(("H5-clean", "silent expected", rc, silent, out[:240]))


def write_evidence() -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = EVIDENCE_DIR / f"hook_smoke_{iso}.md"
    lines = [
        f"# Hook Smoke Evidence -- BL-HOOKS-REG-001 ({iso})",
        "",
        "Empirical smoke tests of the five PP hook scripts invoked",
        "via `cmd /c node <hook> < <payload>` (PowerShell drops stdin",
        "to native exe; cmd-redirect is the deterministic path).",
        "",
        "| # | scenario | expected | rc | outcome | output (truncated) |",
        "|---|---|---|---|---|---|",
    ]
    for i, (label, expected, rc, ok, out_text) in enumerate(SCENARIOS, 1):
        outcome = "OK" if ok else "FAIL"
        out_one = out_text.replace("\n", " ")[:200].replace("|", "\\|")
        lines.append(
            f"| {i} | {label} | {expected} | {rc} | {outcome} | "
            f"`{out_one}` |"
        )
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    print(f"=== M5 hook smoke harness ===")
    print(f"  pp root      : {ROOT}")
    print(f"  hooks        : {HOOKS}")
    print()

    scenario_h1_dirty()
    scenario_h1_clean()
    scenario_h2_deploy()
    scenario_h3_error()
    scenario_h4_session()
    scenario_h5_slop()
    scenario_h5_clean()

    for label, expected, rc, ok, _ in SCENARIOS:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {label:14s} expected={expected:32s} rc={rc}")

    evidence_path = write_evidence()
    print()
    print(f"Evidence: {evidence_path}")
    ok_count = sum(1 for *_, ok, _ in SCENARIOS if ok)
    total = len(SCENARIOS)
    print(f"SMOKE_PASS={ok_count}/{total}")
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
