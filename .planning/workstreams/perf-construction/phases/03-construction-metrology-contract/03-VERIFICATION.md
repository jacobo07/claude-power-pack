---
phase: 03-construction-metrology-contract
verified: 2026-11-23T00:30:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 3/3 roadmap success criteria verified on GEX44 (definitions PROPOSED, TTVD a proxy)
verified_head: 1d9bccb5
behavior_unverified: 0
gaps: []
unknowns:
  - "LP-04: the expansions and start/end mappings of TTFMC, TTFUR and TTVD are PROPOSED by this phase, not the Owner's; no definition exists on this host (iteracion-avanzada-universal.txt NOT ADMITTED). The gates prove the code matches the written contract, not that the contract is what the Owner means"
  - "LP-05: no laptop distribution exists. The live report is a GEX44, capped sample (200 of 4576 files); it says nothing about the laptop where the slowness was reported"
  - "LP-06: TTVD ends at the first ok Bash result after the first change. It cannot tell a test run from any other shell command (command text is not read, D-05). TTVD is a proxy for verification, UNJUDGED as a measure of it"
  - "The metrology unit is DORMANT: declared in the reachability registry, reached only by a manual CLI and its gate suite; no hook, command or agent consumes it until Phase 5"
  - "Live p95 of TTFMC and TTVD is UNJUDGED (n=18 and n=16, below MIN_N 20); the live INCONCLUSIVE and UNAVAILABLE counts are 0, those states are proven by fixtures only"
  - "Test-strength gap found by mutation: mutant J (a Bash call issued before the first change is accepted as the TTVD verify) survives 38/38. It differs from the real code only when such a call has its result after the change; no fixture has that shape. Untested edge, not an observed defect"
human_verification: []
---

# Phase 3: Construction metrology contract - Verification Report

**Phase goal:** The time a construction takes is measured, not guessed.
**Plane:** GEX44 (kobicraft-gex44, Linux, python3 stdlib). Code reading, the phase suite, a fresh capped run of the report CLI, the previously recorded live run, and throw-away mutation copies of a `git archive` of HEAD under /tmp (outside the repo). No transcript content was printed or read into this report; only counts, states and timings.
**Re-verification:** No, initial verification.
**Status: passed_with_unknowns.** The three roadmap success criteria are met on evidence I re-observed. The phase does not establish that the definitions are the Owner's, does not say anything about the laptop, and leaves TTVD as a proxy. None of those is counted as a pass.

## Observable Truths (ROADMAP Phase 3 success criteria)

| # | Truth | Status | Evidence (re-observed, not taken from SUMMARY) |
|---|-------|--------|-----------------------------------------------|
| 1 | Start/end points of TTFMC, TTFUR, TTVD defined in writing; implemented as events in the owner chosen by D1 | VERIFIED (definitions PROPOSED) | Contract `vault/specs/construction-metrology-contract.md` section 2 holds a table with start, end, horizon, applicability and meaning of a missing end for each metric, status `proposed`, and states plainly that the Owner did not define them. Owner is `modules/capability_runtime/construction_metrology.py` (D1 = capability_runtime, per Phase 1): `METRICS` maps TTFMC to HUMAN_PROMPT/WRITE_TOOL_USE, TTFUR to HUMAN_PROMPT/ASSISTANT_TEXT, TTVD to HUMAN_PROMPT/VERIFY_RESULT_OK, `HORIZON_S` 3600/900/7200; `read_events` emits those event kinds from transcript lines. `V-METRO-CONTRACT-MATCHES-CODE` parses the table and compares it with the code; it is load-bearing (mutant C and mutant O both made it fail). Doubt: "implemented as events" is true for the event reader; nothing consumes them in production (DORMANT, see unknowns). |
| 2 | Distribution report (p50/p90/p95, N, censored count) runs over real transcripts of THIS host and says GEX44 plane | VERIFIED (capped sample) | I ran `tools/construction_metrology_report.py --root /home/kobii/.claude/projects --max-files 40 --max-bytes 50000000 --seed 7`: exit 0, header `plane: GEX44`, `host: kobicraft-gex44`, `CAPPED SAMPLE - not the whole population`, per metric `N_total`, `measured`, `censored`, p50/p90/p95 or `UNJUDGED (n=K < M)` (TTFUR N_total=49 measured=15 p50=20.73 p90=129.31 p95 UNJUDGED; TTFMC and TTVD measured=4 so all three UNJUDGED, no digit printed in their place). A missing root exits 2 with `status: UNAVAILABLE (root_unreadable)` and no percentile. `--plane laptop-x` prints `plane: laptop-x (declared by --plane)`. The recorded run `records/03-03-live.txt` (HEAD 8ef8d339, 200 of 4576 files) passes both validators when I re-ran them: `--validate` on the JSON gave VALIDATE_OK, `--validate-text` on the text gave VALIDATE_TEXT_OK. Percentiles come from `tools.verify_bench_all.percentile` (imported; mutant K, a local copy, failed 3 gates). |
| 3 | The eight states are reachable, each tested | VERIFIED | `python3 tools/test_construction_metrology.py`: `METRO_PASS=38/38`, exit 0, including eight `V-METRO-STATE-<S>` gates (reached from a transcript-shaped input through `scan()`) and eight `V-METRO-POLE-<S>` gates (altering the input moves the output). Reasons are a closed set and `classify` asserts membership. Six of the eight states have a non-zero count in the live record; INCONCLUSIVE and UNAVAILABLE are fixture-only (stated honestly in 03-EVIDENCE.md section 4). Mutants against individual states (A, A2, N, W, X) were each caught by the matching STATE and POLE gates. |

