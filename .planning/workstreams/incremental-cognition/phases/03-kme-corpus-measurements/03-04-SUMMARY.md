---
phase: 03-kme-corpus-measurements
plan: 04
subsystem: kme-measurement-instrument
tags: [pillar-I, IC-I, IC-D, IC-E, kme, subagent-bootstrap, cutoff-locator, one-scan-all, cpp-d-w7, population, gex44, smoke, mutation-drill]
requires: ["03-03"]
provides:
  - "wiki/tools/kme_pillars.py: IObserver, distribution, read_subagent_meta / subagent_type / is_subagent_path (shared by H and I), InstantObserver, locate_cutoff (LOCATE_MAX_SCANS 24, LOCATE_WINDOW_H 24, cutoff_accepts), SCAN_COUNT, dw7_spec / frozen_specs()['CPP-D-W7'] (referenced), referenced_coverage, fmt_instant; subcommands i / all / population; flags --since, --until auto, --freeze-instant, --project-filter, --frozen-ce-ledger, --denominator CPP-D-W7"
  - "tools/test_kme_pillars.py: 20 new V-KMEP gates (81 total), drill mutants M17-M20 (20 total)"
  - "vault/programs/incremental-cognition/measurements/I-KME-G-2026-10-03.md (smoke) and I-GEX44-B001-2026-10-03.md (second workload), plane gex44, terminal_evidence false"
affects: ["03-05"]
tech-stack:
  added: []
  patterns: ["cutoff accepted only on an every-field match, then re-verified after the final measuring scan", "referenced denominator: share judged against the ledger figure, observability scaled by coverage", "call-instant observer riding the first scan so the exact-at-freeze path costs one scan", "mutation seams as module-level names resolved at call time (is_subagent_path, cutoff_accepts, scan, referenced_coverage)"]
key-files:
  created: [vault/programs/incremental-cognition/measurements/I-KME-G-2026-10-03.md, vault/programs/incremental-cognition/measurements/I-GEX44-B001-2026-10-03.md]
  modified: [wiki/tools/kme_pillars.py, tools/test_kme_pillars.py]
decisions:
  - "[Phase 3]: [03-04] total scans of a run never exceed 24: the locator gets 23 (the freeze scan counts as one) and one is reserved for the final measuring scan at a located cutoff; the exact-at-freeze path reuses the first scan, so it is one scan in total"
  - "[Phase 3]: [03-04] the locator tries two candidates at the smallest call instant reaching the frozen call count: the instant itself, then the instant just before the next call (later non-call lines such as a new prompt-only session change sessions_dead without adding a call)"
  - "[Phase 3]: [03-04] a located cutoff keeps sub-second precision (fmt_instant: seconds, milliseconds or microseconds); truncating to whole seconds would drop the lines of the located second"
  - "[Phase 3]: [03-04] CPP-D-W7 share is judged against the CE ledger's weighted figure (referenced, never re-measured); observability = min(1, coverage) x the pillar's own; a primary file is terminal only at coverage >= 1 and a measured verdict"
  - "[Phase 3]: [03-04] CPP-D-W7 refuses --select, --since, --until, --freeze-instant and --label (fixed window, fixed selection); --since cannot combine with --until auto; --until auto and --freeze-instant are for KME-L / KME-G only"
  - "[Phase 3]: [03-04] population exits 0 when the frozen population is reproduced, a referenced one is fully covered, or the workload is unfrozen (OTHER); 3 otherwise; it prints per-project rows of the KME-selected sessions only and writes nothing"
status: complete
commits: 3
plan_head_before: 6a02660d97738ed440c350c4d7e5fa2f4e641a19
actuals:
  tokens: 22931
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-03
requirements: [IC-I, IC-D, IC-E]
requirements-completed: []
---

# Phase 3 Plan 04: pillar I, one-scan all, cutoff locator, CPP-D-W7 window, population proof Summary

`python3 wiki/tools/kme_pillars.py i|all|population ...` now measures the subagent bootstrap cost (I), runs all six pillars in one scan, locates the freeze-time cutoff of a growing corpus (`--until auto`), measures over the referenced CPP-D-W7 window, and proves which project dirs hold the frozen KME population. **IC-I, IC-D and IC-E are addressed, not satisfied**: terminals need the laptop KME-L runs (plan 03-05). Ledger `state.I` is `{}`; nothing was ticked and `requirements.mark-complete` was not called.

