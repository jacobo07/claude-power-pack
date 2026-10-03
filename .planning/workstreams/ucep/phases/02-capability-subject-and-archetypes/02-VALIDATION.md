---
phase: "2"
slug: "capability-subject-and-archetypes"
# status lifecycle: draft (seeded by plan-phase) -> validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-03"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract. Source: `02-RESEARCH.md` § Validation Architecture.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain Python scripts printing `<NAME>_PASS=n/m threshold=n/m`, exit 0 iff all pass |
| **Config file** | none |
| **Quick run command** | `$env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_capability_archetypes.py` |
| **Full suite command** | the new file + regression set: `test_family_baselines`, `test_family_injection`, `test_tower_capsule`, `test_tower_inheritance`, `test_tower_ratchet`, `test_baseline_generations`, `test_tower_donegate` |
| **Estimated runtime** | new file < 30 s on synthetic fixtures; full suite ~90 s |

Failure = non-zero exit OR a `FAIL` line OR `PASS=n/m` with n<m. A gate that prints UNJUDGED (e.g. optional real-repo poles with a missing path) is not counted as PASS.

## Sampling Rate

- **After every task commit:** the new test file + `test_family_baselines.py`, `test_family_injection.py`.
- **After every plan wave:** full suite, bracketed by the sorted dirty-path SET before/after (changed set -> INCONCLUSIVE, not green).
- **Before verify:** full suite green; sha256 of `vault/tower/baselines/**` unchanged; liveness offender set diffed by name (baseline 63 offenders) — no new orphan.
- **Max feedback latency:** 90 seconds

## Per-Task Verification Map

| Criterion | Requirement | Automated Command | Passing output | Status |
|---|---|---|---|---|
| 1 ten traits, conjunction archetypes, family ⟂ archetype | UCEP-02 | `tools/test_capability_archetypes.py` (V-ARCH-TRAITS-TEN, -ID-SHAPE, -VOCAB-SHARED, -NA-BRIDGE, -ORTHOGONAL-A/B) | all PASS | pending |
| 2 off-path cache, read-only reader, miss -> UNJUDGED | UCEP-02 | V-ARCH-MISS-UNJUDGED, -READ-ONLY, -STALE-MANIFEST, -STALE-AGE, -TRUNCATED, -BLIND-ECOSYSTEM, -KEY-NORMALIZATION, -CACHE-OUTSIDE-REPO, -HERMETIC-HOME | all PASS; reader makes 0 scan calls | pending |
| 3 intent-only <= CONDITIONAL, EXTRACTED | UCEP-02 | V-ARCH-INTENT-ONLY-CAP, -INTENT-CONTROL, -WEAK-CAP, -DEMOTE-NOT-VETO, -DRILL-CEILING | all PASS; drill shows the cap gate FAIL under a weakened ceiling | pending |
| 4 negative/intent-only controls, transitions, positives | UCEP-02 | V-ARCH-VOCAB-OVERLAP-NEG, -TRANSITION-PERSISTENT, -TRANSITION-DISTRIBUTED, -POSITIVE-{WORLD_MUTATION,EXTERNAL_EFFECT,BACKGROUND_JOB}, optional -REAL-POLES | all PASS (REAL-POLES may be UNJUDGED, never counted PASS) | pending |
| liveness | UCEP-02 | `reachability.gate()` offender set before/after (read-only, never `--baseline`) | no new offender by name; PLANNED rows for `capability_runtime/archetypes`, `capability_runtime/trait_scan` | pending |
| no side effects | UCEP-02 | sha256 of `vault/tower/baselines/**`; dirty-path SET bracket; temp-HOME control | hashes equal; only the phase's own files dirty | pending |

## Wave 0 Requirements

- [ ] `tools/test_capability_archetypes.py` (NEW) — all V-ARCH-* gates, RED first against a missing module / weak ceiling, recorded in EVIDENCE
- [ ] In-test fixture builder (temp repos: ephemeral, persistent, scheduled, scheduled+docker, external-effect, zero-manifest, truncated, vocabulary-only docs)
- [ ] Framework install: none

## Manual-Only Verifications

All phase behaviors have automated verification. (Hosting the producer on the `PP-Tower-Capsules` scheduled task is an Owner step recorded in EVIDENCE, not a Phase 2 verification.)

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