**Score:** 3/3 criteria verified; 0 present-but-behavior-unverified truths. The state classifier is behavior-dependent and has a behavioral test per state, so no truth is left at presence-only.

## Mutation checks I ran (could the instrument have returned the other answer?)

Each mutation was applied to a fresh copy of `git archive HEAD` under /tmp/p3v and `tools/test_construction_metrology.py` re-run there. The repo was not mutated.

| Mutant | Result | Gates that caught it |
|--------|--------|----------------------|
| A end past horizon never TIMED_OUT | 33/38 | STATE-TIMED_OUT, POLE-TIMED_OUT, MUTANT-HORIZON |
| A2 open turn past horizon never TIMED_OUT | 35/38 | STATE-TIMED_OUT, POLE-TIMED_OUT, MUTANT-HORIZON |
| B values include every numeric sample | 36/38 | ONLY-MEASURED-IN-VALUES, MUTANT-VALUES-FILTER |
| C MIN_N all zero (percentile never UNJUDGED) | 35/38 | TRACER-TTFUR-MEASURED, CONTRACT-MATCHES-CODE, MIN-N-UNJUDGED |
| D absent `is_error` treated as an error | 37/38 | TTVD-MEASURED |
| E2 both API-error signals ignored (model `<synthetic>` and `isApiErrorMessage`) | 34/38 | STATE-FAILED, POLE-FAILED, ONLY-MEASURED-IN-VALUES, MUTANT-VALUES-FILTER |
| F module removed from NOT_POLICY | 37/38 | POLICY-ID-UNMOVED |
| I every origin included | 34/38 | STATE-SKIPPED_BY_POLICY, POLE-SKIPPED_BY_POLICY, ONLY-MEASURED-IN-VALUES |
| K percentile reimplemented locally | 35/38 | PERCENTILE-CONNECTED, ONLY-MEASURED-IN-VALUES, MUTANT-VALUES-FILTER |
| L any host labelled GEX44 | 37/38 | PLANE |
| M capped label removed | 37/38 | CAP-LABELLED |
| N NOT_APPLICABLE returned as UNOBSERVED | 35/38 | TTFMC-NOT-APPLICABLE, STATE-NOT_APPLICABLE, POLE-NOT_APPLICABLE |
| O UNOBSERVED not counted as censored | 28/38 | TRACER-UNOBSERVED-CENSORED, TTFMC-NOT-APPLICABLE, CONTRACT-MATCHES-CODE and more |
| Q a file path leaked into `transcript_root` | 37/38 | NO-CONTENT |
| R registry row removed | 37/38 | LIVENESS-DECLARED |
| S tool_result-only user lines open turns | 34/38 | TTFMC-MEASURED, TTVD-MEASURED, NOT-A-START |
| T `Read` counted as a material change | 32/38 | TTFMC-MEASURED, TTFMC-NOT-APPLICABLE, STATE-NOT_APPLICABLE |
| U byte cap ignored | 37/38 | CAP-LABELLED |
| V horizon boundary `>=` instead of `>` | 37/38 | MUTANT-HORIZON |
| W unreadable file not UNAVAILABLE | 35/38 | STATE-UNAVAILABLE, POLE-UNAVAILABLE, ROOT-UNAVAILABLE |
| X missing start timestamp not INCONCLUSIVE | 34/38 | STATE-INCONCLUSIVE, POLE-INCONCLUSIVE, ONLY-MEASURED-IN-VALUES |

Survivors, reported honestly:
- E alone (`isApiErrorMessage` ignored) and E2 alone (`<synthetic>` model ignored) both pass 38/38 because the two signals are redundant; only removing both is detected. That is redundancy, not a hole, but neither signal is individually pinned.
- J (a verify tool_use is accepted when it precedes the first change; the result search is still limited to results after the change) passes 38/38. It only differs when a Bash call is issued before the change and its result arrives after it, which no fixture contains. This is a test-strength gap on an edge the contract names, not an observed defect in live numbers.

