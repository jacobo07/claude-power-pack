---
phase: "0"
slug: "spec-gen2-freeze-novelty-gate"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-05"
---

# Phase 0 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 00-RESEARCH.md § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | repo V-gate scripts (plain Python, `PASS/FAIL V-XXX` lines, exit code, `--selftest`/`--drill` mutant modes; stdlib, not pytest) |
| **Config file** | none |
| **Quick run command** | `python3 tools/test_gex44_env_preflight.py` ; `python3 tools/test_incremental_cognition_program.py --selftest` |
| **Full suite command** | `python3 tools/test_gex44_env_preflight.py --drill && python3 tools/test_incremental_cognition_program.py --selftest && python3 tools/test_incremental_cognition_program.py --generation 2 --selftest && python3 tools/test_incremental_cognition_program.py --generation 2 --status && python3 tools/test_ao_p0.py` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** run the single suite the task touches (each < 30 s).
- **After every plan wave:** full suite command.
- **Before `/gsd-verify-work`:** full suite green. `--final` is EXPECTED red for gen1 L3/L8 and gen2 L3/L8 until later phases; record the exact red lines in EVIDENCE.md, never claim green.
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Criterion | Requirement | Test Type | Automated Command | File Exists | Status |
|-----------|-------------|-----------|-------------------|-------------|--------|
| 1 spec READY, binds without AMBIGUOUS, sections present | AO-01 | unit + mutants | `python3 tools/test_ao_p0.py` | ❌ W0 | ⬜ pending |
| 2 gen2 ledger + FROZEN_AT, gen1 untouched, mutant per rule | AO-02 | unit + selftest | `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` ; `--generation 2 --status` ; `--selftest` | ❌ W0 | ⬜ pending |
| 3 novelty record EXTEND_EXISTING_OWNER, 13 answers, citations resolve | AO-01 | unit + mutants | `python3 tools/test_ao_p0.py` | ❌ W0 | ⬜ pending |
| 4 champion numbers frozen with commands + pinned evidence | AO-02 | unit | `python3 tools/test_incremental_cognition_program.py --generation 2 --status` | ❌ W0 | ⬜ pending |
| 5 preflight floor-by-pick fix; first opportunity row | AO-02 | unit + drill | `python3 tools/test_gex44_env_preflight.py --drill` ; `python3 tools/gex44_env_preflight.py --current --checks pp_install` | partial | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/ic_gen2.py` — gen2 judge + selftest (G2-* rules)
- [ ] `tools/test_ao_p0.py` — spec / novelty V-gates with mutants
- [ ] `tools/test_gex44_env_preflight.py` — new floor-by-pick gates written red first, drill retarget
- [ ] Framework install: none (stdlib)

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
