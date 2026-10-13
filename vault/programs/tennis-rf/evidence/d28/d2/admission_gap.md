# 80252F34 admission gap (WU-D2 step 3)

**Verdict: the missing context item is `NULL`.** Evidence, all deterministic:
- Ledger rows (job ksrmb-20261012-171117, seq 45 O4p and 63 O2): `runner_status=COMPILE_FAILED`, `miss_class=context`,
  `evidence.diagnostic="undefined identifier"`, `rc=1`, `cpu_s` 0.01 (stopped at the first parse error), `status=BLOCKED_CONTEXT`.
- The m2c-with-ctx source (`main_80252F34.c`) uses `NULL` six times (`!= NULL`, `= NULL`). Flags carry `-nodefaults`: mwcc
  has no `NULL`. The header (`tennis_context.h`, copy here) contains 0 occurrences of `NULL`.
- Of the 22 judged outputs, 80252F34 is the only one that uses `NULL` (grep of out/w12/m2c/c/*.c) and the only
  COMPILE_FAILED. Not compiled again here (no job; jobs 5-6 unapproved), so "adding `#define NULL 0` fixes it" is a
  prediction, not a measurement.

## Why lint admitted it
`source_lint.lint_unit` has four checks: `?` as a type, `uncNN` fields, `-lang c` on CXX, and the two C1 checks
MISSING_PRELUDE (s8..f64 with no typedef) and UNDECLARED_TYPE (a capitalised *type* before `*`). Every one of them looks
at **types**. `NULL` is a value-position identifier and an ALL-CAPS macro, so no check sees it. Lint-clean therefore only
meant "no type is missing", and the W12-prep text "22 CLEAN" was read as "compiles". The same blind spot covers any
macro or global named in an m2c body (the header declares `lbl_` externs by hand, which is why those worked).

## The rule that would have refused it
`UNDECLARED_MACRO` (`tools/admission_rule.py`): an ALL-CAPS identifier (3+ chars) used in the unit with no `#define`, enum
constant or declaration in the unit. On the composed 80252F34 unit it returns
`UNDECLARED_MACRO: NULL used with no #define in the unit (-nodefaults provides none)`; on the header alone it returns [];
with `#define NULL 0` added it returns [] (near-miss accepted); a `NULL` inside a comment is ignored. Tests V-D2-RULE-*
in `tools/test_d2.py`. It is not wired into `source_lint.py` (outside this unit): wiring it is a one-line addition to
`lint_unit` plus adding `#define NULL ((void*)0)` (or `0`) to the header prelude, then re-send 80252F34 in a later job.
