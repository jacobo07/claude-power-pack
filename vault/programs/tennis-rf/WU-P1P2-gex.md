# WU-P1P2 (GEX44 plane) -- whole-program extraction + semantic factorization of Tennis (zero model on functions)

Binding plan: `M/trf/../` is a copy; canonical = PP `vault/plans/tennis-rf-compounding-MASTER-PLAN-2026-10-12.md` rev 2,
sections 2 (amendments A1-A8) and 4 (Pass 1, Pass 2). This file is the whole brief you need.
You are ONE headless worker with a hard turn limit. No Agent/Task spawns, no GSD commands, no Monitor, no sleeps.
You write code that analyses the binary. You do NOT reason about individual functions' semantics, write candidate
source, compile with mwcc, or send any job. Every number you report comes from a script you ran, with the command.

## Layout (M = /home/kobii/missions/tennis-w11)
- asm: `M/wst_tennis/step0/split_sports/out/asm` (560 files, all 1,797 Tennis functions; W7 parsed it).
- inventory: `M/wst_tennis/w3/tennis_fns.json`; W7: `M/trf/measure/families.json`, `M/trf/measure/features.json`,
  method `M/trf/evidence/w7/families.py` (copy it, never edit it).
- context header (35 cited structs + prelude): `M/wt/tools/wros/binary/decomp/gex44/tennis_context.h`;
  m2c + lint the way W11/W12-prep ran them: `M/out/tools/dumpasm_linux.py`, `M/out/tools/lint_w11.py`; lint rules
  `M/wt/tools/wros/binary/decomp/gex44/source_lint.py` (now with MISSING_PRELUDE / UNDECLARED_TYPE).
- tools: `export KSR_DECOMP_TOOLS=/opt/ksr-decomp`; python `/opt/ksr-decomp/venv/bin/python`. 20 cores: parallelise
  m2c with a process pool.
- outputs: `M/out/p1p2/` only. Code in `M/out/p1p2/tools/`. Write each output as soon as it exists (a turn limit
  must leave partial results on disk, never nothing).

## Rules
- A1: a label is written only when a deterministic check proves it; otherwise `UNKNOWN`. UNKNOWN is never counted
  as singleton, zero or "unique".
- Every clustering or index gets a red control (permute the feature across functions; structure must collapse),
  exactly as W7 did. A result without its red control is INCONCLUSIVE.
- Structural similarity is not semantic equivalence: name things "structural family", "data family", never "same code".

## Pass 1 -- facts (output `facts.jsonl`, one row per function, 1,797 rows)
fn, addr, size_insns, role (A1: TAILCALL_THUNK = 1-2 insns ending in b; LEAF_ACCESSOR = <=4 insns, one load/store off
r3, blr; CTOR_SHAPE / DTOR_SHAPE only if the shape rule you write is proven on a red control; UNREACHABLE = no direct
caller AND not referenced from any data word in the DOL sections you can read; else UNKNOWN), callees, callers,
cfg_fingerprint (basic-block count, edge count, loop count, ordered block-size hash), field_accesses ([base_reg_origin,
offset, width, rw] where base is r3..r10 at entry or a load from one), globals (lbl_ refs), constants (immediates
>= 0x100 and float literals), helper_sig (callee arity from r3..r10 setup), idiom_hits (from the idiom table below),
m2c_with_ctx {status, n_unresolved_types, n_unk_fields, lint_codes}.
Idiom table v0 (each needs >=1 positive and >=1 negative asm example in `idioms_test.txt`): switch jump table
(bctr after lwzx), bool-from-compare (cntlzw; srwi 5), float->int (fctiwz; stfd; lwz), struct copy (lwz/stw pairs
over consecutive offsets >= 4 words), vtable call (lwz rX,0(r3); lwz rY,N(rX); mtctr; bctrl), ptmf call (r12 use
before bctrl), stack-guarded prologue (stwu r1,-N(r1); mflr r0). Report hits per idiom over the corpus.

## Knowledge Shock (A3) -- output `knowledge_shock.json`
m2c over all 1,797 WITHOUT the header (reuse W7's results if `features.json` has them; else rerun) and WITH the
current header. Report: lint-clean count before/after, functions newly clean, which of the 35 struct tags each newly
clean function references, and functions newly clean that are OUTSIDE the 24 W5a/W12 draws (the leverage beyond the
draw). Knowledge Leverage Ratio input: newly clean functions; the token side (W11 3.02M GEX44 + laptop sessions,
W12-prep 2.50M) is filled in by the coordinator.

## Pass 2 -- factorization (output `factor.json`, `blockers.json`, `hypotheses.json`)
1. Six-resolution index (A2) per function: exact_family (W7 id), structural_family (cfg_fingerprint + size bucket +
   callee arity profile), data_family (set of (struct tag or base-origin, offset) accessed; Jaccard >= 0.5 components),
   idiom_family (idiom_hits multiset), proof_family (UNKNOWN for all until verdicts exist: say so), motif ids (repeated
   basic-block sequences of >= 6 insns with normalised registers/immediates occurring in >= 3 functions).
2. Per function: residual novelty estimate = fraction of its insns NOT covered by any motif, idiom hit, or known-struct
   field access. Label it `residual_structural` (it is structural coverage, not semantic novelty).
3. Corpus summary: whole-function singletons (W7: 1,114) that belong to >= 1 non-singleton group at another resolution;
   distribution of residual_structural (deciles); counts per role incl. UNKNOWN.
4. Blocker index: every unresolved item (unk field offset per base object, `?` type, unknown helper) with the list and
   count of functions it blocks from lint-clean; ranked. Top 20 in the receipt.
5. Hypothesis store v0: for the top 10 blockers, the competing structural hypotheses the asm admits (e.g. field
   width/signedness from load ops, pointer vs scalar from later deref) and which single function would discriminate
   them best (most dependents, smallest size). Data only; no resolution.

## Gates (write `test_p1p2.py`, V-P1P2-* lines, exit 0 only if all pass)
facts rows == 1,797; every role != UNKNOWN has its proof rule recorded; each idiom has its positive and negative
example passing; red control collapses each new grouping (data_family, structural_family, motifs); knowledge shock
counts reproduce on a second run; m2c-with-ctx on the 22 W12 lint-clean ids is still CLEAN (no regression).

## Close
`M/out/p1p2/receipt.md`: line 1 `# P1P2 receipt`, line 2 `Status: DONE` or `Status: PARTIAL`, then PROVEN / NOT_PROVEN /
INCONCLUSIVE per claim, every number with its command, gate result line, and what is still UNKNOWN. Then `touch
M/out/p1p2/FINISHED`. Make the receipt the last write.
