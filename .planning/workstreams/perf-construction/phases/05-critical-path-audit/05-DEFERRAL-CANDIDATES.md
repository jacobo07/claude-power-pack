# Phase 5: Deferral candidates (ledger, nothing applied)

plane: GEX44 host: kobicraft-gex44
Source of the rows: `python3 -I tools/hook_critical_path_audit.py classify --json` at the 05-02 commit, joined with `vault/config/hook-critical-path-classes.json`. The class of an entry is a reading of the repo registry, not a timing.
Laptop facts (what `~/.claude/settings.json` wires, whether `SessionEnd` calls the dispatcher, any wall time) are UNKNOWN on this plane. Every number about waiting time is LAPTOP-ONLY / UNJUDGED (LP-10).

This file is a list of what could move. It is not an instruction to move anything: no entry below has been edited, no `hooks/` file differs from the base, and `settings.json` is Owner-owned (HR-001). Phase 5 made no registration change (D5-01).

There are exactly four DEFERRABLE rows (all `DEF_ACCOUNTING_DUP`, all in `Stop-chain`), so there are four candidates. The dispatcher's own comment (`hooks/hook-dispatcher.js:393-405`) says the Owner must first add a `SessionEnd` entry that calls `node hook-dispatcher.js --event=SessionEnd-chain` (timeout 120) to the laptop `settings.json`, delete the standalone `learning-sentinel.js` entry there, and only then remove the four Stop-chain duplicates ("land the new surface before deleting the old").

What the guard (`tools/hook_critical_path_audit.py guard`) does and does not say about these moves: it accepts removing one of these four entries from `Stop-chain` while `SessionEnd-chain` still carries the script (reported as `moved`, no violation). It cannot see whether the laptop calls `SessionEnd-chain`. The precondition below is the control for that; the guard is not.

Shared precondition for all four: the Owner wires `SessionEnd` to the dispatcher in the laptop `settings.json` (the repo does not own that file), and LP-09 (enumerate the real registry on the laptop) has confirmed it. Until then the Stop-chain entry is the only live copy and must stay.

Shared reversal: put the entry back in `Stop-chain` at its baseline position (0-based index in `records/05-01-inventory-baseline.json`: trace-flusher 3, ads_sync 20, session_writeback 21, session_delta_stop 26). The `SessionEnd-chain` entry can stay (inert or live) because duplicate registration is falsifier F-2, which the boundary suite's duplicate-invocation check watches on the laptop (LP-12).

Common order constraint inside `SessionEnd-chain` (kept by the current list): `ads_sync` before `session_delta_stop`, `session_writeback` before `session_delta_stop`; `learning-sentinel` reads `session_delta_stop` output and stays last.

The four candidates are one pipeline, not four independent moves. The dispatcher comment (`hooks/hook-dispatcher.js:385-392`) warns that moving only part of it breaks the learnings pipeline silently: nothing goes red, `LEARNINGS_PENDING.md` simply stops appearing. So the candidates are all-or-none, and a partial move is itself a falsifier: F-1 for the group is "after the move, the learnings pipeline output still appears for a normally ended session". The guard does not check that all four move together.

## Candidate 1: Stop-chain|./trace-flusher.js

- container and script: `Stop-chain|./trace-flusher.js` (timeout 15000 ms in Stop-chain; 30000 ms in SessionEnd-chain)
- proposed destination: `SessionEnd-chain|./trace-flusher.js` (already present and inert)
- outputs (from the row):
  - HTTP POST of pending trace JSONL files to the trace receiver (`hooks/trace-flusher.js:239`)
  - deletes the flushed trace files on success (`hooks/trace-flusher.js:243`)
  - writes a failure-breaker file on a failed POST (`hooks/trace-flusher.js:199`)
- durability change: the flush moves from per-turn (Stop) to per-session (SessionEnd). A session that ends abnormally never reaches `SessionEnd`, so its buffer waits for the next successful flush (the script already keeps the buffer on failure). Whether anything consumes the receiver's data mid-session is not visible in the repo.
- precondition: the shared precondition above.
- falsifiers:
  - F-1: after an abnormal exit (kill, crash, terminal closed) the trace output for that session is missing or arrives only after a later session, so the candidate is rejected.
  - F-2: with both registrations live the flush runs twice per session; the duplicate-invocation check in `tools/test_hook_boundary.py` must stay green, otherwise the candidate is rejected.
  - F-3: the Stop-chain wall does not improve beyond the A/A spread under LP-10, so the move buys nothing and is rejected.
