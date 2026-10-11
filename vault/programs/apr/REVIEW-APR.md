# REVIEW-APR (APR-4 step 1)

Reviewer: the APR-4 worker itself (self-review). NO pp-code-reviewer / woz agent was dispatched: the worker had no agent-spawn tool.
This is NOT an independent review; the Owner/coordinator should dispatch the two agents if independence is required.
Checks run: full read of `git diff 7501d939..HEAD -- tools/gsdx_chain.py`; test_apr_seal 18/18, test_apr_event 25/25, test_gsdx_chain 19/19 after fixes.

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | HIGH | Seal on incomplete work: an `acceptance` with no gates/files/require_commit passed vacuously and sealed. | FIXED (reason "acceptance declares no check"; V-APR2-EMPTYACC). |
| 2 | MEDIUM | `_git` used bare `git`, absent from the scheduled task PATH: head=="nogit", commits empty (require_commit fail-closed, cache never keyed on HEAD). | FIXED (falls back to C:\Program Files\Git\cmd\git.exe). |
| 3 | MEDIUM | Finalizer gates run inside the tick lock with timeout_s up to 600 each; the event path 540 s budget does not cover them. Sweep stage is 600 s. | OPEN/accepted: no live chain declares acceptance until APR-4 step 5, and EWC gates are short; keep timeout_s <= 120 in chain.json. |
| 4 | MEDIUM | Budget forecast changes arm boundary for chains without new fields (arms later: counts all not-done units). | Accepted: spec item 5, test V-CHAIN-ENVELOPE updated; before/after dry-run shows no live difference. |
| 5 | LOW | FALSE_DONE refusal files accumulate only per receipt; fingerprints list grows by one per new head. Bounded by human_gate. | Accepted. |
| 6 | LOW | `silence_check` alerts once per (goal, action, unit) forever (no re-alert after resolution+recurrence beyond history window 400 rows). | Accepted. |
Hunt list: double arm under event+tick -> exclusive lock + re-read under lock (tested with 2 real processes); unbounded retry -> residuals capped by max_residuals, human_gate on repeated fingerprint; silent stall -> alert after silence_s; FALSE_DONE never advances (decide: refusal removes from done).

## Independent review 1 -- woz (2026-10-11, coordinator-dispatched, read-only, range 6932f9b9..9da3e13f)
VERDICT: VETO. Coordinator re-read F1 and F2 at the cited lines and confirmed them.
- F1 HIGH gsdx_chain.py:592-595: on a residual arm `unit["packet"]` is already `X.residual.md`, so the dup check never looks at base `X`; a halt_continue renewal of X (supervise, unlocked) in the decide->_arm gap is invisible -> two workers on one unit. Fix: check the chain unit's original packet.
- F2 HIGH gsdx_chain.py:128 `_wr` plain write_text for seal/refusal/gate facts; a torn refusal reads as None -> FALSE_DONE counted done. Fix: atomic tmp+fsync+os.replace (reuse gsd_mission._write).
- F3 HIGH gsd_mission.py:2570 / gsdx_chain.py:271-285 try_seal finalizes without the per-goal Exclusive while the tick task may finalize the same unit.
- F4 MEDIUM try_seal globs chain*.json beside the packet vs discover_chains globs live vault/programs/*/chain.json: two owners-of-packet rules; DEFAULT_CHAIN outside programs/* never gets events.
- F5 MEDIUM event path budget 540 s ignores gate runtime (up to timeout_s each) inside a 600 s sweep stage -> killed mid-write (amplifies F2). Self-review #3 accepted this; woz does not.
- F6 MEDIUM silence alert dedup spans history, not the current streak; skipped_locked rows reset the streak.
- F7 MEDIUM _done_ids/_by_packet/_unit_ms duplicate decide's computations: two authorities for "unit done".
- F8 LOW _history reads the whole shared log each tick. F9 LOW _packet_states two extra _scan() per pass.
Cut list: _wr -> atomic writer; try_seal glob -> discover_chains; decide -> _done_ids/_by_packet; redundant second _armed_for; one _latest(ms).
The one thing: every finalize under the one per-goal Exclusive, through the one atomic writer, dup check on the original packet (closes F1-F3).
Not done: woz's ledger line for knowledge_vault/global_vetoes.md was denied to the agent; it is NOT appended (Owner decision).
## Independent review 2 -- pp-code-reviewer (2026-10-11, coordinator-dispatched, read-only, same range)
Severity: CRITICAL 0 | HIGH 1 | MEDIUM 2 | LOW 3 -> WARNING. Coordinator re-read HIGH-1 at gsdx_chain.py:244 and confirmed it.
- HIGH-1 gsdx_chain.py:244 `passed and status in NOT_CLOSED` seals DONE an explicit `Status: PARTIAL` / `IN_PROGRESS` receipt (NOT_CLOSED includes both; WU-APR2.md:16 allows only None/UNREADABLE/STUB). The same branch is reached from gsd_mission._seal_instead_of_renew via try_seal(force=True). NOT latent: APR-4 (9c0a195b) already gave EWC E3-E5 acceptance blocks.
- MEDIUM-1 gsdx_chain.py:256 a refusal fingerprint is appended per HEAD seen, not per attempt, so a waiting unit reaches `repeated` with zero residual attempts -> false human_gate or an unneeded rung climb.
- MEDIUM-2 gsdx_chain.py:146/231 a gate that cannot start (OSError, e.g. PATH under the scheduled task) is filed as the worker's FALSE_DONE -> paid residual, false human_gate.
- LOW-1 :435 wait_finalizer not in SILENT (a persistent _write_residual error halts silently). LOW-2 :595 = woz F1. LOW-3 :259 a stale refusal keyed to an old sha is not rewritten after a crash.
- Self-review #3 also applies to halt_continue -> try_seal inside supervise.

## Disposition (coordinator)
Combined: 3 HIGH (woz F1/F2/F3 overlap; pp HIGH-1), MEDIUM woz F4-F7 + pp M1/M2. Remediation unit WU-APR7 added to the chain after APR6, with the two recorded faults (BLOCKED_HUMAN re-armed as residual; resolved human gate never re-judged).