## Key links

| From | To | Via | Status |
|------|----|-----|--------|
| `construction_metrology.py` | `tools.verify_bench_all.percentile` | import (one owner of the percentile) | WIRED; mutant K |
| `construction_metrology.py` | `tools.tis_observed.store_dirs` | import (one owner of store identity) | WIRED; `V-METRO-PERCENTILE-CONNECTED` names both |
| `agent_resolver.NOT_POLICY` | `construction_metrology.py` | frozenset member, so the resolver policy id does not move | WIRED (line 133); mutant F |
| `tools/construction_metrology_report.py` | `scan` / `format_report` / validators | thin CLI, 100 lines | WIRED (ran it, exit 0 and exit 2) |
| `vault/liveness/reachability_registry.json` | the module | DORMANT row `capability_runtime/construction_metrology` | DECLARED, not offender; `reachability.py --json` still `passed=false` on 56 pre-existing offenders, none this unit |
| any hook, command or agent | the module | none | NOT WIRED by design (DORMANT; first consumer Phase 5) |

## Regression gates (re-run by me at HEAD 1d9bccb5)

`test_capability_invocation` 13/13, `test_capability_runtime` 33/33, `test_agent_resolver` 33/33, `test_agent_telemetry` 20/20, `test_capability_consumption` 11/11, `test_capability_directory` 3/3, `test_reachability` 15/15; `test_git_invocation` 6/7 with only V-GITINV-NO-GROWTH failing, equal to the pre-phase baseline recorded in 02-VERIFICATION.md and 03-EVIDENCE.md (pre-existing offenders, none a Phase 3 file). Files changed under tools, modules and vault since the Phase 2 close (1450e7cb): `modules/capability_runtime/agent_resolver.py` (one NOT_POLICY line), the new module, the new CLI, the new test, the registry row and the contract. `tools/bench_all.py`, `tools/test_bench_*.py`, `tools/verify_bench_all.py` and `modules/capability_runtime/__init__.py` are untouched, as D-07 and D-09 require.

## Requirements coverage

| Requirement | Status | Note |
|-------------|--------|------|
| PERF-03 (TTFMC / TTFUR / TTVD events with p50/p90/p95 and censored samples, in the D1 owner) | SATISFIED on GEX44, with the PROPOSED-definition and TTVD-proxy caveats | No orphaned Phase 3 requirements. |

## Anti-patterns and integrity checks

- Debt-marker scan (TBD / FIXME / XXX / TODO / HACK) over the four new code and contract files: none.
- Privacy: the report schema is closed (`JSON_SCHEMA_KEYS`, `TEXT_LINE_PATTERNS`); `read_events` keeps only types, timestamps, ids and flags; reasons are a closed set asserted in `classify`. The recorded live JSON and text pass the validators. Mutant Q (a path leaked into the output) was caught. I did not open any transcript body and printed none.
- Self-authored instrument: `test_construction_metrology.py` (1289 lines) was written by the phase it judges. Mitigated by the mutants above (24 single mutants run: 21 caught, 3 survived: E, E2 each alone because the two signals are redundant, and J; E and E2 together are caught); it has not been audited by an independent party.
- The live sample is shaped by the origin policy: 133 of 218 turns are SKIPPED_BY_POLICY, leaving 85 human-origin turns per metric; the record does not say what produced the other 133 starts.
- Hostile reading of the numbers: the live percentiles (for example TTFUR p50 15.53 s over 80 measured turns) are timings of this host's own sessions, including this mission's, with TTVD a proxy and TTFMC definition unconfirmed. They are not a performance claim or a statement about the laptop.

## Unknowns and risks (WARNING, none blocking)

1. **LP-04, definitions PROPOSED.** The goal "the time a construction takes is measured" is met for these three operational definitions. Whether they match what the Owner calls TTFMC, TTFUR and TTVD is unknown on this host. The contract names the main alternative reading of TTFMC (time to first model content).
2. **LP-05, laptop distribution absent.** The report runs on any transcript root and labels the plane, but no laptop run exists; the complaint is about the laptop. Procedure and falsifier are written in the contract section 8.
3. **LP-06, TTVD is a proxy.** First ok Bash result after a change. Not a measure of verification until the Owner authorises reading command text in memory.
4. **DORMANT unit.** Measured but not consumed by anything; Phase 5 is the planned consumer.
5. **Single capped sample.** 200 of 4576 files (about 4%); the stores grew between planning and the run; a second run would be a different population. p95 of TTFMC and TTVD is UNJUDGED.
6. **Test-strength gap (mutant J) and redundant-signal survivors (E, E2)**, described above.

---

_Verified: 2026-11-23T00:30:00Z_
_Verifier: Claude (gsd-verifier)_
