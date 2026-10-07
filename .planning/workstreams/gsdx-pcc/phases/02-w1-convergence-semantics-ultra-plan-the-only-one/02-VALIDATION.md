---
phase: "2"
slug: "w1-convergence-semantics-ultra-plan-the-only-one"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-07"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `02-RESEARCH.md` §Validation
> Architecture (lines 528-562).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | plain Python script suites (no pytest): `ok/bad/check` closures, summary line `<SUITE>_PASS=n/m  threshold=n/m`, exit 1 on any FAIL |
| **Config file** | none; each suite sets `sys.path` from `Path(__file__).resolve().parents[1]` |
| **Quick run command** | `python tools/test_gsd_x_goal_pcc_semantics.py` + `test_gsd_x_goal_reconcile.py` + `test_gsd_x_goal_convergence.py` + `test_gsd_x_goal_epoch.py` (add `test_gsd_x_goal_judge.py` when judge imports change) |
| **Full suite command** | all 17 incumbent `tools/test_gsd_x_goal_*.py` (mutation suite excluded, R11) + `tools/test_gsd_x_goal_pcc_semantics.py` + `tools/test_gsd_x_goal_pcc_replay.py` + `python modules/liveness/reachability.py` |
| **Estimated runtime** | quick ~5-14 s; full ~160 s cold (01-EVIDENCE.md:132 sum 154.1 s + new suites) |

All commands run from the PowerShell tool:
`Set-Location 'C:\Users\User\Apps\pp-gsdx-pcc'; $env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' <suite>; "EXIT=$LASTEXITCODE"`.

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite green at the Phase 1 counts (reconcile 22, judge 11, convergence 29, sweep 14, epoch 19, chaos 15, mutation_safety 8, gate_provider 18, goal 26, bind_mission 10, claude_providers 20, cli 25, codex 18, engine_identity 14, gate_class 11, long_run 16, sweep_all 11), plus the drills
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

Requirement -> gate map (task ids are assigned by the planner; every plan task cites the gates it lands):

| Requirement | Gates | Red case that MUST be driven and seen red |
|-------------|-------|-------------------------------------------|
| D01 proof states | `V-PCC-STATE-TRUTH-TABLE`, `V-PCC-STATE-LEGACY-MAP`, `V-PCC-STATE-NO-EVENT-NOT-INHERITED`, `V-PCC-STATE-UNKNOWN-TREE`, `V-PCC-STATE-NOT-IN-DISPOSITION` | mutants: `unknown` treated as `equal`; INHERITED without event; writes `o.disposition` -> KILLED by the named gate |
| D01 certificate | `V-PCC-CERT-CLAIM-REACCEPT`, `V-PCC-CERT-GATE-PIN-SCHEME`, `V-PCC-CERT-REVISION`, `V-PCC-CERT-POLICY-BUMP`, `V-PCC-FINGERPRINT-*` | mutant: fingerprint raises on a missing file / ignores `..` |
| D10 typed contract | `V-PCC-CONTRACT-LEGACY-ONE-ELEMENT`, `V-PCC-CONTRACT-WEAKENING-IGNORED`, `V-PCC-CONTRACT-MALFORMED-RAISES`, `V-PCC-CONTRACT-HIGHER-V-UNKNOWN`, `V-PCC-FRESHNESS-MAP`, `V-PCC-GATE-CLASSES-PINNED` | mutant: edit `GATE_CLASSES`; mutant: text scan drops FRESH_REQUIRED |
| D43 legacy replay | `V-PCC-REPLAY-G002`, `V-PCC-REPLAY-G001`, `V-PCC-REPLAY-SYNTHETIC`, `V-PCC-REPLAY-IGNORE-NEW-TYPES`, `V-PCC-DECIDE-SIG`, `V-PCC-GOLDEN-PRE-CHANGE`, `V-PCC-FIXTURE-MANIFEST`, `V-PCC-HERMETIC-HOME`, `V-PCC-LIVE-STORE-UNTOUCHED`; phase-scoped `V-PCC-NO-LEGACY-EDIT` (EVIDENCE command) | in-process mutants M1-M4 turn REPLAY red; on-disk drill `else: raise` in the `project_convergence` ladder |
| D44 event log only | `V-PCC-NO-SECOND-STORE`, `V-PCC-ADDITIVE-ONLY`, `V-PCC-PROJECTION-PURE`, `V-PCC-ENVELOPE`, `V-PCC-EXPORT-RESTORE-ROUNDTRIP` | mutant: a projection writes a cache file |
| D03 five laws | `V-PCC-LAW-SEMANTIC`, `V-PCC-LAW-PROOF-CONSERVATION-LEDGER`, `V-PCC-LAW-WORK-CONSERVATION`, `V-PCC-LAW-CONCURRENCY-DEF`, `V-PCC-LAW-UNKNOWN-ESCALATES` | one synthetic violating input per law |
| D01/D43 kill switches | `V-PCC-SWITCH-PARSE`, `V-PCC-SWITCH-OFF-IS-LEGACY` | mutant: reader ignores the env var |
| SC1 audit | `V-PCC-SPEC-RESOLVED`, `V-PCC-AUDIT-DISPOSED` | remove one disposition row -> red |
| liveness | `python modules/liveness/reachability.py` -> `gate offenders: 0`, exit 0 | -- |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] fixture capture step + `tools/fixtures/gsdx_legacy_goals/**` + `MANIFEST.json` + `.gitattributes` line `tools/fixtures/gsdx_legacy_goals/** -text`
- [ ] `tools/fixtures/gsdx_legacy_replay_golden.json` captured from the UNMODIFIED engine, committed BEFORE any seam module
- [ ] `tools/test_gsd_x_goal_pcc_replay.py` committed RED-first (fails for the right reason: module/golden absent)
- [ ] amended spec + `02-AUDIT.md` (auditor output persisted by the orchestrator) before seam code

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Auditor gap list is complete and every gap is dispositioned | SC1 | the auditor is an agent; completeness of its reasoning is not machine-checkable | `V-PCC-AUDIT-DISPOSED` checks count equality; the worker reads each disposition against its gap |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
