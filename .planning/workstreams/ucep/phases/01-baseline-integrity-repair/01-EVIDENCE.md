# Phase 1 Evidence: Baseline integrity repair (UCEP-01)

Observed output is copied verbatim from the plan SUMMARYs and from the Phase gate run of plan 01-05. Verdict words are only PROVEN / OBSERVED / UNJUDGED / BLOCKED, never upgraded.

## 1. Scope

- Requirement: UCEP-01. Workstream `ucep`, phase `01-baseline-integrity-repair`, plans 01-01 .. 01-05.
- Worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ucep`, branch `ucep/mission` (the worktree was cut from `581371d`; the recorded start of Phase 1 work, from 01-01-SUMMARY, is BASE below).
- BASE (start of 01-01, `plan_head_before`) = `07f04424919933fcbcf20e3896441f204e072219`. Code HEAD at the phase-gate run = `232836ce2ba00c3ed9a9dbbf3040411563ffdbbf` (01-05 Task 1). Docs commits (this file, the 01-05 SUMMARY) follow it and change no code.
- ROADMAP Phase 1 success criteria (S1 .. S5), as worded in ROADMAP.md:
  - S1 `ratchet.reanchor` writes ONE REANCHORED generation per family, refuses unless the new origin is VERIFIED; the 9 QUOTE_MISSING entries re-anchored to PP skills (`persistent_state/B1.json`, `wii_homebrew/B1.json`).
  - S2 `ratchet.diff` covers `why`/`origin`/`class`/`propagation_scope`; an unanchored child is not ok; authority comes from an allowlist; probe attacks H1/H2/H3b go red, controls stay green.
  - S3 donegate: N/A needs a closed-vocabulary reason and a share cap; `test:` checks never executed on any hook path, report UNJUDGED counted apart from VIOLATED; H5/H6 no longer pass.
  - S4 `test_tower_ratchet.py` and `test_baseline_generations.py` discover subjects by walking `BASELINES_DIR` (nested axes included) with a population floor.
  - S5 the four named tests PASS and B0 + web_surface B1 sha256 are unchanged (before/after recorded).
- Decisions cited: D-01 reanchor, D-02 the 9 origins, D-03 diff/unanchored/allowlist, D-04 donegate (01-02..01-04); D-05 discovery and D-06 immutability (01-05); D-07 discretion choices (section 5).

## 2. Criterion by criterion

Gate of record: one bracketed run at HEAD `232836ce`, drivers run Python directly from the worktree root (no `timeout` wrapper). Commands are `python tools/<file>.py`, rc is the process exit code.

| criterion | command(s) | exit | observed line(s) | verdict |
|---|---|---|---|---|
| S1 reanchor + 9 entries re-anchored | `test_ucep_baseline_integrity.py` (V-UCEP-REANCHOR-*, V-UCEP-REAL-REANCHORED); `test_baseline_generations.py` | 0 / 0 | `UCEP_BASELINE_INTEGRITY_PASS=33/33`; `V-UCEP-REAL-REANCHORED PASS ... both families [0, 1], the 9 ids REANCHORED by an allowlisted authority, every active entry VERIFIED, chains ok, B0 bytes = F0 blobs`; `BASELINE_GENERATIONS_PASS=16/16` | OBSERVED |
| S2 ratchet H1/H2/H3b | `test_ucep_baseline_integrity.py` (V-UCEP-H1-*, H2-*, H3B, ALLOWLIST, CLI-UNANCHORED + controls); `test_tower_ratchet.py` | 0 / 0 | `UCEP_BASELINE_INTEGRITY_PASS=33/33`; `TOWER_RATCHET_PASS=21/21` | OBSERVED |
| S3 donegate H5/H6 | `test_ucep_donegate_exits.py`; `test_tower_donegate.py`; `test_tower_checks.py` | 0 / 0 / 0 | `UCEP_DONEGATE_EXITS_PASS=13/13`; `TOWER_DONEGATE_PASS=10/10`; `TOWER_CHECKS_PASS=23/23`; `git diff --quiet 07f04424..HEAD -- modules/tower/checks.py tools/test_tower_checks.py modules/gsd_x/cli.py` rc=0 | OBSERVED (module level; hook/production path UNJUDGED, section 9) |
| S4 discovered subjects | `test_ucep_baseline_integrity.py` (V-UCEP-DISCOVER-*); `test_tower_ratchet.py`; `test_baseline_generations.py` | 0 / 0 / 0 | `V-UCEP-DISCOVER-REAL PASS 4 subjects, 62 active entries, floor 4/60`; `V-TRAT-REAL-CHAINS PASS 4 discovered subjects verified clean (floor 4): ['kobiicraft_mode', 'persistent_state', 'web_surface', 'wii_homebrew']`; `V-BGEN-REAL-B0-CITATIONS-HOLD PASS 62 stored entries over 4 discovered subjects hold (floor 4/60; 14 moved: ...)` | OBSERVED |
| S5 four named tests + immutability | `test_baseline_generations.py`, `test_tower_ratchet.py`, `test_tower_donegate.py`, `test_family_baselines.py`; sha256 + `git log` over the 5 files | 0 each | `BASELINE_GENERATIONS_PASS=16/16`, `TOWER_RATCHET_PASS=21/21`, `TOWER_DONEGATE_PASS=10/10`, `FAMILY_BASELINES_PASS=20/20`; all five files EQUAL (section 4); `git log --format=%h 07f04424..HEAD --` over the 5 paths printed nothing | OBSERVED |

Regression files in the same run, all rc=0: `TOWER_SELECT_PASS=15/15`, `TOWER_CAPSULE_PASS=16/16`, `TOWER_INHERITANCE_PASS=16/16`, `FINJ_PASS=23/23`, `TOWER_O4_PASS=7/7` (prints `CLAIM NOT PROVEN (b)` by design). Zero `FAIL` lines in any of the 12 files.

Brackets of the gate run:

- Sorted dirty-path SET BEFORE = AFTER (equal): ` M .planning/workstreams/ucep/STATE.md`, `?? .gsd/`, `?? .planning/workstreams/ucep/milestone.lock`, `?? .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-05-SUMMARY.md`, `?? .planning/workstreams/ucep/state.json`. The first, second, third and fifth are orchestrator-owned; the SUMMARY is plan 01-05's own.
- Production tower ledger `C:\Users\User\.claude\state\tower`: 1561 files before, 1562 after. NOT equal. Two paths moved: `consumption.jsonl` (786857 -> 789003 bytes, one appended line) and the new `offers\40c82043-6c42-4a1d-bbcc-8136a2992bbf_family-persistent_state.count`, both at 12:02:24. The appended line carries `"sid": "40c82043-6c42-4a1d-bbcc-8136a2992bbf"`, `"kind": "family"`, `"family": "persistent_state"`; the same sid appears earlier in that file with `"repo": "...\\Cursor Projects\\TUA-X"`: a live session in another repo. Control: the ledger path derives from `os.path.expanduser("~")` (`modules/tower/capsule.py:50,79`), so the 12 files were re-run with the outer HOME/USERPROFILE on an empty temp dir: all 12 rc=0 with the same `_PASS` lines, 0 files created under `<temp>/.claude/state/tower`, production ledger new=0 changed=0 across that run.
  - The plan's literal rule ("listing changed => a test wrote the ledger => BLOCKED") is not met on this host because the ledger has concurrent live writers. I attributed the delta by row content and did not record BLOCKED. This is a deviation from the plan's wording; the orchestrator may overrule it. No test-origin row was found.
- The control run also showed one file created under the temp HOME by the suite: `<temp>/.claude/state/gsd-x-heartbeat.json` (`modules/gsd_x/heartbeat.py:32`). It is outside the tower ledger and pre-dates this phase; which suite file triggers it was not isolated. Recorded as an open item (section 7).

## 3. RED records (the runs that failed first)

Each RED run was made on unchanged code before its fix. The harness predicates already state the fixed behaviour, so a later green is evidence.

| attack / gate | RED line (verbatim) | RED at | fixed by | source |
|---|---|---|---|---|
| H1 raw + H1 API, H2 (4 kinds), H3b | `UCEP_BASELINE_INTEGRITY_PASS=5/12  threshold=12/12` (7 attack gates FAIL with `'ok': True`; 5 controls PASS) | HEAD `acc61048` (harness commit; ratchet.py unchanged) | 01-03 commits `1b087de0`, `c06e28ed`, `630b993c` | 01-01-SUMMARY |
| CLI-UNANCHORED (H3b at the CLI) | `UCEP_BASELINE_INTEGRITY_PASS=5/13  threshold=13/13`; `FAIL V-UCEP-CLI-UNANCHORED  unanchored rc=0 out='web_surface chain: OK (generations [0, 1])\n'` | before `1b087de0` | `1b087de0` | 01-03-SUMMARY |
| H2 (why/origin/class/scope) | harness `7/13`, the four `V-UCEP-H2-*` attacks FAIL with `'ok': True`, control PASS | before `c06e28ed` | `c06e28ed` | 01-03-SUMMARY |
| ALLOWLIST (H1) | `UCEP_BASELINE_INTEGRITY_PASS=11/14  threshold=14/14`; `FAIL V-UCEP-H1-RAW`, `FAIL V-UCEP-H1-API`, `FAIL V-UCEP-ALLOWLIST` | before `630b993c` | `630b993c` | 01-03-SUMMARY |
| H6 (`test:` that fails) | `UCEP_DONEGATE_EXITS_PASS=6/8  threshold=8/8`; `FAIL V-UCEP-H6-TEST-UNJUDGED ... 'verdict': 'DELEGATED' ... 'would_block': False`, `FAIL V-UCEP-REPORT-COUNTS` | HEAD `33a01501` (donegate.py unchanged) | `d0064ee7` | 01-02-SUMMARY |
| H5 (all N/A, free text) | `UCEP_DONEGATE_EXITS_PASS=11/13  threshold=13/13`; `FAIL V-UCEP-H5-FREE-TEXT ... {'verdicts': [('NOT_APPLICABLE', None)], 'would_block': False}`, `FAIL V-UCEP-H5-OVER-CAP` | HEAD `d0064ee7` | `84e77499` | 01-02-SUMMARY |
| reanchor (existence) | `UCEP_BASELINE_INTEGRITY_PASS=14/17  threshold=17/17`; `FAIL V-UCEP-REANCHOR-ONE-GENERATION ... AttributeError: ratchet.reanchor does not exist` | HEAD `eabac68e` | `e39d67c1` | 01-04-SUMMARY |
| reanchor refusals + real tree | `UCEP_BASELINE_INTEGRITY_PASS=23/28  threshold=28/28`; FAIL `V-UCEP-REANCHOR-REFUSES-CHANGED-QUOTE`, `-RELATIVE-PATH`, `-WORKTREE-PATH`, `-NOOP`, `V-UCEP-REAL-REANCHORED` | HEAD `694f5a24` | `d5fd2ae4`, then data `994fe560` | 01-04-SUMMARY |
| discovery | `UCEP_BASELINE_INTEGRITY_PASS=28/33  threshold=33/33`; FAIL `V-UCEP-DISCOVER-NESTED`, `-EMPTY`, `-RESIDUE`, `-CALL-TIME`, `-REAL` (`baselines.discover_subjects does not exist`) | HEAD `4fa22d84` | `232836ce` | 01-05-SUMMARY |

Also on record for 01-05: the floor's red branch (an empty walk and a three-subject walk make `V-TRAT-REAL-CHAINS` and `V-BGEN-REAL-B0-CITATIONS-HOLD` FAIL, population 0 and 47) and the positive control (a planted nested subject `archetype/PLANTED` with a missing-file origin and a mismatched parent anchor makes both gates FAIL, naming `archetype/PLANTED`, population 63) are in the 01-05-SUMMARY, run with throwaway drivers that are not committed.

The probe `wiki/tools/cbr_probe.py` is NOT used for the ratchet. Reason (RESEARCH F3): after web_surface B1 landed, its H1/H2/H3b cases read the real B0+B1 directory, so they read `ok=False` for a different reason (the second generation's own additions). The authoritative ratchet evidence is the harness gates, which run on a B0-only temp copy or synthetic roots, plus the RED records above. Secondary note: at HEAD the unmodified probe now stops with rc=1 at its P4 section, before P5, because the allowlist refuses its `authority="x"` promote (`RatchetRefusal: authority 'x' is not on the allowlist ('Owner',)`). Loading it with `runpy` and calling the two functions directly gave: P4 raised `RatchetRefusal`; `H5 every entry declared N/A with reason 'n/a': would_block=True {'UNJUDGED': 17}`; `H6 test:<file> whose only test fails: verdict=UNJUDGED would_block=True`. The probe file itself was not edited.

## 4. Immutability (D-06)

BEFORE column = git blob sha256 at BASE (`git show HEAD:<path>`, F0 column of 01-01-SUMMARY; the working copies were CRLF before the 01-01 LF pin, only line endings changed on disk). AFTER = on-disk sha256 at the gate run.

| file | BEFORE blob sha256 | AFTER sha256 | equal |
|---|---|---|---|
| vault/tower/baselines/kobiicraft_mode/B0.json | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | yes |
| vault/tower/baselines/persistent_state/B0.json | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | yes |
| vault/tower/baselines/web_surface/B0.json | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | yes |
| vault/tower/baselines/web_surface/B1.json | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | yes |
| vault/tower/baselines/wii_homebrew/B0.json | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | yes |

`git log --format=%h 07f04424..HEAD -- <the 5 paths>` printed nothing. The only baseline files added since BASE are `vault/tower/baselines/persistent_state/B1.json` and `vault/tower/baselines/wii_homebrew/B1.json` (01-04).

Scope hygiene at the gate (`git diff --name-status 07f04424..HEAD`): `M .gitattributes`; `A` 01-01..01-04 SUMMARY and `01-reanchor-map.json`; `M modules/tower/{baselines,donegate,ratchet}.py`; `M tools/{family_baseline,test_baseline_generations,test_tower_donegate,test_tower_ratchet}.py`; `A tools/test_ucep_baseline_integrity.py`, `A tools/test_ucep_donegate_exits.py`; `A` the two B1 files. No `A` under `modules/`; `checks.py`, `test_tower_checks.py`, `gsd_x/cli.py` unchanged; `ukdl-universal.md`, `liveness_report.md`, `.planning/STATE.md`, `modules/sdd_os/` absent from the diff. Because no module was added, no liveness entry is due and `reachability.py` was not run (and `--baseline` was never run).

## 5. Discretion choices (D-07)

- `NA_REASONS` (`modules/tower/donegate.py`): 12 kebab-case tokens, each naming a structural fact about the entry's subject that a reviewer can check (`no-persistent-state`, `single-actor`, `no-bulk-operation`, `no-destructive-operation`, `not-distributed`, `no-external-effect`, `not-scheduled`, `no-money`, `single-policy-layer`, `no-user-interface`, `platform-not-targeted`, `superseded-by-entry`). "out of scope for this change" is excluded on purpose: it defers the work instead of stating a fact about the subject, and is the excuse this mission exists to stop. A comment beside the tuple says so without quoting the phrase as a token.
- `NA_SHARE_CAP_PERCENT = 30`, allowed claims `(30 * n) // 100` over active entries, integer arithmetic. The real families have 15-17 entries and admit 4-5 N/A claims. Consequence for small families: fewer than 4 active entries admit no N/A at all (fail-closed, accepted as T-01-09, documented in the module docstring). Over the cap, every valid claim is voided, not the excess, because choosing which claims count would itself be gameable.
- `AUTHORITIES = ("Owner",)` as a code constant in `modules/tower/ratchet.py`, matched on the first token (split on whitespace, `:`, `(`, `,`, `;`), case-sensitive, so the real `promoted_by` form `Owner (approved 'both', 2026-10-01)` passes while `Ownerx`, `owner`, `Bot Owner`, `Owner's cat`, `x`, blank and `None` do not. A code constant rather than a data file keeps tests hermetic and the list is not writable by whoever writes generations.
- No minimum reason length: existing gates use `reason="new"` and `--reason gone`, which a length floor would break, and a forger picks the reason string anyway. The allowlist on authority is the check that bites.
- Origin root per family for the reanchor (01-04): the PP **main checkout** `C:\Users\User\.claude\skills\claude-power-pack\skills\<skill>\SKILL.md`, read-only, for both families; the home-fallback path was not needed. Every id was VERIFIED at that candidate:

| family | id | skill | line |
|---|---|---|---|
| persistent_state | persistent_state-destructive-op-authorizes-exact-state-seen | destructive-state-authorization | 13 |
| persistent_state | persistent_state-destructive-identity-falsification-test | destructive-state-authorization | 26 |
| persistent_state | persistent_state-absence-of-identity-refuses | destructive-state-authorization | 42 |
| persistent_state | persistent_state-precondition-window-must-be-closed | destructive-state-authorization | 82 |
| persistent_state | persistent_state-batch-reauthorize-per-item | destructive-state-authorization | 109 |
| persistent_state | persistent_state-monetary-qualifiers-travel-with-amount | monetary-quantity-integrity | 15 |
| persistent_state | persistent_state-monetary-conflicting-qualifiers-refuse | monetary-quantity-integrity | 26 |
| persistent_state | persistent_state-monetary-no-conversion-without-authorized-source | monetary-quantity-integrity | 37 |
| wii_homebrew | wii_homebrew-claim-must-name-observing-plane | develop-here-prove-there | 14 |

- `reanchor` stores the old quote verbatim and refuses a changed or empty quote, a relative path, a path under `/.claude/worktrees/`, a no-op, an unknown or reverted id, a non-allowlisted authority; all-or-nothing. A provenance move cannot launder a changed rule text.
- Discovery floors (D-05): at least 4 subjects, at least 60 active entries for the citation gate (62 today). The four family ids are NOT required by name (that would bring the tuple back); the floor is on population.

