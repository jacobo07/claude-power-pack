# STATE — claude-power-pack

milestone: v1
milestone_name: continuation-proven-live

**Active milestone:** v1 `continuation-proven-live`
**Mode:** EXECUTION. The continuation machinery is built and unit-proven; what
remains is producing the live evidence and clearing the debts that attempt
exposed.
**Date:** 2026-09-19 · **Branch:** `feature/knowledge-acquisition`

## Mission

An unattended run must survive its own context wall: cross it, compact, and
re-enter itself through a continuation that reaches the session that owns it or
nobody at all. The autocompact thresholds are session-scoped so a running
session can narrow its own wall; the resume is typed by the terminal inbox that
owns the pane, never into whichever window has focus; and a resume counts only
when the transcript shows the command was really submitted.

## Where it stands

- Session-scoped autocompact thresholds: **landed**. `_thresholds(session_id)`
  reads `~/.claude/state/ctxwd-thresholds-<sid>.json` ahead of the launch-time
  env knob, under one shared validation rule. `tools/test_gsd_long_run.py`
  60/60; two mutations driven (file source removed → 57/60, session id not
  delivered to the accessor → 59/60), both restores verified by SHA-256.
- Terminal-inbox delivery into this pane: **measured live**. An owned but
  expired request was refused by the extension that owns this terminal, and a
  control request with foreign ancestors was ignored.
- A run that crossed a wall twice and came back: **half produced**. Two
  crossings; the first was refused by the old 60 s inbox TTL (fixed, `691c09a`),
  the second delivered its `/compact` and the compaction landed. The sweep then
  re-typed the same `/compact` line three times instead of the resume, because a
  `/compact` tail reads identically whether it was never submitted or was
  submitted and compacted — nine idle hours followed. Fixed in `64ec155`: the
  boundary row discriminates, and the resume is gated and fenced.
  `report` now reads **PARTIAL**: 3 crossings, and the second one's resume was
  confirmed at 09:30:37 — the first `resume_confirmed` this estate has ever
  recorded, which is the live test of the aperture fix (`f2462ee`) passing.
  PROVEN needs a second confirmed crossing.
- This session re-entered itself at 09:07:51 through the terminal inbox
  (`resume_requested` → `resume_dispatched` → the resumed command executing).
  The confirmation is written by the Stop chain at the end of the turn that
  follows, so it is pending rather than missing.

## Phases

- Phase 1: Two-pane exactness drill — IN PROGRESS (Task 1 tool landed, `probe`
  7/7 with its red branch driven; **blocked on the operator step** — Tasks 2-3
  need a live subject session this window's extension owns)
- Phase 2: UserPromptSubmit chain deadline — COMPLETE. Startup (spawn → deadline
  clock) measured at **42 ms** median, n=5, at 15.5% free RAM: neither the cap
  nor the clock is the defect, and the 19.4/17.1 s readings predate the deadline
  that fixed them. Total is a lower bound (synthetic payload). `02-SUMMARY.md`.
- Phase 3: Promote the exact-target lessons — COMPLETE. HR-CONT-01..03,
  PR-CONT-01..04 and T-CONT-01..07 now live in the UKDL with their ids
  (`1b2d6f4`), and the global router's "the SendKeys daemon presses Enter when
  Cursor is foreground" sentence is replaced by the exact-or-refused delivery
  that actually happens. Two cautions: the router edit is in `~/.claude/CLAUDE.md`,
  which is UNVERSIONED (same gap class as the daemon); and the UKDL working copy
  carries 1,029 uncommitted CEPS auto-append rows from a producer outside this
  session — preserved untouched, deliberately not committed, Owner decision owed.
- Phase 4: Reap the stale autorun markers — COMPLETE (`d0477b8`), and the
  roadmap's premise was false: **zero of nine markers are reapable**, not seven.
  What the phase delivered is the instrument. The reap clock read the
  transcript's file mtime, which host metadata rows (`custom-title`,
  `cost-state`, no timestamp of their own) advance without the session speaking
  — measured up to **19.0 h** of drift on a 48 h threshold. Liveness now reads
  the session registry and answers `live` or `unknown`, never `dead`: a session
  conversing 0.00 h earlier had no registry row at 11:40 and acquired one at
  12:24 under a new pid. And a marker's `cwd` was stored as typed (`"."` in 8 of
  9), so the sweep resolved it against itself — one project's `ALL_COMPLETE`
  could have unlinked every other project's marker. `sweep --explain` now names
  the clause holding each kept marker. GSDLR 72 → 87/87, four mutations driven
  (83/87, 85/87, 85/87, 86/87), one of which survived its first run and was
  re-pointed. Nothing was deleted: no marker qualifies, and a purge run on a
  rule written the same hour tests nothing.

The narrow-wall proof is the milestone's acceptance gate, not a phase: it is
produced by this run crossing its own wall while executing the phases above,
and read off `gsd_long_run.py report`.
