---
id: PLAN-COGNITIVE-ECONOMY-PROGRAM
date: 2026-10-03
status: APPROVED 2026-10-03 (Owner "y" = all six defaults); phase-4 audit pending
covers: [cognitive-economy, context-lifetime, capability-virtualization, turn-advancement, compile-out, baseline-ratchet, cognitive-economy-program]
mode: ULTRA reconciliation once; EXECUTION MODE after approval
goal: cpp-cognitive-economy (Goal spine, modules/gsd_x/goal)
workstream: .planning/workstreams/cognitive-economy
done_gate: python tools/test_cognitive_economy_program.py --final
---

# Cognitive Economy Program -- close-out across existing owners

Thesis: CPP must waste less intelligence, never use less. The Reality Scan (2026-10-03, HEAD
`4d1cfb83`) found that most pillars already have a live owner, several executing in other panes.
This campaign is therefore a close-out: drive every pillar A-T to an evidence-backed terminal
disposition, CONSUME owners, BUILD only an unowned material gap.

## 1. Reality at approval (measured unless marked doc)

- Branch `feature/knowledge-acquisition` @ `4d1cfb83`, origin +15/-0 (incl. peer `d9072185` and
  peer K1-K4), 815 dirty entries (peers). Worktrees: main, `.claude/worktrees/gsd-x`, `.../ucep`.
- Peers: 7 CPP interactive panes; Ralph missions CPP `m-876f8b5a904a` (ucep) RUNNING, 2 InfinityOps,
  1 io-mnb. Ralph sweep OK.
- Root GSD milestone v1 archived ("Awaiting next milestone"); root STATE.md carries foreign edits
  -> this campaign uses its own workstream and never touches root .planning.
- /cpp-gsd-long = Ralph v3 only (M1-M5 proven, D1 COMPLETED live 2026-09-28). Not proven:
  multi-day endurance, live no_progress halt, reboot recovery.
- Durable Goal = Goal spine + scheduled `PP-GoalSweep` (LIVE 2026-10-02). No CPP program goal yet.
- Premise corrections: UKDL is `vault/knowledge_base/ukdl-universal.md`; UWCP is the VPS plane
  (`specs/uwcp.md` s12), not the owner here. No repo-wide materiality doctrine exists (grep 0).

## 2. Baseline (doc-reported; reproduced in P0)

7 d to 2026-10-02 (`wiki/tools/token_economy_*`, CCP C1-C4.1): cache read 54 %, write 33 %, output
13 %; main thread 72 % (ctx p50 305k); Opus 85.7 %; floor 91.3k empty dir / 111.6k this repo;
global rules 17.9 % + global CLAUDE.md 9.7 % of floor lead; idle > 1 h = 73 % of rebuilds (252,
~$611); 280/319 skills never invoked; Read re-derived 19.6 % (~188M rent, half siblings);
subagents do not inherit parent (0/219); meter reconciliation FAILS (75 -> 90 % unexplained).
Upper bounds still valid: KSR tool-output dead carriage <= 6.34 % (measured: rerun sha `117d042c`);
floor -40k <= 12.6 %; subagents -> Sonnet <= 3.8 %.
Falsified: generated KSR boot view; tool-I/O firewall; 5-min TTL (net +$1,262); "model-switch
rebuilds"; description hiding as a token saver.

## 3. Ownership matrix (predicted terminal = hypothesis, frozen in P0)

