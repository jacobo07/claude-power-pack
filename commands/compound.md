---
name: cpp-compound
description: "Power-Pack-scoped driver for the Compound Learnings 8-step pipeline. Reads new learning files (.claude/cache/learnings/*.md primary, memory/sessions/session_*.md header-filtered fallback), extracts patterns, applies 1/2/3+/4+ signal thresholds, categorizes into Rule/Skill/Hook/Agent-update via decision tree, proposes artifacts with per-artifact Scope:global|project toggle (default global), creates approved artifacts, advances per-project cursor in ~/.claude/state/compound-learnings.json under mkdir-mutex, then deletes LEARNINGS_PENDING.md marker. Sleepy: only the user invokes this; the sentinel hook only signals."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# /cpp-compound — Compound Learnings driver

Sibling of `/cpp-distill` and `/cpp-customclaw`. Drives the 8-step pipeline defined in the global skill at `~/.claude/skills/compound-learnings/SKILL.md`. The sentinel hook (`~/.claude/hooks/learning-sentinel.js`) is the producer of the `LEARNINGS_PENDING.md` signal; this command is the consumer that consolidates and clears it.

---

## Invocation

```
/cpp-compound                    # default — process current project
/cpp-compound --dry-run          # propose without writing artifacts (no cursor advance, no marker delete)
/cpp-compound --since=YYYY-MM-DD # override cursor with explicit date
/cpp-compound --threshold=N      # one-shot threshold override (does not persist)
```

If the running session has no `LEARNINGS_PENDING.md` and the user did not pass an override, AskUserQuestion: **"No pending-marker found. Run anyway against current corpus?"** with options "Yes, force-run", "No, abort".

---

## Identifiers (must match the sentinel — single source of truth)

```javascript
const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const pid = cwd.replace(/[^a-zA-Z0-9-]/g, '-');
```

State file: `~/.claude/state/compound-learnings.json`
Lock file: `~/.claude/state/compound-learnings.json.lock` (mkdir-mutex)
Marker file: `<cwd>/LEARNINGS_PENDING.md`

---

## Step 1 — Gather

Use Glob:

- Primary: `<cwd>/.claude/cache/learnings/*.md`
- Fallback (only if primary glob is empty): `<cwd>/memory/sessions/session_*.md` filtered by header probe — file MUST contain at least one of: `## Patterns`, `**Takeaway:**`, `**Actionable takeaway:**`, `## What Worked`, `## What Failed`. Files without any of those are session logs, not learnings.

Determine cursor: read state file, get `state.projects[pid]?.last_run_iso`. If `--since` flag passed, use that ISO date. Filter files: keep only those with `mtime > cursor`. Sort newest-first. Read 5-10 most-recent (or all if total ≤ 10).

Surface: `Gathered N learning files from <source>; cursor was <iso or 'none'>`.

## Step 2 — Extract (Structured)

For each gathered file, extract entries matching these section headers:

| Section Header                    | Captures                          |
|-----------------------------------|-----------------------------------|
| `## Patterns` / `Reusable techniques` | Direct rule candidates        |
| `**Takeaway:**` / `**Actionable takeaway:**` | Decision heuristics    |
| `## What Worked`                  | Success patterns                  |
| `## What Failed`                  | Anti-patterns (invert to rules)   |
| `## Key Decisions`                | Design principles                 |

Build the in-session frequency table:

```markdown
| Pattern (verbatim)                | Sessions     | Category   |
|-----------------------------------|--------------|------------|
| "Check artifacts before editing"  | abc, def     | debugging  |
```

## Step 2b — Consolidate

Merge patterns expressing the same principle. Use the most general formulation. Update the table.

Example:
- "Artifact-first debugging" + "Verify hook output by inspecting files" + "Filesystem-first debugging" → **"Observe outputs before editing code"**.

## Step 3 — Detect Meta-Patterns

If more than 50% of patterns cluster around one topic (e.g., hooks, tracing, async), recommend a **dedicated skill** instead of N rules. One skill compounds better than five rules.

