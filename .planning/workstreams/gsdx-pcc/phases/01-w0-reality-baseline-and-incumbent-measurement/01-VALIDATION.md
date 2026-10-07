---
phase: "1"
slug: "w0-reality-baseline-and-incumbent-measurement"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-07"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 01-RESEARCH.md § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none (project convention): standalone Python scripts printing `<SUITE>_PASS=n/m  threshold=n/m`, exit 0 iff all pass |
| **Config file** | none |
| **Quick run command** | `python tools/test_gsd_x_goal_gate_provider.py` |
| **Full suite command** | each `tools/test_gsd_x_goal_*.py` serially + `tools/test_gsd_x_goal.py`; `test_gsd_x_goal_mutation.py` only in a throwaway copy |
| **Estimated runtime** | UNKNOWN until Phase 1 measures it (that measurement is a phase deliverable) |

---

## Sampling Rate

- **After every task commit:** `python tools/test_gsd_x_goal_gate_provider.py`
- **After every plan wave:** all summary suites serially + `tools/test_gsd_x_goal.py`
- **Before `/gsd-verify-work`:** gate_provider 18/18, drill KILLED, liveness decision recorded, EVIDENCE.md complete
- **Max feedback latency:** gate_provider run (seconds; exact value recorded in EVIDENCE.md)

---

## Per-Task Verification Map

| Check | Requirement | Test Type | Automated Command | Failing signal | File Exists | Status |
|-------|-------------|-----------|-------------------|----------------|-------------|--------|
| R01 red | R01 | existing suite | `python tools/test_gsd_x_goal_gate_provider.py` | must show `FAIL V-GATE-VERDICT-FIELDS`, `17/18`, exit 1 BEFORE the fix | ✅ | ⬜ pending |
| R01 green | R01 | existing suite | same | any FAIL line, exit != 0, or summary != `18/18` | ✅ | ⬜ pending |
| R01 mutation | R01 | drill | `python tools/mutation_drill.py --spec <phase>/r01-drill.json` | exit 1 SURVIVED / 2 UNJUDGED / 3 HARNESS / 4 CONTROL_INVALID; only `KILLED gate=V-GATE-VERDICT-FIELDS` exit 0 passes | ❌ W0 | ⬜ pending |
| R01 no collateral | R01 | existing suites | every summary suite vs spec baseline (reconcile 22, judge 11, convergence 29, sweep 14, epoch 19, chaos 15, mutation_safety 8) | count differs from baseline | ✅ | ⬜ pending |
| R01 UKDL | R01 | grep | `Select-String -Path vault\knowledge_base\ukdl-universal.md -Pattern '^### T-SUBPROCESS-'` | no match | ❌ W0 | ⬜ pending |
| SC3 incumbent table | — | measurement + EVIDENCE.md | timing loop; `judge` without `--record`; `GoalLog.read()` timeline | a number without its command + exit code; an estimate where UNKNOWN is due | ❌ W0 | ⬜ pending |
| Liveness | — | gate | `python modules/liveness/reachability.py` | exit 1 with offenders NOT in the recorded baseline (57 at fbca24fc) | ✅ | ⬜ pending |
| Hermeticity | — | fingerprint | file count + max mtime of `~/.claude/state/gsd-x` equal before/after | any change | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `r01-drill.json` drill spec (phase dir)
- [ ] timing/timeline script (under `tools/` or phase dir)
- [ ] baseline fingerprint step for `~/.claude/state/gsd-x`
- [ ] UKDL T-entry text

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency recorded
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
