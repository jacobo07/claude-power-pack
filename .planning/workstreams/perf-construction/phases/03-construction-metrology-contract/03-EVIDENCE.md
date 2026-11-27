# Phase 3 Evidence: Construction metrology contract

Phase: 03-construction-metrology-contract (requirement PERF-03)
Plane GEX44 (kobicraft-gex44, Linux, Python 3.12.3, stdlib only). Date: 2026-11-22/23. Instrument HEAD for the live run: 8ef8d339 (the `# head:` line of `records/03-03-live.txt`). Evidence written at HEAD 2bb7b6d9 plus this file.

Verdict: PASS for the three ROADMAP criteria, each cited to a record below. This is a verdict about the contract, the instrument and its gates on GEX44. It is not a statement that the definitions are the Owner's (they are PROPOSED, section 3), and it is not evidence about the laptop. Phase verification decides closure.

Paths below are relative to `.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/` (written `PH`) unless they start with `tools/`, `modules/` or `vault/`.

## 1. Success criteria

| SC | Criterion | Command | Exit | Record | Verdict |
|----|-----------|---------|------|--------|---------|
| SC1 | Start and end points of TTFMC, TTFUR, TTVD defined in writing and implemented as events in the D1 owner | `python3 tools/test_construction_metrology.py` (V-METRO-CONTRACT-MATCHES-CODE reads the contract table and compares start, end and horizon with `METRICS` and `HORIZON_S`) | 0, METRO_PASS=38/38 | `PH/records/03-03-final-gates.txt`; contract `vault/specs/construction-metrology-contract.md`; owner `modules/capability_runtime/construction_metrology.py` | PASS (definitions PROPOSED) |
| SC2 | Distribution report with p50/p90/p95, N and censored count runs over real transcripts of this host and says GEX44 | `python3 -I record_run.py --out PH/records/03-03-live.txt --expect pass --timeout 600 -- python3 tools/construction_metrology_report.py --root /home/kobii/.claude/projects --max-files 200 --max-bytes 200000000 --seed 0 --json-out PH/records/03-03-live.json` | 0 (`# exit=0`) | `PH/records/03-03-live.txt`, `PH/records/03-03-live.json`; header line `plane: GEX44`, JSON `plane` GEX44, `plane_source` hostname | PASS (capped sample) |
| SC2 validators | The live records hold only closed-schema data | `python3 tools/construction_metrology_report.py --validate PH/records/03-03-live.json` and `--validate-text PH/records/03-03-live.txt` | 0 and 0 (VALIDATE_OK, VALIDATE_TEXT_OK) | the same two records | PASS |
| SC3 | Eight states MEASURED / FAILED / TIMED_OUT / INCONCLUSIVE / SKIPPED_BY_POLICY / NOT_APPLICABLE / UNOBSERVED / UNAVAILABLE reachable, each tested | the same suite: eight V-METRO-STATE-<S> gates (reached from a transcript-shaped input) and eight V-METRO-POLE-<S> gates (a wrong classification changes the output) | 0, 38/38 | `PH/records/03-03-final-gates.txt`; red records `PH/records/03-01-T1.red.txt`, `03-01-T2.red.txt`, `03-02-T1.red.txt`, `03-02-T2.red.txt`, `03-02-T3.red.txt` | PASS |

Exactly one live run was made. Its record is the one committed (commit 2bb7b6d9). No second run was taken and no cap was changed.

## 2. Gates and phase-3 plan 03 scope

This plan wrote no code. `git status --porcelain` showed no path under `tools/bench_all.py`, `tools/test_bench_*.py`, `tools/verify_bench_all.py`, `tools/tis_observed.py` or `modules/capability_runtime/__init__.py`.

## 3. Definitions

The contract is `vault/specs/construction-metrology-contract.md`, status PROPOSED. The Owner did not define TTFMC, TTFUR or TTVD in any admitted source on this host (D-02, 01-EVIDENCE.md section 4, LP-02). The names are labels. The expansions are proposals: TTFMC time to first material change (start `HUMAN_PROMPT`, end `WRITE_TOOL_USE`, horizon 3600 s), TTFUR time to first user-visible response (end `ASSISTANT_TEXT`, horizon 900 s), TTVD time to verified deliverable (end `VERIFY_RESULT_OK`, horizon 7200 s). The horizons are observation windows, not targets.

