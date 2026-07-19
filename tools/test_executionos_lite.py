#!/usr/bin/env python3
"""ExecutionOS Lite structural test suite.

ExecutionOS is prompt doctrine, not executable behavior -- it can't be
proven correct the way CEPS is (record_error -> events.jsonl -> read
back). What CAN be proven is that a refactor didn't silently break it:
files exist, aren't stubs, and the router chain a session actually
follows (SKILL.md -> parts/sleepy/executionos.md -> core.md -> phases/
+ overlays/) resolves to real files end to end.

  V-EXEC-PHASES-EXIST       phases-0-4/5-10/11-15/16-20.md exist, non-stub
  V-EXEC-OVERLAYS-EXIST     every overlays/*.md exists, non-stub, count floor
  V-EXEC-ROUTER-REFS-VALID  SKILL.md -> executionos.md -> core.md -> phases/
                            + overlays/ glob refs all resolve to real files
  V-EXEC-MIGRATE-RETIRED    migrate.py documents itself as a historical
                            tool with no active runtime role

Exit 0 = all PASS. Exit 1 = any FAIL.
"""
from __future__ import annotations
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
EOS = PP_ROOT / "modules" / "executionos-lite"
SKILL_MD = PP_ROOT / "SKILL.md"
SLEEPY_EOS = PP_ROOT / "parts" / "sleepy" / "executionos.md"
CORE_MD = EOS / "core.md"
MIGRATE_PY = EOS / "migrate.py"

STUB_FLOOR_CHARS = 200
EXPECTED_PHASE_FILES = [
    "phases-0-4.md", "phases-5-10.md", "phases-11-15.md", "phases-16-20.md",
]
OVERLAY_COUNT_FLOOR = 15  # 18 exist as of 2026-07-19; catch a mass-deletion regression


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def v_phases_exist() -> bool:
    missing = []
    stubs = []
    for name in EXPECTED_PHASE_FILES:
        p = EOS / "phases" / name
        if not p.is_file():
            missing.append(name)
            continue
        if len(p.read_text(encoding="utf-8")) < STUB_FLOOR_CHARS:
            stubs.append(name)
    ok = not missing and not stubs
    return _step("V-EXEC-PHASES-EXIST", ok,
                 f"checked={len(EXPECTED_PHASE_FILES)} missing={missing} stubs={stubs}")


def v_overlays_exist() -> bool:
    overlay_dir = EOS / "overlays"
    files = sorted(overlay_dir.glob("*.md")) if overlay_dir.is_dir() else []
    stubs = [f.name for f in files if len(f.read_text(encoding="utf-8")) < STUB_FLOOR_CHARS]
    ok = len(files) >= OVERLAY_COUNT_FLOOR and not stubs
    return _step("V-EXEC-OVERLAYS-EXIST", ok,
                 f"found={len(files)} (floor={OVERLAY_COUNT_FLOOR}) stubs={stubs}")


def v_router_refs_valid() -> bool:
    problems = []

    if not SKILL_MD.is_file():
        problems.append("SKILL.md missing")
    else:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        if "parts/sleepy/executionos.md" not in skill_text:
            problems.append("SKILL.md no longer references parts/sleepy/executionos.md")

    if not SLEEPY_EOS.is_file():
        problems.append("parts/sleepy/executionos.md missing")
    else:
        sleepy_text = SLEEPY_EOS.read_text(encoding="utf-8")
        if "modules/executionos-lite/core.md" not in sleepy_text:
            problems.append("executionos.md no longer references modules/executionos-lite/core.md")

    if not CORE_MD.is_file():
        problems.append("modules/executionos-lite/core.md missing")
    else:
        core_text = CORE_MD.read_text(encoding="utf-8")
        if not re.search(r"phases/\*\.md", core_text):
            problems.append("core.md no longer references phases/*.md loader")
        if not re.search(r"overlays/\*\.md", core_text):
            problems.append("core.md no longer references overlays/*.md loader")
        if not list((EOS / "phases").glob("*.md")):
            problems.append("phases/*.md glob resolves to zero files")
        if not list((EOS / "overlays").glob("*.md")):
            problems.append("overlays/*.md glob resolves to zero files")

    ok = not problems
    return _step("V-EXEC-ROUTER-REFS-VALID", ok,
                 f"chain=SKILL.md->executionos.md->core.md->{{phases,overlays}}/*.md "
                 f"problems={problems if problems else 'none'}")


def v_migrate_retired() -> bool:
    if not MIGRATE_PY.is_file():
        return _step("V-EXEC-MIGRATE-RETIRED", False, "migrate.py missing")
    text = MIGRATE_PY.read_text(encoding="utf-8")
    ok = bool(re.search(r"historical tool.*no active runtime role|no active role", text, re.I))
    return _step("V-EXEC-MIGRATE-RETIRED", ok,
                 f"documents_retired_status={ok}")


def main() -> int:
    results = [
        v_phases_exist(),
        v_overlays_exist(),
        v_router_refs_valid(),
        v_migrate_retired(),
    ]
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nEXEC_OS_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
