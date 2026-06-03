# Spec-Driven Department (2026-06-03, BL-SPEC-DEPT-001)

Plan-backup / decision record. Doctrine: SCS C32
(`vault/knowledge_base/apex_baseline_doctrine.md`).

## Goal
Three proactive agents on the existing PP dispatcher:
- **pp-spec-guardian** -- L/XL task starting with no spec in the repo.
- **pp-premise-guardian** -- CLASE 1 unverified-premise risk (session erred).
- **pp-error-analyst** -- recurrence >= 3 without a covering Hard Rule.

## FASE -1 corrections (the plan's snippets would not run -- CLASE 1)
1. Signal contract is `evaluate(...) -> ProactiveSignal | None` (dataclass),
   not `check_*` returning dicts. Dispatcher calls `module.evaluate(...)`.
2. `top_recurring()` returns `NeverAgainEntry` dataclasses -> `.recurrence`
   / `.issue` attribute access, never `.get`; field is `recurrence` not
   `count` (plan's `e.get('count')` would raise AttributeError).
3. Register in the `plan` list + `AGENT_CONFIGS` (throttle built-in via
   `cooldown_minutes`); `dispatch()` returns `list[str]` not dicts.
4. Dispatcher ctx had no `prompt`/`cwd` -> spec signal would be a CLASE 0
   orphan. JIT `ctx_in` now feeds both; `V-DEPT-CTX-FEED` gate guards it.

## Self-imposed invariants (beyond the plan)
- All 3 signals gate on a context field so a clean context still
  dispatches to `[]` -> `test_proactive_agents::V-DISPATCHER-CLEAN` green.
- error_recurrence reads HR text in-process (one file read), never a
  subprocess on the UserPromptSubmit hot path (measurement doctrine).
- HR-001: agent .md staged in `vault/agents/` + installer, not written to
  `~/.claude/agents/` (auto-mode denies; cold-load needs /restart).

## What shipped
| File | Role |
|---|---|
| vault/agents/pp-spec-guardian.md | agent definition (staged) |
| vault/agents/pp-premise-guardian.md | agent definition (staged) |
| vault/agents/pp-error-analyst.md | agent definition (staged) |
| tools/install_department_agents.ps1 | Owner-side installer (HR-001) |
| modules/pp_agents/signals/spec_compliance.py | spec-guardian signal |
| modules/pp_agents/signals/premise_risk.py | premise-guardian signal |
| modules/pp_agents/signals/error_recurrence.py | error-analyst signal |
| modules/pp_agents/proactive_dispatcher.py | imports + AGENT_CONFIGS + plan |
| tools/jit_skill_loader.py | ctx_in feeds prompt + cwd |
| tools/test_spec_department.py | 13 V-gates |
| tools/verify_spp.py | spec-department row (STRICT) |
| apex_baseline_doctrine.md | SCS C32 |

## Evidence
- test_spec_department 13/13 | test_proactive_agents 16/16 (no regression,
  V-DISPATCHER-CLEAN + V-BASELINE-INTACT pytest 43 passed)
- verify_spp --row spec-department STRICT PASS (0.41s)
- dispatch smoke: clean -> [], large prompt -> pp-spec-guardian surfaces

## Honest residuals
- Agents are dispatchable only AFTER the Owner runs the installer +
  /restart (HR-001 + cold-load). Until then they live as advisory signals
  through the dispatcher (which IS live this session via the JIT hook).
- With 11 signals competing for MAX_ADVISORIES_PER_TURN=3, the 3 new ones
  are appended last (least-invasive, SCS C30). On a fresh task prompt the
  data-dependent signals are silent, so spec-guardian reliably gets a slot;
  if the Owner wants it prioritized, reorder the `plan` list (tuning, not a
  bug).
- pp-spec-guardian's intent overlaps the TASK 3 spec-domain card, but is
  distinct: it verifies actual spec-FILE absence (check_spec_gate), which
  the intent card does not.
