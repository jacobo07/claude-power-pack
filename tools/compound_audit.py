#!/usr/bin/env python3
"""compound_audit.py - health check for the Compound Learnings stack.

Runs five assertions:
  1. Sentinel hook file exists at ~/.claude/hooks/learning-sentinel.js
     and is non-empty.
  2. Sentinel is registered in ~/.claude/settings.json on at least one
     of: Stop, SessionEnd, SessionStart.
  3. State file ~/.claude/state/compound-learnings.json parses as valid
     JSON and has the expected schema_version/threshold/projects shape.
  4. No project has been auto-prompted past the sentinel's own suppression
     threshold without consolidation ever advancing.
  5. No project cursor has gone stale beyond the sliding window.

Exit 0 = healthy, 5 = degraded. Designed to be runnable from a CI gate
or a /restart preflight check.

WHY CHECK 4 EXISTS (2026-09-08). Measured, this file reported COMPOUND_AUDIT OK
while printing `last_run_global=never` in the very same run, against a state
holding `directive_count: 49` for one project and 37 for another. Three separate
reasons it could not say otherwise, and all three are the same mistake:

  * `assert_state_valid` FORMATTED `last_run_global` into its success message
    (`or 'never'`) and never tested it. A verdict that prints its own disproof.
  * `assert_no_stale_markers` returned True on every one of its four return
    paths, including the branch that had found stale cursors -- it was labelled
    "(advisory)". A check that cannot fail carries no information when it passes,
    and this one's own docstring named the exact condition it was declining to
    report: "stale markers usually indicate a run that never completed Step 7".
  * `directive_count` -- the field that records the runaway -- was read by
    nothing.

Check 4 also SEPARATES THE TWO CAUSES, which is the part that was doing real
damage. The pending marker asserts "Step 7 is likely partial-failing", but the
counter it cites increments on PROMPT, not on ATTEMPT, so "49 prompts nobody
acted on" and "49 runs that died in Step 7" are the same number to it. That
sent an investigator to debug a step that, per `last_run_global: null`, had
never executed anywhere. `last_run_global` is what tells the two apart, and it
was already in the file.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys

HOME = os.path.expandvars(r"%USERPROFILE%")
SENTINEL = os.path.join(HOME, ".claude", "hooks", "learning-sentinel.js")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
STATE = os.path.join(HOME, ".claude", "state", "compound-learnings.json")
STALE_MARKER_DAYS = 30

# Mirrors DIRECTIVE_DEGRADE_AT in ~/.claude/hooks/learning-sentinel.js. At this many
# un-consolidated auto-prompts the sentinel suppresses itself, which is the point at
# which the stack has stopped working and nothing else says so.
DEGRADE_AT = 4


def _load_state(d=None):
    """The parsed state, or None when there is no file. `d` short-circuits for tests."""
    if d is not None:
        return d
    if not os.path.isfile(STATE):
        return None
    try:
        with open(STATE, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def assert_sentinel_present() -> tuple[bool, str]:
    if not os.path.isfile(SENTINEL):
        return False, f"missing {SENTINEL}"
    sz = os.path.getsize(SENTINEL)
    if sz < 1024:
        return False, f"sentinel suspiciously small ({sz} bytes)"
    return True, f"sentinel OK ({sz} bytes)"


def assert_sentinel_registered() -> tuple[bool, str]:
    try:
        with open(SETTINGS, "r", encoding="utf-8-sig") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        return False, f"settings.json read failed: {e}"
    events = []
    for evt, lst in d.get("hooks", {}).items():
        for entry in lst:
            for h in entry.get("hooks", []):
                if "learning-sentinel" in (h.get("command") or ""):
                    events.append(evt)
    if not events:
        return False, "sentinel not registered on any event"
    return True, f"registered on: {sorted(set(events))}"


def assert_state_valid(d=None) -> tuple[bool, str]:
    if d is None and not os.path.isfile(STATE):
        return True, "state file not yet created (cold start)"
    d = _load_state(d)
    if d is None:
        return False, "state read failed"
    if d.get("schema_version") != 1:
        return False, f"schema_version != 1: {d.get('schema_version')!r}"
    if not isinstance(d.get("threshold"), int):
        return False, f"threshold not int: {d.get('threshold')!r}"
    if not isinstance(d.get("projects"), dict):
        return False, "projects key missing or wrong type"
    # last_run_global is REPORTED here and JUDGED in assert_consolidation_advances.
    # It stays out of this verdict on purpose: an estate that has genuinely never
    # needed a consolidation is not malformed, and shape is all this check owns.
    return True, (f"threshold={d['threshold']}, "
                  f"projects={len(d['projects'])}, "
                  f"last_run_global={d.get('last_run_global') or 'never'}")


def assert_consolidation_advances(d=None) -> tuple[bool, str]:
    """FAIL when a project has been auto-prompted past the suppression threshold.

    The message names WHICH of the two causes applies, because they need opposite
    fixes: `last_run_global` empty means consolidation has never completed anywhere
    (nobody ran the command), while a populated one means it completes elsewhere and
    is failing for these projects specifically.
    """
    if d is None and not os.path.isfile(STATE):
        return True, "no state file -> nothing to consolidate yet"
    d = _load_state(d)
    if d is None:
        return False, "state unreadable, so consolidation progress cannot be judged"

    projects = d.get("projects", {})
    if not isinstance(projects, dict):
        return False, "projects key missing or wrong type"

    stuck = sorted(
        ((pid, int(info.get("directive_count") or 0))
         for pid, info in projects.items()
         if isinstance(info, dict) and int(info.get("directive_count") or 0) >= DEGRADE_AT),
        key=lambda t: -t[1])
    never = not d.get("last_run_global")

    if not stuck:
        note = "; last_run_global=never, but no project has hit the threshold" if never else ""
        return True, f"no project past the {DEGRADE_AT}-prompt suppression threshold{note}"

    names = ", ".join(f"...{pid[-38:]}={n}" for pid, n in stuck[:3])
    cause = (
        "last_run_global is empty, so consolidation has NEVER completed in ANY project. "
        "The counter increments on PROMPT, not on attempt, so this is 'nobody ran it', "
        "NOT 'Step 7 is partial-failing' -- do not go debugging Step 7. "
        if never else
        "last_run_global is set, so consolidation completes elsewhere and is failing for "
        "these projects specifically -- Step 7 is the right place to look. ")
    return False, (
        f"{len(stuck)} project(s) past the {DEGRADE_AT}-prompt suppression threshold "
        f"(worst={stuck[0][1]}): {names}. {cause}"
        "Fix: run the compound command for one of them (a successful Step 7 resets the "
        "counter), wire tools/compound_unattended.py so the cursor advances without a "
        "human, or delete the project's LEARNINGS_PENDING.md to dismiss deliberately.")


def assert_no_stale_markers(d=None) -> tuple[bool, str]:
    if d is None and not os.path.isfile(STATE):
        return True, "no state file -> no projects to check"
    d = _load_state(d)
    if d is None:
        return True, "state unreadable, skipping marker check"
    projects = d.get("projects", {})
    now = dt.datetime.now(dt.timezone.utc)
    stale = []
    for pid, info in projects.items():
        iso = (info or {}).get("last_run_iso")
        if not iso:
            continue
        try:
            t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            continue
        age_days = (now - t).days
        if age_days > STALE_MARKER_DAYS * 3:
            stale.append(f"{pid[:50]} ({age_days}d)")
    if stale:
        # Was "(advisory)" and returned True, which made this the only check in the file
        # that could not fail. Ninety days without a cursor advance IS the degradation
        # this tool exists to report, and reporting it as a pass is how it stayed unseen.
        return False, (f"projects with cursors older than {STALE_MARKER_DAYS * 3}d: "
                       f"{stale[:3]}{' and more' if len(stale) > 3 else ''}")
    return True, f"all {len(projects)} project cursors within sliding window"


def main() -> int:
    checks = [
        ("sentinel-file", assert_sentinel_present),
        ("sentinel-registered", assert_sentinel_registered),
        ("state-shape", assert_state_valid),
        ("consolidation-advances", assert_consolidation_advances),
        ("marker-staleness", assert_no_stale_markers),
    ]
    failed = []
    print("=== compound_audit ===")
    for name, fn in checks:
        ok, msg = fn()
        tag = "OK " if ok else "FAIL"
        print(f"  [{tag}] {name}: {msg}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"COMPOUND_AUDIT FAIL: {failed}")
        return 5
    print("COMPOUND_AUDIT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
