# S26E plan: compounding self-evolution for certification -- PROPOSED 2026-11-11, needs Owner approval

Status: APPROVED (Owner "apruebo ambos", 2026-11-11, session e31c61e1): (1) S26E at 9M / 0 fresh / USD 0, armed after
S26D CHECKPOINT_COMPLETE; (2) E0 (read-only reloc oracle) may run BEFORE S26D D1. Was PROPOSED at 3949788a. Author: pane e31c61e1 (recon research). Owner ask (2026-11-11):
"una capa fortisima de autoevolucion que cada vez sea mas fuerte y eficiente y efectiva" + "llevalo mas alla".
Not a new system (HR-NOVELTY-001): it completes S26 (`S26-PLAN.md`: method escape, independent oracle, held-out,
negative knowledge, baseline ratchet) with the parts that make it COMPOUND. It does not edit S26D, which is approved
(Owner y 16:35Z) and armed by the GEX44 watcher with its own phase mirror (d0690344).

## 1. Reality (facts in hand, 2026-11-11)
| fact | state | source |
|---|---|---|
| KSR certified 8,687 historical + 582 G-NT1 (S26C, profile ksr-v5r-s25stage), 0 overlap | PROVEN | S26D-PLAN.md, ef377bd3 |
| Of the 582, only 25 pilot fns had a per-fn structural check; 557 rest on replay sha == sweep sha + size | PROVEN | S26D-PLAN.md caveat |
| CERTIFIED = objdiff match_percent == 100.0 + replay sha == sweep sha (self vs self) + A2 negative control; no relocation-target comparison in certify.py | OBSERVED | t1 7a560498 certify.py, cv1.py:222-237 |
| Pinned objdiff-cli 3.8.1 (sha c8290281e821) treats relocs as equal on `symbol_name_addend_matches \|\| address_eq` (#381); a reloc to a DIFFERENT symbol at the same address scores 100. Issue #393 OPEN, no fix in release notes 3.8.1-3.8.3 | SOURCE-CONFIRMED, not reproduced on KSR | github encounter/objdiff#393, releases |
| Failure modes already measured: selector overfit 5/5 -> 1/4 (S24); per-fn edit method exhausted 0-1/53-65 (S17); S26B 15.8M spent, 0 evaluated; global `?` rewrite broke 178 matched fns; LLM edit ~0.09 certs per M tokens | PROVEN | S24/S17/S26B records, G10/G24 prompts |
| NO_COMPILE collapses to 7 type classes (~5,968 fns) repeating per TU | OBSERVED | s25/nocompile/clusters.json |
| Research corpus: recon-research.jsonl 135 rows, all HYPOTHESIS, none executed on KSR; Codex route works (G07) | OBSERVED | research/RESUMPTION_FILE.md |
| DRX deep_research has an evidence ledger + checkpoint/resume (PP 1c68ddd8..0de91ea6) | OBSERVED | git log |

## 1b. E0 findings (measured 2026-11-11 ~17:20-17:40Z on GEX44, pinned toolchain objdiff-cli 3.8.1)
The blind spot is WIDER than #393 and NARROWER in practice than feared:
| mutant (target vs candidate, fn `f`) | objdiff match_percent |
|---|---|
| same source (control) | 100 |
| defined `int a=1` vs defined `int b=2` (different name AND value) | **100** |
| defined `int a=1` vs `int a=2` (same name, different value) | **100** |
| string literal "abc" vs "xyz" | **100** |
| float literal 2.5f vs 3.5f | **100** |
| undefined extern `a` vs `b` | 96.7 (caught) |
| call `g()` vs `h()` (extern) | 95 (caught) |
| target extern float vs candidate inline literal | 95 (caught) |
| target extern vs candidate other extern | 97.5 (caught) |
match_percent covers the function's .text; a datum DEFINED in the object is compared by address only, never by name or bytes.
Exposure census over all 9,269 certified (8,687 ksr-v5r + 582 s25stage), from the TARGET objects: 3,944 have no relocation; 1,207 reference
data only as named externs (caught by name); 10 reference a symbol defined in their own target object -- all 10 are address-taken SAME-TU
FUNCTIONS (`fn_*`), not data; 0 reference literals. Why: KSR targets are dtk `*_text.o` splits, so data lives in other objects.
The 10 were rebuilt with their receipt sha and every relocation names the same symbol with the same addend.
Gate: t1 `tools/test_s26e_e0.py` S26E_E0_PASS (4 blind mutants scored 100 by objdiff and refused by the oracle, 5th extern mutant refused,
4 positive controls, byte-blind drill misses 2 value mutants, a real cert rebuilt sha-exact and CONSISTENT over 6 relocs).
Oracle: t1 `modules/recon_fabric/reloc_oracle.py`. Full sweep (rebuild + sha + oracle, all 9,269): `tools/s26e_e0_sweep.py` ->
`evidence/ascension/s26e/e0/`. RESULT (18:18Z, 79.4 s, 8 threads, nice 10; t1 2ae98cc5): **9,269/9,269 CONSISTENT** (8,687
ksr-v5r + 582 s25stage), 0 contradictions, 0 UNKNOWN (every object rebuilt with its receipt replay sha). oracle sha 2a3e6f48, results sha
81c640db. E0 DONE. S26D D1 keeps its own scope (declarations), not relocations. Consequence for E4: these 4 blind classes are the first pinned mutants; they become live risk the day a
stage puts data in the same object as code (G14 full-object matching), so the oracle must sit in certify.decide BEFORE that happens.

## 2. Design: four levels, each with its own ratchet
The system improves at four levels. Each level has ONE receipt-backed measure, an independent judge, and a ratchet
that only moves the baseline up. No level judges itself.

| level | what evolves | measure (receipts only) | judge | ratchet |
|---|---|---|---|---|
| L0 functions | certificates | certified set (receipt ids) | certify.py + E0 reloc oracle | set only grows; a contradiction is reported, revocation is an Owner act |
| L1 methods | operators, type rules, repairs, method cards | new certs on held-out per method, regressions on certified set | E5 promotion gate | promoted only with held-out delta > 0, 0 regressions, replicated on a 2nd cohort |
| L2 sources | where candidates come from (typelift, search, LLM edit, Codex/ChatGPT gaps, DRX) | certs per M tokens per source, on held-out | E1 ledger (never the source's own report) | budget follows yield (E3) |
| L3 the judge | the set of fake-match classes the certifier refuses | mutants killed | E4 mutant suite | suite only grows; a judge change that kills fewer mutants is refused |

L3 is what "cada vez mas fuerte" means. Every new way a 100% can lie (#393 is the first) becomes a permanent
mutant, so the system becomes harder to fool with each cycle. L2 is what "mas eficiente" means: tokens move to
whatever source certifies, and exhausted sources lose budget without anyone deciding it. L1 is what "mas efectiva"
means: only methods that transfer are kept.

## 3. Workstreams (each gated, each can close early)
E0 Relocation-target oracle (soundness, first). Read-only, no model calls in the check itself.
   Rule per relocation in the function: same type, same addend, same offset, and EITHER the same target symbol name
   OR both targets are anonymous compiler literals (`@N`, `...data.0`, pool labels) whose target bytes are identical.
   This keeps #381's literal case and refuses #393's case.
   Gates: positive control = the 25 S26C pilot fns pass; mutant = retarget one reloc to a different symbol at the same
   address -> REFUSED (it must fail without the oracle and pass with it); fixture where objdiff says 100 and the oracle
   refuses. Then apply to all 9,269 certificates (8,687 + 582). Output: contradiction list with evidence, never
   auto-revoked. Hand the result to S26D D1 if it has not run yet. Cap 1.5M.
E1 Yield ledger. Every new receipt carries `origin` = {source, method_card_id, gap_id/prompt sha, tokens attributed,
   cohort}. Historical receipts are backfilled ONLY where the origin is recorded; otherwise `origin: UNKNOWN`,
   never guessed. Measures: certs per M tokens per source on held-out; cost per cert per cycle. Cap 1M.
E2 Research bridge. recon-research.jsonl rows (E3 grade + a `test`) and DRX evidence-ledger claims become
   hypotheses with a discriminator, a positive control and a negative control, run through the unchanged certify
   path. The result is written back to the row: CONFIRMED / REFUTED / INCONCLUSIVE + receipt ids + fns moved.
   First three: G07 TU type inference (already S26 typelift: link, do not rebuild), G05-011 (#393 -> E0),
   G03-013 FLAGS_SPLIT vs incomplete extern arrays. Cap 2M.
E3 Allocator. Each cycle's budget is split by posterior yield per source (Thompson sampling over E1 counts),
   with a 15% exploration floor and a per-source cap of 50%. Retirement: a source with 0 held-out certs for
   3 cycles drops to the floor and opens a method-escape review (S26 section 4 A) instead of more spend.
   The allocator reads E1 only; a source cannot report its own yield. Cap 0.5M.
E4 Judge ratchet. Mutant suite pinned by receipt: #393 retarget, alias rename (family rule
   alias-needs-byte-evidence), declaration-only override (G23 class), size-only extent. A certify.py or objdiff
   change is accepted only if it kills every pinned mutant and re-judges a frozen sample identically. objdiff stays
   pinned at 3.8.1 until that gate passes for a newer version. Cap 1M.
E5 Promotion and transfer. A method enters the lane only with: held-out delta > 0, 0 regressions on the certified
   set (the 178 lesson), and replication on a second cohort (another KSR sport TU set, or Tennis after S27).
   Otherwise it is a local rule with its scope recorded. Negative results are kept with a reopen condition. Cap 1.5M.
E6 Efficiency ratchet. Rolling cost per certificate must not rise two cycles in a row; if it does, the cycle is
   flagged and E3 shrinks the offending source. Before any scheduler or ordering work, measure exhaustion (family
   rule measure-exhaustion-before-reordering): a search that exhausts its move set triggers vocabulary growth
   (G15/G17/G26 operators), not more budget. Cap 0.5M.
E7 Generator evolution. Research prompts are scored by E2 outcomes: prompts whose rows get CONFIRMED become
   templates; every refuted premise (e.g. `m2c --struct` does not exist) becomes a precondition in the next prompt.
   E3 picks the next research batch by expected certs, not by gap number. Cap 1M.

Total <= 9M processed, 0 fresh, USD 0 for E0-E7. Codex/ChatGPT research runs are a separate Owner go.

## 4. Sequencing
One writer per goal: S26E arms after S26D reaches CHECKPOINT_COMPLETE. Exception requested below: E0 is read-only
and protects certificates already counted, so it is worth running before S26D D1.

## 5. Done gates (all must pass; each a test_s26e_* script with a red mutant)
- E0: pilot 25/25 pass, #393 mutant refused, contradiction list over 9,269 receipts with counts derived from receipts.
- E1: every receipt written in S26E has `origin`; UNKNOWN count reported, never 0 by omission.
- E2: >= 3 research rows executed and written back, each with its receipt ids.
- E3: allocation for cycle n+1 reproducible from the E1 ledger alone.
- E4: mutant suite >= 4 classes, all killed by the current judge, pinned by sha.
- E5: no method counted without held-out + second-cohort receipts.
- E6/E7: cost-per-cert series and prompt scores derived from receipts.
- Gates pin receipts, never a frontier count (family rule pin-receipts-not-counts).

## 6. Not authorised
Revoking any certificate; merging counters; push; upgrading objdiff; editing ~/.codex/config.toml; any paid call.

## 7. Owner decisions
1. Approve S26E at 9M processed / 0 fresh / USD 0, armed after S26D's checkpoint?
2. Allow E0 (read-only reloc oracle) to run BEFORE S26D D1, so the 557 are checked first?
