---
covers: [ce-a4, estate-rearm, presence-enforce, estate-migration-queue, capability-reachability, work-extinction, boundary-extinction, parentless-execution, cognitive-ci, cbr-economy]
status: PROPOSED (one Owner approval; phrase in section 11)
extends: gen2 program -- Amendment A3 (5617f901), A3b (b2754615), Presence Contract U6 (fb9f10fd, merged 7e201298), CAA (3fe39764), cep-gen4 (f14f33a5), cost-collapse T0-T3 (branch cost-collapse/main)
source: interactive pane f883c056, read-only Reality Scan, 2026-10-08
---

# CE Amendment A4 -- estate rearm: stop the bleeding, migrate, self-deflate

This is the 7th economy mega-prompt in two days. Under HR-NOVELTY-001 and memory `project-ce-a3-goal-binding`, it
becomes Amendment A4 of the existing gen2 program. It is not a new program. Almost every requested capability
already has an owner. The missing work is reachability: merging branches, flipping switches, and connecting callers.

## 1. Reality Scan (MEASURED at HEAD 8259a97e unless marked)

Budget authority:
- `ce-a3`: used 10,797,470 against a 9.9M cap. **OVER CAP**, so it is contained and cannot carry new work.
- `ce-presence`: 6,080,514 against 6.0M. Contained.
- `ce-a3b`: 5,618,975 against 7.2M. 1,581,025 remains.

New work therefore needs a new goal id. Every breach so far was caused by a coordinating pane, never by a worker.

Presence Contract U6a is merged on HEAD at 7e201298 and 666e18d2:
- `resolve_baseline` sits in `tools/gsd_mission.py:951`.
- `CPP_CE_BASELINE` defaults to `shadow` (`:909-911`).
- U6b packet and route exist, untracked, in `Apps/pp-ce-presence`. U6b, U6c and U6d were never run.
- The negative canary is not run. So "missing model resolves to Sonnet" is wired but UNVERIFIED in a real worker.

A3b:
- B0 entry matrix is built but UNCOMMITTED in `Apps/pp-ce-a3b`: `tools/entry_matrix.py` and `ENTRY_MATRIX.md`.
- Matrix finding: 28 of 35 headless launch-site files have no binding reference and no ceiling.
- B1 is blocked by a false positive in the live guard: `GOAL_STATE` regex at `hooks/session_budget_guard.js:218`.

Missions (`gsd_mission.py status`): 130 records; 113 HALTED, 6 COMPLETED, 11 non-terminal. None is burning except
one. `m-b76843b319af` (pp-cost-collapse, LAUNCHING) has the supervisor planning `replace` ("start ack overdue").

Branches carrying unmerged CE work (commits ahead of HEAD / changed files):

| Branch | Ahead / files | What it carries |
|---|---|---|
| cost-collapse/main | 17 / 34 | Compiled grammar G1/G2, envelope admission, packet done_gate, `gsd_dossier`, autopsy+forecast; plan to move gsdx-pcc onto it |
| ce/gen2-completion | 15 / 17 | Zero-hot WAITING via WAKE_FLAG, forget-safety, lifecycle gates |
| ce/gen3-t3-runtime | 8 / 11 | Session-tree meter, Agent-dispatch budget judgement, `/kclear` rotation |
| ce/gen3-t1-envelope | 2 / 6 | Mandatory launch envelope (shadow) |
| land/slim-workers | 1 / 2 | Slim workers get pre-approvals and PowerShell |
| ce/a2, ce/a3, ce/a3b, a1/a1-2 | 21-29 | Meter, autopsy, packets, ledger blocks |
| gsdx/pcc | 41 / 131 | Proof-conserving convergence, Phase 1 of 10. Deterministic gate supervisor fix R01 |

Fully merged, nothing left: ce/goal-admission, ce/presence, ce/t1g-guard-fix, cep-gen3-t2, ce-gen3-t1b,
t1c-auto-budget, cognitive-economy/autonomous-run, tower/constitutive-substrate, fix/mission-cost-breaker.

