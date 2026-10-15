# WU-D12c receipt -- Status: DONE_WITH_LIMITS (test_d12c.py exit 0, 10/10; stop-loss fired at step 3 of 10)

Evidence: `evidence/d28/d12c/` (step1.json, split.json, joint_arm.json, summary.json, run.log, d12c.py, joint_delta.py, test_d12c.py). GEX44 CPU, no model, job 4 unused, no capsule edit. Command: `KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python d12c.py <out>`.

## Step 1 reproduction (d5.run_set + D7 dirty closure)
- B1 = H801C7770+H801C9670+H801C83F4: unlock **12** (12 targets, closure ran on 1449 fns), 0 errors. Matches D12a.
- L = hdr_e74_v1.h alone: **0** newly lint-clean over closure + 91 C0004 dependents. Matches D12b. Selector re-run reproduces the D12a top-10 order (438 candidates).

## Step 2 split
P = closure(B1) union 91 dependents minus the 12 targets = 91 fns; seed 20261015 -> 45 pack / 46 held-out, disjoint, written (split.json) before any composition. Helper prototypes are derived from asm admission with callsites from pack-half fns only; they are identical to the full-callsite prototypes (0 differences), so no held-out evidence entered a fact. No new field width was written.

## Step 3 per-bundle table (cumulative; universe 1449 fns)
| step | added | cum vars | unlock B | unlock L | unlock B+L | complementarity | B1 targets | pack | held-out | other | hidden blockers | new lint codes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | B1 + L | 3 | 12 | 0 | 12 | 0 | 12 | 0 | 0 | 0 | none | UNRESOLVED_TYPE x2 (fn_8024DE84, fn_80279FCC; regressions are from L, B alone has 0) |
| 1 | rank4 (801C3480, 801C6030) | 5 | 12 | 0 | 12 | 0 | 12 | 0 | 0 | 0 | none | same 2 |
| 2 | rank5 (+801C34D0) | 6 | 12 | 0 | 12 | 0 | 12 | 0 | 0 | 0 | none | same 2 |
Stop-loss fired after step 2 (B1+L plus next 2 bundles: held-out 0, no hidden blocker). 7 further bundles (up to 10) not run. complementarity = unlock(B+L) - unlock(B) - unlock(L) = 12-12-0 = **0** at every step.

## Step 4 curve (held-out only, STRUCTURE not cost)
(vars resolved, held-out fns lint-clean): (3,0) (5,0) (6,0). Slope 0, so no fns-per-var rate and no Wilson interval is stated. D12a's closure curve is in-sample (e.g. 12 fns at 3 vars) and is not matched by any held-out value.

## Step 5 controls
- No-op: byte-identical on 30 clean fns, unlock 0.
- Matched null (size-3 helper set 800B4508+801DB24C+80263CA8, closes no target set) plus L: unlock 0 (= L alone, 0).
- L with u32 instead of u8 at +0xA4C: unlock 12 (B1 targets) vs 12 right width, held-out 0 vs 0: wrong width does not raise lint-clean. Note this control is weak: L's own effect is already 0, so it cannot discriminate widths.

## Answer
Does a joint bundle transfer to held-out lint-clean? **No: 0 of 46 held-out (0 of 45 pack) newly lint-clean at 3, 5 and 6 resolved vars; complementarity 0.** B1's 12 are its own targets (in-sample by construction) and L adds 0 and 2 new UNRESOLVED_TYPE regressions.

## Limits
Only 3 of 10 steps run (stop-loss as written). Each unlock fact depends on the targets; P members were not targets of any helper bundle, so the held-out test is "do unrelated fns get cleaned", which the closure shows they do not. MODEL_NEEDED not invoked.

## Plan delta
MDG joint prototype+field bundle: held-out lint-clean transfer 0/46, complementarity 0; helper unlock stays target-local (12 at 3 vars), layout unlock 0. The shared-residual route has no measured held-out gain in lint-clean; vars only (D12b, 5.0%).