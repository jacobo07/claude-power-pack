# Phase 2 Evidence: Capability subject and archetypes (UCEP-02)

Observed output is copied verbatim from the plan SUMMARYs and from the phase gate run of plan 02-05 (log of that run: sections 2 and 4). Verdict words are only PROVEN / OBSERVED / UNJUDGED / BLOCKED. PROVEN needs behaviour on the live production path, and Phase 2 has none, so no row below reads PROVEN.

## 1. Scope

- Requirement: UCEP-02. Workstream `ucep`, phase `02-capability-subject-and-archetypes`, plans 02-01 .. 02-05.
- Worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ucep`, branch `ucep/mission`, not pushed.
- PHASE2_BASE (the `head` value of `02-liveness-before.json`, written before any Phase 2 code) = `409dca8977d08a885d872745bda62d5ec479f75f`. Code HEAD at the phase-gate run = `9f3f38a0` (02-05 Task 2). The docs commits that carry this file and the 02-05 SUMMARY follow it and change no code.
- ROADMAP Phase 2 success criteria, as worded in ROADMAP.md:
  - C1 `modules/capability_runtime/archetypes.py`: traits (persistent, multi_actor, bulk, destructive, distributed, external_effect, scheduled, money, policy_layers, ui) and archetypes as trait conjunctions; family and archetype are independent outputs.
  - C2 Structural traits come from a cache keyed by repo root + cheap fingerprint, computed OFF the prompt path; the prompt path only reads it [G4]. Cache miss -> traits UNJUDGED, never absent.
  - C3 Intent-only traits carry fact state EXTRACTED and can yield at most CONDITIONAL, never REQUIRED [G16].
  - C4 `tools/test_capability_archetypes.py`: vocabulary-overlap negative control, intent-only control, trait-transition (ephemeral->persistent, local->distributed) recompiles differently, positive controls per archetype.
- Decisions (defined in 02-01-PLAN.md `<objective>`) and the plan that implemented each:

| id | statement | implemented in |
|---|---|---|
| D-01 | owner is `modules/capability_runtime`, new `archetypes.py`, reuse the matcher, no parallel authority | 02-01 (vocabulary imported from `modules.tower.families`, `_spans` parity-gated in 02-02) |
| D-02 | ten traits, archetypes are trait conjunctions, family and archetype independent; modifiers raise consequence and never create or change strength | 02-01 (shape), 02-02 (orthogonality gates), 02-05 (`modifiers_for`, `V-ARCH-TRANSITION-DISTRIBUTED`) |
| D-03 | anti-triggers demote, never veto | 02-02 (`V-ARCH-DEMOTE-NOT-VETO`) |
| D-04 | no archetype from vocabulary alone | 02-02 (`V-ARCH-NOUN-ONLY-NEG`, `V-ARCH-VOCAB-OVERLAP-NEG`, `V-ARCH-DRILL-NOUN-LIST`) |
| D-05 | structural traits from a cache, produced off the prompt path, read-only on it, miss -> UNJUDGED [G4] | 02-01 (tracer), 02-03 (entitlement, honest absence), 02-04 (fingerprint, freshness, reader contract, CLI), 02-05 (`V-ARCH-CAUSES-REACHABLE`) |
| D-06 | intent-only is EXTRACTED and at most CONDITIONAL [G16] | 02-02 (`ceiling`, `V-ARCH-INTENT-ONLY-CAP`, `V-ARCH-DRILL-CEILING`) |
| D-07 | `tools/test_capability_archetypes.py` with the four control classes | 02-01 (harness), 02-02 (controls), 02-03 (positives), 02-05 (transitions) |
| D-08 | archetypes in code only, no baseline generation written | all plans; `vault/tower` byte-unchanged (section 4) |
| D-09 | discretion choices | 02-04 (freshness constants), section 6 |
| R-1 | structure-only evidence with no intent yields CONDITIONAL, not NONE | 02-02 (`ceiling`) |
| R-2 | `ARCHETYPES` in code is the sole conjunction authority | 02-01 |
| R-3 | calibration of the persistence signal against KobiiSports Resort is Phase 7 | 02-03 (`code-module` WEAK and provisional) |
| R-4 | hosting the `--all` producer is an Owner step | 02-01 (record), 02-04 (CLI built, not hosted) |
| R-5 | archetype ids are single path segments, `distributed` is a modifier | 02-01 (`ARCHETYPE_ID_RE`), 02-05 (modifier) |

- Plan-checker report: `02-PLAN-CHECK.md` (verdict ISSUES FOUND, 0 blockers, 4 warnings, 4 info). Resolution of each item as executed: F1 (budget_s=0 must cut deterministically) -> 02-03 compared `time.perf_counter()` with `>=` before each directory, pinned by `V-ARCH-BUDGET`; F2 (no-secret-read gate needed a positive control) -> 02-03 `V-TSCAN-NO-SECRET-READ` records `package.json` among the opens; F3 (CLI counter wrapped the wrong module object) -> 02-04 `V-ARCH-CLI-ALL-INJECTED` carries a positive control (`produce_all(None)` reaches a stubbed `find_repos` exactly once); F4 (RESEARCH open questions not marked RESOLVED) -> resolved in plan content as R-1..R-4 and `subject_root`, the RESEARCH heading itself was not edited; I2 (demoter control removes both phrases) -> 02-02 control; I3 (skip ignores cap and budget of the stored document) -> safe direction (UNJUDGED), the CLI always uses defaults.

## 2. Criterion by criterion

Gate of record: one bracketed run at HEAD `9f3f38a0` (start 2026-10-03T19:09:16Z, end 19:09:55Z), every driver run as Python directly from the worktree root. rc is the process exit code. The 11-file suite, in the order run:

| file | rc | observed line | FAIL lines |
|---|---|---|---|
| `test_capability_archetypes.py` | 0 | `CAPABILITY_ARCHETYPES_REAL_POLES=PASS` then `CAPABILITY_ARCHETYPES_PASS=59/59  threshold=59/59` | 0 |
| `test_capability_trait_scan.py` | 0 | `CAPABILITY_TRAIT_SCAN_PASS=27/27  threshold=27/27` | 0 |
| `test_family_baselines.py` | 0 | `FAMILY_BASELINES_PASS=20/20  threshold=20/20` | 0 |
| `test_family_injection.py` | 0 | `FINJ_PASS=24/24  threshold=24/24` | 0 |
| `test_tower_capsule.py` | 0 | `TOWER_CAPSULE_PASS=16/16  threshold=16/16` | 0 |
| `test_tower_inheritance.py` | 0 | `TOWER_INHERITANCE_PASS=17/17  threshold=17/17` | 0 |
| `test_tower_ratchet.py` | 0 | `TOWER_RATCHET_PASS=21/21  threshold=21/21` | 0 |
| `test_baseline_generations.py` | 0 | `BASELINE_GENERATIONS_PASS=18/18  threshold=18/18` | 0 |
| `test_tower_donegate.py` | 0 | `TOWER_DONEGATE_PASS=10/10  threshold=10/10` | 0 |
| `test_ucep_baseline_integrity.py` | 0 | `UCEP_BASELINE_INTEGRITY_PASS=40/40  threshold=40/40` | 0 |
| `test_ucep_donegate_exits.py` | 0 | `UCEP_DONEGATE_EXITS_PASS=17/17  threshold=17/17` | 0 |

Each file exited 0 with n == m. The Phase 1 counts (for example 40/40 and 17/17 here) are the observed values at this HEAD, not compared against Phase 1's earlier figures.

Mapping of 02-VALIDATION.md "Per-Task Verification Map" and of the ROADMAP criteria to gates (the gate names in the map match the names in the file):

| criterion | gates (all in `tools/test_capability_archetypes.py` unless noted) | command | exit | observed | verdict |
|---|---|---|---|---|---|
| C1 ten traits, conjunction archetypes, family orthogonal to archetype | `V-ARCH-TRAITS-TEN`, `-ID-SHAPE`, `-ARCHETYPES-THREE`, `-VOCAB-SHARED`, `-NA-BRIDGE`, `-NO-BARE-REQUIRED`, `-ORTHOGONAL-A`, `-ORTHOGONAL-B`, `-SUBJECT-SHAPE` | `python tools/test_capability_archetypes.py` | 0 | `CAPABILITY_ARCHETYPES_PASS=59/59`; `V-ARCH-VOCAB-OVERLAP-NEG PASS active=[] persistent=UNJUDGED AND classify_prompt('schema')=['persistent_state']`; `V-ARCH-SUBJECT-SHAPE PASS fresh, stale, missing and no-intent subjects: JSON-safe, nine keys, one entry per archetype (NONE listed), modifiers shaped` | OBSERVED |
| C2 off-path cache, read-only reader, miss -> UNJUDGED | `V-ARCH-MISS-UNJUDGED`, `-READ-ONLY`, `-STALE-MANIFEST`, `-STALE-EVIDENCE-FILE`, `-STALE-AGE`, `-STALE-DEEP-BLINDSPOT`, `-TRUNCATED`, `-BUDGET`, `-BLIND-ECOSYSTEM`, `-UNREADABLE-SUBTREE`, `-KEY-NORMALIZATION`, `-CACHE-OUTSIDE-REPO`, `-CACHE-PATH-SAFE`, `-HERMETIC-HOME`, `-CAUSES-REACHABLE`, `-CLI-*`, `-DRILL-ABSENT-ON-MISS`, `-DRILL-READER-SCAN`, `-DRILL-FP-IGNORES-MANIFEST`; `test_capability_trait_scan.py` (`V-TSCAN-*`) | the same, plus `python tools/test_capability_trait_scan.py` | 0 / 0 | `V-ARCH-READ-ONLY PASS walk=0 scan=0 produce=0 over 20 resolve calls (fresh, stale, missing); _HOME unchanged (90 paths); median=7.94 ms p95=16.32 ms; control saw walk=1 sca...`; `CAPABILITY_TRAIT_SCAN_PASS=27/27` | OBSERVED |
| C3 intent-only <= CONDITIONAL, EXTRACTED | `V-ARCH-INTENT-ONLY-CAP`, `-INTENT-CONTROL`, `-WEAK-CAP`, `-DEMOTE-NOT-VETO`, `-STRUCTURE-ONLY-CONDITIONAL`, `-DRILL-CEILING` | same | 0 | `V-ARCH-INTENT-ONLY-CAP PASS 12 assessments over 2 intent-only subjects x 2 prompts: all CONDITIONAL/intent/EXTRACTED, no basis=intent REQUIRED`; `V-ARCH-DRILL-CEILING PASS mutated ok=False calls=12 named_sub_assertion=True restored ok=True` | OBSERVED |
| C4 controls, transitions, positives | `V-ARCH-VOCAB-OVERLAP-NEG`, `-NOUN-ONLY-NEG`, `-TRANSITION-PERSISTENT`, `-TRANSITION-DISTRIBUTED`, `-POSITIVE-WORLD_MUTATION`, `-POSITIVE-EXTERNAL_EFFECT`, `-POSITIVE-BACKGROUND_JOB`, uncounted `V-ARCH-REAL-POLES` | same | 0 | see the three lines below the table | OBSERVED |
| liveness | `reachability.gate()` offender set by name | section 5 | 0 | `offenders 63 before 63 rows 488 new [] mine []` | OBSERVED |
| no side effects | dirty-path SET bracket, hermetic control, sha256 of the five generation files, `git diff` over `vault/tower` | section 4 | 0 | sets equal, listing empty, five EQUAL | OBSERVED |

C4 observed lines (gate of record):

```
PASS V-ARCH-TRANSITION-PERSISTENT   CONDITIONAL/intent->REQUIRED/structural+intent sig=a2e66bc6c0a0b8ea->81cb73f56317c09c fp1=c99107075e5f429b->25efd3479e2e5d8e STALE seen; twin dir equa...
PASS V-ARCH-TRANSITION-DISTRIBUTED  BACKGROUND_JOB REQUIRED [] -> REQUIRED ['distributed'] after a compose file (STALE seen), sig 9fc8c35e204f177a -> 625c080109a00c59; intent modifiers [...
PASS V-ARCH-CAUSES-REACHABLE        all 9 causes reachable (no-cache, stale, cache-malformed, unresolvable-root, truncated, budget-exhausted, unreadable-subtree, no-manifest-ecosystem, n...
```

The two signatures of `V-ARCH-TRANSITION-PERSISTENT` (`a2e66bc6c0a0b8ea` for the ephemeral subject, `81cb73f56317c09c` after `prisma/schema.prisma` and `@prisma/client` were added) were identical in the 02-05 Task 2 GREEN run and in the gate run, while the stored `fp1` differed between runs (`29558e5f7e564c32->8cfbe334dece8543` in the Task 2 run, `c99107075e5f429b->25efd3479e2e5d8e` in the gate run). The fingerprint depends on the temp directory; the signature does not.

Real-repo poles (the uncounted `V-ARCH-REAL-POLES` line of the gate run, verbatim, read-only `ts.scan(root, budget_s=60)`):

```
PASS V-ARCH-REAL-POLES InfinityOps (PASS; want persistent and external_effect PRESENT; held): files=4105 seconds=0.235 truncated=False budget_hit=False ecosystems=gradle,mix,npm,pip | persistent=PRESENT(dependency+marker) multi_actor=PRESENT(dependency) bulk=UNJUDGED(no-structural-detector) destructive=UNJUDGED(no-structural-detector) distributed=PRESENT(marker) external_effect=PRESENT(dependency) scheduled=PRESENT(dependency) money=PRESENT(dependency) policy_layers=ABSENT(no policy_layers evidence in a complete walk (ecosystems seen: gradle, mix, npm, pip)) ui=PRESENT(224 ui files) || ABSW2-Wii (PASS; want persistent not ABSENT; held): files=10127 seconds=0.289 truncated=False budget_hit=False ecosystems=- | persistent=UNJUDGED(no-manifest-ecosystem) multi_actor=UNJUDGED(no-manifest-ecosystem) bulk=UNJUDGED(no-structural-detector) destructive=UNJUDGED(no-structural-detector) distributed=UNJUDGED(no-manifest-ecosystem) external_effect=UNJUDGED(no-manifest-ecosystem) scheduled=UNJUDGED(no-manifest-ecosystem) money=UNJUDGED(no-manifest-ecosystem) policy_layers=UNJUDGED(no-manifest-ecosystem) ui=ABSENT(no ui evidence in a complete walk (ecosystems seen: none))
CAPABILITY_ARCHETYPES_REAL_POLES=PASS
```

Reading of that line: on InfinityOps `persistent` and `external_effect` are PRESENT as required. On ABSW2-Wii `persistent` reads UNJUDGED `no-manifest-ecosystem` (the repository has no manifest any parser knows), which satisfies "not ABSENT" and is the honest answer for a repository the producer cannot read; it does not read WEAK, so the plan's "(UNJUDGED or WEAK)" resolved to its UNJUDGED half. The line is not part of the 59 counted gates. A missing path would read UNJUDGED and never counts as a PASS; both paths existed on this host. KobiiSports Resort was not scanned (walk over 48 s; calibration is Phase 7, R-3).

## 3. RED records (the runs that failed first) and drills

Each RED run was made on unchanged implementation before its fix. Tasks marked "no RED run" had no implementation to precede: the drill is the red branch of its target gate.

| plan / task | RED line (verbatim) | RED at | turned green by | source |
|---|---|---|---|---|
| 02-01 T1 | `CAPABILITY_ARCHETYPES_PASS=1/5  threshold=5/5` (4 FAIL, only `V-ARCH-HERMETIC-HOME` PASS) | `98224610` | `9c709359` | 02-01-SUMMARY |
| 02-01 T2 | `CAPABILITY_ARCHETYPES_PASS=9/12  threshold=12/12` (`V-ARCH-ID-SHAPE`, `-ARCHETYPES-THREE`, `-NA-BRIDGE` FAIL) | `9c709359` | `7a17f6d4` | 02-01-SUMMARY |
| 02-02 T1 | `CAPABILITY_ARCHETYPES_PASS=12/14  threshold=14/14` (`V-ARCH-INTENT-ONLY-CAP`, `V-ARCH-INTENT-CONTROL` FAIL) | `9e9953b3` | `f9ee905a` | 02-02-SUMMARY |
| 02-02 T2 | `CAPABILITY_ARCHETYPES_PASS=18/27  threshold=27/27` (9 FAIL incl. `V-ARCH-INTENT-BOUNDED` at 2865 ms against 1000 ms) | `f9ee905a` | `7e69bc3d` | 02-02-SUMMARY |
| 02-03 T1 | `CAPABILITY_ARCHETYPES_PASS=29/33  threshold=33/33` (`V-ARCH-TRUNCATED`, `-BUDGET`, `-BLIND-ECOSYSTEM`, `-UNREADABLE-SUBTREE` FAIL) | `f90e4911` | `994200c4` | 02-03-SUMMARY |
| 02-03 T2 | archetypes `33/36`; trait scan `CAPABILITY_TRAIT_SCAN_PASS=2/14` | `994200c4` | `d2c26ee9` | 02-03-SUMMARY |
| 02-03 T3 | archetypes `36/37`; trait scan `17/27` (junction gate measured RESEARCH A10: `files with link 128 == without 2`) | `d2c26ee9` | `275f14e1` | 02-03-SUMMARY |
| 02-04 T1 | `CAPABILITY_ARCHETYPES_PASS=37/38` (`V-ARCH-STALE-MANIFEST`: `after the edit cache=FRESH (want STALE)`) | `e99168f9` | `25454743` | 02-04-SUMMARY |
| 02-04 T2 | `CAPABILITY_ARCHETYPES_PASS=45/51` (6 FAIL) | `25454743` | `d686f294` | 02-04-SUMMARY |
| 02-04 T3 | `CAPABILITY_ARCHETYPES_PASS=51/55` (4 `V-ARCH-CLI-*` FAIL) | `d686f294` | `a02455ed` | 02-04-SUMMARY |
| 02-05 T1 | `CAPABILITY_ARCHETYPES_PASS=55/56  threshold=56/56`, rc=1; `FAIL V-ARCH-TRANSITION-PERSISTENT  SIGNATURE-MISSING: s1=None s2=None` (the only FAIL line) | `e1ad52a8` | `7c725e40` | 02-05-SUMMARY |
| 02-05 T2 | `CAPABILITY_ARCHETYPES_PASS=57/59  threshold=59/59`, rc=1; `FAIL V-ARCH-TRANSITION-DISTRIBUTED` (`modifiers=None` for BACKGROUND_JOB) and `FAIL V-ARCH-SUBJECT-SHAPE` (`missing ['modifier_basis', 'modifiers']`); `V-ARCH-CAUSES-REACHABLE` already PASS | `7c725e40` | `9f3f38a0` | 02-05-SUMMARY |

`V-ARCH-CAUSES-REACHABLE` passing in the 02-05 Task 2 RED run is expected: every cause was already reachable, so the gate holds from its first run. It is not vacuous because its instrument control is part of the gate: it appends the token `zz-unreachable` to `ar.UNJUDGED_CAUSES`, re-runs the same predicate, and requires the predicate to fail and to name that token (restored in `finally`). No separate mutation run was recorded for it.

Falsification drills (a drill installs a mutation, re-runs the target predicate, and requires red, the counter reached, the named sub-assertion, and green after the restore):

| drill | target gate | mutated result | calls | source |
|---|---|---|---|---|
| `V-ARCH-DRILL-CEILING` (ceiling weakened to return REQUIRED on any intent) | `V-ARCH-INTENT-ONLY-CAP` | `mutated ok=False calls=12 named_sub_assertion=True restored ok=True` | 12 | 02-02 |
| `V-ARCH-DRILL-NOUN-LIST` (intent detector degraded to any persistence noun) | `V-ARCH-VOCAB-OVERLAP-NEG`, `V-ARCH-NOUN-ONLY-NEG` | `mutated vocab ok=False noun-only ok=False calls=20 named_sub_assertions=True restored ok=True/True` | 20 | 02-02 |
| `V-ARCH-DRILL-ABSENT-ON-MISS` (`unjudged_reading` replaced by an ABSENT-returning wrapper) | `V-ARCH-MISS-UNJUDGED` | `mutated ok=False calls=102 named_sub_assertion=True restored ok=True` (gate of record; 02-04 recorded 92 for the same drill, the count moves with the number of unusable shapes the target runs) | 102 | 02-04 |
| `V-ARCH-DRILL-READER-SCAN` (`fingerprint` replaced by a wrapper that pulls one item from `os.walk`) | `V-ARCH-READ-ONLY` | `mutated ok=False calls=20 named_sub_assertion=True restored ok=True`, `READER-WALKED: os.walk calls=14 during 20 resolve calls` | 20 | 02-04 |
| `V-ARCH-DRILL-FP-IGNORES-MANIFEST` (`MANIFEST_NAMES = frozenset()`) | `V-ARCH-STALE-MANIFEST` | `mutated ok=False calls=10 named_sub_assertion=True restored ok=True`, `STALE-MANIFEST-NOT-DETECTED: after the edit cache=FRESH (want STALE)` | 10 | 02-04 |
| instrument control inside `V-ARCH-CAUSES-REACHABLE` (unreachable cause `zz-unreachable` added) | itself | predicate returns not-ok and names the token | n/a | 02-05 |

## 4. Side effects

Dirty-path SET (sorted `git status --porcelain`), BEFORE and AFTER the 11-file suite, equal:

```
 M vault/progress.md
?? .gsd/
?? .planning/workstreams/ucep/config.json
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/state.json
```

These five paths pre-date plan 02-05 and were not touched by any Phase 2 plan. The set did not move during the run, so the run is not INCONCLUSIVE and was not repeated. (Between plan start and the gate run the only additions to the tree were this plan's own two code commits, which leave the working tree clean for tracked paths.)

Hermetic control (RESEARCH Pitfall 6): an empty directory `...\Temp\ucep05\hermeticX`; `test_capability_archetypes.py` and `test_capability_trait_scan.py` run with `HOME` and `USERPROFILE` set to it. Both rc=0 (`CAPABILITY_ARCHETYPES_PASS=59/59  threshold=59/59`, `CAPABILITY_ARCHETYPES_REAL_POLES=PASS`, `CAPABILITY_TRAIT_SCAN_PASS=27/27  threshold=27/27`). Recursive listing afterwards: the directory itself and nothing else, `entries under X: 0`.

Real state dir `C:\Users\User\.claude\state\tower`: `traits_*.json` count 0 before and 0 after (the 02-01 value was 0); `traits_production.jsonl` absent before and after. No run escaped the hermetic HOME, so nothing is BLOCKED on T-02-06.

`vault/tower` immutability (D-08, T-02-17): `git diff --quiet 409dca89 HEAD -- vault/tower` rc=0; `git status --porcelain -- vault/tower` printed nothing (0 lines). The five generation files hold their Phase 1 values:

| file | sha256 at gate run | vs Phase 1 F0 blob column |
|---|---|---|
| vault/tower/baselines/kobiicraft_mode/B0.json | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | EQUAL |
| vault/tower/baselines/persistent_state/B0.json | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | EQUAL |
| vault/tower/baselines/web_surface/B0.json | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | EQUAL |
| vault/tower/baselines/web_surface/B1.json | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | EQUAL |
| vault/tower/baselines/wii_homebrew/B0.json | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | EQUAL |

Scope hygiene: `git diff --name-only 409dca89 HEAD` at the gate run lists, outside `.planning/workstreams/ucep/`, exactly: `modules/capability_runtime/archetypes.py`, `modules/capability_runtime/trait_scan.py`, `tools/capability_traits.py`, `tools/test_capability_archetypes.py`, `tools/test_capability_trait_scan.py`, `vault/liveness/reachability_registry.json`. All six are in the Phase 2 allowlist. Under `.planning/workstreams/ucep/` the diff holds the five SUMMARY files, `02-OWNER-QUEUE.md`, `02-liveness-before.json`, `ROADMAP.md`, `STATE.md` and `LIVE-OBSERVATIONS.md`. The orchestration bookkeeping commits in that range, which are not executor plan code: `9e9953b3` (STATE decisions), `e99168f9` and `e1ad52a8` (`LIVE-OBSERVATIONS.md`), and the per-plan `docs(02-0N): update STATE and ROADMAP` commits. Confirmed untouched since PHASE2_BASE (a diff over them printed 0 paths): `modules/tower/families.py`, `modules/capability_runtime/applicability.py`, `modules/capability_runtime/__init__.py`, `modules/tower/capsule.py`, `tools/tower_capsule.py`, `vault/tower/`. No live file under `~/.claude/hooks`, no `settings.json`, no scheduled task was touched or registered by any Phase 2 plan.

## 5. Liveness

Read-only `modules.liveness.reachability.gate()` (never `--baseline`), compared by unit name with `02-liveness-before.json` (written at PHASE2_BASE):

```
offenders 63 before 63 rows 488 new [] mine []
```

Offender count 63 before and 63 after; rows 486 before and 488 after (the two new registry rows). New offender names: none. `capability_runtime/archetypes` and `capability_runtime/trait_scan` are not offenders; both registry rows read `PLANNED` (class values printed from `vault/liveness/reachability_registry.json`). The gate itself remains red on the 63 standing offenders, as before the phase; Phase 2 added none and cleared none. Both rows point at `02-OWNER-QUEUE.md` (L-1, section 9). `tools/capability_traits.py` has no registry row because `tools/` is not scanned by the liveness gate (plan-checker finding, L650).

## 6. Discretion choices (D-09)

- **Fingerprint inputs** (02-04). `fp1` = sha256 over the sorted names of the root's direct entries plus the `name|size|mtime_ns` of each root entry named in `MANIFEST_NAMES` (19 lower-cased basenames), by `os.scandir` only. `fp2` (producer skip rule) adds, per root child directory the producer would walk, its mtime, its sorted entry names and the stats of its manifest-named entries (depth 2). The reader also re-stats up to 32 evidence files recorded in the document. Reason: NTFS moves a directory mtime only when a direct child is created, deleted or renamed, never when a file is edited in place, so each manifest and each evidence file is stat'ed on its own. Stats use `os.stat`, never `DirEntry.stat()`: the cached listing mtime lagged by 1 ms for seconds on this host and made two fingerprints of an untouched repository disagree.
- **Cache location and schema** (02-01). `~/.claude/state/tower/traits_<repo_key>.json`, schema `ucep-traits/1`, written atomically by `trait_scan.produce`; never inside a repository. The reader refuses nine unusable shapes with ten UNJUDGED and a named cause.
- **`TRAIT_MAX_AGE_S` = 7 days** (RESEARCH A2): the fingerprint carries freshness, age is the backstop; the capsule's 24 h would read STALE every Monday on a laptop that was off. **`SKIP_WINDOW_S` = 24 h**: a skip never extends a document's age, so a change the fingerprints cannot see is rewalked within a day of the scheduled run. **`CACHE_MAX_BYTES` = 256 KiB**, refused before parsing. Walk defaults: cap 100000 files, budget 120 s.
- **STRONG and WEAK classes** (02-03). STRONG: a declared dependency name parsed from a manifest (eight ecosystems, 113 signal names), a named marker file or directory (`schema.prisma`, `migrations`, a compose file, `plugin.yml`, a workflow with `cron:`, `vercel.json` with `crons`, a Deployment or CronJob manifest in a workload directory), at least 20 UI files. WEAK: data files by name or extension (`.db`, `.sqlite`, `.sqlite3`, `.mca`, `level.dat`, `playerdata`), a source file under a `save`/`persistence`/`storage` directory segment (`code-module`, provisional, R-3), a dev-only dependency, policy directories, fewer than 20 UI files, a Dockerfile. `Thumbs.db` is ignored. A data file is never an evidence file for freshness.
- **UI threshold**: `UI_PRESENT_MIN = 20`, one to nineteen files WEAK (RESEARCH A8 proposed 5 and "WEAK below 20"; the edge is pinned in `V-TSCAN-UI-THRESHOLD`).
- **Archetype set** (`ARCHETYPES` in code, sole authority, R-2). `WORLD_MUTATION`: anchor `persistent`, modifiers `destructive`, `bulk`, `multi_actor`, `distributed`, `money`, demoters `read-only`, `read only`, `solo lectura`, `dry run`, `sin escribir`, `simulacion`. `EXTERNAL_EFFECT`: anchor `external_effect`, modifiers `money`, `scheduled`, `distributed`, `multi_actor`, demoters `sandbox`, `dry run`, `test mode`, `modo prueba`, `simulado`, `sin enviar`. `BACKGROUND_JOB`: anchor `scheduled`, modifiers `distributed`, `persistent`, `external_effect`, demoters `one-off`, `one off`, `una sola vez`, `manualmente`, `dry run`.
- **Strength rules** (`ceiling`, the only place a strength is decided): anchor PRESENT with intent and no demoter -> REQUIRED (`structural+intent`); with a demoter -> CONDITIONAL; PRESENT without intent -> CONDITIONAL (`structural`, R-1); WEAK -> CONDITIONAL; ABSENT or UNJUDGED with intent -> CONDITIONAL (`intent`); otherwise NONE. A modifier appears in `modifiers` when its structural reading is PRESENT or WEAK or its intent reading is PRESENT, with basis `structural`, `intent` or `structural+intent`; it never enters `ceiling` (02-05).
- **Fact-state mapping**: vocabulary of `modules.gsd_x.mission.obligation`, imported. Archetype `fact_state` is OBSERVED when the basis contains structural evidence, EXTRACTED for intent alone, UNKNOWN for none; every intent reading is EXTRACTED; every miss is UNKNOWN.
- **Subject signature** (02-05): first 16 hex of sha256 over canonical JSON of the ten trait states, the ten intent states, one `[id, strength, basis, sorted modifiers]` row per archetype and the sorted family ids. Excluded on purpose: root, cache path and state, `produced_at`, every timestamp, evidence strings, spans and reason text, so equal structure signs equal in two directories (pinned by `V-ARCH-TRANSITION-PERSISTENT`).
- **Intent detector coverage**: bilingual verb-object detectors for six traits (persistent, external_effect, scheduled, destructive, bulk, money), a verb within 60 characters of an object, folded text, first 20000 characters only. `multi_actor`, `distributed`, `policy_layers` and `ui` read UNJUDGED `no-intent-detector`. No noun list was added for them: a noun bag at trait level reopens the D7 defect (a word alone creating a requirement) that `V-ARCH-DRILL-NOUN-LIST` shows the current design refuses.

## 7. Assumptions needing Owner review (recorded, not asked)

None of these is an Owner confirmation.

- **A3 / R-1** structure-only evidence with no intent yields CONDITIONAL, not NONE. Risk: more CONDITIONAL surfaces in later envelopes. The alternative (NONE) lets a naked verb escape when the closed intent vocabulary misses its wording.
- **A2** the 7 day age bound. Too long serves deep changes stale; too short reads UNJUDGED most mornings. The depth-1 fingerprint and evidence re-stat carry most of the freshness.
- **A4, A5** closed dependency vocabularies (113 names) and closed verb and object lists. A library or wording outside them is a recall gap: a missing dependency reads ABSENT only when a manifest was parsed and the walk was complete, and an intent miss is compensated by structure-only CONDITIONAL.
- **A6 / R-3** the `code-module` persistence signal (a source file under a `save`, `persistence` or `storage` segment) ships WEAK and provisional; its calibration against KobiiSports Resort is Phase 7. RESEARCH A6 proposed STRONG; the resolution made it WEAK so it cannot by itself reach REQUIRED.
- **A8** the UI threshold of 20 files (PRESENT) with WEAK below.
- **A10** directory junctions: measured, not assumed. `os.walk(followlinks=False)` descends a junction on this host (128 files with the link followed against 2), so the producer prunes symlinks and junctions itself.

## 8. Known limits

- The dependency and verb vocabularies are closed and fitted to the repositories seen (GSDX-M04 debt, recorded in `modules/gsd_x/mission/obligation`).
- Depth-1 blind spot: a module added below the root is neither an evidence file nor in the depth-1 fingerprint. Only the 7 day age bound on the reader and the producer's depth-2 check on its next run catch it (`V-ARCH-STALE-DEEP-BLINDSPOT` pins the bound: `cache=FRESH fp1_unchanged=True fp2_moved=True`).
- `bulk` and `destructive` have no structural detector and read UNJUDGED `no-structural-detector` on every repository, including the two real ones above; they can only become facts through intent.
- ABSW2-Wii and other repositories with no manifest any parser knows read every manifest-dependent trait UNJUDGED `no-manifest-ecosystem`. On the real pole this is the observed answer (`persistent=UNJUDGED`), not WEAK.
- KobiiSports Resort calibration of the persistence signal is Phase 7 (R-3). The real-pole read covered InfinityOps and ABSW2-Wii only.
- `tools/capability_traits.py --all` was NOT run over the real estate, and no cache exists in the real `~/.claude/state/tower` (`traits_*.json` count 0).
- Reader latency is informational here: `V-ARCH-READ-ONLY` measured median 7.94 ms and p95 16.32 ms over 20 mixed `resolve` calls in the gate run (7.28/16.21, 10.21/18.05 and 11.51/31.26 ms in three 02-04 runs). The figure moves with host load and is far under the 3000 ms chain deadline. The prompt-path budget gate belongs to Phase 6.
- Nothing is wired into the prompt path: no hook, command or module outside the tests imports `archetypes` or `trait_scan` (the PLANNED liveness rows say so). Wiring is Phase 5 (envelope) and Phase 6 (delivery).
- The real-pole result depends on this host's trees. A walk that is cut (cap or budget) reads UNJUDGED for that pole rather than FAIL; only a complete walk that contradicts the expectation fails the run.
- Enforcement stays report-only until Phase 8 (T-02-07).

## 9. Owner queue

Copied from `02-OWNER-QUEUE.md` with current status. All three items are open and none blocks Phase 2.

| id | scope | item | status | effect until done |
|---|---|---|---|---|
| O-1 | Owner action | Host the out-of-band producer after merge: run `tools/capability_traits.py --all` as a second action of the scheduled task `PP-Tower-Capsules`, or as a sibling task using the same `tools/hidden_launch.vbs` wrapper. | open | every real-session read of the trait cache finds no file, so each trait reads `no-cache` and UNJUDGED; nothing is ever read as ABSENT |
| O-2 | Owner action, Phase 6 scope | Optional: a SessionStart detached refresh of the subject repository (the `hooks/jit_warm.js` pattern; needs a new file under `hooks/` and an Owner registration). | open | none for Phase 2; it only shortens the window in which a freshly cloned repository has no cache |
| L-1 | not an Owner action | The liveness exit: the two PLANNED rows `capability_runtime/archetypes` and `capability_runtime/trait_scan` are removed when a live surface imports the modules (Phase 5 envelope, delivered in Phase 6). | open | both units stay declared PLANNED and are not offenders |

Phase 1 carry-over (STATE.md, not a Phase 2 item): A1, the agent-typed "Owner" authority on the two re-anchor generations, still open for Owner review.

Phase 2 changed no live hook, no file under `~/.claude/`, no `settings.json` and no scheduled task, and registered nothing.

## 10. Production Reality verdict

| component | verdict | basis |
|---|---|---|
| trait producer (`trait_scan.scan` / `produce`, `tools/capability_traits.py`) | OBSERVED | real tests and fixtures (27/27 and the producer gates in the 59), on an unmerged branch; the CLI ran only inside a hermetic HOME |
| trait cache (`traits_<repo_key>.json`, fingerprint, freshness, refusal of unusable shapes) | OBSERVED | 59 gates including STALE-*, MISS-UNJUDGED, KEY-NORMALIZATION and three drills; no real cache file exists |
| reader (`read_traits`) | OBSERVED | `V-ARCH-READ-ONLY`: walk=0 scan=0 produce=0, listing unchanged, with a positive control; never exercised by a real prompt |
| subject (`resolve`, `assess`, `ceiling`, `modifiers_for`, `subject_signature`) | OBSERVED | module-level tests, falsification drills, transition gates; no live caller |
| real-repo poles (InfinityOps, ABSW2-Wii) | OBSERVED | `V-ARCH-REAL-POLES` PASS in the gate run, read-only, uncounted; ABSW2-Wii `persistent` reads UNJUDGED, not WEAK |
| prompt-path delivery of the subject | UNJUDGED | not wired until Phases 5 and 6 |
| producer hosting on a schedule | UNJUDGED | Owner step O-1 open; until done every real read is `no-cache` |
| overall Phase 2 | OBSERVED | nothing here is on a live hook path |
| PROVEN | none | no component ran on the live production path |
| BLOCKED | none | no earlier SUMMARY and none of the bracket steps (dirty-path SET, hermetic listing, real `traits_*.json` count) recorded a BLOCKED item |

## 11. Handoff

```
PANE: UCEP mission, Phase 2 executor (plan 02-05)
SPRINT: Phase 2 capability subject and archetypes (UCEP-02), plans 02-01..02-05 executed
STATUS: COMPLETE (verdict OBSERVED; no PROVEN, no BLOCKED)
LIVE: 9f3f38a0 (branch ucep/mission, not pushed; the docs commit carrying this file follows it)
NEXT: Phase 3 promotion admission and scope contract; Owner step O-1 after merge
DEBT: O-1, O-2, L-1 open; A1 from Phase 1 open; bulk/destructive have no structural detector; KobiiSports calibration is Phase 7
```

## Addendum 2026-10-03 (epoch 3): figures after the CR-01 fix

The record above is left as it was measured. After fix `d61b5c23` (code review CR-01, see
`02-REVIEW-FIX.md`), the current figures are: `CAPABILITY_TRAIT_SCAN_PASS=28/28` (was 27/27, new gate
`V-TSCAN-PARTIAL-MANIFEST-UNJUDGED`) and `V-ARCH-CAUSES-REACHABLE` over 10 causes (was 9, new cause
`manifest-unparsed`). `CAPABILITY_ARCHETYPES_PASS=59/59` is unchanged. Re-measured independently by the
verifier for `02-VERIFICATION.md`.
