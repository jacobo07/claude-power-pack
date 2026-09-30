#!/usr/bin/env python3
"""The goal spine must run on the plane it is judged on, not only on this workstation.

    python tools/test_gsd_x_goal_portability.py

Found 2026-09-30 on GEX44 (Linux): a hardcoded Windows git path stopped 4 of 11 owning
suites before their first gate, and pid liveness was wrong on both platforms. Each gate
here drives the red case, and the sweep carries a positive control so a sweep that stopped
finding anything cannot read green.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import proc                                  # noqa: E402
from modules.gsd_x.goal.git_state import git_exe                     # noqa: E402

# A bare Windows path used as the ONLY way to reach git: `GIT = r"C:\...git.exe"` or
# `subprocess.run([r"C:\...git.exe", ...`. A candidates tuple that also offers "git" is fine,
# and so is a name bound to the path and used only after an isfile() check.
HARDCODED = re.compile(
    r'(\bGIT\s*=\s*|\(\[)r"C:\\{1,2}Program Files\\{1,2}Git\\{1,2}cmd\\{1,2}git\.exe"\s*(\n|,)')


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    # --- git resolution ---
    g = git_exe()
    out = subprocess.run([g, "--version"], capture_output=True, text=True, timeout=60)
    check("V-PORT-GIT-EXE-RUNS", out.returncode == 0 and "git version" in out.stdout,
          f"{g} -> {out.stdout.strip()}", f"{g} did not run: rc={out.returncode}")

    # --- pid liveness ---
    check("V-PORT-PID-SELF-ALIVE", proc.pid_alive(os.getpid()), "own pid alive",
          "own pid reported dead")
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    check("V-PORT-PID-DEAD-CHILD", not proc.pid_alive(child.pid), f"exited pid {child.pid} dead",
          f"exited pid {child.pid} reported alive")
    check("V-PORT-PID-GARBAGE", not any(proc.pid_alive(x) for x in (None, "", "x", 0, -1)),
          "None/''/garbage/0/-1 are dead", "a non-pid read as alive")
    if os.name != "nt":
        # pid 1 belongs to root; an unprivileged caller gets PermissionError. As root the
        # signal succeeds. Either way pid 1 exists and must read alive -- the old code said
        # dead whenever the caller lacked permission.
        check("V-PORT-PID-OTHER-USER-ALIVE", proc.pid_alive(1), "pid 1 alive",
              "pid 1 reported dead (PermissionError read as death)")
        real_kill = os.kill

        def denied(pid, sig):
            raise PermissionError(1, "Operation not permitted")
        os.kill = denied
        try:
            check("V-PORT-PID-PERMISSION-IS-ALIVE", proc.pid_alive(4242), "EPERM -> alive",
                  "EPERM -> dead")
        finally:
            os.kill = real_kill
    else:
        # The substring trap: a pid that is a prefix of a live pid must not read alive.
        real = subprocess.run
        fake_row = '"python.exe","12345","Console","1","10,000 K"\n'

        def fake_run(argv, **kw):
            return subprocess.CompletedProcess(argv, 0, stdout=fake_row, stderr="")
        proc.subprocess.run = fake_run
        try:
            check("V-PORT-PID-NO-SUBSTRING-MATCH", not proc.pid_alive(123),
                  "123 is not alive because 12345 is", "123 read alive inside 12345")
            check("V-PORT-PID-EXACT-MATCH", proc.pid_alive(12345), "12345 alive",
                  "exact pid not found")
        finally:
            proc.subprocess.run = real

    # --- the sweep ---
    files = sorted((ROOT / "modules" / "gsd_x").rglob("*.py")) + \
        sorted((ROOT / "tools").glob("test_gsd_x_*.py"))
    # This file carries the hardcoded forms on purpose, as the sweep's positive control.
    files = [p for p in files if p.resolve() != Path(__file__).resolve()]
    hits = [f"{p.relative_to(ROOT)}" for p in files
            if HARDCODED.search(p.read_text(encoding="utf-8", errors="replace"))]
    check("V-PORT-SWEEP-POPULATION", len(files) >= 20, f"{len(files)} files scanned",
          f"only {len(files)} files scanned -- the sweep lost its population")
    check("V-PORT-SWEEP-HAS-TEETH",
          bool(HARDCODED.search('GIT = r"C:\\Program Files\\Git\\cmd\\git.exe"\n'))
          and bool(HARDCODED.search('subprocess.run([r"C:\\Program Files\\Git\\cmd\\git.exe", "-C"'))
          and not HARDCODED.search('GIT_CANDIDATES = (r"C:\\Program Files\\Git\\cmd\\git.exe", "git")')
          and not HARDCODED.search('_W = r"C:\\\\Program Files\\\\Git\\\\cmd\\\\git.exe"\n'),
          "matches both hardcoded forms, spares the candidates tuple and a guarded name",
          "the sweep regex no longer recognises the forms it exists to catch")
    check("V-PORT-NO-HARDCODED-GIT", not hits, "no module or suite hardcodes git as its only path",
          f"hardcoded: {hits}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_PORTABILITY_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
