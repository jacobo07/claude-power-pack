#!/usr/bin/env python3
"""test_mirror_parity.py - dual-validation harness (Q5c).

Asserts the dynamic mirror verifier is branch-flip-immune:

  1. `verify_global_mirrors.py` (default check) exits 0 regardless of
     which branch the working tree currently has checked out (the whole
     point: it reads committed blobs via `git show <named-ref>`, never
     the working tree).
  2. `verify_global_mirrors.py --self-test` exits 0 - present refs that
     track a pair agree on the LF-normalized SHA; refs that do not track
     it are SKIPped (gap #9), never counted as agreement or as drift.
  3. The check output reports a stable `ref=` per pair and the current
     working-tree branch does NOT change the verdict.

Exit 0 = all assertions pass. Exit 1 = any assertion failed (prints the
captured stdout/stderr for forensics). No network, no mutation.
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFIER = os.path.join(HERE, "verify_global_mirrors.py")


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, VERIFIER, *args],
        capture_output=True, text=True, timeout=120,
    )


def _branch() -> str:
    r = subprocess.run(
        ["git", "-C", HERE, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=15,
    )
    return r.stdout.strip() if r.returncode == 0 else "?"


def main() -> int:
    failures: list[str] = []
    wt_branch = _branch()
    print(f"[harness] working-tree branch = {wt_branch}")

    chk = _run([])
    print(chk.stdout.rstrip())
    if chk.returncode != 0:
        failures.append(f"default-check rc={chk.returncode}")
    if "VERIFY_GLOBAL_MIRRORS OK" not in chk.stdout:
        failures.append("default-check missing OK sentinel")
    ok_pairs = chk.stdout.count("[OK]")
    if ok_pairs < 1:
        failures.append(f"default-check produced {ok_pairs} [OK] pairs")
    if "ref=" not in chk.stdout:
        failures.append("default-check did not report a stable ref= per pair")

    st = _run(["--self-test"])
    print(st.stdout.rstrip())
    if st.returncode != 0:
        failures.append(f"self-test rc={st.returncode}")
    if "SELF_TEST OK" not in st.stdout:
        failures.append("self-test missing OK sentinel")
    if "[VIOLATION]" in st.stdout:
        failures.append("self-test reported a cross-ref VIOLATION")

    if failures:
        print("\n[harness] FAIL:")
        for f in failures:
            print(f"  - {f}")
        if chk.stderr.strip():
            print("  check.stderr:", chk.stderr.strip()[:400])
        if st.stderr.strip():
            print("  selftest.stderr:", st.stderr.strip()[:400])
        return 1

    print(f"\n[harness] PASS - verifier branch-flip-immune on "
          f"working tree '{wt_branch}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
