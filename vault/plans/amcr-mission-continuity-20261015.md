---
covers: [mission-continuity, execution-binding, workspace-rebind, semantic-progress, progress-reconciliation-gate, cost-breaker, amr-recovery, child-obligations, goal-liveness]
status: awaiting-owner-approval
date: 2026-10-15
extends: vault/plans/amr-autonomous-mission-recovery-20261013.md
incident: m-4e31db7aca3f (Credit Score Engine)
---

# AMCR — Autonomous Mission Continuity & Recovery (master plan)

Backup of the inline approval surface. Extends AMR; no new Mission OS, no new database: the mission
record (`~/.claude/state/gsd-mission-<id>.json`) and `gsd-autorun-ledger.jsonl` stay the host-resident store.

## 1. Reality Delta (verified 2026-10-15 08:40-08:55 local)

| Fact | Evidence |
|---|---|
| m-4e31db7aca3f RUNNING, seq 7, unchanged since 00:16; owner_hold kind=cost, recovery NOT_APPLICABLE | mission record |
| Worker 37e13a49 gone (pid 35520); killed by `recovery_fenced` 22:16:43Z, not by the breaker itself | ledger |
| Breaker: spent 7,099,973; 5,051,831 since last fingerprint move > stall budget 4,262,035 (= auto estimate 8,524,071 / ratio 2) | ledger `cost_breaker_tripped` |
| Breaker measured `rec.work_dir or rec.cwd`; work_dir never set -> main checkout | gsd_mission.py:1583 |
| Worker worked in `Credit Score Engine-wt` (branch gsd/dispute-engine-v1, base 47e0f3c, HEAD 8043467) via `git worktree add` + `Set-Location`; transcript `cwd` stayed main | transcript L261-274 |
| 8043467 = 01-CONTEXT.md only (+77); not in main; main clean at 47e0f3c; wt clean | git |
| wt: vitest 136 pass + 1 skip, tsc exit 0 (re-run 08:53) | this scan |
| Researcher (gsd-phase-researcher, background) launched 22:08:30Z, no RESEARCH.md written; died with parent | transcript, wt tree |
| Recovery: `gsd_unit` regex `^current_phase:` in STATE.md frontmatter; GSD 1.14 roadmapper STATE.md has no such field (body `Phase: 1 of 4`); unreadable in main AND wt | mission_recovery.py:248, STATE.md |
| Tests seed synthetic `current_phase: 02` (fixture written by the same assumption) | test_mission_recovery.py:63,303 |
| NOT_APPLICABLE -> goal_liveness OWNER_BOUNDARY; sweep logs nothing more; parked 8.5 h silently | mission_recovery.py:354, sweep log |
| Edit block = Claude Code built-in bg-session isolation (`worktree.bgIsolation`), not a PP hook, not another pane | tool_result text L261 |
| `effective_workdir` exists but is relay-time only and reads transcript `cwd` (blind to Set-Location) | gsd_mission.py:2529 |
| Same class, 3rd instance in 5 days: m-4a0f39b59a60 (add_dirs, 10-11), m-07a78fbae3c7 (excluded .planning, 10-15, uncommitted fix by another session), m-4e31db7aca3f | gsd_mission.py:4626, live diff |
| PP live tree: branch feature/knowledge-acquisition, 1172 dirty entries; gsd_mission.py has a foreign uncommitted +27 hunk (08:50) | git |
| UWCP: no implementation found under PP by name | scan |

## 2. Root-cause matrix

| # | Defect | Class | Mechanism |
|---|---|---|---|
| D1 | Observer on stale root | CLASE 0 (recurrence) | breaker/recovery/status each derive root as `work_dir or cwd`; nothing binds a worker-created worktree |
| D2 | Child activity invisible | CLASE 2 | live background researcher counted as zero progress; fence killed parent+child |
| D3 | Residual parser schema drift | CLASE 1 | private regex over a GSD field the producer does not emit; fixture shares the assumption |
| D4 | WAITING collapse | CLASE 5 | unreadable residual -> NOT_APPLICABLE -> OWNER_BOUNDARY, no wake, no surface |
| D5 | Improvised topology | CLASE 2 | bg isolation guard is correct; mission gives the worker no sanctioned way to declare a worktree |

## 3. Target

Durable Goal (cwd|workstream) -> mission record -> `binding` {gen, repo_common_dir, root, branch, base, head_at_bind, bound_at, cause}
-> single resolver `execution_root(rec)` -> every observer (breaker, frontier, AMR, status, card, align, transcript lookup).

