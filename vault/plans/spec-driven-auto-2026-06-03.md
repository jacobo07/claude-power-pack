# Spec-Driven-Auto + Root Cause (2026-06-03, BL-SPEC-GATE-001 + BL-PREMISE-001)

Plan-backup / decision record. Doctrine: SCS C31
(`vault/knowledge_base/apex_baseline_doctrine.md`) + root-cause taxonomy
(`vault/knowledge_base/root_cause_taxonomy.md`).

## Owner decision
- Scope: **Full 9-block plan** (chosen over the lean alternative).
- premise_verifier wiring: **Tool + HR + verify_spp row** (chosen).

## FASE -1 corrections applied (not optional -- the plan wouldn't run without them)
1. `compile_contract` is 2-param + pure -> M4 added an OPTIONAL `cwd=None`
   (backward-compatible advisory), not the plan's non-existent 4-param API.
2. auto-testing fails to import -> synthetic cards only for karimo + arch
   (which work); none for auto-testing.
3. Triple-injection risk -> spec-domain card is MUTEX with the already-firing
   `_oneshot_contract_inject` (decorator reorder).
4. Emoji snippets -> ASCII (Windows cp1252 + slop discipline).

## FASE -1 evidence
- Spec-driven pipeline LARGELY pre-existed: `_oneshot_contract_inject`,
  `_arch_check_inject`, `_active_spec`, `_detect_new_feature_intent_and_flag`.
  This build added the spec DOMAIN + gate + premise verifier, not a parallel
  pipeline.
- NEVER_AGAIN #1 recurring class is orphan/wiring (CLASE 0), not "plan
  assumes API" -> premise_verifier wired (never a bare library).

## What shipped (commits 514b6f0, 23f5957, 78167ca, + BLOQUE D)
| Block | File | Role |
|---|---|---|
| A | intent_classifier.py | "spec" domain (L/XL signals, EN+ES) |
| A | skill_index.py | SkillEntry.invoke + synthetic karimo/arch cards |
| A | jit_skill_loader.py | invoke-aware card + One-Shot mutex + stack reorder |
| B | spec_gate/gate.py | check_spec_gate (L/XL spec detection) |
| B | one_shot/compiler.py | optional cwd advisory (pure by default) |
| C | error_prevention/premise_verifier.py | CLASE 1/2 fix + --self-test CLI |
| C | CLAUDE.md | HR-PREMISE-001, HR-SPEC-001, HR-CONTEXT-001 (34 HRs) |
| D | tools/test_spec_driven.py | 11 V-gates |
| D | tools/verify_spp.py | spec-driven + premise-verifier rows |
| D | apex_baseline_doctrine.md | SCS C31 |
| D | root_cause_taxonomy.md | evidence-ranked CLASE 0-5 + meta-fix |

## Evidence
- test_spec_driven 11/11 | sleepy 8/8 (no regression) | premise self-test exit 0
- verify_spp spec-driven + premise-verifier rows STRICT PASS | bug_to_hardrule --list = 34
- V-CROSS-REPO: 72 skills indexed from a foreign cwd

## Honest residuals
- vault/hard_rules/HARD_RULES.md is a pre-existing stale/partial archive
  (~7 of 34 HRs); operative source is the CLAUDE.md block. Not expanded here.
- Root-cause taxonomy written to a dedicated file (not ukdl-universal.md)
  because that file was under active multi-pane edit at seal time.
- apex "v18" axis label: no separate apex-axis registry found; SCS C31 is
  the apex seal (not inventing a v18 registry entry).
- context_pct still not threaded from the hook (inherited from C30).
