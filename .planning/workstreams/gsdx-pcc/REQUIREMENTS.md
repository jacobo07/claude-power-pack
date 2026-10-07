# Requirements -- gsdx-pcc

The requirement set IS `DENOMINATOR.md` (rows D01-D47 from the dataset, R01-R09 from the Reality Scan, plus the
mutation corpus). Each roadmap phase closes the rows whose `phase` column names it. A requirement is met only when
its row is DONE (or an allowed non-OPEN disposition) with evidence, and the final done-gate in `ROADMAP.md` passes.

Hard constraints (from the spec root function): proof strength never decreases; UNKNOWN escalates to FULL;
fresh-required evidence is never inherited; no optimisation may hide a failure the incumbent full path detects;
adapter authority ceiling PROBATION; no writes outside worktree `C:\Users\User\Apps\pp-gsdx-pcc` and pilot worktrees.
</content>
</invoke>
