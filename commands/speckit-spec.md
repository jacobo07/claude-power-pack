# /speckit-spec

Create a **feature specification** from a natural-language description. Power-Pack-flavoured wrapper around the SDD `/speckit.specify` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-constitution` exists for the project.
- Before any plan, tasks, or implementation work.
- For any feature that touches >1 file or introduces new user-visible behavior.

NOT for: single-line fixes, doc-only changes (commit directly), or refactors that don't change behavior.

## What it produces

`./.specify/specs/<feature-id>/spec.md`, populated from `vault/templates/speckit/spec.md.template`. The `<feature-id>` is `[###]-[short-name]` (Spec Kit convention: 3-digit sequence + kebab-case slug).

## Process

1. **Branch.** Create `<feature-id>` branch off the project default. The branch IS the spec's identity.
2. **Generate.** Start from `vault/templates/speckit/spec.md.template`. The template encodes the SDD shape (P1/P2/P3 user stories, FR-### functional requirements, SC-### success criteria, Edge Cases, Assumptions, ambiguity markers via `[NEEDS CLARIFICATION: <question>]`).
3. **Fill from the user description.** For every part of the description the user did NOT explicitly specify, insert a `[NEEDS CLARIFICATION: <question>]` marker. DO NOT guess. The marker is structured ambiguity, not a defect.
4. **Prioritize user stories.** Each must be **independently testable** (an MVP slice that delivers value alone). Assign P1/P2/P3.
5. **Measurable success criteria.** Each `SC-###` is technology-agnostic and numerically verifiable (e.g. "<2s p95 latency", "1000 concurrent users", "90% task completion on first attempt").
6. **Commit.** `git commit -m "feat(spec): <feature-id> draft"`.
7. **Next.** If ambiguity markers exist → `/speckit-clarify`. If zero markers → `/speckit-plan`.

## Done-Gate

- `.specify/specs/<feature-id>/spec.md` exists.
- Every user story has P1/P2/P3 + an Independent Test sentence + Given/When/Then.
- Every `FR-###` is a single-capability MUST statement.
- Every `SC-###` is measurable + technology-agnostic.
- Edge Cases + Assumptions sections are NOT empty.
- Spec is on its `<feature-id>` branch.

## PP layering

- Reality Contract: the spec describes WHAT, never HOW. Stack choices belong in `plan.md`, not here.
- "Honest no-guess" is mandatory: if the user description omits a detail, mark it `[NEEDS CLARIFICATION]` rather than fabricate.
- Cross-link in commit message to the parent constitution if a principle is invoked.

## Chain

→ `/speckit-clarify` (if ambiguity markers exist)
→ `/speckit-plan` (when spec is clarification-free)
