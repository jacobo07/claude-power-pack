# ctx-rent-x follow-ups: everything the programme left open, and what its own run exposed (2026-11-01)

Source: pane 60a49899 (successor of f432029e), after the Owner closed ctx-rent-x ("merge al arbol principal y registrar gasto
medido", then "añadelo absolutamente todo"). Plan `vault/plans/ctx-rent-x-2026-10-31.md` (ac32606a). Nothing below is started.

## State at write time
- **Live:** CCR release `0.1.0-265d3d55`, `RELEASE.json` source_commit `e8d29ffb`: main-lean canary DEFAULT-ON for interactive
  panes; `CCR_MAIN_CANARY=0` opts a pane out; rollback target `0.1.0-b15bfc3d` (rollback + restore verified 2026-10-31).
  Start receipts: unset -> `canary:"enforce"`, `=0` -> `canary:"off"` (`vault/programs/ctx-rent-x/LAPTOP_RESULTS.md` L8).
- **Landed:** merge `cb877667` on `feature/knowledge-acquisition` (from `ctx-rent-x-l5` @ `3c42b965`). Main-tree
  `mods/cpp-cognitive-runtime/hooks/{policy,register}.ts` == live release byte-for-byte (Get-FileHash, 2026-11-01).
- **done_gate:** `python vault/programs/ctx-rent-x/done_gate.py` -> pass=21 fail=0 unknown=11 of 32 (rc 1).
- **Spend:** goal `ctx-rent-x` settled 77,378,863 against cap 55,000,000 (plan hard ceiling 75M). Breakdown: f432029e
  26,962,948 (since the 14:24:32Z binding), 60a49899 16,193,275, 35 probe sessions 4,693,964, GEX44 m-f92eb3ef9ccc
  18,613,963, m-a2963f33021e 10,914,713. Pre-approval planning 4,866,363 (f432029e before 14:24Z) unbooked.
  Re-check: `python tools/mission_spend.py goal-status --goal ctx-rent-x`.
- **Measured effect so far (small n):** L5 call-1 -22.3 %; L6 processed -27.8 % on a real bounded unit, 6/6 correct,
  0 page faults; L8 smoke call-1 65,258 vs 87,704 (-25.6 %, n=1, neutral cwd). Phase 7 replay X 1767M -> X' 1444M is an ESTIMATE.

Sizes: S < 1M tokens, M 1-5M, L > 5M. Priority P0 = prevents a repeat overrun or a silent live regression.

---

## A. Spend control (P0)

**A1. Ledger never reports exhaustion past the cap** (S).
`goal-settle` accepted 77.4M on a 55M cap and returned `"exhausted": false, "remaining": -22378863`.
Done when: `remaining <= 0` implies `exhausted: true`; a settle that crosses the cap emits an `OVER_CAP` ledger row with the
excess; one test per pole (under cap stays open, crossing flips exhausted and records the row). Owner: `tools/mission_spend.py`.

**A2. Coordinator-pane ceiling armed at approval** (M).
Coordinator panes spent 43.2M against the plan's 2M stop-loss (`ctx-rent-x-2026-10-31.md` §3); nothing enforced it.
Done when: the `approve <programme> only` path runs `mission_spend.py session-declare` on the approving pane with the plan's
warn/stop, and a test drives the stop branch red. Related memory: `feedback_coordinator_pane_is_the_overrun`.

**A3. Programme hard ceiling enforced across panes + probes + workers** (M).
The plan wrote "authority 55M + 1x20M = hard ceiling 75M"; the total was only computed by hand at close (77.4M).
Done when: `goal-status` aggregates every session settled or open under the goal, and the next lease/reserve is refused once
the declared programme ceiling is crossed.

**A4. Probe sessions book themselves** (S).
The 35 probe sessions (4.69M) were found by scraping UUIDs out of result JSONs (`probe_spend.py`, scratch).
Done when: `l5_canary_driver.py` / `l6_quality_driver.py` / any canary driver declares each spawned session to the goal at
spawn (`goal-spawn --estimate`) and settles it at exit.

**A5. Pre-approval planning is accounted** (S).
4.87M of reality scan + plan writing sat outside any goal because the goal is created by the approval.
Done when: a provisional `<programme>-plan` goal opens at the start of a reality scan and is closed (and reported in the plan's
economics) at the approval phrase.

**A6. Runner refuses an epoch with no runnable unit** (M).
Proposed in `vault/programs/ctx-rent-x/IMMUNITY.md`, no owner. m-f92eb3ef9ccc HALTED after 3 empty epochs (8-10);
m-a2963f33021e spent ~5M on epochs 5-6 + 14 reconciles ("L8 still laptop-only").
Done when: `gsd_mission` refuses epoch N+1 after K consecutive epochs whose only commit is `.planning/**/STATE.md` and whose
remotes did not move; test drives the refusal and the reset-on-progress branch.

**A7. Laptop-plane steps park the mission instead of spinning it** (M).
Done when: a worker writing an `L*` step to `LAPTOP_STEPS.md` puts the mission in a `WAITING_PLANE(laptop)` state that spends
nothing, notifies the Owner once, and wakes on a new commit from the laptop plane (fetchable ref) or an Owner decision.

## B. CCR release safety (P0/P1)

**B1. Lineage guard in `ccr_release.py build`** (S, P0).
Now possible because `RELEASE.json` carries `source_commit`. Without it, a release built from a tree that lacks `35776051`
lineage (e.g. the `dc4bf2b4` branch) silently drops the default-on canary.
Done when: build refuses unless the source tree descends from the active release's `source_commit`, overridable only with
`--allow-regress --reason`; `test_ccr_release.py` gains both poles.

**B2. Reconcile `isPlannerType` divergence** (S).
`dc4bf2b4` added `isPlannerType` to `register.ts` on another branch; the live release never had it; `35776051` synced
`register.ts` to live and left the test importing it (fixed by dropping the test, `e8d29ffb`).
Done when: that branch merges main's `register.ts` (canary + default-on) before its next release, and its test returns.

**B3. Minimum loaded-test floor in the mod gate** (S).
`policy.test.ts` loaded 0 tests (import failure) and nothing noticed until L8. UKDL `PR-TEST-THAT-NEVER-LOADED-IS-NOT-GREEN-001`.
Done when: the release gate records `pass` per test file and fails if any file reports fewer than its ratcheted floor
(28 for `policy.test.ts` at `e8d29ffb`).

**B4. Start-receipt smoke is a release step, not a manual one** (M).
L8's two-pane ConPTY smoke (`scratchpad/l8_smoke.py`, unset -> enforce, `=0` -> off) proved the flip; it was hand-run.
Done when: `ccr_release.py release --smoke` runs the two arms against the new release id and refuses to report LIVE without
both receipts; the driver lives in `tools/`, not a scratchpad.

**B5. Census of panes still on the previous generation** (S).
Default-on applies only to sessions started after the release; the census already showed 7 STALE processes on 2026-10-31.
Done when: `ccr_release.py status --sessions` lists live panes by loaded release id, so the Owner can choose which to restart.

**B6. The kill switch is documented where it is used, and executed by a test** (S).
`CCR_MAIN_CANARY=0` appears only in `policy.ts` comments and LAPTOP_RESULTS. Rule `documented-capability-must-be-executable`.
Done when: the mod README / plan kill-switch section names it and a test runs the documented form (`=0` -> `off`).

## C. Measure the real effect (P1)

**C1. Weekly delta by generation** (M).
ESTATE week 2026-11-01..08 vs 10-25..11-01, split by class and by loaded CCR release id (`b2/w6_estate.py` + receipts join).
This is the only estate-level number for default-on; everything so far is n=1..3.

**C2. Quality watch under default-on** (M).
Per pane: `mcp__cpp-cognitive-runtime__page` calls, Skill/Agent mis-picks or repeated loads attributable to missing
descriptions. Done when: a threshold fixed BEFORE reading the week's data decides keep / revert of the default.

**C3. Receipts separate provider cache from logical rent** (S, CR-07).
`CACHE_HIT` is not `SAVED_CONTEXT`; report processed tokens and cache-weighted cost as separate fields in every receipt.

**C4. Dogfood comparison** (M, Phase 8 remainder).
Re-run W0's comparable bounded unit on the new path (default-on) and publish X -> X' with calls, repairs, rereads, verified result.

**C5. KSR replay on a real KSR-style session** (M, CR-22).
Phase 7's -18.3 % is an ESTIMATE because no KSR-style session fell in the replay window.

**C6. This programme's own coordinator pane as a case study** (S).
60a49899 spent 16.2M in ~100 calls (context peak 197,868). Split it into floor / tool_result / hook injections / thinking with
`ctx_rent.py` and publish it as the baseline that section D reduces.

## D. Rent observed in this pane (P1, direct evidence)

**D1. JIT spec injection without a match** (S).
On two "cómo va?" prompts the UserPromptSubmit hook injected 14,480 B of `vault/specs/recon-fabric-llm-fix.md` with the note
"no Apollo trigger matched this prompt" (output spilled to persisted-output). Done when: injection requires a match, with the
per-prompt saving measured.

**D2. "Tower baseline" lessons on every prompt** (S).
Six inherited lessons, self-labelled "ranked by kind, NOT by relevance to this prompt", arrive on most prompts. Done when: off
by default, or kept only with evidence that one changed a decision.

**D3. Deferred MCP tool-name listing** (M).
The system prompt lists ~600 deferred MCP tool names (vercel ~300, rea ~250). Collapse to `server (N tools)` and let
ToolSearch resolve names; same doctrine as the names-only canary.

**D4. SessionStart full-skill injection** (S).
`using-superpowers` is injected in full at every session start. Convert to a latent card (Sovereign Standard: latent-card + JIT).

**D5. Woz trap advisories repeat per tool call** (S).
The same two traps (bare git on PATH, PowerShell `2>&1`) were re-injected dozens of times this session. Emit once per session per trap.

**D6. L4 hook context cap 1K** (S, blocked).
Plan W1 row 5; blocked by foreign WIP in `hooks/session_start_hub.js`. D1-D5 are its concrete evidence. Unblock by agreeing
with the WIP's owner pane, never by committing over it.

**D7. Remaining W1 floor-diet rows** (M).
Rows 1 (agent listing) and 3 (MEMORY index trim) were not applied; rules->skills (-4,645 call-1, ~/.claude `fda26c4`) was.
Each row: backup + revert script + ratchet in `tools/test_floor_regression_gate.py` (FLOOR 61/61 + 10 skipped at cb877667).

## E. Unfinished programme work (P2, from the plan)

**E1. Phase 4: successor smoke + fresh-start cost** (M; CR-11, 14, 15, 16, 29).
`/clear` -> `/kresume` with `CPP_ROLLOVER_STATE_DIR` empty; measure bootstrap tokens, page-ins, time to first correct action.
Data point: 60a49899 itself resumed via `/kresume` and certified (RESUME_CERTIFIED) within its first 4 calls.

**E2. Phase 5: Safe-to-Forget in main panes** (L; CR-09, 10, 13).
Project a tool output only when its raw is durable on disk with a pointer and no open obligation names it; page-fault counter.

**E3. W4: tool-output + thinking carriage in main** (L).
Units measured -77 % (B5 94d7b49a) and a 40.8 % thinking share (B3 e9c7f071); main panes get none of it today. This is the
second half of the saving, and C6 will size it.

**E4. W5: waiting-call classifier, shadow** (M).
Classify model calls made while waiting (poll, status re-ask, sleep-check) from transcripts; feed `ccr_pgo` admission in shadow.
This session's "cómo va?" status probes over ssh are exactly the class.

**E5. W3: rollover-economics advisory** (M).
Turn `gsd_epoch` breakeven into an advisory at semantic boundaries: continue-rent x expected calls vs successor cost.

**E6. W6: champion/challenger replay corpus** (L).
KSR-style, long repo task, cpp-gsd-long mission, successor, debugging, sparse-capability, one coherent-large-context task.

**E7. done_gate aggregates the section-8 commands** (S, CR-30).
Results sit scattered in HANDOFF.md; the gate should run (or read receipts of) each command and report one verdict.

**E8. Pre-existing reds the programme saw but did not own** (S each).
`tools/test_mission_capsule_v2.py` 72/73 (`V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT`, GEX44); `modules/liveness/reachability.py`
exit 1 on standing offenders outside ctx-rent-x. Route each to its owner programme.

## F. Tooling and operations (P2)

**F1. `--step 0` rejected when `--topups 0`** (S).
`mission_topup.py:68 parse_tokens` refuses `0`, so `C:/Users/User/ctx_rent_x_succ_gex44.ps1` failed after HOLD (mission left
PREPARED+held). With 0 top-ups the step is inert (`:118`). Fix the tool (accept 0 when topups=0) and the arming recipe
(memory `gex44-mission-arming-recipe`).

**F2. GEX44 `status` reports `liveness: UNKNOWN`, "host session list unavailable", for every mission** (M).
The planner decided `owner UNKNOWN` on it while the worker was alive; make the host session list readable there.

**F3. Tracked files vanished from `%TEMP%/claude/ctxrx-w0`** (S).
Between two `claude plugin test` runs, `plugin.json`, `hooks/hooks.json`, `kernel/HARD-RULES-DIGEST.md` were deleted; restored
from git, did not recur. UKDL `T-LAPTOP-TEMP-WORKTREE-FILES-VANISH-001`. Find the cleaner; until then no worktrees under `%TEMP%/claude`.

**F4. Landing into a shared dirty tree as a tool** (M).
`cb877667` was landed by a scratch script: merge-tree -> commit-tree -> CAS update-ref, then exact-append of the merge side's
suffix over two foreign-WIP files, refusing on any non-append. Make it `tools/land_shared_tree.py` with tests; it will recur.

**F5. `Select-Object -First` voids `$LASTEXITCODE`** (S).
This pane's own guard read a meaningless exit code and reported a false merge conflict. Add the executable pattern
(redirect to file, then read rc) to `powershell-51-native-cli-orchestrator`.

**F6. CEPS regression regex reads `key=N failed=0` as "N failed"** (S, done in this commit as a FP entry).
`hooks/bug-hunter-ceps-bridge.js:73` `/\b(?!0+\b)\d+ failed\b/i` matched `settled=35 failed=0` and recorded
`ceps_6542d7bed025aaf0`. Fix: require the count not to be the value of a preceding `key=`, or exclude `failed=`.

## G. Governance (P2)

**G1. Promotion watch** (S).
`T-DEFAULT-FLIP-NEEDS-LIVE-PANE-RECEIPT-001` and `PR-TEST-THAT-NEVER-LOADED-IS-NOT-GREEN-001` stay UKDL until a production
recurrence; then promote to a Hard Rule.

**G2. CCR certificate v5** (S).
Move `vault/programs/ccr/CERTIFICATE-v4.md` EFFECTIVENESS_PARTIAL to a figure once C1 + C2 have a week of data.

**G3. Programme template carries A2, A4, A5, A7 by default** (S).
So the next programme's spend is measured as it happens, not reconstructed at close.

**G4. Index row** (S).
This file has no row in `vault/plans/deferred-backlog.md` yet: that file carries another pane's staged + unstaged WIP at
write time. Add the row once that WIP is committed.

---

## Suggested order
1. A1, A2, A6: stop the next programme from repeating the overrun.
2. B1: protect what is live.
3. D1, D2: immediate per-prompt saving with direct evidence.
4. C1, C2 after one week of data: decide whether default-on stays.
