# /speckit-plan

Translate a clarification-free spec into a **technical plan**: stack, architecture, file-level layout, sequencing. Power-Pack-flavoured wrapper around the SDD `/speckit.plan` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-spec` (and `/speckit-clarify` if it ran).
- Before `/speckit-tasks` — task breakdown depends on the plan's architecture.

NOT for: re-architecting an already-implemented feature (that's a new spec).

## What it produces

`./.specify/specs/<feature-id>/plan.md`, populated from `vault/templates/speckit/plan.md.template`. Contains: stack choices, file map, module dependencies, sequencing graph, risk register, done-gate.

## Process

1. **Read.** Load `.specify/memory/constitution.md` (principles) + the active `spec.md` (requirements) FULLY before any plan content.
2. **Stack.** Choose languages, frameworks, libraries. Each choice MUST trace to a principle ("Library-First" → split into 3 libs; "Test-First" → property-based testing) OR a requirement ("FR-007 retention ≥30d" → durable store).
3. **File map.** List every file the plan will create/modify, with one-line purpose each.
4. **Sequencing.** Order the work so each step compiles + tests cleanly before the next starts. No leap-frog dependencies.
5. **Risk register.** What can break? What's the rollback? Each P1 user story gets a risk entry.
6. **Done-Gate.** Concrete commands that exit 0 prove the feature works (e.g. `pytest tests/feature/`, `node tools/test_feature.js`, `tools/verify_full_install.py`).
7. **Commit.** `git commit -m "feat(plan): <feature-id> architecture + sequencing"`.
8. **Next.** `/speckit-tasks`.

## Done-Gate

- `.specify/specs/<feature-id>/plan.md` exists.
- Every stack choice has a one-line justification linked to a principle or FR.
- File map enumerates every file the plan touches.
- Done-Gate section contains REAL commands (not aspirations).
- Risk register has at least one entry per P1 user story.

## PP layering

- Reality Contract: every numeric claim in the plan ("<2s latency", "70% compression") must be either measured upstream OR explicitly flagged as a hypothesis to verify in implement.
- Micro-Commit: the sequencing section maps directly onto the commit chain — one commit per sequenced step.
- OVO Gate: the plan's Done-Gate commands ARE what OVO will verify before allowing push.

## Chain

→ `/speckit-tasks`
