---
covers: [ic-gen2-freeze, ic-gen2-ledger, optimization-opportunity-row, pp-install-floor-by-pick, champion-baseline-freeze]
date: 2026-10-05
updated: 2026-10-05
tier: T3
status: ready
plan: vault/plans/autonomous-optimization-2026-10-05.md
programme: IC-gen2 autonomous-optimization
scope: [vault/specs/autonomous-optimization.md, vault/audits/autonomous-optimization-novelty-2026-10-05.md, vault/programs/incremental-cognition/gen2/, tools/ic_gen2.py, tools/test_ao_p0.py, tools/test_incremental_cognition_program.py, tools/gex44_env_preflight.py, tools/test_gex44_env_preflight.py, tools/usage_index.py, tools/tis_observed.py, wiki/tools/kme_pillars.py, wiki/tools/kme_token_audit.py, wiki/tools/kme_replay.py, modules/cognitive_os/co_12_telemetry.py, tools/skill_opportunity_signals.py, tools/sovereign_miner.py, modules/tower/ratchet.py, .planning/workstreams/autonomous-optimization/]
open_questions:
  - Q1 | RESOLVED | D-OQ1 the spec covers entries are multi-token and disjoint from the six entries of the plan of record, the plan front matter is never edited, and every task text names vault/specs/autonomous-optimization.md literally so the binding is REFERENCED, which outranks STRONG
  - Q2 | RESOLVED | D-OQ2 the cherry-pick trailer path is the operative preflight fix on GEX44 because floor object 5962571c is absent from this repository; the patch-id path is implemented only where the floor object exists; the constant needed to enable it without the object is a [P0] owner-bundle line for the laptop, never fabricated here
  - Q3 | RESOLVED | D-OQ3 the IC wrapper prints a distinct ICP_GEN2_VERDICT line; the programme done-gate is the gen2 --final PASS plus the Phase 6 Production Reality probe; gen1 red pillars A,B,C,I,J,K,M,N and L8 are inherited state, reported verbatim, never claimed green, never edited
  - Q4 | RESOLVED | D-OQ4 all five gen2 pillars M,O,P,Q,R predict IMPLEMENTED_AND_VERIFIED; the rule of P names FALSIFIED_OR_REJECTED_BY_EVIDENCE with a falsification artifact as a valid outcome; the frozen object is audited before the freeze commit because it cannot be repaired after it
  - Q5 | RESOLVED | D-OQ5 the champion Run 5 command is tagged reconstructed and never presented as verbatim because the script text was overwritten; the champion evidence files are copied into gen2/evidence with sha256 and plane gex44
  - Q6 | RESOLVED | PFP_PASS=28/28 and LG_PASS=20/20 re-measured on GEX44 on 2026-10-05 at 3f48f2e3 and reproduced on 2026-10-06 at 9b2bb43a
acceptance:
  - AC-1 spec READY at tier 3 and bound to its own task text without a tie | verify: python3 tools/test_ao_p0.py
  - AC-2 novelty record answers 13 of 13 questions with citations that resolve in tracked files | verify: V-AOP0-NOVELTY-CITES-RESOLVE
  - AC-3 gen2 pre-registration is valid and frozen | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --status
  - AC-4 one mutant is killed per gen2 rule with a green control | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --selftest
  - AC-5 preflight accepts a pick-only history and still refuses an unrelated history | verify: python3 tools/test_gex44_env_preflight.py --drill
  - AC-6 champion numbers are pinned to copied evidence with sha256 | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --audit
  - AC-7 Phase 1 pillar O closes with its frozen rule | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-8 Phase 2 pillar P closes with its frozen rule | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-9 Phase 3 pillar Q closes with its frozen rule | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-10 Phase 4 pillar M closes with its frozen rule | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-11 Phase 5 pillar R closes with its frozen rule | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-12 Phase 6 ratchet, inheritance, regression and overhead hold for pillars M, P and R | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
  - AC-13 Phase 7 red team findings are closed and the programme ledger is complete | verify: python3 tools/test_incremental_cognition_program.py --generation 2 --final
