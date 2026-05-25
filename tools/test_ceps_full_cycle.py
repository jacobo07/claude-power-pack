#!/usr/bin/env python3
"""M16 -- CEPS full-cycle empirical: error -> records -> propagates ->
distributes -> stub generated -> baseline tests still pass.

Demonstrates the end-to-end CEPS+ATG flow without polluting production
paths. All CEPS / generator paths monkeypatched to a tmpdir.

Exit 0 = full cycle PASS. Exit 1 = any step fails.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import ceps  # noqa: E402
import ceps_test_gen  # noqa: E402

PYTHON = sys.executable


def _isolate_ceps(tmp: Path) -> None:
    ceps.EVENTS_PATH = tmp / "events.jsonl"
    ceps.DB_PATH = tmp / "patterns.db"
    ceps.LESSONS_PATH = tmp / "session_lessons.md"
    ceps.UKDL_PATH = tmp / "ukdl.md"
    ceps.DRAFTS_DIR = tmp / "drafts"


def step(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")


def run() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ceps-full-cycle-"))
    failed = []

    # 1. Isolate CEPS paths
    _isolate_ceps(tmp)
    step("V-FULL-1 isolate-paths", True, f"tmp={tmp}")

    # 2. Record a real-shape error
    ev = ceps.record_error(
        category="regression",
        subsystem="ceps-full-cycle-demo",
        root_cause="full-cycle test: synthetic regression in CEPS pipeline "
                   "to exercise record -> propagate -> distribute -> stub",
        confidence="high",
    )
    ok = ev is not None
    step("V-FULL-2 record_error", ok,
         f"id={ev['id'] if ev else 'NONE'} sig={ev['pattern_signature'] if ev else 'NONE'}")
    if not ok:
        failed.append("V-FULL-2")
        return 1

    sig = ev["pattern_signature"]

    # 3. Verify events.jsonl has the entry
    events_text = (tmp / "events.jsonl").read_text(encoding="utf-8")
    ok = sig in events_text
    step("V-FULL-3 events.jsonl-append", ok,
         f"bytes={len(events_text)}")
    if not ok:
        failed.append("V-FULL-3")

    # 4. Verify session_lessons.md and ukdl.md got the entry
    lessons_text = (tmp / "session_lessons.md").read_text(encoding="utf-8")
    ukdl_text = (tmp / "ukdl.md").read_text(encoding="utf-8")
    ok = (ev["id"] in lessons_text) and (ev["id"] in ukdl_text)
    step("V-FULL-4 distribute-to-2-mds", ok,
         f"lessons={len(lessons_text)}b ukdl={len(ukdl_text)}b")
    if not ok:
        failed.append("V-FULL-4")

    # 5. Propagate query: matching prompt -> top-k should contain sig
    lines = ceps.propagate(
        "synthetic regression in the CEPS pipeline full-cycle demo",
        top_k=3)
    ok = any(sig[:8] in l for l in lines)
    step("V-FULL-5 propagate", ok,
         f"top_k={len(lines)} hit={'yes' if ok else 'NO'}")
    if not ok:
        failed.append("V-FULL-5")

    # 6. Generator: write the stub to tmp/tests
    tmp_tests = tmp / "tests" / "ceps_generated"
    ceps_test_gen.STUB_DIR = tmp_tests
    rc = ceps_test_gen.main(["generate", "--events", str(tmp / "events.jsonl")])
    stub_path = tmp_tests / f"test_{sig[:12]}.py"
    ok = (rc == 0) and stub_path.exists()
    step("V-FULL-6 stub-generation", ok,
         f"path={stub_path.relative_to(tmp) if stub_path.exists() else 'MISSING'}")
    if not ok:
        failed.append("V-FULL-6")
        return 1

    # 7. Run pytest on the tmp stub -> expect 1 skipped, 0 failed
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", str(stub_path), "-q",
         "--tb=no", "--no-header"],
        capture_output=True, text=True, timeout=60,
    )
    combined = (proc.stdout + proc.stderr).lower()
    ok = ("skipped" in combined) and ("failed" not in combined or "0 failed" in combined)
    step("V-FULL-7 pytest-skip-honored", ok,
         f"rc={proc.returncode}")
    if not ok:
        failed.append("V-FULL-7")
        print("   pytest output:")
        for line in (proc.stdout + proc.stderr).splitlines()[-8:]:
            print(f"     {line}")

    # 8. Baseline tests still pass (29/29). Run the real testable subset.
    proc = subprocess.run(
        [PYTHON, "-m", "pytest",
         "tests/test_forensic_probes.py",
         "tests/test_mistake_frequency_xplat.py",
         "-q", "--tb=no", "--no-header"],
        capture_output=True, text=True, timeout=120,
        cwd=str(PP_ROOT),
    )
    tail = (proc.stdout + proc.stderr)
    ok = ("29 passed" in tail) and (proc.returncode == 0)
    step("V-FULL-8 baseline-29-PASS", ok,
         f"rc={proc.returncode}")
    if not ok:
        failed.append("V-FULL-8")
        print("   baseline output tail:")
        for line in tail.splitlines()[-6:]:
            print(f"     {line}")

    print()
    if failed:
        print(f"CYCLE_PASS=false  failed: {', '.join(failed)}")
        return 1
    print("CYCLE_PASS=true  (record -> events -> distribute -> "
          "propagate -> stub -> pytest-skip-honored -> baseline-intact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
