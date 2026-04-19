# Governance Overlay — Post-Output Learning

> Loaded for DEEP and FORENSIC tiers. ~100 tokens. Runs after task completion.
> Inherits workspace context from PART A0 Assimilation Scan. All paths in logs use `./` relative format.

## Failure Capture

If any mistake from the full registry (51 mistakes + agent governance) was caught during this task:

1. **Log to failure patterns** — if `/governance/12_FAILURE_PATTERNS.md` exists in the project:
   ```
   ### [DATE] Mistake #N: [Short description]
   - **What happened:** [Brief description]
   - **How caught:** [Which check caught it — during-task, pre-output, quality gate]
   - **Prevention rule:** "Before [action], always [check]"
   ```

2. **Extract prevention rule** — distill into a one-line rule that prevents recurrence

3. **Project-specific mistakes** — if the mistake is NOT in the full registry (it's unique to this project):
   - Add to `governance/domain/PROJECT_DOMAIN_RULES.md` as a new DR-NNN rule
   - Format: Rule, Rationale, Detection, Status: ACTIVE

4. **Increment frequency counter (Mistakes→Curriculum loop)** — for registered Mistake-IDs, run:
   ```bash
   python tools/mistake_frequency.py --increment M<N> --project <current-project-name>
   ```
   This updates `./modules/governance-overlay/mistake-frequency.json`. When any entry crosses the threshold (default 3), `pre-task.md` Section 9 will surface it as a WATCH banner on the next STANDARD+ task in any project. Closes the post-output → pre-task feedback loop.

## Rejection Recovery (when Council returns B or REJECT)

When `pre-output.md` Section 13 Council returns a `[COUNCIL_VERDICT: B]` or `[COUNCIL_VERDICT: REJECT]`, the output is BLOCKED. Execute this recovery loop (max 3 iterations, then HALT):

1. **Read the iteration prompt** — in-repo path: `./knowledge/iteration-prompts/visual-v1.md` (ported from the Downloads source on 2026-04-19 to fix E11 / PART Q). It defines an Intent Compiler + Baseline Elevation framework (forensic visual/logic root-cause + DNA propagation).

2. **Apply the Intent Compiler** from the iteration prompt to the rejected output:
   - Identify the Intent Gap: what the original prompt asked vs what the output delivers.
   - Classify the gap: hallucination, language-specific bug, logic error, or "feel" failure.
   - Cross-language mapping: if the gap is language-general, register the lesson in GAL (`SYSTEM OVERRIDE: Register error in domain [X]: [gap]`).

3. **Re-render the output** at baseline `current + 1` (e.g. if current baseline is v600, target v601), addressing each advisor's caveat explicitly. Run Council again.

4. **Iteration cap:**
   - **Pass on iter 1 or 2:** ship. Log success to MEMORY.md (brief 1-line note).
   - **Pass on iter 3:** ship, but treat as "barely passing" — flag for manual review by the Owner.
   - **Still B/REJECT after iter 3:** HALT. Do NOT ship. Return to plan mode. Register the failure in GAL (Mistake #16 "compiles != works" if relevant). The implementation approach itself is wrong — no amount of iteration will fix it.

5. **Baseline promotion:** if iteration 1 produced an A+ output by introducing new engineering rigor (e.g. stricter Never-Do Matrix, new invariant), the Translator Hook (`baseline-translator.js`) will detect it on the next UserPromptSubmit and bump the ledger. No manual action needed — the Flywheel closes itself.

## FORENSIC Tier Additional Logging

If task was classified as FORENSIC:
- Create incident trace in `/governance/17_CAUSAL_TRACE.md`
- Record the full causal chain: symptom → investigation → root cause → fix → verification
- Update `/governance/18_CONFIDENCE_LOG.md` with certainty level of the fix
- Flag if the fix is a workaround vs a root-cause resolution
