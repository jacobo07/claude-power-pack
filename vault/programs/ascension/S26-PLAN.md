# S26 plan: Open-Ended Scientific Evolution (method escape), PROPOSED 2026-11-11T14:30Z

Status: AWAITING OWNER APPROVAL. Nothing below is executed. Coordinator pane d957c937 (laptop).
Brief: Owner's pasted /cpp-gsd-long "GSD X Open-Ended Reconstruction Intelligence" (this session's first message).
Mission terms: open-ended reconstruction, strategy genesis, scientific uncertainty, method evolution,
independent certification, constitutive baseline ratchet.

## 1. Reality scan (measured 2026-11-11 14:14-14:20Z)
| fact | state | source |
|---|---|---|
| m-97b5a3985b92 (S25) RUNNING, epoch 4, worker 928323ee, goal ACTIVE, spend 25.52M of record 62.46M, hold null | OBSERVED | GEX44 `topology` 14:14:18Z |
| S25 cap: stop at 55.14M processed, 0.8M fresh, wall 2026-11-12T16:40Z | OBSERVED | t1 evidence/ascension/s25/budget.md |
| S25 phases 1-3 ticked, Phase 4 (W4 NO_COMPILE) WIP, 5-6 open | OBSERVED | gen3 ROADMAP @bfd413ee |
| t1 `t1/campaign` 9c526aa9; gen3 `mission/gen3` bfd413ee; GEX44 live PP 7bbaeb50; laptop PP 31d81a36 | OBSERVED | git log |
| t1 dirty: 6 tracked evidence files (pre-existing residue since 11-06/11-10) + untracked docs/arch | OBSERVED, NOT OURS | git status |
| GEX44 64 GB, 49 GB available, load 15; laptop 1.36 GB free (4.2%) | OBSERVED | free / hook |
| Tennis unique certified 1,198 (C 1,139 + CXX-only 58 + 1 C-via-cert_cxx); 3 overlaps not double-counted | PROVEN (S25_W0_PASS, receipt shas pinned) | s25/w0_account.md |
| KSR 8,687 CERTIFIED / 9,941 CNM / 5,453 NO_COMPILE / 3,447 FLAGS_SPLIT / 2,858 NO_TARGET / 2 XF_ERROR | PROVEN | ksr-frontier + W0 |
| NO_TARGET: 2,837 = CAPSULE_OMITTED_UNIT; additive stage ksrmb-s25-20261111-140212 built, pinned tree sha unchanged; G-NT1: 1,690 compile, 582 BINARY_EXACT canonical arm, 699 any arm, 1,147 NO_COMPILE, 21 NO_TARGET. Nothing certified. | PROVEN as diagnostic (S25_W1_PASS, 6 mutants red) | s25/g-nt1/run.json |
| FLAGS_SPLIT "one arm per object" H: REFUTED 0/6 objects; no arm is canonically admissible per fn | PROVEN negative (S25_W2_PASS) | s25/flags/test.json |
| 16/16 S24 overrides first-blocked at R2 (`ksr_lane.py:332 candidates()`), certifier contract | PROVEN (S25_W3_PASS) | s25/refusal/first_block.json |
| NO_COMPILE clusters: KSR 5,453 + Tennis 515 collapse to a few shared classes: POINTER_EXPECTED:long 977, IMPLICIT_CONVERSION void*->long 947, NOT_STRUCT 670, ILLEGAL_OPERANDS void*+long 373, UNDEFINED_IDENT 342, UNKNOWN_TYPE_DECL 337, ILLEGAL_OPERANDS void*+int 299 | OBSERVED (W4 gate pending) | s25/nocompile/clusters.json |
| S17 per-function model edits on NO_COMPILE: K2 retired IMPLICIT_CONVERSION 1/65, NOT_STRUCT 0/53, ILLEGAL_OPERANDS 13/61, UNDEFINED_IDENT 26/48 | PROVEN (S17 W1) | RESUMPTION_FILE |
| S24: selector 5/5 -> 1/4 on cohort 2 (overfit); challenger equal exact, -16% judge calls; Tennis 0/164 = 55 never fired + 109 fired-and-failed | PROVEN | checkpoint_s24.md |
| MethodGraph / Strategy Genome: no code under those names in PP modules (0 matches) | UNKNOWN owner; discovery in A0 | grep |
| GSDX-ARSI-001, CPP-ZTA-001, Context-First Agent Prompting Standard | NOT FOUND (2nd search; S24 also absent) | grep ~/.claude |
| Iteration methodology iteracion-avanzada-universal.txt | READ (5 phases: read source, classify CLASE 0-6, minimal fix + real done-gate, UKDL seed, cross-project) | Downloads/Promptsss |

## 2. Decisive reading
- NO_TARGET's key uncertainty is resolved (S24X + S25 W1). What blocks it now is an AUTHORITY (certify on a new stage identity), not science. Not the slice.
- FLAGS_SPLIT and the 16 refusals are blocked by the certification contract (R2 / no per-fn arm). Negative knowledge, not the slice.
- NO_COMPILE is the best case of METHOD EXHAUSTION vs REPRESENTATION: the per-function edit method was retired in S17 (0-1 of 53-65), yet W4 shows the failures are not per-function: ~5,968 fns fall in ~7 type classes that repeat per TU. Hypothesis: the source representation lacks TU-shared type knowledge (pointer/struct types emitted as `long`), which no per-fn operator can express consistently.

## 3. Mission objective
Prove one closed loop of method escape on a real exhausted method, with an independent oracle, a held-out cohort,
a second reuse case, negative knowledge with reopen conditions and a fresh-agent transfer. Certificates stay the
product goal; intermediate transitions (NO_COMPILE->COMPILES->BINARY_EXACT canonical arm->CERTIFIED) are tracked separately.

