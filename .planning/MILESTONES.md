# Milestones

## v1 continuation-proven-live (Shipped: 2026-09-21)

**Phases completed:** 5 phases, 2 plans, 3 tasks
**Closeout:** verified (all 5 phases `phase_complete` + `verification_status: passed`; pre-close artifact audit all clear)
**Audit:** `.planning/milestones/v1-MILESTONE-AUDIT.md` — status `tech_debt`, 0 blockers, 7/7 integration legs wired

**The milestone's own definition of done, and the measurement that met it:**

`tools/gsd_long_run.py report --session 9af80e55-…` returns **PROVEN** —
crossings 4, confirmed 2, `proven_window 2`, `window_confirmed 2`. The two
confirmed cycles are 18:52:03 → 18:56:24 and 20:48:26 → 20:54:39, both
`/gsd-autonomous`, both written by the Stop chain from the transcript.

**Key accomplishments:**

- **A run crossed its own context wall and came back, twice, with no human
  keystroke in the loop.** Wall crossed → one `/compact` emitted → typed into
  the session's own pane by the extension that owns it → compaction landed →
  Stop chain asked for the resume → typed → the run re-entered itself. This had
  never happened on this estate before 2026-09-19; before this milestone the
  ledger held zero confirmed resumes.
- **Exactness proved on the refusal side, live** (phase 1): an owned request
  answered `refused / session-unreadable` in 0.28 s, and 33 other live panes
  examined at the moment of a real delivery — zero received the line.
- **The UserPromptSubmit chain's 15 s cap diagnosed as scheduling, not budget**
  (phase 2): sequential execution at SUM meant a 2.2 s critical guard died
  behind an 11.4 s straggler. Per-chain deadline, critical hooks first.
- **14 exact-target continuation rules promoted into the UKDL** (phase 3), with
  the router sentence corrected to match what the code actually does.
- **A false premise measured rather than acted on** (phase 4): "seven markers
  are armed for sessions that no longer exist" was wrong — zero of the
  population qualified. The reaper now reads the session's own clock, and G1
  (a file the sweep refused to admit was invisible) was closed in `c3b493b`.
- **Four continuation debts closed** (phase 5), including a fifth found during
  the phase: `write_trigger` wrote the daemon's flag but no ledger row, so a
  manual re-arm was invisible to the very gate this milestone is measured by.

**Known deferred items:** carried in the audit's `tech_debt` block — no
re-derivable instrument for the chain-deadline measurement, the reap path has
never run in anger, `continuation_transport`'s own delivery and confirmation
path is unexercised on this host's route, the mirrored extension is on disk but
not loaded until a window reload, and six pre-existing mirror DRIFT pairs
predating this milestone.

---
