# WU-D2 receipt
Status: DONE
Done-check: `python evidence/d28/d2/tools/test_d2.py` -> TEST_D2 OK, exit 0 (19 checks V-D2-*). Evidence in PP `evidence/d28/d2/`.

## Results
1. **Causality** (`causality.json`, 22 rows, 35 header tags): per judged function, tags / tag.fields / prelude types / externs /
   prototypes found in its m2c-with-ctx source. 13 of 35 tags are used by none of the 22 (they were written for the two
   EXCLUDED draws or for callee-only structure).
2. **Near-match** (`near_match.json`, from the interrupted predecessor, red control passed, positive control passed): 9 PARTIAL ->
   5 primary classes, **compression ratio 5/9 = 0.556**. Classes: FLAG/CODEGEN x4 (802128D4, 80241018 bool idiom;
   80253348, 8032CF78 sda21 vs @ha/@l), SIZE_-1 x2 (8022621C, 80278FEC), POINTER_STRIDE x1 (8021F8BC), PTMF_R12 x1
   (8021F3E4), REGALLOC x1 (80254440). The "6 SIZE +-1-2" prior is not confirmed: only 2 are pure SIZE; 4 size
   differences are a symptom of a FLAG/CODEGEN idiom.
3. **80252F34** (`admission_gap.md`): missing item = `NULL` (header has none, flags `-nodefaults`, diagnostic "undefined
   identifier"). Lint checks types only. Rule `UNDECLARED_MACRO` written and tested (`tools/admission_rule.py`); the fix
   prediction (`#define NULL`) is UNMEASURED (no job).
4. **Knowledge-shock attribution 175 -> 276** (`shock_attribution.json`, `shock_residual.json`; m2c+lint, no compile, 20 cores;
   rerun of the 101 newly-clean functions reproduced 101/101 with the full header, prelude-only header 0/101):
   - alone-critical: 9 functions (8 distinct tags, each 1; Ptmf8021F3E4 also shares one); conjunctive (>=2 tags needed): 7 functions; **redundant
     (no single tag flips them): 85**. 9+7+85 = 101 reconciles exactly.
   - The 85: dropping every struct (prototypes/externs kept) leaves **85/85 clean**; dropping every prototype (structs kept)
     leaves **0/85 clean**. So ~84% of the shock comes from untagged prototype/extern lines of the header, not from struct tags; all
     16 functions that depend on tags are in the 24 W5a/W12 draws.
   - Ranking: Ptmf8021F3E4 1.5 credit; Obj80203E40, Obj8020711C, Obj8020CC14, Obj8021F8BC, Obj80230BF8, Obj80241018,
     Obj80279E44, Obj8032CF78 1.0 each; then shared tags 0.5 .. 0.11 (Elem80230ABC, Obj802128D4, ... Tab80253348);
     remaining 4 tags 0.
   - Red control: dropping 5 random non-header struct names changes 0 functions (header text identical: weak by construction;
     the stronger controls are prelude-only = 0 clean and the 9 single-tag flips all being the tag's own function).
   - Not re-tested: the 175 clean without header (knowledge_shock newly_dirty = []).

## Plan delta
MDG 6 (causality) = 22 rows done; MDG 7 (near-match root causes) = 5 classes / 9 PARTIAL = 0.556; MDG 8 (shock attribution)
= 16 tag-dependent + 85 prototype-dependent of 101, residual 0. Implication: the knowledge lever is the prototype/extern table, not
struct tags -- cheap to extend by script, no per-function model work.

## Commands
GEX44 (M/out/d28/d2): `KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python tools/d2_run.py <out> tools/records.jsonl --jobs 20`
then `d2_resid.py <out> records.jsonl`. Near-match: `tools/near_match.py` (predecessor). No model calls on functions.