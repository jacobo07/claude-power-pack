# WU-D4 -- Ph4 uncertainty frontier, dominators, failure causal graph (GEX44 cpu)

Common brief: `D28-BRIEF.md`. Plan Ph4 and section 4 "frontier", MDG 10, 11, 14, 15. Inputs: D3 residuals.jsonl,
P1P2 facts.jsonl (call / access / type edges), D2 near_match.json.

Steps:
1. Frontier: group residuals by unresolved variable -> `frontier.json` {var, blocked_direct, blocked_transitive
   [low, high], resolution_cost class}. Transitive via the call/access edges in facts.jsonl (a callee's unresolved
   type blocks its callers' clean compile only when the signature uses it: state the rule).
2. Semantic dominators: dominator score = blocked fns (direct + transitive range) / resolution cost. Potential energy
   reported as [low, high], never a point. Top 30 ranked with their evidence rows.
3. Failure causal graph: rows in ONE JSON (`causal.json`), not a graph engine: failure class (from W10c/W12 verdicts,
   D2 near-match classes, lint codes) -> root cause var or rule -> functions. Counterexample compression: classes
   whose functions all share one root cause.
4. Red control: shuffle the var->function mapping; the top-30 dominator scores must fall (report both).
5. `test_d4.py` (V-D4-*): every frontier var traces to residual rows; ranges have low <= high; red control falls;
   reproduces on rerun.
Done-check: test_d4 exit 0; top 30 dominators in the receipt; evidence to PP `evidence/d28/d4/`.
Receipt: `WU-D4-receipt.md`.
