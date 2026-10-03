---
phase: "3"
slug: "promotion-admission-and-scope-contract"
# status lifecycle: draft (seeded by plan-phase) -> validated (set by validate-phase)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-03"
---

# Phase 3 — Validation Strategy

> Per-phase validation contract. Sources: ROADMAP Phase 3 success criteria 1-5, `03-CONTEXT.md` decisions A1-E4,
> plan of record `vault/plans/ucep-naked-verb-2026-10-02.md` S4 items 8-9, audit gaps G5, G6, G15.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain Python scripts printing `<NAME>_PASS=n/m  threshold=n/m`, exit 0 iff all pass; the new suite holds a literal `EXPECTED` so a deleted or skipped gate cannot print a satisfied n/n |
| **Config file** | none |
| **Quick run command** | `Set-Location 'C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ucep'; $env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_tower_admission.py; exit $LASTEXITCODE` |
| **Full suite command** | the new file plus the fifteen Phase 1/2 suites, run with `HOME`, `USERPROFILE` and `CLAUDE_STATE_DIR` on a fresh `$env:TEMP` directory (03-04 Task 3 verify command) |
| **Estimated runtime** | new file < 30 s (temp roots, one `copytree` of the real baselines); full suite about 120 s |

Failure = non-zero exit OR a `FAIL` line OR `PASS=n/m` with n < m OR a count below its floor. A run whose sorted
dirty-path SET changed between start and end is INCONCLUSIVE, never green.

## Sampling Rate

- **After every task commit:** `tools/test_tower_admission.py` plus the Phase 1 suites that task's plan names in its `<verify>`.
- **After every plan:** the plan's `<verification>` block (the suites it touched, at their floors).
- **Before verify (03-04 Task 3):** the full suite in one bracketed run; the F0 three-way check; the liveness offender SET compared by name.
- **Max feedback latency:** 120 seconds.

## Floors (measured in 03-01 Task 1 Step 0; a lower count at any later point is a regression)

| suite | pass line | floor |
|---|---|---|
| test_ucep_baseline_integrity | UCEP_BASELINE_INTEGRITY_PASS | 40 |
| test_ucep_donegate_exits | UCEP_DONEGATE_EXITS_PASS | 17 |
| test_baseline_generations | BASELINE_GENERATIONS_PASS | 18 |
| test_tower_ratchet | TOWER_RATCHET_PASS | 21 |
| test_tower_donegate | TOWER_DONEGATE_PASS | 10 |
| test_family_baselines | FAMILY_BASELINES_PASS | 20 |
| test_tower_select | TOWER_SELECT_PASS | 15 |
| test_tower_checks | TOWER_CHECKS_PASS | 23 |
| test_tower_capsule | TOWER_CAPSULE_PASS | 16 |
| test_tower_inheritance | TOWER_INHERITANCE_PASS | 17 |
| test_family_injection | FINJ_PASS | 24 |
| test_tower_o4 | TOWER_O4_PASS | 7 |
| test_capability_archetypes | CAPABILITY_ARCHETYPES_PASS | 59 |
| test_capability_trait_scan | CAPABILITY_TRAIT_SCAN_PASS | 28 |
| test_gsd_x_heartbeat_path | GSD_X_HEARTBEAT_PATH_PASS | 7 |
| test_tower_admission (new) | TOWER_ADMISSION_PASS | 30 at phase end (6, 9, 15, 19, 20, 21, 25, 27, 30 after each task) |

## Criterion Verification Map (Nyquist)

