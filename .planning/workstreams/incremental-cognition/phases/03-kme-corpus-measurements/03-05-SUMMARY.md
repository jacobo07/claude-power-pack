---
phase: 03-kme-corpus-measurements
plan: 05
subsystem: kme-measurement-instrument
tags: [IC-D, IC-E, IC-F, IC-G, IC-H, IC-I, r3, done-gate, owner-bundle, evidence, gex44, pillars-open]
requires: ["03-04"]
provides:
  - "tools/test_incremental_cognition_program.py: front_matter_fields, check_measurement_scope (R3, role-aware), `--pillar <P>` branch printing ICP_PILLAR_<P>=PASS|FAIL, R3 in --final; selftest poles V-ICP-R3-* and V-ICP-MUT-terminal-evidence-false"
  - "wiki/tools/kme_pillars.py: build_parser() (the parser main() uses)"
  - "tools/test_kme_pillars.py: V-KMEP-R3-E-PAIR, V-KMEP-BUNDLE-ARGV-PARSES (83 gates total)"
  - "vault/programs/incremental-cognition/owner-bundle.md: Phase 3 header + **[D]** **[E]** **[F]** **[G]** **[H]** **[I]** (append-only)"
  - "vault/programs/incremental-cognition/evidence/phase3.md: smoke table, proofs, Product Delta, Intelligence Delta, debts, Status: OPEN"
affects: []
tech-stack:
  added: []
  patterns: ["done-gate guard in the program-owned wrapper only (CE verifier untouched)", "line-anchored front-matter read so quoted words in a body are not fields", "bundle commands proven by parsing them with the shipped parser, with a found-count positive control", "cherry-pick list replayed in a scratch clone before it is written down"]
key-files:
  created: [vault/programs/incremental-cognition/evidence/phase3.md]
  modified: [tools/test_incremental_cognition_program.py, tools/test_kme_pillars.py, wiki/tools/kme_pillars.py, vault/programs/incremental-cognition/owner-bundle.md]
decisions:
  - "[Phase 3]: [03-05] R3 is in the program-owned wrapper only: a kme_pillars measurement supports a terminal only as a primary file with terminal_evidence true; a second_workload file only when second_workload_valid is true AND the same pillar also cites such a primary; smoke never; a file naming another pillar never; a file with neither evidence_role nor terminal_evidence is another instrument's and is skipped; an unknown evidence_role string is refused"
  - "[Phase 3]: [03-05] second workloads accepted for E (orchestrator advisory 2): the program accepts any instrument-written file with evidence_role second_workload and second_workload_valid true beside a terminal KME-L primary -- CPP-D-W7 at coverage >= 1 (named in the bundle), a KME-G run with an exact population, or a named OTHER workload (valid by construction, no population to reproduce). Reason: the frozen rule says 'a second workload' without naming one and the claim stays in the KME-L primary; KME-G can never stand in for KME-L because R3 refuses a second workload with no terminal primary. Independence is argued at close time in evidence/E.md (named debt)"
  - "[Phase 3]: [03-05] the bundle cherry-pick list is the fourteen phase-3 code commits (not 'four'), preceded conditionally by the FROZEN_AT pointer commit d4d35059 (V-KMEP-FREEZE-INSTANT reads that file); replayed in a scratch clone from 18e928af: clean picks, KMEP_PASS=82/82, ICP_SELFTEST=PASS"
  - "[Phase 3]: [03-05] the population proof in the bundle is UNFILTERED over the whole projects root first (KME is classified by content and the P0 dir list was never recorded); --project-filter is only an optional speed-up accepted if the population stays exact"
  - "[Phase 3]: [03-05] item [I] follows the frozen rule's own words (CE B / SC A-C) for the handoff and names the CE B and SC B terminals that R2 needs"
status: complete
commits: 4
plan_head_before: 0d7ca7a95b92f52f5c82d005b283a6d628511e14
actuals:
  tokens: 11861
  tasks: 3
  commits: 4
metrics:
  completed: 2026-10-03
requirements: [IC-D, IC-E, IC-F, IC-G, IC-H, IC-I]
requirements-completed: []
---

# Phase 3 Plan 05: R3 measurement-scope guard, [D]-[I] laptop bundle lines, phase3 evidence Summary

The program done-gate now reads each cited kme_pillars file's `evidence_role` and `terminal_evidence`, so "never substitute KME-G for KME-L" cannot pass `--pillar` or `--final`; the owner bundle carries one laptop line per pillar D..I with commands proven to parse with the instrument's own parser; `evidence/phase3.md` records the phase with `Status: OPEN`. **IC-D..IC-I are addressed, not satisfied**: ledger `state.D..I` are all `{}`, nothing was ticked, `requirements.mark-complete` was not called.

