# WU-D12c -- joint helper-prototype + field-layout bundle, propagated by D7, measured on held-out (GEX44 CPU, no model on fns, no job)

Common brief: `D28-BRIEF.md`. Plan: `vault/plans/d12-factory-scaling-2026-10-13.md`. Owner, 2026-10-15: "1" (arm the next
abstraction D12b names: a joint prototype+field bundle propagated by D7 and composed with one layout fact).
Inputs: `evidence/d28/d12/` (joint_delta.json, struct_clusters.json, residuals_v1.jsonl, hypergraph.json, tools/),
`evidence/d28/d12b/` (hdr_e74_v1.h, split_lbl_80513E74.json, tools/pack.py arm2.py ladder.py), `evidence/d28/d5/`
(d5.run_set, d5.asm_admits), `evidence/d28/d7/` (dirty.py closure). Read the D12a and D12b receipts first.

Why: D12a top HELPER bundles unlock 11-12 fns at 2-3 vars (H801C7770+H801C9670, +H801C83F4) but on their own target sets
(in-sample by construction). D12b: one layout fact (C0004) moves held-out vars -5% and lint-clean 0. Untested: whether the
two compose, and whether either transfers to fns that were not chosen as targets.

Steps (deterministic; GEX44 CPU; laptop light only):
1. **Reproduce.** Bundle B1 = H801C7770+H801C9670+H801C83F4 alone (expect unlock 12) and layout L = hdr_e74_v1.h alone
   (expect 0 newly lint-clean), both via d5.run_set + D7 dirty closure. A mismatch stops the unit: record and end.
2. **Held-out split.** Population P = D7 dirty closure of B1 union the 91 C0004 dependents, minus B1's 12 targets. Seeded
   split (seed 20261015) into pack/held-out, disjoint, written before any fact is composed. Any new fact (prototype or
   field width) may be written from pack-half evidence only.
3. **Joint arm.** Apply B1 + L together, then the next helper bundles from joint_delta.json by EBU (selector reads var
   sets only; no degree field) until 10 bundles or stop-loss. Per step record: vars resolved (cumulative), newly
   lint-clean in pack / held-out / B1 targets, hidden blockers revealed, new lint codes, and
   complementarity = unlock(B+L) - unlock(B) - unlock(L).
4. **Curve.** Fns lint-clean vs vars resolved for the joint arm, held-out only, next to D12a's closure curve. Label it
   STRUCTURE, not cost. If the held-out slope is > 0, state it as fns per resolved var with a Wilson interval.
5. Controls: no-op (byte-identical); a size- and degree-matched bundle that closes no target set (unlock 0); L applied
   with a wrong width at +0xA4C (must not raise lint-clean).
Stop-loss: if B1+L and the next 2 bundles give held-out newly lint-clean 0 AND reveal no hidden blocker, stop and record.

6. `test_d12c.py`: reproduce numbers of step 1; split disjoint and seeded; selector greps no degree field; controls behave;
   every composed fact cites pack-half evidence only.

Limits: no model calls on functions, no GEX44 job (job 4 stays unused), no capsule edit. A step that cannot be done
deterministically is recorded as MODEL_NEEDED with the reason, never guessed.
Done-check: `test_d12c.py` exit 0; evidence in `evidence/d28/d12c/` committed (pathspec).
Receipt: `WU-D12c-receipt.md` (Status DONE / DONE_WITH_LIMITS / PARTIAL; include the step-1 reproduction, the per-bundle table
in-sample vs held-out, complementarity, the held-out curve, and one sentence: does a joint bundle transfer to held-out
lint-clean, yes/no, with numbers).
