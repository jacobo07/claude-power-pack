# S27 Tennis: open the residual 599 with methods that are not the exhausted ones -- APPROVED, NOT ARMED

Approved: Owner "y" 2026-11-11T16:14:16.399Z (laptop session d957c937, uuid 3427a3a4) to the proposal
"prepare S27 Tennis for ddf4990e to launch when S26C closes; ~15M processed, 0 fresh, USD 0".
Arming belongs to the sole Ascension coordinator (pane ddf4990e), AFTER S26C reaches CHECKPOINT_COMPLETE.
One writer per goal: never arm while m-077596a9935d holds an active worker on gen3.

## Facts it rests on (re-derive in T0; do not trust)
- Tennis 1,797; unique certified 1,198 (C 1,139 + CXX-only 58 + 1); C-lane residual 164 COMPILES_NO_MATCH + 494 NO_COMPILE
  (658, includes ~59 functions holding a CXX certificate) -> ~599 uncertified (S25_W0_PASS, s25/w0_account.md).
- CNM 164: S24 transfer 0/164 = 55 never fired + 109 fired-and-failed; S25 W5 split of the 55 by deciding line:
  PATH_NEVER_REACHED 43, OPERATOR_CANNOT_EXPRESS 12, SELECTOR_TOO_STRICT 0. S23 B search arms 0 certs; S18 W5 >=95% re-pass 0/30.
- NO_COMPILE (S25 clusters.json, n_tennis 515 incl. `?`): NOT_STRUCT 101, ILLEGAL_OPERANDS void*+int 35, UNDEFINED_IDENT 33,
  POINTER_EXPECTED:long 23, ILLEGAL_OPERANDS void*+long 11, IMPLICIT_CONVERSION void*->long 6, UNKNOWN_TYPE_DECL:? 1, rest unclassified.
- KSR-only evidence (does NOT transfer by default): typelift (S26) ~20% COMPILES-or-exact, ~2% exact; `?` repair 253/336 compile, 87 exact;
  NOT_STRUCT 0 in 3 KSR cohorts for every method; void*+int belongs to the S17 handler.
- Blocker of record: S25 q_summary "Tennis `?` fns UNMEASURED: needs a Tennis-target judge".

## Authority (proposed new mission record)
<= 15M processed (13.5M work + 1.5M closeout), 0 fresh, USD 0, 8 cycles, 16 h, no push. Same NOT-authorised list as S26
(pinned stages, receipts, frontiers, certify.py / cert_cxx.py rules, canonical ctx and headers, H2/R2, push, paid).
A Tennis certificate counts ONLY if produced by the unchanged Tennis certifier on the canonical context. A candidate that is
exact only under a changed declaration/context is reported OVERRIDE-style, uncertified, and goes to the Owner.

## Phases packet (copy to gen3 vault/programs/gsdx-factory-2/S27-PHASES.md; lines start "Phase N:")
Phase 1: T0 Reality and cohorts (cap 2M): re-derive the Tennis residual by function identity (C receipts U CXX receipts, overlaps by id) and classify every uncertified fn by state and first-error class from real compiler text; locate the Tennis judge path actually used by the certified C lane (file:line) and record whether a source candidate can be judged on the Tennis target today; freeze dev and held-out cohorts per lever (seed drawn after the freeze commit); gate tools/test_s27_t0.py (mutants: double-counted overlap, cohort overlap, held-out read before freeze)
Phase 2: T1 Tennis judge for variant candidates (cap 3M): the smallest extension that judges a typelift / `?`-repaired source on the Tennis target through the existing compile + objdiff path; positive control = a certified Tennis fn re-judged byte-identical; negative control = swapped inference must not be exact; a judge that cannot see its positive control = INSTRUMENT_FAIL and Phases 3 and 5 stop; gate tools/test_s27_judge.py
Phase 3: T2 Transfer typelift + `?` to Tennis NO_COMPILE (cap 3M): run the S26 transform at its frozen sha with method_card_v2 routing on dev, then held-out; pre-registered: report COMPILES and BINARY_EXACT separately per class, exclude any class where the swap control is exact from exact claims, certified-fn bytes in the same units unchanged; every exact goes to the UNCHANGED Tennis certifier; certified ones are the Product Delta, the rest stay uncertified with their first blocking condition; gate tools/test_s27_transfer.py
Phase 4: T3 Route the 43 PATH_NEVER_REACHED (cap 2M): read the deciding code line from S25 W5, make the smallest routing change that lets the existing operators reach them (additive, old behaviour byte-identical for every other fn), freeze the 43, run the EXISTING search unchanged, certify through the unchanged certifier; the 12 OPERATOR_CANNOT_EXPRESS are recorded as grammar gaps with the missing source form named, not searched; gate tools/test_s27_route.py (mutant: routing change alters another fn's path)
Phase 5: T4 Struct-layout recovery pilot for NOT_STRUCT (cap 3.5M): infer struct layouts from the constant offsets and access widths each base pointer receives across ALL functions of the unit (not per function), emit them as source declarations in an isolated variant; dev = Tennis NOT_STRUCT, held-out = a frozen KSR NOT_STRUCT sample (cross-title check); rivals: S1 layouts are unit-shared, S2 per-function, S3 the real blocker is something else (record the post-repair first error); controls as Phase 3; K3: 0 movement on dev = retire with negative row and reopen condition; gate tools/test_s27_struct.py
Phase 6: T5 Checkpoint (cap 1.5M incl. reserve): re-run all test_s27_* + S26 x6 + S25 x6 + S24X x2 + FRONTIER_CHECK + KSR_FRONTIER_CHECK + receipts shas and paste rc; frontier delta for Tennis by identity; negative rows with reopen conditions; UKDL candidates; the 109 fired-and-failed CNM are NOT attempted in S27 (deferred: highest cost per fn) and are listed with residual class; checkpoint_s27.md; gsd_mission.py checkpoint CHECKPOINT_COMPLETE

## Expected yield (not a promise)
Phase 3: tens of fns NO_COMPILE -> COMPILES, a few exact, at KSR rates if they transfer (unmeasured). Phase 4: unknown; cheap.
Phase 5: unknown; largest ceiling (101 Tennis + ~670 KSR NOT_STRUCT). 0 is an honest outcome for any phase.

## Arming recipe (for ddf4990e)
gen3: archive the S26C milestone, add S27-PHASES.md (from the packet above) + this plan; `gsd_mission.py arm --no-launch --cwd gen3
--milestone-from S27-PHASES.md --add-dir t1 --add-dir recon-general --max-cycles 8 --max-hours 16`; then
`authority --tokens 15M --owner-turn d957c937-f56d-4447-9386-5d8002fe0b90:2026-11-11T16:14:16.399Z` (copy the d957c937
transcript to GEX44 ~/.claude/projects/laptop-coordinator-d957c937/ first so the turn verifies); verify worker_acked + reads.
