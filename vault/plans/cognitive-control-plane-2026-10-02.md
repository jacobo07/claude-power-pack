# Cognitive Control Plane — ULTRA-PLAN (2026-10-02)

> Status: **APPROVED** by the Owner 2026-10-02 ("y", six defaults accepted). Phase-4 audit done
> (10 gaps, all accepted); section 10 OVERRIDES sections 4-6 where they disagree.
> Extends, never replaces: `weekly-limit-burn-rca-2026-10-02.md` (incident of record),
> `cognitive-resource-os-2026-09-27.md` (CRO), `context-rent-2026-09-27.md`,
> `specs/interactive-context-rollover.md`, `specs/agent-capability-virtualization.md`.
> Zero new mega-system (HR-NOVELTY-001): every phase lands in an existing owner.

## 0. Reality at plan time (measured 2026-10-02)
- HEAD `8a4f036`, branch `feature/knowledge-acquisition` (tracks origin), 694 dirty paths
  (shared tree, other writers live), 14 worktrees.
- Live: 26 `claude.exe` (14 panes, 6 `--resume`, 2 mission workers `m-*-e1`, bg daemon).
  CO-08 gatherer: **34 hot sessions** in 120 min (cap 2): InfinityOps 9, CPP 7, TUA-X 7,
  GEO-audit 4, a scratch probe dir 4.
- Weekly meter ~90 % at 40 h 40 min (Owner). Remaining allowance is the binding constraint:
  phases that call models wait for the reset unless the Owner says otherwise.

## 1. P0 — subagent context inheritance (MEASURED, scratch `p0_inherit.py`, read-only)
219 subagent transcripts born in the window, 219/219 joined to the exact parent call that
dispatched them (meta `toolUseId`).
- First-call context p10/p50/p90: 49k / 95k / 101k. Parent at dispatch: 155k / 297k / 409k.
- **0/219 fork-like** (child first call >= 80 % of parent). spawnDepth = 1 for all 219
  (no recursion observed).
- Child median 96k when parent > 300k vs 49k when parent < 120k: correlation 0.36 comes from
  agent TYPE, not inheritance. Median first-call by type: general-purpose 98k, gsd-executor 98k,
  gsd-planner 97k, oneshot-auditor 78k, pp-code-reviewer 65k, **cpp-carrier-verifier 49k,
  Explore 26k**.
- RCA §6: 2,294 M cache read / 9,894 subagent calls = **~232k per subagent call** vs 95k at
  birth. Subagent cost = floor (~95k) x calls, and in-agent growth is about 1.4x the floor.

**Verdict:** the premise "subagents replay the parent transcript" is FALSE for this estate.
A parent-transcript Context Firewall is UNNECESSARY. The levers are (a) the agent FLOOR,
which carriers already prove can be halved, (b) in-agent growth on long executors, (c) model
inheritance, and (d) unattended fan-out volume.

## 2. Premises checked
| claim | status |
|---|---|
| CO-08 "hard" hot-session cap | DOCUMENTED-NOT-LIVE: demoted to an advisory (`modules/wrapper/prelaunch.py:262-280`); sees only kclaude pane launches, not missions, subagents or GEX44 |
| alarm output-only + 40 s silent timeout | CONFIRMED (RCA §4 items 4-5, `prelaunch.py:253`) |
| rollover ON | LIVE, but active only at 45 % (~450k); economic decider SHADOW and called without `start_head`, so 110/126 = "not at a boundary" (RCA §11) |
| nested agent recursion | NOT OBSERVED (depth 1 x 219) |
| model inheritance 53.5 % | MEASURED (RCA §6); intent UNKNOWN |

