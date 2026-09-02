# RESUMPTION — effective state

**Repo** `~/.claude/skills/claude-power-pack` · **branch** `frontier28/session-2026-08-26`
· **worktree** isolated. The main checkout is on another pane's branch
(`feature/knowledge-acquisition`, 41 commits, dirty) and must not be switched, reset or
merged into.

**Thesis.** The install location is a git working tree. `~/.claude/skills/claude-power-pack`
is at once the repo and the directory 11 live hook registrations execute from, so the bytes
that run are whichever branch a pane last checked out. Committed and pushed is not
installed.

## State

Measured, not assumed: of the 27 files this branch's 45 commits changed, **0 were identical
to the running tree**, 16 differed, 11 were absent. Two fixes sealed 2026-08-27 are not the
bytes executing. Three branches sit unmerged at 45 / 41 / 3 commits ahead of a `main` last
moved 2026-08-25.

`mirror_unpaired_audit.py` now carries the version dimension (EFFECTIVE / SHADOWED /
ABSENT_RUNNING / LOCAL_EDIT / NOT_HERE), typed by direction so a checkout that is merely
behind is never reported as a delivery failure. 14 gates, both previously-unreachable
branches driven by real fixtures. It runs in the umbrella under `mirror-divergence`
(the audit) and `effective-state` (the unit row).

Coherence anchor: `python tools/mirror_unpaired_audit.py --quiet` exits 1 and names
**5 SHADOWED** registrations. `python tools/capture_liveness.py` exits 1 and names
**PowerShell unobserved**. Both gaps are real and visible by design.

## The single Owner decision

Everything else collapsed into it. Three actions were forwarded from the prior session;
re-measured, **two were defective**:

- *Copy `hook-dispatcher.js` to `~/.claude/hooks/`* — **OBSOLETE and was harmful.**
  Installed and live both register 54 scripts; only this worktree (53) is behind.
  Executing it would have deleted `closer-guard.js` from production. Do not do it.
- *Run `migrate_capture_surface.py --apply`* — **unexecutable as written.** That file
  exists only on this branch, so the Owner cannot run it from the installed tree. Still
  correct in substance: two registrations declare `Bash|PowerShell` and match `Bash`.
- *Path debt* — recounted: 143 doc leaks, 38 code leaks (was 144 / 18). Standing, not
  blocking.

**DONE 2026-09-02:** `origin/main` fast-forwarded `9e69d11 -> ee5cb07`, 49 commits, zero of
main's commits lost, no merge commit, `feature/knowledge-acquisition` untouched. The work is
INTEGRATED and still NOT EFFECTIVE -- re-measured after the push, SHADOWED stayed at 5,
because the installed tree is still checked out on the other pane's branch. Integration and
delivery are two events; do not let the first be reported as the second.
HR-001 keeps `settings.json` and `~/.claude/hooks/` Owner-sovereign permanently — that is
governance working, not a task to keep forwarding.

## Next three actions

1. After integration, run `tools/mirror_unpaired_audit.py`; SHADOWED must fall to 0.
2. Then `migrate_capture_surface.py --apply`, then `capture_liveness.py` must flip to
   COVERED.
3. Then watch the corpus broaden past `bash:*`. It is 103 of 118 today while Bash is 27.6%
   of command traffic. Until it moves, coverage is configured, not proven.

## Start instruction

Run `python tools/mirror_unpaired_audit.py --quiet` and `python tools/capture_liveness.py`.
Their output is the current truth. Do not trust any prose claim of doneness over them, and
re-measure any forwarded action before executing it — two of the last three were wrong.
