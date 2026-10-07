# 01-FIX-RECEIPT -- CR-01, WR-01, WR-02 + phase 1 verification

plane: gex44. Authority and envelope: per 01-FIX-PACKET.md. No push, no GSD commands, no Phase 2.

## Commits (pathspec, prefix `ao-p1fix:`)
- d0700cbe CR-01 -- population refuses a bad or date-only --until
- 9cb5e319 WR-01 -- non-OSError on one transcript is that file's typed error, refresh continues
- ae720bcb WR-02 -- only a file read from byte 0 can define a launch root
- (this receipt + 01-VERIFICATION.md: the commit that adds them)

Files touched: `tools/usage_index.py`, `tools/test_usage_index_v5.py`, `01-VERIFICATION.md`, `01-FIX-RECEIPT.md`.

## RED then GREEN
CR-01 (RED, unfixed):
```
FAIL V-UX5-UNTIL-DATE-ONLY-REFUSED: --until 2026-09-01: exit=0 verdict=MEASURED until=None reasons=[]
FAIL V-UX5-UNTIL-GARBAGE-REFUSED: --until garbage: exit=0 verdict=MEASURED reasons=[]; population(until=object()) -> CRASH ProgrammingError
PASS V-UX5-UNTIL-VALID-CONTROL ... exit=0 verdict=MEASURED calls=2
USAGE_INDEX_V5_PASS=72/74
```
CR-01 (GREEN):
```
PASS V-UX5-UNTIL-DATE-ONLY-REFUSED: --until 2026-09-01: exit=3 verdict=UNMEASURED until=2026-09-01 reasons=['until is not an ISO instant']
PASS V-UX5-UNTIL-GARBAGE-REFUSED: ... exit=3 verdict=UNMEASURED ...; population(until=object()) -> UNMEASURED
PASS V-UX5-UNTIL-VALID-CONTROL ... exit=0 verdict=MEASURED calls=2
USAGE_INDEX_V5_PASS=74/74
```
WR-01 (RED):
```
FAIL V-UX5-POISON-FILE-CONTINUES: non-OSError on one file: status=FAILED good file calls=3/3 poison rows left=0 files.error=None offset=None files_with_errors=None; population verdict=MEASURED reasons=[]
USAGE_INDEX_V5_PASS=74/75
```
WR-01 (GREEN):
```
PASS V-UX5-POISON-FILE-CONTINUES: ... status=OK good file calls=3/3 poison rows left=0 files.error='InterfaceError: ...' offset=0 files_with_errors=1; population verdict=UNMEASURED reasons=[... '1 in-scope file(s) carry a file error (unreadable transcript)']
```
Side effect: V-UX5-CRASH-RESUME asserted the old contract (`status == FAILED` for a mid-file crash). It went red under the new contract and I restated it: status OK, `files_with_errors == 1`, the crashed file keeps only its files row carrying the typed error, other rows 0, next refresh equals the one-shot build. Its intent (rollback + convergence) is unchanged. Flagging as a test edit you may want to look at.

WR-02 (RED):
```
FAIL V-UX5-LEGACY-GROWN-NO-LAUNCH-ROOT: legacy file grown from offset 653 with a new cwd: registry roots=['C--Users-User-Apps-beta', 'C--Users-User-Apps-gamma'] (want only the byte-0 control C--Users-User-Apps-gamma); homes of the grown session=[('...alpha','...alpha','SL')]
USAGE_INDEX_V5_PASS=75/76
```
WR-02 (GREEN):
```
PASS V-UX5-LEGACY-GROWN-NO-LAUNCH-ROOT: ... registry roots=['C--Users-User-Apps-gamma'] ...; homes of the grown session=[]
USAGE_INDEX_V5_PASS=76/76
```

## Full suite (tail per command)
```
test_usage_index.py            exit 0  USAGE_INDEX_PASS=22/22
test_usage_index_v5.py         exit 0  USAGE_INDEX_V5_PASS=76/76   (--drill: killed=18/18, clean rerun 76/76)
test_usage_index_identity.py   exit 0  USAGE_INDEX_IDENTITY_PASS=11/11
test_estate_shadow.py          exit 1  ESTATE_SHADOW_PASS=10/11   (baseline-identical)
test_fanout_ledger.py          exit 0  17/17
test_root_progress.py          exit 0  11/11
test_spawn_outcomes.py         exit 0  24/24
test_spawn_policy_v2.py        exit 0  26/26
test_async_spawns.py           exit 0  12/12
test_goal_journey.py           exit 0  7/7
test_execution_shape.py        exit 0  14/14
test_displacement.py           exit 0  16/16
test_store_identity_consumers  exit 0  12/12
test_frontier_intelligence_os  exit 1  FIOS_ACTIVATION_PASS=48/49  DATASET_FAMILY_VERDICT=FAIL (baseline-identical)
test_token_ground_truth_junct. exit 1  FileNotFoundError 'cmd' (baseline-identical)
test_incremental_cognition_program.py --generation 2 --selftest  exit 0  ICP_GEN2_SELFTEST=PASS
```
The done_gate "every command exit 0" is therefore NOT met: 3 commands exit 1, each the same as recorded in 01-BASELINE.md before Phase 1, none touched by these changes. I did not fix them (out of scope).

## UNKNOWN
- Whether the surrogate-in-cwd case from the review actually raises in SQLite binding (the WR-01 gate injects `sqlite3.InterfaceError`; the real trigger was not executed).
- Criterion 4 (refresh cost) not re-measured; carried from 01-EVIDENCE.md.
- Verdict in 01-VERIFICATION.md is GAPS (the 3 pre-existing red consumer commands, criterion 4 not re-run).
