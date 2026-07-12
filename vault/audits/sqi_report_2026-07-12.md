# SQI Report — claude-power-pack

> Generated 2026-07-12 16:27 UTC by `tools/run_sqi.py`. Commit `ca05e467`.
> The executable layer of the SQI corpus. Doctrine: `vault/knowledge_base/sqi/`.

## Verdict

- **Baseline guardian:** `BASELINE_PASS`
- **Weakening detectors:** `WEAKENING_PASS`
- **Signal integrity:** `PARTIAL_GREEN` → ontology `PARTIALLY-VERIFIED`
- **Environment:** `PARTIALLY_QUALIFIED` — verdict ceiling: per-surface; UNVERIFIED or BLOCKED for the unobserved
- **Reach under the authoritative invocation:** `UNKNOWN`
- **Orphaned test files:** **98** of 101 authored

## Baseline guardian (SQI-02 Part XII)

BASELINE_PASS: 76 executed across 1 root(s), 101 authored, reach=3.0% (stable)

Baseline: `sqi_baseline.json` · environment `b5ec3ed51c2f23b1` · ratcheted this run: False

## Weakening detectors (SQI-02 Part XV)

WEAKENING_PASS: 101 file(s) tracked, 2106 assertion(s), 0 for review, 0 advisory, 23 unknown. No assertion was lost.

The guardian above gates **counts**, so it catches deletion, the skip, and the relocation. Weakening lowers **no count at all**: the file is present, the case is collected, the case passes, and the protection is gone (§15.1). These gates read the **content** of the surviving tests.

**Not detected here, and declared rather than faked:** the lowered threshold (§15.7) needs a threshold inventory that does not exist in this repository, and the unreal fixture (§15.4) has no counting detector by the Part's own admission. The tautological assertion (§15.8) is detectable **only** by a mutation probe — `--mutation-probe` runs it; it executes tests and mutates source, so it is never part of a default measurement.

## Findings

- INERT-IN-ROOT (4): authored test files that live INSIDE a canonical invocation's root and yield zero collected cases. They are inside the reach boundary and protect nothing. The founding audit counted these as reached, because it counted files in the directory rather than identities in the manifest: ['tests/test_globalization.py', 'tests/test_graphify_live.py', 'tests/test_hooks_registration.py', 'tests/test_mistake_frequency_xplat.py']
- AUTHORITATIVE INVOCATION BROKEN: `pytest` (oracle=zero_arg_default) exits 3 and produces no manifest. Reach under the estate's de facto canonical command is UNKNOWN, not zero. Blocker (verbatim):

  ```
  INTERNALERROR>   File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  INTERNALERROR>   File "C:\Users\User\AppData\Local\Programs\Python\Python312\Lib\site-packages\_pytest\assertion\rewrite.py", line 197, in exec_module
  INTERNALERROR>     exec(co, module.__dict__)
  INTERNALERROR>   File "C:\Users\User\.claude\skills\claude-power-pack\_logs\_m1_secret_firewall_test.py", line 118, in <module>
  INTERNALERROR>     sys.exit(0 if passes == total else 1)
  INTERNALERROR> SystemExit: 0
  no tests collected in 0.89s
  mainloop: caught unexpected SystemExit!
  ```

## 1. Repository reality (SQI-01)

- Languages: python, javascript
- Domains: agent_system, prompt_system, content_vault, frontend_application, cli_tool, hybrid_monorepo, library
- Lock state: python=UNLOCKED, javascript=UNLOCKED
- Authored test artifacts: 106
- Discovery rule hits: `{"python:test_*.py": 88, "python:*_test.py": 13, "javascript:*.test.js": 5}`
- **Engine uncertainty:** 2 files matched no rule but live where tests live

## 2. Environment qualification (SQI-03)

| gate | result | observed |
|---|---|---|
| `host_census` | PASS | Windows 11 / py3.12.10 |
| `toolchain_presence` | PASS | present: ['python', 'javascript']; absent: [] |
| `toolchain_version` | PASS | python=Python 3.12.10; javascript=v24.15.0 |
| `dependency_resolvability` | UNKNOWN | manifest present with no resolved lock: ['python', 'javascript'] |
| `build_reachability` | PASS | pytest 9.0.3 |
| `service_availability` | UNKNOWN | no external service contract declared; not evaluated |
| `harness_containment` | UNKNOWN | requires a differential observation around a run; not performed |

