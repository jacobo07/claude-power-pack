---
covers: [d21-tennis, tennis-reforecast, c2b-stale-input, fanout-readiness, rea-disposition, recon-cognitive-deflation]
tier: T3
status: awaiting-owner-approval
date: 2026-10-11
---

# Tennis Reconstruction Optimization + Reforecast (TRF) -- Master Plan, 2026-10-11

Status: AWAITING OWNER APPROVAL (boundary 1). The chat is the approval surface; this file backs it up.
Nothing was mutated to produce it except this file. Source brief: the Owner's /cpp-gsd-long prompt of 2026-10-11.
Owner "y" of 2026-10-11 (to "authorize Phase-7 job 2 of 4") is recorded; this plan does not spend it before W2 certifies.

## 1. Reality delta (measured read-only, 2026-10-11)

| Claim in the brief | Verified state | Evidence |
|---|---|---|
| ~50 C2b jobs returned STALE_INPUT "environment" | **ONE job** (ksrmb-20261010-203003), 50 units, ONE job-level custody verdict copied onto 50 rows. "environment" is the fixed miss_class label for ANY custody verdict, not an environment finding | candidate.py:485-487; candidate_ledger.jsonl: 50/50 rows, identical evidence |
| Cause unknown | `no CURRENT_CAPSULE to compare capsule cap1-ba8a3cfe2822 against`: C2a-fix built a new capsule, nothing registered it as CURRENT, the local judge failed closed AFTER the remote job ran | ledger evidence field; custody.py:321-322 |
| Remote run failed | Remote receipt verdict PASS, reason OK, 549/549 capsule files verified, 50 units executed | returns/ksrmb-20261010-203003/run/receipt.json |
| (hidden) | **All 50 compiles rc=1, "Errors caused tool to abort."** Every source is raw m2c output with unresolved `?` types (1-7 per function) and `unk*` fields; family CXX compiled with `-lang c`. Uncompilable by construction | task.json units[].source_text; receipt units[].compile |
| C2b measures tokens per function | **It could not.** Strategy was `free_baseline` only (compile m2c output unchanged): no model step exists in the job. Even with CURRENT_CAPSULE fixed it would have produced 0 model-cost observations | task.json strategies = {free_baseline} |
| C2b informs Tennis | **No.** CP50 draws from the Wii Sports Resort main.dol (main:8042..., draw anchor 0f2ecb37). Tennis lives in SportsPackEP.dol, never onboarded (no corpus, census, split certification or oracle parity) | ROADMAP:15, :232; d11-tennis-step0.md:8-11 |
| stderr is diagnosable | Receipt keeps only the last line of the compiler's stderr | receipt units[].compile.stderr_tail |
| 4 model MATCHes ever | Confirmed (Sonnet, match-accel ledger) | recon STATE.md:86 |
| cp50-c2 ~11.2M left | 11,226,294 remaining, open 0 (goal-status 2026-10-10) | mission_spend.py goal-status |
| REA is a candidate for Tennis | **REA admits no PowerPC/DOL target.** Windows lane = x86/x86-64 PE only (Ghidra 12.1.x, JDK 21+); ELF lanes are per-architecture (MIPS documented); no doc read mentions PowerPC/PPC/Gekko. MIT, release rea-agents-6.3.0 (2026-10-09), HEAD 9515d2fcd398 (2026-10-10). Upstream refuses unsupported targets explicitly instead of guessing | docs/windows-ghidra-p0.md:14-31, docs/ghidra-mips.md:9-20, README:147-182 |
| Local tooling | Ghidra 12.1.2, Dolphin, JDK 17/21, Node v24.15.0 present; Owner rule "zero local compiles, GEX44 lane only" (2026-10-03) still binds compiles | Apps listing; recon STATE.md:66-67 |
| Commits in recon worktrees | `.ksr_vault` snapshot gate refuses commits in fresh worktrees (blocked C1, C2a, C2b); workaround = byte-identical copy into keosdtk-home | C2a-receipt, cp50-c2-remaining.md row 2 |
| Iteration standard | File present; applied by workers at the checkpoints of section 7 (not read in this scan) | Test-Path True |

## 2. Assumptions overturned

