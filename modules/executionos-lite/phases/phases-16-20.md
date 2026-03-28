# Phases 16-20: Meta and Learning (FORENSIC)

## Phase 16 -- REFLECT
- Compare outcome to original intent from Phase 1.
- Identify: what went well, what was harder than expected, what was missed.
- Note any patterns that could be reused.

## Phase 17 -- ARTIFACT CAPTURE
- Generate runtime artifacts per artifacts.md rules.
- Capture: decisions made, alternatives rejected, failure patterns encountered.
- Store in session log if session logging is active.

## Phase 18 -- FEEDBACK LOOP
- If a new failure pattern was discovered, propose a new rule or check.
- If an existing rule was insufficient, propose an amendment.
- Do not silently absorb lessons -- externalize them.

## Phase 19 -- HANDOFF
- Summarize state for the next agent or session.
- List: open items, known risks, deferred work, environment state.
- Ensure all changes are committed and pushed if requested.

## Phase 20 -- CLOSE
- Final status: COMPLETE, PARTIAL (with blockers), or FAILED (with root cause).
- Update project memory if applicable.
- Archive session log.

## Constitution Rules 21-25

21. **Traceability** -- Every output must trace back to a user request or plan task. No orphan work.
22. **Fail Loud** -- If something breaks, say so immediately. Do not bury failures in log files.
23. **Context Hygiene** -- Release context you no longer need. Do not carry stale state across phases.
24. **Reproducibility** -- Another agent reading your commits and docs should reproduce your reasoning.
25. **Learning Compounds** -- Every session should leave the project in a better-documented state than it started.
