#!/usr/bin/env python3
"""Governance Overlay hook + structural test suite.

Five V-gates closing the 2026-07-19 audit finding (PARTIALLY_FUNCTIONAL ->
FUNCTIONAL): mistake-ingest.js was built and documented but never
registered in ~/.claude/settings.json PostToolUse array, so the
mistakes-registry self-learning loop never fired (T-ORPHAN-HOOK-001).

  V-GOV-GATES-EXIST          core.md declares >=12 substantive pre-output gates
  V-GOV-HOOK-REGISTERED      mistake-ingest.js appears in the live PostToolUse array
  V-GOV-SESSION-CHECKPOINT   session_checkpoint.py exposes a working learn-error CLI
  V-GOV-HOOK-INVOKABLE       mistake-ingest.js runs standalone against a synthetic
                             isolated repo skeleton and exits 0 with valid JSON
  V-GOV-MISTAKE-INGEST-FIRES a real "## Mistake #N" addition drives the hook to
                             actually invoke learn-error and append to errors.md

All hook/session_checkpoint invocations run against a throwaway tmpdir
skeleton; production mistakes-registry.md, errors.md and
_audit_cache/seen_mistakes.json are never touched. V-GOV-HOOK-REGISTERED
reads (never writes) the live ~/.claude/settings.json.

Note: this suite verifies the hook's execution path directly (subprocess,
synthetic PostToolUse payload) rather than through a live Claude Code
session, because settings.json hooks load once at session start -- a
mid-session registration change is not observable in-session without a
restart (feedback_settings_session_load).

Exit 0 = all PASS. Exit 1 = any FAIL.
"""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
HOOK_JS = PP_ROOT / "modules" / "governance-overlay" / "hooks" / "mistake-ingest.js"
CORE_MD = PP_ROOT / "modules" / "governance-overlay" / "core.md"
CHECKPOINT_PY = PP_ROOT / "tools" / "session_checkpoint.py"
SETTINGS_JSON = Path(os.path.expanduser("~")) / ".claude" / "settings.json"
NODE = r"C:\Program Files\nodejs\node.exe"
PY = sys.executable


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def v_gates_exist() -> bool:
    text = CORE_MD.read_text(encoding="utf-8")
    nums = [int(m.group(1)) for m in re.finditer(r"^(\d+)\.\s+\*\*", text, re.M)]
    ok = len(nums) >= 12 and len(text) > 2000
    return _step("V-GOV-GATES-EXIST", ok,
                 f"gates={len(nums)} (need>=12) core.md_chars={len(text)}")


def v_hook_registered() -> bool:
    data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    post = data.get("hooks", {}).get("PostToolUse", [])
    hit = any(
        "mistake-ingest.js" in h.get("command", "")
        for entry in post
        for h in entry.get("hooks", [])
    )
    return _step("V-GOV-HOOK-REGISTERED", hit,
                 f"PostToolUse_entries={len(post)} hook_found={hit}")


def v_session_checkpoint() -> bool:
    out = subprocess.run(
        [PY, str(CHECKPOINT_PY), "learn-error", "--help"],
        capture_output=True, text=True, timeout=15,
    )
    ok = (out.returncode == 0 and "--symptom" in out.stdout
          and "--root-cause" in out.stdout and "--fix" in out.stdout)
    return _step("V-GOV-SESSION-CHECKPOINT", ok,
                 f"rc={out.returncode} has_required_flags={ok}")


def _build_isolated_repo(tmp: Path) -> Path:
    (tmp / ".git").mkdir(parents=True, exist_ok=True)
    (tmp / "modules" / "governance-overlay").mkdir(parents=True, exist_ok=True)
    (tmp / "tools").mkdir(parents=True, exist_ok=True)
    registry = tmp / "modules" / "governance-overlay" / "mistakes-registry.md"
    registry.write_text(
        "# Mistakes Registry\n\n## Mistake #1: Baseline seed mistake\n"
        "Detection: n/a. Example: n/a. Root Cause: seed for isolated test.\n",
        encoding="utf-8",
    )
    shutil.copyfile(CHECKPOINT_PY, tmp / "tools" / "session_checkpoint.py")
    return registry


def _run_hook(registry_path: Path, tmp: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(registry_path)},
    })
    return subprocess.run(
        [NODE, str(HOOK_JS)],
        input=payload, capture_output=True, text=True, timeout=15, cwd=str(tmp),
    )


def v_hook_invokable() -> bool:
    tmp = Path(tempfile.mkdtemp(prefix="gov-overlay-invokable-"))
    registry = _build_isolated_repo(tmp)
    proc = _run_hook(registry, tmp)
    ok = proc.returncode == 0
    if ok:
        try:
            json.loads(proc.stdout)
        except json.JSONDecodeError:
            ok = False
    return _step("V-GOV-HOOK-INVOKABLE", ok,
                 f"rc={proc.returncode} stdout_len={len(proc.stdout)} "
                 f"stderr={proc.stderr[:120]!r} tmp={tmp}")


def v_mistake_ingest_fires() -> bool:
    tmp = Path(tempfile.mkdtemp(prefix="gov-overlay-fires-"))
    registry = _build_isolated_repo(tmp)

    # Baseline pass: seeds _audit_cache/seen_mistakes.json with Mistake #1.
    _run_hook(registry, tmp)

    # Real edit: append a brand-new mistake header, exactly like the Owner
    # editing mistakes-registry.md in a live session would.
    registry.write_text(
        registry.read_text(encoding="utf-8") +
        "\n## Mistake #2: Synthetic test mistake for V-GOV-MISTAKE-INGEST-FIRES\n"
        "Detection: n/a. Example: n/a. Root Cause: hermetic hook-fire test.\n",
        encoding="utf-8",
    )
    proc = _run_hook(registry, tmp)

    errors_md = tmp / "vault" / "knowledge_base" / "errors.md"
    cache = tmp / "_audit_cache" / "seen_mistakes.json"

    fired = False
    if proc.returncode == 0 and proc.stdout:
        try:
            out = json.loads(proc.stdout)
            ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
            fired = "fired" in ctx
        except json.JSONDecodeError:
            pass
    errors_has_it = (errors_md.is_file()
                      and "Synthetic test mistake" in errors_md.read_text(encoding="utf-8"))
    cache_has_2 = False
    if cache.is_file():
        cache_has_2 = 2 in json.loads(cache.read_text(encoding="utf-8")).get("seen_numbers", [])

    ok = fired and errors_has_it and cache_has_2
    return _step("V-GOV-MISTAKE-INGEST-FIRES", ok,
                 f"hook_reports_fired={fired} errors_md_has_entry={errors_has_it} "
                 f"cache_tracks_num2={cache_has_2}")


def main() -> int:
    results = [
        v_gates_exist(),
        v_hook_registered(),
        v_session_checkpoint(),
        v_hook_invokable(),
        v_mistake_ingest_fires(),
    ]
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nGOV_OVERLAY_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
