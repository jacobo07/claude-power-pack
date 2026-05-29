"""V-gates for tools/bug_to_hardrule.py + modules/hard_rules/.

Sealed BL-HARDRULE-001 (2026-05-29).

Helpers named ``_check_*`` so pytest does not auto-collect this file
(per BL-HOOKS-REG-001 V-gate convention).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
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


# ---- V-HR-EXTRACTOR ----
def _check_extractor() -> None:
    try:
        from modules.hard_rules.extractor import load_candidates
        cands = load_candidates()
        if isinstance(cands, list):
            _ok("V-HR-EXTRACTOR",
                f"{len(cands)} candidate(s) load OK")
        else:
            _fail("V-HR-EXTRACTOR", f"unexpected type {type(cands)}")
    except Exception as exc:
        _fail("V-HR-EXTRACTOR", f"{type(exc).__name__}: {exc}")


# ---- V-HR-PROPOSE ----
def _check_propose() -> None:
    try:
        from modules.hard_rules.extractor import (
            BugCandidate, propose_hard_rule,
        )
        cand = BugCandidate(
            source="test",
            issue="Mock data clearing before backup",
            root_cause="No precondition check",
            fix="Add backup step",
            recognizer="Sees clear-before-backup",
            severity="CRITICAL",
        )
        text = propose_hard_rule(cand, "HR-X01")
        if ("TRIGGER:" in text and "STOP:" in text
                and "EVIDENCE:" in text and "HR-X01" in text):
            _ok("V-HR-PROPOSE", "fields TRIGGER/STOP/EVIDENCE present")
        else:
            _fail("V-HR-PROPOSE", f"missing fields: {text[:120]}")
    except Exception as exc:
        _fail("V-HR-PROPOSE", f"{type(exc).__name__}: {exc}")


# ---- V-HR-WRITER-APPEND ----
def _check_writer_append() -> None:
    try:
        from modules.hard_rules.writer import (
            append_hard_rule, list_hard_rules,
        )
        with tempfile.TemporaryDirectory(prefix="hr_app_") as td:
            cmd_path = Path(td) / "CLAUDE.md"
            archive = Path(td) / "archive" / "HARD_RULES.md"
            rule = ("### HR-NEXT -- Append Smoke\n"
                    "TRIGGER: smoke trigger\n"
                    "STOP: smoke stop\n"
                    "EVIDENCE: smoke\n"
                    "SEVERITY: CRITICAL\n")
            rid = append_hard_rule(rule, cmd_path, archive)
            rules = list_hard_rules(cmd_path)
            ids = [r["id"] for r in rules]
            if rid in ids and rid == "HR-001":
                _ok("V-HR-WRITER-APPEND",
                    f"id={rid} listed={ids}")
            else:
                _fail("V-HR-WRITER-APPEND",
                      f"id={rid} ids={ids}")
    except Exception as exc:
        _fail("V-HR-WRITER-APPEND", f"{type(exc).__name__}: {exc}")


# ---- V-HR-WRITER-BACKUP ----
def _check_writer_backup() -> None:
    try:
        from modules.hard_rules.writer import append_hard_rule
        with tempfile.TemporaryDirectory(prefix="hr_bak_") as td:
            cmd_path = Path(td) / "CLAUDE.md"
            archive = Path(td) / "archive" / "HARD_RULES.md"
            rule = ("### HR-NEXT -- Backup\n"
                    "TRIGGER: t\nSTOP: s\nEVIDENCE: e\n"
                    "SEVERITY: CRITICAL\n")
            append_hard_rule(rule, cmd_path, archive)
            backups = list(cmd_path.parent.glob("CLAUDE.md.pre-hr-*.bak"))
            if backups:
                _ok("V-HR-WRITER-BACKUP",
                    f"backup created: {backups[0].name}")
            else:
                _fail("V-HR-WRITER-BACKUP", "no backup file")
    except Exception as exc:
        _fail("V-HR-WRITER-BACKUP", f"{type(exc).__name__}: {exc}")


# ---- V-HR-WRITER-IDEMPOTENT ----
def _check_writer_idempotent() -> None:
    try:
        from modules.hard_rules.writer import append_hard_rule
        with tempfile.TemporaryDirectory(prefix="hr_idem_") as td:
            cmd_path = Path(td) / "CLAUDE.md"
            archive = Path(td) / "archive" / "HARD_RULES.md"
            rule = ("### HR-NEXT -- Idempotent Smoke\n"
                    "TRIGGER: same trigger\n"
                    "STOP: same stop\n"
                    "EVIDENCE: same evidence\n"
                    "SEVERITY: CRITICAL\n")
            r1 = append_hard_rule(rule, cmd_path, archive)
            r2 = append_hard_rule(rule, cmd_path, archive)
            if r1 == r2:
                _ok("V-HR-WRITER-IDEMPOTENT",
                    f"two writes -> same id={r1}")
            else:
                _fail("V-HR-WRITER-IDEMPOTENT",
                      f"first={r1} second={r2}")
    except Exception as exc:
        _fail("V-HR-WRITER-IDEMPOTENT", f"{type(exc).__name__}: {exc}")


# ---- V-HR-WRITER-SENTINEL ----
def _check_writer_sentinel() -> None:
    try:
        from modules.hard_rules.writer import (
            DEFAULT_CLAUDE_MD,
            SENTINEL_START,
            SENTINEL_END,
        )
        if not DEFAULT_CLAUDE_MD.is_file():
            _fail("V-HR-WRITER-SENTINEL",
                  f"CLAUDE.md not present: {DEFAULT_CLAUDE_MD}")
            return
        body = DEFAULT_CLAUDE_MD.read_text(encoding="utf-8-sig")
        if SENTINEL_START in body and SENTINEL_END in body:
            _ok("V-HR-WRITER-SENTINEL",
                "both sentinels present in CLAUDE.md")
        else:
            _fail("V-HR-WRITER-SENTINEL", "sentinel missing")
    except Exception as exc:
        _fail("V-HR-WRITER-SENTINEL", f"{type(exc).__name__}: {exc}")


# ---- V-HR-LIST ----
def _check_list() -> None:
    try:
        from modules.hard_rules.writer import list_hard_rules
        rules = list_hard_rules()
        if isinstance(rules, list) and len(rules) >= 1:
            _ok("V-HR-LIST", f"{len(rules)} rules installed")
        else:
            _fail("V-HR-LIST", f"rules={rules!r}")
    except Exception as exc:
        _fail("V-HR-LIST", f"{type(exc).__name__}: {exc}")


# ---- V-HR-CLI-SCAN ----
def _check_cli_scan() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "bug_to_hardrule.py"), "--scan"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=30, env=env,
    )
    if proc.returncode == 0 and "BUG CANDIDATES" in proc.stdout:
        _ok("V-HR-CLI-SCAN", "rc=0 with candidates header")
    else:
        _fail("V-HR-CLI-SCAN",
              f"rc={proc.returncode} head={proc.stdout[:80]!r}")


# ---- V-HR-CLI-LIST ----
def _check_cli_list() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "bug_to_hardrule.py"), "--list"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=30, env=env,
    )
    body = proc.stdout
    if proc.returncode == 0 and ("INSTALLED HARD RULES" in body
                                  or "No hard rules" in body):
        _ok("V-HR-CLI-LIST", "rc=0 with list header")
    else:
        _fail("V-HR-CLI-LIST",
              f"rc={proc.returncode} head={body[:80]!r}")


# ---- V-HR-CASCADE-MAP ----
def _check_cascade_map() -> None:
    try:
        from modules.pp_agents.signals.cascade import _build_cascade_map
        m = _build_cascade_map()
        if isinstance(m, dict):
            _ok("V-HR-CASCADE-MAP",
                f"map has {len(m)} pattern(s)")
        else:
            _fail("V-HR-CASCADE-MAP", f"unexpected: {type(m)}")
    except Exception as exc:
        _fail("V-HR-CASCADE-MAP", f"{type(exc).__name__}: {exc}")


# ---- V-HR-CASCADE-SIGNAL ----
def _check_cascade_signal() -> None:
    try:
        from modules.pp_agents.signals.cascade import evaluate
        result = evaluate("regression:windows-text-mode-io", "smoke")
        if result is None or hasattr(result, "advisory"):
            _ok("V-HR-CASCADE-SIGNAL",
                f"clean state -> {result!r}")
        else:
            _fail("V-HR-CASCADE-SIGNAL", f"unexpected: {result!r}")
    except Exception as exc:
        _fail("V-HR-CASCADE-SIGNAL", f"{type(exc).__name__}: {exc}")


# ---- V-HR-NEVER-AGAIN-AUTO ----
def _check_never_again_auto() -> None:
    try:
        from modules.osa import never_again as na
        proposals_dir = ROOT / "vault" / "hard_rules"
        before = set(p.name for p in proposals_dir.glob("auto_*.md")
                     if proposals_dir.is_dir())
        na.inject(
            issue="ZZZ-SMOKE-CRITICAL probe for auto-propose gate ZZZ",
            root_cause="V-gate smoke probe",
            fix="N/A smoke",
            recognizer="Sees ZZZ-SMOKE-CRITICAL token",
            severity="CRITICAL",
            project="hr-gate-smoke",
        )
        after = set(p.name for p in proposals_dir.glob("auto_*.md")
                    if proposals_dir.is_dir())
        new = after - before
        if new:
            _ok("V-HR-NEVER-AGAIN-AUTO",
                f"draft created: {next(iter(new))}")
        else:
            _fail("V-HR-NEVER-AGAIN-AUTO", "no new draft")
    except Exception as exc:
        _fail("V-HR-NEVER-AGAIN-AUTO", f"{type(exc).__name__}: {exc}")


# ---- V-HR-DISPATCHER ----
def _check_dispatcher() -> None:
    try:
        from modules.pp_agents.proactive_dispatcher import (
            AGENT_CONFIGS, dispatch,
        )
        has_cascade = "pp-cascade-guard" in AGENT_CONFIGS
        ctx = {
            "project": "hr-disp-smoke",
            "current_error": "irrelevant",
            "last_written_code": "",
            "last_written_file": "",
            "session_had_errors": False,
            "errors_fixed": 0,
        }
        result = dispatch(ctx)
        if has_cascade and isinstance(result, list):
            _ok("V-HR-DISPATCHER",
                f"cascade registered + dispatch -> {len(result)} adv")
        else:
            _fail("V-HR-DISPATCHER",
                  f"cascade_in_config={has_cascade}")
    except Exception as exc:
        _fail("V-HR-DISPATCHER", f"{type(exc).__name__}: {exc}")


# ---- V-BASELINE-INTACT ----
def _check_baseline() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=240, env=env,
    )
    last = (proc.stdout.strip().splitlines() or [""])[-1]
    if proc.returncode == 0 and "passed" in last:
        _ok("V-BASELINE-INTACT", f"rc=0 last='{last}'")
    else:
        _fail("V-BASELINE-INTACT",
              f"rc={proc.returncode} last='{last}'")


def main() -> int:
    print("=== test_hard_rules (BL-HARDRULE-001) ===")
    print(f"  pp root: {ROOT}")
    print()
    _check_extractor()
    _check_propose()
    _check_writer_append()
    _check_writer_backup()
    _check_writer_idempotent()
    _check_writer_sentinel()
    _check_list()
    _check_cli_scan()
    _check_cli_list()
    _check_cascade_map()
    _check_cascade_signal()
    _check_never_again_auto()
    _check_dispatcher()
    _check_baseline()
    total = passes + fails
    print()
    print(f"HARDRULES_PASS={passes}/{total}  threshold=14/14")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