TTVD proxy caveat: the end is the first ok Bash result after the first change in the turn. Reading command text is forbidden by D-05, so the instrument cannot tell a test run from any other shell command. TTVD is a proxy for verification until LP-06 is answered.

## 4. Live distribution (copied from `PH/records/03-03-live.txt`; the JSON carries the same counts)

Instrument for every number in this section: `tools/construction_metrology_report.py` at HEAD 8ef8d339, `--max-files 200 --max-bytes 200000000 --seed 0`, plane GEX44, host kobicraft-gex44, transcript root `/home/kobii/.claude/projects`, 1919 stores, files read 200 of 4576, bytes read 199998680 of 6189100855, `capped=yes`, text line `CAPPED SAMPLE - not the whole population`. 575 subagent files were excluded and counted, 0 files were unavailable.

Scope for every number: this host only; a CAPPED SAMPLE (200 of 4576 files), not the population; the sample includes this mission's own sessions; not evidence about the laptop. The planning-time probe saw 4575 files and 1913 stores; the stores grew while this plan ran, so the totals differ by the live growth, and a second run would be a different sample.

| Metric | N_total | measured | censored | p50 (s) | p90 (s) | p95 (s) |
|--------|---------|----------|----------|---------|---------|---------|
| TTFMC | 218 | 18 | 5 | 111.54 | 218.91 | UNJUDGED (n=18 < 20) |
| TTFUR | 218 | 80 | 5 | 15.53 | 52.15 | 83.94 |
| TTVD | 218 | 16 | 7 | 124.34 | 272.84 | UNJUDGED (n=16 < 20) |

State counts (eight states, all from the same run):

| State | TTFMC | TTFUR | TTVD |
|-------|-------|-------|------|
| MEASURED | 18 | 80 | 16 |
| FAILED | 2 | 1 | 2 |
| TIMED_OUT | 1 | 0 | 1 |
| INCONCLUSIVE | 0 | 0 | 0 |
| SKIPPED_BY_POLICY | 133 | 133 | 133 |
| NOT_APPLICABLE | 62 | 0 | 62 |
| UNOBSERVED | 2 | 4 | 4 |
| UNAVAILABLE | 0 | 0 | 0 |

Reading notes, each limited to what the record shows. Censored is FAILED + TIMED_OUT + UNOBSERVED (TTFMC 2+1+2, TTFUR 1+0+4, TTVD 2+1+4). Each column sums to N_total 218. The p95 of TTFMC and TTVD is UNJUDGED because the declared minimum is 20 measured values (MIN_N p50=5, p90=10, p95=20); no number is printed in its place. 133 of 218 turns are SKIPPED_BY_POLICY by the origin policy, which leaves 85 human-origin turns for each metric. The origin policy excludes starts whose `turnOrigin` is not `human` (or, without `turnOrigin`, whose entrypoint is not `cli`); the record does not say who or what produced those 133 starts. These numbers describe this sample of this host's sessions only. They are not a performance claim, not a target and not a ranking.

States whose live count is 0 for all three metrics, and the fixture gate that reaches each:

- INCONCLUSIVE: reached only by V-METRO-STATE-INCONCLUSIVE (a start or end timestamp that is missing, unparseable or inverted), with V-METRO-POLE-INCONCLUSIVE as its pole.
- UNAVAILABLE: reached only by V-METRO-STATE-UNAVAILABLE (a file that cannot be opened or holds no JSON line) and V-METRO-ROOT-UNAVAILABLE (a missing root, exit 2), with V-METRO-POLE-UNAVAILABLE as its pole.

Zero live count for one metric only: TTFUR NOT_APPLICABLE is 0 by construction (every included human turn expects a response); TTFUR TIMED_OUT is 0 in this sample and is reached by V-METRO-STATE-TIMED_OUT. A zero here is a measured zero over this sample, not a proof that the state cannot occur on the laptop.

## 5. Gates: baseline (03-01), after (03-02), final (03-03)

Records: `PH/records/03-01-baseline.txt`, `PH/records/03-02-gates-after.txt`, `PH/records/03-03-final-gates.txt`.