Self-question: *"Is there a skill that would make all these rules unnecessary?"*

## Step 4 — Categorize (Decision Tree)

```
Is it a sequence of commands/steps?
  YES → SKILL
  NO ↓
Should it run automatically on an event?
  YES → HOOK
  NO ↓
Is it "when X, do Y" or "never do X"?
  YES → RULE
  NO ↓
Does it enhance an existing agent workflow?
  YES → AGENT UPDATE
  NO  → Skip
```

## Step 5 — Apply Signal Thresholds

| Occurrences | Action |
|-------------|--------|
| 1 | Note but skip (unless critical failure) |
| 2 | Consider — present to user |
| 3+ | Strong signal — recommend creation |
| 4+ | Definitely create |

## Step 6 — Propose (with per-artifact Scope toggle)

For each candidate above the threshold, emit a proposal block:

```markdown
---

## Pattern: [Generalized Name]

**Signal:** [N] sessions ([list session IDs])
**Category:** [debugging / reliability / workflow / etc.]
**Artifact Type:** Rule / Skill / Hook / Agent Update
**Scope:** global    ← default; user toggles via AskUserQuestion
**Rationale:** [Why this artifact type, why worth creating]

**Draft Content:**
\`\`\`markdown
[Actual content that would be written to file]
\`\`\`

**File (if global):** `~/.claude/rules/[name].md` or `~/.claude/skills/[name]/SKILL.md`
**File (if project):** `<cwd>/.claude/rules/[name].md` or `<cwd>/.claude/skills/[name]/SKILL.md`

---
```

Then invoke AskUserQuestion **per artifact** (or batched for ≥4 artifacts):

- Question: `"Approve [name] as [type] at [scope] scope?"`
- Options: `"Approve global"`, `"Approve project"`, `"Skip"`, `"Edit draft"`

Track each accepted artifact's chosen scope. Default-global means `Approve global` is option 1.

## Step 7 — Create Approved Artifacts (Transactional Order)

**MANDATORY ORDER — do not reorder:**

1. **Acquire mkdir-mutex** on `~/.claude/state/compound-learnings.json.lock`. Stale-lock recovery: if EEXIST and dir mtime > 30 s old, `rmdir` + retry. Bail if not acquired in 5 s (do not write any artifact, surface error).
2. **Write each approved artifact sequentially** via the Write tool (no parallel writes — Windows harness drops parallel payloads, see `feedback_sequential_writes_per_turn` in MEMORY).
   - Rule: write the rule body (see shape below).
   - Skill: write `SKILL.md` (frontmatter + body).
   - Hook: write the single `.js` file using the Windows-native pattern (mirror `~/.claude/hooks/session-summary.js`); register in `~/.claude/settings.json` as a separate Edit (atomic backup-and-rename).
   - Agent update: Edit the existing agent file at `~/.claude/agents/<name>.md`.
3. **Advance cursor (MERGE, never replace)**: read state file, then `state.projects[pid] = { ...state.projects[pid], last_run_iso: nowIso(), directive_count: 0 }`. The spread is mandatory — a bare `= { last_run_iso }` would WIPE the sentinel's `auto_prompt` opt-out flag and the GAP-7 `directive_count` runaway guard. Resetting `directive_count` to 0 is the canonical signal that consolidation succeeded (the sentinel's L1 auto-prompt re-arms; the STUCK-degrade clears). Write atomically via `atomicWriteJson` from `~/.claude/skills/claude-power-pack/lib/atomic_write.js` (fsync + EBUSY retry; falls back to `<state>.tmp`+`fs.renameSync` if the lib is unresolvable).
4. **Release lock** (`rmdir` lockdir).
5. **Delete marker** `<cwd>/LEARNINGS_PENDING.md` if present (use `fs.unlinkSync`, ignore ENOENT).

**On any step-2 failure: STOP.** Do NOT advance the cursor. Do NOT delete the marker. The next session's sentinel keeps surfacing the marker, and the operator can re-run `/cpp-compound`.

