---
phase: "1"
slug: "baseline-integrity-repair"
# status lifecycle: draft (seeded by plan-phase) -> validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-02"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract. Source: `01-RESEARCH.md` § Validation Architecture.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain Python scripts printing `<NAME>_PASS=n/m threshold=n/m`, exit 0 iff all pass |
| **Config file** | none |
| **Quick run command** | `$env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_ucep_baseline_integrity.py` |
| **Full suite command** | the 4 required files (`test_baseline_generations`, `test_tower_ratchet`, `test_tower_donegate`, `test_family_baselines`) + regression set (`test_tower_select`, `test_tower_checks`, `test_tower_capsule`, `test_tower_inheritance`, `test_family_injection`, `test_tower_o4`) |
| **Estimated runtime** | ~60 seconds |

Failure = non-zero exit OR a `FAIL` line OR `PASS=n/m` with n<m.

## Sampling Rate

- **After every task commit:** the NEW file + the test file of the touched module.
- **After every plan wave:** full suite, bracketed by the sorted dirty-path SET before/after (changed set -> INCONCLUSIVE).
- **Before verify:** full suite green + F0 sha table (blob/LF form) re-checked.
- **Max feedback latency:** 60 seconds

## Per-Task Verification Map

| Criterion | Requirement | Automated Command | Passing output | Status |
|---|---|---|---|---|
| 1 reanchor + 9 entries | UCEP-01 | `tools/test_ucep_baseline_integrity.py` (V-UCEP-REANCHOR-*) + `tools/test_baseline_generations.py` | `BASELINE_GENERATIONS_PASS=16/16`; generations == [0, 1] for persistent_state, wii_homebrew | pending |
| 2 diff fields, unanchored, allowlist, H1/H2/H3b | UCEP-01 | V-UCEP-H1/-H2/-H3B (+ -CONTROL) on a B0-only synthetic family + `tools/test_tower_ratchet.py` | `TOWER_RATCHET_PASS=21/21`; RED proof on pre-change code recorded in EVIDENCE | pending |
| 3 N/A vocabulary + cap; `test:` UNJUDGED | UCEP-01 | `tools/test_ucep_donegate_exits.py` (V-UCEP-H5-*, V-UCEP-H6-*, V-UCEP-NO-EXEC-*; separate file so plan 01-02 runs in wave 1 beside 01-01) + `tools/test_tower_donegate.py` + `tools/test_tower_checks.py` | `UCEP_DONEGATE_EXITS_PASS=13/13`; `TOWER_CHECKS_PASS=23/23` unchanged; no `verdict=DELEGATED` for a `test:` check | pending |
| 4 discovery walk + floor | UCEP-01 | V-UCEP-DISCOVER-* + both edited tests; hardcoded-tuple grep returns nothing | discovered counts cited | pending |
| 5 green + immutability | UCEP-01 | full suite + LF sha256 of 5 pre-existing generation files == F0 table | all PASS; hashes equal | pending |

## Wave 0 Requirements

- [ ] `tools/test_ucep_baseline_integrity.py` (NEW) — all V-UCEP-* gates, RED first against unchanged code
- [ ] Line-ending normalisation (`.gitattributes` + re-checkout) before any generation write; `git ls-files --eol` -> `w/lf`
- [ ] F0 sha table (blob form) recorded at start, recomputed at end

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