- **Bind at arm**: gen 1 = cwd. **Explicit rebind**: `gsd_mission.py bind --mission <id> --path <worktree>` (card tells the worker to run it after creating a worktree). **Detected rebind** (backstop): a worktree of the same common dir created after `bound_at` AND named in the worker transcript's tool inputs -> `workspace_rebound` gen+1 (seq-CAS). Ambiguous -> union fingerprint + PROGRESS_UNKNOWN. Bound worktree removed -> `binding_invalidated`, resolve by branch ref.
- **Stale-generation guard**: a trip requires measurement gen == record gen inside the same CAS transition.
- **Progress frontier**: hash of mission-relevant ref *trees* (bound branch + branches created since bound_at; tree hashes so empty/amend commits do not count), bound tree dirty set, `.planning` artifacts (adopt the concurrent session's `_planning_artifacts`), child receipts. Clean tree after a commit = progress.
- **Progress Reconciliation Gate** before any trip: GOOD/PARTIAL -> mark; TOPOLOGY_CHANGED -> rebind, no trip this pass; CHILD_ACTIVE (pending bg child, transcript grew <10 min) -> no trip up to one extra stall budget, then save child obligation BEFORE fence; PROGRESS_UNKNOWN -> no trip, 3 in a row -> surfaced RECOVERY incident; ZERO_PROGRESS_CONFIRMED -> trip. Breaker receipt row: gen, root, frontier, evidence, spend, class, action.
- **Recovery**: `gsd_unit` asks GSD (`gsd-tools.cjs query` state/roadmap.analyze) with a fallback regex for both formats; residual subtracts phase artifacts (CONTEXT present, RESEARCH absent -> research residual only); child obligations {kind, prompt ref saved under state dir, expected output, state KILLED_WITH_PARENT|LOST|RETRYABLE|COMPLETED|SUPERSEDED} in the record; successor packet carries them.
- **State machine**: NOT_APPLICABLE split: ALL_COMPLETE -> settle; residual unreadable -> RECOVERY_FAILED (retry with the other method next pass, then surfaced incident), liveness LIVENESS_INCIDENT not OWNER_BOUNDARY. Every hold carries {reason, owner, condition, wake, expires, next}. WAITING_OWNER only for budget/authority/permission.
- **UWCP**: not used (absent); the AMR successor packet is the ContextImage transport.
- **Kill switch**: `CPP_MISSION_CONTINUITY=off` restores old observer behaviour.

## 4. Regressions (tools/test_mission_continuity.py, real git repos + real GSD 1.14 STATE.md fixture)

R1 main protected -> worktree -> commit -> main clean -> no false stall. R2 worker dies after commit -> research-only residual.
R3 rebind race (old-gen sample cannot trip). R4 clean tree after commit + high spend. R5 research-only artifact = progress.
R6 parent+child die -> obligation durable. R7 one recovery source unreadable -> fallback or RECOVERY_FAILED, never silent wait.
R8 two successive worktrees -> latest gen only. R9 bound worktree removed -> invalidation, no fabricated progress.
R10 breaker -> recovery -> successor end to end with no release. Each refusal paired with a control.

## 5. Credit Score rescue (after R1-R10 green and landed)

1. Capture evidence: 8043467, wt clean, researcher prompt from transcript -> state dir.
2. Migrate in place (no new mission/Goal): `bind` gen 1 -> Credit Score Engine-wt / gsd/dispute-engine-v1 / base 47e0f3c / head 8043467, cause migration; record child obligation "phase-1 research"; `authority --extend-hours 24`.
3. Recovery (new code) relaunches on the next sweep from residual: research -> plan -> execute phase 1. No manual release.
4. 8043467 stays on the branch; fast-forward main at phase completion only if main is unmoved and tests are green.
5. Retire wt + branch only after merged and clean.

## 6. Execution, concurrency, knowledge

- Work in a PP worktree `amcr-continuity` from live HEAD; land with `git apply` of my hunks only; foreign hunks never committed; same-line conflict -> explicit wait on that writer's commit.
- Commits: incident doc; binding+resolver+call-site inventory test; bind CLI+detection+generations; frontier+gate+receipt; GSD-backed residual; child obligations; state machine/liveness/wait contract; card+skill done-gate; UKDL/NEVER_AGAIN/CBR.
- Inline execution (not a Ralph mission): the supervisor under repair should not supervise its own repair. Self-host proof = the rescued Credit Score mission plus every new arm getting binding gen 1.
- Knowledge: vault/knowledge_base/ukdl-universal.md (HR/PR/Traps), NEVER_AGAIN entry for the class (CLASE 0 escalation: why the add_dirs fix did not prevent it), CBR via cpp-gsd-long done-gate.

## 7. Budget (processed tokens, cache reads included, as PP meters)

Semantic lower bound 2.0M · Lower 3.0M · P50 5.0M · P80 7.5M · P95 11M · Hard authority 12M (confidence ~60%).
Breakdown (P50): reality 0.35 (spent) · identity+resolver 0.6 · rebind+gen 0.5 · frontier 0.4 · gate+breaker 0.5 · recovery ledger 0.3 ·
residual 0.3 · children 0.3 · state machine+liveness 0.3 · fault suite 0.8 · landing+suites 0.4 · rescue 0.3 · canary 0.2 · self-host 0.1 ·
knowledge 0.3 · final review 0.6 · recovery reserve 0.8 (held) · meta tax 0.3. Excludes the Credit Score mission's own run.
Stop-loss: reforecast at 7.5M; halt and report at 12M.
