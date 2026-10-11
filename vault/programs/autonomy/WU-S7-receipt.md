# S7 receipt
Status: DONE

Slice done; remainder in continuation unit S7b (inserted in chain.json after S7; S8 now follows S7b).

- PROVEN: tools/autonomy_gates.py has 8 invariant V-gates (duration, goal count, history, capability, test estate, observability, wait, control) plus a spend-agreement gate; missing input is INCONCLUSIVE, never PASS. tools/test_autonomy_gates.py 25/25, each gate has a red branch and a mutation drill (gates neutered -> all red states pass through).
- PROVEN: reflex coverage counter REFLEX_COVERAGE=8/8 (linger-kill, steward, reapers, chain refusals, breaker-halt continuation, NO_WORK, manual re-arm->chain, manual landing->land_worktree), as evidence-file existence per class; drops to 0 when evidence is absent.
- PROVEN: programme_status prints settled 15439389 equal to `mission_spend goal-status --goal autonomy-convergence` (the UNKNOWN no longer reproduces); the gate that compares both exists (unit level). programme_status now shows interactive spend apart (test_programme_status 18/18).
- NOT_PROVEN: gates wired to live state (S7b step 1); release->readmit reflex; breaker-halt chain test; interactive charge at ledger level; compiled patterns recorded only as coverage rows.
- Calls used: about 14.

Next unit must know: see WU-S7b.md steps 1-5.
