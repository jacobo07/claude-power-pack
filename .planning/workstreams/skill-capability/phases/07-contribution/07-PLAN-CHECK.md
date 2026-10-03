# Phase 7 plan check (07-01, 07-02)

Verified on gex44 (python3), by grep, git and an independent Fraction/comb recomputation:
- Rows: 8 rows. Stored grade PASS only for P-r1. C rows have card_rows ["unknown"]. All transcripts start with C:\Users\User. Regrade file: 6 rows, no C row, P-r1 regraded FAIL-SWALLOW-REPAIRED.
- Commits: 713b02a7 added both files, and its body has "reflog-aware grader". Its subject has "6/6 swallow". The p3_delivery.py blob at 713b02a7 contains FAIL-SWALLOW-REPAIRED (3 hits). 123c96cc is an ancestor of HEAD, and its subject is as quoted in the plan.
- Text sources: audit line 19 and residency plan lines 92-93 are verbatim. The audit "2/2 PASS" is on line 21 and is bold. p3_runner.py lines 29-32 hold the Windows constants. The p3_delivery.py docstring is on line 6.
- Fisher pins: all exact (1/35, 1/126, 1/21, 1/6, 1/3, 1, 1/21, and 21/646 for 10/10 vs 5/10).
- Bound: equal-allocation floors are None x3, then 1, then 4/5. The all-allocation floor is 3/4. Floors for budgets 2..10 are monotone. needed_k(1/2) = 10.
- Ledger: the state.E line is at line 103. FROZEN_AT is 217d72b5. D-CARD.arm_c and new_benchmark_cap are as cited. The E owners exist. D and H are already terminal (from the concurrent 04-04 work), which the plan tolerates.
- CE: `_check_evidence(pid, e, res, owners, denoms)`, `Resolver()`, `lf_sha256`, the DEFERRAL_PROSE regex and the `CEP_PILLAR_<X>=PASS` print all exist. The skill-capability file rebinds `ce`.
- Session phrasings: the three regexes match the three plan-time lines. The traceability rows exist.
- SC-E is covered by both plans. depends_on is valid (07-02 depends on 07-01). Scope is 3 and 2 tasks.

## Issues
1. WARNING (07-01 T3; dependency on phases 5, 6, 8 and 9): the measurement goes stale whenever a later phase writes a summary.
2. WARNING (07-01 T2/T3): the drills do not declare the full set of clauses each one breaks.
3. WARNING (07-01 T3): a git failure is not stated to give INCONCLUSIVE for the AUTH clauses.
4. WARNING (07-01): the gate reads text sources from the working tree, not from committed files.
5. WARNING (07-02 T2; 07-01 T3): `p=1/3` is not in the --json output, so it would be typed by hand.
6. INFO (07-01 T2): the mutant with grade "" must target a row that has no regrade row.
VERDICT: ISSUES FOUND