| Pillar | Owner | Campaign action | Predicted terminal |
|---|---|---|---|
| A baseline | CCP usage_index / tis_observed | freeze before-snapshot | IMPLEMENTED (connect) |
| B resident floor | CCP C4.1 + r2-instruction-residency + P3 ablation | consume, batch moves | AUTHORIZATION_BOUND per move |
| C capability virtualization | skill-residency-program, K-slice, ACV | consume; judge tool-schema floor | DEFERRED_STRONGER_OWNER (tools: likely REJECTED) |
| D context lifetime | economic-rollover-trigger + cognitive_os/gc.py | measure realized savings + displacement, hand to owner | MERGED_INTO_EXISTING_OWNER |
| E fresh epochs | parent-context-epoch-rotation, interactive rollover, idle-return proposal | measure via gsd_epoch census | MERGED_INTO_EXISTING_OWNER |
| F reread | CCP s15 | pre-registered sibling recurrence test | by data |
| G CCSE | none | folded into F | REJECTED/RESEARCH unless F earns it |
| H turns/advancement | CCP c7 root_progress v1 + Goal spine | turn-taxonomy archaeology | by data (campaign-owned) |
| I work packet | Goal brief.py + Ralph card | none | MERGED |
| J non-convergence | Ralph no_progress, Rule 12 | from H data | by data |
| K admission | KSR C | one CPP-corpus replication, same rule | REJECTED unless earned |
| L compile-out | CBR tower, compound-learnings | via R repair | IMPLEMENTED (repair) |
| M model routing | CCP C4 policy, cost_collapse | consume | DEFERRED / AUTH (quota) |
| N event-driven | PP-GoalSweep, Ralph sweep | none | MERGED |
| O cognitive IR | Goal spine | none | MERGED |
| P proof reuse | Goal judge, engine_identity | measure verification share | likely REJECTED |
| Q capital accounting | FIOS + this ledger | CAPEX/OPEX fields only | MERGED |
| R institutionalization | UKDL + /cpp-compound (STUCK 9x) | repair steps 7+8 | IMPLEMENTED |
| S baseline compiler | tools/baseline_ledger.py, family_baseline.py | audit trait derivation | likely MERGED |
| T institutional GC | /liveness, never-invoked skills | sweep + retire proposals | PARTIAL + AUTH |

## 4. Phases (workstream cognitive-economy; owned new files, pathspec commits, no push)

P0 Freeze: reproduce anchors; declare goal; one obligation per pillar; freeze triage, decision
rules, denominators (sha256). P1 Done-gate verifier with selftest mutants. P2 Measure (read-only
to owners): D, H, K, F/G, P, C-tools. P3 Repair: R/L compound pipeline; T liveness sweep.
P4 Build P2 winners only if unowned and >= materiality (possibly none), PRG in a real fresh
session. P5 One Owner decision bundle. P6 Close: UKDL 3-level + CBR review, ledger final,
judge --record, meta-analysis. Rollback = revert the phase's commits; goal log append-only.
CBR: EXPERIMENTAL for every finding until earned.

## 5. Done-gate (fixed before arming)

`python tools/test_cognitive_economy_program.py --final` exits 0 only when: Goal spine judge PASS
and `may_close`; ledger `vault/programs/cognitive-economy/ledger.json` has all 20 pillars in a
terminal state; every evidence pointer resolves (commit reachable, file sha256, owner plan
present); IMPLEMENTED requires a SATISFIED obligation + PRG; any move away from a frozen IMPLEMENT
needs a falsification artifact; every saving is realized|upper_bound|UNKNOWN with displacement
status; UKDL/CBR review record present; `--selftest` mutants (all-DEFERRED, dangling evidence,
unbacked demotion, saving without displacement, deferral prose) each RED.

## 6. Materiality, quality, displacement

Materiality: >= 3 % of a named weighted denominator earns a dedicated slice; correctness /
authority / security / horizontal-primitive exceptions argued separately, never lowering the
threshold; rules frozen before data. Quality: negative control, need-time delivery, full-context
oracle sample, missing-context incidents; recall dominates. Displacement: savings are intervals
(CCP S3 method); realized only when displaced work is measured on the same denominator.

## 7. Owner decisions (Q&A 2026-10-03, "y" = defaults)

1. Quota: approval = "spend now" for THIS mission only (CCP reset rule otherwise stands).
2. Peer-gated moves (rules->skills, skill hide in settings.json, idle-return): not executed;
   batched into P5.
3. Push: none.
4. Epoch renewal: existing PREPARED path only, as designed; no bypass.
5. Materiality: >= 3 % + exceptions as in s6.
6. /cpp-compound repair in scope (P3).

## 8. No-build

