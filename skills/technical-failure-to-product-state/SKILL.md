---
name: technical-failure-to-product-state
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when an error, timeout or failed request is shown to a person, when a failure result carries a message string, or when auditing error copy, empty states and retry buttons. Classify at the boundary that sees the status into a closed union plus a cause for logs, give the failure arm no renderable message, make EMPTY constructible only from a success and retry unreachable from a non-retryable failure, and detect leaks by narrowing rather than by property name. Core rule - the layer that knows the status must not throw it away."
---

# Technical Failure to Product State

When software tells a person something went wrong, two different things are
decided: **what happened** (a status, an exception, a timeout) and **what that
means for you** (retry, wait, reconnect, nothing you can do). The first is
machine-attributable and belongs in logs. The second is product copy.

The defect is not that developers write bad error messages. It is that the layer
which *knows* the status throws it away before any layer that could act on it,
so the surface renders the only thing it was given.

> **A failure result carrying a `message: string` has already lost the
> argument.** Downstream cannot tell a dead network from a missing route from an
> expired session, so every surface either invents copy or prints the string.

## The shape that survives review

Classify at the one boundary that sees the status. Carry forward:

- **a closed union** the UI switches on — the product semantic;
- **a cause** — status, kind, the upstream's own words, a timestamp, a
  correlation id — for logs and support.

Then make the failure arm carry **no renderable message field at all**. A
component cannot print the transport by reaching for the obvious property when
there is nothing there to reach for. That is the difference between a convention
and a guarantee.

Debugging evidence *improves*: `status: 0` and `status: 404` used to be
indistinguishable downstream; now they are different states with the status kept.

## Two invariants worth making structural

- **`EMPTY` constructible only from a SUCCESS.** Then "the load failed and
  rendered an empty list" is unrepresentable rather than tested for.
- **A retry affordance unreachable from a non-retryable classification.** Not
  discouraged — unreachable. The primitive should DROP a retry handler passed
  alongside a permanent failure rather than trust the caller, because the caller
  is the party that does not know.

## Reassurance is a claim and needs evidence

Calming copy in a failure branch is usually asserted from the failure of the very
request that would have proved it. "The engine is still running", after the
engine's own status call failed, is invention.

The test is mechanical: **what does the failed path still know?** A read-only
surface knows its failure moved nothing and may say so. A surface whose failure
means it cannot tell whether something was committed must say *that* — and the
honest sentence is usually shorter and more trusted than the soothing one.

## Do not flag the upstream's PRODUCT message as a leak

The same property name sits on both sides of the line:

```
{state.kind === "error" && <p>{state.message}</p>}        LEAK
{state.kind === "ready" && data.status === "no_data"
                        && <p>{data.message}</p>}         NOT a leak
```

The first renders the failure arm of the client's own union — the words are the
transport's. The second renders a field of a successful response: the backend
explaining, in product language, why it has no evidence yet.

So the rule is **narrowing-based, not name-based**: a leak is a raw-cause read on
a binding *the enclosing branch narrowed to a failure discriminant*. A gate that
misses this accuses correct code, and a gate that cries wolf is switched off
within a week.

## Detect it structurally, because the words are not in the file

A copy regex finds surfaces that hardcode bad copy. It cannot find the dominant
case, where the words are minted in a client and the component contains only
`{state.message}`. Measured: 13 sites by regex, 14 real leaks by AST, the two
sets barely overlapping.

Then, building that sweep:

- **Learn the codebase's state vocabularies from the codebase.** One tree had
  three — `kind` (hook unions), `phase` (form machines), `status` (widgets). A
  sweep that knew two filed six real leaks as "unclassified".
- **A system state is not an entity status.** `item.status === "approved"`
  describes a row, not the health of a fetch. Resolve the condition's root
  against the module's **own bindings** (what a `use*()` hook or `useState`
  returned), never a list of plausible names — and recurse into the receiver
  only, or the property NAME matches a binding and domain content floods the
  denominator.
- **Name the happy path too.** A denominator that dumps every success branch into
  "unclassified" cannot distinguish *a state nobody classified* from *a state
  that needs no design*, which is the number the completion criterion uses.
- **Keep an `AMBIGUOUS_ABSENCE` family.** `!data` cannot say whether the load
  failed or the collection is empty. That ambiguity is the defect; folding it
  into `EMPTY` hides it.

## A justified exception is not debt, and must be able to fail

Once a form builds its own sentence, the detector's heuristic still matches it.
Leaving those in a shrink-only list they can never leave turns the inventory into
an excuse. Give them an exception entry with a **reason a reader can disagree
with**, and make the mechanism falsifiable three ways: a missing or trivial
reason is refused, a file exceeding its count reports as growth, a count larger
than measured reports as stale. Recompute the headline number *after* exceptions,
so it describes outstanding debt rather than detector matches.

## DON'T

- **Don't read a green suite as evidence the doctrine is enforced.** One estate
  asserted "never a raw 'Failed to fetch'" across ~20 test files and a dozen
  docstrings while having no state component at all — so every surface
  re-implemented it and one skeleton helper ended up defined twice,
  independently. A doctrine living only in comments and per-file tests reads
  exactly like an enforced one.
- **Don't trust a test fixture as a description of the producer.** A test
  asserting the backend's validation message reached the user carried a friendly
  invented fixture; the real route raised a Python exception *class name*, as a
  string, so the branch under test could never fire on it. Green, and measuring a
  world that does not occur.
- **Don't let a status code into the sentence.** It tells the reader nothing they
  can act on, and on a localised surface it is the one untranslatable fragment.
- **Don't delete a raw message without asking what it was doing.** Sometimes it
  is the upstream's genuine product copy and removing it loses real information.
- **Don't call a fix proven because the errors disappeared.** Hold the failure
  conditions constant and show the same failures reported differently. Errors
  that stopped happening prove nothing about how errors are presented.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/technical-failure-to-product-state.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