### Rule shape

```markdown
# [Rule Name]

[Context: why this rule exists, based on N sessions]

## Pattern
[The reusable principle in one sentence.]

## DO
- [Concrete action 1]
- [Concrete action 2]

## DON'T
- [Anti-pattern 1]

## Source Sessions
- [session-id-1]: [what happened]
- [session-id-2]: [what happened]
```

### Skill shape

```markdown
---
name: [skill-name]
description: "[when to invoke; what it produces]"
allowed-tools:
  - [list]
---

# [Skill Title]

## When to Use
[Trigger phrases]

## Process
[Numbered, executable steps]

## Examples
[From the source learnings]
```

### Hook shape (Windows-native, single .js file)

Write the hook to `~/.claude/hooks/<name>.js` mirroring `~/.claude/hooks/session-summary.js`:

```javascript
const fs = require('fs'), path = require('path');
function run(data) {
  try {
    const cwd = data.cwd || process.cwd();
    const logPath = path.join(cwd, '.claude', 'cache', 'last-event.json');
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.writeFileSync(logPath, JSON.stringify({ ts: new Date().toISOString(), event: data.hook_event_name || 'unknown' }));
  } catch (_) { /* silent */ }
  return { continue: true };
}
if (require.main === module) {
  let input = '';
  const t = setTimeout(() => { try { process.stdout.write(JSON.stringify({continue:true})); } catch {} process.exit(0); }, 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => input += c);
  process.stdin.on('end', () => {
    clearTimeout(t);
    let data = {}; try { data = JSON.parse(input); } catch {}
    console.log(JSON.stringify(run(data)));
    process.exit(0);
  });
} else { module.exports = { run }; }
```

Then Edit `~/.claude/settings.json` to add the registration (always backup first):

```json
{
  "hooks": {
    "<EventName>": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/<name>.js\"",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

### Agent update

Edit existing agent file at `~/.claude/agents/<name>.md`. Add the learned capability under a new `## History` or `## Learned Capabilities` heading. Preserve existing frontmatter and body.

## Step 8 — Summary Report

Emit a final summary block:

```markdown
## Compounding Complete

**Learnings Analyzed:** [N] files
**Patterns Found:** [M]
**Artifacts Created:** [K]
**Cursor advanced to:** [ISO timestamp]

### Created (global):
- Rule: `~/.claude/rules/[name].md` — [one-line purpose]
- Skill: `~/.claude/skills/[name]/SKILL.md` — [one-line purpose]

### Created (project):
- Rule: `<cwd>/.claude/rules/[name].md` — [one-line purpose]

### Skipped (insufficient signal):
- [Pattern X] (1 occurrence)

**Marker cleared.** Setup permanently improved.
```

If `--dry-run` was passed, emit the proposals without performing Step 7. Make the dry-run state explicit in the summary.

---

## Reality Contract (vMAX-NULL-ERROR)

- Zero stub-language tokens in artifact bodies — validator can reject any forbidden-token hit outside code fences. Forbidden-token enumeration is the same as `/cpp-distill` Reality Contract; see `~/.claude/skills/claude-power-pack/commands/distill.md` Reality Contract section for the canonical list.
- Per-artifact scope toggle is mandatory — never silently default to project when the user expects global, or vice versa.
- Cursor advance is transactional with artifact write. Partial writes leave both unchanged.
- Marker deletion is the LAST step and only happens on full success — partial failure leaves marker intact for retry.
- Sentinel never advances cursor; only this command does.

## Reference

- Source spec: `~/.claude/skills/compound-learnings/SKILL.md`
- Sentinel hook: `~/.claude/hooks/learning-sentinel.js`
- State file schema: `{ schema_version: 1, threshold: 5, last_run_global: null, projects: { [pid]: { last_run_iso } } }`
- Sealed by `/ultra plan Build [GLOBAL COMPOUND LEARNINGS INFRASTRUCTURE]` (2026-05-15).