KSR generated view (falsified); tool-I/O firewall (not earned); context firewall (subagents do not
inherit); 5-min TTL (refuted); new long-run orchestrator (Ralph owns); new event system (sweeps
own); new state store (Goal spine owns); UWCP (VPS plane); capital dashboard (complexity tax);
CCSE without identity evidence.

## 9. Long-horizon state

Goal spine log is the authority; Ralph mission bound observe-only via `bind-mission`. Intra-
mission: Ralph relays at 40 % / 300k with <= 8 KB card. Budget halt: PREPARED successor only as
designed. Agents: <= 2 per wave, solo, durable output.

## 10. Execution log

- C0 `1cabd117` this plan.
- Phase-4 audit (general-purpose in the auditor role; `oneshot-architect-auditor` was refused by the
  agent-contract guard because it has no Write tool): `vault/audits/cognitive-economy-phase4-audit.md`,
  EXECUTE-WITH-FIXES, 11 gaps. Dispositions:
  - G1-G4, G11 (bind deadlock, whole-tree verdict pin, missing `obligations` key, plane machinery,
    double driver): the Goal spine is NOT the closure judge. The done-gate re-runs each IMPLEMENTED
    pillar's declared gate argv in one pass; the committed ledger is the campaign's authority; no
    goal is bound or marked autonomous. Finding handed to the spine owner via pillar O.
  - G2 fix (a) own-branch worktree REJECTED on measured evidence: the live `ucep` mission
    (`m-876f8b5a904a`) is held right now with "cwd not aligned with work_dir (diverged)" -- a worktree
    on its own branch blocks every fresh-worker relay once main moves. The mission runs in the main
    checkout like every other CPP mission.
  - G5 (no_progress blind in a shared checkout): ACCEPTED risk; bounds are --max-cycles 12 /
    --max-hours 24, and every phase (measurement included) commits its evidence. Recorded under J.
  - G6: compound repair narrowed to a new campaign module proven on a temp state copy; live apply
    and call-site switch are Owner items (pillar L rule).
  - G7: verifier hardened -- MERGED/DEFERRED need a per-pillar handoff file committed AFTER the freeze
    and naming the owner; sha256 mandatory on file evidence; measurements must name a frozen
    denominator and their command; owner evidence must be a frozen owner.
  - G8: L/R owner paths corrected; L1 now checks every frozen owner exists.
  - G9: workstream uses the precedent format (ROADMAP `### Phase N:`, STATE, REQUIREMENTS) and
    `init.manager` must list every phase before arming.
  - G10: UKDL/CBR candidates go to `vault/programs/cognitive-economy/ukdl-candidates.md`; promotion
    into `ukdl-universal.md` is an Owner item.
- Verifier `tools/test_cognitive_economy_program.py --selftest`: 30/30 (25 ledger mutants each
  killed by its intended clause, gate-red, unfrozen, real subprocess runner both poles, allowlist,
  real-git handoff both poles). Scratch mutation drill (L6 disabled) -> selftest FAIL, live file
  unchanged.
- Baseline reproduced: CCP anchor exact (23,925 / 6,230,548,450 / 9,893); D-W7 frozen in the ledger.
- Mission rotation stays legacy (no `--rollover-protocol capsule-v2`: peer spec, T8 held).
- P0 freeze `fa9ae2ed`, FROZEN_AT `c7e9a82f`, workstream `3859cabf` (init.manager 7 phases; freshness
  6/6 FRESH, foreign-terms control STALE).
- ARMED 2026-10-03: mission `m-fdefb0fca0c0`, `/gsd-autonomous --ws cognitive-economy`, 12 cycles / 24 h,
  permission auto, wall 35/40/30. Verified started: record RUNNING with owner session `4a7ee8bc`
  (pid 42728, heartbeat), host lists `m-fdefb0fca0c0-e1` bg busy, worker transcript carries the
  `--ws cognitive-economy` command. The arming pane does not run /gsd-autonomous (one writer).
  Monitor: `python tools/gsd_mission.py status`; done-gate: `python tools/test_cognitive_economy_program.py --final`.