1. "50 failures" -> one shared precondition failure, fanned out after the effect (FANOUT_BEFORE_READINESS, confirmed).
2. "environment" -> a label, not a diagnosis (diagnostic vocabulary collapse).
3. "Fix STALE_INPUT, rerun C2b, measure tokens/function" -> the rerun would still measure nothing: the job had no model step and its sources cannot compile. Two more shared preconditions were missing: source compilability and an experiment that contains the cognition it claims to measure.
4. "C2b/C3 gives the Tennis number" -> CP50 is a Resort benchmark. A Tennis forecast needs Tennis evidence.
5. "REA as Tennis evidence plane" -> not for a PowerPC DOL today. Principles (evidence + unknown ownership, projections, explicit refusal) are adoptable; the dependency is not.
6. 215M / 1,927M -> function count x a guessed cost under a topology that never ran. Not a measurement of anything.

## 3. Root-cause matrix

| Class | Verdict | Mechanism / evidence | Fix owner |
|---|---|---|---|
| C2B_STALE_INPUT_ENVIRONMENT | CONFIRMED, root found | no CURRENT_CAPSULE registration after a capsule rebuild | W1 |
| SHARED_PREFLIGHT_MISSING | CONFIRMED | preflight.json checks daemon/keys/shutdown/return path; not capsule-current, not source validity | W1/W2 |
| FANOUT_TOO_EARLY | CONFIRMED | one job-level verdict replicated into 50 rows; job slot spent | W2 |
| (new) SOURCE_UNCOMPILABLE_BY_CONSTRUCTION | CONFIRMED | m2c `?` types + `-lang c` on CXX; detectable with zero compiles | W1 |
| (new) EXPERIMENT_CANNOT_MEASURE_ITS_TARGET | CONFIRMED | free_baseline only; no cognition in the job | W5 design |
| (new) DIAGNOSTIC_TRUNCATION | CONFIRMED | stderr_tail = last line only | W1 |
| (new) COMMIT_GATE_BLOCKS_WORKTREES | CONFIRMED (3 lanes) | .ksr_vault snapshot gate drift in fresh worktrees | W1 (diagnose; fix or certified copy route) |
| COST_PER_FUNCTION_UNMEASURED | CONFIRMED | 4 model MATCHes ever; 0 Tennis observations | W5 |
| FORECAST_TOPOLOGY_CONTAMINATION | CONFIRMED | d21 budget = N x guessed c | W8 |
| CONTEXT_FLOOR_UNKNOWN | PARTIAL | fresh floor 115-150k measured elsewhere; slim floor 18,739 measured (ce-a4 F0); not on recon workers | W5/W6 |
| LEARNING_CURVE_UNKNOWN | CONFIRMED | no sequence ever run | W5 same-family sequence |
| NOVELTY_DENSITY_UNKNOWN | PARTIAL | shape overlap 23% exact / 32% loose with Resort; novel closure 1,323 | W7 |
| MODEL_NECESSITY_UNPROVEN | CONFIRMED | no admission records why a model is needed | W5 cascade |
| CROSS_BINARY_REUSE_UNMEASURED | PARTIAL | shape matches exist; Resort side mostly unsolved (294 SRC PROVEN of 34,159) | W7 |
| PROOF_COST_UNKNOWN | CONFIRMED | no per-unit proof attribution | W6 |
| REA_VALUE_UNKNOWN | RESOLVED for native PPC: EXTERNAL_LIMITATION | see section 1 | W4 confirms with one tool-catalog call |

## 4. Owner map

| Capability | Disposition | Owner |
|---|---|---|
| Capsule build / custody / judge | EXTEND_CPP (recon core) | capsule_build.py, custody.py, candidate.py |
| Fan-Out Readiness Certificate | EXTEND preflight.json (job dir) into a certificate children cite | stage.py send path |
| Source compilability gate | IMPLEMENT (zero-compile lint for unresolved m2c types, lang/family consistency) | m2c_producer.py / arm_a.py prepare |
| Type repair transform | IMPLEMENT minimal deterministic pass; model only for the residual | new transform in decomp core |
| Compile + objdiff oracle | ALREADY_DONE (canonical GEX44 runner, A/A PASS) | runner_lib, match.py, objdiff_xcheck.py |
| Tennis corpus / split / shapes | EXTEND (step0-3 artifacts exist) | wst_tennis/step0-3, corpus.py, split_player.py |
| Family clustering | EXTEND shape hashes (step0) + closure_profiles.py | decomp core |
| Causal token ledger | CONNECT session_autopsy / usage_index / mission_spend per unit; CDC C1 is the long-term owner | PP tools |
| Proof of Model Necessity | CONNECT work_proof (A6) + tier_routing (A4) as a unit-level admission record | PP tools |
| Semantic IR / theorem registry | MINIMAL: JSONL claim ledger (claim, evidence, invalidators) consumed by the transform; no new OS | decomp core |
| Native evidence plane | USE existing DTK + m2c + Ghidra 12.1.2 (PPC Gekko language) where needed; REA = EXTERNAL_LIMITATION for PPC | -- |
| REA | REJECT as dependency now; OVERLAY_CPP principles; UPSTREAM_CANDIDATE: a PowerPC/DOL lane (an issue, not code, this mission) | upstream |
| Dolphin proof | NO_WORK this mission (Scope A execution, not the reforecast) | D7 harness on GEX44 |
| UWCP / GEX44 placement | USE existing GEX44 compute-job lane only | stage.py |
| Goal / capital | Owner Capital Authority (OCA) capsule from the approval | capital_authority.py |
| Execution driver | Ralph mission, packet workers, deterministic chain tick; no coordinator pane | gsd_mission, gsdx_chain |