The 18-capability audit has no file in the repo, so its input is the prior conversation only. The matrix below is
my reclassification from code anchors and commit history. W0 re-derives it mechanically before any merge.

## 2. Capability reachability matrix (provisional; W0 makes it deterministic)

| # | Capability | State now | Owner (extend, never duplicate) | A4 target |
|---|---|---|---|---|
| 1 | Work Extinction / Proof of Non-Work | BRANCH_ONLY (cost-collapse `gsd_dossier`) + MANUAL (no-work canary 8b727623) | dossier in `gsd_mission` launch path | run before every unit launch |
| 2 | Boundary Extinction | ACTIVE_PARTIAL, opt-in (`tranche_driver` deterministic receipts) | `tranche_driver.py` | default for mission units |
| 3 | ContextImage / compiled packet | ACTIVE_PARTIAL, opt-in (`route_admission`, slim-t2) | `route_admission.py` + packet grammar | resolver picks COMPILED_UNIT by default |
| 4 | Semantic compaction | ACTIVE_PARTIAL cross-epoch (capsule-v2, rehydration card); within-epoch HOST-LIMITED | `gsd_epoch`, capsule-v2 | decisions-to-consequences card section |
| 5 | Read Extinction | ADVISORY (`gatekeeper-semantic` soft mode) | `audit_cache` + graphify query | dossier replaces repeated ownership reads |
| 6 | Transport Extinction | MANUAL (receipts exist, parent still reads narratives) | receipt schema | receipt-by-reference between units |
| 7 | Agent admission | ACTIVE_PARTIAL (goal-admission Agent lane); dispatch budget BRANCH_ONLY (gen3-t3) | `agent-solo-guard`, `session_budget_guard` | merge gen3-t3 delta |
| 8 | Planner / reviewer extinction | BRANCH_ONLY (grammar packet gates) | packet done_gate | default on COMPILED_UNIT |
| 9 | Deterministic proof transaction | BRANCH_ONLY (grammar law 7, gsdx R01 gate supervisor) | packet done_gate | on mission path, Fault Capsule on red |
| 10 | Zero-hot WAITING | BRANCH_ONLY (gen2-completion C3) | `gsd_mission` supervisor | merge + canary |
| 11 | Event-driven wake | BRANCH_ONLY (WAKE_FLAG) | sweep `PP-GsdLongRun-Sweep` | merge + canary |
| 12 | Model routing per decision | WIRED_SHADOW (U6a resolver); `model-routing.json` vs `cost_collapse/router.py` SPLIT-BRAIN | resolver + `model-routing.json` | enforce; one table |
| 13 | Hard Budget Kernel | CERTIFIED_ACTIVE for bound sessions (Owner done, canary #6 2,912,243/3M); default binding ABSENT | `session_budget_guard` + GoalLedger | default binding (A3b B1) |
| 14 | Cognitive CI | MANUAL (`cep_gen2 --tranche` clauses) | `cep_gen2` + `reachability.py` | route-null / model-null / Agent-fanout clauses |
| 15 | CBR integration | UNREACHABLE for CE (substrate merged, no CE caller) | CBR substrate | versioned baseline policy = CBR artifact |
| 16 | Prompt Extinction | ABSENT | `commands/cpp-gsd-long.md` | U6b retires the manual-flag prose |
| 17 | Semantic PGO | UNREACHABLE (`cost_to_completion.py` DORMANT; `estate_shadow` PARTIAL) | `estate_shadow`, autopsy (cost-collapse T2) | completed-mission profile into policy file |
| 18 | Mandatory envelope | ACTIVE_PARTIAL (auto envelope 03e1b0c3 default-on); mandatory variant BRANCH_ONLY shadow | `gsd_mission` envelope | merge, enforce |

The "seven branch families" correspond to rows 1, 2, 3, 7, 8, 9 and 18. All seven still carry value. Row 2 lives on
HEAD as an opt-in. The rest live in cost-collapse/main, gen3-t3, gen3-t1 and gen2-completion. Integration extracts
deltas by file. It never does a blind merge.

## 3. Estate Migration Queue (initial dispositions; W0 makes them a deterministic tool)

| Mission | cwd | Disposition | Reason |
|---|---|---|---|
| m-53847a002b65 | pp-gsdx-pcc | FREEZE_AND_MIGRATE (Canary 10) | Raw GSD grammar measured 162.2M; Phase 2 of 10 not started, so most work remains; cost-collapse T0 already specs this move |
| m-b76843b319af | pp-cost-collapse | MIGRATE_NEXT_EPOCH, absorbed as A4-W1a | Overlapping owner of the compiled grammar; its T3 becomes A4's integration unit; singleflight |
| m-ed6e0c6cc526 | recon_work | KEEP (Canary 11 candidate) | Sonnet, PREPARED, not launched; migration buys nothing |
| m-54df1c6f0511 | io-ql-story | UNKNOWN, resolve before launch | PREPARED with explicit `opus`; needs `legacy_reason` under enforce or a re-resolve |
| m-9bee7894f20f | claude-power-pack | UNKNOWN | Cost breaker 3.0M > 2x 1.5M; Owner hold |
| m-6f7451aefe40 | _wt-creative-addc | BLOCKED_ZERO_HOT | Cost breaker 175M > 2x 87.5M; Owner hold stays |
| m-608c8d8d761f | io-device-trust | BLOCKED_ZERO_HOT | Owner hold TOK-18; never resumed by A4 |
| m-8c83bf14d61d, m-bc35112a5514 | io-ucg, io-vlab | BLOCKED_ZERO_HOT (verify no live process) | Host lists them blocked |
| m-72fba680c953 | pp-ce-a2 | CLOSE_NO_WORK | A2 superseded, Owner stopped it |
| m-ce41dd79ddd7 | _wt-creative-addc | CLOSE_NO_WORK | Superseded 2026-10-06 |

The priority score is (expected remaining work) x (avoidable architecture multiplier) x (confidence), minus
migration capital spend. Inputs come from the cost-collapse T2 autopsy+forecast. A4 adds no new instrument.
UNKNOWN stays UNKNOWN. A mission never launches while its disposition is UNKNOWN. Owner holds are never lifted by
A4, except the one exception in section 11.

## 4. How no new mission is born expensive after Wave 1

Every mission path converges on `launch_worker`: arm, renewal, relay and successor. U6a already resolves absent
fields there. Wave 1 closes the remaining gaps:

1. The resolver moves from `shadow` to `enforce`, gated by the U6c negative canary measured from a raw worker
   transcript. Under enforce, `--bg` + Opus + 600k without a `legacy_reason` is refused, never silently downgraded.
2. A missing packet resolves through the dossier into COMPILED_UNIT where the phase kind is certified. Otherwise it
   resolves to the BASIC tier (Sonnet, policy ceiling, `continue_max_tokens`). It never resolves to the host maximum.
3. Default goal binding by program path (A3b B1). The `GOAL_STATE` false positive is fixed in the repo copy plus a
   live copy.
4. The 28 unbound headless launch sites from ENTRY_MATRIX get a ceiling or a named exception. Cognitive CI fails a
   new site that has neither.
5. Agent dispatch is judged against the session-tree budget (gen3-t3 delta).

Interactive panes stay the Owner's choice of model, because the host owns that choice. They are bound to a goal
budget by default instead.

## 5. Execution architecture: A4 runs on the baseline it builds

- This pane does four things only: declare the goal, write the W0 packet, arm one unit, exit. Coordinator sub-cap
  is 0.6M for this pane, metered with `goal-status`.
- Every unit is one compiled packet plus one slim Sonnet headless worker. Its cwd is the root `Apps/pp-ce-a4`
  (worktree off HEAD 8259a97e). Each unit has a turn budget derived from the ~120k floor and commits early.
- Units chain through `tranche_driver --manifest`. The path is: receipt, deterministic gate, next unit. There is no
  parent model relay and no Agent teams. An Agent is allowed only for an independent-assurance review of a merge
  where a mutation drill cannot decide.
- From W1d on, every unit is armed with no model, route or autocompact. The resolver chooses. That is the
  self-hosting proof.
- Two-strike rule per unit. A crossed cap means stop and write state. A cap is never raised.

## 6. Units, ordered by dependency and return on spend

| Unit | Wave | Work | Proof (repository-native) | Cap |
|---|---|---|---|---|
| W0 | 1 | Commit A3b B0. Turn ENTRY_MATRIX + `reachability.py` into a capability-reachability matrix (18 rows, deterministic). Turn the section 3 queue into `estate_queue` inside `gsd_mission status`. | Matrix and queue regenerate byte-identical; a planted unreachable capability goes red | 1.2M |
| W1a | 1 | Integrate deltas by file: cost-collapse G1/G2 + dossier + T2 autopsy, gen3-t1 mandatory envelope, gen3-t3 dispatch meter, slim-workers, gen2-completion C3. Reject superseded hunks with evidence. | Each family: own suite green on HEAD + mutation drill red-before; `test_gsd_mission*`, `test_gsd_epoch` green | 3.0M |
| W1b | 1 | A3b B1-B3: default binding, null-config, relay re-admission. `GOAL_STATE` regex fix. Runs inside `ce-a3b`'s remaining 1.58M. | V-GOAL suite; zero-activation canaries | (ce-a3b) |
| W1c | 1 | Presence U6b-U6d. Arm with no route (negative canary). Misconfiguration canary. Legacy-exception canary. Flip to `enforce`. Route-null CI clause. Retire `/cpp-gsd-long` manual-flag prose (prompt extinction #1). | Raw-transcript model / autocompact / floor vs incident; V-BASE mutants red; `run-all.js` green | 3.0M |
| W1-gate | 1 | Canaries 1, 2, 7, 13, 14 (one non-PP repo with CPP present, plain task). | Wave-1 gate table, all rows MEASURED | 0.8M |
| W2a | 2 | Run the queue: close CLOSE_NO_WORK, verify BLOCKED_ZERO_HOT has no live process. Migrate gsdx-pcc at its Phase-2 checkpoint onto the compiled grammar (Canary 10). Show KEEP (Canary 11). | Commits preserved; end-to-end spend vs the 162.2M incumbent rate | 3.0M |
| W2b | 2 | Work Extinction before every launch. Deterministic proof transaction on the mission path with a Fault Capsule. Planner / reviewer / researcher extinction on COMPILED_UNIT. Physical-call compression on one measured boundary. | Canaries 3, 4, 6; calls-per-boundary before vs after | 2.5M |
| W2c | 2 | Parentless chain (Canary 8). Lifecycle: wall, checkpoint, successor with zero Owner operations (Canary 9). Zero-hot WAITING + wake (Canary 12). ContextImage projection (Canary 5). | Ledger rows + raw transcripts | 2.0M |
| W3 | 3 | Read Extinction (dossier replaces a recurring ownership read). Transport Extinction (receipt by reference). Semantic PGO (autopsy writes the policy profile). CBR: the baseline policy file versioned as a CBR artifact, inherited by any project where CPP is present. Cognitive CI full clause set. UKDL HR/PR/T via CEPS. KV root-cause records. | Canary 15 (self-host) + equivalent-work cost comparison | 3.5M |
| reserve + coordinator | | | | 2.1M + 0.6M |

**Total cap: 21.7M**, goal `ce-a4`, root `Apps/pp-ce-a4`, excluding W1b, which stays in `ce-a3b`. Each unit's cap
comes from measured units: U6a 1.04M, A3-U1 1.82M.

## 6b. Inherited from cep-gen4 (fold 2026-10-08, Owner, pane 0f9b771b)

gen4 (f14f33a5, 9658c5f2) is folded into A4. Its 15M envelope is CLOSED, never spent (0 processed); A4 does not
inherit budget from it. Its proof obligations ARE inherited and join the Master Done-Gate:

| gen4 unit | A4 owner | obligation A4 must prove (unchanged from gen4) |
|---|---|---|
| P0 worker write | root `Apps/pp-ce-a4` worktree, W0 | one real BACKGROUND worker commits on this repo through the worktree; name the layer that refused T1c's edits to the live checkout (m-3b71f5457c70, bg 62ac7eb5) from its log |
| S4 zero-model coordinator | tranche_driver --manifest, W2b | one real unit whose coordinator spend is MEASURED <= 1.5M (A4 sub-cap 0.6M is stricter and wins) |
| S9 estate enforcement | W3 CBR baseline | CBR "no mission without an envelope" backed by a live `envelope_auto_assigned` ledger row |

**F0 stays outside A4** as a bounded 1M unit with its own receipt (gen4 card, section F0): split the per-call floor
into host vs Power Pack with a pass-through mod. A4's turn budgets derive from the ~120k floor (section 5), so:

- **F0 runs before W0.** No A4 unit is armed until gen4/F0-receipt.md exists.
- **A4 reforecast checkpoint after F0.** Re-derive every unit's turn budget from the measured split, and from the
  removable Power Pack share if F0 finds one. The 21.7M cap below is NOT approved until that reforecast is written.

Budget consolidation, as measured here: combined live authorization falls from 36.7M (gen4 15M + A4 21.7M) to
22.7M (A4 21.7M + F0 1M). No A4 row is double-counted against gen4 money, because gen4 spent none. A4's own rows
are not reduced yet: lowering them now would be a guess; F0's floor split is the input that can lower them.

Rule candidates (UKDL BLOCKED_BY_OWNERSHIP: ukdl-universal.md has another pane's uncommitted hunks):
- When two active programs claim the same obligation, execution stops until one canonical owner is resolved.
- Consolidating programs consolidates budget, not only ownership: the folded envelope is closed, not kept live.
- A folded program becomes provenance, never a second execution source.

## 7. Null-policy semantics, legacy deopt, rollback

- An absent field resolves to policy. Unreadable policy resolves to builtin cheap values (U6a, landed).
- `legacy_reason` comes from a closed enum. Safe deopt raises one dimension only and is recorded.
- Rollback switches:
  - `CPP_CE_BASELINE=off`: byte-identical legacy argv (golden-pinned).
  - `CPP_MISSION_CONTINUATION=off`.
  - Every integration is a revertible micro-commit on `ce/a4`, merged into the live branch fetch-first with
    pathspec.

## 8. Security and project sovereignty

Workers get least privilege: their own worktree, no `~/.claude` writes (HR-001), no secrets in packets
(HR-SECRET-006). Cross-project inheritance carries the policy file only, never project state. GEX44 stays DEFERRED.
It needs Owner steps on its own `~/.claude`.

## 9. Master Done-Gate (repository-native)

- Every row of the prompt's gate maps to one unit's proof above.
- Done means every in-scope row is MEASURED from raw transcripts, ledgers or suites. Configuration alone counts
  for nothing.
- Rows not reached inside 21.7M stay listed as UNKNOWN or DEFERRED, never PASS.
- Named deferrals: GEX44 cross-machine; cross-account; within-epoch compaction (host-limited); interactive model
  rewriting (host-owned); scheduled entry points beyond the swept launch sites.
- "Cognitive deflation" means one equivalent unit class measured before and after A4, with its normalisation
  stated.

## 10. Owner operations that remain (honest list)

Live `~/.claude` hook and command copies cannot be made by workers (HR-001). Each wave ends with at most one batched
`Copy-Item` diff for the Owner: the W1 guard regex and agent guard, then the W3 command text. Everything else is
automatic.

## 11. Approval

One approval covers all of the following:
1. Declare goal `ce-a4` with cap 21.7M, bound to root `Apps/pp-ce-a4` (coordinator included).
2. W1b runs inside `ce-a3b`.
3. CAA T0-T5 and cep-gen4 P0/S4/S9 are absorbed as A4 units where they overlap, not run as parallel programs.
4. Lift the economic-containment hold on gsdx-pcc **only** to migrate it under the compiled baseline.
5. Accept the deferrals in section 9.

Phrase: **"go a4: 21.7M, gsdx migrate, deferrals accepted"**