**Code commits:** `263d8ac2` (tracer: IObserver, shared meta reader, `i`, V-KMEP-I-E2E), `80eab96c` (all / locate_cutoff / D-W7 / population / flags, 18 gates), `3e5fd0d7` (drills M17-M20, KME-G smoke and second workload for I; carries the plan's subject).

## Observed results

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=81/81  threshold=81/81  skipped=0  inconclusive=0`, 11.4 s (limit 60 s). New: `V-KMEP-I-E2E`, `-I-SYNTHETIC-FIRST`, `-I-NO-SUBAGENTS`, `-I-AGENT-TYPE`, `-I-INLINE-SIDECHAIN-UNOBSERVED`, `-ALL-ONE-SCAN`, `-UNTIL-AUTO-LOCATE`, `-UNTIL-AUTO-AT-FREEZE`, `-UNTIL-AUTO-UNREACHABLE`, `-UNTIL-AUTO-BEFORE-NEXT-CALL`, `-UNTIL-AUTO-OTHER-REFUSED`, `-UNTIL-AUTO-BUDGET`, `-WINDOW-SINCE`, `-DW7-SPEC`, `-DW7-COVERAGE`, `-DW7-WINDOW-FIXED`, `-DW7-ROLES`, `-PROJECT-FILTER`, `-POPULATION-SUBCOMMAND`, `-KMEG-AUTO-REAL` (the real gate PASSes on GEX44: exact, `exact_at_freeze`, scans 1).
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL` 78/78, twenty `KILLED` lines, `PASS DRILL-CLEAN-AFTER-MUTANTS` 78/78, `DRILL killed=20/20`. New: M17 (every file read as a main-thread file, kills V-KMEP-I-E2E), M18 (locator accepts a calls-only match, kills V-KMEP-UNTIL-AUTO-UNREACHABLE), M19 (`all` scans once per pillar, kills V-KMEP-ALL-ONE-SCAN), M20 (coverage ignored for a referenced denominator, kills V-KMEP-DW7-COVERAGE).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`. Frozen pipeline `kme_token_audit.py --host gex44 --expand` on the a5 tree exits 0 (`OK host=gex44 dirs=3 sessions=8 kme=4`). `V-KMEP-AUDIT-BYTE-IDENTICAL(-REAL)` still PASS.
- Acceptance command: `timeout 120 python3 wiki/tools/kme_pillars.py population --denominator KME-G --until auto --expand --root a5 --root a7 --root b001 --root ~/.claude/projects` -> exit 0 in 3.4 s, `"population_match": "exact"`, `"method": "exact_at_freeze"`, `"scans": 1`, `until` 2026-10-03T16:13:37Z, population 13 active / 151 dead / 1,322 calls; `per_project` lists 4 dirs (`-home-kobii-kobii-a7` 507 calls, `-a5--claude-worktrees-a5-epoch2` 412, `-a7--claude-worktrees-a7-e15-phase11` 396, `-a5` 7).

## RED outputs

- Task 1 RED (IObserver / subcommand `i` absent): `FAIL V-KMEP-I-E2E rc=2 files=[] err=usage: kme_pillars.py [-h] PILLAR ... error: argument PILLAR: invalid choice: 'i' (choose from 'd', 'e', 'f', 'g', 'h')`, `KMEP_PASS=61/62`.
- Task 2 RED (gates added before any implementation): 15 FAIL, `KMEP_PASS=66/81`: `V-KMEP-ALL-ONE-SCAN` and `-KMEG-AUTO-REAL` (`module 'kme_pillars' has no attribute 'SCAN_COUNT'`), `-UNTIL-AUTO-LOCATE` / `-UNREACHABLE` / `-WINDOW-SINCE` / `-DW7-COVERAGE` / `-DW7-WINDOW-FIXED` (subcommand or flag refused, `NoneType` result), `-UNTIL-AUTO-AT-FREEZE` (`rc=2`), `-UNTIL-AUTO-BEFORE-NEXT-CALL`, `-UNTIL-AUTO-OTHER-REFUSED` (the KME-L control also rc 2), `-UNTIL-AUTO-BUDGET` (`no attribute 'locate_cutoff'`), `-DW7-SPEC` (`frozen_specs() missing 1 required positional argument`), `-DW7-ROLES`, `-PROJECT-FILTER`, `-POPULATION-SUBCOMMAND` (`rc=2`). First green run after the build had 4 FAILs from one locator bug (a memoised probe returned a bare dict, `too many values to unpack`), fixed, then 81/81.
- M18 first SURVIVED the drill (see deviations); after the gate was extended `DRILL killed=20/20`.

## One-scan `all` vs the per-pillar KME-G files (real corpus, `--until auto`)

`all --denominator KME-G --until auto --expand` over a5, a7, b001 and `~/.claude/projects` (written to `/tmp/ic-p3-04-all`, not committed) against the files committed in 03-01..03-03 and the new I file. All six report `population=exact`, `cutoff=exact_at_freeze`, one scan.

| pillar | share_interval (all == committed) | materiality | numerator | equal |
|---|---|---|---|---|
| D | [0.026388, 0.039582] | STRADDLES | equal | yes |
| E | [0.0, 0.0] | < 3 % | equal | yes |
| F | [0.00688, 0.01032] | < 3 % | equal | yes |
| G | [0.0, 0.0] | < 3 % | equal | yes |
| H | [0.072976, 0.073973] | >= 3 % | equal | yes |
| I | [0.082611, 0.082611] | >= 3 % | equal | yes |

## Pillar I smoke on KME-G (GEX44, read only)

Command: `timeout 600 python3 wiki/tools/kme_pillars.py i --denominator KME-G --until auto --expand --root a5 --root a7 --root b001 --root ~/.claude/projects` -> exit 0, `I-KME-G-2026-10-03.md`: `plane: "gex44"`, `evidence_role: "smoke"`, `terminal_evidence: false`, `population_match: "exact"`, `until_located.method: "exact_at_freeze"`, observability 1.0 (no inline sidechain line on this host).

- 11 subagent files: first-call context min 124,905, median 125,746, p90 128,432, max 128,739, total 1,393,005. Main-thread first-call context (13 files): min 172,753, median 184,030, max 194,591. So a subagent boots at about 68 % of a main thread's first-call context here. All 11 first calls are cold (cache_write > cache_read).
- Numerator 4,535,325.7 weighted = first calls 2,795,013 + floor rent 1,740,312.7; share **8.26 %** of 54,899,559, materiality `>= 3 %`, `second_workload_required: true`. By agent type: `kme-g1-ownership-arbiter` x6 2,332,108; `kme-g2-production-reality` x3 1,182,476; `kme-r1-evaluator-redteam` x1 683,395; `pp-code-reviewer` x1 337,347.
- **Second workload** (required by the file): `i --denominator OTHER --label GEX44-B001 --select all --host gex44 --expand --root b001/projects` -> `I-GEX44-B001-2026-10-03.md`, smoke, `population_match: "not_frozen"`, share **17.25 %**, `>= 3 %`. Committed.
- Reading (not a terminal, not the frozen denominator): the bootstrap of a subagent is above 3 % of the weighted denominator on both GEX44 workloads; the frozen rule for I is only "add the measured figure to CE B / SC A-C, no move of a rule or skill here", which this file feeds. KME-L decides.
- **No-write proof:** `find ... -type f -printf '%p %s %T@\n' | sort` over the a5, a7 and b001 project trees (736 files) before and after the `i` and `all` runs: `diff /tmp/ic-p3-04-snap.before /tmp/ic-p3-04-snap.after` printed nothing; the same for the B001 run (`/tmp/ic-p3-04-snap2.*`). `~/.claude/projects` is scanned but excluded from the snapshots (live sessions append there).
- `grep -c 'sk-ant-'` on both new files -> 0; `terminal_evidence: false`, `evidence_role: "smoke"`, `plane: "gex44"` each count 1 in `I-KME-G-2026-10-03.md`. `python3 -c "...print(d['state']['I'])"` -> `{}`.

## Deviations from Plan

**1. [Process] No RED run for four I pole gates.** `V-KMEP-I-SYNTHETIC-FIRST`, `-NO-SUBAGENTS`, `-AGENT-TYPE`, `-INLINE-SIDECHAIN-UNOBSERVED` passed on their first run: Task 1 already built the whole IObserver. To show they can go red, each was driven against a deliberate break in an ad hoc script (not committed): synthetic counted as the first call -> FAIL; empty distribution inventing a value -> FAIL; agent type always unknown -> FAIL (with V-KMEP-I-E2E); inline sidechain lines not counted -> FAIL.

**2. [Rule 1 - gate gap] M18 SURVIVED at first.** `_resolve` re-verifies the located cutoff after its final scan, so a calls-only locator was masked by the CLI: `V-KMEP-UNTIL-AUTO-UNREACHABLE` saw `not_found` either way. The gate now also drives `locate_cutoff` directly with a probe whose calls reach the frozen figure while `cache_read` is off by one (must be `not_found`) and a control that matches (must be `bisect`); then M18 is killed.

**3. [Rule 2 - correctness] Second locator candidate and two extra gates.** The plan's bisection checks only the smallest call instant reaching the frozen call count. A prompt-only session created after the last call but before the P0 run changes `sessions_dead` and no call instant, so the exact cutoff lies just before the next call. The locator now tries that instant too (still every-field exact only). Added `V-KMEP-UNTIL-AUTO-BEFORE-NEXT-CALL` (positive: dead session at T4.5 -> located T5 - 1 us) and `V-KMEP-UNTIL-AUTO-BUDGET` (unit: 5,000 virtual instants never matching -> `not_found` in 14 scans, `max_scans=5` stops at 5 with "budget" in why, a reachable one found in 14).

**4. [Rule 1 - bug avoided] Sub-second cutoffs.** Real timestamps carry milliseconds; the existing `until` rendering truncated to whole seconds, which would have dropped the lines of the located second. `fmt_instant` renders seconds, milliseconds or microseconds as needed; fixtures use `ts()` with milliseconds and `--freeze-instant` at T4.5.

**5. [Plan wording] 24 scans.** The plan bounds `--until auto` at 24 scans and also needs a final measuring scan at a located cutoff; the total never exceeds 24 (locator 23 + 1 final); `V-KMEP-UNTIL-AUTO-BUDGET` checks the locator bound.

**6. [Plan wording] M17.** "IObserver takes the main thread's first call for subagent files" is implemented as `is_subagent_path` always False (every file read as a main-thread file, so `subagent_files` is 0 and the first-call figures land in `main_first_ctx`). It also touches H, but only V-KMEP-I-E2E is its target.

**7. [Design] Flag refusals added** (exit 2, nothing written): `--select`/`--label` with CPP-D-W7; `--since` with `--until auto`; `--freeze-instant` without `--until auto`; invalid `--project-filter` regex. `all --json` prints one JSON line per pillar.

**8. [Attribution]** Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the attribution in force in this session's system reminder), not the Opus 5.5 line named in the dispatch; same choice as 03-01..03-03.

**9. [Process]** The agent-branch-namespace pre-commit check was not applied: this is a sequential run on the dispatched `mission/incremental-cognition-run` branch; HEAD was never on a protected branch.

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None new. `population` prints project directory names and counts (passed through the secret redactor); the tool reads transcripts, `meta.json` files and the CE ledger (read-only json load, never written) and writes only markdown under the measurements directory. No env tree, CE/SC ledger or IC ledger state was written.

## Debts / notes for the owner bundle (plan 03-05)

- Laptop proof of the frozen KME-L population, unfiltered first (KME is classified by content): `python wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root <laptop projects root>`; its `per_project` rows name every dir holding KME sessions; `--project-filter REGEX` is only a speed-up afterwards. Exit 0 and `"population_match": "exact"` is the proof; `cutoff_not_found` (exit 3) names the fields that differ.
- Measurement on KME-L in one scan: `python wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root <laptop projects root>`. D's second leg: `d --denominator CPP-D-W7 --expand --root <laptop projects root>` (window and selection are fixed by the CE ledger; coverage must reach 1 for a terminal). E's second workload: `e --denominator CPP-D-W7 --role second_workload ...`.
- The `--until auto` search window is 24 h before the freeze instant; a laptop corpus whose frozen population needs an earlier cutoff reports `not_found` rather than guessing.
- D-W7 caveat in every such file: the CE parser dedupes across files keeping the last copy, this instrument per file with max-merge, so coverage >= 1 does not prove the same call set.
- Untracked `docs/{arch,changelog,constitution,prd}/*kme_pillars*` files (hook-generated) were left alone, as were `vault/progress.md`, the workstream `config.json` and `milestone.lock`.

## Self-Check: PASSED

Verified after writing: wiki/tools/kme_pillars.py, tools/test_kme_pillars.py, I-KME-G-2026-10-03.md and I-GEX44-B001-2026-10-03.md present; commits 263d8ac2, 80eab96c, 3e5fd0d7 in the log; `grep -c "def read_subagent_meta"` is 1; `terminal_evidence: false`, `evidence_role: "smoke"`, `plane: "gex44"` each count 1 in the I KME-G file; `sk-ant-` count 0; ledger `state.I` is `{}`; `git show --stat HEAD` lists only kme_pillars-related test code and measurement files.