## 5. Work units, mode, dependency order (self-hosting order)

Order: make measurement trustworthy -> remove shared waste -> build the cheap cascade -> measure on Tennis ->
learn families -> optimize only where it pays -> remeasure -> reforecast.

| WU | Content | Mode | Depends | Done check |
|---|---|---|---|---|
| W0 | This scan + plan | ULTRA-PLAN | -- | this file |
| W1 | Root fixes: (a) capsule rebuild registers CURRENT_CAPSULE atomically or refuses send; (b) zero-compile source lint (unresolved m2c `?` types, `unk` fields, lang/family mismatch) at prepare; (c) full stderr preserved (bounded head+tail); (d) diagnose the .ksr_vault gate in fresh worktrees (fix, or a certified copy route with hash proof); regression tests with red controls reproducing C2b's exact rows | EXECUTION | W0 | C2b replay fixture: judge refuses BEFORE send; lint rejects all 5 C2b sources; mutants killed |
| W2 | Fan-Out Readiness Certificate: one content-addressed record (capsule id + manifest, CURRENT pointer, pins/tool hashes, source-lint pass, job key, binary identity) that stage.py send REQUIRES and children cite; invalidated by any input change | EXECUTION | W1 | send refuses without a valid certificate; certificate invalidates on capsule change (drill) |
| W3 | Tennis onboarding, minimal for measurement: SportsPackEP.dol split reuse (step0), compiler fingerprint (mwcc version/flags from the binary, checked against the Resort pins), m2c over a stratified Tennis sample, oracle parity on 2-3 known-good objects (A/A on Tennis) | EXECUTION, PLAN for the compiler fingerprint only | W2 | Tennis A/A PASS on GEX44 or a named refusal |
| W4 | REA canary: install rea-agents 6.3.0 in an isolated prefix, one target-resolution call on SportsPackEP.dol and on one DTK .o; record the refusal or admission. Ghidra 12.1.2 headless PPC-Gekko import of SportsPackEP as the comparison evidence path, only if W5 needs evidence DTK/m2c lack | EXECUTION | -- (parallel to W1) | disposition table with the tool's own output |
| W5 | Stratified measurement (the redesigned C2b), on Tennis, in cascade order: NO_WORK -> Resort-shape donor -> deterministic type-repair transform -> compile/objdiff -> model repair only with a Proof of Model Necessity record. Sample ~24 functions: 6 m2c-clean, 6 with few unresolved types, 6 with many, and one same-family sequence of 6 (cold first, warm after) | EXECUTION; topology = one locality worker per cohort, no fan-out | W2, W3 | per-function record (amendment-d fields) for >= 20 functions; causal categories filled |
| W6 | Causal ledger: per-unit attribution (semantic inference, startup/context floor, search, control, proof, repair) from transcripts + receipts, deterministic | EXECUTION | W5 running | attribution covers >= 95% of measured tokens; unattributed share reported |
| W7 | Family / novelty: deterministic clustering over all 1,797 Tennis candidates (shape hash, unresolved-type profile, call context, Resort donor availability) -> family count, recurrence, novelty density | EXECUTION, zero-model scripts | W3 | family table + novelty density with method stated |
| W8 | C3 recompiled: current-topology forecast vs compiled-learning forecast; Scope A and B semantic lower bound / LOWER / P50 / P80 / P95 / hard; CAPEX vs Tennis OPEX; Scope-B admission decision | EXECUTION | W5-W7 | file with every figure sourced M/D/H |
| W9 | KV / FIOS / UKDL / CBR promotion (dedup first), handoff | EXECUTION | W8 | entries + one final handoff |

