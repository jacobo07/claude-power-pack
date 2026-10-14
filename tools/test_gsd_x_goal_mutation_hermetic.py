#!/usr/bin/env python3
"""The goal mutation suite must never move the tree it was started from.

    python tools/test_gsd_x_goal_mutation_hermetic.py

The property under test is about an ENTRY TREE, not about this checkout: the suite is
started from a sandbox copy (the copy mechanism `gsdx_reality_baseline` owns), so the
test can run a suite that still mutates in place without ever touching the real tree.
A suite that edits its own tree and restores it is one hard kill away from leaving a
mutant behind; this test drives that kill.

Gates:
  V-HERM-CONTROL          the fingerprint can see a one-byte change (instrument control)
  V-HERM-KILL-UNMOVED     a hard tree-kill mid-run leaves every mutation target byte-identical
  V-HERM-KILL-NO-JOURNAL  and no restore journal exists for the entry tree (it does not
                          depend on a journal to be clean)
  V-HERM-FULL-UNMOVED     an uninterrupted run leaves the entry tree byte-identical and
                          reports the full anchored set CAUGHT (58/58 at this candidate)
  V-HERM-REAL-TREE-UNMOVED the real checkout's targets are byte-identical before/after all of it
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gsdx_reality_baseline as rb  # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
SUITE ="test_gsd_x_goal_mutation.py"
KILL_AFTER_S = float(os.environ.get("GSDX_HERMETIC_KILL_AFTER_S") or 20)
FULL_TIMEOUT_S = int(os.environ.get("GSDX_HERMETIC_FULL_TIMEOUT_S") or 1500)
passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, why):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {why}")


def target_paths(tree: Path) -> list[Path]:
    """Every file the suite can mutate, read from the suite's own MUTATIONS table."""
    src = (tree / "tools" / SUITE).read_text(encoding="utf-8")
    ns: dict = {"__file__": str(tree / "tools" / SUITE), "__name__": "mut_probe"}
    sys.path.insert(0, str(tree / "tools"))
    try:
        exec(compile(src.split("\ndef suite_for")[0], SUITE, "exec"), ns)
    finally:
        sys.path.pop(0)
    return sorted({m[0] for m in ns["MUTATIONS"].values()} | set(ns["SUITES"].values()))


def fingerprint(paths) -> dict:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def journal_for(tree: Path) -> Path:
    return Path(tempfile.gettempdir()) / f"gsdx-goal-mutation-{hashlib.sha256(str(tree).encode()).hexdigest()[:12]}.json"


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=60)
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    proc.wait(timeout=60)


def start(tree: Path, log: Path) -> subprocess.Popen:
    fh = open(log, "wb")
    return subprocess.Popen([sys.executable, "-B", str(tree / "tools" / SUITE)], cwd=str(tree),
                            stdout=fh, stderr=subprocess.STDOUT, start_new_session=(os.name != "nt"),
                            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})


def main() -> int:
    sandbox = rb._make_copy(ROOT).resolve()          # stands in for "the tree the suite is started from"
    real_paths = target_paths(ROOT)
    real_before = fingerprint(real_paths)
    try:
        paths = target_paths(sandbox)
        base = fingerprint(paths)

        # control: the instrument must be able to answer "moved"
        probe = paths[0]
        raw = probe.read_bytes()
        probe.write_bytes(raw + b"\n")
        moved = fingerprint(paths) != base
        probe.write_bytes(raw)
        if moved and fingerprint(paths) == base:
            _ok("V-HERM-CONTROL", f"1-byte change on {probe.name} seen, then restored")
        else:
            _fail("V-HERM-CONTROL", "fingerprint did not register a 1-byte change")

        # interrupted run: hard-kill the whole tree mid-mutant
        logk = sandbox.parent / (sandbox.name + ".kill.log")
        jr = journal_for(sandbox)
        jr.unlink(missing_ok=True)
        p = start(sandbox, logk)
        t0 = time.time()
        while time.time() - t0 < KILL_AFTER_S and p.poll() is None:
            if fingerprint(paths) != base:
                break                       # a live target is mutated right now: kill here
            time.sleep(0.2)
        died_early = p.poll() is not None
        if not died_early:
            kill_tree(p)
        time.sleep(1.0)
        after_kill = fingerprint(paths)
        if died_early:
            _fail("V-HERM-KILL-UNMOVED", f"suite exited rc={p.returncode} before the kill; nothing was interrupted")
        elif after_kill == base:
            _ok("V-HERM-KILL-UNMOVED", f"entry tree byte-identical after a hard kill at {time.time() - t0:.1f}s")
        else:
            bad = [Path(k).name for k in after_kill if after_kill[k] != base[k]]
            _fail("V-HERM-KILL-UNMOVED", f"entry tree left mutated after a hard kill: {bad}")
        if jr.exists():
            _fail("V-HERM-KILL-NO-JOURNAL", f"a restore journal exists for the entry tree ({jr.name}): the run depends on it")
        else:
            _ok("V-HERM-KILL-NO-JOURNAL", "no restore journal for the entry tree")
        # put the sandbox back to base so the next gate starts clean whatever happened
        for k, v in after_kill.items():
            if v != base[k]:
                subprocess.run([GIT, "-C", str(sandbox), "checkout", "--", Path(k).relative_to(sandbox).as_posix()],
                               capture_output=True, stdin=subprocess.DEVNULL)
        jr.unlink(missing_ok=True)

        # uninterrupted run
        logf = sandbox.parent / (sandbox.name + ".full.log")
        p = start(sandbox, logf)
        try:
            rc = p.wait(timeout=FULL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            kill_tree(p)
            rc = None
        text = logf.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"GSDX_GOAL_MUTATIONS_CAUGHT=(\d+)/(\d+)", text)
        same = fingerprint(paths) == base
        if rc is None:
            _fail("V-HERM-FULL-UNMOVED", f"full run did not finish in {FULL_TIMEOUT_S}s (UNRUN, not a verdict)")
        elif m and m.group(1) == m.group(2) and rc == 0 and same:
            _ok("V-HERM-FULL-UNMOVED", f"CAUGHT={m.group(1)}/{m.group(2)}, entry tree byte-identical")
        else:
            _fail("V-HERM-FULL-UNMOVED",
                  f"rc={rc} caught={m.groups() if m else None} entry_unchanged={same}; tail: {text[-300:]!r}")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        for suffix in (".kill.log", ".full.log"):
            Path(str(sandbox) + suffix).unlink(missing_ok=True)

    if fingerprint(real_paths) == real_before:
        _ok("V-HERM-REAL-TREE-UNMOVED", f"{len(real_paths)} real target(s) byte-identical")
    else:
        _fail("V-HERM-REAL-TREE-UNMOVED", "the real checkout moved while this test ran")
    print(f"GSDX_MUTATION_HERMETIC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
