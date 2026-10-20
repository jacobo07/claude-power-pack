# P1 Reality delta + fence audit (owner-control-plane)

Measured 2026-10-20, read-only. No ledger mutation, no change to the econ-safex programme.
Paths are relative to the worktree `C:\Users\User\Apps\pp-owner-control` (branch `ocp/owner-control`) unless marked MAIN.

## 1. Hook order and the capture leg

| Claim | Evidence |
|---|---|
| UserPromptSubmit order: `econ_admission.js`, then hook-dispatcher UserPromptSubmit-chain, then orca `claude-hook.cmd` | MAIN `~/.claude/settings.json:778-815` (read by the previous pane) |
| `econ_admission` is registered from the MAIN checkout path, so worktree edits are not live until merged | MAIN `settings.json:785` |
| Capture runs inside `econ_admission` BEFORE `decide()`, so a block does not stop it | `hooks/econ_admission.js:144-152` |
| `owner_capital_capture.js` is NOT a separate hook registration: it is `require`d by `econ_admission` (fail-open try/catch). The "wiring gap" in the plan is resolved: no registration exists or is needed | `econ_admission.js:144-147`; grep `owner_capital_capture` in MAIN `settings.json` and `~/.claude/hooks/*.js` = 0 matches; in the worktree only `econ_admission.js`, `owner_capital_capture.js`, `tools/test_capital_authority.py` reference it |
| Verbs are only `econ status|detach` | `econ_admission.js:29` |
| `econ_admission` is out of the hook-dispatcher chain on purpose | MAIN `hooks/hook-dispatcher.js:595-600` |

Consequence for Phase 3: the router goes inside `econ_admission.js` before `decide()`, next to the capture call. Any edit is dormant until merged to MAIN.

## 2. Ledger: programme, lease, succession

All in `modules/provider_routing/ledger.py`.

- `set_programme` (415-435): first value and any lowering are admitted; a raise from `inside_agent` is refused (424-426). A FIRST programme above the goal cap is refused for an agent (427-432). Only `inside_agent=False` can raise.
- `lease_open` (437-449) takes the lock and calls `_open_locked` (457-485): idempotent by `succession_id` (460), CAS on `prev_lease` (464), no programme means UNKNOWN (468), `need > executable` journals one `authority_required` row and returns AUTHORITY_REQUIRED (471-479).
- `_executable` (451-455) = programme - settled - open - other open leases' committed reserves.
- `set_succession` (487-506): enabling or loosening needs the Owner (498-501); tightening or off is always admitted.
- `_auto_succeed` (508-535): opens `<goal>:auto:<lease>` at `min(tranche, executable - keep - carry)` (524-525). If that cannot fund one call plus every live pane's final reply it journals `authority_required` and stops (529-534). This is the only automatic capital movement.
- `programme_status` (405-413) is read-only and reports `executable`.

Reusable for the control plane: `programme_status`, `lineage`, `set_programme` lowering path, `set_succession(tranche=0)` (tighten, always admitted). Not reusable without an Owner leg: any raise or enable.

## 3. Re-measured goals (`python tools/mission_spend.py programme-status --goal <g>`)

| Goal | programme | settled | open | open lease reserves | executable | status |
|---|---|---|---|---|---|---|
| econ-safex | 32,000,000 | 28,495,332 | 1,593,218 | 1,200,000 | 711,450 | AUTHORITY_REQUIRED (lease L2) |
| owner-control-plane | 72,000,000 | 6,434,767 | 2,706,878 | 0 | 62,858,355 | OK (lease L2) |

- UPDATE 2026-10-20 (after the measurement above): the Owner typed `ADD +70M` and `approve econ-safex only` against packet `econ-safex-add-70m-2026-10-20` (sha 46698b82caac). econ-safex is now programme 102,000,000, executable 70,711,450, approval 8f8e90f6. Before applying, its automatic tranche was tightened 50M -> 4M (keep 1.2M), which closes the Phase 6 oversize-tranche risk for this goal only.
- D9a CONFIRMED live: `apply_pending` takes the transcript from `approvals.jsonl[-1]` (`capital_authority.py:240`), the latest row from ANY pane. Pending-sweep rows from other panes became `[-1]` before the detached apply ran, so the leg searched the wrong transcript and applied nothing; a manual `capital-apply-pending` applied it. Also `find_owner_decisions` matches the packet sha in lowercase (`capital_authority.py:99`), so a hash displayed in uppercase never binds. Both go to the Phase 3 router work (resolve per row, normalise case).
- Original measurement (superseded): econ-safex was at 711K executable with a 50M tranche that could not fit, so succession would journal `authority_required`, not spend.
- owner-control-plane programme source is `owner-econ-raise:...:L1`, i.e. the programme is 72M, not the 22M in the original RESUMPTION header. The raise was Owner-applied; STATE.md must be corrected.
- `plan` row "programme 22M" and "L1 cap 4M" are stale. `settled` 6.43M already exceeds the 4M L1 cap by design (L2 exists).

## 4. Missing and present modules

- `modules/provider_routing/succession.py` does not exist (previous pane, verified). Succession logic lives only in `ledger.py:487-535`.
- Capital approval machinery that already exists (from `vault/plans/owner-capital-ctx-rent-2026-10-11.md` section 1): packet-sha-bound approval, per-(sha, goal) idempotence, 500K drift revalidation, expiry, P95 cap on `modify`, same-pane `revoke`, detached apply leg spawned by the UserPromptSubmit hook with zero model calls. Open defects D9a (apply_pending resolves the transcript from the latest approval row of any pane), D9b (sweep spawns python on every prompt while a pair is outstanding), D10 (no capital freeze) are carried from that plan; this phase did not re-verify them in code.

## 5. Decision Plane entry points (`tools/decision_plane.py`)

CLI subcommands, `main` at 493-514: `create --file` (498), `show`, `resolve`, `resolve-transcript` (506, resolves from an Owner-typed transcript entry, then routes the receipt), `consume --file` (511, verify, persist, apply, wake the owner), `deliver` (514, ship a resolved decision to a host and run its consumer). Authority tie-in: `gm.set_authority(consumer, budget, ...)` at 417 (cumulative ceiling). Caller in `tools/gsd_mission.py:4986`. Tests: `tools/test_decision_plane.py`, `tools/test_wake_progress.py`.

Reusable: `resolve-transcript` is the existing provenance-checked path from an Owner-typed message to a durable receipt, which is what the grammar router in Phase 3 should feed rather than reimplement.

## 6. Open items handed to later phases

1. Phase 6: econ-safex 50M automatic tranche vs 711K executable (section 3).
2. Phase 3: router lives in `econ_admission.js`, dormant until merged to MAIN.
3. D9a/D9b/D10 unverified in code; re-check before Phase 3 relies on `apply_pending`.
4. Not read this pass: `vault/plans/econ-succession-2026-10-11*.md` (ledger code was read directly instead).
