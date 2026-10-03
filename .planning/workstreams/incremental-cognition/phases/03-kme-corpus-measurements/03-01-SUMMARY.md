---
phase: 03-kme-corpus-measurements
plan: 01
subsystem: kme-measurement-instrument
tags: [pillar-D, IC-D, kme, hook-rent, materiality, gex44, smoke, mutation-drill]
requires: ["02-04"]
provides:
  - "wiki/tools/kme_pillars.py: weighted, call_weighted, burden, burden_interval, resident_calls, counts_for_d, frozen_specs, compare_population, materiality, make_keep, PillarObserver, DObserver, scan, population, render_measurement, write_measurement, main (subcommand d; flags --denominator --label --select --host --root --expand --until --out-dir --frozen-file --role --json); exit 0 measured / 2 usage / 3 UNMEASURED"
  - "wiki/tools/kme_token_audit.py (additive): finish_session(s, host); scan_file/scan_project observer= and keep= (default None = P0 behaviour)"
  - "tools/test_kme_pillars.py: 24 V-KMEP-* gates plus --drill (6 mutants)"
  - "vault/programs/incremental-cognition/measurements/D-KME-G-2026-10-03.md (smoke, plane gex44, terminal_evidence false) and D-GEX44-B001-2026-10-03.md (named workload sample)"
affects: ["03-02", "03-03", "03-04", "03-05"]
tech-stack:
  added: []
  patterns: ["frozen parser imported with observer/keep hooks, never forked", "population reproduced field by field before any share is judged", "evidence_role (primary / second_workload / smoke) separate from terminal eligibility", "exclusive-create measurement files with -2/-3 suffixes", "full file text through secret_firewall.redact before the single write"]
key-files:
  created: [wiki/tools/kme_pillars.py, tools/test_kme_pillars.py, vault/programs/incremental-cognition/measurements/D-KME-G-2026-10-03.md, vault/programs/incremental-cognition/measurements/D-GEX44-B001-2026-10-03.md]
  modified: [wiki/tools/kme_token_audit.py]
decisions:
  - "--until defaults to the freeze instant for the frozen denominators (KME-L / KME-G) and to none for a named workload: the live corpora keep growing (an unwindowed GEX44 scan today already reads 14 active / 1,679 calls against the frozen 13 / 1,322), so reproducing the frozen population requires the window"
  - "terminal_evidence is true only for a primary file whose population is exact AND whose materiality is not UNMEASURED (stricter than the plan's 'only when the population reproduced': an unmeasured file never counts as a terminal)"
  - "a frozen denominator must use the frozen selection rule: --select all with KME-L / KME-G is refused (exit 2); --label is refused for a frozen denominator"
  - "mutation seams are module-level functions (resident_calls, counts_for_d, make_keep, compare_population, materiality, write_measurement) that main() resolves at call time, so a drill's monkeypatch reaches the CLI path"
status: complete
commits: 3
plan_head_before: e35c2753035ce3e4f8bd8dc53cf11907735b7f07
actuals:
  tokens: 21200
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-03
requirements: [IC-D]
requirements-completed: []
---

# Phase 3 Plan 01: kme_pillars instrument core and pillar D (hook rent) Summary

One CLI, `python3 wiki/tools/kme_pillars.py d --denominator <NAME> --root <dir> ...`, scans transcripts with the frozen instrument's own parser and writes one measurement markdown naming its denominator, plane and exact `command:`; pillar D is its first subcommand. **IC-D is addressed, not satisfied**: its terminal needs the laptop KME-L run (recorded for plan 03-05), ledger `state.D` is still `{}`.

**Code commits:** `4e0333f8` (tracer: audit hooks + core + D + 3 gates), `d1f67731` (21 expansion gates incl. the two real-corpus gates), `ac0e5f2e` (drill + the two committed measurement files). `git show --stat ac0e5f2e` lists tools/test_kme_pillars.py and the two files under measurements/ only.

## Observed results

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=24/24  threshold=24/24  skipped=0  inconclusive=0`, exit 0, 7.3 s (limit 60 s). Both `-REAL` gates PASS on GEX44: `V-KMEP-AUDIT-BYTE-IDENTICAL-REAL sessions=177 files=6 differing=[]` and `V-KMEP-KMEG-FROZEN-REAL` measured `{13 active, 151 dead, 1322 calls, input 2644, cache_write 6272100, cache_read 381540448, output 839734}` = the frozen KME-G entry exactly.
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL 22/22`, six `KILLED` lines (M1 materiality UNMEASURED->"< 3 %", M2 compare_population always exact, M3 D resident calls forced to 1, M4 D counts every hook type, M5 make_keep ignores until, M6 writer truncates), `PASS DRILL-CLEAN-AFTER-MUTANTS 22/22`, `DRILL killed=6/6`.
- Frozen pipeline regression: `kme_token_audit.py --host gex44 --expand ... a5 a7` exit 0.

## RED outputs

- Task 1 RED (before the module existed): `ModuleNotFoundError: No module named 'kme_pillars'` from `tools/test_kme_pillars.py`, exit 1.
- Task 2 RED: **not observed as a FAIL run.** The core written for Task 1 already contained the population check, verdict function, role logic, `make_keep` and the writer, so the 21 Task-2 gates passed on their first run. Their ability to go red is shown by the drill instead (six of them are killer gates for a mutant) and by the pole pairs inside the gates (D-POSITIVE has a 1-char control, UNTIL-CUTOFF runs with and without the cutoff, OTHER-LABEL runs refusals and an accepted label). Recorded as a deviation.

## Additive change to kme_token_audit.py

`git diff 18e928af -- wiki/tools/kme_token_audit.py` removes exactly these 8 lines, every other change is an added line:

```
-def scan_file(path, sess):
-def scan_project(pdir):
-                scan_file(full, s)
-            s['class'], s['kme_share'] = classify(s)
-            s['host'] = a.host
-            s['residency'] = sorted(s['residency'], key=lambda x: -x[4])[:40]
-            s['reads'] = {k: v for k, v in s['reads'].items() if v >= 2}
-            s['attach'] = {k: v for k, v in s['attach'].items()}
```

The five per-session lines moved verbatim into `finish_session(s, host)`. Default output is byte-identical to 18e928af on the synthetic fixture (audit, report and denominator files, `V-KMEP-AUDIT-BYTE-IDENTICAL`) and on a stat-pinned copy of the real a5/a7/b001 corpora.

## Smoke measurements (GEX44, read only)

- **D-KME-G-2026-10-03.md**: `plane: "gex44"`, `evidence_role: "smoke"`, `terminal_evidence: false` (reason names KME-L / CPP-D-W7), `population_match: "exact"` (13 / 151 / 1,322 / ... all deltas 0), command `... d --denominator KME-G --until 2026-10-03T16:13:37Z --expand --root a5 --root a7 --root b001 --root ~/.claude/projects`, exit 0. Numerator 1,105 `hook_additional_context` attachments, 740,326 chars (477 chars per tool use, 560 per call); share interval [2.64 %, 3.96 %] -> **STRADDLES**, `second_workload_required: true`, observability 1.0. 788 of the attachments are `PreToolUse:Bash`. `hook_success` (4,838, 2.59 M chars), `hook_system_message` (92) and `hook_blocking_error` (9) are listed beside the numerator, not in it.
- **Second workload** (required by that verdict): `D-GEX44-B001-2026-10-03.md`, `--denominator OTHER --label GEX44-B001 --select all --host gex44 --expand --root b001`, `denominator_kind: named_workload`, population not_frozen (10 active / 1 dead / 1,879 calls), share [0.0015 %, 0.0022 %] -> `< 3 %`. Role auto -> `smoke` (no primary file exists on GEX44 for it to confirm); it is a sample, not a confirmation, and the two workloads disagree by three orders of magnitude (b001 carries almost no hook context). The KME-L run decides pillar D; neither file is a terminal.
- **No-write proof:** `find ... -type f -printf '%p %s %T@\n' | sort` over the a5, a7 and b001 project trees before and after each smoke run (736 files each time): `diff` empty both times (`/tmp/ic-p3-01-snap.{before,after}`, `/tmp/ic-p3-01-snap2.{before,after}`). `~/.claude/projects` is excluded from the snapshot (live sessions append there); the instrument opens every transcript read-only and `V-KMEP-READ-ONLY` proves it on a chmod a-w tree.

## Checker advisory applied (orchestrator)

`V-KMEP-AUDIT-BYTE-IDENTICAL-REAL` copies the ~240 MB of a5/a7/b001 into `tempfile.TemporaryDirectory(dir=tempfile.gettempdir())` (removed on exit, independent of `$CLAUDE_JOB_DIR`); a free-disk guard (>= 300 MB) prints `SKIP`, never PASS; the copy is pinned by a (path, size, mtime_ns) snapshot of the originals before and after, one recopy, then `INCONCLUSIVE`. On this run the originals did not move and the gate PASSed.

## Deviations from Plan

**1. [Process] Task 2 had no observed RED run.** See "RED outputs"; the module core was built ahead of the Task-2 gates. Gate strength is shown by the drill and the paired poles instead.

**2. [Rule 1 - fixture] D-POSITIVE fixture inconsistent.** The first version put 4,000 chars of context before each of 10 calls with only 5,000 cache_read tokens each, giving a share above 100 %. Raised the fixture's cache_read to 100,000 per call; the share is now 21-32 % and still `>= 3 %`. Fixed before the Task 2 commit.

**3. [Rule 2 - correctness] terminal_evidence also requires a measured verdict** (see Decisions): a primary, exact-population file whose materiality is UNMEASURED is not terminal.

**4. [Process] Commits.** Three commits (one per task) instead of the plan's single Task-3 commit, per the executor's atomic-commit protocol; the Task-3 commit carries the plan's subject. The agent-branch-namespace pre-commit check was not applied: this is a sequential run on the dispatched `mission/incremental-cognition-run` branch; the protected-branch check was (HEAD never on main/master/develop/trunk/release).

**5. [Attribution]** Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the attribution in force in this session's system reminder), not the Opus 5.5 line named in the dispatch.

## Auth gates

None.

## Known Stubs

None. (The `OBSERVERS` / `PILLAR_HELP` registries hold only D by design: plans 03-02..03-04 register E..I.)

## Threat Flags

None. The tool reads transcripts and writes only markdown under the measurements directory.

## Debts / notes for the owner bundle

- The KME-L laptop command for D (to be recorded in plan 03-05): `python wiki/tools/kme_pillars.py d --denominator KME-L --expand --root <laptop projects roots>` (default `--until` is the freeze instant; the population must match the frozen KME-L entry exactly or the verdict is UNMEASURED).
- Untracked `docs/{arch,changelog,constitution,prd}/*kme_pillars*` files were generated by a hook during the run; they are not part of this plan and were not committed.
- `vault/progress.md`, the workstream `config.json` and `milestone.lock` were left alone as instructed.

## Self-Check: PASSED

Verified after writing: wiki/tools/kme_pillars.py, tools/test_kme_pillars.py, both measurement files present; commits 4e0333f8, d1f67731, ac0e5f2e present in the log; `grep -c 'sk-ant-'` on both measurement files is 0; ledger `state.D` is `{}`.
