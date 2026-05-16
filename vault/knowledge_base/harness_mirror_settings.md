# Harness Mirror — settings.json UserPromptSubmit

**Live file (non-git):** `~/.claude/settings.json` → `hooks.UserPromptSubmit`
**Mirror purpose:** version-controlled record of the KARIMO sentinel
registration (the live file cannot be git-tracked; this doc is the
canonical reference per the flat-file PP mirror convention).

**Applied:** 2026-05-16 · BL-0068 residue closure · explicit Owner
authorization (per-action, by name).

## Registered entry (3rd in the array)

The `UserPromptSubmit` array now holds 3 entries — `hook-dispatcher.js`,
`correction-guard.js`, and this appended sentinel:

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/prd-keyword-sentinel.js\"",
      "timeout": 10,
      "statusMessage": "KARIMO PRD sentinel"
    }
  ]
}
```

## Safety contract honoured (Q3a)

1. Pre-write timestamped backup `settings.json.bak-<epoch>` (byte-equal,
   valid JSON verified).
2. Post-write structural assertion (not bare parse): array length is
   exactly 3, exactly one entry references `prd-keyword-sentinel.js`,
   the entry schema is `{type:"command", timeout:10}`.
3. Auto-rollback wired: `node JSON.parse || cp .bak settings.json` — a
   discrete gated step, not implicit.

## Activation honesty

The sentinel is **standalone-verified** (exit 0, emits a correct
`hookSpecificOutput.additionalContext` with a `<prd-constraints>`
block by really spawning `prd_parser.py`). Live in-pipeline firing is
**cold-load-bound**: hooks load once at session start, so this entry
does not fire until the next `/restart`. That is an honest limit, not
a defect — it is not claimed as proven in-pipeline this turn.
