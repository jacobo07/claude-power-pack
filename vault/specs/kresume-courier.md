---
covers: [kresume, kresume-courier, rollover-autotype, successor-arm, rollover]
tier: T2
status: approved 2026-10-01 (Owner "y")
---

# /kresume courier — arm the successor from the predecessor

## Problem (measured, 2026-09-28 .. 2026-10-01)

After a rollover `/clear`, `/kresume focus on ...` was supposed to be typed automatically. It
was armed by the SUCCESSOR's SessionStart hook (`hooks/rollover_autotype.js`), which runs at
the most starved moment a host has, on stdin the harness may never close. Observed misses:

| capsule | successor | what happened |
|---|---|---|
| 5b46e055 | d3e92cda | hub log 06:25:40Z `stdin unreadable (readStdinRaw outcome=timeout)`; nothing armed, nothing logged; claimed by hand 77 min later |
| 31ab653e | (none) | registry pid 48292 still holds 31ab653e: `/clear` itself never landed |
| f3099e7b | 614697c1 | armed 19:01:54, daemon reached it 41 s later, extension `status-busy`, withdrawn: a human typed first |

Three timeout patches (09-29 chain deadline, 09-30 stdin budget, 10-01 harness timeout) each
moved the failure to the next link. `rollover_autotype.js:39` returned silently on an empty
payload, which is why two of the three left no trace.

## Decision

Arm from the PREDECESSOR. `/clear` does not restart `claude.exe`: the host registry
`~/.claude/sessions/<pid>.json` keeps the pid and rewrites `sessionId` in place (verified on
35/35 live sessions, e.g. pid 44312 now holds d3e92cda). So when the watchdog dispatches
`/clear`, it spawns `tools/kresume_courier.py`, which knows the predecessor's pid and watches
that one file until `sessionId` changes, then arms `/kresume` for the new id through the
existing daemon and its fresh-session guard. No dependence on the successor's stdin or hooks.

The successor's SessionStart arm stays as a second path. Both go through ONE writer
(`session_start_hub.armKresumeAutotype`, reached via `node hooks/rollover_autotype.js --arm`),
and the flag is keyed by session id, so two arms type one line; `/kresume` refuses a second
claim regardless.

## Contract

`kresume_courier.py --predecessor SID --cwd DIR [--transcript PATH]`, detached, never raises.
Exactly ONE ledger row (`kresume_courier`, via `gsd_long_run.ledger_append`) per crossing:

| outcome | meaning |
|---|---|
| ARMED | sessionId changed under the same process; arm returned a flag |
| NOT_ARMED | arm ran and declined (no unretired capsule here, kill switch) — reason carried |
| ARM_FAILED | the arm CLI could not run or returned garbage |
| CLEAR_NEVER_LANDED | deadline passed, same process, same id: `/clear` did not happen |
| PROCESS_GONE | the registry file vanished or its procStart changed (pid reused) |
| NO_REGISTRY_ENTRY | no registry file names the predecessor; nothing to watch |

Bounded: deadline 600 s (`CPP_KRESUME_COURIER_DEADLINE_S`), poll 1 s. Kill switch:
`CPP_KRESUME_AUTOTYPE=off` (the same switch as the hook path). Registry dir override for
tests: `CPP_CLAUDE_SESSIONS_DIR`.

## Acceptance (tools/test_kresume_courier.py, V-KRC-*)

- in-place id swap -> ARMED, flag for the NEW sid with the capsule's focus, ledger row
- the starved shape: the hook path given an empty stdin arms nothing (pinned), the courier
  still arms
- pid reuse (procStart differs) -> PROCESS_GONE, no flag
- no swap within the deadline -> CLEAR_NEVER_LANDED, no flag
- no capsule for the cwd -> NOT_ARMED, no flag
- kill switch -> no flag
- the watchdog spawns the courier at the `/clear` dispatch (wiring, not just a module)
- the hook path's empty-payload return is logged, never silent
- each check proven able to fail (mutation drill on an isolated copy)

## Verified (2026-10-01, CODE_VERIFIED + real components, not yet a live crossing)

- `tools/test_kresume_courier.py` KRC_PASS=20/20: real courier subprocess, real node arm CLI,
  real hub writer, real watchdog `_rollover_step` (gate verdict and transport stubbed only).
- `tools/test_kresume_courier_mutation.py` 8/8 mutants killed, each proven applied, live files
  sha-identical before and after.
- The suite caught a race in the first design: a courier that looked its process up itself
  started AFTER the swap on a loaded host (Python start ~6 s) and found nothing. The watchdog
  now resolves the registry file and procStart at dispatch and passes them
  (`V-KRC-LATE-START-STILL-ARMS`, `V-KRC-WATCHDOG-RESOLVES-AT-DISPATCH`).
- node aborted once (rc 134, `InitializeOncePerProcessInternal`) under memory pressure; the
  arm is retried 3x and the ledger keeps stderr's head, where node names the fatal error.
- Regressions: ROLLACT 15/15, GSDAC 27/27. KRA 31/33: the two `V-KRA-D-*` daemon failures also
  fail on the HEAD versions of the hook and hub (28/33 there), so they predate this change.
- **Not yet observed:** a live rollover arming through the courier. The first one leaves a
  `kresume_courier` row in `~/.claude/state/gsd-autorun-ledger.jsonl`; `outcome=ARMED` with a
  `successor` is the live proof.

## Duplicate session-id holders (review MEDIUM, fixed and gated 2026-10-01)

pp-code-reviewer: APPROVE, 1 MEDIUM — two live claude.exe can hold one sessionId (pids
21620/41256 on c4f1031c), so a first-match lookup could watch the wrong pane. Fix:
`kresume_courier.resolve()` keeps only entries whose pid is an ancestor of the caller
(`ancestor_pids`), and refuses with AMBIGUOUS_REGISTRY rather than guess between two. The
watchdog resolves with its own ancestry at dispatch; the detached fallback has none and refuses.

- `V-KRC-AMBIGUOUS-REFUSED`: two registry files for the predecessor, no resolved process ->
  one AMBIGUOUS_REGISTRY row naming both candidates, no flag.
- `V-KRC-WATCHDOG-PICKS-OWN-PROCESS`: the session is held by the test's own pid and by pid 777;
  the spawned argv carries the own-pid file and its procStart.
- Mutants `ambiguity-not-refused` (courier, the >1 refusal dropped) and
  `ancestry-filter-dropped` (watchdog call site; the watchdog loads the REAL courier through
  `_load_tool`, so a courier-side mutant could not reach the wiring gate).

Commit is BY HUNK: hooks/rollover_autotype.js and hooks/session_start_hub.js also carry another
pane's uncommitted stdin-budget hunks (45000 budget, 50 s ceiling), which are not ours to commit.

## Out of scope (named follow-ups)

`/clear` not landing (31ab653e); the daemon's ~40 s boot on a starved host, which is also why
`V-KRA-D-*` exit with the flag left inside their 5-6 s test TTL; tests writing into the real
capsule store and `%TEMP%\pp-session-hub.log` (gsdlr-*, mcw-plai*, succ-2222 rows seen live).

## Rollback

Delete the spawn line in `context-watchdog.py::_rollover_step`; the hook path is unchanged in
behaviour, so removing the courier restores the 2026-10-01 state exactly.
