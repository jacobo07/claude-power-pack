---
covers: [exact-target-continuation, compaction-truth, continuation-transport, autocompact-resume, gsd-long-run, sendkeys-daemon, orca-terminal-send]
tier: T2
status: approved 2026-09-18 (Owner, one-click on the inline plan)
supersedes_parts_of: [gsd-long-run-v2.md, autocompact-per-session-flags.md]
---

# Exact-Target Continuation

## Incident (2026-09-18, session 8178f7d0, times UTC)

| time | evidence | meaning |
|---|---|---|
| 09-17 13:19 | last `compact_boundary` row in the transcript | last REAL compaction |
| 09-17 20:45 | autorun marker `ts` (schema v1, no `armed_at`) | run armed after that compaction |
| 09-18 12:41 | watchdog heartbeat `used_pct=?` | no context metric existed |
| 09-18 14:12 | transcript: session restarted (`--resume`) | a resumed session reads ~15-23% |
| 09-18 14:16:53 | heartbeat `used_pct=17.0 outcome=block`, ledger `resume_requested` | "COMPACTION LANDED" with no compaction |
| 09-18 14:19:16 | daemon log `SENT ... leaf=Orca X why=no-own-window typed=[/d1-continue]` | global SendKeys into the focused Cursor window |
| 09-18 14:17:11 | daemon log `SENT ... typed=[/absw2-continue]` (session 23c962ed) | a second wrong-target injection |
| 09-18 14:26:01 | first `/d1-continue` user row | typed by the Owner; no `resume_confirmed` ever |

Neither automated command appears in ANY Claude transcript. The target session is PID
62516 under `cmd.exe < Orca X.exe`: it lives in an Orca terminal, which a Cursor-focus
daemon can never reach.

The two `UserPromptSubmit` timeouts (Orca `claude-hook.cmd` at 10 s, Power Pack chain at
17.1 s against a 15 s cap) discarded hook OUTPUT only: the prompt was submitted and the
assistant began at 14:26:21.

## Root causes

1. `context-watchdog.py` read "context < rearm floor AND marker present AND no resume
   flags" as "compaction landed". Any low reading after arming or after a restart
   satisfies it.
2. `auto-compact-sendkeys-daemon.ps1` routes by Cursor window title, and its legacy
   `no-own-window` rule types into whatever Cursor window is foreground.
3. `wait-ram --session` records the id and targets nothing; `ORCA_PANE_KEY`, present in
   the session's env, was never used.
4. `resume_dispatched` without `resume_confirmed` escalates to nothing; the sweep's
   `recovered` path feeds the same foreground daemon.

## Authorities

| question | authority |
|---|---|
| did a compaction happen | a transcript row `type=system, subtype=compact_boundary` newer than the cycle reference |
| which terminal is the mission's | `ORCA_PANE_KEY` (`tabId:leafId`) inherited by every hook of that Claude process |
| where that terminal is now | Orca `terminal.list` -> `handle`, `ptyId`, `incarnationId`, `writable`, `orphaned` |
| deliver input | Orca `terminal.send {handle, text, enter, agentPrompt}` -> `accepted`, `bytesWritten`, `refusedReason` |
| consumed | a transcript user row carrying `<command-name>` newer than the send |
| resumed | the first assistant tool call after that row |

Cycle reference = max(marker `armed_at` or `ts`, the `boundary_ts` of the last
`resume_requested` ledger row for the session). Each observed boundary licenses at most
ONE resume.

## Behaviour

- **C1 compaction truth.** The resume branch asks `gsd_long_run.compaction_observed`. No
  boundary newer than the reference, an unreadable transcript, or an unloadable module
  -> no resume request, ledger `compaction_unobserved` (once per reference). Fail CLOSED:
  a resume is an effect, and "could not observe" is not "observed".
- **C2 endpoint capture.** Every Stop records host kind (orca / cursor / unknown),
  `ORCA_PANE_KEY` and the Claude PID for the session, so a replaced worker rebinds itself.
- **C3 transport** (`tools/continuation_transport.py`). Resolve the pane key to exactly
  one terminal; require writable, not orphaned, incarnation unchanged since capture;
  send. 0 matches, >1 matches, stale incarnation, refusal -> refuse with its own reason.
- **C4 foreground removed.** No autonomous path types into a focused window. One door
  (`_dispatch_continuation`) with two exact providers: Orca-hosted sessions via this
  spec's transport; every other session via the PP Sessions terminal inbox that another
  pane shipped the same afternoon (commit `e5ed2d3`), which types only through the
  extension owning that session's terminal. The daemon's `no-own-window` branch is
  deleted, and its foreground fallback after an unanswered inbox request runs only with
  `CPP_LEGACY_FOREGROUND_SENDKEYS=1`; by default an unanswered request is refused and
  ledgered. (Amended during execution: the first cut routed non-Orca sessions to
  `manual`, which would have bypassed the inbox's exact path.) Daemon diff:
  `exact-target-continuation.daemon.patch`.
- **C5 receipts.** Ledger stages `delivery_requested -> target_resolved ->
  transport_accepted -> resume_confirmed -> mission_advanced`, continuation id
  `sid:cycle`, transcript reconciliation before any resend, at most 2 attempts, then
  `resume_unconfirmed`. The sweep's recovery uses the same transport.

## Kill switches

- `CPP_CONTINUATION_TRANSPORT=off`: resume becomes manual; never a foreground fallback.
- `CPP_LEGACY_FOREGROUND_SENDKEYS=1`: explicit Owner opt-in, logged as manual-class.

## Done

- LANDED/OBSERVED cannot be emitted without an observed boundary (drill: the incident's
  exact shape stays red-then-green).
- Delivery is exact or refused, with a receipt; a resend reconciles first.
- Two-pane drill: A receives, B's transcript is unchanged, B focused.
- One real unattended re-entry with nobody typing. Until then the full boundary is
  UNPROVEN and reported as such.
