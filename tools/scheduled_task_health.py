#!/usr/bin/env python3
"""scheduled_task_health.py -- L-SCHED detector (Cognitive Leak Taxonomy, C70).

The token audits (C68/C69) are blind to the OS layer. This closes the gap for
ONE concrete, previously-invisible leak: PP scheduled tasks that fire and either
(a) FAIL every run (a process spins up daily, exits nonzero, produces nothing),
(b) go STALE (last run far older than their own interval -> hanging or disabled
by the scheduler), or (c) fire at HIGH frequency unconditionally (every few
minutes whether or not any session is active). None of these cost tokens; they
cost CPU + host RAM + scheduler churn -- a real computational-cost leak.

Design mirrors token_ground_truth: a PURE classifier (`classify_task`, unit-
tested hermetically with synthetic dicts) is separated from the Windows-only
live reader (`scan_live`, calls Get-ScheduledTask). The classifier NEVER touches
the OS, so the done-gate test runs on any host.

Verdicts (priority high->low): FAILING > STALE > HIGH_FREQ > RUNNING > OK.
Every non-OK verdict carries a concrete, NON-destructive recommendation. This
tool NEVER mutates a scheduled task -- repair/disable is an Owner decision
(verify-before-destructive; several PP tasks exit nonzero BY CONVENTION, e.g.
a `--check` that returns 1 when it finds drift, and must NOT be disabled).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Windows LastTaskResult codes that are NOT failures.
RESULT_OK = 0
RESULT_RUNNING = 0x41301        # 267009 -- task is currently running
RESULT_NEVER_RAN = 0x41303      # 267011 -- task has never run
BENIGN_RESULTS = frozenset({RESULT_OK, RESULT_RUNNING, RESULT_NEVER_RAN})

# A HIGH_FREQ task fires more often than this (seconds). Candidate for a
# "session-active" guard so it does not run when no pane is open.
HIGH_FREQ_SECONDS = 600         # 10 min
# STALE when the last run predates this many multiples of its own interval
# (a q5min task not run in >1h is hung/disabled, not merely idle).
STALE_INTERVAL_MULTIPLE = 12.0
# For tasks with no sub-day repetition interval (daily/weekly triggers don't
# populate Repetition.Interval), STALE only after this many seconds -- 8 days,
# so a genuinely WEEKLY task (~168h between runs) is not a false positive while
# a dead daily task still surfaces.
STALE_ABSOLUTE_SECONDS = 8 * 24 * 3600   # 8 days


@dataclass
class TaskVerdict:
    name: str
    verdict: str                 # FAILING | STALE | HIGH_FREQ | RUNNING | OK
    detail: str
    recommendation: str


def classify_task(info: dict, *, now_epoch: float | None = None) -> TaskVerdict:
    """Pure classifier. `info` keys (all optional, fail-safe to OK):
      name:str, state:str, last_result:int, last_run_epoch:float|None,
      interval_seconds:float|None, now_epoch:float
    No OS access -- deterministic, hermetically testable.
    """
    name = str(info.get("name", "?"))
    res = info.get("last_result")
    interval = info.get("interval_seconds")
    last_run = info.get("last_run_epoch")
    now = now_epoch if now_epoch is not None else info.get("now_epoch")

    # 0. DISABLED -- a disabled task cannot fire, so it is not a live leak
    #    regardless of a stale nonzero last_result. Resolved, not a problem.
    if str(info.get("state", "")).lower() == "disabled":
        return TaskVerdict(name, "DISABLED", "task disabled (will not run)", "")

    # 1. FAILING -- ran and exited a non-benign, nonzero code.
    if isinstance(res, int) and res not in BENIGN_RESULTS:
        return TaskVerdict(
            name, "FAILING", f"last_result={res} (0x{res & 0xFFFFFFFF:X})",
            "Run the task's script manually to read its real exit; repair the "
            "root cause or, if obsolete, disable (reversible). Do NOT assume "
            "nonzero==broken: a --check task returns nonzero BY CONVENTION.")

    # 2. STALE -- last run far older than the task's own cadence.
    if isinstance(last_run, (int, float)) and isinstance(now, (int, float)):
        age = now - last_run
        stale_thresh = (interval * STALE_INTERVAL_MULTIPLE
                        if isinstance(interval, (int, float)) and interval > 0
                        else STALE_ABSOLUTE_SECONDS)
        if age > stale_thresh:
            return TaskVerdict(
                name, "STALE", f"last_run {age/3600:.1f}h ago "
                f"(threshold {stale_thresh/3600:.1f}h)",
                "Task is hung or silently disabled. Verify whether a healthier "
                "task supersedes it; if so, disable this one.")

    # 3. HIGH_FREQ -- fires unconditionally more often than the cap.
    if isinstance(interval, (int, float)) and 0 < interval < HIGH_FREQ_SECONDS:
        return TaskVerdict(
            name, "HIGH_FREQ", f"interval={interval:.0f}s",
            "Fires every few minutes regardless of whether a session is active. "
            "Gate on session-active (a live transcript in the last N min) to "
            "skip the spawn when idle.")

    if res == RESULT_RUNNING:
        return TaskVerdict(name, "RUNNING", "currently executing", "")
    return TaskVerdict(name, "OK", f"last_result={res}", "")


# ---- Windows-only live reader (not exercised by the hermetic test) ----------

# PS 5.1-safe: no inline-if expressions (PS7+ only); last_run pre-computed with
# a statement-form if; interval parse guarded.
_PS_SCAN = r"""
Get-ScheduledTask | Where-Object {
  $_.TaskName -match 'claude|pp-|kobii|vault|hibernat|reap|compact|sleepy|orphan|miner|snapshot|normalize|kickback|watchdog'
} | ForEach-Object {
  $task = $_
  $i = $task | Get-ScheduledTaskInfo
  $sec = $null
  foreach ($t in $task.Triggers) {
    if ($t.Repetition -and $t.Repetition.Interval) {
      try { $sec = [System.Xml.XmlConvert]::ToTimeSpan($t.Repetition.Interval).TotalSeconds } catch {}
    }
  }
  $lr = $null
  if ($i.LastRunTime) { $lr = [int64]($i.LastRunTime - (Get-Date '1970-01-01')).TotalSeconds }
  [pscustomobject]@{
    name = $task.TaskName; state = [string]$task.State
    last_result = $i.LastTaskResult; last_run = $lr; interval_seconds = $sec
  }
} | ConvertTo-Json -Depth 4
"""


def scan_live(now_epoch: float | None = None) -> list:
    """Read live PP scheduled tasks via PowerShell and classify each.
    Windows-only; fail-open to [] on any non-Windows host or PS error."""
    import time
    now = now_epoch if now_epoch is not None else time.time()
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive",
                            "-Command", _PS_SCAN],
                           capture_output=True, text=True, timeout=60)
        raw = (p.stdout or "").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
    except Exception:  # noqa: BLE001 -- fail-open
        return []
    out = []
    for d in data:
        info = {"name": d.get("name"), "state": d.get("state"),
                "last_result": d.get("last_result"),
                "last_run_epoch": d.get("last_run"),
                "interval_seconds": d.get("interval_seconds")}
        out.append(classify_task(info, now_epoch=now))
    return out


def summarize(verdicts: list) -> dict:
    counts: dict = {}
    for v in verdicts:
        counts[v.verdict] = counts.get(v.verdict, 0) + 1
    return {"total": len(verdicts), "counts": counts,
            "problems": [asdict(v) for v in verdicts
                         if v.verdict in ("FAILING", "STALE", "HIGH_FREQ")]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    verdicts = scan_live()
    s = summarize(verdicts)
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    print(f"PP scheduled tasks scanned: {s['total']}")
    print(f"verdicts: {s['counts']}")
    for p in s["problems"]:
        print(f"  [{p['verdict']}] {p['name']} -- {p['detail']}")
        if p["recommendation"]:
            print(f"      -> {p['recommendation']}")
    # nonzero exit iff any FAILING task (so the tool itself is CI-gate-able)
    return 1 if s["counts"].get("FAILING", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
