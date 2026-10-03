# Phase 2 (ucep) plan check — gsd-plan-checker

Phase goal: A capability subject (traits + archetypes) resolved from repo reality first, intent second.
Requirement: UCEP-02 (CONTEXT; ROADMAP section lists no Requirements line). Success criteria 1-4 from ROADMAP.
Inputs read: roadmap.get-phase 2, 02-CONTEXT.md, 02-VALIDATION.md, 02-01..02-05-PLAN.md, 02-RESEARCH.md (Phase
Requirements, Responsibility Map, Open Questions, Validation Architecture), plan of record + audit (G4 = audit item 4,
G16 = audit item 16), and source premises below.
Tool runs (read-only): verify.plan-structure on all 5 plans -> valid, 0 errors, 1 warning (02-01, R6, see I1);
estimate-check --calibrated: 0.70 / 0.85 / 0.95 / 0.90 / 0.85 of the 100k budget, none over (confidence low, 0 samples).

## Findings (appended as confirmed)

Premises confirmed in source: applicability._hits (L97), families._fold/_match/classify_prompt/_SKIP_DIRS/_MAX_ENTRIES
(classify_prompt does not walk; load_families is one listdir), obligation OBSERVED/EXTRACTED/UNKNOWN/FACT_STATES (gsd_x
package __init__ files import nothing), donegate.NA_REASONS (12 tokens, first ten equal the planned TRAIT_NA_REASON values),
baselines.REQUIRED + discover_subjects, identity.canonical_repo (Path.resolve -> on-disk case, so the case variants in
V-ARCH-KEY-NORMALIZATION converge) / repo_key, reachability.gate (offender dicts carry "unit"; tools/ not scanned, L650,
so no registry row for tools/capability_traits.py is correct), capsule produced_at = epoch float (02-04 age arithmetic
consistent). ORTHOGONAL-B prompt words appear in no vault/tower/families/*.json trigger (grep: 0 hits). No traits_*.json
exists anywhere in the worktree (V-ARCH-CACHE-OUTSIDE-REPO starts from a true zero).

Coverage: SC1 -> 02-01 T1/T2 + 02-02 ORTHOGONAL-A/B; SC2 -> 02-01 T1, 02-03 (entitlement), 02-04 (fingerprint, reader
contract, CLI); SC3 -> 02-02 ceiling + DRILL-CEILING; SC4 -> 02-02 VOCAB-OVERLAP-NEG, INTENT-ONLY-CAP, 02-03 POSITIVE-*,
02-05 TRANSITION-PERSISTENT/-DISTRIBUTED. UCEP-02 in every plan's requirements. D-01..D-09 each traced to a task; deferred
prompt-path wiring is absent from all tasks. Dependency chain 01->02->03->04->05 linear, acyclic, waves consistent; no
same-wave pairs (Dimension 3b n/a). Gate arithmetic checked: 5,12,14,27,29,33,36,37,38,51,55,56,59 and 14,27 all consistent.

F1 [warning] 02-03 Task 1, V-ARCH-BUDGET: `produce(..., budget_s=0)` must make `walk.budget_hit` true. The plan says only
"stops at budget_s wall-clock". On this host (CPython 3.12, Windows) time.monotonic() ticks at ~15.6 ms, so an
implementation comparing `elapsed > budget_s` on a 4-file fixture can read elapsed == 0 and never hit the budget -> the gate
fails or gets "fixed" by loosening it. Required property: budget_s=0 deterministically cuts the walk. Example fix: specify
`>=` against time.perf_counter(), checked before descending each directory.

F2 [warning] 02-03 Task 3, V-TSCAN-NO-SECRET-READ: the instrument is a counting wrapper over `builtins.open`, but no
positive control requires that it saw anything. If trait_scan reads manifests via pathlib (Path.read_text -> io.open) or
binds `open` at import, the wrapper records zero paths and the gate passes vacuously ("none matches .env*" over an empty
list). Required property: the gate can return the other answer. Example fix: assert `package.json` (and one named content
marker) appears in the recorded opens, and/or wrap io.open as well.

F3 [warning] 02-04 Task 3, V-ARCH-CLI-ALL-INJECTED: the "explicit list never enumerates the estate" assertion wraps
`tools.family_scan.find_repos`, but the plan tells the CLI to copy tools/tower_capsule.py, which does
`sys.path.insert(0, _HERE); from family_scan import find_repos, main_repo_of` (tower_capsule.py L45-46): a top-level module
`family_scan`, a different module object from `tools.family_scan`. The counter reads 0 even if produce_all enumerated the
real estate. Required property: the counter wraps the object the CLI actually calls. Example fix: pre-import `family_scan`
the way the CLI does and patch `sys.modules["family_scan"].find_repos` (or both names), with a positive control
(produce_all(None) under a raising wrapper shows calls > 0).

F4 [warning] Phase-level, Dimension 11: 02-RESEARCH.md `## Open Questions` (L445) has no `(RESOLVED)` suffix and none of the
five questions carries an inline RESOLVED marker. Substance is resolved in executable plan content (02-01 <objective>
R-1 = Q2, R-2 = Q1, R-3 = Q3, R-4 = Q4; Q5 by `subject_root` taking root as a required argument, never os.getcwd()), so the
phase goal is not at risk; filed as warning rather than the dimension's default blocker for that reason. Required
property: RESEARCH.md carries no unmarked open question. Example fix: retitle `## Open Questions (RESOLVED)` and append
`RESOLVED: R-n (02-01-PLAN.md)` to each item.

I1 [info] 02-01: verify.plan-structure R6 warning (bare `git diff`). The bare form is the pre-commit hunk read of the shared
registry (intentionally about the uncommitted tree); the acceptance criterion already pins `<PHASE2_BASE> <s6>`. No change
needed beyond optionally saying "uncommitted tree" next to it.

I2 [info] 02-02 Task 2, V-ARCH-DEMOTE-NOT-VETO: each demoted prompt carries TWO demoter phrases (`dry run` + `sin escribir`;
`dry run` + `read-only`), but the control says "the demoter phrase removed". Removing only one leaves the prompt demoted and
the control fails. State that the control removes every demoter phrase.

I3 [info] 02-04 Task 2, producer skip: the skip test compares fp2, evidence stats and age but not the `cap`/`budget_s` the
stored document was produced with, so a truncated or budget-cut document is kept (as UNJUDGED) for up to 24 h after a later
default-argument produce. Safe direction (UNJUDGED), and the CLI always uses defaults; worth one sentence in the docstring.

I4 [info] 02-03 estimate 95k = 0.95 of the smart-zone budget with 13 new gates in Task 3; closest plan to the edge.

VERDICT: ISSUES FOUND

0 blockers, 4 warnings, 4 info.
1. 02-03 Task 1 — warning — V-ARCH-BUDGET can miss the cut with budget_s=0 on a coarse clock; require a deterministic cut (`>=`, perf_counter, checked before each directory).
2. 02-03 Task 3 — warning — V-TSCAN-NO-SECRET-READ has no positive control; require package.json (and a content marker) in the recorded opens, and/or also wrap io.open.
3. 02-04 Task 3 — warning — V-ARCH-CLI-ALL-INJECTED wraps tools.family_scan but the CLI (copying tower_capsule) calls top-level family_scan; patch the module object actually used, with a positive control.
4. Phase (02-RESEARCH.md) — warning — Open Questions not marked RESOLVED although resolved as R-1..R-4 and subject_root; add the markers.
5. 02-01 — info — R6 bare git diff is the intentional pre-commit hunk read; optional clarifying note.
6. 02-02 Task 2 — info — DEMOTE-NOT-VETO control must remove both demoter phrases.
7. 02-04 Task 2 — info — producer skip ignores cap/budget of the stored doc; document it.
8. 02-03 — info — estimate at 0.95 of budget.