| Gate | Baseline 03-01 | After 03-02 | Final 03-03 |
|------|----------------|-------------|-------------|
| tools/test_capability_invocation.py | 13/13, exit 0 | 13/13, exit 0 | 13/13, exit 0 |
| tools/test_capability_runtime.py | 33/33, exit 0 | 33/33, exit 0 | 33/33, exit 0 |
| tools/test_agent_resolver.py | 33/33, exit 0 | 33/33, exit 0 | 33/33, exit 0 |
| tools/test_agent_telemetry.py | 20/20, exit 0 | 20/20, exit 0 | 20/20, exit 0 |
| tools/test_capability_consumption.py | 11/11, exit 0 | 11/11, exit 0 | 11/11, exit 0 |
| tools/test_capability_directory.py | 3/3, exit 0 | 3/3, exit 0 | 3/3, exit 0 |
| tools/test_reachability.py | 15/15, exit 0 | 15/15, exit 0 | 15/15, exit 0 |
| tools/test_git_invocation.py | 6/7, exit 1 | 6/7, exit 1 | 6/7, exit 1 |
| tools/test_construction_metrology.py | absent | 38/38, exit 0 | 38/38, exit 0 |
| modules/liveness/reachability.py --json | exit 1, 56 offenders | exit 1, 56 offenders | exit 1, 56 offenders, `passed=False`, new unit not listed |

Comparison of final against `03-02-gates-after.txt`: no gate result changed. The section headers and exit codes are equal. The only differing lines are volatile values: the timing and resolution-id lines of the three V-TEL-CLI gates, the random temporary directory name in V-CAPDIR-ROW, and `## HEAD` (e00beb98 to 2bb7b6d9). The added sections are the metrology suite (38/38) and the reachability summary. `## policy_hash` is `f113a59d0dc99c56` in both. The reachability offender set after (`PH/records/03-02-reach-after.json`) and now are identical by name (56 = 56, none added, none removed; checked in process against the final `--json` output).

- `tools/test_git_invocation.py` stays 6/7: only V-GITINV-NO-GROWTH fails, with the same 14 pre-existing offenders as the baseline; none is a Phase 3 file. The full section is line-for-line unchanged from 03-02.
- The reachability gate exits 1 on the pre-existing standing debt, unchanged by name. The new unit is declared DORMANT (registry row added by commit a28a110c) and is not an offender. Exit 0 is not the criterion.

Red records for the tasks that added gates (each taken with the owner files pristine and verified with `record_run.py --verify ... --expect fail --pristine-required`): `PH/records/03-01-T1.red.txt` (0/4), `03-01-T2.red.txt` (5/9), `03-02-T1.red.txt` (15/27), `03-02-T2.red.txt` (30/37), `03-02-T3.red.txt` (37/38); their green records exit 0. Plan 03-03 added no gate and so has no red record.

## 6. Policy id

Live `policy_hash()` before (`PH/records/03-01-baseline.txt`): `169abc7fce15ce84`. After (`PH/records/03-02-gates-after.txt` and `PH/records/03-03-final-gates.txt`): `f113a59d0dc99c56`. It moved once, in commit 00e7d004, caused by the one-line NOT_POLICY edit to `modules/capability_runtime/agent_resolver.py`, which is itself hashed. The mechanism is the same as for the earlier agent_telemetry and agent_resolver_cli additions (commit 050c3484). V-METRO-POLICY-ID-UNMOVED proves the metrology file itself never moves it: identical ids with the file, without it and edited, equal to the live id. The id was unchanged by plans 03-02 and 03-03.

## 7. D-01..D-09 trace

