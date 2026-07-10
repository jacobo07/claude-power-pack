---
title: Universal Meta-Systems — Domain-Agnostic Worked Examples
tier: reference
purpose: Show how to apply the meta-systems to any project without hardcoding a domain. Loaded at DEEP depth. Every example uses abstract nouns; the reader substitutes their own.
---

# Worked Examples (domain-agnostic)

Each example applies the **domain-substitution** protocol from `SKILL.md`. The
machinery is fixed; you supply the noun-map. Placeholders like `<your artifact>`
are where you write your domain's noun — the example never picks a domain for you.

---

## Example 1 — Apply MS-0 (Provenance) to a new project

**Goal:** make every output of a new project reproducible-by-construction, so
audits become re-derivations instead of ceremony.

**Step 1 — Map the nouns** (from `datasets/MS-0`, Part I):

| MS-0 abstract noun | Your domain's noun |
|---|---|
| `artifact` | `<the thing your project produces>` |
| `producer` / `transform@version` | `<the process that makes it> @ <its version>` |
| `inputs` | `<what the process consumes>` |
| `witness` | `<who or what executed the process>` |
| `claim` | `<any statement you assert about an artifact>` |

**Step 2 — Instantiate the nine laws verbatim.** For instance, Law 1 ("No orphan
artifacts") becomes: *every `<your artifact>` records which `<process@version>`
produced it, from which `<inputs>`, and by which `<witness>`.* Law 9 ("Provenance
never blocks progress; absent provenance blocks consolidation") becomes: *work
proceeds without full lineage, but a `<your artifact>` cannot be trusted /
promoted / reused downstream until its chain is closed.*

**Step 3 — North-star metric:** Reproduction Coverage — the fraction of your
authoritative artifacts regenerable from lineage alone. Drive it toward 100%.

**Universality check:** if "reconstruct any artifact from its recorded origin"
is still a meaningful, non-trivial guarantee in your project, MS-0 applied
correctly. It always is — that is why MS-0 is the floor everything else trusts.

---

## Example 2 — Use MS-6 (Absence) to decide what to build next

**Goal:** stop guessing at the backlog; let absence itself point at the
highest-value hole.

**Step 1 — Map the nouns** (from `datasets/MS-6`): an `absence` is a first-class
object — a *missing capability*, an *uncollected signal*, a *capital deficit*, a
*missing contract*, or an *integrity gap* in your world.

**Step 2 — Enumerate absences, don't solve them yet.** Write each as an object
with a type and a value estimate. "We have no reproducible way to make `<X>`" is
a missing-capability absence. "We never record `<signal Y>`" is an
uncollected-signal absence. "This subsystem has unbooked drift" is an
integrity-gap absence.

**Step 3 — Route each absence** to the meta-system that fills it: a missing
capability → **MS-2** to compile it; a dormant-but-validated asset → **MS-1** to
re-admit it; an integrity gap → **MS-5** to fix it. MS-6's job is to *model and
prioritize*, then hand off — not to build.

**Step 4 — Kill re-learned dead ends.** Absences that were already refuted stay
as *negative knowledge* so the project never re-investigates them.

**Universality check:** if "the project's effort is now aimed at its own
highest-value holes" is true, MS-6 applied correctly.

---

## Example 3 — Run the closed loop over any corpus

**Goal:** self-directed, self-improving construction over a body of work (a
codebase, a document set, a product surface — any `corpus`).

```
MS-6 finds what's missing in the corpus
  → MS-2 compiles the missing capability from the accumulated frontier
     → MS-1 assembles it from existing contracts (reuse, don't rebuild)
        → MS-0 makes the new capability reproducible by construction
           → MS-3 distills the lesson into the frontier (next build is cheaper)
              → MS-4 books the net capital the build created
                 → MS-5 keeps the whole corpus coherent, drift-free, reversible
                    → MS-6 now sees the next, deeper edge …
```

**Order discipline:** MS-0 is applied first as the floor (everything downstream
trusts provenanced artifacts). MS-6 opens and closes each turn of the loop.
Because MS-2 and MS-5 are strongly recursive, the loop **can be run over its own
architecture** — the corpus improving the corpus.

**When to stop a turn:** when MS-4 shows the next build costs more net capital
than it creates, or MS-6 surfaces no absence above your value threshold.

---

## Example 4 — Compose MS-1 + MS-5 for swappable, evolvable parts

**Goal:** build a subsystem you can replace or upgrade later without breaking
its consumers.

1. **MS-1:** define the subsystem's `provides(<contract>)` and its consumers'
   `requires(<contract>)`. Any compliant provider now composes with any compliant
   consumer — this is the swap boundary.
2. **MS-5:** evolve the subsystem *behind* that contract. The drift auditor
   watches for the contract's meaning silently shifting; rollback re-points to a
   prior provenanced version (MS-0) if an upgrade regresses.

**Universality check:** if "swap or upgrade the implementation without touching
consumers, and catch drift before it corrupts the boundary" holds, the
composition applied correctly.

---

## Pattern behind every example

Every application is the same three moves: **name your nouns → instantiate the
dataset's laws verbatim → check universality.** You never edit a meta-system and
you never import another domain's words. If an application feels like it needs
the machinery changed, you mapped the wrong noun — re-map, don't rewrite.
