---
gsd_state_version: "1.0"
milestone: v1
status: awaiting_acceptance_gate
last_updated: "2026-09-21T21:15:00.000Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 2
  completed_plans: 2
current_phase: 05
current_phase_name: Close the continuation debts
---

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

- Phase 5: Close the continuation debts — **COMPLETE** (2026-09-21). All three
  debts closed; debt 3 was answered at the checkpoint and carried out.
  Debt 1 (`839a14c`): the ledger `armed` row derives its cwd from the marker
  dict already loaded two lines above, so two records of one arming can no
  longer disagree; `:98` deliberately untouched, because the asymmetry between
  the two writes WAS the defect. GSDLR 96/96, two mutations on distinct
  assertions, restore `3bc96c1ab2fd`.
  Debt 2 (`f702c5a`): `argumentTail()` moved out of `extension.js` — which
  requires vscode, so nothing could drive the predicate that types into a live
  terminal — into `terminal_inbox.js`, already vscode-free and already run by a
  Python gate. Seven synthetic cases, `ok=23 → 30`, three mutations on distinct
  assertion sets, restore `4400f98c3c86`. Two instruments repaired in the same
  task: an equality-pinned population count (permanently red for *growing*, and
  satisfied as a substring by `ok=120`) and a gate pinning the literal
  `enters: 2`, which made a correct change fail a check measuring one build's
  spelling.
  Debt 3 (`c71e9a4`): four items inventoried, no reader found, then answered by
  the Owner and carried out at 21:11:49 — backup first at
  `~/.claude/backups/residue-20260921-211149\` (4 files, 51,130 B), every copy
  re-hashed before anything was removed, `RESIDUE_DELETED=4/4`. The readers
  finding was then TESTED rather than trusted: MADM 7/7, INTENT 9/9, GSDLR 96/96
  afterwards. Digests and harness in `05-RESIDUE-INVENTORY.md`.
  Summary `da489a0`.

### Open, and each needs the Owner rather than more work

1. **The live extension mirror.** Cursor executes
   `~/.cursor/extensions/kobii.pp-sessions-0.4.0`, which the auto-mode
   classifier refuses to write (HR-001). `scratchpad/apply-argtail-helper.ps1`
   is staged — backs up, copies, `node --check`, live selftest — and a window
   reload is required after it. Until then `f702c5a` changes nothing at runtime
   and `V-INBOX-LIVE-MATCHES-REPO` stays red. That gate is correct; it must not
   be skipped or re-baselined.
2. **Whether `auto-compact-sendkeys-daemon.ps1` gets a repo mirror.** It has no
   version-controlled copy here, so this phase's edit to it (SENT line now
   carries `enters=` and `arg_tail=`) is unversioned. Same gap class as the
   router edit in phase 3.

### The fifth debt — CLOSED 2026-09-21 (`7f88790`)

Its shape was sharper than its name. `_recover_via_transport` wrote the trigger
flag and returned `"terminal-inbox"` with **no ledger row**, while the watchdog's
equivalent branch records `delivery_inbox_requested` (`context-watchdog.py:675`).
Two producers of one effect, one of them mute — so a delivery that **succeeded**
could not be counted by the milestone gate it was serving. Found by breaking this
session's deadlock with a hand call to `write_trigger`: it worked, and it left no
trace.

The row now lives where the flag is written, not in the caller — a caller-side
row is a convention, and this one had already been forgotten once. `kind` is
derived from the payload just written (same rule as the `armed` row at
`gsd_autorun_marker.py:253`); `producer` is recorded because the event name now
has two writers, and a reader that cannot tell them apart cannot tell a swept
re-delivery from a watchdog crossing.

GSDLR 96/99 → **99/99**; CWIRE 14/14, GSDAC 26/26, CTRUTH 15/15 unchanged. Three
mutations, each landing on its own assertion set, restore byte-exact
(`a6fa53be3045d7ce`). **The gate's first version carried the very defect it was
written to catch** — it re-stat'd the marker file to rebuild a cid built from the
transcript's mtime, and so failed against a correct row. It now derives the
expected value from the sibling row the same action wrote, with the reason kept
in the comment.

### The delivery deadlock, diagnosed 2026-09-21

Two halves. *Transient:* the extension defers while the session is busy and the
deferral clears on IDLENESS, not on a timer — so a turn that keeps working after
emitting its `/compact` line spends the daemon's 310 s budget (18:12 refused
after 310 s; 18:24 sent in 3 s). *Permanent:* after a `refused`, nothing
re-arms, because `THRESHOLD_REARM_PCT = 45` (`context-watchdog.py:49`) clears the
debounce only below 45 % used — reachable only by compacting, which is what the
refusal was carrying. The rule this produces: **the turn that emits a compact
line does no further tool work.**

The narrow-wall proof is the milestone's acceptance gate, not a phase: it is
produced by this run crossing its own wall while executing the phases above,
and read off `gsd_long_run.py report`.

### Acceptance gate, MEASURED 2026-09-21 21:17 — and a correction

`report --session 9af80e55` reads **PARTIAL: crossings 3, confirmed 1,
proven_window 2, window_confirmed 1.**

| crossing | resume confirmed |
|---|---|
| 2026-09-20T21:56:22Z | — |
| 2026-09-21T18:11:46Z | — (the 310 s refusal; see the deadlock above) |
| **2026-09-21T18:52:03Z** | **2026-09-21T18:56:24Z**, `/gsd-autonomous` |

**The correction, and it is mine.** Everything in this file and in commits
`da489a0`, `f59c471` and `e879d18` written before 21:17 says *"crossings 2,
confirmed 0, window 0/2"*. That number was carried forward from a pre-compaction
summary and never re-measured, while the third crossing had already confirmed at
18:56:24 — before any of those commits were written. The instrument was one
command away the whole time. A measured claim restated from memory is not a
measured claim, and the commits are left standing with the wrong figure rather
than rewritten, because the correction belongs where a reader will look.

**What this means:** the 18:52 crossing is the FIRST confirmed resume this
session has produced, and the second confirmed one this estate has ever recorded.
`PROVEN` needs exactly one more crossing whose resume confirms. Nothing about the
wall is blocking it; it needs context to be spent on real work until the wall is
crossed again.
