---
title: Windows argv 8 KB cap — pass LLM user-message via STDIN, not argv
date: 2026-05-23
incident: WinError 206 during Paso 1.8 first-run of deep_research.py
scope: any PP-shipped tool that subprocess-invokes claude.exe with
       user content that may exceed ~8 KB
status: SEALED
---

## Trigger

Paso 1.8 of the deep-research-agent-2026-05-23 plan: first real
depth=1 breadth=2 run on a JEP 401 question. The driver fed two
fetched markdowns (~25 KB each, truncated per spec) into
`extract_learnings` which formatted them into a positional `prompt`
argument to `claude.exe`. The subprocess returned:

```
WinError 206: El nombre del archivo o la extensión es demasiado largo
```

The Windows process-creation API (`CreateProcessW`) caps the combined
command-line length at 32,767 wide characters. Real-world headroom is
much smaller — paths, system args, and quoting consume a chunk. With
two 25 KB markdowns concatenated into one argv slot, the effective
limit was blown well before reaching the cap.

The Reality Contract caught the failure honestly: `extract_learnings`
returned no learnings, the driver collected zero, and
`generate_report` emitted the INSUFFICIENT DATA template instead of
fabricating content. No silent failure, no invented URLs — exactly
what the contract guarantees.

## The rule

When subprocess-invoking `claude.exe` (or any CLI) with user-message
content that may exceed ~8 KB:

- **Pass the user message via STDIN**, never as argv.
- Keep the system prompt + small flags in argv (those are fixed-size).

For `claude.exe` specifically:

```python
args = [
    "claude.exe",
    "-p",                              # non-interactive
    "--disable-slash-commands",        # lock the spawned session down
    "--disallowed-tools", "*",
    "--append-system-prompt", system,  # small, fits in argv
    # NO positional prompt argument here
]
subprocess.run(args, input=user_message, ...)  # via STDIN
```

`claude.exe -p` reads stdin when no positional prompt is provided
(empirically verified 2026-05-23: `echo "Say HELLO" | claude.exe -p`
returned `HELLO`).

## Why this slipped past the spec

The n8n source workflow passes content via JSON over HTTP — the
argv cap doesn't apply to HTTP bodies. The reverse-engineering
translated `chainLlm.text` directly into a Python f-string passed
as argv, which is the natural-looking but wrong port. Bug surfaced
the first time the prompt grew past ~3 KB.

## Detection in advance (future)

Pre-flight check before any subprocess invocation:

```python
total_argv_chars = sum(len(s) for s in args) + len(args)  # +1 per separator
if total_argv_chars > 4096:
    # Refuse argv; force stdin path. Or split into smaller invocations.
```

`4096` is conservative; the real Win32 cap is higher but other args
+ quoting consume the budget unpredictably.

## Cross-references

- Empirical fix in production: `claude-power-pack/modules/deep-research/
  deep_research.py:_llm_claude_cli` — the post-fix subprocess.run uses
  `input=augmented_user` and omits the positional prompt arg.
- The same pattern applies to ANY Owner-spawned subprocess that may
  receive large content (page content, code reviews, log dumps).
- Sister lesson: `vault/lessons/heavy-io-must-be-governed.md` — both
  catalogue Windows-subprocess gotchas in PP-shipped tools.

## Vaccine

Future PP scripts that subprocess-invoke a CLI with user-content
arguments MUST either:

1. Use STDIN for the user content (the safer default), OR
2. Include the 4096-char pre-flight check above with a stdin
   fallback, OR
3. Document why argv is safe (e.g. the content is bounded
   constant-time, like a UUID or short flag value).

Missing any of the three without explicit justification is REJECTED
in code review.