## 3. Test reach reconciliation (SQI-02)

### Canonical invocation set

| oracle | command | authoritative | status | exit | files | cases | verdict |
|---|---|---|---|---|---|---|---|
| documentation | `pytest tests/` | no | `OK` | 0 | 3 | 76 | `PARTIAL_GREEN` |
| zero_arg_default | `pytest` | **yes** | `BROKEN` | 3 | 0 | UNKNOWN | `UNKNOWN` |

Precedence (SQI-02 §9.4): a CI job is authoritative where one exists, because it is the only oracle backed by an observation rather than an intention. Where none exists, the zero-argument default is authoritative — it is what a human, a hook, or an agent with no prior context will actually type. **Documentation is never authoritative.**

### Metrics

| metric | value |
|---|---|
| Test File Reach | 3.0% (3/101) |
| Test Case Reach | UNKNOWN |
| Suite Activation Ratio | 11.1% |
| **Orphaned Test Count** | **98** (absolute) |
| Orphaned Ratio | 97.0% |
| Silent Collection Loss | 0 |
| Executed Protection Ratio | 4.4% |
| Surprise set (self-audit) | 0 |
| Hermetic runs | 3 → stable: True |

Test Case Reach is `UNKNOWN` and is not estimated. Establishing it requires parsing every orphaned file, which nothing in this pipeline has ever done. **The unknown is the finding** (SQI-02 §7.6): a repository that cannot state how many cases it has authored cannot compute the metric that would tell it how many are protecting anything, and an engine that filled the gap with an estimate would manufacture the exact false confidence it exists to destroy.

### Self-reach (mandatory — SQI-02 §5.10)

- Engine: `modules/sqi` · reached: **True** · report admissible: **True**
- exercised by `tests/test_sqi_engine.py`

*An auditor exempt from its own audit is not an auditor.* A report without a positive self-reach assertion is inadmissible.

### Unprotected surface (65 elements)

Module packages with **zero references from any test the canonical invocation reaches**. This is the only metric here whose denominator is risk rather than tests (SQI-02 §8.6) — the metric that catches a green suite standing beside an unprotected surface.

- `modules/agent-governance`
- `modules/agent-lightning`
- `modules/akos_knowledge`
- `modules/arch-decision`
- `modules/auto-testing`
- `modules/autoresearch`
- `modules/backlog_autopilot`
- `modules/backup`
- `modules/bug-hunter`
- `modules/cascade_prevention`
- `modules/cdio`
- `modules/code-review`
- `modules/code_review`
- `modules/cognitive_os`
- `modules/cost_collapse`
- `modules/cpc_os`
- `modules/daemon`
- `modules/dataset_first`
- `modules/decision_review`
- `modules/deep-research`
- `modules/deployment`
- `modules/design-md`
- `modules/dispatcher`
- `modules/done_gate`
- `modules/duplicate_to_advantage`
- `modules/error_prevention`
- `modules/executionos-lite`
- `modules/fable_distillation`
- `modules/frontier_intelligence`
- `modules/governance-overlay`
- `modules/graphify`
- `modules/hard_rules`
- `modules/harness`
- `modules/infrastructure`
- `modules/karimo-harness`
- `modules/liveness`
- `modules/memory-engine`
- `modules/monitoring`
- `modules/omnicapture`
- `modules/omniram-sentinel`
- `modules/one_shot`
- `modules/osa`
- `modules/output_contracts`
- `modules/owner_queue`
- `modules/parallel_mesh`
- `modules/pp_agents`
- `modules/recall_roi`
- `modules/refcheck`
- `modules/rollback`
- `modules/rtk-core`
- `modules/rule_compiler`
- `modules/sdd_os`
- `modules/secret_firewall`
- `modules/session-continuity`
- `modules/session_resilience`
- `modules/setup_os`
- `modules/skill_router`
- `modules/sleepless_qa`
- `modules/spec_gate`
- `modules/sweep_enforcer`
- `modules/token-optimizer`
- `modules/universal-meta-systems`
- `modules/uqf`
- `modules/wrapper`
- `modules/zero-crash`

### Orphaned test files (98)

The list, not the percentage. A reader shown 98 paths reacts differently from a reader shown a percentage, and the difference in reaction is the entire point of publishing it (SQI-02 §8.2).

