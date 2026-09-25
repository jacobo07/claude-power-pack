# UWCP S0-S1 incidents -- 2026-09-25 (causal evidence; UKDL distillation at S10)

Program: Universal Workstream Continuity Plane (`vault/specs/uwcp.md`). Host: Windows, starved
(858 MB free of 32 GB during the runs below), several live panes committing to the same tree.

## I-1 The oracle raced its own subject (false 22/25)
- **Evidence:** `test_gsd_x_goal_cli.py` reported 22/25 (V-CLI-CLOSURE-CLEARS,
  CLEAR-IS-NOT-CONVERGED, CONVERGED-IS-REACHABLE). Same suite: 25/25 at HEAD `c58e00f` in a clean
  `git worktree`, and 25/25 on the working tree minutes later.
- **Root cause:** the suite spawns `gsd_x_goal.py reconcile` subprocesses; it was running in the
  background while I added `blocking_reason(...)` to `reconcile.py` one edit BEFORE its import
  line. Every subprocess in that window raised NameError, which the suite read as "closure never
  clears".
- **Class:** CLASE 2 (the plan assumed a stable tree) -- and the writer that moved it was me.
- **Why the architecture allowed it:** a wide oracle with a long wall time (8+ min under
  starvation) and an editor working in its observation domain; nothing bracketed the run.
- **Fix / regression:** never edit a module a running suite exercises; a result-blocking suite
  runs foreground (Rule I). The disambiguating instrument -- same suite, clean worktree at HEAD --
  is now the standard move before blaming a change.
- **Sibling exposure:** `test_gsd_x_goal_mutation.py` mutates the goal modules ON DISK while it
  runs; any edit during that window would be both clobbered by its restore and misjudged. The
  suite already refuses a dirty tree (exit 2, INSTRUMENT_FAILED) -- a correct design that saved
  this run from a worse version of I-1.

## I-2 A test name that claims more than it measures (V-CHAOS-7-REPLAY)
- **Evidence:** characterization `e6b6411` showed a NEW receipt for an epoch that had already
  ended LOST was ingested. The KSEIP chaos gate "replaying a receipt after the epoch ended is
  refused" passed only because it replayed the SAME receipt, so the duplicate check fired.
- **Root cause:** the red path was driven with an input that a different guard also rejects.
- **Fix:** epoch fencing (`cf4d71b`) makes the claim true; the characterization is the
  regression. **Pattern:** drive a guard's red branch with an input ONLY that guard can reject.

## I-3 A mutation snippet that occurs twice
- **Evidence:** `if e.state == "ended":` exists in both `end()` and `ingest_receipt()`; the drill
  harness refused (HARNESS-FAILED, count 2) instead of mutating the first copy.
- **Pattern:** a mutation tool that guesses which occurrence to change proves nothing about the
  guard; refuse ambiguous snippets and widen them (multi-line, eol-aware -- epoch.py is CRLF).

## I-4 Guard behaviour: a partial Read does not reset anti-thrash
- **Evidence:** after 3 Edits to `epoch.py`, a Read with offset/limit did not reset the counter;
  the next Edit was blocked again. A full Read did reset it.
- **Status:** observation, not yet reproduced deliberately; recorded so the next session does not
  loop on the partial-read recovery the block message offers.

## I-5 The goal engine is unreachable from any live surface
- **Evidence:** `modules/liveness/reachability.py` lists all 16 `gsd_x/goal/*` modules ORPHAN;
  their only entrance is `tools/gsd_x_goal.py`, outside the scanner's aperture, and no command,
  agent or hook references it.
- **Consequence:** a capability that is correct, tested and canonical is not delivered.
  UWCP S6 wires it (placement rule in `/cpp-gsd-long`, VPS sweep cron); S1 modules declared PLANNED.

## I-6 Live concurrent writer on the file a slice needed
- **Evidence:** `tools/gsd_mission.py` received 4 commits from another pane between 13:42 and
  14:36 (workstream binding, card changes), the last 3 minutes before S1-11 was due to edit
  `render_card`.
- **Decision:** the card-from-brief merge is deferred until that writer is quiet; S1-11 extends
  only the provider file. Following "prefer a new file over a shared one while another writer is
  live" -- measured, not assumed.