## 3. D2A
| capability | class | decision | owner |
|---|---|---|---|
| burn monitor / alarm | OWNED, INCOMPLETE | EXTEND | `modules/wrapper/cost_gate.py` + `tools/token_ground_truth.py` |
| usage index (incremental) | MISSING | EXTEND | `tools/tis_observed.py` (CRO-proposed single parser owner) |
| fan-out / call tree | MISSING (data exists: meta `toolUseId`, mission ids) | EXTEND | `tis_observed` report mode |
| estate concurrency governor | DOCUMENTED-NOT-LIVE | EXTEND | `modules/cognitive_os/scheduler.py` (CO-08) |
| spawn enforcement point | OWNED (agent-solo-guard on PreToolUse-Agent) | CONNECT | `hooks/agent-solo-guard.js` chain |
| mission admission | OWNED (Ralph, peer) | CONNECT (adapter only) | `tools/gsd_mission.py` — peer-owned, no edit without coordination |
| agent floor / tool surface | OWNED (ACV carriers, 49k) | EXTEND | ACV spec S5 + GSD agent defs |
| model policy | OWNED (routing table, TCO rule 5) not enforced | CONNECT | `vault/config/model-routing.json` -> PreToolUse-Agent |
| fresh epochs | LIVE, mis-triggered | EXTEND | `tools/rollover.py`, `context-watchdog.py` |
| semantic history compiler | PARTIAL (kclear capsule) | EXTEND: typed settled-question + negative-memory fields | capsule |
| parent-transcript firewall | — | REJECTED by P0 | — |
| in-session working-set GC / Context MMU | harness cannot evict live messages | REJECTED as a system; delivered via epochs + tool-output trimming (RTK) | — |
| quality lab | OWNED (ACV bench v2, P3 ablation harness) | EXTEND | `vault/benchmarks/agent_virtualization_v2` |

## 4. Phases (dependency order; mode)
- **C1 Burn monitor (EXECUTION, 0 model calls).** Incremental index, all categories, per-hour
  derivatives, typed MONITOR_FAILURE with last-success stamp, never silent. Replay on the
  10-02, 09-25 and 09-18 windows. Done = first warning time on the 10-02 replay is materially
  before 90 %, the false-positive rate on prior windows is stated, and a killed reader yields a
  visible failure.
- **C2 Fan-out ledger (EXECUTION, 0 calls).** prompt / mission / scheduled trigger -> parent,
  subagent, verifier, Ralph and remote calls. "Why did this prompt cost N calls" report.
  Unknown ancestry is typed UNKNOWN. Better unattended attribution than the 1 h heuristic.
- **C3 Estate governor, SHADOW (PLAN for the priority policy, then EXECUTION).** One estate view
  (panes, missions, subagents, GEX44 snapshot) feeding CO-08 `decide` with priority classes
  (interactive > critical verify/recovery > normal > background CAPEX). Shadow decisions are
  logged at two real points: PreToolUse-Agent for background spawns, and mission arm/renew
  through an adapter. Replay says what it would have deferred.
- **C4 Agent floor + model policy (EXECUTION; the A/B needs quota).** Attribute the
  98k -> 49k gap (tools / CLAUDE.md / skills listing per class). PreToolUse-Agent records
  inherit-vs-explicit (shadow). A/B on frozen bench v2: gsd-executor class inherit-Opus vs
  Sonnet. Policy changes only if non-inferior.
- **C5 In-agent growth (PLAN).** Growth curve of long executors (95k -> 232k average). Options:
  per-task executor epochs inside GSD execute, tool-output trimming. Chosen by measurement.
- **C6 Rollover trigger fix (EXECUTION).** Pass `start_head`; let the economic decider ask for
  the crossing below 45 % at a real boundary; record one AUTOMATIC crossing (owed §8). Add
  settled-question and negative-memory fields to the capsule.
- **C7 Bounded active control.** Only after C3 replay shows no critical work deferred:
  backpressure on background spawns and missions under the circuit-breaker states. Interactive
  panes stay advisory unless the Owner says otherwise.
- **C8 Baseline.** RCA closed with P0, UKDL (HR, PR, T), CBR entry, router line. Supersede
  CO-08's "hard cap" wording to match what is live.

## 5. Maturity
OBSERVE (C1, C2) -> SHADOW (C3, C4 policy, C6 economic trigger) -> WARN (C1 alarm) ->
BOUNDED (C7, background only) -> CERTIFIED (after one week of shadow data with no critical
deferral).

## 6. Benchmarks / PRG
Incident replay (C1, C3) · agent floor before/after per class (C4) · bench v2 A/B model
(C4) · one automatic rollover crossing on a real working session (C6) · deferral of one
synthetic background spawn while a protected verifier proceeds (C7) · fault injection:
reader timeout, missing ancestry, 29 workers, high burn with progress vs zero progress.