- `_logs/_m1_secret_firewall_test.py`
- `_logs/_m3_backlog_signal_test.py`
- `_logs/_m4_cascade_prevention_test.py`
- `_logs/_m4_oneshot_jit_test.py`
- `_logs/_m5_output_contracts_test.py`
- `_logs/_m6_one_shot_test.py`
- `_logs/_m7_cost_collapse_test.py`
- `_logs/_m8_backlog_test.py`
- `_logs/_m9_cpc_os_test.py`
- `modules/arch-decision/test_closed_loop.py`
- `modules/arch-decision/test_v_block.py`
- `modules/auto-testing/auto_test.py`
- `modules/backup/test_v_block.py`
- `modules/code-review/test_closed_loop.py`
- `modules/code-review/test_combined_gate.py`
- `modules/code-review/test_v_block.py`
- `modules/deployment/test_v_block.py`
- `modules/rollback/test_v_block.py`
- `tests/test_globalization.py`
- `tests/test_graphify_live.py`
- `tests/test_hooks_registration.py`
- `tests/test_mistake_frequency_xplat.py`
- `tools/ghost_driver_test.py`
- `tools/lazarus_forensic_test.py`
- `tools/shadow_sandbox_test.py`
- `tools/test_ads.py`
- `tools/test_akos_integration.py`
- `tools/test_atomic_branding.py`
- `tools/test_auto_reset.py`
- `tools/test_autoresearch_vps.py`
- `tools/test_build_everything.py`
- `tools/test_cdio.py`
- `tools/test_ceps_closed_loop.py`
- `tools/test_ceps_edge_cases.py`
- `tools/test_ceps_full_cycle.py`
- `tools/test_claude_md_router.py`
- `tools/test_co12_readiness_telemetry.py`
- `tools/test_co12_telemetry.py`
- `tools/test_cognitive_leak_taxonomy.py`
- `tools/test_cognitive_os_build.py`
- `tools/test_compact_rescue.py`
- `tools/test_conversation_quality_audit.py`
- `tools/test_cpc_snapshot.py`
- `tools/test_dataset_build.py`
- `tools/test_dataset_first_protocol.py`
- `tools/test_decision_review.py`
- `tools/test_duplicate_to_advantage.py`
- `tools/test_enforcement_systems.py`
- `tools/test_fable_distillation.py`
- `tools/test_frontier_intelligence_os.py`
- `tools/test_governance_propagation.py`
- `tools/test_hard_rules.py`
- `tools/test_hibernation.py`
- `tools/test_hook_hubs.py`
- `tools/test_jit_performance.py`
- `tools/test_karimo.py`
- `tools/test_lateral_thinking.py`
- `tools/test_manual_tools_automation.py`
- `tools/test_meta_systems_runtime.py`
- `tools/test_mirror_parity.py`
- `tools/test_monitoring.py`
- `tools/test_osa.py`
- `tools/test_pane_map.py`
- `tools/test_pane_map_snapshot.py`
- `tools/test_parallel_mesh.py`
- `tools/test_playwright_resilience.py`
- `tools/test_proactive_agents.py`
- `tools/test_ram_optimization.py`
- `tools/test_recovery_control_plane.py`
- `tools/test_rename_sessions.py`
- `tools/test_restart_and_lag.py`
- `tools/test_restart_kclear.py`
- `tools/test_restore_all_panes.py`
- `tools/test_scope_a_activation.py`
- `tools/test_sdd_os.py`
- `tools/test_session_resilience.py`
- `tools/test_session_resilience_build.py`
- `tools/test_setup_os.py`
- `tools/test_sleepy_skills.py`
- `tools/test_sovereign.py`
- `tools/test_spec_department.py`
- `tools/test_spec_driven.py`
- `tools/test_speckit.py`
- `tools/test_sqi.py`
- `tools/test_strategic_gaps.py`
- `tools/test_tab_order.py`
- `tools/test_tco.py`
- `tools/test_tco_tracking.py`
- `tools/test_tis_core.py`
- `tools/test_tis_e2e.py`
- `tools/test_token_corpus_audit.py`
- `tools/test_topology_reconcile.py`
- `tools/test_uqf.py`
- `tools/test_vague_lint.py`
- `tools/test_vscode_autorun.py`
- `tools/test_weekly_burn_tracking.py`
- `tools/test_wrapper.py`
- `tools/test_zero_command.py`

## Reproduce

```
python tools/run_sqi.py
```
