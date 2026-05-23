---
name: arch-decision
description: Architecture Decision Record (ADR) generator backed by the Claude Power Pack vault. Before committing to a non-trivial architectural choice, the agent consults the local knowledge_vault, surfaces vetoes/lessons/sealed Standards that bear on the decision, and writes a 6-section ADR (Context / Decision / Consequences / Alternatives / Vault-conflicts / Lessons-cited) to vault/decisions/&lt;ts&gt;_&lt;slug&gt;.md. Use for decisions like "should I store sessions in Redis or Postgres?", "which framework for the new dashboard?", or any cross-cutting choice the Owner wants reviewed against prior decisions. Fast-mode advisory (no ADR) is auto-injected by the JIT loader on any prompt with two or more design verbs.
---

# /arch-decision — Architecture Decision Record

## What it does

`/arch-decision "DESCRIPTION"` consults the pre-built vault index
(8 source classes, weighted) and generates an ADR that explicitly
cites every relevant prior veto, lesson, or sealed Standard. The ADR
is durable on disk and becomes a future scan target via the
closed-loop UKDL row.

The fast-path `arch_check.py` engine that drives this skill is also
the same engine the JIT loader auto-fires on every UserPromptSubmit
that contains two or more design verbs — so even without the slash
command, COLLISION-level matches surface in the agent's context. The
`/arch-decision` slash command exists for the cases where the Owner
wants the durable ADR artifact and a deeper review.

## Usage

```
/arch-decision "short description of the architectural choice"
```

Examples:

- `/arch-decision "store TUA-X user sessions in Redis vs Postgres"`
- `/arch-decision "use FastAPI or Phoenix for the metrics service"`
- `/arch-decision "add a new PreToolUse hook vs extend hook-dispatcher.js"`

## Execution protocol (the agent's responsibilities)

When this command is invoked, the agent MUST execute the following
seven steps in order. None of these may be skipped; the ADR is not
DONE until step 7 produces a real file on disk.

### Step 1 — Confirm the index is fresh

Run:

```
python modules/arch-decision/build_index.py
```

Empirical: stdout must show `TOTAL` >= 50 sources and the eight
source classes (apex / feedback_memory / gex44_antipatterns /
antipatterns / session_lessons / governance / errors / ukdl).

### Step 2 — Run the deep-mode verdict engine

Pipe the description into:

```
python modules/arch-decision/arch_check.py --deep
```

Parse the JSON output. Capture:

- `verdict` (COLLISION / WARNING / CLEAR)
- `sources[]` (top 3 cited sources with `path`, `section`, `is_veto`,
  `score`, `class`)
- `signals_summary.entities_hit` and `concepts_hit`

### Step 3 — Read the cited source files

For each source in `sources[]`, read the full file (or the cited
section). Do NOT paraphrase what you have not read. Every claim in
the ADR's Vault-conflicts or Lessons cited sections MUST trace to
text that was actually read at this step.

### Step 4 — Compose the ADR

The ADR is a single markdown file with exactly these six sections in
this order, with real values substituted for the bracketed labels:

```
# ADR-[YYYYMMDD-HHMMSS]: [short title slug]

Date: [ISO date]
Status: Proposed | Accepted | Rejected
Verdict from arch_check: [COLLISION | WARNING | CLEAR]

## Context

[2-4 paragraphs explaining the problem and the constraints]

## Decision

[the chosen direction, 1-3 paragraphs]

## Consequences

### Positive
- ...

### Negative
- ...

### Neutral
- ...

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| ... | ... |
| ... | ... |

## Vault-conflicts

[one row per source from arch_check that is verdict COLLISION or
WARNING. If no conflicts, write exactly: "None surfaced by
arch_check."]

| Source | Class | is_veto | Why it bears |
|---|---|---|---|
| `path` | class | true/false | one-line summary read from the source |

## Lessons cited

[bulleted list of session_lessons or sealed-standard sections that
informed the Decision. Each cited file path must have been READ in
step 3. If no lessons cited, write exactly: "None cited."]

- `path:section` — one-line takeaway
```

### Step 5 — Slug + path

`slug` = `arch_check_signals_summary.entities_hit[0]` if present,
else first 5 words of description, kebab-cased, max 60 chars.

Filename: `vault/decisions/[YYYY-MM-DD-HHMMSS]_[slug].md`.

Create the `vault/decisions/` directory if missing.

### Step 6 — Write the ADR

Write the file. Every section must have real content; if a section
has no content, write the explicit "None X." sentinel for that
section.

### Step 7 — Report

Print the absolute path of the new ADR plus the verdict from step 2.
If verdict was COLLISION, also remind the Owner: "Verdict was
COLLISION. Re-confirm the Decision section before treating this ADR
as Accepted."

## Reality Contract (binary)

- No source citation in the ADR may name a path that does not exist.
- No Vault-conflicts row may reference a file that was not read in
  step 3.
- If the verdict is COLLISION and the Decision proceeds anyway, the
  Status MUST be "Proposed" — never "Accepted" without Owner
  confirmation.

## Closed-loop via UKDL

When the ADR is written, append a new row to
`vault/knowledge_base/ukdl-universal.md` under a "Decisions"
section, of the shape:

```
| UKDL-AC-NN | vault/decisions/filename | one-line summary |
```

Owner can accept or revert the row. UKDL is the explicit hub for
cross-references.

## Cross-references

- `vault/specs/arch-decision-skill.md` — full spec.
- `vault/plans/arch-decision-skill-2026-05-23.md` — implementation plan.
- `modules/arch-decision/arch_check.py` — verdict engine.
- `modules/arch-decision/build_index.py` — index builder.
- `knowledge_vault/core/apex-completion-standard.md` — "Architecture
  Decision Axis" section (sealed 2026-05-23).
