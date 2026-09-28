---
covers: [interactive-context-rollover, context-rent-p3, kclear-capsule, kresume, rollover-shadow, safe-to-forget]
status: SHADOW (P3 phase 1); active rollover = opt-in, not enabled
date: 2026-09-28
mode: ULTRA-PLAN for ownership (this document), EXECUTION for every slice
parent: vault/plans/context-rent-2026-09-27.md (P3), sibling vault/specs/parent-context-epoch-rotation.md
---

# Interactive Context Rollover (P3) -- spec

## 1. Reality (measured 2026-09-28 11:00 local, read-only)

- HEAD `e1a64f2`, branch `feature/knowledge-acquisition`; `9b9afd0` (rules-evidence split) is an
  ancestor. ~20 dirty files belong to live peer panes (gsd_epoch, mission_wall, ...): not touched.
- P2/D1-A holds: `tools/rules_evidence_split.py` preview moves 0 files, all 20 "already a pointer";
  20 evidence files; backup `~/.claude/backups/rules-20260928-000739` has 20 files; 210,800 chars
  (the tool scans top-level rules only; with `common/` + `python/` it is 219,272); no rule edited
  after the migration.
- **Handoff premise corrected (iteration CLASS 2).** The mission/worker half of "P3" is already
  built by pane c2 (`tools/gsd_epoch.py`: turn continuation vs wall rotation, certification,
  crash points; `vault/specs/parent-context-epoch-rotation.md`), with its live multi-epoch proof
  in flight. That spec states: *"Interactive-pane rotation is a SEPARATE brief and is out of
  scope."* P3 here is exactly that brief.
- Today's interactive path: `/kclear` writes a free-text handoff (`tools/session_checkpoint.py
  record`), prints "Next: /clear", and nothing checks it. The watchdog's Tier 2 writes a
  mechanical kclear-equivalent and asks for `/compact`. After a reset,
  `session_start_hub.js::hookWorkStateResume` injects the newest `work_state_*.json` **matched by
  cwd only** and **deletes it on read** -- two panes in one repo can take each other's state, and a
  failed resume has already destroyed its only record (state-lifetime-and-incarnation).
- `/clear` has no supported programmatic API. The only exact-target keystroke path is the watchdog's
  C4 transport (Orca pane or PP Sessions terminal inbox; refuses rather than typing into focus).

## 2. Ownership (EXTEND > MERGE > CONNECT > NEW)

| capability | owner | decision |
|---|---|---|
| mission / worker epochs | gsd_mission + gsd_epoch (peer c2/e9) | REUSE; untouched |
| checkpoint | `tools/session_checkpoint.py` | EXTEND: `capsule` subcommand, read-back |
| policy, capsule, completeness, safe-to-forget, bootstrap, refresh, exam, ledger | `tools/rollover.py` | NEW (no owner exists) |
| trigger | watchdog Tier1/Tier2 crossing | CONNECT: detached shadow observe |
| resident / floor tokens | `tools/tis_observed.py` via `session_autopsy` | REUSE |
| price ratio | dated `vault/pricing` book | REUSE; tokens only (D4) |
| child work | `gsd_epoch` child-work reader | CONNECT by import; absent = UNKNOWN |
| reset primitive | C4 transport typing `/clear` | ACTIVE phase only, opt-in |
| rehydration | `/kresume` command | NEW, thin |
| SessionStart auto-inject | session_start_hub | deferred to active phase |

No Goal engine for interactive panes: the Goal is the plan/RESUMPTION file the session was
working from, named by pointer. No new continuity framework.

## 3. State machine (ledger `~/.claude/state/rollover-ledger.jsonl`)

`CANDIDATE -> CAPSULE_SEALED (sha256 + read-back) -> SAFE_TO_FORGET | REFUSED(reasons)`
then, active only: `RESET_REQUESTED -> SUCCESSOR_CLAIMED -> REALITY_REFRESHED ->
RESUME_CERTIFIED | RESUME_FAILED`.

- Capsule keyed by predecessor session id. Successor CLAIMS atomically (one claim; a second is
  refused, naming the holder). Claim is not consumption; the capsule is retired only after
  certification. This is the incarnation fix the hub's work_state path lacks.
- Preservation and destruction are separate calls: `seal` never resets; reset requires a
  SAFE_TO_FORGET receipt whose capsule hash still matches the file on disk.

## 4. Safe-to-forget

Required, UNKNOWN counts as absent: identity (session, cwd, ts) · repo (root, branch, HEAD,
dirty set) · goal pointer (existing file) · >= 1 open obligation · handoff that exists, is fresh,
reads back · child-work state. Pending background children HOLD. A dirty tree is recorded, not
refused (it survives a reset on disk; peers' writes are dirty too).

## 5. Trigger policy (deterministic, explainable)

Inputs: resident R (last call), floor F (call #1 of the session), capsule estimate B (bytes/4,
ESTIMATED), boundary (tree clean, or HEAD advanced during the session), used_pct.
Break-even future calls `N* = (F+B)(w-r) / ((R-F-B) r)` with w/r = cache write/read prices from
the book, UNKNOWN when absent. WOULD_ROLLOVER when `R-F-B >= 150k` at a boundary and N* is known
and <= 20, or when used_pct >= Tier 2 (pressure). Everything recorded, including why not.

## 6. Shadow mode (this phase)

Nothing is destroyed. Each Tier1/Tier2 crossing spawns `rollover.py shadow` detached; it records
the decision, capsule size, completeness, safe-to-forget verdict and predicted saving. Kill switch
`CPP_ROLLOVER_SHADOW=off`. Manual path upgraded: `/kclear` seals a capsule, `/clear`, `/kresume`
reconstructs, refreshes reality and prints the exam.

## 7. Exit criteria for active rollover (not met yet)

>= 20 shadow candidates from real sessions; >= 1 real `/kclear -> /clear -> /kresume` crossing
certified; zero lost obligations across them; would-rollover rate and predicted saving reviewed by
the Owner; then `CPP_ROLLOVER_ACTIVE=1` opt-in wiring of the C4 transport + hub auto-inject.

## 8. Production Reality owed

A real fresh-session crossing spends subscription quota; Owner memory defers model experiments
until the limit resets. It is OWED, not claimed. Shadow runs on real transcripts are in scope.

## 9. Rollback

Additive: new files + one detached call in the watchdog behind a kill switch. `git revert`.
Capsules and ledger live in `~/.claude/state` (not git): telemetry and short-lived continuation
state, atomic write + hash read-back; loss means a manual resume, never destroyed work.
