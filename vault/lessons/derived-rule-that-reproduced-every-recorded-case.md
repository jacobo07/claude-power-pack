# A derived rule reproduced every recorded case and was still wrong

**2026-09-15.** Companion to `installer-population-was-a-memory.md`. Both are
`PR-COVERAGE-BY-CONSTRUCTION-001`; this one is about the repair going wrong.

## The setup

`modules/mirror_discovery` carries `ALIASES`, a hand-written map of live→repo
names for pairs whose two halves are spelled differently. It held **one**
entry. The census found a second real pair — live `commands/cpp-compound.md`
against repo `commands/compound.md` — that nobody had recorded, and the
repaired installer would therefore have written a *second* file onto the
operator's machine beside the live one.

A hand-maintained map that had drifted to 1-of-2 is the same disease this
module has now had four times: hand-enrolled files, then a hand-declared
domain root, then a hand-curated install manifest, now a hand-written identity
map. So the instinct was right: close the class, do not add a line.

## The candidate rule, and the controls it passed

Frontmatter looks like the identity oracle. Twelve command sources drop a
`cpp-` prefix on disk while declaring `name: cpp-<x>`. Deriving the live name
from `name:` and measuring before implementing:

- it **reproduced the hand-written entry unaided** — `resume-sovereign.md →
  cpp-resume-sovereign.md`, exactly as a human had recorded it;
- it reproduced **every** declared alias, missing none;
- it produced **zero collisions** on either domain;
- agents were entirely unaffected.

That is four controls, including the one that feels conclusive: *the derived
rule independently re-derives the decision a human already made.*

## Why it was wrong anyway

Seven live command files — `autoupdate`, `customclaw`, `design-md`,
`obsidian-setup`, `update`, `vault-setup`, `vault-sync` — declare a `cpp-`
name while living under the **unprefixed** filename, and the harness lists
them by filename. For commands the filename is the registered name and
`name:` is decorative.

Deriving would have renamed eleven working commands to close one gap.

## The transferable trap

> **Reproducing every recorded instance is a necessary control and a
> systematically biased one. The recorded instances are precisely the cases
> somebody already thought about.**

A hand-maintained map is not a random sample of its domain. It is a sample of
the cases that *hurt* — the ones that surfaced, got diagnosed, got written
down. A rule inferred from those will re-derive them beautifully and can still
be wrong about the silent majority, because the silent majority is silent for
the opposite reason: nothing broke there.

So the control that mattered was not "does it reproduce the map". It was:

> **what does this rule do to the cases the map does NOT mention?**

One query, over the population the rule would newly govern rather than the
population it was inferred from. It cost two tool calls and it inverted the
decision.

The corollary is uncomfortable and worth keeping: **an estate with an
inconsistent convention cannot have that convention derived.** The map stays
hand-written. What changed is that missing an entry is no longer free —
`alias_candidates` nominates an unpaired live file when a repo source claims
its name, and **nominates only**, because acting on a nomination is the rename
mistake above.

## The sibling finding: a field with no reader

The inventory carries a `sha256` per claimed artifact. **Nothing in the estate
reads it.** The installer computes its own hashes from files; no other tool
touches the field. Written once in May, consumed by nothing — so two entries
drifted for four months in silence and were found by hand, which is not a
mechanism.

Refreshing the two numbers buys one honest day. The repair is to give the
orphan field a **consumer**, which only became possible once the claimed
artifacts had repo sources to compare against.

Generalisation: **an integrity value with no reader is not integrity, it is a
number.** When you find one, the question is never "is it current" — it is
"what would read it, and can that thing exist yet".

## Two instruments worth reusing

**A session's own injected instructions are a reachability oracle.** Asking
whether `rules/common/agents.md` affects behaviour was answered by observing
that two sibling files in the same tree appear in the running session's
context and this one does not. Presence in a repo, presence in the live tree,
and presence in a session are three different facts, and only the third is
effect.

**Ambient load is strictly additive, so the minimum of repeated runs estimates
intrinsic cost.** A budget gate that had been flapping red and green on one
tree now samples again only when the first run fails, and takes the best. Same
subject, same tree, seconds apart: **25.19s then 9.21s.** The threshold was
never touched — and a run whose tree moved mid-measurement is INCONCLUSIVE,
counted in neither column, because this estate already owns the failure where
a host-starved verdict is folded into the pass total.

## Evidence

`87c9d24` (alias + nomination detector, 3 gates), `8121228` (nine commands
captured), `33fe0f9` (restart captured, digests given a reader),
`35a9665` (ECC agent doctrine adapted), `b9d0be7` (budget gate).

claimed-without-source 10 → 0 · live-only commands 11 → 0 · command sources
76 → 86 · clean install 27 agents + 86 commands, E1 PASS · inventory digests
verified 32.
