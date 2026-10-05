# Pillar K -- SessionStart rise: exact producers, and the reference's component is degraded

Session c59ad762, 2026-10-05, laptop plane, HEAD baf91b69. Read-only; every number below was read from the two
startup windows (`~/.claude/projects/C--Users-User-Apps-listing-probe-champion/<sid>.jsonl`, rows before the first
assistant row) or from `~/.claude/logs/hook-dispatcher-errors.log`.

## 1. What the +6,436 chars is

The probe fa7e93cb window has two SessionStart `hook_additional_context` elements:

| el | chars | sha256[:10] | producer (hook_success row of the same event) |
|---|---|---|---|
| 0 | 3,405 | 48ebb41e10 | superpowers plugin `run-hook.cmd session-start` -- ALSO in the reference, same sha |
| 1 | 6,436 | 11b18c8a24 | `hook-dispatcher.js --event=SessionStart-chain` (stdout 6,607) -> `hooks/session_start_hub.js` |

The superpowers hypothesis is FALSIFIED: its element is identical in both windows. Element 1 sections, measured by
section marker, sum exactly to 6,436:

| Section | chars | Producer (introduced) |
|---|---|---|
| `[recovery] FAILED ...` (panes interrupted 2026-10-03T01:35:59Z) | 608 | `tools/recovery_epoch_gate.py` (bdd610cd, 2026-07-14) |
| `[AutoResearch VPS] Latest digest` ("No notable signals") | 261 | hub (14bb955a, 2026-06-30) |
| `[OWNER_QUEUE] 9 HR-001 residual(s) pending > 24h` | 1,536 | `modules/owner_queue` (24782cda, 2026-07-10) |
| `### Global Rule: <file>` x3 (moved-rule stubs) | 2,985 | `~/.claude/hooks/learning-sentinel.js:442-466` |
| `### Global Rules -- 18 delivered by file, not inline` | 1,046 | `learning-sentinel.js:475` (b96c62ff, 2026-09-16) |

All five were deployed (d3f7e8db, 2026-09-26) a week before the reference was taken.

## 2. Why the reference has 0

Reference 8f983bc6: dispatcher SessionStart `hook_success` at 2026-10-03T13:34:38.886Z, durationMs 7,353, stdout
`{"continue":true}` (17 chars). Dispatcher error log, same window:

    2026-10-03T13:34:37.839Z [SessionStart-chain] CHAIN-DEADLINE-ABANDONED after 4000ms Error: still running:
    ../skills/claude-power-pack/hooks/session_start_hub.js, ./learning-sentinel.js; host free=5950MB/32061MB (18.6%)

The chain started ~13:34:31.5Z (38.886 - 7.353 s); 4,000 ms later it abandoned exactly the two producers of
element 1 and failed open. Probe fa7e93cb (dispatcher row 2026-10-05T20:40:00.096Z, 11,492 ms) has no abandonment
logged at its start. A different session's start at 2026-10-05T20:41:10Z was abandoned the same way (11.7 % free).

## 3. Classification

- Reference SessionStart component (0 chars): **INCOMPARABLE** -- a fail-open of the producers under host RAM
  pressure, not a smaller resident prefix. The reference is NOT reset (Owner decision); the component is marked.
- The +6,436 is **not new growth**: it is the hub delivering what it failed to deliver on 2026-10-03.
- It is still resident rent, and its delivery is **load-dependent**: the same content is present or absent
  depending on host RAM. Content that silently disappears under load cannot be constitutionally required at
  startup; that is direct evidence that none of it belongs in the resident kernel.
- Consumers (to be confirmed per section in commits 4-6): OWNER_QUEUE is Owner-facing; the recovery verdict
  concerns panes of other workspaces; the AutoResearch digest carries no signal; the rule stubs duplicate the rules
  layer already loaded as instructions (sizes 1,164 / 913 / 728 in that layer); the 18-rule pointer orders every
  session to read `~/.claude/state/inherited-global-rules.md` and claims "~148 KB" for a file measured at 30,431 bytes.
- Why the gate's correlator left element 1 unattributed: UNRESOLVED here (commit 2).
