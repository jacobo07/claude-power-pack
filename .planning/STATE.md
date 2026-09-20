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

### 2026-09-20 — the guard was inaudible, and the confirmation oracle has a gap

**Fixed and pushed (`15bcdbe`).** `_run_inner` returned the auto-reset advisory
before the whole continuation path — used_pct stamp, endpoint refresh, resume
confirmation, rearm, post-compaction resume, snapshot, crossing. The advisory
is once-per-session, so it cost one Stop; but it fires on CONTEXT PRESSURE,
which is the same condition that produces a crossing, so the one Stop it could
take was the one most likely to matter. Armed runs now keep the path and the
advisory is layered on. `tools/test_watchdog_overlay_precedence.py` 4/4, both
poles; mutation 3/4 red on its own assertion, restore SHA-256 verified.
GSDAC 26/26, GSDLR 93/93, OVERLAY_GUARD 4/4, REARM 8/8 (which names this run's
wall: `(35,40,30)` accepted).

**Two premises this session inherited are FALSE, measured:**
- The host DOES write `compact_boundary`. Three rows in this transcript, newest
  2026-09-20T12:43:08Z. The single `compaction_unobserved` was a compaction
  that never happened, not a row the host failed to write. F2 as stated is
  closed; what remains is a delivery question, not a recording one.
- There was no rearm deadlock. The advisory flag cleared on its own and the
  next Stop resumed at used_pct=24.

**OPEN, and now the top blocker for the acceptance gate.** At 13:11–13:13 the
run re-entered itself with no human: `resume_requested` → `resume_dispatched`
→ inbox ack `status:"sent"`, `terminal:"claude"`, `window_cwd` = this project.
`/gsd-autonomous` then EXECUTED. But **no user row records that submission**,
so `user_issued_command_since` reads False and `resume_confirmed` cannot fire.
On 2026-09-19 the same flow left `type=user, isMeta=True, list['text']` at
09:08:06.552Z and confirmed. Control: the Owner's own typed messages today ARE
recorded (`go ahead`, 14:51:39.917Z), so the host has not stopped recording.
Two readings remain open — the host did not record this delivery, or the
delivery reached the model by a path that produces no user row — and they are
not distinguishable from the archaeology. **Do not weaken the oracle to close
this.** The next watchdog-initiated crossing is to be watched live end to end;
that observation separates them, and context is at 36% against a 40% wall.

**F5 ROOT CAUSE FOUND (2026-09-20 15:5x), and it explains the working case too.**
`extension/src/extension.js:103-107` types the line and then writes
`status:"sent"` unconditionally:

    term.sendText(req.text, false);
    await sleep(ENTER_DELAY_MS);
    term.sendText("\r", false);
    writeAck(..., status: "sent", ...)

The ack asserts only that `sendText` was CALLED. Readiness is read at :80 from
`~/.claude/sessions/<claude_pid>.json`, a registry written at TURN BOUNDARIES,
so it is stale by construction between them — and the decision is not atomic
with the Enter. The model that fits every observation:

- typed while genuinely idle -> submitted at once -> ordinary user row ->
  `user_issued_command_since` matches -> `resume_confirmed` fires. This is
  2026-09-19 09:08:06, and it is the only reason C6 is marked PROVEN.
- typed while BUSY -> Claude Code QUEUES the line -> it is delivered at the
  next turn end -> it EXECUTES but leaves no ordinary user row -> the oracle
  reads False and the cycle can never confirm.

The 13:12 resume is the second case exactly: typed mid-turn, and
`/gsd-autonomous` reached the model at 14:06 — the moment that turn ended. The
line was never lost. It was queued, and the confirmation oracle cannot see a
queued delivery.

So F5 is NOT "the host stopped recording". It is a readiness check that expires
before the effect it authorises, plus an ack that reports the call instead of
the postcondition. Both are fixable here and neither needs the C6 oracle
weakened: re-read readiness immediately before the Enter (or refuse), and make
the ack carry a verified postcondition rather than `sendText` having returned.

**Two-pane POSITIVE leg, negative half: measured live against a real
delivery.** 33 other live panes examined with the product's own predicate at
the moment of a genuine inbox delivery; **zero** received the line. No window
was opened and no Owner action was used, which retires the "needs a second
pane" framing for that half. Pane A's half is blocked on the same missing row
as the confirmation above. (Count soft by one: the glob returned pane A twice.)

## Phases

- Phase 1: Two-pane exactness drill — IN PROGRESS, refusal half PROVEN LIVE
  (`.planning/01-EVIDENCE-refusal-legs.md`). Task 1's tool landed and `probe` is
  7/7 with its red branch driven. Tasks 2-3 split cleanly in two, and the half
  that needs no operator is now real: an **owned** request was answered by this
  window in 0.28 s with `refused / session-unreadable`, and an **unowned** one
  was ignored by every window for 15 s with no ack and nothing typed — leg A
  being the positive control that makes leg B's silence mean anything. The
  negative control was checked where a keystroke would have landed (this pane's
  own transcript): 0 typed rows, against an 801-occurrence positive control.
  The **positive** leg — the line really typed into a subject's terminal while a
  second pane gets nothing — is still unproven: it needs a live subject session
  in a terminal an extension owns, and at drill time the host had 766 MB free of
  32 GB (2.4 %), below the run's own 1500 MB floor, so a second window was
  refused on those grounds rather than attempted.
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
