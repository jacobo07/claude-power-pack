---
type: component
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-sdd-internal-inventory]
path: modules/sdd_os/, modules/spec_gate/gate.py, governance/SDD_OS_GOVERNANCE.md
status: LIVE
---

# SDD-OS (Spec-Driven Development OS)

Per-prompt check that classifies a task T0–T3 and, from T2 up, tells the agent to write a spec
before editing. Doctrine: `vault/knowledge_base/sdd_os/` (PARTE 01–06 + MASTER). Standing rule: the
"SDD-OS" section of `~/.claude/CLAUDE.md`.

## How it reaches the agent (LIVE)

`settings.json` UserPromptSubmit → `hooks/hook-dispatcher.js` → `tools/jit_skill_loader.py:1288-1321`
→ `modules/sdd_os/activation.py::build_directive` → injected as `additionalContext`. Advisory and
fail-open. Silent when the prompt is under 40 characters, throttled for 20 minutes per prompt, and
silent for T0 with no spec ([[2026-10-01-sdd-internal-inventory]]).

## Capability status @ e0f541f

| capability | status |
|---|---|
| Tier classification + spec binding + injected directive | LIVE |
| Standing CLAUDE.md instruction | LIVE |
| Spec skeleton generation | LIVE via the CLI only; the hook never writes |
| Refusing edits without a spec | ABSENT (wording only) |
| Checking a spec's content (sections, testable AC, status, tier) | ABSENT |
| AC → test traceability (`intent_verified`) | PLANNED (CLI-only, keyed on V-gate ids) |
| Per-tier done floor (`TIER_OQS_FLOOR`) | PLANNED (tests only) |
| Spec drift check | PLANNED (CLI-only mtime heuristic) |
| Task decomposition, open questions, ambiguity scanner | ABSENT |
| `/cpp-sdd-os`, `/prd-tier0..3` commands | PLANNED (not installed) |
| Spec Kit (`.specify/`) | ABSENT in practice |

Gaps, verified defects and ranked fixes: [[sdd-os-gap-analysis]].
