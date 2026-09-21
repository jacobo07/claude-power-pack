---
description: Decide which entry-surface architecture a product's measured constraints justify, and where its value / identity / persistence / assurance / consent / commitment / activation boundaries fall. Refuses in four distinguishable ways rather than guessing.
---

# /surface-architecture

Eleven capability contracts existed and none answered *"given this product's
constraints, which surface architecture is justified?"*. That gap was declared by the
incumbents, not inferred: `architecture_reconstruction`'s own `non_scope` holds
"deciding what to build" and "specifying the change".

This command is also what makes the module reachable. `modules/liveness/reachability.py`
seeds from `commands/*.md` among four other globs, and resolves a module from a literal
path in the body. The paths below are therefore load-bearing text, not decoration --
deleting them orphans the package.

## Decide

Write a context file naming what you have MEASURED. Every field is optional and `None`
means nobody looked, which is never a default:

```
python modules/surface_architecture/resolver.py <context.json>
python modules/surface_architecture/resolver.py <context.json> --json
```

Four outcomes, four exit codes. The first three match `modules/cdicf/selector.js` so
two gates stay comparable; the fourth is added because this subject needs it.

| exit | outcome | what it means | what to do |
|---|---|---|---|
| 0 | `RECOMMEND` | one archetype is justified by the measured facts | read the boundaries and the rejected alternatives |
| 20 | `ABSTAIN` | the facts are complete and no archetype fits, or several tie | the product's constraints, not the measurement, are the problem |
| 21 | `REQUIRE_APPROVAL` | justified, but a constraint puts the consequence outside the product, or a boundary has no valid position | a human decides |
| 22 | `UNDETERMINED` | it could not be evaluated | go and measure the named facts |

**20 and 22 are not the same answer.** "We have the facts and none fits" and "we could
not evaluate" need opposite responses, and collapsing them is the failure this estate
has already paid for in `done_gate/strength_ladder`, `cdio/scorer` and
`capability_runtime/applicability`.

A `RECOMMEND` is evidence, not an instruction. It carries no authority to build
anything, and nothing downstream may treat it as approval.

## Verticals

The kernel is domain-blind. Domain vocabulary lives in
`modules/surface_architecture/verticals/signup.py`, which is a six-component
`SpecializationSpec` compiled through the universal-meta-systems specialization map and
recorded as a genealogy row, so an improvement to the kernel still reaches it.

```
python tools/seed_surface_architecture_contract.py --dry-run
python tools/seed_signup_derivative.py --dry-run
```

Both refuse rather than overwrite, and both ship a positive control: the derivative seed
deliberately contaminates a probe spec and requires the contamination detector to fire,
because a clean result from a detector nobody proved still works is indistinguishable
from a clean result.

## Gates

```
python tools/test_surface_architecture.py
python tools/prg_assess.py --claim IMPLEMENTED
```

`tools/prg_assess.py` grades a completion claim against collected evidence using the
thirteen-rung LAW IX ladder in `modules/done_gate/strength_ladder.py`. Run it before
writing "done" anywhere about this capability.

## What this does NOT do

Registering a capability makes it **discoverable**, not **callable**.
`capability_runtime/applicability.compile_stack` returns capability ids and never
invokes a capability, so no dispatch path runs `resolve()` on your behalf. Building that
dispatch is DS08, which the binding `vault/audits/apir/NON_DUPLICATION_LEDGER.md`
reserves to `hooks/hook-dispatcher.js`. The contract's own `non_scope` says so, and the
signup derivative inherits it verbatim.

It also does not own visual quality or interaction behaviour (CDIO, which is evaluative
and never authors), which component realises a semantic (`modules/cdicf`), or
authentication mechanics.