- status: CANDIDATE - NOT APPLIED
- reversal: put the entry back in `Stop-chain` (shared reversal above).

## Candidate 2: Stop-chain|../skills/claude-power-pack/tools/ads_sync.py

- container and script: `Stop-chain|../skills/claude-power-pack/tools/ads_sync.py` (timeout 6000 ms in Stop-chain; 30000 ms in SessionEnd-chain)
- proposed destination: `SessionEnd-chain|../skills/claude-power-pack/tools/ads_sync.py` (already present and inert)
- outputs (from the row):
  - docs/{prd,arch,constitution,changelog} files in the session's working tree via update_docs (`tools/ads_sync.py:100`)
  - a log line in the ads-sync log under the live .claude/logs directory (`tools/ads_sync.py:43-44`)
- durability change: generated docs refresh once per session instead of once per turn, so the working tree shows them later, and a session that ends abnormally never refreshes them. `session_delta_stop` reads the tree this entry writes, so the SessionEnd order (ads_sync before session_delta_stop) must be kept; the current `SessionEnd-chain` list keeps it.
- precondition: the shared precondition above.
- falsifiers:
  - F-1: after an abnormal exit the docs this entry would have refreshed for that session are stale or missing, so the candidate is rejected.
  - F-2: with both registrations live the doc sync runs twice; the duplicate-invocation check in `tools/test_hook_boundary.py` must stay green, otherwise the candidate is rejected.
  - F-3: the Stop-chain wall does not improve beyond the A/A spread under LP-10, so the move buys nothing and is rejected.
- status: CANDIDATE - NOT APPLIED
- reversal: put the entry back in `Stop-chain` (shared reversal above).

## Candidate 3: Stop-chain|../skills/claude-power-pack/modules/graphify/session_writeback.py

- container and script: `Stop-chain|../skills/claude-power-pack/modules/graphify/session_writeback.py` (timeout 8000 ms in Stop-chain; 60000 ms in SessionEnd-chain)
- proposed destination: `SessionEnd-chain|../skills/claude-power-pack/modules/graphify/session_writeback.py` (already present and inert)
- outputs (from the row):
  - central graph store re-index of the current repo via global_store.index_repo (`modules/graphify/session_writeback.py:228`)
  - writeback receipt lines in the state directory (`modules/graphify/session_writeback.py:58-63`)
- durability change: graph freshness moves from at most every 900 s to once per session. `hooks/graph_first_gate.js` (PreToolUse-Read-chain) reads from the graph store during the session, so the in-session graph gets staler: a freshness cost, not a safety one. A session that ends abnormally skips the re-index (the docstring names a scheduled indexer for repos it defers).
- precondition: the shared precondition above.
- falsifiers:
  - F-1: after an abnormal exit the graph store lacks that session's re-index and no scheduled indexer covers it, so the candidate is rejected.
  - F-2: with both registrations live the re-index runs twice; the duplicate-invocation check in `tools/test_hook_boundary.py` must stay green, otherwise the candidate is rejected.
  - F-3: the Stop-chain wall does not improve beyond the A/A spread under LP-10, so the move buys nothing and is rejected. The 900 s per-repo throttle means most Stop invocations may already be cheap, which makes F-3 the likely one to fire for this entry (a prediction, unmeasured).
- status: CANDIDATE - NOT APPLIED
- reversal: put the entry back in `Stop-chain` (shared reversal above).

## Candidate 4: Stop-chain|../skills/claude-power-pack/hooks/session_delta_stop.js

- container and script: `Stop-chain|../skills/claude-power-pack/hooks/session_delta_stop.js` (timeout 8000 ms in Stop-chain; 15000 ms in SessionEnd-chain)
- proposed destination: `SessionEnd-chain|../skills/claude-power-pack/hooks/session_delta_stop.js` (already present and inert)
- outputs (from the row):
  - `<cwd>/.claude/cache/learnings/<date>_<sid>.md` written by `modules/session_delta/delta.py` (`hooks/session_delta_stop.js:5-7`)
  - a line appended to the pp-stop-hooks log in the temp directory (`hooks/session_delta_stop.js:38`)
