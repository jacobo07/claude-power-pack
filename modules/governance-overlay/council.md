# The Council of 5 — TheWarRoom

> Native (inline) multi-perspective gate. NOT an external skill. Invoked by the main agent directly before emitting any STANDARD+ output. Part of the Global Baseline Flywheel (MC-U3).
> Loaded automatically by `pre-output.md` Section 13. ~400 tokens.

## Why inline (and not a sub-agent)

The Council is deterministic reasoning the main agent performs in one pass. No sub-model calls, no external process. Running 5 advisors as real sub-agents would cost 5× tokens and serialize the critical path — the value is the *perspective diversity*, which the main agent can generate natively if forced through the structured prompts below.

## Invocation

Before emitting final output at STANDARD+ tier, produce a `[COUNCIL BLOCK]` in the response that contains each advisor's verdict. Then stamp a final `[COUNCIL_VERDICT: A+|A|B|REJECT]` banner. B or REJECT blocks the output and triggers Rejection Recovery (see `post-output.md`).

## The 5 Advisors

Each advisor speaks in first-person, ≤2 sentences, on the specific question assigned. No hedging — a position, not an analysis.

### 1. Contrarian — "What breaks this?"
Adversarial. Assume the proposal is wrong. Find the one failure mode the author didn't consider (race, edge case, config that doesn't exist in prod, input that wasn't validated). If nothing found, say "no contrarian objection."

### 2. First Principles — "What is the minimum that must be true?"
Strip away the scaffolding. Reduce the change to its atomic operations. Identify which of those operations are NEW vs REUSED from the existing codebase. Flag any operation that's new-and-reinvented when a reusable form exists.

### 3. Expansionist — "What becomes possible next?"
Forward projection. If this ships as drafted, what unlocks? What becomes trivial in the next commit? What constraint is lifted ecosystem-wide? If the answer is "nothing — this is purely local", flag it: STANDARD+ work should lift a constraint.

### 4. Outsider — "Would a senior engineer unfamiliar with this codebase approve it?"
Fresh-eyes review. Is naming self-explanatory? Are invariants documented or enforceable? Would the change be reverted in review at FAANG / Stripe / Elixir-shop level? Flag any convention the change assumes the reader will recognize without declaration.

### 5. Executor — "Can I ship this now, or do I need to do more work?"
Operational honesty. Are all integration points wired? Does it pass the 5-gate cascade (static → build → scaffold → tests → E2E)? Is there a concrete verification command the reader can run in under 30 seconds? If "it compiles" is the strongest evidence, the answer is "more work."

## Howard's Loop (input to every advisor)

Each advisor reads TWO sources before rendering their verdict, so positive lessons from prior failures propagate across sessions:

1. **Visual antipatterns** — top-3 most recent entries from `~/.claude/knowledge_vault/governance/visual-antipatterns.md`.
2. **Recurring mistakes** — top-3 entries from `./modules/governance-overlay/mistake-frequency.json` where `count >= threshold` (default 3). Fetch via `python tools/mistake_frequency.py --top 3`. Each entry resolves to its registry section in `./modules/governance-overlay/mistakes-registry.md` (e.g. `M16` → `## Mistake #16:`).

Both injections happen textually: the advisor block in the response shows
`Prior antipatterns considered: [vis-1], [vis-2], [vis-3] | Recurring mistakes: [M<N>], [M<N>], [M<N>]`
before the verdict.

For KobiiCraft and KobiiSports (visual stacks), also load top entries from `~/.claude/knowledge_vault/gex44_antipatterns/`.

## Verdict Grading Rubric

| Grade | Criteria |
|-------|----------|
| **A+** | All 5 advisors unconditionally approve. Zero open objections. Ship. |
| **A**  | ≤1 advisor raises a minor caveat that's addressed in the response (not in follow-up). Ship. |
| **B**  | ≥2 advisors raise caveats, OR any advisor raises a major concern. **BLOCK.** Route to Rejection Recovery. |
| **REJECT** | Any advisor identifies a correctness bug, security hole, or scaffold illusion. **BLOCK.** Return to planning. |

The agent assigns the grade itself, honestly. Self-grading is the protocol — there is no external auditor in the critical path. Dishonest grading will surface in Mistake #17 (static verification ≠ runtime works) on the next session.

## Example block (template)

```
[COUNCIL BLOCK]
Prior antipatterns considered: scaffold-illusion, hook-boundary-contract, deploy-drift | Recurring mistakes: M16 (count=4), M39 (count=3)

• Contrarian: <verdict>
• First Principles: <verdict, with reuse-vs-reinvent call-out>
• Expansionist: <what this unlocks>
• Outsider: <conventions flagged>
• Executor: <ship-now-or-not + 30s verification command>

[COUNCIL_VERDICT: A+]
```

If the recurring-mistakes list is empty, render it as `Recurring mistakes: (none)`.

## Escalation

- **3 consecutive B verdicts on the same task** → HALT. Register error in GAL (`SYSTEM OVERRIDE: Register error in domain [X]: 3 consecutive Council B verdicts on [task]`).
- **1 REJECT** → HALT. Return to plan mode; do not retry the same implementation approach.
- **A+ with baseline elevation** → the delivering project's ledger entry bumps (handled by `baseline-translator.js` on the next UserPromptSubmit).

## Non-goals

- The Council does NOT check style/formatting — that's lint/prettier's job.
- The Council does NOT re-derive correctness from scratch — it reviews the *proposed output* the main agent is about to emit.
- The Council does NOT call external models. It is the main agent's structured self-review.