## 7. Risks
Shared tree with 694 dirty paths (pathspec commits, narrow oracles) · Ralph/gsd_mission
peer-owned (adapter, not edit) · the remaining weekly quota (model-calling work deferred) ·
GEX44 transcripts unread (C1 needs an ssh snapshot) · PreToolUse-Agent `updatedInput`
behaviour for `model` must be verified on the live harness before C4 relies on it.

## 8. First action after approval
Phase 4 of /ultra: one `oneshot-architect-auditor` pass over this file. Then C1: seal P0
into the RCA §13 and build the incremental burn index with the replay test.

## 9. Q&A defaults (approval accepts these)
1. Active control touches background spawns and missions only; interactive panes stay advisory.
2. GEX44 is included through a read-only ssh transcript snapshot.
3. Model-calling runs (C4 A/B, C6 crossing) wait for the weekly reset unless the Owner says "spend now".
4. Running missions (orca-dws-wt, recon) are not paused by this program before C7.
5. Alarm delivery: statusline + SessionStart card; PushNotification only at CRITICAL.
6. Thresholds are relative to the prior windows; the Owner's meter readings are optional calibration.

## 10. Phase-4 audit -> fix injection (oneshot-architect-auditor, Sonnet, 101.8k tok, 8 tool uses)
- **G1/G2 C6 duplicated SPEC-ECON-ROLLOVER**, which is already implemented by a peer (`139b19d`,
  `65bb95b`; `tools/rollover.py` dirty by a live writer). C6 = OBSERVE ONLY: after the reset, read
  ledger rows `tier: econ` -> `rollover_kclear_asked route=economic` from ordinary sessions.
  Capsule fields (settled-question, negative-memory) deferred to that spec's owner as a proposal.
  No edit to rollover.py or context-watchdog.py from this program.
- **G3 PreToolUse-Agent sees only Agent calls inside sessions that load the hook**, not mission
  processes. C3 first MEASURES which spawn classes traverse it, with a positive control that a
  mission worker's subagent appears. Mission admission stays a separate surface (adapter).
- **G4 Do not touch agent-solo-guard.** The shadow is a NEW sibling PreToolUse-Agent hook:
  append-only, never blocks, hard time budget, reads a cached estate view written by C1, and
  never scans transcripts inline.
- **G5 C4.0 zero-quota probe** of `updatedInput.model` before any model-policy enforcement claim.
  If it does not rewrite, C4 = record + advise only.
- **G6 C1 done-gate is a HOLDOUT.** Calibrate the weighted-unit allowance on the 09-23 week's
  meter pair (75 % at 2026-09-30 07:51Z, commit `90c9e82`), freeze, then score on the 10-02 week
  (90 % at 09:40Z). Pass = (a) the projected % at 09:40Z within +-15 points of 90 without
  re-tuning; (b) the first ELEVATED warning >= 12 h before 09:40Z; (c) negative control: no
  warning in the 09-16..09-18 window at matched elapsed time unless its own projection > 70 %;
  (d) killed reader -> MONITOR_FAILURE, healthy reader -> none. The weighting itself stays
  ESTIMATED.
- **G7 One parser.** The incremental index caches `tis_observed._calls_in` output per file
  (size+mtime) and `token_ground_truth.window_usage` reads through it, so no second parser.
- **G8 C0 first:** correct the CO-08 "hard cap" wording (0 calls). C5 depends on C1+C2 data.
- **G9 Model-call tripwire:** each phase's tests run with no `claude` subprocess; bench v2 and the
  ablation harness do not run before the reset.
- **G10 C7 unlock:** a frozen critical class list (verifier, recovery, interactive), >= 7 days of
  shadow rows with zero critical deferrals, and a control where a critical spawn is NOT deferred.

Revised order: C0 -> C1 -> C2 -> C3 (shadow) -> C4.0 probe -> [reset] -> C4 A/B, C6 observe ->
C5 -> C7 -> C8.

## 11. Reconciliation after C1 (2026-10-02 evening; AWAITING Owner approval)

