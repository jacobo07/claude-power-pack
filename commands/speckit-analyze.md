# /speckit-analyze

Cross-artifact consistency check: detect drift between `constitution.md`, `spec.md`, `plan.md`, and `tasks.md` BEFORE implementation. Power-Pack-flavoured wrapper around the SDD `/speckit.analyze` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-tasks` and before `/speckit-implement`.
- After any mid-stream edit to spec, plan, or tasks (the change may invalidate downstream artifacts).
- As a forensic step when implementation surprises arise.

NOT for: post-commit verification (that's `/ovo-audit`).

## What it produces

A `./.specify/specs/<feature-id>/analyze-<iso>.md` report listing every detected drift, classified as:

- **BLOCKING** — implementation would produce a wrong feature (e.g. a `T-###` task contradicts an `FR-###` requirement). Resolve before implement.
- **CONSISTENCY** — artifact drift that should be reconciled but does not block (e.g. a renamed file in plan not reflected in tasks).
- **INFO** — observation, no action required.

## Process

1. **Load all four.** `constitution.md`, `spec.md`, `plan.md`, `tasks.md`. If any is missing, abort with "PASO -1 incomplete".
2. **Principle ↔ Plan trace.** Every plan choice MUST trace to a constitution principle OR a spec FR/SC. List orphaned choices.
3. **FR ↔ Plan trace.** Every `FR-###` MUST map to at least one plan section. List orphaned FRs.
4. **Plan ↔ Tasks trace.** Every plan file-map entry MUST have at least one `T-###` that touches it. List orphans.
5. **Tasks ↔ FR/US trace.** Every `T-###` MUST cite a `FR-###` or `US-###`. List untraceable tasks.
6. **Done-Gate consistency.** The plan's Done-Gate commands MUST be reachable by the tasks; if a Done-Gate command depends on a file no task creates, that's BLOCKING.
7. **Clarifications echo.** Every entry in `spec.md`'s `## Clarifications` MUST be reflected in either an `FR-###` or an Edge Case. Otherwise the clarification was wasted.
8. **Write the report.**
9. **Commit.** `git commit -m "verify(analyze): <feature-id> <N> blocking / <M> consistency / <K> info"`.

## Done-Gate

- Report file exists at `./.specify/specs/<feature-id>/analyze-<iso>.md`.
- Zero **BLOCKING** drifts; if any exist, `/speckit-implement` is denied until they resolve.
- Consistency drifts are explicitly accepted (with rationale) or fixed.

## PP layering

- Reality Contract: drift detection is NOT optional polish — it prevents the "code compiles but feature wrong" failure mode (Mistake #16).
- Honest no-guess: if traceability cannot be determined, mark BLOCKING and surface, do NOT assume the link.
- Pairs with OVO (post-commit): `/speckit-analyze` is pre-commit drift catch; OVO is post-commit verdict.

## Chain

→ Resolve any BLOCKING items by editing the upstream artifact, then re-run `/speckit-analyze`.
→ When clean → `/speckit-implement`.
