---
name: kclear
description: Session checkpoint + handoff — atomic write, token-lean (v3)
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# /kclear — Session Checkpoint & Handoff (v3, token-lean)

**Goal:** one atomic write of session state, < 30s, < 2k tokens. Vault-first long-term memory, memory-index for the rolling handoff only.

---

## What you do (fixed caps — do NOT exceed)

1. **Extract** from the conversation. Hard limits:

   | Field | Cap | Guidance |
   |---|---|---|
   | `summary` | ≤ 400 chars | one coherent sentence per thing built/changed; no bullet-fluff |
   | `pending` | max 5 items, each ≤ 80 chars | priority order; string or `{title,detail}` |
   | `insights` | max 3, only genuinely non-derivable | category/title/body/path/tags |
   | `lesson` | ≤ 200 chars | one atomic learning per session, or omit |

   Skip derivable content (code conventions, file paths, git history, recent changes). Empty list > padded list.

2. **Build** payload JSON in memory (no temp files):

   ```json
   {
     "session_id": "<id if known else 'unknown'>",
     "date": "YYYY-MM-DD",
     "summary": "≤400 chars",
     "pending": ["..."],
     "insights": [{"category":"feedback|project|reference|user","title":"...","body":"...","path":null,"tags":[]}],
     "lesson": "≤200 chars or omit field"
   }
   ```

3. **Invoke** via stdin (cross-platform, no `/tmp`):

   ```bash
   echo '<json>' | python "$USERPROFILE/.claude/skills/claude-power-pack/tools/session_checkpoint.py" record --stdin
   ```

   Bash/zsh on Windows resolves `$USERPROFILE`; fall back to `$HOME` if unset. PowerShell: `$env:USERPROFILE`. **Don't** write to `/tmp` first — stdin is the contract.

4. **Print** verbatim:

   ```
   Session saved.
     Handoff:  memory/project_session_handoff.md
     Lesson:   vault/knowledge_base/session_lessons.md  (if lesson provided)
     Insights: _audit_cache/insights.json  (+N new)
   Next: /clear → resume with the first prompt of the next session.
   ```

5. **Suggest** `/clear`.

---

## Registering a corrected error (optional, after any fix)

```bash
python "$USERPROFILE/.claude/skills/claude-power-pack/tools/session_checkpoint.py" learn-error \
  --category "windows" \
  --symptom  "DateTime.TryParse 2-arg overload missing in PS 5.1" \
  --root-cause "PS 5.1 TryParse requires 3 args (str, IFormatProvider, DateTimeStyles, out DateTime)" \
  --fix "try/catch + [DateTime]::Parse(str, InvariantCulture, AssumeUniversal|AdjustToUniversal)"
```

Writes to `vault/knowledge_base/errors.md` (each line < 400 chars). Use this instead of burying fixes in conversation.

---

## Tool guarantees

Atomic write (`tempfile.mkstemp` + `os.replace`, Windows + POSIX). Insight dedup by SHA256(category|title|body). `memory/MEMORY.md` updated with single one-line Session Handoff entry (prior replaced). `vault/knowledge_base/{session_lessons,errors}.md` bootstrapped on first write (append-only). Insights with `path` surface via gatekeeper when that file is read.

## Path anchors

| OS/Shell | Variable |
|---|---|
| bash/zsh/Git Bash | `$USERPROFILE` (Windows) or `$HOME` |
| PowerShell | `$env:USERPROFILE` |
| cmd | `%USERPROFILE%` |

Tool lives at `<userprofile>/.claude/skills/claude-power-pack/tools/session_checkpoint.py` regardless of project cwd. **Don't** invoke as `python tools/session_checkpoint.py` — no project-local copy exists.

## When to use

End of work session before `/clear` · before context rot threshold (15+ exchanges) · when context budget drops below 30% free.
