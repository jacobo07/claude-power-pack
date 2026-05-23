---
description: ONESHOT 7-phase ULTRA-PLAN protocol. /ultra plan <target> forces Q&A → Plan → Audit → Fix → Execute → Verify. Discovery Mode is mandatory. (BL-0063)
---

# /ultra — ONESHOT Workflow Protocol

Arguments: $ARGUMENTS

## Activation Rule

If the first argument is `plan`, the rest is the build target. Treat the entire remainder as the TARGET SPEC. If no target follows `plan`, ask the Owner for a 1-3 line target description and STOP — do NOT generate the 6 questions yet.

If $ARGUMENTS is empty, print this protocol's summary (the 7 phases) and exit.

## The 7 Phases (mandatory order, no skipping)

1. **Ultra Plan** — restate the target in your own words. Identify scope, surface area, files involved, env/config dependencies. Estimate file count. **KARIMO pre-pass (BL-0068, advisory):** if the TARGET SPEC contains a raw PRD (a `PRD:` header or a `<prd>…</prd>` block), first run `python ~/.claude/skills/claude-power-pack/modules/karimo-harness/prd_parser.py --in <prd|->` to emit `PRD_BASELINE.json` + `BLUEPRINT.md`, then treat the blueprint seed tasks + the `<prd-constraints>` block as pre-extracted hard scope (do NOT re-derive). This step is purely additive and does NOT alter the Phase 2 mandatory stop.
2. **Q&A Pass** — emit EXACTLY 6 critical clarifying questions. Number them. Cover: auth/credentials, env vars, file paths, edge cases, success criteria, scope boundaries. STOP and wait for Owner's answers. Do NOT proceed without them.
3. **Revised Plan** — fold answers into a numbered task list. Each task has: file path, action (create/edit/delete), 1-line purpose, verification step.
4. **Audit Pass** — invoke the `oneshot-architect-auditor` sub-agent (via Agent tool, `subagent_type: oneshot-architect-auditor`). Pass the revised plan. The sub-agent returns a numbered list of GAPS (auth, env vars, file paths, edge cases). Do NOT rewrite the plan from sub-agent output — the sub-agent reports gaps, you fix them.
5. **Fix Injection** — for each gap, amend the plan with a concrete fix line. Re-emit the corrected plan. If no gaps, state "Audit clean" and proceed.
6. **Execution** — Auto Mode. Execute every task. No partial commits. No scaffold-illusion. Reality Contract applies (zero TODO/FIXME/PLACEHOLDER).
7. **Verification** — run with REAL input. Show actual output. If frontend/UI, screenshot or describe observed state. If hook/daemon, show log line proving it fired. No vapor.

## Anti-Failure Modes (block-list)

- **>5 files in one phase 6 batch** → split into N micro-batches before exec (Ley 24, PART U Anti-Crash).
- **Skipping Q&A** → REJECT. Six honest answers > one vague paragraph. Even if Owner says "just do it", emit the questions and accept terse answers.
- **No preflight credentials/env-var check** → plan is incomplete, return to phase 3.
- **No real-input verification** → not Done. Ley 25 + Gate 7.

## Honest Limits

- This command runs INSIDE my turn. Auto Mode means I don't stop between phases for confirmation, but I DO stop at phase 2 to wait for the Owner's 6 answers — that's the protocol's value, not a defect.
- The Q&A pause is the ONLY mandatory Owner-gate. Everything else is autonomous.
- Failure to emit phase markers (`## Phase 1`, `## Phase 2`, etc.) is a protocol violation. Always label.

## Reference

Sealed by **BL-0063** (CLI capacitation, 2026-05-04). Documented in `vault/knowledge_base/session_lessons.md`.
