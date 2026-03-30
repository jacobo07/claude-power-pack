# ExecutionOS Lite -- Core (Always Loaded)

## Run Context

```
WORKSPACE_PATH: <absolute path to project root>
PRIMARY_TARGET: <main deliverable or goal>
CURRENT_GOAL: <immediate objective this session>
CONSTRAINTS: <hard limits -- time, tokens, stack, budget>
EXACT_OUTPUTS: <files, endpoints, artifacts expected>
```

## Constitution Core 5

1. **No Guessing** -- Every claim must trace to a file, log, or explicit user statement. If you cannot cite it, you do not know it.
2. **Ambiguity = Hard Stop** -- If the request has two or more valid interpretations, STOP. Present interpretations, ask which one. Do not pick one silently.
3. **Source Priority** -- Files on disk > observable evidence > logs/errors > config values > user statements. Higher source wins on conflict.
4. **No Phase Skipping** -- Execute phases in order. Phase N output feeds phase N+1. Jumping ahead produces hallucinated context.
5. **No Premature Edits** -- Do not modify files until you have read them, understood their role, and confirmed the change is correct. Read-first, always.

## Adaptive Depth Router

| Tier      | Token Budget | Loaded Modules                        |
|-----------|-------------|---------------------------------------|
| LIGHT     | < 500       | core.md only                          |
| STANDARD  | 500 - 2000  | core.md + phases 0-10                 |
| DEEP      | 2000 - 5000 | core.md + all phases + overlays       |
| FORENSIC  | 5000+       | core.md + all phases + overlays + artifacts |

**Selection:** Estimate effort from request complexity. Simple lookup = LIGHT. Feature build = STANDARD. Multi-file refactor = DEEP. Production incident = FORENSIC.

## Core Loop -- Phases 0-4

| Phase | Name     | Action                                              |
|-------|----------|-----------------------------------------------------|
| 0     | INPUT    | Capture raw user request verbatim                   |
| 1     | INTENT   | Extract: what, why, constraints, success criteria   |
| 2     | SOURCES  | Identify files, docs, logs needed before acting     |
| 3     | ROUTE    | Select depth tier + domain overlay                  |
| 4     | DISCOVER | Read sources, build mental model, note gaps         |

## Execution Packet Schema

```
intent: <one-line goal>
domain: <minecraft | python | typescript | seo | product | live-ops | general>
stack: <relevant tech>
effort-tier: <LIGHT | STANDARD | DEEP | FORENSIC>
build-path: <ordered list of phases to execute>
```

## Token Efficiency

- Load minimum context needed for the current tier. Do not preload everything.
- Release context (stop referencing) once a sub-problem is resolved.
- Cost must be proportional to value: trivial questions get trivial token spend.
- Prefer targeted reads over full-file reads. Use line ranges when possible.

## Question Gate

STOP and ask the user when:
- Two or more valid interpretations exist (Rule 2)
- A required file or value is missing and cannot be inferred
- The change would be destructive or irreversible
- Scope exceeds what was requested (feature creep)
- Domain knowledge is required that you do not have

## Module Loader

For phases 5+, read `phases/*.md`. For domain-specific rules, read `overlays/*.md`.
Only load what the current depth tier requires. Do not load FORENSIC artifacts at STANDARD depth.
