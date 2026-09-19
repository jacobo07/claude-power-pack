# CEPS auto-append writes malformed rows into the canonical rule corpus

**Measured** 2026-09-19, claude-power-pack, session `37cfb187`, while promoting the
exact-target continuation rules into `vault/knowledge_base/ukdl-universal.md`
(Phase 3 of milestone v1).

## What was found

The UKDL working copy carried **1,029 uncommitted auto-generated rows** appended
by a CEPS producer running outside the session. During the ~40 minutes it took to
promote one section, the count rose to **1,031** — the producer is live and still
appending.

They are not wrong in a subtle way. Four defects, each visible in the rows:

**1. The "tool" key is a fragment of shell text, not a tool.** Real examples,
copied verbatim from the appended block:

```
[tooling/powershell:g]
[tooling/powershell:m]
[regression/powershell:foreach($f]
[regression/powershell:print(GREEN]
[regression/powershell:[IO.File]::WriteAllText(]
[regression/powershell:env:PYTHONIOENCODING=utf]
[tooling/powershell:ForEach-Object]
```

`powershell:g`, `powershell:m` and `powershell:print(GREEN` name nothing. The
producer appears to be splitting a command string on whitespace and taking a
token, so the key is whatever word happened to sit at that position.

**2. The same event id repeats.** `ceps_91bd58c83335b24d` appears four times in
the block under four different keys (`powershell:Select-Object`, `powershell:node`
twice, `powershell:python.exe`, `powershell:[IO.File]::WriteAllText(`). One
underlying event is being recorded once per token it was split into.

**3. The "learning" is a constant template.** Every row of a class ends with the
same sentence — *"Confirm the tool actually ran and returned the expected output
before trusting its absence-of-error"* or *"Before touching X, verify the
regression scenario (Y) is still covered by a passing test"*. The only varying
part is the interpolated fragment, which is defect 1. A rule that is identical
across a thousand rows carries no information per row.

**4. It captures the measuring apparatus.** Two rows in the block record this
session's own probe output:

```
Error: critical lane used 3249ms of 1500ms; pool NOT spawne...
Error: ETIMEDOUT after 5000ms
```

The first is the dispatcher's **deadline drill** — a synthetic chain that exists
to overrun its budget on purpose. Recording its designed behaviour as an
estate-wide "tool failure" is the corpus learning that its own test fixture is
broken. And one row was appended in reaction to the very verification script
being used to check the block, which makes the producer partly a recorder of
whoever is currently looking at it.

## Why it matters more than row count

`ukdl-universal.md` is the estate's canonical rule corpus — the file
`MEMORY.md` points to first for "search by id before re-deriving". Diluting it
with a thousand content-free rows is a retrieval problem, not a disk problem: the
signal-to-noise of every future lookup falls, and the rows carry `ceps_` ids that
look like citable rule ids but resolve to nothing.

There is a second, sharper hazard, and it is what surfaced this. **The rows sit
uncommitted.** Any session that commits that file with a normal pathspec takes
all 1,031 under its own message — the file-granular collision described in
`~/.claude/rules/concurrent-writers-shared-tree.md`. This session avoided it only
by backing the file up, returning it to HEAD, committing its own 92 lines alone,
and restoring the rows afterwards (verified: 882 CEPS rows before and after, git
reporting 1029 insertions and zero deletions). That is not a manoeuvre every
session will think to perform, and the next one to touch the UKDL will silently
absorb the block.

## Recommended fix, in order

1. **Stop keying on a whitespace token.** The key must be a tool name from a
   closed set (`Bash`, `PowerShell`, `Edit`, …), or the row is not written.
   Err toward not writing: a missing row costs nothing, a malformed one is
   permanent.
2. **One row per event id.** Deduplicate on `ceps_<hash>` before append.
3. **Do not write a row whose learning is the class template with no
   event-specific content.** If the only variable part is the key, and the key is
   defect 1, there is nothing to record.
4. **Exclude the estate's own test and drill output.** A chain named
   `*-deadline-drill-chain` overrunning its budget is a passing test, not an
   incident.
5. **Write somewhere other than the canonical corpus** — its own
   `vault/ceps/learnings.jsonl`, promoted into the UKDL only by an explicit,
   reviewed step. A producer that appends directly to a hand-curated rule file
   will keep colliding with hand edits regardless of row quality.

## Status

Rows left **in place and uncommitted** by Owner decision (2026-09-19): not purged,
not committed. This file is the defect record against the generator. Nothing in
the producer has been changed by this session.

## Not established

Which module writes them. The rows carry `ceps_` ids and the estate has
`vault/ceps/events.jsonl` plus a `pp-ceps-analyst` agent, but the specific append
path into `ukdl-universal.md` was not traced — the session's scope was the
promotion, and tracing the writer would have meant editing a producer while it
was running. That trace is the first step of the fix.