must_still_pass:
  - python3 tools/test_incremental_cognition_program.py --selftest
  - python3 tools/test_gex44_env_preflight.py
  - python3 tools/test_persistent_failure_park.py
  - python3 tools/test_mission_launch_gate.py
checkpoints:
  - CP-1 | spec is READY at tier 3 and binds REFERENCED to its own task text, never AMBIGUOUS against the plan of record
  - CP-2 | novelty verdict is EXTEND_EXISTING_OWNER with 13 of 13 citations resolving in tracked files, otherwise the slice stops
  - CP-3 | gen2 frozen object is audited, then FROZEN_AT is committed in a second commit, and --generation 2 --status exits 0 with the L2 pin live
  - CP-4 | preflight pick-only history reads READY, an unrelated history reads NOT_READY, and the drill kills every mutant with a green control
  - CP-5 | Phase 1 usage_index v5 ingests incrementally with zero re-read, parity 102 sessions 34871 calls 11549646300 cache_read, and its negative controls go red when they should
  - CP-6 | Phase 2 challenger reproduces the 7 KME-L measurement files identically and either beats the scoped path or is narrowed or rejected with a falsification artifact
  - CP-7 | Phase 3 discovery eval finds the KME-L hotspot without a KME signature, with the seeded, no-optimization and low-ROI controls behaving as labelled
  - CP-8 | Phase 4 opportunity rows carry the full field list, no row jumps straight to promoted, and the autonomy envelope tests drive both sides
  - CP-9 | Phase 5 the loop raises, prices and accepts the second workload itself with shadow agreement, a GEX44 canary and a realized dividend
  - CP-10 | Phase 6 a fresh worker takes the index path, bypassing the index turns a gate red, and overhead is below realized savings
  - CP-11 | Phase 7 independent red team findings reopen their phase and the programme closes with a handoff
---

# Autonomous Optimization -- IC gen2 programme spec (Tier 3)

Programme: IC gen2 (reopen pillar M, add pillars O, P, Q, R) of the incremental-cognition programme. Plan of record:
`vault/plans/autonomous-optimization-2026-10-05.md` (Owner APPROVED 2026-10-05). This file is the executable
optimization contract the gen2 ledger cites. Pillar letters M, O, P, Q, R collide with the cognitive-economy
letters, so every evidence line and rule id names the programme (IC-gen2 / AOP-*).

## Measured baseline (2026-10-05, plane gex44)

Plane: GEX44 host `kobicraft-gex44`, worktree `ao-gen2`, git 2.43.0, Python 3.12.3. Every figure below names its command.

- Champion Run 5 (unscoped, 2026-10-05 12:13 start, head 61909502): `STEP r4-population exit=3 killed=no wall_s=869 peak_rss_MB=184 read_GB=101.53`. Command: `grep r4-population /home/kobii/missions/zero-rescan-out/summary.txt` (file sha256 `a91bcbd477ebc9a13942bb470aa9a767539ace29b3bf6e3c0266a284b0c98dbe`, host-local, copied into the repo by plan 00-04). The command that produced the run is reconstructed, not verbatim.
- Champion Run 6 (scoped to `KobiiCraft-Core-Files|kme-wt-arena2`): `STEP r4-population exit=0 killed=no wall_s=24 peak_rss_MB=99 read_GB=2.83`. Command: `grep r4-population /home/kobii/missions/zero-rescan-out2/summary.txt` (sha256 `75e10e10f2e6a9de8280a22cb256c06f74ce9009b790be73ed3cb1c81205793e`). Ratio 869 s / 24 s is 36.2x and 101.53 GB / 2.83 GB is 35.9x.
- Frozen KME-L denominator: 102 sessions, 34,871 calls, cache_read 11,549,646,300. Source: `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json` and the gen1 ledger `frozen.denominators`.
- Preflight: `python3 tools/test_gex44_env_preflight.py` prints `ENVPF_PASS=55/57`; the two failing gates are `V-ENVPF-PP-REAL-READY` and `V-ENVPF-PP-STALE-REAL`, both because the floor commit object 5962571c is absent from this repository while picks 25a10ce5 and 308da56b are present.
- Park and launch gate: `python3 tools/test_persistent_failure_park.py` prints `PFP_PASS=28/28`; `python3 tools/test_mission_launch_gate.py` prints `LG_PASS=20/20`.
- IC done-gate today: `python3 tools/test_incremental_cognition_program.py --final` prints `L3` failures for pillars A, B, C, I, J, K, M, N, four `L8` failures (review ukdl, review cbr, delta product, delta intelligence), `CEP_VERDICT=FAIL failures=12` and `ICP_VERDICT=FAIL failures=1`. This is inherited gen1 state, outside this programme.