Bounded optimization (W5b, inside W5's envelope, only on a measured signal): if the same-family sequence shows a falling
cost, compile one transform for that family and re-run 3 siblings; if flat, record why and do not scale.

## 6. Experiments, canaries, holdouts

- Canary 1 (W1): replay C2b's job record through the new gates -> refused before send, zero GEX44 jobs.
- Canary 2 (W2): certificate invalidation drill (touch the capsule -> send refuses).
- Canary 3 (W3): Tennis A/A on GEX44 (spends 1 compute job).
- Experiment (W5): 2-3 GEX44 compute jobs (one per cohort batch), each holding all of a cohort's compile candidates.
- Holdouts: cold vs warm (same-family sequence); tooling holdout (3 functions with and without the type-repair
  transform); model-routing holdout (Sonnet vs Haiku proposal on 3 functions under the same oracle). The REA holdout is
  replaced by the W4 refusal record unless REA admits the target.
- Not run: Dolphin, real Wii, mass Scope A or B, CP50 itself.

## 7. Stop-losses and self-deflation

- Each WU runs as a packet worker with its own route (target/stop); a crossed unit stop halts that unit, never raised.
- W5 stop: if after 12 functions no model-free path closes anything AND the model path verifies < 2, stop, record, and
  reforecast from what exists.
- Meta-optimization tax cap: W1+W2+W6+W7 <= 40% of mission spend; if exceeded, W5 proceeds with what exists.
- No coordinator pane: the chain tick arms units; this pane ends after arming. Coordinator spend <= 1.0M total.
- Two identical failures of one shape -> pivot (Regla 12). Repeated failure -> invariant/detector, recorded in FIOS.
- Iteration standard (`iteracion-avanzada-universal.txt`) applied inside W1, W3, W5, W8 and before W9.

## 8. Token budget for THIS mission (processed tokens; the Tennis budget is an output)

Basis: worker per-call 122k measured (C1); slim floor 18.7k measured (ce-a4 F0); substantial unit ~4.5M (Autonomy S1).

| Line | LOWER | P50 | P95 |
|---|---:|---:|---:|
| W0 reality scan (this pane, sunk) | 1.5 | 2.0 | 2.5 |
| W1 root fixes + tests | 1.0 | 2.0 | 3.5 |
| W2 readiness certificate | 0.5 | 1.0 | 2.0 |
| W3 Tennis onboarding (minimal) | 2.0 | 4.0 | 8.0 |
| W4 REA canary (+ Ghidra comparison if needed) | 0.3 | 0.8 | 2.0 |
| W5 measurement (24 fns, cascade, holdouts) | 4.0 | 9.0 | 18.0 |
| W6 causal ledger | 0.5 | 1.0 | 2.0 |
| W7 family / novelty | 0.5 | 1.0 | 2.5 |
| W8 C3 + reforecast | 0.8 | 1.5 | 3.0 |
| W9 KV/UKDL/CBR + handoff | 0.8 | 1.5 | 2.5 |
| Coordination (chain, <= 1.0M) | 0.3 | 0.7 | 1.0 |
| Recovery reserve | 1.5 | 3.5 | 5.0 |
| **Total** | **~13.7M** | **~28.0M** | **~52.5M** |

Semantic lower bound ~8M (root fixes + 20 measured functions with zero waste + reforecast). P80 ~38M.
**Hard authority recommended: 55M** (token_estimate 27.5M x breaker 2.0). Meta-optimization tax at P50 = W1+W2+W6+W7 =
5.0M of 28.0M (18%). Confidence: MEDIUM on W1/W2/W4/W8; LOW on W3 and W5 (Tennis compiler fingerprint and
type-repair success rate are unmeasured).

GEX44 compute jobs (second budget): up to 4 (Tennis A/A 1, measurement 2-3). Phase-7 job 2 of 4 (Owner "y") stays
reserved for the Resort CP50 lane and is not used for Tennis.

## 9. Approval surface

"y" approves: goal `tennis-rf` with hard stop 55M declared through the Owner Capital Authority; a new recon worktree
from keosdtk-home for this mission; W0-W9 as packet workers driven by a chain tick; up to 4 GEX44 compute jobs for
Tennis; local recon-core changes and tests; an isolated REA install (rea-agents 6.3.0) and Ghidra headless use;
local commits (pathspec; certified copy route into keosdtk-home if the snapshot gate still refuses); KV/UKDL/CBR entries.

Excluded: Scope A or B execution beyond the ~24-function measurement sample; Dolphin and real-Wii runs; raising any
cap; push; GEX44 live-install changes; cp50-c2 spend; Phase-7 jobs; any change to the Tennis scope definition.

Returns to the Owner only on: capital (55M reached with obligations open), a legal/security question, a credential,
or a scope question the evidence cannot answer.
