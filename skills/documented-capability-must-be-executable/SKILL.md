---
name: documented-capability-must-be-executable
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when writing or reviewing documentation that promises a command, path, flag, endpoint or enforcement (README, docstring, runbook, verification report), or when fixing a documented capability. Extract every documented command and run it, give each capability an explicit status (LIVE, PLANNED, ABSENT), land the enforcement, its test and the sentence claiming it together, and never rewrite a historical report. Core rule - a documented capability nobody executes is indistinguishable from a working one."
---

# A Documented Capability Must Be Executable

Documentation written beside a change describes what the author *intended*. Nothing
re-reads it afterwards, and nothing executes it. So a README can promise a command,
name a path, or assert an enforcement that has never existed — and the project will
behave, for years, exactly as if the promise were kept, because the only thing the
promise changes is what humans believe.

> **A documented capability nobody executes is indistinguishable from a working one,
> and the difference only surfaces when someone depends on it.**

This is the docs-shaped sibling of a gate that never runs. A gate that cannot fire and
a gate that passes produce the same observable; a capability that was promised and one
that works produce the same *document*.

## The three shapes, in increasing order of how well they hide

1. **The capability does not exist.** A README's validation command names a module
   with zero occurrences in the codebase. Anyone who ran it got an import error and
   assumed they held it wrong; mostly nobody ran it at all.
2. **The capability exists and its documented invocation is dead.** Worse, because the
   first half is now true: the module is real, so a reader who checks *that* stops
   checking. The argument — a path, a flag, an env var, an endpoint — was deleted
   months ago, and the documented line still fails.
3. **The document asserts an enforcement that is not implemented.** The most dangerous,
   because it reads as a *constraint* rather than an instruction. Nobody runs a
   constraint; they rely on it, and build on top of it.

Shape 2 is the one to expect after a partial fix. **Making the command real does not
make the documented line real** — those are separate claims, and closing the first
while reporting the second as closed is how a defect survives its own repair.

## Fixing one phantom is the likeliest moment to create another

Writing "the validator enforces X" and *then* implementing X leaves a window in which
the document is exactly the defect being fixed. If the session ends, the budget runs
out, or the next step turns out harder than expected, that sentence is now permanent,
load-bearing, and false — and it carries the authority of a fresh commit.

So: **the enforcement, its test, and the sentence claiming it land together.** Not as a
tidiness preference — as the only ordering in which the document is never ahead of the
code. A commit that splits them for "reviewability" has optimised the wrong thing.

## Status beats tense

Prose has no way to say "this is aspirational", so it says everything in the present
tense and every reader takes it as current. Give each documented capability an explicit
status, and the ambiguity disappears:

| status | meaning |
|---|---|
| **LIVE** | implemented, reachable, exercised by a test or a real delivery |
| **PLANNED** | not implemented; name the slice building it |
| **ABSENT** | described historically; no implementation exists |

Then a claim that decays is *visibly* wrong rather than quietly wrong, and a reader who
disagrees has something specific to disagree with.

## The durable defence executes, it does not advise

The reflex fix is a sentence telling future readers to keep docs current. That is
operator discipline, which is the thing the design exists to replace, and it is
answering a mechanical failure with prose — the same error one level up.

**Extract every command a document promises and run it.** A code block in a README is a
claim with an exit code; treat it as a test. The check is cheap, it fails loudly, and
unlike a review it cannot get tired. Where a documented command is genuinely not
runnable in CI (it needs credentials, a device, a live store), that is not an exemption
— it is a status of its own, declared, so "we cannot check this one" never silently
becomes "this one is fine".

## DON'T

- **Don't read a docstring as evidence about behaviour.** It was accurate about intent
  on the day it was written, which is a different claim, and it is the artifact least
  likely to have been updated.
- **Don't trust the half you happened to check.** Module exists ≠ command runs.
  Command runs ≠ it does what the sentence beside it says.
- **Don't let a historical record be rewritten to match the present.** A verification
  report describes a run that happened. Editing its output to match today's filenames
  fabricates a verification. Supersede it with a dated header; keep the original.
- **Don't count a comment as a constraint.** If a rule matters, it is a check with a
  name and a failing branch. The constraint that survived three months as a README
  sentence in the source incident was violated by the very tree that documented it.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/documented-capability-must-be-executable.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