Reality: HEAD `ebc5446` (ea34e0c/286ccbe/19a7bc5 ancestors), 13 commits ahead of origin, unpushed,
697 dirty paths, 28 `claude.exe`. C1 revalidated: 22/22, incident window = 23,925 calls / 6,230,548,450.
Peer `ebc5446` (state-centric mission, reality scan, not yet approved) assigns: CCP owns burn,
fan-out, estate governor, agent floor, rollover observation. Durable Goal state / packet /
semantic delta / event log = state-centric peer, by CONNECT to `modules/gsd_x/goal` (orphan spine).
CCP does not build them; it supplies metrology.

**Provider meter signal found locally.** Transcript rows carry `quotaLimits` (511 rows since
09-16): `rateLimitType` seven_day / five_hour, `status`, `resetsAt`, `overageDisabledReason`.
Distinct seven_day reset anchors coexist in time: Wed 17:00Z (09-16, 09-23, 09-30, 10-07),
Sat 18:00Z (09-27 -> 10-04, `out_of_credits`), 10-06 02:00Z. One account has one weekly window,
so >= 2 (probably 3) accounts/orgs write into the same transcript store. Current: the Wed-17Z
window REJECTED since 2026-10-02T11:54Z until 2026-10-07T17:00Z, while this session kept
calling = another account. New leading hypothesis H4 for RCA §14: week A usage was split across
accounts, the meter read covered one. The external meter becomes an ADAPTER over `quotaLimits`
(rejection, reset, window identity) -- provider truth, no fitted percentage.

Revised sequence: C1b (quota adapter + RCA §15) -> C2 (causal fan-out from promptId / origin.kind /
turnOrigin / subagent meta) -> C3 (post-hoc shadow over the index first; a live hook only with
Owner OK, since registration edits the shared dispatcher) -> C4.0 (differential floor decomposition
from visible injected text + agent-class differences; provider-opaque remainder explicit;
lifetime rent from the index) -> C4.1 decision by ranked controllable lifetime rent.
C5-C8 of section 4 move to the state-centric peer or wait for C4.1.

## 12. Observation -> governed admission (Owner "y", six defaults, 2026-10-02 night)

PRG-1 and PRG-2 passed on the real index (RCA §16). Six defaults accepted: PRG-2 = PASS with
five preconditions for enforcement; fix only the transcript-store identity now (workspace =
cwd and repository = git common dir arrive with their first consumer); progress v1 = commits,
goal-log events, green test runs, everything else UNSETTLED; obligations / proof / semantic
delta / epochs stay with the peer Goal spine (`modules/gsd_x/goal`, read-only joins, no edits);
phase-4 audit before code; no live admission hook in this plan.

Ownership: fan-out, shape, spawn outcomes = `tools/fanout_ledger.py`; admission =
`scheduler.decide_spawn` + `tools/estate_shadow.py` (shadow); identity = inside
`tools/usage_index.py`, no new module. Repeated-attempt refusal already exists
(`goal/epoch.RetryWithoutNewInformation`); proof reuse is `goal/judge.py` + `git_state.py`.

Sequence (micro-commits, execution mode):
1. this record. 2. `usage_index`: resolved-path store identity, alias rows migrated in one
transaction + schema bump, sha256-verified sqlite copy first; fixture with reversed listing
order. 3. `estate_shadow`: project from the resolved identity. 4. spawn outcomes REQUESTED /
HOOK_BLOCKED / FAILED_TO_START / RAN / RETURNED. 5. execution shape per root: width (peak
concurrent subagents), depth (parent chain + longest child chain), area (calls), surface
(input + cache write + cache read), duration; per-root sums must equal window totals.
6. golden incident f319ce75. 7. progress v1, UNSETTLED default, coverage reported.
8. `decide_spawn` v2 shadow: owner present, spend since last advancement, equivalent spawn
active, UNKNOWN separate from BACKGROUND; ALLOW / WOULD_DEFER / WOULD_REJECT; replay diff vs v1.
9. mutants via `tools/mutation_drill.py`: reversed listing -> two identities; blocked spawn
charged as executed; protected deferred; UNKNOWN treated as BACKGROUND; bands tuned on the
judged window; shape sums diverge; UNSETTLED reported as WASTE. 10. UKDL traps.

