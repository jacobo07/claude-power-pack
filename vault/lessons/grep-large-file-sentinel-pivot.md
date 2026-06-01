# Grep tool sentinel on large files (cross-repo)

**Sealed:** 2026-06-01
**Severity:** transversal — Owner reports recurrence across ALL repos
**Sister rule:** v15 Bash blocklist (already in CLAUDE.md)

## The pattern

On Windows hosts, the `Grep` tool extends the same MSYS2-bridge fragility
that already affects `tail | head | cat | grep | find | ls` via Bash. The
Grep tool itself uses ripgrep through that bridge under load.

Trigger conditions (any TWO firing = high sentinel risk):

- File size ≥ 100 KB (any single file)
- Pattern with ≥ 3 regex alternations (`|` operators)
- Pattern with lookbehind/lookahead/complex character classes
- `output_mode: content` without a tight `head_limit`
- Concurrent batch with other Read/Glob/Bash calls

When trigger fires: harness returns
`[Tool result missing due to internal error]`. Same canonical sentinel
documented in `feedback_bash_bridge_transversal_hang.md` v14+.

## The pivot (canonical, copy-paste)

```powershell
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' -c "
import re
p = r'<absolute path>'
pat = re.compile(r'<pattern>')
for i, l in enumerate(open(p, encoding='utf-8', errors='replace'), 1):
    if pat.search(l):
        print(f'{i:5d}  {l.rstrip()[:100]}')
" 2>&1 | Select-Object -First 60
```

Why this works:

- Native Python on Windows has no MSYS2 bridge layer.
- The harness sees one PowerShell process; stdout streams in small
  chunks well under the frame-clip threshold.
- `Select-Object -First N` bounds output the same way `head_limit` did
  for Grep — but in PowerShell's own pipeline, not via the bridge.

## Post-sentinel recovery contract (Anti-Waiting G)

When the sentinel DOES fire (it still will, occasionally): the turn
AFTER must NEVER yield silently. Three obligations in order:

1. **Name the dropped frame.** "`Grep` returned
   `[Tool result missing due to internal error]` on `<file>` with
   pattern `<short>`."
2. **Re-issue with a DIFFERENT tool family.** Never the same Grep
   call. For large files: pivot to Python-via-PowerShell. For batches:
   re-issue ONE call solo. Sister rule from
   `parallel-batch-large-output-cascade.md`.
3. **State next concrete action.** Never close with "Waiting...",
   "Standing by...", "the harness will notify...". Sealed cross-repo
   2026-05-29 (Owner explicit ban); re-confirmed 2026-06-01.

The dead-screen hang the Owner reports cross-repo is the
sentinel-without-recovery-text combination. Sentinel alone is a tool
failure; sentinel + silent yield is the screen freeze.

## Origin

PP_DATASET ingestion 2026-06-01. A 329 KB / 15,425-line markdown file
plus a multi-alternation regex hit the sentinel on the first Grep call.
Pivoted to PowerShell + Python re; recovered cleanly with the same
results in <2 s. The ingestion continued without further sentinels.

## Cross-refs

- `~/.claude/CLAUDE.md` — Windows Bash Bridge Reliability + Anti-Waiting (G)
- `memory/feedback_grep_large_file_sentinel.md` — personal memory mirror
- `memory/feedback_bash_bridge_transversal_hang.md` — parent doctrine v14
- `vault/lessons/parallel-batch-large-output-cascade.md` — sister rule