| Decision | Commits | Files and records |
|----------|---------|-------------------|
| D-01 owner is `modules/capability_runtime`, vocabulary added, policy id guarded | 00e7d004, 3c53c9e7 | `modules/capability_runtime/construction_metrology.py`, `modules/capability_runtime/agent_resolver.py` (NOT_POLICY), contract section 1, V-METRO-POLICY-ID-UNMOVED |
| D-02 definitions PROPOSED, never Owner-defined | 3c53c9e7, 921f9c34 | `vault/specs/construction-metrology-contract.md` (status proposed), V-METRO-CONTRACT-MATCHES-CODE, LP-04 |
| D-03 eight states, censoring, both poles | 7d604db1, 519d5847 (RED 555b2baf, d751517c) | V-METRO-STATE-<S>, V-METRO-POLE-<S>, V-METRO-UNKNOWN-NEVER-MEASURED, V-METRO-MUTANT-HORIZON |
| D-04 percentile connected to one owner, UNJUDGED below MIN_N | 00e7d004, 519d5847 | V-METRO-PERCENTILE-CONNECTED, V-METRO-MIN-N-UNJUDGED, V-METRO-ONLY-MEASURED-IN-VALUES, V-METRO-MUTANT-VALUES-FILTER; `tools/verify_bench_all.py` `percentile` imported, not copied |
| D-05 real transcripts, plane GEX44, bounded, no content | 519d5847, 2bb7b6d9 | V-METRO-NO-CONTENT, V-METRO-JSON-SCHEMA, V-METRO-TEXT-GRAMMAR, V-METRO-CAP-LABELLED, V-METRO-ROOT-UNAVAILABLE, V-METRO-PLANE; `PH/records/03-03-live.txt`, `PH/records/03-03-live.json` |
| D-06 reuse owners, new files only with a written reason | 3c53c9e7, 921f9c34 | contract section 7; `tools/construction_metrology_report.py` is a thin CLI; `store_dirs` of `tools/tis_observed.py` connected |
| D-07 existing gates unmoved, liveness declared, git_invocation unchanged | 57dc895b, a28a110c | `PH/records/03-01-baseline.txt`, `03-02-gates-after.txt`, `03-03-final-gates.txt`, `03-01-reach-before.json`, `03-02-reach-after.json`, `vault/liveness/reachability_registry.json` (DORMANT row), V-METRO-LIVENESS-DECLARED |
| D-08 red record per gate, numbers name instrument, plane and N, this evidence file | 18404f01, f8e69469, 555b2baf, d751517c, e00beb98, 2bb7b6d9 | the five red records in section 5, section 4 of this file, `PH/03-EVIDENCE.md` |
| D-09 pathspec commits, no push, forbidden files untouched | all phase 3 commits | `git status --porcelain` clean of forbidden paths; nothing pushed |

## 8. LAPTOP-ONLY items (copied from the contract, section 8)

- LP-04 (definitions). Procedure: the Owner, or the laptop-side source text once it is admitted, confirms or replaces each expansion and each start and end mapping in contract section 2. Falsifier: any definition that names a different start or end event means the corresponding `METRICS` row is swapped and the gates rerun; the definitions stay PROPOSED until then. The main candidate replacement is TTFMC read as "time to first model content", with the end event the first assistant line of any block type. Never replaced by a GEX44 reading.
- LP-05 (laptop distribution). Procedure: on the laptop, run `python tools/construction_metrology_report.py --root <laptop transcript root>` with the same caps and seed as the GEX44 run. Falsifier: a laptop header that says GEX44, or laptop numbers filled in from the GEX44 run; the header must say UNDECLARED or a laptop plane label. Never replaced by a GEX44 reading.
- LP-06 (TTVD proxy). Procedure: decide whether verification may be classified from command text read in memory, which needs the Owner's authorization because D-05 forbids reading content. Falsifier: on a sampled set of turns, if the proxy end (the first ok Bash result after a change) and a human judgement of "verified" disagree in most cases, the proxy is not a measure of verification and TTVD stays UNJUDGED. Never replaced by a GEX44 reading.

A GEX44 distribution is not evidence about the laptop. The Owner's complaint is the laptop; nothing in section 4 answers it.

## 9. P-ids and open debt

P-ids touched: none

Open debt:

- The metrology unit is declared DORMANT in `vault/liveness/reachability_registry.json`: no hook, command or agent reaches it. It waits for its Phase 5 consumer; until then only the CLI and the gate suite invoke it.
- TTVD is a proxy (section 3, LP-06). Its numbers in section 4 are the time to the first ok Bash result after a change, not a verified-deliverable time.
- The three definitions remain PROPOSED until LP-04 is answered.
- The live run is one capped sample (4% of files by count). Any claim about the population needs a larger or repeated run, which this phase did not make.
