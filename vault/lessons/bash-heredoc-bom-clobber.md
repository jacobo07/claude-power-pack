---
title: bash heredoc append `>>` clobbers UTF-8 BOM-prefixed files on Windows
date: 2026-05-23
incident: POST-2 of auto-testing-skill plan — session_lessons.md head replaced
scope: any PP-shipped script that uses bash heredoc append on files with BOM
status: SEALED
---

## Trigger

POST-2 of the Auto-Testing Skill plan: a `cat >> file.md <<'EOF' ... EOF`
heredoc was expected to append a fresh "## 2026-05-23 — Auto-Testing"
table to the end of `vault/knowledge_base/session_lessons.md`.

The actual outcome: the heredoc content landed at the TOP of the file
and overwrote the first 13 lines (including the "## 2026-05-21 —
Marker > Cloaking" section header and its first content paragraph).
A second `## ... tier-2 auto-checkpoint` line was also appended at
the file tail.

The file's first byte is `﻿` (UTF-8 BOM). Bash on Windows
(MSYS2 / Git Bash) appears to interact with BOM-prefixed files such
that `>>` does NOT seek to end-of-file before writing — under some
conditions it writes at the beginning, after the BOM. Other tools
(`tee`, `printf >>`) may behave the same way.

The diff hunk shape was:
```
@@ -1,19 +1,17 @@
-﻿
-## 2026-05-21 — Marker > Cloaking ...
-...12 lines of original content...
+
+---
+## 2026-05-23 — Auto-Testing ...
+...new content...
```

The Reality Contract caught the breakage: `grep -n "Marker > Cloaking"`
returned nothing post-append, and `git diff` showed the head clobber
clearly.

## The rule

When appending to a markdown / text file on Windows that MAY carry a
UTF-8 BOM (most session-managed PP files do — including
`session_lessons.md`, `ukdl-universal.md`, the apex doc, and any file
written by PowerShell `Out-File` or Notepad), use **Python's
read-bytes + write-bytes pattern**, NOT bash heredoc `>>`:

```python
from pathlib import Path
p = Path("target.md")
data = p.read_bytes()                # preserves the BOM exactly
new_block = "\n\n## New section\n...\n".encode("utf-8")
p.write_bytes(data + new_block)      # idempotent + atomic-ish on Win
```

If a heredoc is essential (e.g. CI scripts that need to be
shell-portable), strip the BOM first:

```bash
# Detect BOM and strip before append.
if [ "$(head -c 3 file.md | od -An -tx1 | tr -d ' ')" = "efbbbf" ]; then
    tail -c +4 file.md > file.md.tmp && mv file.md.tmp file.md
fi
cat >> file.md <<'EOF'
... new content ...
EOF
```

But Python is simpler and removes the failure mode entirely.

## Detection in advance (future)

Pre-flight check before any large bash heredoc append:

```bash
FILE=session_lessons.md
LINES_BEFORE=$(wc -l < "$FILE")
# ... heredoc ...
LINES_AFTER=$(wc -l < "$FILE")
DIFF=$((LINES_AFTER - LINES_BEFORE))
EXPECTED=14
if [ "$DIFF" -lt "$EXPECTED" ]; then
    echo "BOM clobber suspected: only $DIFF lines added, expected $EXPECTED+"
    git diff "$FILE" | head -30
fi
```

PP scripts that append to markdown files SHOULD prefer the Python
pattern and skip the heredoc entirely.

## Cross-references

- The auto-testing-skill POST-2 incident is the empirical proof:
  `vault/plans/auto-testing-skill-2026-05-23.md` status row.
- Recovery pattern: `git checkout HEAD -- <file>` cleanly restores
  any clobbered file before the working tree is staged. The Python
  re-append then lands correctly.

## Vaccine

Any PP-shipped script (Bash, PowerShell, Node, Python) that appends
to a Markdown or text file MUST either:

1. Use Python `read_bytes` + `write_bytes` (preserves BOM), OR
2. Explicitly check + strip the BOM before bash `>>` heredoc, OR
3. Document why the target file is guaranteed to be BOM-free.

Missing any of the three is REJECTED in code review on Windows hosts.