| Criterion | Requirement | Automated command | Passing output | Status |
|---|---|---|---|---|
| SC1 evidence bar: origin VERIFIED and not under a worktree or a rules pointer file [G15]; runnable check or explicit MANUAL do-confirm; evidence ref; production evidence ref; negative applicability; counterfactual; status provisional (C5, C6, C7, B2) | UCEP-03 | `tools/test_tower_admission.py` | `PASS` on V-ADM-TRACER-ARCHETYPE (record `status` provisional), V-ADM-TRACER-REFUSED-ORIGIN, V-ADM-REFUSE-WORKTREE-ORIGIN, V-ADM-REFUSE-RULES-POINTER, V-ADM-REFUSE-ORIGIN-NOT-VERIFIED, V-ADM-REFUSE-MATCH-ALL-CHECK, V-ADM-REFUSE-CHECK-NOT-RUNNABLE, V-ADM-REFUSE-EVIDENCE-REFS, V-ADM-REFUSE-NO-NEGATIVE-APPLICABILITY, V-ADM-REFUSE-COUNTERFACTUAL-INSTANCE, V-ADM-ALL-REASONS; every refusal gate also asserts its admitted control | pending |
| SC2 scope DERIVED from write location + applicability; declared narrower refused [G6]; family/archetype AUTO_ADMITTED; cross-family/universal/constitutive PENDING_OWNER, never written (C1-C4) | UCEP-03 | `tools/test_tower_admission.py` | `PASS` on V-ADM-SCOPE-FROM-LOCATION, V-ADM-SCOPE-APPLICABILITY-WIDENS, V-ADM-REFUSE-NARROW-SCOPE, V-ADM-PENDING-OWNER-NOT-WRITTEN (directory listing unchanged) | pending |
| SC3 `promote` and archetype B0 creation require a record [G5]; `verify_chain` refuses any entry added outside the grandfathered set without one; grandfathering pinned by identity (A1, A2, B1, B3, B4, D1, D2) | UCEP-03 | `tools/test_tower_admission.py`; `tools/test_tower_ratchet.py` (V-TRAT-REAL-CHAINS) | `PASS` on V-ADM-TRACER-ARCHETYPE, V-ADM-TRACER-RECORD-INVALID, V-ADM-LEGACY-IDENTITY, V-ADM-UNADMITTED-RAW-WRITE, V-ADM-LEGACY-IS-THE-ONLY-SWITCH, V-ADM-DONEGATE-CHAIN-UNADMITTED, V-ADM-REVERT-REANCHOR-NEED-NO-ADMISSION, V-ADM-BUILD-B0-ADMITS; `V-TRAT-REAL-CHAINS PASS` | pending |
| SC4 `baselines.propagation_scope(entry, gen)` projects grandfathered entries as LEGACY_UNSPECIFIED; C/D gain no meaning; unrecorded -> UNADMITTED, never a guess (D3) | UCEP-03 | `tools/test_tower_admission.py` | `PASS` on V-ADM-TRACER-ARCHETYPE (projection arm), V-ADM-PROPAGATION-LEGACY (both classes present in the population), V-ADM-PROPAGATION-ADMITTED (carried entry, C/D pair, bogus scope, legacy carry) | pending |
| SC5 bad origin, `glob:**`, self-declared narrow scope and unadmitted raw `write_generation` all refused; fully evidenced archetype entry admitted (E2, E3) | UCEP-03 | `tools/test_tower_admission.py` | `PASS` on V-ADM-TRACER-REFUSED-ORIGIN, V-ADM-REFUSE-MATCH-ALL-CHECK, V-ADM-REFUSE-NARROW-SCOPE, V-ADM-UNADMITTED-RAW-WRITE, V-ADM-TRACER-ARCHETYPE | pending |
| E4 real tree by discovery + mutation drill (record removed / scope widened in a copy turns it red) | UCEP-03 | `tools/test_tower_admission.py` | `PASS V-ADM-REAL-CHAINS-ADMITTED` (floor 4 subjects; grandfathered generations = 7; drill arms a-c red, arm d ok) | pending |
| A3 no default switches the requirement off for the real tree | UCEP-03 | `tools/test_tower_admission.py` | `PASS` on V-ADM-LEGACY-REFUSED-ON-REAL-TREE and V-ADM-DONEGATE-LEGACY-PASSTHROUGH (ValueError for root=None and any `vault/tower/baselines` path) | pending |
| A4 the seven grandfathered generation files keep their exact bytes | UCEP-03 | 03-04 Task 3 second verify (`F0_THREE_WAY`), plus `git log --format=%h <PHASE3_BASE>..HEAD -- <seven paths>` | `F0_THREE_WAY=EQUAL rows=7`; empty `git log`; `V-ADM-LEGACY-IDENTITY PASS` throughout | pending |
| D4 liveness (as corrected by the orchestrator): offender SET does not grow; `tower/admission` is not an offender | UCEP-03 | throwaway `reachability.gate()` script before (03-01 Step 0 -> `03-liveness-before.json`) and after (03-04 Task 3); `V-ADM-LIVENESS-DECLARED` | after-minus-before offender names = empty set; `tower/admission` row ORPHAN + PLANNED with an existing Owner-queue path | pending |
| Phase 1/2 suites keep or grow their counts (A3) | UCEP-01, UCEP-02 (regression) | 03-04 Task 3 first verify (bracketed, temp HOME) | every line in the Floors table at or above its floor; equal dirty-path SETs | pending |
| Documented CLI matches what runs | UCEP-03 | 03-04 Task 1 second verify; `V-ADM-CLI-VERIFY-NAMES-ADMISSION` | usage documents `build-b0 ... --authority`; UNADMITTED / ADMISSION_INVALID lines carry admission reasons | pending |
| No side effects on the real tree or home | UCEP-03 | `git diff --stat <PHASE3_BASE>..HEAD -- vault/tower/baselines`; `V-ADM-HERMETIC-HOME` | empty diff; hermetic gate PASS | pending |

