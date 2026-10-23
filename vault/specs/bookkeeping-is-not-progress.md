---
covers: [progress_fingerprint, no_progress, bookkeeping, idle-epoch, STATE.md, RESUMPTION.md]
status: LIVE
date: 2026-10-23
---
# Bookkeeping is not progress (mission progress fingerprint)

## Incident (measured)
GEX44 a7-env, SkyParty spawn workstream: missions m-95e10a5bb636 and its budget renewal m-01e5d5509ee6 ran
~54 epochs (2026-10-22 23:00 -> 2026-10-23 06:56) while two Owner questions sat unanswered in a DIFF file.
Each epoch committed only `.planning/workstreams/skyparty-spawn/STATE.md` + `RESUMPTION.md` ("no Owner input,
no unit"). `progress_fingerprint` hashed `HEAD^{tree}`, so every bookkeeping commit read as progress, the
`no_progress` halt (3 unchanged epochs, terminal, never renewed) never fired, and the budget halt renewed.
(The a7-env copy of gsd_mission.py was also older and had no `no_progress` halt at all.)

## Change
`progress_fingerprint` reads the tree with bookkeeping left out:
- top-level `git ls-tree HEAD` minus the `.planning` entry, plus `git ls-tree -r HEAD -- .planning` minus
  `.planning/**/STATE.md` and `.planning/**/RESUMPTION.md`;
- `git status --porcelain` minus the same paths;
- `git diff HEAD --shortstat` with those paths excluded by pathspec;
- `_planning_artifacts` (for git-excluded `.planning/`) skips RESUMPTION.md as it already skipped STATE.md.
Anything else under `.planning/` (plans, context, research) still counts, as does any product change.

## Acceptance
`tools/test_progress_fingerprint_planning.py` 13/13: tracked STATE dirt is still, a STATE+RESUMPTION-only commit
is still, a committed plan moves, product dirt moves, the kill switch restores the old reading. RED before the
change: 11/13 (the two bookkeeping gates). `test_gsd_mission.py` 233/233, `test_wake_progress.py` 11/11.

## Rollback / kill switch
`CPP_PROGRESS_BOOKKEEPING=count` restores the HEAD^{tree} reading. Revert = this one commit.

## Not in this change (named, not done)
Parking a mission that waits on the Owner and waking it on a new Owner answer file is project-specific; with
this change such a mission halts `no_progress` after 3 idle epochs (terminal, not renewed) and is re-armed after
the answer. The worker-side rule (never commit an idle epoch; blocked branch != blocked mission) is in the
SkyParty workstream's OWNER_REF28.md and in the KobiiCraft UKDL.