NEXT: duplicate-spawn report (singleflight observer), C4.0 rent ranking, re-derivation detector
(identical Read/Grep/Explore inputs across sessions) feeding "known work compiled out",
per-workflow cost envelopes. LATER: live admission, renewable leases, Goal P&L, event waits,
proof DAG. RESEARCH: archetypes, evidence market, correlated cognition, policy genomes,
digital twin. REJECTED: a goal/uncertainty graph inside CCP, a scalar cognitive currency, a
second telemetry system, fixed N-agent councils, a compiler framework as code.

### 12.1 Phase-4 fix injection (`vault/audits/ccp-s12-audit.md`, EXECUTE-WITH-FIXES)

- Commit 2 (G1-G3): migration rewrites all 8 path keys (`files.path`, `calls.file`, `calls.k`
  for `off|` keys, `quota.file`, `prompts.file`, `spawns.file`, `subagents.file`) with
  UPDATE OR IGNORE + delete-leftover, canonical row wins; one `BEGIN IMMEDIATE` transaction that
  re-checks the version inside it; sha256-verified copy first; no forced re-read. Dedupe in
  `_iter_files` by resolved path, keeping junction targets outside the store. Real `mklink /J`
  fixture, reversed order variant, shown red on the pre-fix code.
- Commit 4 (G4): schema gains `spawns.result_ts / is_error / result_head`; the index parses the
  parent's tool_result; HOOK_BLOCKED by an explicit marker set.
- Commit 5 (G5, G6): root resolved transitively with a cycle guard (nested fixture); depth =
  longest sequential call chain, children by max; spawn-tree height separate; active duration
  beside wall-clock; width stated as an approximation from call timestamps.
- Commit 7 (golden incident, RCA §17): progress cannot be "commit issued by this root". Attribute
  by joining the root's written files to commits in the WORKSPACE repository, in-span vs later,
  and report the instrument's own blind spots (truncated commands, quiet output).
- Commit 8 (G7): only pre-spawn data; equivalence via an input hash stored at index time;
  "active" = no `result_ts <= t`; UNKNOWN separate, replay-only vs live counts reported.
- Commit 9 (G8): the bands assertion moves into `replay()`; each mutant names its killing test.
- G9: goal-log joins stay out of `usage_index` (engine-closure test pins it).

## 13. Meta-optimization mega-prompt reconciled onto §12 (2026-10-02; Owner APPROVED, six defaults)

Defaults accepted: first dimension = spawn admission; journey unit = root joined to goal;
receipts regenerable from the index; only "path identity is not resource identity" becomes a
UKDL trap now; no live hook, no model-calling runs before 10-07 17:00Z; push per sealed commit.
c4 sealed `2856f8e` (owner: the pane writing §13; the s12 pane stepped off c4-c8 by message).

Reality: HEAD `7dd864d`, 9 commits past `5b8057c`; PRG-2 PASS (`e8d05c9`), store identity sealed
(`f234580`), nested-spawn project (`6b95854`). Anchor re-run: 22/22, 11/11, 17/17, 11/11, 4/4,
window 23,925 / 6,230,548,450. The prompt's P0/P1/P3 are DONE; its P2/P4/P5 are §12 commits 4-8.
Goal spine holds 3 goal logs / 226 events: goal-level learning is LOW SAMPLE (M0-M1).

Owners (D2A): journey substrate = goal log + epochs (`epoch.py`, peer, read-only join); journey
metrology = `fanout_ledger`; policy + shadow verdict = `scheduler.decide_spawn`; Policy Lab =
`estate_shadow replay`; ledger = `usage_index` (never written by the optimizer); CBR =
`modules/tower/ratchet.py`; mutants = `tools/mutation_drill.py`. NEW modules: none.

Additions to §12 (all zero model calls, shadow only):
- c8 gains a POLICY RECEIPT: policy id+version (bands hash), subject, pre-spawn features with
  as-of ts, verdict, reason band, floors checked, expected effect labelled ESTIMATE, evidence class
  (OBSERVATIONAL / REPLAY), deopt condition. Derived from the index, regenerable, never in context.