## 4. Experiments (each gated; each can close early)
A. METHOD ESCAPE (vertical slice). Representation change: TU-scoped type-constraint model derived from the
   compiler's own diagnostics + the binary's use of the value (loads/stores through it = pointer; field offsets = struct).
   Rival hypotheses: H1 shared TU type context (fix once per TU); H2 per-fn m2c defects (fix per fn); H3 missing
   headers/externs (UNDEFINED_IDENT/UNKNOWN_TYPE_DECL only). Discriminator: on a frozen dev cohort of TUs, apply
   H1 in an ISOLATED ctx variant and count transitions per fn; H1 predicts many fns per TU move together, H2 predicts
   isolated moves. Positive control: a certified fn in the same TU still matches under the variant. Negative control:
   a variant with the inferred type deliberately wrong must not raise COMPILES. Oracle: real mwcc + objdiff (independent
   of the generator). Held-out TUs frozen BEFORE the model is built. Builds on S25 W4's isolated-ctx repair result:
   if W4 already falsifies H1, A pivots to the Tennis 55 never-fired population (grammar expressiveness).
B. INSTRUMENT (only if A needs it): the type-constraint extractor is the candidate instrument. Retained only if it
   changes a decision on a second population (Tennis 515 or G-NT1 1,147 NO_COMPILE). If no instrument is justified, recorded as such.
C. PORTFOLIO: champion = current router (S17 per-fn llm_fix + O6 families + S24 challenger). Challenger = class-scoped
   portfolio with explicit ABSTAIN where applicability is unknown. Independent frozen cohort; the evaluator is not edited.
D. META: one challenger to strategy selection built from A-C outcomes, judged against the frozen champion on a
   population not used to build it. A negative result with its cause is a valid outcome.
E. TRANSFER: a fresh worker gets a new applicable TU set with only the recorded method + its applicability card;
   measured: correct retrieval, correct abstention, work avoided.

## 5. Ownership (REUSE first; no second runtime, ledger, registry or scheduler)
Mission runtime: CPP `tools/gsd_mission.py` (GEX44 live clone). Control plane: gen3 `mission/gen3` (.planning, PHASES packet).
Product + evidence: t1 `t1/campaign` (`modules/recon_fabric/*`, evidence/ascension/s26/). Certifier `certify.py`,
`ksr_lane.py`, receipts, pinned stage, canonical ctx, H2: READ-ONLY. Negative knowledge: t1 evidence + gen3 vault,
format of existing override/disposition sidecars (append-only). Institutional: UKDL via private index (laptop), KV.
New code only as t1 tools/s26_*.py + gates tools/test_s26_*.py with mutants.

## 6. Phases and token budget (PROPOSAL; new authority, not S25's)
| ckpt | content | processed cap | fresh cap |
|---|---|---|---|
| A0 | reconcile S25 checkpoint, ownership discovery (MethodGraph/Genome/WROS by grep), frozen cohorts (dev/heldout TUs) | 3M | 0 |
| A | type-constraint representation + discriminating experiment on dev, then held-out | 9M | 0 |
| B | instrument retention test on 2nd population (Tennis 515 or G-NT1 1,147) | 6M | 0.2M |
| C+D | portfolio vs champion; one meta challenger; independent cohort | 8M | 0.3M |
| E | fresh-agent transfer, negative knowledge + reopen conditions, UKDL/KV promotion, handoff | 4M | 0 |
| reserve | closeout | 1.5M | - |
| **total** | | **31.5M** | **0.5M** |
USD 0 (subscription CLI only). 12 cycles, 24 h wall. Measured basis: S23 ~39M, S24 ~26M, S24X ~17M per generation.
Tracked: processed, fresh, compiler invocations, CPU, wall, instrument build cost, outcomes, reuse.

## 7. Production reality gates (observable, executable)
test_s26_repr (dev+heldout transitions, controls, >=4 mutants red), test_s26_instrument (pos/neg controls,
UNKNOWN on blind input), test_s26_portfolio (frozen cohort sha, evaluator sha unchanged), test_s26_transfer
(fresh transcript), FRONTIER_CHECK OK + KSR_FRONTIER_CHECK OK + receipts sha 02c80ae3/8687 unchanged + pinned
stage tree sha eb0c92b4 unchanged, all S25 gates still rc=0. Coordinator re-runs every gate independently.

## 8. Stop rules
Budget/fresh/wall caps; per-lever K3 (0 of pilot = retire, two failed pilots = retire lever); 3 epochs no
progress = HALTED (runtime); A falsified AND alternative falsified = RESEARCH_EXHAUSTED scoped to those methods,
reopen conditions written; only Owner acts left = CHECKPOINT_COMPLETE.

## 9. Rollback
Every t1/gen3 change a micro-commit; new files only; ctx variants in new directories; `gsd_mission.py hold`;
CPP_MISSION_AUTORESUME=off. Nothing canonical is written, so rollback never touches receipts.

## 10. Not authorized by this plan
Certifying anything on the S25 stage or a ctx variant; any certifier/canonical-ctx/H2/receipt change; push;
paid API; live CPP deploy; budget beyond the new authority.

## 11. Owner decisions
1. Approve S26 with a NEW authority: 31.5M processed (incl. 1.5M reserve), 0.5M fresh, USD 0, 12 cycles, 24 h.
2. Sequencing: arm only after S25 reaches CHECKPOINT_COMPLETE and is judged (one writer per goal), as a new
   mission record in gen3 on GEX44 (S25's record has <= 7.3M left after its own cap and its wall ends 2026-11-12T16:40Z).
3. Close m-97b5a3985b92 COMPLETED at that checkpoint (`close` needs a typed Owner message; this approval message can carry it).