## 6. Assumptions needing Owner review (recorded, not asked mid-run)

These are Owner-review items. None of them is an Owner confirmation.

- **A1** (verbatim from 01-04-SUMMARY): "Assumption A1 (RESEARCH, stated for 01-05 EVIDENCE as an Owner-reviewable assumption): the Owner's approved plan of record is the Owner's authority for this re-anchoring, so the real writes carry `Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)`. Both writes are append-only and supersedable by a later reanchor/revert." Concretely: the `authority` recorded on `persistent_state/B1.json` and `wii_homebrew/B1.json` is `Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)`. It relies on the Owner-approved plan of record; the Owner did not personally issue those two writes. Owner review item: confirm that this authority string is acceptable, or supersede the two generations by a later reanchor/revert.
- **A2** vocabulary and cap values: the 12 `NA_REASONS` tokens and `NA_SHARE_CAP_PERCENT = 30` are my choice (section 5). A wrong cap blocks legitimate N/A; both are constants pinned by `V-UCEP-H5-*` gates and cheap to change. Owner review item.
- **A3** the main-checkout skill path (a live tree on another branch) as the long-term origin of 9 entries. It is read-only and tracked there, but it is another session's working tree: its branch can change or move those lines, and the citation gate would then say so (QUOTE_MISSING or MOVED). Owner review item: keep, or pin to a stable path.
- **A4** the `.gitattributes` EOL pin `vault/tower/baselines/** text eol=lf` (01-01) as the fix for the CRLF anchor mismatch, instead of a CRLF-insensitive `generation_sha256`. The pin was applied and on-disk bytes normalised only after each LF hash equalled its blob hash. Owner review item.

