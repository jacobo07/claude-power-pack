<audit_checklist>

## Per category, the questions to answer

### AUTH
- Does the plan reference any external service (DB, API, SSH, OAuth)?
- Is the credential source explicitly stated (env var, vault, ~/.ssh/<key>, secret manager)?
- Are auth failures handled (timeout, 401, expired token)?

### ENV
- Are env vars enumerated by name?
- Is there a fallback or validation if an env var is missing?
- Is `.env.example` updated when `.env` keys change?

### PATH
- Are file paths absolute or `~/`-rooted (correct), not bare relative (often wrong)?
- Do paths resolve on Windows AND POSIX? (`os.path.join` / `path.join`, not raw `\\`/`/`)
- Are new files placed in conventional locations (e.g., hooks → `~/.claude/hooks/`, tools → `<repo>/tools/`)?

### EDGE
- What happens on empty input?
- What happens on input >10x typical size?
- What happens on concurrent invocation (race condition)?
- What happens if a dependency file is missing?
- What happens on permission denied / read-only fs?

### INTEGRATION
- Is each new file actually consumed by something? (Mistake #16: Scaffold Illusion; §20 Zero Vapor)
- Is the call chain traced from caller → callee?
- Does the plan name the verification step that proves wiring?

### REALITY-CONTRACT
- Does the plan leave any unfinished-work marker in shipped code — one of the three canonical comment markers (todo / fix-me / stand-in), a bare no-op statement as a function body, or a not-implemented raise? → BLOCK. The exhaustive banned-token list and its analytical-log exemption are owned by `~/.claude/knowledge_vault/claude-doctrine/reality-contract-detail.md`; do not re-derive it here.
- Any "we'll handle X later" → BLOCK.
- Empty catch blocks → BLOCK.

### COMPLETION-GATE
- Does phase 7 verification use REAL input?
- Is the success criterion observable (output line, file existence, log entry, screenshot)?
- Is the gate measurable, not "should work"?
- Which real boundary does it cross (§18)? Name it.

### ANTI-CRASH
- File count >5 in a single execution batch? → flag for micro-batching.
- Cross-cutting refactor without checkpoint? → flag.
- Any harness file (settings.json, hooks/*, ~/.claude/CLAUDE.md) edited? → confirm permission rule exists or auth flow is clear.

### APOLLO-GRAPHQL — GraphQL operation ground rules (tiered severity)
Applies when the plan's scope touches any `.graphql`/`.gql` file or a
`gql`/`graphql` tagged template literal. Source of truth:
`vendor/apollo/upstream/graphql-operations/SKILL.md` (vendored).

HARD VETO — counts toward **Gaps found**; Phase 5 MUST fix before Phase 6:
- **Unnamed operation.** `query`/`mutation`/`subscription` with no identifier
  before the `{`/`(`. Regex: `/(^|\n)\s*(query|mutation|subscription)\s*[({]/`.
  Anonymous ops break cache normalization, telemetry, persisted queries.
- **Inline literal instead of `$variable`.** A request-specific scalar literal
  passed to a field argument inside an operation (e.g. `user(id: "abc")`,
  `first: 10`) that is not declared as a `$var` in the operation signature.
  Heuristic: arg value matches
  `/:\s*("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|true|false)\b/` and no matching
  `$name` appears in the operation's variable definitions.

SOFT WARNING — emit under a trailing `### Apollo advisories (non-blocking)`
subsection; do NOT count in **Gaps found** (Q&A 4c):
- **Duplicate field selection.** Same field name >1× in one selection set
  (distinct aliases/arguments excepted).
- **Over-fetch.** A selection set with ≥8 scalar leaf fields and no fragment
  spread — likely fetching more than the caller renders.

</audit_checklist>

