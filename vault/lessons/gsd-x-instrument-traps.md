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

---

2026-09-16. Four more, from the session that took GSD X from a branch to the
live UserPromptSubmit path. Two of these were caught by a guard or an advisory
rather than by my own reading, which is the part worth noticing.

---

## T-GSDX-MTIME-IS-NOT-AUTHORSHIP-001

**Trap.** Deciding which side of a drift is *newer* by comparing file mtimes,
when one side is managed by git.

`test_dispatcher_drift.js` compared `mtimeMs` of the repo mirror against the live
dispatcher. git stamps a file's mtime at **checkout** time, so creating a
worktree, switching a branch or finishing a merge makes the repo copy "newer"
than a live file nobody has touched for days. Creating an integration worktree
did exactly that, and the gate reported

    diverged -- REPO is newer ... if repo is newer, sync repo->live

against a live dispatcher 3360 bytes larger and genuinely last edited the
previous evening. Followed literally it overwrites the executing dispatcher with
a stale snapshot and destroys another pane's work.

The detection half was never wrong: the sha256 comparison was correct throughout.
Only the **direction** was invalid — and the direction is the half that chooses
between a harmless copy and data loss.

**Rule.** mtime answers "when did something write these bytes", never "when did
this content last change". For a git-managed file the authorship signal is
`git log -1 --format=%ct -- <path>`; for an unversioned file mtime is honest,
because nothing rewrites it mechanically. Never compare the two kinds of clock as
if they were one.

**Corollary.** A remediation sentence is part of the verdict. A gate confident
enough to name a direction must be right about it, or it is worse than a gate
that only says "these differ" — and a third outcome, DIRECTION UNDETERMINED, is
the correct answer whenever the repo copy is uncommitted or git is unreachable.

---

## T-GSDX-SNAPSHOT-MUST-NOT-BE-LINE-MERGED-001

**Trap.** Resolving a merge conflict in a **snapshot** artifact the way you would
resolve one in source.

Both branches carried a copy of the live dispatcher, 62678 and 67503 bytes, both
stale against a live file at 72078. Git offered a normal content conflict and the
reflex is to merge the hunks. That reflex produces a dispatcher that never
existed on any machine — strictly worse than either input, because a snapshot's
only value is that it faithfully records one real historical state.

**Rule.** Ask what an artifact *is* before choosing a resolution. Source merges;
a snapshot is chosen. For a snapshot, take one whole side (the fresher baseline)
and reconcile deliberately afterwards, bracketed on the live file's hash.

---

## T-GSDX-ECHOED-PHRASE-CANNOT-DISCRIMINATE-001

**Trap.** Counting occurrences of your hook's own phrasing in a chain's
aggregated stdout, to decide whether your hook emitted.

Discrimination was measured by grepping the real chain output for
`ExecutionOS Lite tier`. A trivial prompt scored 1 and read as a false
escalation. It was not: the match was inside the **JIT hook's** injected project
spec, which quotes the phrase. Any hook that echoes your vocabulary is
indistinguishable from you under that instrument, and a shared chain is exactly
where such echoes live.

**Rule.** Discriminate on a **provenance** marker no other producer can emit —
here `modules.gsd_x.tier`. Re-measured on provenance, heavy emitted and trivial
was silent, which is the opposite of the first reading.

---

## T-GSDX-MACHINE-NOISE-HIDES-THE-ONE-REAL-LINE-001

**Trap.** Classifying a diff by its aggregate shape and treating it as
disposable.

A 431-line uncommitted delta blocking a fast-forward was 215 machine-generated
CEPS rows appended by a PostToolUse hook — some of them produced by my own tool
calls that session, so the file could never be clean while any session ran, and
"wait for the writer to finish" was not a strategy. On that reading the delta was
noise and safe to discard.

It was 99.8% noise and it carried one line of another pane's real design work:

    -  declares an `aesthetic_family` (F1-F9, CDIO-06) ... three-question picker
    +  declares an `aesthetic_family` (F1-F10, CDIO-06) ... four-question picker

The single `-` line is what exposed it. A pure append has no deletions.

**Rule.** Before calling a diff machine-generated, inspect its **deletions**
specifically, and count the added lines that do *not* match the machine pattern.
Both are one command. The aggregate is what hides the exception, and the
exception is somebody's uncommitted work.

**Corollary.** When a union resolution is applied to a hunk containing a
*modified* line rather than pure appends, it keeps both spellings — here that
would have left the taxonomy declaring nine families and ten families in the same
file. Verify the modified line survives exactly once, after resolving.
