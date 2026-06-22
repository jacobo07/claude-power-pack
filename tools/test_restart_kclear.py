#!/usr/bin/env python3
"""test_restart_kclear.py -- V-gates for the /restart + /kclear recursive audit.

Hermetic, no-mock gates sealing the 7 findings (PF-1..PF-7) of the 2026-06-22
recursive deep audit. Scoped to NOT duplicate tools/test_restart_and_lag.py
(which owns the restart_pending.json marker-writer/consume/hub gates); this
suite asserts the NEW findings + an honest /kclear contract + a baseline-intact
check that the existing restart suite still passes.

Gates:
  V-RESTART-FLOW-COMPLETE       live /restart flow pieces exist (command +
                                ps1 writes restart_pending + hub consumes)
  V-RESTART-SELFHEAL-DEAD       PF-1: NOTHING produces restart-target.json
                                (no false-mismatch revive); documented inert
  V-RESTART-LESSON-SUPERSEDED   PF-2: pane-eviction lesson carries the
                                SUPERSEDED banner -> in-pane design
  V-RAMWATCHDOG-THRESHOLD        PF-3: ram-watchdog.js RSS threshold >= 20 GB
  V-RAMWATCHDOG-DEDUP-DOC        PF-3: ram-watchdog.js documents the metric
                                caveat + context_monitor authoritative
  V-RAMGUARDSTOP-DEPRECATED      PF-4: ram-guard-stop.js header-deprecated AND
                                NOT registered in settings.json
  V-CPCRESTART-INTENT-ONLY       PF-5: cpc_os/restart.py documents no-live-caller
  V-KCLEAR-CHECKPOINT-INTEGRITY  PF-6: session_checkpoint record writes handoff
                                + insights HERMETICALLY (under a tmp root),
                                real repo tree untouched
  V-KCLEAR-WORKSTATE-SAVED       work_state_saver writes a structured record to
                                a tmp state_dir (the auto-reset companion)
  V-KCLEAR-CLEAR-SUGGESTED       PF-6: /kclear command suggests native /clear;
                                UKDL attributes RAM-free to /clear, not /kclear
  V-RESTART-KCLEAR-INDEPENDENT   no circular dependency between the two surfaces
  V-EDGE-CASES-DOCUMENTED        all 5 new UKDL traps present
  V-BASELINE-INTACT              tools/test_restart_and_lag.py still exits 0
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
PY = sys.executable

CMD_RESTART = HOME / ".claude" / "commands" / "restart.md"
CMD_KCLEAR = HOME / ".claude" / "commands" / "kclear.md"
PS1_RESTART = HOME / ".claude" / "scripts" / "restart-claude.ps1"
SETTINGS = HOME / ".claude" / "settings.json"
HUB = PP_ROOT / "hooks" / "session_start_hub.js"
RAM_WATCHDOG = PP_ROOT / "modules" / "zero-crash" / "hooks" / "ram-watchdog.js"
RAM_GUARD_STOP = PP_ROOT / "hooks" / "ram-guard-stop.js"
CPC_RESTART = PP_ROOT / "modules" / "cpc_os" / "restart.py"
LESSON = PP_ROOT / "vault" / "lessons" / "restart-command-pane-eviction.md"
UKDL = PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
CHECKPOINT = PP_ROOT / "tools" / "session_checkpoint.py"
SUBPROC_TIMEOUT_S = 60

PASS = 0
FAIL = 0


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _ok(gate: str, ev: str) -> None:
    global PASS
    PASS += 1
    print(f"  [OK]   {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {gate}: {ev}")


def gate_restart_flow_complete():
    parts = {
        "command": CMD_RESTART.is_file(),
        "ps1": PS1_RESTART.is_file(),
        "ps1_writes_pending": "restart_pending.json" in _read(PS1_RESTART),
        "hub_consumes": "restart_pending.json" in _read(HUB)
        and "hookRestartResume" in _read(HUB),
    }
    if all(parts.values()):
        _ok("V-RESTART-FLOW-COMPLETE",
            "command + ps1(writes restart_pending) + hub(hookRestartResume)")
    else:
        _fail("V-RESTART-FLOW-COMPLETE", json.dumps(parts))


def gate_restart_selfheal_dead():
    """PF-1: confirm NOTHING produces restart-target.json -> the consumer's
    session_id-mismatch revive can never spuriously fire. Producer absence is
    the proof; documentation is the second leg."""
    ps1 = _read(PS1_RESTART)
    producer_in_ps1 = ("restart-target.json" in ps1
                       or "Write-RestartTarget" in ps1)
    # lazarus-revive.ps1 may READ restart-target (via -OnlySession) but must
    # not WRITE it. Check the scripts dir for any writer of the path.
    scripts_dir = HOME / ".claude" / "scripts"
    writers = []
    for p in scripts_dir.glob("*.ps1"):
        body = _read(p)
        if "restart-target.json" in body and (
            "WriteAllText" in body or "Set-Content" in body
            or "Out-File" in body
        ):
            # crude: a write verb co-located with the path
            writers.append(p.name)
    documented = "T-RESTART-SELFHEAL-OBSOLETE-001" in _read(UKDL)
    if not producer_in_ps1 and not writers and documented:
        _ok("V-RESTART-SELFHEAL-DEAD",
            "no producer of restart-target.json (revive cannot misfire); "
            "documented in UKDL")
    else:
        _fail("V-RESTART-SELFHEAL-DEAD",
              f"producer_in_ps1={producer_in_ps1} writers={writers} "
              f"documented={documented}")


def gate_restart_lesson_superseded():
    body = _read(LESSON)
    if "SUPERSEDED" in body and "in-pane" in body and "T-RESTART-001" in body:
        _ok("V-RESTART-LESSON-SUPERSEDED",
            "banner present, points to in-pane design + T-RESTART-001")
    else:
        _fail("V-RESTART-LESSON-SUPERSEDED",
              f"SUPERSEDED={'SUPERSEDED' in body} "
              f"in-pane={'in-pane' in body}")


def gate_ramwatchdog_threshold():
    body = _read(RAM_WATCHDOG)
    # Find the active constant assignment (last occurrence wins over comments).
    val = None
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("const RSS_THRESHOLD_MB") and "=" in s:
            try:
                val = int("".join(ch for ch in s.split("=", 1)[1] if ch.isdigit()))
            except ValueError:
                val = None
    if val is not None and val >= 20000:
        _ok("V-RAMWATCHDOG-THRESHOLD", f"RSS_THRESHOLD_MB={val} (>= 20000)")
    else:
        _fail("V-RAMWATCHDOG-THRESHOLD", f"RSS_THRESHOLD_MB={val} (< 20000)")


def gate_ramwatchdog_dedup_doc():
    body = _read(RAM_WATCHDOG)
    if ("context_monitor" in body and "METRIC CAVEAT" in body
            and "authoritative" in body.lower()):
        _ok("V-RAMWATCHDOG-DEDUP-DOC",
            "metric caveat + context_monitor authoritative documented")
    else:
        _fail("V-RAMWATCHDOG-DEDUP-DOC",
              f"context_monitor={'context_monitor' in body} "
              f"caveat={'METRIC CAVEAT' in body}")


def gate_ramguardstop_deprecated():
    body = _read(RAM_GUARD_STOP)
    header_ok = "SUPERSEDED" in body and "ram-watchdog.js" in body
    settings = _read(SETTINGS)
    not_registered = "ram-guard-stop.js" not in settings
    if header_ok and not_registered:
        _ok("V-RAMGUARDSTOP-DEPRECATED",
            "header-deprecated + absent from settings.json")
    else:
        _fail("V-RAMGUARDSTOP-DEPRECATED",
              f"header={header_ok} not_registered={not_registered}")


def gate_cpcrestart_intent_only():
    body = _read(CPC_RESTART)
    cmd = _read(CMD_RESTART)
    documented = "LIVE-PATH NOTE" in body and "NO live caller" in body
    # The live command must NOT invoke restart_intent.
    cmd_clean = "restart_intent" not in cmd
    if documented and cmd_clean:
        _ok("V-CPCRESTART-INTENT-ONLY",
            "documented inert-by-design; command does not call restart_intent")
    else:
        _fail("V-CPCRESTART-INTENT-ONLY",
              f"documented={documented} cmd_clean={cmd_clean}")


def gate_kclear_checkpoint_integrity():
    """PF-6: run session_checkpoint record HERMETICALLY. A tmp root with both
    a `.claude` marker (so find_project_root stops there) and a `memory/` dir
    (so get_memory_dir writes under tmp, not ~/.claude/projects). Assert the
    handoff + insights land under tmp AND the real repo tree is untouched."""
    if not CHECKPOINT.is_file():
        _fail("V-KCLEAR-CHECKPOINT-INTEGRITY", f"missing: {CHECKPOINT}")
        return
    # Snapshot a real-repo sentinel to prove no leak.
    real_handoff = PP_ROOT / "memory" / "project_session_handoff.md"
    real_before = real_handoff.stat().st_mtime if real_handoff.is_file() else None
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".claude").mkdir()
        (root / "memory").mkdir()
        payload = {
            "session_id": "hermetic-test",
            "date": "2026-06-22",
            "summary": "V-KCLEAR-CHECKPOINT-INTEGRITY hermetic checkpoint",
            "pending": ["verify hermetic write"],
            "insights": [{"category": "reference", "title": "h-test",
                          "body": "hermetic", "path": None, "tags": []}],
        }
        try:
            proc = subprocess.run(
                [PY, str(CHECKPOINT), "record", "--stdin"],
                input=json.dumps(payload), capture_output=True, text=True,
                cwd=str(root), timeout=SUBPROC_TIMEOUT_S,
            )
        except subprocess.SubprocessError as exc:
            _fail("V-KCLEAR-CHECKPOINT-INTEGRITY", f"spawn failed: {exc}")
            return
        handoff = root / "memory" / "project_session_handoff.md"
        insights = root / "_audit_cache" / "insights.json"
        real_after = (real_handoff.stat().st_mtime
                      if real_handoff.is_file() else None)
        leaked = real_before != real_after
        if (proc.returncode == 0 and handoff.is_file()
                and insights.is_file() and not leaked):
            _ok("V-KCLEAR-CHECKPOINT-INTEGRITY",
                "handoff + insights written under tmp; real repo untouched")
        else:
            _fail("V-KCLEAR-CHECKPOINT-INTEGRITY",
                  f"rc={proc.returncode} handoff={handoff.is_file()} "
                  f"insights={insights.is_file()} leaked={leaked} "
                  f"err={proc.stderr[:120]!r}")


def gate_kclear_workstate_saved():
    """work_state (auto-reset companion) saves a structured record to a tmp
    state_dir. Documents that work_state belongs to the auto-reset path, not
    manual /kclear (session_checkpoint)."""
    sys.path.insert(0, str(PP_ROOT))
    try:
        from modules.cpc_os.work_state_saver import (  # type: ignore
            save_work_state, load_work_state_for_cwd,
        )
    except Exception as exc:  # noqa: BLE001
        _fail("V-KCLEAR-WORKSTATE-SAVED", f"import failed: {exc}")
        return
    with tempfile.TemporaryDirectory() as td:
        rec = save_work_state(str(PP_ROOT), session_id="ws-test",
                              task="hermetic work_state", state_dir=td)
        back = load_work_state_for_cwd(str(PP_ROOT), state_dir=td)
        if (rec.get("schema_version") == 1 and back is not None
                and back.get("session_id") == "ws-test"):
            _ok("V-KCLEAR-WORKSTATE-SAVED",
                f"record saved+reloaded under tmp ({rec.get('_path')})")
        else:
            _fail("V-KCLEAR-WORKSTATE-SAVED",
                  f"rec={rec.get('schema_version')} back={back}")


def gate_kclear_clear_suggested():
    body = _read(CMD_KCLEAR)
    ukdl = _read(UKDL)
    suggests_clear = "/clear" in body
    ukdl_attributes = ("T-KCLEAR-RAM-SEMANTICS-001" in ukdl
                       and "native `/clear`" in ukdl)
    if suggests_clear and ukdl_attributes:
        _ok("V-KCLEAR-CLEAR-SUGGESTED",
            "/kclear suggests /clear; UKDL attributes RAM-free to /clear")
    else:
        _fail("V-KCLEAR-CLEAR-SUGGESTED",
              f"suggests_clear={suggests_clear} ukdl={ukdl_attributes}")


def gate_restart_kclear_independent():
    """No circular dependency: the /kclear backend must not import the restart
    module, and the restart ps1 must not invoke the kclear backend."""
    checkpoint = _read(CHECKPOINT)
    ps1 = _read(PS1_RESTART)
    kclear_clean = ("cpc_os.restart" not in checkpoint
                    and "restart_resume" not in checkpoint)
    restart_clean = "session_checkpoint" not in ps1
    if kclear_clean and restart_clean:
        _ok("V-RESTART-KCLEAR-INDEPENDENT",
            "no cross-imports between /restart and /kclear surfaces")
    else:
        _fail("V-RESTART-KCLEAR-INDEPENDENT",
              f"kclear_clean={kclear_clean} restart_clean={restart_clean}")


def gate_edge_cases_documented():
    ukdl = _read(UKDL)
    traps = [
        "T-RESTART-SELFHEAL-OBSOLETE-001",
        "T-RAM-DEDUP-001",
        "T-RESTART-INTENT-ORPHAN-001",
        "T-KCLEAR-RAM-SEMANTICS-001",
    ]
    missing = [t for t in traps if t not in ukdl]
    fold_note = "Fold note (2026-06-22, PF-7)" in ukdl
    if not missing and fold_note:
        _ok("V-EDGE-CASES-DOCUMENTED",
            f"{len(traps)} new UKDL traps + T-RESTART-001 fold note present")
    else:
        _fail("V-EDGE-CASES-DOCUMENTED",
              f"missing={missing} fold_note={fold_note}")


def gate_baseline_intact():
    suite = PP_ROOT / "tools" / "test_restart_and_lag.py"
    if not suite.is_file():
        _fail("V-BASELINE-INTACT", f"missing: {suite}")
        return
    try:
        proc = subprocess.run(
            [PY, str(suite)], capture_output=True, text=True,
            timeout=SUBPROC_TIMEOUT_S,
        )
    except subprocess.SubprocessError as exc:
        _fail("V-BASELINE-INTACT", f"spawn failed: {exc}")
        return
    tail = (proc.stdout or "").strip().splitlines()
    summary = tail[-1] if tail else "(no output)"
    if proc.returncode == 0:
        _ok("V-BASELINE-INTACT", f"test_restart_and_lag exit 0 :: {summary}")
    else:
        _fail("V-BASELINE-INTACT",
              f"exit {proc.returncode} :: {summary}")


def gate_marker_nobom_contract():
    """R2-2: every producer of restart_pending.json must write UTF-8 NO BOM
    (sealed contract, UKDL T-RESTART-001 step 2). restart-claude.ps1 uses
    WriteAllText + UTF8Encoding($false); compact_rescue.ps1 (the second
    producer) must too -- never Set-Content -Encoding UTF8 (which BOMs in
    PS 5.1)."""
    cr = _read(PP_ROOT / "tools" / "compact_rescue.ps1")
    nobom = "UTF8Encoding" in cr and "WriteAllText" in cr
    bad = any(
        "restart_pending.json" in ln and "Set-Content" in ln and "UTF8" in ln
        for ln in cr.splitlines()
    )
    if nobom and not bad:
        _ok("V-MARKER-NOBOM-CONTRACT",
            "compact_rescue.ps1 writes restart_pending.json BOM-free")
    else:
        _fail("V-MARKER-NOBOM-CONTRACT",
              f"writeAllText_nobom={nobom} bad_set_content_utf8={bad}")


def main() -> int:
    print("=" * 64)
    print("V-RESTART + V-KCLEAR recursive-audit gates (PF-1..PF-7)")
    print("=" * 64)
    for gate in (
        gate_restart_flow_complete,
        gate_restart_selfheal_dead,
        gate_restart_lesson_superseded,
        gate_ramwatchdog_threshold,
        gate_ramwatchdog_dedup_doc,
        gate_ramguardstop_deprecated,
        gate_cpcrestart_intent_only,
        gate_kclear_checkpoint_integrity,
        gate_kclear_workstate_saved,
        gate_kclear_clear_suggested,
        gate_restart_kclear_independent,
        gate_edge_cases_documented,
        gate_marker_nobom_contract,
        gate_baseline_intact,
    ):
        try:
            gate()
        except Exception as exc:  # noqa: BLE001 -- a gate crash is a FAIL, not a stop
            _fail(gate.__name__, f"gate raised {type(exc).__name__}: {exc}")
    print()
    total = PASS + FAIL
    print(f"RESTART_KCLEAR={PASS}/{total}  threshold=14/14")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
