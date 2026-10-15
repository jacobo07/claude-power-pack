# WU-D9 receipt

Status: DONE (negative result; closed by the coordinator pane after the BLOCKED_HUMAN gate was cleared, 2026-10-14)

Gate: ADMITTED. fn_802128D4 (6/8 insns, bool idiom) and fn_8032CF78 (3 insns, sda21 vs @ha/@l) are PARTIAL, <=16 insns.

## Blocker cleared
The worker stopped at `SEND=CAP_REACHED`: `stage.py` still carried `TNS_PHASE_JOB_CAPS = {1: 4}` from the 2026-10-11
approval, while JOBS.md records the Owner's later approvals up to 7 (job 7 for D9 on admission). The cap was raised to
7 in wt_tennis_rf `tools/wros/binary/decomp/gex44/stage.py` to match that record; no job beyond the approved 7.

## Result (`evidence/d28/d9/synthesis.json`)
- Job 7 `ksrmb-20261014-164017` (build candidate-20261014T160717Z, CERTIFY READY c2e43d02...): 34 units, repatriated
  (tree 215bda9d...), judged. Donors 3/3 MATCH, so the job is valid.
- fn_802128D4: 24 variants at O4p, **0 MATCH**. Best `bool_var` / `bool_var_init1` objdiff 60.6, SIZE 7 vs 8. The
  other 22 variants collapse to 6 insns (objdiff 10-17): the compiler folds every comparison form the same way.
- fn_8032CF78: 7 variants, **0 MATCH**. 5 compile to 4 insns vs 3 (objdiff 46.7). The two `#pragma` sda variants
  failed to compile (BLOCKED_COMPILER), so the sda21 addressing hypothesis is untested, not refuted.
- Synthesis rate on this sample: 0/2 fns (31 variants), 0 model calls per variant.

## Plan delta
Ph9: deterministic source-variant synthesis does not close these two PARTIALs at O4p. 802128D4 needs a 7th->8th insn
cause beyond expression shape (candidates: O2/other preset, a stack temp). 8032CF78 needs a compilable sda21 path
(section attribute or `-sdata` flags, not pragma). O2 arm still unrun (dropped for OUT budget).