## 1. Problem

Execution history of the estate is read many times by many parsers. The measured case is KME-L: an unscoped population run
reads 101.53 GB in 869 s and, with `--until auto`, repeats a 9.5 GB scan ten times, while a scoped run reads 2.83 GB in 24 s.
`tools/usage_index.py` is incremental but lacks tool events, cwd, project attribution and content identity, and
the champion path never reads it. Recurring avoidable cost is found by the Founder naming it, not by the system. The
optimization lifecycle (opportunity, price, challenger, promotion) exists only as prose in plans.

## 2. Objective

Observe execution, detect recurring avoidable cost, price it, build the smallest challenger, prove it equal or stronger,
promote it through the existing `modules/tower/ratchet.py`, and make future work inherit it. KME-L is the first proving
incident; a second workload must be taken by the loop itself. The programme is pre-registered before any edit: the gen2
ledger freezes pillars M, O, P, Q, R with predicted terminals and falsifiable rules.

## 3. Non-goals

- No new operating system, runtime, database, scheduler or ratchet. EXTEND before NEW (HR-NOVELTY-001, record `vault/audits/autonomous-optimization-novelty-2026-10-05.md`).
- TOK-18 Gen3 (cost planner, PGO, model-boundary accounting, T2-1 canary) is not touched.
- `tools/gsd_mission.py` is out of scope. Gen1 frozen objects, `tools/test_cognitive_economy_program.py`, `tools/test_skill_capability_program.py` and the root `.planning/STATE.md` are never edited.
- No claim about the laptop install: laptop-only work is an owner-bundle line.

## 4. Actors

- Orchestrator (GSD execute-phase) owns tracking writes and wave order.
- Executor agents write the artifacts under pathspec-scoped commits.
- Owner decides authority items through `vault/programs/incremental-cognition/gen2/owner-bundle.md`.
- The verifiers: `modules/sdd_os/readiness.py`, `modules/sdd_os/spec_binding.py`, `modules/spec_gate/gate.py`, the CE verifier reused by rebinding, and `tools/ic_gen2.py`.

## 5. Functional requirements

- AOP-M (pillar M, reopened): durable priced opportunity rows with a lifecycle and an autonomy envelope. Rows carry the P4 field list, no row jumps straight to promoted, the envelope tests drive both sides, a branch below break-even stops and is recorded, and a predicted dividend is never labelled realized.
- AOP-O (pillar O): `usage_index` v5 substrate. Incremental migration with zero re-read of ingested files, six negative controls that go red when they should, population parity 102 / 34,871 / 11,549,646,300 on the GEX44 copy, cold and delta refresh cost measured.
- AOP-P (pillar P): KME-L challenger. The seven KME-L measurement files reproduce identically; it beats the scoped path (24 s, 2.83 GB) on repeated queries, otherwise it is narrowed or rejected with a falsification artifact naming the pillar.
- AOP-Q (pillar Q): generic detectors plus discovery eval. The KME-L hotspot is found without a KME signature; a seeded hit is found, a no-optimization control is not flagged, a low-ROI candidate is rejected; detected, missed and false positive counts and the detector overhead are reported.
- AOP-R (pillar R): a second workload taken by the loop. The loop raises, prices and accepts the candidate itself; shadow agreement, a GEX44 canary and a realized dividend are measured; the laptop scheduled-task deploy is an owner-bundle line.

