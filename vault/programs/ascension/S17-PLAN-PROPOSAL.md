# S17 PLAN PROPOSAL — "Yield First": exact functions per million tokens (NOT ARMED)

Status: PROPOSAL, awaiting Owner approval. Drafted 2026-11-07 by coordinator 6451ca22 after Owner "go ahead".
The ascension programme was CLOSED today (gen3 3a500710). Approving this plan reopens it with a new mission. A closed mission is never renewed.

## 1. Why S16 yielded 0, and what this plan changes
Every S since S9 was a research generation. Each one pre-registered 2-3 hypotheses, froze cohorts, sealed held-outs and decided by falsification. That kind of generation retires ideas; it does not produce functions. The model fixing pool spent USD 0 from S11 to S16.
S17 is a production generation:
- the primary metric is **certified exact functions per 1M processed tokens**;
- rigor is limited to what keeps a certificate trustworthy;
- cert_cxx is unchanged.

## 2. Facts this plan is built on (measured; sources in t1 /home/kobii/missions/t1-campaign)
- Frontier 1156/1797 (C 1098 + CXX 58). There are 641 unresolved: **NO_COMPILE 443 + COMPILES_NO_MATCH 198** (`evidence/ascension/s16/w0_reconciliation.md`). The route dimension is MODEL:nocompile 413, MODEL:near 185, FIXED_POINT 15, SHARED 14, OPERATOR_SEARCH 13.
- **Shared types were already attacked (S1, t1 6d7cbf82).** It built one struct per source global and swept 106 dependents: 15 NO_COMPILE functions began to compile, with 0 lapses. A struct-only generation is therefore NOT a new lever. Correction: the coordinator said otherwise on 2026-11-07 before reading this.
- **Compiling is not the hardest step.** S8 made 73 functions compile, and deterministic search plus the model closed 0/27 of them. S14's closeout names the compile-to-exact shape as the dominant bottleneck: INSERT_DELETE instruction count plus mwcc register allocation, with no single cause above 60%.
- **There is no per-error census of the 443.** No artifact records which mwcc error stops each NO_COMPILE function. S16 route B pointed at struct/extern declarations from 11 callers only.
- About 10 functions are at >=99.7%, held by the SDA policy row. The Owner's NO stands, so they are out of scope.
- What works today, cheaply: the hotpath (deterministic families plus the wb_cxx operators). It runs at 0.63 s and USD 0 per eligible function (S14).

## 3. Phases
- **W0, census (no model, real compiler).**
  - For every one of the 641, record the first mwcc error class (NO_COMPILE) or the residual class (COMPILES_NO_MATCH: insert/delete, regalloc, reloc, other).
  - Record the shared root where one exists (global, struct, extern, prototype).
  - Gate: classes sum to 641, with UNKNOWN counted. **K1: if UNKNOWN > 20%, STOP.** The instrument is blind, and nothing downstream can be ranked.
- **W1, shared fixes for the top classes.**
  - Take classes in descending size, at most 4.
  - For each: one shared fix (a header with declarations, externs or prototypes, or one operator) applied to every member, then judged by cert_cxx.
  - Freeze each class's cohort, and keep a 20% hidden split before the fix is written.
  - **K2: a class with 0 certified, hidden included, is retired; move to the next one.**
- **W2, model pilot on COMPILES_NO_MATCH (lease-capped).**
  - 20 functions, chosen from the most frequent residual class, prompted with that residual's context.
  - **K3: 0/20 certified ends model spend for S17** (S8 precedent: 0/27).
  - If the pilot is >=2/20, scale to the class within the USD cap.
- **W3, fold and sweep.** Winning fixes and operators go into the hotpath, and the hotpath sweeps all 641 at USD 0.
- **W4, closeout.**
  - Frontier recount from receipts.
  - Yield: certified per 1M tokens and per USD, by phase.
  - Promotions to the coordinator. No research items beyond the census.

## 4. Invariants (unchanged from the programme)
- cert_cxx byte-exact contract unchanged.
- SDA NO stands.
- H2 stays sealed and unspent: it is excluded from W0-W3 cohorts by the manifest (sha 922f214e).
- No push. The worker never edits the PP.

## 5. Budget and limits (Owner sets; defaults proposed)
- 40M processed tokens, 0 top-ups.
- Model cap **USD 20** through the spend lease; spent only after K3 passes.
- 12 cycles / 24 h.
- Stop rule: after W1, if the yield is < 1 certified per 10M tokens, close at the checkpoint and do not continue to W2.

## 6. Honest expectation
Unknown, and two precedents point against a large jump: S1 (shared types: 15 compiled) and S8 (73 compiled, 0 exact). What is new here is that S17 measures where all 641 stop before choosing a fix, and judges every phase by yield. If W0 shows no class above about 30 functions, S17 should close early. That result would itself mean that no single generation can resolve "many" functions with these tools.

## 7. Owner decisions needed
1. Approve, edit or reject this plan.
2. Token authority, and the USD cap for the W2 model pilot.
On approval: write the S17 section into gen3 ASCENSION-PLAN.md plus S17-PHASES.md, then `arm --no-launch --milestone-from <gen3>/S17-PHASES.md`, then the authority on your owner turn. The sweep launches it.
