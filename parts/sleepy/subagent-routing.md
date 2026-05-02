# PART SR — SUBAGENT ROUTING (BL-0034)

When to delegate to a subagent vs do work inline. Loaded on demand when the main flow has > 3 candidate files to inspect, > 200 lines of expected raw read, or open-ended exploratory questions.

**Trigger:** "search across the codebase", "where is X defined", "review all uses of Y", "audit", "find every", multi-file refactor, > 50 KB raw-read budget exceeded.

---

## The Rule

The main context window is the **scarce resource**. Subagents are the **token reservoir**. Use the reservoir for grunt work; keep the main window for synthesis and decision.

**Delegate when ANY of the following is true:**

- The query touches > 3 unrelated files.
- Expected raw bytes read > 40 KB (per CLAUDE.md Token Austerity Protocol Circuit Breaker).
- Question is open-ended ("how does X work across the system", "why might Y be slow", "is this safe to remove").
- Result fits in a < 500-token summary (not a code edit).

**Do inline when ALL of the following are true:**

- Target file path is already known.
- Question is closed ("does function Z return X?", "is line N correct?").
- Inline read budget is < 5 KB.
- Decision must be made in the same turn.

---

## Routing Matrix — Which Subagent For Which Job

| Query archetype | `subagent_type` | Why this one |
|---|---|---|
| "Find/locate X across codebase" | `Explore` | Read-only, fast. Returns file paths + excerpts. |
| "How would I implement X" | `Plan` | Returns step-by-step plan, no edits. |
| "Code review of branch" | `superpowers:code-reviewer` | Independent perspective, won't echo your reasoning. |
| "Map out architecture of repo" | `gsd-codebase-mapper` | Writes structured docs to `.planning/codebase/`. |
| "Debug X bug" | `gsd-debugger` | Persistent session state, hypothesis-driven. |
| "Open-ended research, multi-step" | `general-purpose` | Default. Has all tools. |

---

## Anti-Patterns (don't do these)

1. **Don't delegate single-file grep.** "Omitted long matching line" → narrow the pattern + use Grep directly. Memory: `feedback_no_subagent_for_single_file_grep.md` (BL-0011 era).
2. **Don't delegate hot-path implementation.** Subagents return reports; if you need code edited, write it yourself in the main flow.
3. **Don't trust subagent claims of work done.** Per the Agent tool docs: "Trust but verify: an agent's summary describes what it intended to do, not necessarily what it did. When an agent writes or edits code, check the actual changes before reporting the work as done."
4. **Don't dispatch if the user said "just do X".** Single-shot user requests don't need planning agents.

---

## Briefing Template (when you DO delegate)

A bad prompt produces a shallow report. Use this structure:

```
GOAL: <one sentence — what we want>
CONTEXT: <what we already know, what we ruled out>
DELIVERABLE: <"a list of file paths", "a markdown report", "a 200-word summary">
NON-GOALS: <what NOT to investigate>
LENGTH: <"under 200 words" or specific section count>
```

Without all 5, the agent fills in defaults that may not match intent.

---

## Token Discipline (cite OmniRAM-Sentinel BL-0021)

Subagents help you stay under the 60% snapshot threshold (BL-0033). Each delegation:
- Frees the main window from raw search noise
- Returns a digested summary that fits in < 500 tokens
- Survives `/compact` because the SUMMARY is in the chat history, while the noise is gone

If the main window is at 50% used and you're about to do a big read: **delegate first**. The subagent eats the noise; you eat only the conclusion.

---

## Return to Dormant

After the routing decision is made and dispatch happens (or doesn't), this part returns to sleep. Do NOT keep loaded across unrelated tasks.
