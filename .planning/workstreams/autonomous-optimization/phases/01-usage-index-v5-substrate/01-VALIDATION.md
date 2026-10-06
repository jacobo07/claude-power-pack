---
phase: "1"
slug: "usage-index-v5-substrate"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-06"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 01-RESEARCH.md § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | repo V-gate scripts (plain Python, `ok(gate, cond, evidence)`, final line `X_PASS=n/n  threshold=n/n`; stdlib, not pytest); AAA + paired controls |
| **Config file** | none |
| **Quick run command** | `python3 tools/test_usage_index.py && python3 tools/test_usage_index_v5.py` |
| **Full suite command** | quick + `python3 tools/test_usage_index_identity.py` + consumer regression set (01-RESEARCH.md § Validation Architecture) + `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` |
| **Estimated runtime** | quick ~30 s; full a few minutes; corpus measurement steps (parity, cost) minutes |

---

## Sampling Rate

- **After every task commit:** Run the quick command
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite green, THEN the two corpus measurement steps (parity, cost) with commands and output in `01-EVIDENCE.md`, every row labelled `plane: gex44`
- **Max feedback latency:** 150 seconds (hermetic)

---

## Per-Task Verification Map

Filled by the planner from the Phase Requirements -> Test Map in 01-RESEARCH.md. Gates by clause of the frozen
pillar O rule:

| Clause | Gate(s) | Test Type | Automated Command | File Exists | Status |
|--------|---------|-----------|-------------------|-------------|--------|
| O(1) schema | V-UX5-SCHEMA, V-UX5-TOOL-EVENT, V-UX5-CWD | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(2) zero re-read | V-UX5-MIGRATE-ZERO-REREAD (+ control that does read) | unit, open spy | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(3a) mixed project | V-UX5-MIXED-BOTH, V-UX5-MIXED-CONTROL | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(3b) distinct histories | V-UX5-HISTORIES-NOT-MERGED, V-UX5-COPY-ONCE | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(3c) junction alias | V-UX5-ALIAS-ONCE + identity gate | unit (symlink) | `python3 tools/test_usage_index_identity.py` | partial (Linux crash) | ⬜ pending |
| O(3d) `_archived` | V-UX5-ARCHIVED-RULE, V-UX5-SHAPE-SKIP-VISIBLE | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(3e) parser failure | V-UX5-PARSE-ERROR-SURFACED, V-UX5-PARTIAL-LINE-NOT-ERROR | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(3f) empty population | V-UX5-EMPTY-REFUSES | unit | `python3 tools/test_usage_index_v5.py` | ❌ W0 | ⬜ pending |
| O(4) parity | population verb on the corpus copy | integration | `python3 tools/usage_index.py population ...` (verb created this phase) | ❌ | ⬜ pending |
| O(5) cost | cold + delta refresh measured | measurement | `refresh` on scratch DB / scratch copy | ❌ | ⬜ pending |
| ledger | pillar O row in gen2 `state` | gate | `python3 tools/test_incremental_cognition_program.py --generation 2 --status` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/test_usage_index_v5.py` — gates for every O clause, each refusal paired with an admitting control, plus mutant kills
- [ ] `tools/test_usage_index_identity.py` — `junction()` Linux fallback (`os.symlink`)
- [ ] Baseline run of the consumer regression set on the untouched tree

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Parity + cost on the 9.6 GB corpus copy | AOP-O (4), (5) | minutes-long measurement, not a per-commit gate | run the commands recorded in the plan, paste output into 01-EVIDENCE.md labelled `plane: gex44` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 150s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
