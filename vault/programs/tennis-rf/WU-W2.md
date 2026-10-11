# WU-W2 -- Fan-Out Readiness Certificate (zero GEX44 jobs)

Common brief: `PROGRAMME.md`. Plan section 5 (W2). Needs W1 DONE.

Goal: one shared precondition is proven ONCE per job, and the send refuses without it, so no batch of children
discovers a shared failure after the effect.
1. Read the existing job dir artefacts (`preflight.json`, `build_record.json`, `job_record.json`) and stage.py's send
   path. Extend `preflight.json` into a certificate (do not add a parallel file type): content hash over capsule id +
   manifest sha256, CURRENT pointer value, tool pins hashes, W1 source-lint result per unit, job key in live keys,
   binary identity (target DOL sha256), and the unit list hash.
2. stage.py send: refuse unless the certificate exists, verifies, and every hashed input still matches.
   Refusal code distinct from STALE_INPUT/INVALID_CUSTODY (e.g. `NOT_READY:<check>`).
3. RED first: certificate missing -> refuse; capsule touched after certify -> refuse (invalidation drill); one unit
   fails lint -> refuse whole job with that unit named; all good -> send proceeds (use the test host double, no SSH).
4. Kill switch env var; fail CLOSED on its own error for send (this is a pre-effect gate on a scarce resource).
5. Replay the C2b job dir through it: must refuse, naming CURRENT_CAPSULE and the lint.
Receipt (write it to vault/programs/tennis-rf/WU-W2-receipt.md, Status line per PROGRAMME.md step 3; the chain reads only that file): tests, drill, replay output, commits.

## CPX amendment (B0, 2026-10-11)
- Step: port trim: runner_lib.py:1472 shutil.copyfile -> trim_objdiff_report (PP patch 147115b0).
- Certificate check: output budget: sum(.o + trimmed diff) + log ceiling <= 20,971,520 else NOT_READY:OUT_BUDGET.

