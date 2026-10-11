# ROOT-CAUSE-C2B (WU-W1)

Run C2b = ONE GEX44 job, 50 units. Result: 0 usable units.

## Mechanism (two independent defects, both visible locally before the send)
1. Custody: the job carried capsule `cap1-ba8a3cfe2822` but no `CURRENT_CAPSULE.json` existed. `custody.judge_receipt`
   fails closed (STALE_INPUT, "no CURRENT_CAPSULE to compare ... against"). The remote receipt was PASS, 549/549 files
   verified, so the spend produced a perfectly good receipt that the judge could never accept.
2. Sources: all 50 units were raw m2c output (unresolved `?` types, `unk*` fields) and the CXX family was compiled with
   `-lang c`. All 50 compiles: rc=1 "Errors caused tool to abort." Only the last 2 KB of stderr was kept, so the first
   (diagnostic) errors were discarded and the receipt showed only the summary line.
3. Misclassification: candidate.py wrote miss_class "environment" for ANY custody verdict, so one shared refusal
   was booked as 50 environment misses (it looks like noise, not a rule to fix).

## Why it was detected after the effect
The only check of CURRENT_CAPSULE lived in the judge, which runs on the returned receipt. Nothing at send time compared
the job's capsule to CURRENT, and nothing at build_units time asked "can this text compile at all".

## The three missing preconditions
- P1 send: CURRENT_CAPSULE.json must name the job's capsule id and manifest sha256 (stage.send -> CAPSULE_NOT_CURRENT,
  exit 16, before any spend). Invariant chosen: CURRENT == X at send time (the judge already compares against CURRENT,
  so a job not matching CURRENT can only come back STALE_INPUT).
- P2 source lint: build_units refuses (SOURCE_LINT) unresolved `?` type, `->unkNN`/`.unkNN` access, CXX with `-lang c`.
  Comments and strings are stripped first, so `a ? b : c` and `// ?` are not rejected.
- P3 diagnosability: stderr/stdout kept as 2 KB head + elision marker + 2 KB tail; custody verdicts get their own
  miss classes (custody_no_current, custody_capsule_mismatch, custody_invalid) instead of "environment".

## Cost
1 GEX44 job (one slot), 50 compiles, worker tokens per C2b-receipt.md; 0 candidates; plus the misleading
"environment" class that hid the cause.

## Evidence
gex44/test_fanout_preconditions.py (24 gates). Mutation drill: see the WU-W1 receipt.