**Commits:** `754d19c9` (Task 1, R3 + selftest poles + V-KMEP-R3-E-PAIR), `333adc90` (parser entry point `build_parser()`), `3d8752f0` (Task 2, bundle lines + V-KMEP-BUNDLE-ARGV-PARSES), `7492d2c0` (Task 3, phase3.md; carries the plan's final subject).

## Observed results

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=83/83  threshold=83/83  skipped=0  inconclusive=0` (81 at the start; +`V-KMEP-R3-E-PAIR`, +`V-KMEP-BUNDLE-ARGV-PARSES`). Real-corpus gates PASS: `V-KMEP-KMEG-FROZEN-REAL`, `V-KMEP-AUDIT-BYTE-IDENTICAL-REAL` (`sessions=177 files=6 differing=[]`), `V-KMEP-KMEG-AUTO-REAL` (exact, `exact_at_freeze`, scans 1/1).
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL 78/78`, twenty `KILLED`, `PASS DRILL-CLEAN-AFTER-MUTANTS 78/78`, `DRILL killed=20/20` (unchanged: the two new gates are outside the drill set; they were driven red by hand, below).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`, with `ok   V-ICP-R3-CLEAN`, `-REAL`, `-SMOKE-REFUSED`, `-E-PAIR-ACCEPTED`, `-SECOND-ALONE-REFUSED`, `-SECOND-INVALID-REFUSED`, `-SECOND-WITH-FALSE-PRIMARY-REFUSED`, `-WRONG-PILLAR-REFUSED`, `-NON-KMEP`, `-QUOTED-NOT-FIELD` and `V-ICP-MUT-terminal-evidence-false killed by R3`. `V-ICP-REAL-OWNER-READ` still prints `INCONCLUSIVE` (commits fa9ae2ed / 21671d6c are absent from this clone); pre-existing, does not fail the selftest.
- `--pillar D|E|F|G|H|I` -> each prints `  FAIL L3 <P>: no terminal disposition`, `CEP_PILLAR_<P>=FAIL`, `ICP_PILLAR_<P>=FAIL`, exit 1 (state is open). `--status` output is byte-identical before and after (`diff /tmp/ic-p3-05-status.before /tmp/ic-p3-05-status.after` empty). `--final` -> `ICP_VERDICT=FAIL failures=1` (CE clauses fail on the open pillars, as before).
- Regression: `PFP_PASS=28/28`, `BREAKER_PASS=18/18`. `git diff --stat -- tools/test_cognitive_economy_program.py` empty. `grep -c '^- \*\*\[[DEFGHI]\]\*\*'` on the bundle = 6; `git diff HEAD` lines removed from the bundle = 0 (append-only); `NOT RUNNABLE HERE` count 1. Ledger `state.D..I` all `{}` (`True`); `[x] **IC-[D-I]**` count 0.
- Phase3.md: three headings (Product Delta, Intelligence Delta, Status: OPEN), each of `[D]`..`[I]` named, 14 artifact sha256 rows equal `ce.lf_sha256` at HEAD, re-checked after the commit (no drift).

## RED outputs

- Task 1 RED (guard absent): `FAIL V-KMEP-R3-E-PAIR AttributeError: module 'test_incremental_cognition_program' has no attribute 'check_measurement_scope'` (after the instrument's three real E files were produced), `KMEP_PASS=81/82`; wrapper selftest poles written first: `NameError: name 'check_measurement_scope' is not defined`.
- Task 2 RED (no bundle lines): `FAIL V-KMEP-BUNDLE-ARGV-PARSES 0 commands parsed (>= 7), unparsable=[] missing_items=['D', 'E', 'F', 'G', 'H', 'I'] ... D-W7(d)=False E-second_workload=False first_population_unfiltered_expand=False`, `KMEP_PASS=82/83`.
- Gate strength (by hand, uncommitted): driving R3 with the smoke refusal removed turned `V-ICP-R3-SMOKE-REFUSED` and `V-ICP-R3-REAL` red; removing the orphan-second-workload refusal turned `-SECOND-ALONE-REFUSED` and `-SECOND-WITH-FALSE-PRIMARY-REFUSED` red. The bundle gate went red for a misspelt flag, a `--expand`-less first `population`, a `--project-filter` on the first `population`, a missing `[F]` item, a missing `--role second_workload`, and an empty bundle; the clean bundle PASSed with 11 commands.

## Cherry-pick proof (scratch clone, deleted)

`git clone` of this worktree, `18e928af` checked out detached, `d4d35059` (FROZEN_AT pointer) then the fourteen listed commits picked in order: all applied cleanly, `tools/test_kme_pillars.py` -> `KMEP_PASS=82/82`, `ICP_SELFTEST=PASS`. Without `d4d35059` the same replay read `KMEP_PASS=81/82` (`V-KMEP-FREEZE-INSTANT` reads `FROZEN_AT`), which is why the bundle carries the conditional first pick.

## Deviations from Plan

**1. [Plan wording] `build_parser` was already factored.** `main()` built its parser in `_build_parser()`; the change is a rename to `build_parser()` in its own commit `333adc90` (no behaviour change; the suite stayed green), so the bundle commit can cite it.

**2. [Plan wording] Four commits, not one, and fourteen picks, not "four".** Per the executor's commit-early protocol each task committed when green, and the refactor is its own commit so its sha can appear in the bundle (a commit cannot list its own sha). The phase-3 code is spread over thirteen earlier commits plus `333adc90`; the bundle lists all fourteen in order. The commits that only add the bundle text, its gate and the evidence file are declared not needed on the laptop.

**3. [Rule 2 - correctness] Conditional FROZEN_AT pick.** Found by the scratch replay (see above); added to the bundle's Expects paragraph with its full sha.

**4. [Rule 2 - correctness] R3 refuses an unknown `evidence_role`** (not in the plan's list); a role-bearing file with no `pillar` field is not refused (the plan names only a pillar field that names another pillar).

**5. [Design] Second workloads.** Orchestrator advisory 2 applied: see Decisions and phase3.md "Plane and denominator". The program accepts CPP-D-W7, a KME-G run and a named OTHER workload as second workloads when the instrument marks them valid and a terminal KME-L primary exists; independence is a close-time argument.

**6. [Plan wording] Item [I] handoff target.** The plan says "CE B / SC B"; the frozen rule says "CE B / SC A-C". The bundle uses the rule's words for the handoff and names the CE B and SC B terminals for R2 (what `ledger.frozen.consumes.I` lists).

**7. [Design] Two verdict lines for `--pillar`.** The wrapper runs `ce.main(argv)` first, so `--pillar P` prints CE's `CEP_PILLAR_P=` and then R3's `FAIL R3 ...` lines and `ICP_PILLAR_P=`.

**8. [Attribution]** Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the attribution in force in this session's system reminder), not the Opus 5.5 line named in the dispatch; same choice as 03-01..03-04.

**9. [Process]** The agent-branch-namespace pre-commit check was not applied: sequential run on the dispatched `mission/incremental-cognition-run` branch; HEAD was never on a protected branch. `vault/progress.md`, the workstream `config.json`/`milestone.lock` and the hook-generated `docs/*/*kme_pillars*` files were left alone.

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None new. R3 only reads files through `ce.Resolver().file_text`; the bundle adds documentation; no ledger, CE/SC file, env tree or `~/.claude/` path was written.

## Debts

- Six KME-L runs pending in the owner bundle (laptop plane); no pillar D..I has a terminal. D also needs the CPP-D-W7 file; E its second workload when the primary says so.
- P0's KME-L project-dir list was never recorded: the bundle's population proof starts unfiltered and may need the roots settled from its `per_project` rows.
- D-W7 parser difference (CE dedupes across files keeping the last copy; this instrument per file with max-merge): coverage >= 1 does not prove the same call set.
- G precision is a hand sample only (empty on KME-G); H's R2 needs CE P and G terminals on this history; I's R2 needs CE B and SC B terminals.
- R3 cannot judge the independence of a second workload: `evidence/E.md` must argue it (KME-G or a named OTHER workload is weaker than CPP-D-W7).
- `V-KMEP-R3-E-PAIR` and `V-KMEP-BUNDLE-ARGV-PARSES` are not in the mutation drill set (driven red by hand only).

## Self-Check: PASSED

Verified after writing: `check_measurement_scope` and `front_matter_fields` defined in tools/test_incremental_cognition_program.py; `V-KMEP-R3-E-PAIR` and `V-KMEP-BUNDLE-ARGV-PARSES` present in tools/test_kme_pillars.py; `build_parser` in wiki/tools/kme_pillars.py; owner-bundle.md and evidence/phase3.md present; commits 754d19c9, 333adc90, 3d8752f0, 7492d2c0 in the log; `git rev-list --count 0d7ca7a9..HEAD` = 4 (matches `commits: 4`); `git show --stat 7492d2c0` lists only phase3.md; CE verifier diff empty; ledger `state.D..I` empty.
