---
type: component
created: 2026-09-30
updated: 2026-09-30
sources: []
path: knowledge/PORTFOLIO_LEARNINGS.md
status: LIVE
---

# PORTFOLIO_LEARNINGS.md

Ledger of where each governance rule came from: LRN-01..10, each "what happened · what was learned ·
rule · where it applies", pointing to the `governance/*.md` file that enforces the rule
(`knowledge/PORTFOLIO_LEARNINGS.md` @ `8574446`). 8,098 bytes; one commit, `de62e1b` (2026-07-11).

Status LIVE means the file exists and is referenced from PP `CLAUDE.md` ("Confirmed learnings"). In
practice it is **an archive**: 2 agent reads and 1 write in 30 days across 3,015 transcripts, and no
hook or tool reads it ([[measure-knowledge-store-consultation]]).

## Findings

- Low reads are partly by design: the enforced layer is `governance/`, which sessions read; this file
  records origins.
- The PP CLAUDE.md "standing obligation" to add each new learned pattern here the same session was
  barely met: the last entry was added 2026-07-30 and never committed; nothing since in ~2 months
  while sessions kept learning (see the Owner memory index). Correction: an earlier version of this
  page said "nothing since 2026-07-11" from git history alone — the uncommitted entry was invisible
  to that check.
- Defect: the ID `LRN-03` was used twice. That was the uncommitted 2026-07-30 entry.
- Overlaps this wiki's role: descriptive "what happened and why", separate from normative rules.

## Decision — applied 2026-09-30 (Owner: "y")

- File frozen as history with a header note; duplicate renumbered to LRN-11 (no other file
  referenced any LRN ID).
- PP `CLAUDE.md` obligation changed: new learnings go to their existing homes (UKDL, memory,
  governance); origin stories go to this wiki. The `KNOWN_FALSE_POSITIVES.md` half of the obligation
  is unchanged (no evidence about it).
- Rationale: an unmet obligation in an always-loaded file costs tokens every call and teaches that
  rules there are optional ([[lean-always-loaded-context]]).
- Not committed: the ledger also carries the uncommitted 2026-07-30 entry, which is another
  session's work.
