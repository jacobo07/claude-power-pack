# Exact-target continuation -- lessons from the false COMPACTION LANDED (2026-09-18)

Spec: `vault/specs/exact-target-continuation.md`. Dataset: `vault/datasets/gsd_x/claims.jsonl`
GSDX-C01..C11. Staged here because `ukdl-universal.md` had another writer's uncommitted
hunks at the time.

**PROMOTED 2026-09-19 in `1b2d6f4`** — these rules now live in
`vault/knowledge_base/ukdl-universal.md` under "Exact-Target Continuation (GSD X)", with
their ids, plus two new traps from the run that promoted them (T-CONT-06, a `/compact` tail
is the same line in two opposite states; T-CONT-07, a confirmation cannot see a row its
window excludes). This file is kept as the origin record, not as a second source of truth:
edit the UKDL, not this.

## What happened, in one paragraph

Session 8178f7d0 was restarted with `--resume`; a resumed session reads ~17% context. The
watchdog's rule "context below the rearm floor + autorun marker + no flags" read that as a
landed compaction, 25 hours after the last real one. It asked the model to print
`/d1-continue`, then a daemon typed that command, with Enter, into whichever Cursor window had
focus. The session lived in an Orca terminal. Two minutes earlier the same daemon typed
`/absw2-continue` for another session the same way. Neither command reached any Claude
transcript. The Owner typed it by hand at 14:26.

## HARD RULE candidates

- **HR-CONT-01 -- A lifecycle state is claimed only from its post-condition.** "Compaction
  landed" requires the host-written `compact_boundary` row newer than the cycle reference.
  A proxy (a low context reading) is produced by other events too -- here, a restart.
- **HR-CONT-02 -- Foreground is presentation, never identity.** No automated input may be
  routed by window focus, window title or "the active terminal". Every effect names its
  target (Orca: `terminal send --terminal <handle>`; the CLI without it resolves the ACTIVE
  terminal -- the same trap one layer down).
- **HR-CONT-03 -- No exact target, no keystroke.** A missing or ambiguous target refuses and
  is ledgered. A delayed continuation is recoverable; a command in the wrong session is not.

## PROCESS RULE candidates

- **PR-CONT-01 -- Separate the stages and never promote one into the next:** requested ->
  target resolved -> transport accepted -> consumed (transcript row) -> mission advanced.
  `accepted` from a PTY write is transport only.
- **PR-CONT-02 -- Capture identity at the point of observation.** The session's own hook
  records its `ORCA_PANE_KEY`; a sweep running outside the session uses that record.
- **PR-CONT-03 -- Re-resolve immediately before the effect** and require the same
  incarnation; reconcile against the transcript before any resend; bound attempts per
  logical continuation id.
- **PR-CONT-04 -- Resource admission is its own predicate.** `wait-ram` succeeding says
  nothing about compaction or delivery.

## TRAP candidates

- **T-CONT-01 -- A correct foreground during testing hides missing routing.** Every drill
  here marks the WRONG pane active, so an unaddressed call lands visibly in it.
- **T-CONT-02 -- Printing a command looks like automation.** The UI showed `/d1-continue`;
  nothing had been delivered.
- **T-CONT-03 -- A hook timeout on UserPromptSubmit discards output, not the prompt.**
  Measured: prompt at 14:26:01, hooks cancelled at 14:26:11/18, assistant at 14:26:21.
- **T-CONT-04 -- A fallback added for availability reopens the incident.** The terminal
  inbox (e5ed2d3) was exact, but it fell back to foreground SendKeys after 10 s without an
  answer -- which is exactly what an Orca-hosted session produces. The fallback is now an
  explicit Owner opt-in (`CPP_LEGACY_FOREGROUND_SENDKEYS=1`).
- **T-CONT-05 -- The Orca runtime pointer can vanish while the app runs.** Observed
  `runtime_unavailable` with Orca X alive; the transport reports it as
  BLOCKED_BY_DELIVERY_PROVIDER instead of guessing.

## Instrument errors of my own, in the same session

- `Get-Process -Name 'Orca X'` returned nothing for a running process; a regex over
  ProcessName found it. I nearly recorded "Orca is not running".
- A lowercase grep for `no-own-window` missed the gate `V-ACPS-D-NO-OWN-WINDOW-SENDS`,
  which pinned the very behaviour being removed.
- An assertion excluding the substring `focused window --` matched my own new refusal
  sentence; the intent (no LEGACY wording) had to be asserted directly.