- c8b `fanout_ledger journey`: per root, joined to goal/epoch when bound, else UNBOUND: origin,
  shape, spawn outcomes, progress v1 or UNSETTLED, receipts, meta-overhead (wall s, rows read).
- c8c accounting independence: closure test that scheduler/estate_shadow never write usage_index.
- c9 extra mutants: receipt without deopt; optimizer writes ledger; UNSETTLED counted as WASTE.
- c10: UKDL trap "path identity is not resource identity" (evidence f234580); other laws stay
  candidates; tower entry for the receipt contract recorded EXPERIMENTAL, never promoted here.
- c10 closure (2026-10-03, Owner "y" option A). Trap committed `47d2e93a`. The tower clause is
  NOT executed, on purpose: the tower has no EXPERIMENTAL tier. CBR generations
  (`vault/tower/baselines/<family>/B<n>.json`) carry only `reviewed` / `auto` / `reverted`, and
  every non-reverted entry is injected and judged by the family done-gate (`active_entries`);
  FD deposits (`fable_distillation/deposits_*.jsonl`) have no maturity field and are inherited
  by every repo. Either write would make the receipt contract binding or broadcast. So the
  receipt contract is recorded HERE, with its maturity:

  | capability | status | owner | authority |
  |---|---|---|---|
  | policy receipt (`scheduler.spawn_receipt` / `replay_receipt`) | EXPERIMENTAL | §13 pane | shadow only: no hook, gate or launch reads it; regenerable from the index; gates V-SPV2-RECEIPT-* + c9 mutants |

  Promotion path, not taken here: a tower maturity tier excluded from injection and judging
  (tower owner's decision), then a control-plane family. The four candidate laws stay candidates.
Kill criterion: if v2 adds no would-defer over v1 with protected_deferred=0 across two windows,
verdict NO_CHANGE and the extra features are retired.
NEXT/LATER/RESEARCH/REJECT: see the inline plan of this date; NEXT = singleflight observer,
re-derivation detector (first compile-out candidate), C4.1 rent ranking, rollover-timing shadow.

## 14. C4.1 -- controllable lifetime rent, ranked (2026-10-03, offline, zero model calls)

Command: `python tools/floor_probe.py probe` (window 09-30T17Z..10-02T09:40Z, key `c41`).
351 transcripts, 0 skipped; fit 0.2746 tok/char, |residual| median 928 / p90 5,304.
Total startup floor rent 2,719,590,330 token-calls, IDENTICAL to C4.0 (reclassification only).
Rent = resident tokens x calls, mostly served as cache reads: it RANKS levers, it is not a price.
Named this pass: `agent_listing_delta`, `hook_additional_context`, `mcp_instructions_delta`,
`hook_success`/`hook_cancelled` (injection unverified, kept UNKNOWN). Unmapped fell 8.5 % -> 0.27 %.

| rank | lever | share of floor | where | control |
|---|---|---|---|---|
| 1 | global rules (`~/.claude/rules/*.md`, 13 bodies still always-loaded) | 17.9 % | all 346 transcripts incl. every subagent | CPP_NOW, Owner (HR-001 path) |
| 2 | global `~/.claude/CLAUDE.md` | 9.7 % | all 346 | CPP_NOW, Owner |
| 3 | skill listing (~9.9k tok each) | 8.2 % | main + most subagent types | CPP_NOW (disable unused skill sets) |
| 4 | agent directory listing | 5.5 % | main sessions | CPP_NOW (agent count) |
| 5 | project context (`~/CLAUDE.md` 1.5 %, PP CLAUDE.md, AGENTS.md) | 4.7 % | per project | CPP_NOW |
| 6 | MEMORY.md (InfinityOps 1.1 %, Orca-X 1.0 % lead) | 4.1 % | per project | CPP_NOW |
| 7 | mission payload (prompt_snapshot + opening) | 5.5 % | gsd-* ~14k each | CPP_NOW, per workflow |
| - | provider/runtime remainder | 39.6 % | system prompt, tool schemas, agent body | PARTIAL |

Reading: levers 1+2 are 27.6 % of the whole floor and travel into EVERY subagent (~40k
instructions tokens each; Explore carries none -- agent type is the switch, RCA §13 P0). The
rules move (rule -> skill + card hook) already exists as a pattern; four moves since 09-30 carry
NO ablation of their own. On disk now: rules 70,023 B in 23 files, CLAUDE.md 40,117 B.

Decision (Owner): which lever first. Each edits `~/.claude` (Owner-side, HR-001) and a quality
check needs model calls, so measurement waits for the weekly reset (2026-10-07 17:00Z) unless
"spend now". Recommendation: lever 1, one rule at a time, ranked by its own share (top:
concurrent-writers 1.78 %, technical-failure 1.76 %, scoped-side-effect 1.66 %), each with the
P3 ablation the first three moves had. Gates: `test_floor_probe` 9/9 (V-FLOOR-DETAIL-FILES,
-NAMED-TYPES, -INSTR-CLASS, -RANK-CONTROLLABLE, -RANK-CLASSES; RANK-CLASSES seen red first).
Owner "y" + "spend now" (2026-10-03): lever 1 via P3 set R2 (`ADDENDUM-R2.md`, frozen `6f5c3cf9`).

## 15. Re-derivation, first measurement (2026-10-03, prototype, read-only, zero model calls)

Same window, 351 transcripts, 13,173 Read/Grep/Glob calls paired with their results. A
re-derivation = same tool + same canonical input + same result bytes already seen in an EARLIER,
DIFFERENT transcript (a changed file is not one). Script: session scratchpad `rederive_proto.py`
(not in the repo; promote only with a consumer).

| tool | calls | re-derived | share of result chars |
|---|---|---|---|
| Read | 7,708 | 855 (11.1 %) | 19.6 % (8.56M chars, ~2.35M tok at read time) |
| Grep | 4,707 | 10 | 0.2 % |
| Glob | 758 | 11 | 0.2 % |

Resident rent of re-derived results (tokens x later calls in that transcript) ~188M token-calls,
~6.9 % of the startup-floor size; split evenly: same root (a subagent re-reading what its own
root session read: 473 reads, ~94M) and other roots (403, ~94M). Top inputs: `.planning` phase
docs in worktrees (orca-dws, recon_work), GEO-audit client context, `gsd-core/workflows/autonomous.md`.

Limits: rent ignores compaction (over-estimate); a fresh subagent MUST read what it needs, so
this is spend, not waste (RCA §18). The controllable part is the same-root half, where the parent
already held the bytes; the lever there is what the spawn prompt carries, not a cache. Grep/Glob
re-derivation is negligible: a detector for them would measure nothing. NEXT if pursued: per-
workflow attribution of the same-root half (gsd planner -> executor -> verifier re-reading PLAN).

### 15.1 Same-root attribution (Owner "y", same prototype, same window; ~94M token-calls)

| first reader -> re-reader | share |
|---|---|
| general-purpose -> general-purpose (siblings) | 55.0 % |
| gsd -> gsd | 30.9 % (executor -> executor 13.4, researcher -> planner 5.8, plan-checker -> executor 4.5, planner -> executor 4.3) |
| MAIN -> any subagent | 8.2 % |
| everything else | 5.9 % |

By file: `.planning` docs 53 % (PLAN 23.5, SUMMARY 8.6, RESEARCH 7.7, CONTEXT 6.4, STATE 2.1);
source and other files 46.9 %; workflow/agent definitions 0.1 %.

**Correction to §15:** the same-root half is NOT mainly "the parent already held the bytes".
Parent -> child is 8.2 %; ~86 % is SIBLINGS reading the same file: parallel general-purpose
agents, and gsd executors of one phase each reading PLAN / CONTEXT / RESEARCH.

What this does and does not license. Carrying a file in the spawn prompt instead of letting the
child Read it moves the same bytes into the same resident context, so it saves ~nothing. The
rent falls only if (a) fewer subagents each hold the document (fewer siblings, or one agent
doing the work serially), or (b) each child gets only the excerpt it needs. Both change workflow
behaviour (gsd is not this repo's code: `~/.claude/gsd-core`), so neither is a CCP edit; they
are inputs for whoever owns the workflow. No detector tool is promoted: no consumer, and the
finding is a one-off structural fact, not a quantity that needs watching.
