# /speckit-clarify

Resolve every **structured ambiguity marker** in the current feature spec. Power-Pack-flavoured wrapper around the SDD `/speckit.clarify` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-spec` if any `[NEEDS CLARIFICATION: ...]` markers remain.
- Before `/speckit-plan` — planning against an ambiguous spec produces drift later.
- When `/speckit-analyze` flags spec-vs-plan inconsistencies traceable to missing clarification.

NOT for: ad-hoc Q&A about implementation (that goes in chat, not in the spec).

## What it produces

The same `./.specify/specs/<feature-id>/spec.md` updated in place: every `[NEEDS CLARIFICATION: <question>]` replaced by a definitive answer, plus an audit trail at the bottom of the spec (`## Clarifications`) recording the resolved questions.

## Process

1. **Scan.** Grep the active spec for the literal pattern `NEEDS CLARIFICATION`. List every match by location (user story, FR, SC, edge case).
2. **Cluster.** Group questions by domain (auth, data, performance, UX) so the Owner can answer them in batches.
3. **Ask one batch at a time.** For each cluster, present the questions verbatim and request answers. Use `AskUserQuestion` with multi-select where applicable.
4. **Apply.** Replace each marker with the answer inline. The answer becomes the requirement.
5. **Audit-trail.** Append a `## Clarifications` section to the spec containing: question, answer, date, who-answered. This is what `/speckit-analyze` reads later for drift detection.
6. **Validate.** Grep again — zero `NEEDS CLARIFICATION` remaining.
7. **Commit.** `git commit -m "spec(clarify): <feature-id> ambiguities resolved (N answers)"`.
8. **Next.** `/speckit-plan`.

## Done-Gate

- Zero `[NEEDS CLARIFICATION` markers in the spec.
- `## Clarifications` section contains every Q/A pair.
- Spec passes a `/speckit-analyze` consistency check on first try.

## PP layering

- Surface ambiguity to the Owner ONCE per cluster, not per question — saves a turn per topic.
- Never silently invent an answer. If the Owner declines to clarify, mark the spec `Status: blocked-on-clarification` and stop.
- Honest no-guess: if you would have answered yourself, the marker SHOULD HAVE BEEN in the original spec instead of being preempted.

## Chain

→ `/speckit-plan`
