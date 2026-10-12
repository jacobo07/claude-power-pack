# WU-D7 -- Ph7 incremental recompile (GEX44 cpu)

Common brief: `D28-BRIEF.md`. Plan Ph7 and section 4 "Incremental build", MDG 13. Inputs: D6 fact delta, P1P2
facts.jsonl edges, D3 residuals.

Steps:
1. `M/out/d28/tools/dirty.py`: fact id -> dependents (from facts.jsonl access/call/type edges and residual
   unresolved vars). Given a header delta, the dirty closure = functions whose residual or m2c input references a
   changed fact, transitively by the D4 rule.
2. Replay D6's delta incrementally: rerun m2c + lint only on the dirty closure. It must reproduce D6's whole-corpus
   lint-clean set exactly (diff empty). Report closure size vs 1,797 and wall time vs the whole-corpus run.
3. Direct vs transitive unlock split for D6's facts.
4. Negative control: a delta to a fact no function uses -> empty closure; a delta to a widely used struct -> its
   closure contains every function D6 saw change.
5. `test_d7.py` (V-D7-*): reproduction diff empty, both controls, closure deterministic across runs.
Done-check: test_d7 exit 0; evidence to PP `evidence/d28/d7/`.
Receipt: `WU-D7-receipt.md`.
