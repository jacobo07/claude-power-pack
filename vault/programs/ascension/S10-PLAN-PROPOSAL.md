# Wave S10: C++ certification lane (`-lang c++`), bounded (PROPOSAL, 2026-11-02)

Owner decisions, 2026-11-02 (verbatim intent):
1. YES to a separate `-lang c++` certification lane and a bounded S10. NO relaxing the definition of exact.
2. NO: a pooled literal is not the same as a labelled SDA constant at another address. SDA_RELOCATION stays 0/4.
3. YES, only to the isolated S9-8 canary on GEX44.

Goal: show that the C++ lane reproduces the original binary faithfully, not that it gets a PASS by changing the judge.

On approval, this text goes into `gen3-pp/.../ASCENSION-PLAN.md` as the S10 section. Until then nothing is armed.

## Facts this plan rests on (measured)

- The current certificate (`cv1.judge`, t1) is: compiles with rc 0, the symbol is defined, and objdiff `match_percent == 100` under `cv1.FLAGS` (`... -lang c -O4,p`). It runs no separate check of code bytes, relocations or referenced data.
- S9 B3: 3 functions are LANE_EXACT under `-lang c++` with every other flag unchanged: fn_80222ED8, fn_80222480, fn_80256314. Two more are near misses: fn_802262F0 at 99.64 and fn_80226454 at 99.53.
- 139 uncertified targets carry the r12 vptr idiom (`r12_idiom_targets.json`), and 14 of them are in H (closeout). So 125 are candidates outside H.
- B4 already spent H once: frozen `vcall-virtual@1` applied to 0 of 14.
- S9 used 11.13M tokens in 3 epochs (record `cost_mark`) and $0 of model spend. The campaign has spent $331.03 of its $471.10 authority, leaving $140.07.

## Certification contract `cert-cxx@1` (stricter than the C lane, never weaker)

A function is CERTIFIED_CXX only if ALL of the following hold, checked by a verifier that does not import the lane tool:

1. **Pinned lane manifest:** the sha256 of `mwcceppc.exe`, `wibo`, `objdiff-cli` and `tennis_context.h` matches. The flags are `cv1.FLAGS` with exactly one token changed, `-lang c` → `-lang c++`. Any other difference refuses.
2. Compiles with rc 0, the symbol is defined, and the source declares the function `extern "C"`, so the symbol name is unchanged.
3. objdiff `match_percent == 100` (the existing contract).
4. The code bytes equal the target's after masking only the bit fields that relocations cover.
5. The relocation list is equal by (offset, type, addend), and each relocation resolves to the same target symbol or the same data.
6. Every symbol the function references that is defined in our object (vtables, literal pools, sdata) is byte-identical to the target's, or is an undefined external in both. Otherwise the result is DATA_MISMATCH. This is the rule that refuses a pooled literal standing in for a labelled constant, in both lanes.
7. Two independent rebuilds in clean directories produce the same object sha256.
8. If the same source also passes the C lane, the function is CERTIFIED_C, not CXX. A function is never counted in both lanes.

Certificates are kept apart: `evidence/ascension/s10/certs_cxx.jsonl`. The frontier reports CERTIFIED_C, CERTIFIED_CXX, LANE_CANDIDATE and UNCERTIFIED as separate counts.

**Provenance is not certification.** A C++ certificate says "this C++ source and this pinned toolchain reproduce these bytes". A separate field, `language_provenance`, carries independent evidence graded E1-E3: vtable data layout, neighbouring functions in the same TU, and constructor/destructor patterns. r12 alone is never evidence (Owner).

## Units and micro-commits (one commit per unit; gen3 status line after each)

