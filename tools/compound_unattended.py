#!/usr/bin/env python3
"""compound_unattended.py — run /cpp-compound with no human present.

Owner, 2026-09-01: "/cpp-compound debe correr desatendido."

The synthesis step is a judgment operation, not a scriptable one: turning a set
of recurring signals into a durable rule is exactly what a model does and a
regex does not. So "unattended" here means a scheduled HEADLESS AGENT run
(`claude -p`), not a Python reimplementation of the 8-step pipeline. Anything
else would be a different, worse product wearing the same name.

Three properties make that safe enough to leave alone on a timer:

  1. BOUNDED DISCOVERY. Candidates come from graphify's existing active_repos()
     — the estate's own definition of "active", discovered from the live
     session registry — filtered to those with pending learnings. A hand-kept
     list of projects would measure memory, not reality
     (PR-COVERAGE-BY-CONSTRUCTION-001), and the 191-entry state file cannot be
     reversed into paths (its keys are lossy path encodings).
  2. BOUNDED BLAST RADIUS. --max-projects per run, a per-project timeout, and
     `--permission-mode acceptEdits` rather than bypassPermissions. Every run
     writes a receipt naming what was touched, so an unattended write is
     auditable and revertible rather than anonymous.
  3. NO OVERLAP. A mkdir-mutex, the same primitive the pipeline already uses
     for its cursor. Two timers, or a timer racing an interactive
     /cpp-compound, must not both advance the cursor.

Fail-open: a failure here is a missed compound pass, never a broken session.
Exit 0 on "nothing to do" so a scheduled task does not flag healthy silence.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_HOME = Path(os.path.expanduser("~"))
_PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PP_ROOT / "modules" / "graphify"))

_STATE_DIR = _HOME / ".claude" / "state"
_LOCK = _STATE_DIR / "compound-unattended.lock"
_RECEIPT = _STATE_DIR / "compound-unattended.log"
_CLAUDE = _HOME / ".local" / "bin" / "claude.exe"

# A stale lock must not wedge the timer forever. The pipeline is minutes, not
# hours; anything past this is a dead process, not a slow one.
_LOCK_STALE_S = 45 * 60
_DEFAULT_TIMEOUT_S = 900
_DEFAULT_MAX_PROJECTS = 3

# Bounded tool set: the pipeline reads learnings, writes artifacts, and needs a
# shell for nothing else. Narrower than the command's own allowed-tools on
# purpose — an unattended run gets less latitude than a watched one.
_ALLOWED_TOOLS = "Read,Write,Edit,Glob,Grep"


def _log(payload: dict) -> None:
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(_RECEIPT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass


def acquire_lock() -> bool:
    """mkdir-mutex. Returns False when another run holds it."""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            _LOCK.mkdir()
            return True
        except FileExistsError:
            age = time.time() - _LOCK.stat().st_mtime
            if age < _LOCK_STALE_S:
                return False
            # Stale: the holder died. Reclaim rather than wedge forever.
            _log({"event": "stale_lock_reclaimed", "age_s": round(age)})
            return True
    except OSError:
        return True  # unmeasurable lock must not block the pass


def release_lock() -> None:
    try:
        _LOCK.rmdir()
    except OSError:
        pass


def pending_learnings(repo: Path) -> dict:
    """What this repo has waiting. A marker OR unconsumed learning files —
    the marker is the sentinel's signal, the files are the ground truth, and
    either alone is enough to justify a pass."""
    marker = repo / "LEARNINGS_PENDING.md"
    cache = repo / ".claude" / "cache" / "learnings"
    files = []
    try:
        if cache.is_dir():
            files = sorted(p.name for p in cache.glob("*.md"))
    except OSError:
        files = []
    return {"marker": marker.is_file(), "files": len(files)}


def candidates(max_projects: int) -> tuple:
    """(to_run, filling) — active repos ready to compound, and those still
    accumulating.

    Selection is the MARKER, not the files. `LEARNINGS_PENDING.md` is the
    sentinel's "threshold crossed" signal; the files under
    .claude/cache/learnings/ are raw input that has not yet earned a pass.
    Selecting on files would spawn an agent session per repo that would
    immediately STOP under the --unattended policy ("no marker -> stop") --
    the driver and the policy it invokes must agree on what "ready" means, or
    every run is three wasted sessions. Caught by the first dry-run: all three
    candidates had marker=false.

    `filling` is returned so the receipt shows the pipeline loading rather
    than reporting bare idleness. A producer that fires into an empty sink
    looked healthy here for 80 days once already.
    """
    try:
        import indexer  # graphify's discovery — reused, not reinvented
        repos = indexer.active_repos()
    except Exception as exc:  # noqa: BLE001 — discovery failure != crash
        _log({"event": "discovery_failed", "error": str(exc)})
        return [], []

    ready, filling = [], []
    for raw in repos:
        repo = Path(raw)
        try:
            if not repo.is_dir():
                continue
        except OSError:
            continue
        state = pending_learnings(repo)
        if state["marker"]:
            ready.append({"repo": str(repo), **state})
        elif state["files"]:
            filling.append({"repo": str(repo), **state})
    ready.sort(key=lambda r: -r["files"])
    filling.sort(key=lambda r: -r["files"])
    return ready[:max_projects], filling


def run_one(repo: str, timeout_s: int, dry_run: bool) -> dict:
    prompt = ("/cpp-compound --unattended\n\nYou are running with NO HUMAN "
              "PRESENT. Do not ask questions; follow the --unattended policy "
              "in the command definition and stop if it does not cover a case.")
    cmd = [str(_CLAUDE), "-p", prompt,
           "--permission-mode", "acceptEdits",
           "--allowed-tools", _ALLOWED_TOOLS]
    if dry_run:
        return {"repo": repo, "dry_run": True, "cmd": " ".join(cmd[:5]) + " ..."}
    t0 = time.time()
    try:
        res = subprocess.run(cmd, cwd=repo, capture_output=True, text=True,
                             timeout=timeout_s)
        return {"repo": repo, "rc": res.returncode,
                "elapsed_s": round(time.time() - t0, 1),
                "stdout_tail": (res.stdout or "")[-600:],
                "stderr_tail": (res.stderr or "")[-300:]}
    except subprocess.TimeoutExpired:
        return {"repo": repo, "rc": "timeout",
                "elapsed_s": round(time.time() - t0, 1)}
    except (OSError, ValueError) as exc:
        return {"repo": repo, "rc": "error", "error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Unattended /cpp-compound driver")
    ap.add_argument("--max-projects", type=int, default=_DEFAULT_MAX_PROJECTS)
    ap.add_argument("--timeout", type=int, default=_DEFAULT_TIMEOUT_S,
                    help="per-project wall-clock budget in seconds")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would run; invoke nothing")
    args = ap.parse_args()

    if not _CLAUDE.is_file():
        _log({"event": "claude_missing", "path": str(_CLAUDE)})
        print(json.dumps({"ok": False, "error": f"claude not at {_CLAUDE}"}))
        return 0  # a missing binary is not a scheduled-task failure to alarm on

    todo, filling = candidates(args.max_projects)
    if not todo:
        _log({"event": "idle", "candidates": 0, "filling": len(filling),
              "filling_repos": [f["repo"] for f in filling[:5]]})
        print(json.dumps({"ok": True, "candidates": 0, "ran": 0,
                          "filling": filling}, indent=2))
        return 0

    if not args.dry_run and not acquire_lock():
        _log({"event": "locked", "skipped": len(todo)})
        print(json.dumps({"ok": True, "locked": True, "ran": 0}))
        return 0

    results = []
    try:
        for item in todo:
            r = run_one(item["repo"], args.timeout, args.dry_run)
            r["pending"] = {"marker": item["marker"], "files": item["files"]}
            results.append(r)
            _log({"event": "ran", **r})
    finally:
        if not args.dry_run:
            release_lock()

    print(json.dumps({"ok": True, "candidates": len(todo),
                      "ran": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
