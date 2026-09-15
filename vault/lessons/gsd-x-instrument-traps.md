# Instrument traps measured while building GSD X

2026-09-15. Five of these cost a wrong conclusion inside one session, and four
of the five were in instruments I had just written myself. Candidates for the
shared UKDL corpus; kept in a new file rather than appended to
`ukdl-universal.md` because another writer was live in this checkout and a
shared file is exactly where pathspec scoping stops protecting anyone.

---

## T-GSDX-APERTURE-AT-THE-LAUNCHER-001

**Trap.** Measuring a runtime at its launcher directory and concluding it has no
code.

`~/.claude/skills/gsd-*` is 72 single-file `SKILL.md` prompts and nothing else,
so the first reading was "GSD is a prompt framework with no extension surface".
The runtime is `~/.claude/gsd-core/`: 246 `.cjs`, a CLI, a capability system, a
hook bus and a frozen host-integration SDK. The skills are thin launchers that
resolve their workflow spec at call time.

**Rule.** When a component's directory looks too small for what it does, find
what it *invokes* before concluding what it *is*. A launcher is not an aperture.

---

## T-GSDX-MIRROR-IS-NOT-LIVE-001

**Trap.** `Test-Path` against a repo's `hooks/` directory answering "is this hook
live".

The Power Pack repo's `hooks/` is a mirror. The live hooks are `~/.claude/hooks/`.
Four probes returned `False` for files that exist and run on every prompt.

**Rule.** For any artifact with a canonical copy and a deployed copy, liveness is
a question about the deployed one. This estate already carries the split-brain
lesson for the dispatcher; it generalises to every file beside it.

---

## T-GSDX-NAME-GREP-AS-PRIOR-ART-001

**Trap.** Grepping for a proposal's own name, finding nothing, and reading that
as an empty field.

"Zero occurrences of GSD X in the repo" was accurate. The inference was false: a
classification ladder was already reaching the model on the exact target event
under a different name, from a constant string. No grep for the proposal's
vocabulary could ever have found it.

**Rule.** Absence of the NAME is not absence of the CAPABILITY. Enumerate the
population structurally, from the registration surfaces, and ask what each member
DOES. Same family as `PR-COVERAGE-BY-CONSTRUCTION-001`, one level down: at the
instrument rather than at the registry.

---

## T-GSDX-DISCRIMINATOR-MATCHES-PROSE-001

**Trap.** A textual discriminator that matches the prose it is reading.

Two successive versions of the sweep returned a false negative on the one hook it
existed to find. First `does it read the prompt` — the file contains the word
`prompt` because it parses a session id, while its emitted text comes from a
zero-argument function returning a constant. Then `does the line concatenate` —
the ladder itself contains the prose `5+ files`, and `+ files` reads as
concatenation.

**Rule.** Put the discriminator where the question actually lives, and strip the
string spans before looking for code. Mentioning a thing and branching on it are
different facts, and only one of them is about the emission.

---

## T-GSDX-MUTATION-SURVIVED-IS-A-SUITE-HOLE-001

**Trap.** Reading a surviving mutation as "the fix was unnecessary".

Reverting the abstain gate left the suite green, because no corpus prompt reaches
the state where the two spellings differ. The fix was correct and the suite could
not see it.

**Rule.** A mutation nothing catches is a hole in the suite, not a property of
the code. Drive the differing state directly; an unreachable branch is an
unpinned one.

---

## PR-GSDX-ABSTENTION-NEEDS-A-POSITIVE-TO-CANCEL-001

**Process rule, from two bugs with opposite signs.**

A verdict that declines to speak (`NOT_APPLICABLE`, dormant, not-applicable-here)
must never cancel an abstention earned by a verdict that wanted to speak and
could not. One dormant contract suppressed nine blocked ones and every prompt
bottomed out on the floor.

And the mirror: a blocked verdict only means "wanted to run and could not" if the
capability was ADDRESSED. Where an evidence gate runs before a dormancy gate, an
unaddressed capability still returns blocked — and one contract requiring
evidence no caller can supply then makes *everything* abstain.

**Rule.** Abstention is cancelled by positives only, and earned by addressed
blockers only. Both halves, or the gate fires on everything or on nothing.

---

## PR-GSDX-SAY-NOTHING-WHEN-YOU-AGREE-001

**Process rule.** An advisory that fires on every prompt to restate the standing
default is noise, and noise is what gets a gate switched off. When the measured
answer equals the incumbent's constant, emit nothing — and count the silence, so
the rate at which the measurement adds nothing stays visible rather than
flattering.