## 6. Non-functional requirements

- UNKNOWN, INCONCLUSIVE and UNMEASURED are never PASS. A failed read is unknown, not absence.
- A predicted saving is never labelled realized.
- Every result names its plane (`plane: gex44`); a laptop figure is never reused as a GEX44 figure.
- Every rule has a live judge and a mutant that kills it, with a green control first.
- Commands are typed `python3` on this host; there is no bare `python` binary.

## 7. Acceptance criteria

The front matter `acceptance:` list is the authority: AC-1 to AC-6 are the Phase 0 items and AC-7 to AC-13 are one per
ROADMAP phase 1 to 7, each judged by the frozen pillar rule through `--generation 2 --final`. No acceptance item names a gate
that a later phase has not built.

## 8. Architecture spec

### 8.1 Components affected

Extended owners: `tools/usage_index.py` (substrate), `tools/tis_observed.py` (store identity), `wiki/tools/kme_pillars.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_replay.py` (champion and challenger), `modules/cognitive_os/co_12_telemetry.py` and `tools/skill_opportunity_signals.py` (detectors), `modules/tower/ratchet.py` (promotion), `tools/sovereign_miner.py` (second workload), `tools/gex44_env_preflight.py` (instrument fix). The single new file class is `tools/ic_gen2.py`, a judge of an existing ledger convention, plus the gen2 ledger under `vault/programs/incremental-cognition/gen2/`.

### 8.2 System flow

Plan of record -> this spec (judged by readiness and binding) -> novelty record -> champion evidence copied with sha256 -> gen2 `ledger.json` (frozen pillars, state, opportunities) -> commit A pre-registration -> commit B `FROZEN_AT` -> `--generation 2` judging by `tools/ic_gen2.py`, which rebinds the CE verifier globals inside a context manager and restores them.

### 8.3 Contracts

- Gen2 ledger shape copies the gen1 IC ledger: top-level `schema`, `program` (`incremental-cognition`), `generation` (2), `plan`, `terminal_vocabulary`, `frozen` (`frozen_note`, `materiality`, `denominators`, `consumes`, `pillars`, `champion`, `reopens`), `state`, `reviews`, `deltas`, plus an `opportunities` list outside `frozen`.
- CLI: `python3 tools/test_incremental_cognition_program.py --generation 2 [--status|--selftest|--audit|--final]`. Output lines: `ICP_GEN2_VERDICT=<PASS|FAIL> failures=<n>` for `--final` and `--status`, `ICP_GEN2_SELFTEST=<PASS|FAIL>` for `--selftest`, `ICP_GEN2_AUDIT=<PASS|FAIL>` for `--audit`. Exit codes: 0 pass, 1 a judged failure, 2 a usage or environment error.
- Only `frozen` is pinned by `FROZEN_AT` (a commit sha naming the pre-registration commit); `state`, `reviews`, `deltas` and `opportunities` may change after the freeze.

### 8.4 Failure modes

- A typo in `frozen` after commit A cannot be repaired: it is superseded by a generation 3.
- A `covers:` tie with the plan of record blocks every T2+ task as AMBIGUOUS; guarded by the disjoint covers, the REFERENCED rule and the binding V-gates.
- A leaked CE global binding after a gen2 run is a B1 failure; a gen2 gate asserts restoration.
- A keyword-silent novelty gate is a vocabulary limit, not evidence; the record answers the 13 questions from a discovered sweep anyway.
- A preflight trailer accepted without the required files or with a lookalike sha would fail open; exact 40-hex match and required-file checks guard it.

### 8.5 Rollback plan