| Unit | Repo | Content | Gate (DONE = observed) |
|---|---|---|---|
| S10-0 | gen3 | S10 section in ASCENSION-PLAN.md, Owner approval recorded | the plan commit exists |
| S10-1 | t1 | `modules/recon_fabric/cert_cxx.py`: lane manifest + checks 1-8 | V-CXX-* gates (below) green |
| S10-2 | t1 | Controls and mutation drill for the certifier | all controls behave as specified; every mutant killed |
| S10-3 | t1 | Independent revalidation of the 3 LANE_EXACT functions (fresh process, clean dirs, verifier only) | each one CERTIFIED_CXX or a named refusal |
| S10-4 | t1 | `language_provenance` classifier over the 125 (no tuning on H) | per-function grade written; r12-only = E0 |
| S10-5a..e | t1 | Batches of 25 over the 125: the deterministic operator first, then a model rewrite only for a shape the operator does not match | per batch: certs, refusals by check, $ |
| S10-6 | t1 | H one-shot: the frozen method at that point, run once over the 14, no reading of H sources before the run | result recorded, never tuned on |
| S10-7 | gen3 | Closeout: separate counts, maturity rescore under the rubric (never edited), checkpoint verb | master gate run, checkpoint declared |

V-CXX gates (S10-1/2):
- **POSITIVE-C:** 20 functions sampled from the 1,086 CERTIFIED_C, re-judged by checks 1-7 in `-lang c` mode, must pass. If any fails, the strict comparator has found something about existing C certificates. It is REPORTED, not applied to S9 or older results (Owner: no retroactive change).
- **NEGATIVE:**
  - the 2 near misses (99.64, 99.53) refuse;
  - a single-instruction mutant refuses;
  - a relocation-target swap refuses;
  - a flag-drift mutant (`-O4,s`) refuses;
  - a wrong toolchain hash refuses;
  - a pooled-literal variant of one SDA function refuses with DATA_MISMATCH.
- **MUTATION DRILL:** each of these certifier mutants must be killed by at least one control:
  - skip relocation compare;
  - skip data check;
  - accept pct ≥ 99;
  - skip the manifest;
  - skip the second rebuild.
- **S9-IMMUTABLE:** the sha256 of every `evidence/ascension/s9/*` file is pinned before S10-1 and re-checked at every gate.

## Kill gates (any one stops the lane; the closeout says which)

- **K1:** a control or mutant behaves wrongly → no certificate is issued in S10.
- **K2:** independent revalidation refuses any of the 3 → stop after S10-3, report the refusing check.
- **K3:** two consecutive batches with 0 new CERTIFIED_CXX → stop the batches, go to S10-6.
- **K4:** spend:
  - tokens over the authority;
  - model USD over the cap;
  - more than $8 per certified function (the Gen4 rule);
  - `--budget-usd` ≤ 10 per llm_fix batch, through the spend lease.
- **K5:** any write to S9 evidence, or any read of H before S10-6 → stop, reported as contamination.
- **K6:** a certificate that fails a re-run of checks 1-7 at closeout → the lane is not trusted and the wave closes.

## Budget (proposed)

- **Tokens:** 40M authority plus one 15M top-up, max 12 cycles, 36 h. Basis: S9 ran ~3.7M per epoch, and S10 has about 9 epochs.
- **Model:** a 20 USD cap through the lease, from the $140.07 remaining.
- Waiting consumes zero execution budget (HR-MISSION-WAIT-ZERO-EXECUTION-001).

## Stop rule

If S10-3 certifies 0 of 3, or S10-5 and S10-6 together add ≤ 1 CERTIFIED_CXX, then METHOD_PIVOT_REQUIRED with the exact residual, and the programme closes (the Owner's pilot rule, carried over from S9).

## Out of scope

- SDA_RELOCATION equivalence: refused. Researching layout or compiler decisions is allowed only if a match then passes this contract unchanged.
- Changing `cv1.FLAGS` or any existing certificate.
- Using H for tuning.

## Arming (after approval)

Run `arm-chain --no-launch` in gen3-pp, with a Workset of gen3 + t1 + PP. Then `mission_topup.py budget` (40M). The sweep launches it. Never hold a mission whose worker could die.
