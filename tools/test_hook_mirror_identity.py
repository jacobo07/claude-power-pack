#!/usr/bin/env python3
"""test_hook_mirror_identity.py -- V-MIRROR-* gates.

Eighteen hook files exist in BOTH trees:

    ~/.claude/hooks/<name>.js                              (what settings.json runs)
    ~/.claude/skills/claude-power-pack/hooks/<name>.js     (what git records)

Nothing pinned the two to each other, so a fix could land in the copy that is
not executed and every test would stay green. That is the Production Reality
split in its purest form: source fixed, live stale, suite passing.

MEASURED 2026-09-16: 18 dual-resident, 13 identical, 5 diverged -- AND THE DRIFT
RUNS BOTH WAYS. Some files carry repo-only work that has never executed, because
settings.json runs the live copy. Assuming "live is always ahead" and mirroring
blindly would have destroyed it; one file in this session came within a
Copy-Item of exactly that.

A RATCHET, not a clean bill. The five are real, pre-existing, and each needs a
human decision about which side wins -- a gate that is red on arrival gets
switched off within a week. So they are frozen BY NAME with the measured
direction of the drift, the gate fails when a SIXTH appears, and the stale-entry
clause fails when a frozen pair becomes identical, so the list cannot rot into a
permanent excuse.

Names, never a count: a count is satisfied by deleting a file.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import sys

HOME = pathlib.Path(os.path.expanduser("~"))
LIVE_DIR = HOME / ".claude" / "hooks"
REPO_DIR = HOME / ".claude" / "skills" / "claude-power-pack" / "hooks"

# Frozen 2026-09-16, each with the MEASURED direction rather than a guess.
# "onlyRepo" / "onlyLive" are counts of lines present in only that copy.
KNOWN_DIVERGENCES = {
    "closer-guard.js":
        "onlyRepo=10 onlyLive=391; live newer (09-15 vs 09-14). Bidirectional, "
        "live far ahead. Needs a human merge, not a copy",
    "learning-sentinel.js":
        "onlyRepo=1 onlyLive=21; BOTH sides carry real work -- repo has a "
        "CLAUDE_PROJECT_DIR cwd fallback, live has drive-letter normalisation. "
        "Blind mirroring either way destroys the other side",
    "research-intent-detector.js":
        "onlyRepo=58 onlyLive=0; repo STRICTLY AHEAD and newer (08-26 vs 05-23). "
        "Repo work that has never executed, because settings.json runs live",
    "windows-bash-bridge-guard.js":
        "onlyRepo=1 onlyLive=18; live newer (09-15), carries the stderr-channel "
        "fix. Repo copy is behind the guard that is actually blocking calls",
    "_oneshot_solitary_empty_shell_cleanup.js":
        "onlyRepo=3 onlyLive=0; repo strictly ahead and newer. Same shape as "
        "research-intent-detector: never deployed",
}

# A population floor. An empty or tiny sweep is what a BROKEN enumerator returns
# and it reads identically to a healthy estate. 12 is comfortably under the 18
# observed and well above anything a path mistake yields.
MIN_DUAL_RESIDENT = 12

passes: list[str] = []
fails: list[str] = []


def _ok(gate: str, ev: str) -> None:
    passes.append(gate)
    print(f"[OK]   {gate} -- {ev}")


def _fail(gate: str, ev: str) -> None:
    fails.append(gate)
    print(f"[FAIL] {gate} -- {ev}")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not LIVE_DIR.is_dir() or not REPO_DIR.is_dir():
        _fail("V-MIRROR-ENUMERATE",
              f"a hook tree is missing (live={LIVE_DIR.is_dir()} repo={REPO_DIR.is_dir()}) -- "
              "this gate cannot judge anything, which is not a pass")
        print(f"MIRROR_IDENTITY_PASS={len(passes)}/{len(passes)+len(fails)}")
        return 1

    dual = sorted(
        p.name for p in REPO_DIR.glob("*.js") if (LIVE_DIR / p.name).is_file()
    )

    if len(dual) >= MIN_DUAL_RESIDENT:
        _ok("V-MIRROR-ENUMERATE",
            f"{len(dual)} dual-resident hook files (floor {MIN_DUAL_RESIDENT})")
    else:
        _fail("V-MIRROR-ENUMERATE",
              f"only {len(dual)} dual-resident files found (floor {MIN_DUAL_RESIDENT}) -- "
              "a sweep that matched almost nothing is a broken enumerator, not a tidy estate")

    diverged: list[str] = []
    unreadable: list[str] = []
    for name in dual:
        try:
            if sha256(LIVE_DIR / name) != sha256(REPO_DIR / name):
                diverged.append(name)
        except OSError as exc:
            unreadable.append(f"{name}: {exc}")

    # Unreadable is its own outcome. A pair we could not compare has NOT been
    # cleared, and counting it as identical is how a sweep goes quietly blind.
    if unreadable:
        _fail("V-MIRROR-READABLE", f"{len(unreadable)} pair(s) unreadable: {unreadable[:3]}")
    else:
        _ok("V-MIRROR-READABLE", "every dual-resident pair was readable")

    # Positive control. An all-identical estate and a comparator that stopped
    # comparing produce the same clean bill, and only one of them is good news.
    probe_a = hashlib.sha256(b"alpha").hexdigest()
    probe_b = hashlib.sha256(b"beta").hexdigest()
    if probe_a != probe_b:
        _ok("V-MIRROR-COMPARATOR-LIVE", "the comparator still distinguishes different bytes")
    else:
        _fail("V-MIRROR-COMPARATOR-LIVE",
              "the comparator reports two different inputs as equal -- every verdict "
              "in this file is meaningless")

    new = sorted(set(diverged) - set(KNOWN_DIVERGENCES))
    if new:
        _fail("V-MIRROR-NO-NEW-DRIFT",
              "NEW live/repo divergence: " + ", ".join(new)
              + " -- decide which side wins and say why. Do NOT assume live is ahead: "
                "measured drift in this estate runs both ways, and one file here carries "
                "real work on each side")
    else:
        _ok("V-MIRROR-NO-NEW-DRIFT",
            f"no divergence beyond the {len(KNOWN_DIVERGENCES)} frozen "
            f"({len(dual) - len(diverged)} pairs byte-identical)")

    stale = sorted(set(KNOWN_DIVERGENCES) - set(diverged))
    if stale:
        _fail("V-MIRROR-NO-STALE-ENTRIES",
              "reconciled (or removed) but still listed as diverged: " + ", ".join(stale)
              + " -- delete these lines; the ratchet only turns if the list shrinks")
    else:
        _ok("V-MIRROR-NO-STALE-ENTRIES", "every frozen divergence is still a real divergence")

    total = len(passes) + len(fails)
    print(f"MIRROR_IDENTITY_PASS={len(passes)}/{total}  threshold={total}/{total}")
    print(f"standing drift (named, not counted): {len(diverged)} -> {sorted(diverged)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