## Per-Task Verification Map

| Plan / Task | Gates added (cumulative EXPECTED) | RED expected first | Automated verify |
|---|---|---|---|
| 03-01 T1 (tracer) | 1-6: HERMETIC-HOME, TRACER-ARCHETYPE, TRACER-REFUSED-ORIGIN, TRACER-RECORD-INVALID, LEGACY-IDENTITY, LIVENESS-DECLARED (6) | `TOWER_ADMISSION_PASS=1/6` | new suite + ratchet, integrity, generations, donegate, donegate-exits, archetypes |
| 03-01 T2 | 7-9: REFUSE-WORKTREE-ORIGIN, REFUSE-RULES-POINTER, REFUSE-ORIGIN-NOT-VERIFIED (9) | `7/9` | new suite + ratchet |
| 03-02 T1 | 10-15: REFUSE-MATCH-ALL-CHECK, REFUSE-CHECK-NOT-RUNNABLE, REFUSE-EVIDENCE-REFS, REFUSE-NO-NEGATIVE-APPLICABILITY, REFUSE-COUNTERFACTUAL-INSTANCE, ALL-REASONS (15) | `9/15` | new suite + ratchet |
| 03-02 T2 | 16-19: SCOPE-FROM-LOCATION, SCOPE-APPLICABILITY-WIDENS, REFUSE-NARROW-SCOPE, PENDING-OWNER-NOT-WRITTEN (19) | `16/19` | new suite + ratchet, integrity |
| 03-03 T1 | 20: LEGACY-REFUSED-ON-REAL-TREE (20) | `19/20` | new suite + ratchet, integrity, generations |
| 03-03 T2 | 21: DONEGATE-LEGACY-PASSTHROUGH (21) | `20/21` | new suite + donegate, donegate-exits |
| 03-03 T3 | 22-25: UNADMITTED-RAW-WRITE, LEGACY-IS-THE-ONLY-SWITCH, DONEGATE-CHAIN-UNADMITTED, REVERT-REANCHOR-NEED-NO-ADMISSION (25) | `21/25` (the E1 case: raw adds pass on the unchanged chain check) | new suite + seven regression suites, temp HOME |
| 03-04 T1 | 26-27: BUILD-B0-ADMITS, CLI-VERIFY-NAMES-ADMISSION (27) | `25/27` | new suite + generations, ratchet, integrity; CLI usage check |
| 03-04 T2 | 28-30: PROPAGATION-LEGACY, PROPAGATION-ADMITTED, REAL-CHAINS-ADMITTED (30) | `29/30` | new suite + ratchet, generations, family baselines |
| 03-04 T3 (phase gate) | none (30) | n/a | full suite bracketed; `F0_THREE_WAY=EQUAL rows=7`; liveness by name |

Every task has an automated verify; no three consecutive tasks lack one. Each RED line is recorded verbatim in
`03-EVIDENCE.md` section 5 with its HEAD hash. A gate that already passes when written is recorded as such, and only
counts if it carries an arm that returns the other answer (a refusal arm, a mutation-drill arm or an instrument
control).

## Wave 0 Requirements

- [ ] `tools/test_tower_admission.py` (NEW, 03-01 Task 1 Step 1) — hermetic header before any `modules` import, guarded admission import, literal `EXPECTED`, `evidenced()` fixture builder that is fully evidenced from the first task; RED recorded in 03-EVIDENCE.md before any admission code exists
- [ ] `03-EVIDENCE.md` (NEW, 03-01 Task 1 Step 0) — start state, F0 at phase start, suite floors, liveness before, RED records table
- [ ] `03-liveness-before.json` (NEW, 03-01 Task 1 Step 0) — offender names before the module exists
- [ ] Framework install: none

## Manual-Only Verifications

All phase behaviours have automated verification. The Owner items in `03-OWNER-QUEUE.md` (O-1 unforgeable approval
channel, O-2 PENDING_OWNER queue file, O-3 review of the `build-b0 --authority` requirement) are decisions or reviews,
not Phase 3 verifications; until O-1 exists, no PENDING_OWNER entry can be admitted, and that is asserted by
V-ADM-PENDING-OWNER-NOT-WRITTEN.

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