- durability change: the learnings file moves from per-turn to per-session. It reads the working tree, so it must run after ads_sync and session_writeback (the `SessionEnd-chain` list keeps that order); `learning-sentinel` reads its output. The entry is already detached and unref'd (fire-and-forget), so deferring saves only the spawn of the wrapper, not the work.
- precondition: the shared precondition above.
- falsifiers:
  - F-1: after an abnormal exit the learnings file for that session is missing, so the candidate is rejected.
  - F-2: with both registrations live the learnings file is written twice (or its consumer sees two runs); the duplicate-invocation check in `tools/test_hook_boundary.py` must stay green, otherwise the candidate is rejected.
  - F-3: the Stop-chain wall does not improve beyond the A/A spread under LP-10, so the move buys nothing and is rejected. Because the work is already detached, this is the entry most likely to fail F-3 (a prediction, unmeasured).
- status: CANDIDATE - NOT APPLIED
- reversal: put the entry back in `Stop-chain` (shared reversal above).

## Not candidates

Entries the audit holds out of this list, with the reason it could not clear them. UNKNOWN is not permission, and a later reader should see what the audit could not see.

Stop-chain accounting-like entries held UNKNOWN (`TABLE_UNKNOWN`, each with a named missing fact in the class table):
- `Stop-chain|./learning-sentinel.js`: a SessionEnd duplicate, but its source emits `hookSpecificOutput`/`additionalContext` on a SessionStart path and spawns a detached claude child; the Stop branch was not separated from the others, so it fails the no-model-context guard.
- `Stop-chain|../skills/claude-power-pack/tools/ceps_promote_stop.py`: looks write-only, but `hooks/graph_first_gate.js:166-169` reads `promoted.jsonl` per tool call, so a later refresh changes a gate input.
- `Stop-chain|./session-summary.js`: deletes a temp pointer whose reader (`session-logger.js`) is live-only and absent from this checkout.
- `Stop-chain|./lazarus-snapshot.js`: a per-turn snapshot may be the only recovery state after an abnormal exit; whether revive reads it is not shown.
- `Stop-chain|../skills/claude-power-pack/hooks/mark-live-session.js`, `background-verifier.js`, `jit_correlate_stop.js`, `ceps_correction_stop.js`: consumers of what they write are not enumerated in this checkout.

SessionEnd-chain twins (five entries, all `TABLE_UNKNOWN`): the container is inert in the repo and its wiring is LAPTOP-ONLY (LP-09). Their work is classified under Stop-chain.

Entries whose source is not in this checkout (`UNRESOLVED_LIVE_ONLY`, 14, all UNKNOWN, none readable here):
- `UserPromptSubmit-deadline-drill-chain|./tests/fixtures/drill-slow-straggler.js`
- `UserPromptSubmit-deadline-drill-control-chain|./tests/fixtures/drill-pooled-fast.js`
- `UserPromptSubmit-deadline-drill-critstarve-chain|./tests/fixtures/drill-spawn-sentinel.js`
- `PreToolUse-default|./session-init.js`
- `PreToolUse-default|./lazarus-heartbeat.js`
- `PostToolUse-default|./turn-boundary-breadcrumb-close.js`
- `PostToolUse-default|./session-logger.js`
- `PostToolUse-default|./dna-flywheel.js`
- `PostToolUse-default|./trace-emitter.js`
- `UserPromptSubmit-default|./power-pack-reminder.js`
- `UserPromptSubmit-default|./baseline-translator.js`
- `PreToolUse-Bash-default|./turn-boundary-breadcrumb.js`
- `PreToolUse-Edit-default|./turn-boundary-breadcrumb.js`
- `PreToolUse-Read-default|./turn-boundary-breadcrumb.js`

(The full 51-entry residual UNKNOWN set is the named list printed by `classify`; the other 24 have no table row because their evidence was not read in Plan 05-01, D5-05.) The standalone `settings.json` hooks (the laptop-owned layer) are not in this inventory at all.