## 7. Known limits and open items (not closed by Phase 1)

Limits:
- A forger who recomputes `parent_sha256` after hollowing both generations is undetectable at file level; repo history is the root of trust (stated in the code comment above `AUTHORITIES`).
- Whoever edits `modules/tower/ratchet.py` controls the allowlist.
- `registry:` checks stay DELEGATED and non-blocking.
- No production caller of `donegate.judge` exists until Phase 6; enforcement stays REPORT-ONLY.
- The `cli.py` delivered sentence is deferred to Phase 6 per CONTEXT.
- Fewer than 4 active entries admit no N/A (T-01-09).

Open items for a later phase:
- **14 MOVED citations.** `V-BGEN-REAL-B0-CITATIONS-HOLD` reports 14 entries as MOVED (pre-existing, tolerated: the quote still exists in the cited file at a different line). Reported first in 01-04-SUMMARY, listed here from a discovery run at HEAD: kobiicraft_mode (10): `kobiicraft_mode-async-io`, `-golden-run-e2e`, `-gui-state-via-pdc`, `-ingame-verifier-fail-closed`, `-inventory-open-close-tick-delay`, `-no-heavy-ops-in-onenable`, `-observability-without-ssh`, `-p3-player-experience-required`, `-wiring-check-every-command`, `-zero-stubs-nd7`; web_surface (4): `web_surface-cdio-review-gate`, `-effect-keeps-http-status`, `-mobile-first-check`, `-ui-verified-on-production-build`; persistent_state 0, wii_homebrew 0. Nothing was re-anchored for these in Phase 1 (the plan bound was the 9 QUOTE_MISSING). The gate tolerates MOVED; `reanchor` requires VERIFIED.
- **Probe regression.** `wiki/tools/cbr_probe.py` aborts at P4 on the allowlist refusal (section 3), so its P5 lines are unreachable when run as a script. The probe was not edited (outside this plan's files).
- **Ledger concurrency.** The strict before/after listing-equality check of `~/.claude/state/tower` cannot hold while other sessions write it (section 2). A later phase that wants that bracket should key it on rows carrying its own sid, or on a temp HOME as done in the control.
- **Heartbeat write.** One suite file writes `gsd-x-heartbeat.json` under `HOME/.claude/state` (outside the tower ledger); the writer file was not isolated.

## 8. Owner queue

Phase 1 changes no live hook, no `~/.claude/` file, no `settings.json`, no `CLAUDE.md`, no rules file. No Owner mirror step is due from Phase 1. (The review items of section 6 are not mirror steps.)

## 9. Production Reality verdict

PROVEN is reserved for behaviour exercised on the live production path. Phase 1 is repair of repo-local gate code and two repo-local baseline generations on an unmerged branch (`ucep/mission`, pushed to origin by the orchestrator); no live hook path is changed. So no component below is PROVEN.

| component | verdict | basis |
|---|---|---|
| Baseline chain and citations on the real baselines, in this worktree | OBSERVED | real data, real tests, unmerged branch: `TOWER_RATCHET_PASS=21/21`, `BASELINE_GENERATIONS_PASS=16/16`, 62 entries over 4 discovered subjects |
| Ratchet hardening (H1/H2/H3b) | OBSERVED | RED on unfixed code (`5/12`, `5/13`, `7/13`, `11/14`), GREEN after (`UCEP_BASELINE_INTEGRITY_PASS=33/33`), controls green throughout |
| `ratchet.reanchor` and the two real generations | OBSERVED | refusal matrix RED then GREEN; `V-UCEP-REAL-REANCHORED` PASS; authority rests on assumption A1 (Owner-review item, not Owner confirmation) |
| Donegate exits (H5/H6), module level | OBSERVED | `UCEP_DONEGATE_EXITS_PASS=13/13`, `TOWER_DONEGATE_PASS=10/10`; `would_block` is reported, nothing enforces |
| Donegate on any hook or production path | UNJUDGED | no caller of `donegate.judge` until Phase 6 |
| Subject discovery in the two real-tree gates | OBSERVED | real tree 4 subjects / 62 entries; floor red branch and planted nested subject driven, throwaway drivers (SUMMARY) |
| Live `family_block` stamp change for persistent_state and wii_homebrew in real sessions | UNJUDGED | branch not merged, no live session exercised the new generations |
| Production-ledger hygiene of the suite | OBSERVED | delta attributed to a foreign live session; temp-HOME control wrote no ledger row; the plan's literal "listing changed => BLOCKED" was not applied (section 2) |
| Overall Phase 1 | OBSERVED | no earlier SUMMARY recorded a BLOCKED criterion, so none is carried forward |

## 10. Handoff

```
PANE: ucep / mission worktree (GSD executor 01-05)
SPRINT: Phase 1 baseline-integrity-repair, plans 01-01..01-05
STATUS: COMPLETE (OBSERVED; PROVEN none; UNJUDGED: donegate hook path, live family_block stamp)
LIVE: 232836ce (last code commit on ucep/mission; docs commits follow, pushed by the orchestrator)
NEXT: Owner review of A1-A4; Phase 2 capability subject and archetypes
DEBT: 14 MOVED citations; cbr_probe P4 abort; ledger-bracket method; gsd-x-heartbeat writer unidentified
```

## 11. Addendum 2026-10-03 (orchestrator, after code-review fixes; sections 1-10 above are kept as written at 232836ce)

Superseding facts at HEAD 0939d27b (pushed to origin/ucep/mission):
- Review `01-REVIEW.md` (0 critical / 7 warning / 3 info) fixed WR-02..WR-07 and IN-01 (commits 8ddb5b0b, a3b35fd6, b1732af7, 6c6835f6, 099a6579, 1ba16a61, 66556c06); WR-01 comment-only (cc61c551), binding the authority deferred to Phase 3; IN-02 and the IN-03 reason-mapping half deferred.
- Gate counts now (CLAUDE_STATE_DIR on a temp dir, all rc=0, re-run independently by the orchestrator and by the verifier): BASELINE_GENERATIONS 18/18, TOWER_RATCHET 21/21, TOWER_DONEGATE 10/10, FAMILY_BASELINES 20/20, UCEP_BASELINE_INTEGRITY 40/40, UCEP_DONEGATE_EXITS 17/17, TOWER_SELECT 15/15, TOWER_CHECKS 23/23, TOWER_CAPSULE 16/16, TOWER_INHERITANCE 17/17, FINJ 24/24, TOWER_O4 7/7, GSD_X_HEARTBEAT_PATH 7/7 (new). Liveness gate: 63 offenders / 486 rows, unchanged.
- CORRECTION to section 9: "no live hook path is changed in Phase 1" is no longer true. Fix 1ba16a61 changed `modules/gsd_x/heartbeat.py` (path resolved per call, same formula; module no longer raises at import without a home). Behaviour-preserving by 7/7 gates; never run in a live session -> Production Reality for that change is UNJUDGED. Live sessions run the main checkout's copy until this branch is merged, so nothing live changed yet.
- WR-07 commit message cites a real-HOME heartbeat bracket as proof; that bracket is confounded by other live sessions writing the same file. The decisive evidence is the RED/GREEN temp-state-dir gates (see 01-REVIEW.md).
- Verification `01-VERIFICATION.md`: status passed, 5/5. A1 accepted as a disclosed assumption, still on the Owner-review list.
- Overall Phase 1 verdict unchanged: OBSERVED; PROVEN none; UNJUDGED: donegate hook path, live family_block stamp, live heartbeat.py.