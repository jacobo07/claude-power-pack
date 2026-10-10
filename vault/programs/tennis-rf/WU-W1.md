# WU-W1 -- Root fixes for the C2b failure class (zero GEX44 jobs)

Common brief: `vault/programs/tennis-rf/PROGRAMME.md`. Plan sections 1, 3. Iterate after step 2 (root cause written).

Facts already measured (do not re-derive; verify each with one read):
- C2b = ONE job, 50 units. Judge verdict STALE_INPUT, reason `no CURRENT_CAPSULE to compare capsule cap1-ba8a3cfe2822
  against` (custody.py judge_receipt, `current_capsule` missing). candidate.py:485-487 writes miss_class "environment"
  for ANY custody verdict.
- Remote receipt PASS, 549/549 files verified, but all 50 compiles rc=1 "Errors caused tool to abort.": every source is
  raw m2c with unresolved `?` types and `unk*` fields; family CXX compiled with `-lang c`; only the last stderr line kept.

Steps:
1. Find where CURRENT_CAPSULE is read by the judge and written by capsule build/stage (grep `CURRENT_CAPSULE`,
   `current_capsule`). Decide the invariant: a send for capsule X requires CURRENT == X at send time, OR the job record
   pins the capsule and the judge compares against the pinned id. Pick the one the existing tests already imply.
2. Write `vault/programs/tennis-rf/ROOT-CAUSE-C2B.md` (<= 40 lines): mechanism, why it was detected after the effect,
   the three missing preconditions, cost of the failure (1 job, worker tokens from C2b-receipt.md).
3. RED tests first (a new `gex44/test_fanout_preconditions.py`, gate-style like the existing tests):
   a. replay the real C2b job record: the send path refuses BEFORE any job is created;
   b. source lint rejects all 5 C2b sources (unresolved `?` type, `unk` field access, CXX family with `-lang c`) and
      accepts a clean fixture; red control: a near-miss (`?` inside a comment/string) is NOT rejected;
   c. miss_class for custody verdicts names the custody reason class instead of "environment";
   d. stderr kept as bounded head+tail (e.g. 2 KB each) in the receipt.
4. Implement the minimum to turn them green. Re-run the existing suites you touched (test_candidate, test_custody,
   test_arm_a, test_reproduce) -- they must stay green; report any pre-existing red by name.
5. The `.ksr_vault` snapshot gate: reproduce its refusal in wt_tennis_rf with an empty commit attempt on a scratch file,
   read the hook, name why a fresh worktree drifts. Fix it if it is a defect of the gate (with a test); otherwise write
   a certified copy route (hash before/after) and document it. Never --no-verify.
6. Mutation drill: break each new guard once in an isolated copy, each must go RED.
Receipt: tests and drill results, commits (or patch files), the invariant chosen, the gate outcome.