Per artifact: revert the commit that introduced it. The spec, the novelty record and `tools/test_ao_p0.py` revert independently. The preflight fix reverts as one commit group and the live GEX44 install only changes through its normal fast-forward sync, never by hand. The gen2 freeze itself is not revertible: a wrong frozen object is only superseded by a generation 3.

## 9. Test plan

`tools/test_ao_p0.py` judges this spec (READY, sections, covers disjointness, binding, decisions) and the novelty record
(13 rows, citations resolve in tracked files, the live gate control, verdict), each with mutants. `tools/ic_gen2.py` has its own selftest with one mutant per gen2 rule.
`tools/test_gex44_env_preflight.py` gains red-first pick gates and a drill. The existing suites in `must_still_pass` stay green.

## 10. Validation

Run `python3 tools/test_ao_p0.py` (every line PASS, `AOP0_PASS=n/n`), then the gen2 commands of AC-3 to AC-6 as the later Phase 0 plans land. A clean control precedes every mutant so a judge that refuses everything cannot pass.

## Governance spec (Tier 3)

SDD-OS tier T3: new standard on a persisted ledger with cross-repo evidence. This spec is written before the first edit, carries `covers:` front matter and `status: ready` under the readiness grammar. Commits use explicit pathspecs, one falsifiable increment each, with the subject verified after the commit. The never-edit list of the plan of record applies unchanged.

## Cross-repo applicability (Tier 3)

The programme runs on GEX44 against the Owner-authorized KME-L corpus copy at `/home/kobii/kme-corpus/projects`, passed explicitly as a root. Results are labelled `plane: gex44`. Laptop deployment, the laptop inheritance test and anything under the laptop `~/.claude/` are owner-bundle lines (`[<P>]`), never actions of this programme.

## Compatibility matrix and migration strategy (Tier 3)

| Surface | Gen1 | Gen2 | Migration |
|---|---|---|---|
| IC ledger `frozen` | immutable (`FROZEN_AT` 18e928af) | separate gen2 ledger and its own `FROZEN_AT` | additive, gen1 untouched |
| IC wrapper CLI | `--final --status --pillar --selftest` | adds `--generation 2` dispatch | default generation stays 1 |
| `usage_index` schema | v4 | v5 in Phase 1 | incremental, no re-read of ingested files |
| Pillar M | `MERGED_INTO_EXISTING_OWNER` (dispositions only) | reopened as `IMPLEMENTED_AND_VERIFIED` | `frozen.reopens.M` records the gen1 prediction |

## Kill switches (Tier 3)

- KS-1 LIVE: revert the preflight commits; the live GEX44 install only changes through its normal fast-forward sync.
- KS-2 LIVE: gen2 judging is reached only through `--generation 2` and the wrapper `--final` / `--selftest`; reverting the dispatch commit removes it and gen1 judging is unaffected.
- KS-3 LIVE: `modules/tower/ratchet.py` `revert` undoes a promotion.
- KS-4 PLANNED (Phase 2): a forced champion or scoped path for `kme_pillars`.
- KS-5 PLANNED (Phase 5): a miner full-parse fallback for `tools/sovereign_miner.py`.

## Standardization rule (Tier 3)

A new programme generation is a new ledger directory with its own `FROZEN_AT`; the frozen object of an earlier generation is
never edited. Any new judge rule ships with a mutant that kills it and a green control. A documented capability carries an explicit status word (LIVE, PLANNED, ABSENT) and is never written as present while PLANNED.

## 11. Completion gate

Programme done-gate: `python3 tools/test_incremental_cognition_program.py --generation 2 --final` PASS (ICP_GEN2_VERDICT) plus the Phase 6 Production Reality probe. Gen1 red pillars A, B, C, I, J, K, M, N and L8 are inherited state, reported verbatim, never claimed green, never edited. Phase 0 is complete when AC-1 to AC-6 hold and CP-1 to CP-4 are observed.
