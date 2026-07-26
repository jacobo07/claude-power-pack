# CLAUDE.md Governance — index first, vault as source

> Sealed BL-CLAUDEMD-COMPACT, 2026-07-26. Plan:
> `vault/plans/claude-md-compaction-2026-07-26.md`.
> Enforcement: `hooks/claude_md_linter_stop.js` (live, Stop chain).
> Config: `vault/config/claude_md_thresholds.json`.
> Gate: `node tools/test_claude_md_compaction.js`.

## The problem this closes

`~/.claude/CLAUDE.md` is the only text guaranteed to be in context in every
session in every repo. That makes it the most valuable real estate in the
system — and the default destination for every new rule. Nothing ever retired
anything, so it grew monotonically until it crossed Claude Code's 40,000-char
performance warning.

Twice during the compaction session itself, other panes appended to the file
while it was being compacted (+289 chars, then +277). The growth is not an
event to clean up periodically; it is continuous pressure that needs a
standing policy.

**T-CLAUDE-MD-GROWTH-WITHOUT-RETIREMENT-001** — *CLAUDE.md grows with every new
system and nothing is ever retired automatically, so it accumulates until it
crosses the performance limit. The fix is not recurring manual trimming — it is
that CLAUDE.md becomes an index of pointers while the normative content lives in
the vault, where it can grow without competing for the context budget.*

## The rule: TRIGGER stays, EXPLANATION moves

A section may be externalized **only if its TRIGGER stays in CLAUDE.md and only
its EXPLANATION moves.**

- **TRIGGER** (stays): the recognition condition, the imperative, the pointer.
  What makes the agent notice the situation and act correctly.
- **EXPLANATION** (moves): rationale, incident origin, worked examples, recovery
  narratives, detail tables — what only matters once you are already in the
  situation *and* the trigger named the file.

**Why the split runs this way and not by size.** A pointer is followed only if
the agent chooses to follow it. Anything that must fire *without* the agent
deciding to read anything is unconditional and stays. Externalize a trigger and
the rule does not become less prominent — it silently stops existing. That is
`T-SDD-OS-IMPLICIT-ACTIVATION-001` reappearing in a new file, which is exactly
the failure this system was built to prevent.

**PR-CLAUDE-MD-INDEX-FIRST-001** — *Every new normative block over 500 chars
added to CLAUDE.md must have its canonical file in the vault. CLAUDE.md carries
the pointer, the activation triggers, and a one-line description; the full
content lives in the vault and is referenced or injected. This prevents
T-CLAUDE-MD-GROWTH-WITHOUT-RETIREMENT-001.*

## Protected sections — never externalized

Listed in `protected` in the config; the linter excludes them from every
recommendation:

Windows Bash Bridge Reliability · Parallel Subagent Limit / Anti-Waiting (A)-(I)
· HARD RULES router triggers · Environment Awareness · Critical Rules · Reality
Contract core · Token Efficiency · PP Activation Criteria · SDD-OS.

The first two are additionally sealed by
`reference_claude_md_40k_char_warning.md` (*never relocate Bash-Bridge/Anti-
Waiting rules*) — they are 44% of the original file and the single most
tempting target, which is precisely why the prohibition exists.

## Enforcement (live, not aspirational)

`hooks/claude_md_linter_stop.js` runs on every Stop event
(`hook-dispatcher.js`, Stop chain). Above `margin` it emits a WARN, above `hard`
an ALERT, and in both cases it **names the largest unprotected sections that
carry no vault pointer**, with the destination directory.

Its v1 counted correctly and then prescribed `trim_claude_md.py`. By 2026-07-26
that trimmer reclaimed **zero** — it harvests provenance prose, and that had
already been taken on 2026-07-04. *Dead advice is worse than no advice, because
it looks like a remedy.* v2 names what to move.

Thresholds are configuration, never literals in the hook. A corrupt or missing
config falls back to built-in defaults, so the gate degrades to counting —
never to silence.

## Adding a new block — the procedure

1. Write the canonical file first: `~/.claude/knowledge_vault/claude-doctrine/<topic>-detail.md`.
2. Add to CLAUDE.md only: the trigger(s), the one-line imperative, the pointer.
3. Keep it under 500 chars. If it will not fit, the block is explanation, not
   trigger — reread step 1.
4. Check the budget: `node tools/test_claude_md_compaction.js`
   (`V-CMD-UNDER-TARGET` must pass).

## When the linter says there is nothing left to move

That message is real, not a failure: it means every remaining oversized section
is protected always-on doctrine. At that point the file cannot be compacted
further without deleting a rule. **Reduce by retiring a rule the system no
longer needs — a deliberate decision with an owner — never by demoting a trigger
to a pointer.**
