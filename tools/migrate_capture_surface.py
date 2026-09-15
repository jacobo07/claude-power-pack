#!/usr/bin/env python3
"""Idempotent settings.json migration: widen a NARROW capture registration.

A producer can be registered, firing and recording while blind to most of
its subject, because the entry carrying its name matches fewer tool
surfaces than the hook's own code handles. `capture_liveness.py` measures
that gap; this applies the one correction it justifies.

WHAT IT IS NOT
--------------
It is not a bulk widen. Evaluated 2026-08-27, of the five `Bash`-matched
registrations on this host, TWO should change and three should not:

  bug-hunter-ceps-bridge.js  WIDEN  -- declares Bash AND PowerShell since the
                                       2026-08-14 repair; 75.5% of command
                                       traffic here is PowerShell
  PreToolUse-Bash-chain      WIDEN  -- carries cascade_check_bash.js, the sole
                                       live enforcement of HR-CASCADE-001..005.
                                       It accepts both surfaces in code and is
                                       inert on PowerShell purely because of
                                       this matcher, so HR-CASCADE-002 -- whose
                                       flagship pattern is `Remove-Item -Recurse -Force`
                                       -- cannot fire on the only surface where
                                       that command is ever written
  bug-hunter-learning.js     NO-OP  -- its code hard-rejects non-Bash
                                       (`tool_name !== 'Bash'`), so widening
                                       the matcher changes nothing
  osa_deploy_detector.js     NO-OP  -- same self-rejection
  tty-restore.js             KEEP   -- narrow ON PURPOSE: DECSET 1004 focus
                                       reporting leaks from the Bash bridge,
                                       not from the PowerShell tool

CORRECTION, same day. An earlier revision of this file said the chain must be
KEPT because it carries windows-bash-bridge-guard.js, which blocks git/npm via
Bash to force them onto PowerShell -- so widening it would block the surface
the doctrine redirects to. That is wrong twice over: the guard self-rejects
non-Bash at its first line, so widening is harmless to it; and the chain's
LAST entry is the cascade guard, which the earlier reading missed because the
chain definition ran past the lines that were read. The disposition rule held;
the evidence behind one row did not. Read the whole chain before judging it.

The two self-rejecting entries are why the candidate set is bounded rather
than derived from "every narrow matcher": widening those would assert in
settings.json a coverage their own code declines to honour.

SAFETY CONTRACT (every guard must hold or the entry is left untouched)
  1. The hook must be in CANDIDATES -- an explicit, reviewed allow-list.
  2. `capture_liveness.coverage_of` must independently report NARROW. The
     evidence comes from the measuring owner, never restated here, so the
     two cannot drift apart.
  3. The hook's source must not hard-reject the surface being added. A
     `tool_name !== 'X'` guard means widening the matcher buys nothing and
     would leave settings.json claiming a coverage the code refuses.
  4. Only the matcher string changes. No entry is added, removed or
     reordered, and no other event is touched.

IDEMPOTENT: a second run finds nothing NARROW -> no backup, no write.
Default is DRY-RUN. Pass --apply to write (backup taken and verified first).

    python tools/migrate_capture_surface.py           # dry-run
    python tools/migrate_capture_surface.py --apply   # apply
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.capture_liveness as cl  # noqa: E402
from tools.capture_liveness import (  # noqa: E402
    PRODUCERS, coverage_of, declared_surfaces,
)

# Imported, never re-derived. plan() reads capture_liveness.SETTINGS and
# apply() used to read a private copy, so a test patching one wrote the
# other -- and the one that writes is the Owner's live config.
from tools.capture_liveness import SETTINGS  # noqa: E402

# Guard 1. Reviewed, bounded, and deliberately not "everything narrow".
CANDIDATES = {"bug-hunter-ceps-bridge.js", "PreToolUse-Bash-chain"}


def self_rejects(source: Path | None, surface: str) -> bool:
    """Does the hook's own code refuse this tool surface outright?

    Matches the `tool_name !== 'Bash'` shape three hooks on this host use.
    A hook that rejects everything but Bash cannot be helped by a wider
    matcher, and widening one would put a false coverage claim in
    settings.json -- the exact confusion this whole layer exists to end.
    """
    if not source or not Path(source).is_file():
        return False
    try:
        text = Path(source).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for stripper in (re.compile(r"/\*.*?\*/", re.S),
                     re.compile(r"(?m)^\s*//.*$")):
        text = stripper.sub("", text)
    # The SET of tools named across every `!==` comparison, not the first
    # one that differs. `tool_name !== 'Bash' && tool_name !== 'PowerShell'`
    # is the canonical "handles exactly these two" guard, and reading its
    # first clause alone reported the hook as rejecting the very surface it
    # accepts.
    named = {m.group("only") for m in re.finditer(
        r"tool_?[Nn]ame[^\n]{0,40}?!==?\s*['\"](?P<only>\w+)['\"]", text)}
    return bool(named) and surface not in named


def _entries_for(marker: str, event: str | None) -> list[str]:
    """Which settings.json entries carry this marker, named for the preview.

    apply() rewrites EVERY entry carrying the marker; the dry-run used to
    show one line per marker and say nothing about how many that was.
    """
    try:
        blob = json.loads(cl.SETTINGS.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    hooks = blob.get("hooks") or {}
    scoped = {event: hooks.get(event) or []} if event else hooks
    out = []
    for ev, entries in scoped.items():
        for entry in entries or []:
            joined = " ".join(
                str(h.get("command", "")) for h in entry.get("hooks") or [])
            if marker in joined.replace("\\", "/"):
                out.append(f"{ev}/matcher={entry.get('matcher')!r}")
    return out


def plan() -> list[dict]:
    """Entries this migration would change, with the evidence for each."""
    actions = []
    for spec in PRODUCERS:
        marker = spec.get("hook_marker")
        if not marker or marker not in CANDIDATES:
            continue
        cover = coverage_of(spec)
        if cover["state"] != "NARROW":          # guard 2
            continue
        declared = declared_surfaces(spec.get("hook_source")) or set()
        blocked = [s for s in cover["uncovered"]
                   if self_rejects(spec.get("hook_source"), s)]   # guard 3
        addable = [s for s in cover["uncovered"] if s not in blocked]
        # A blocked-only entry is still REPORTED. Dropping it made main()
        # print "nothing NARROW and addable", which is the same sentence a
        # fully-migrated tree prints -- so an operator could not tell a
        # finished migration from one the code refuses to allow, while
        # capture_liveness stayed red.
        actions.append({
            "marker": marker,
            "add": addable,
            "declared": sorted(declared),
            "matched": cover["matched"],
            "refused_by_code": blocked,
            "entries": _entries_for(marker, spec.get("event")),
        })
    return actions


def apply(actions: list[dict]) -> tuple[int, str]:
    """Rewrite the matcher of each planned entry. Returns (changed, backup)."""
    raw = cl.SETTINGS.read_text(encoding="utf-8-sig")
    blob = json.loads(raw)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = str(cl.SETTINGS) + f".bak-capture-surface-{stamp}"
    shutil.copy2(cl.SETTINGS, backup)
    if Path(backup).read_text(encoding="utf-8-sig") != raw:
        raise RuntimeError("backup verification failed -- refusing to write")

    changed = 0
    for action in actions:
        for entries in (blob.get("hooks") or {}).values():
            for entry in entries or []:
                joined = " ".join(
                    str(h.get("command", "")) for h in entry.get("hooks") or [])
                if action["marker"] not in joined.replace("\\", "/"):
                    continue
                if "matcher" not in entry:
                    # An entry with no matcher is universal already; giving
                    # it one would NARROW it.
                    continue
                current = str(entry.get("matcher") or "")
                parts = [p.strip() for p in current.split("|") if p.strip()]
                for surface in action["add"]:
                    if surface not in parts:
                        parts.append(surface)
                        changed += 1
                entry["matcher"] = "|".join(parts)

    cl.SETTINGS.write_text(
        json.dumps(blob, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # The backup check proved the COPY succeeded, not that what we wrote is
    # loadable. Re-read it; restore and raise if it is not.
    try:
        reparsed = json.loads(cl.SETTINGS.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        shutil.copy2(backup, cl.SETTINGS)
        raise RuntimeError(
            f"post-write parse failed ({exc}); {cl.SETTINGS} restored "
            f"from {backup}") from exc
    if set(reparsed.get("hooks") or {}) != set(blob.get("hooks") or {}):
        shutil.copy2(backup, cl.SETTINGS)
        raise RuntimeError("post-write event set differs; restored")
    return changed, backup


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the change (default is dry-run)")
    args = ap.parse_args()

    actions = plan()
    if not actions:
        print("CAPTURE_SURFACE: nothing NARROW and addable -- no change "
              "(idempotent: this is also what a second run prints)")
        return 0

    for action in actions:
        print(f"{action['marker']}")
        print(f"  declares : {'|'.join(action['declared'])}")
        print(f"  matches  : {'|'.join(action['matched']) or '(nothing)'}")
        print(f"  entries  : {len(action['entries'])} -> "
              f"{', '.join(action['entries']) or '(none)'}")
        if action["add"]:
            print(f"  ADD      : {'|'.join(action['add'])}")
        if action["refused_by_code"]:
            print(f"  BLOCKED by guard 3: "
                  f"{'|'.join(action['refused_by_code'])} -- the hook's own "
                  "code rejects this surface, so widening the matcher would "
                  "assert a coverage it will not honour. Fix the code first.")

    if not any(a["add"] for a in actions):
        print("\nNo addable surface. This is NOT the post-migration state: "
              "the gaps above are blocked by guard 3, and capture_liveness "
              "stays NARROW until the hooks accept the surface.")
        return 0

    if not args.apply:
        print("\nDRY-RUN. Re-run with --apply to write "
              f"(a verified backup of {cl.SETTINGS} is taken first).")
        return 0

    changed, backup = apply(actions)
    print(f"\nAPPLIED: {changed} surface(s) added. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
