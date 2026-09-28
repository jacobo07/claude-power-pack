# P3 ablation — addendum to the predeclared protocol (2026-09-28, before any counted run)

Protocol: `vault/plans/cognitive-resource-os-P3-ablation-protocol.md`. This file only fixes what the
protocol left open; it changes no threshold and no decision row.

- **Owner go**: run now on subscription quota (2026-09-28, weekly usage ~50% at the time).
- **Host / version**: laptop, claude 2.1.284. The GEX44 pre-flight (CRO-03) validated
  `--settings {"claudeMdExcludes": [...]}` statically on 2.1.283 with zero model calls; this run is the
  first runtime use, so it carries its own positive control (below).
- **Model**: `claude-opus-5-5` for both arms (the model the Owner's sessions run; the relocation decision
  is about that prefix). One task per fresh `claude -p` session, `--permission-mode acceptEdits`,
  tools Read/Edit/Write/Grep/Glob/Bash/PowerShell, `--max-turns 40`, 1500 s bound.
- **Tasks**: `p3-tasks.json`, 8 seeded mutants, frozen by the commit that adds this file. 3 are in R1's
  domain (T6 destructive guard, T7 measured population, T8 unknown-is-not-zero). `p3_runner.py validate`
  must print 8/8 (clean test green with PASS lines, mutant red) before `run`.
- **Grade**: the ORIGINAL test file is restored from BASE before grading, so an agent that edited the
  test cannot pass. task_pass = that test's exit 0.
- **A/A**: the two arm-A replicates per task are the noise floor the protocol's P1 asks for.
- **Positive control for arm B (runtime)**: R1 is ~92.9 KB of rules (~24k tokens est.). Arm B's
  `first_call_context` must be lower than arm A's on the same task by an amount of that order. If B is
  not lower, `claudeMdExcludes` did not apply and every B run is INVALID for the decision, whatever its
  pass result. Judged at analysis time from results.jsonl; reported beside the verdict.
- **Validity per run** (protocol): transcript MEASURED, entrypoint `sdk-cli`, grade printed PASS lines.
  Invalid -> replaced, max 2 replacements per run id, then STOP (instrument unreliable).
- **Order**: arms alternate A-first / B-first by task and replicate, so host drift lands on both.
