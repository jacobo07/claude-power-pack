---
title: OSR-L1 — Arrival Does Not Witness Ordering
date: 2026-07-31
status: DRAFTED — awaiting placement by `rule_compiler` (OWNER_QUEUE 2026-07-31 (a))
origin: vault/audits/usirc/ — the only element of an 18-dataset chartered category
  that survived a discovered-denominator sweep
executable: modules/osr/ordering.py — 6 gates green in tools/test_osr.py
---

# OSR-L1 — Arrival Does Not Witness Ordering

## The law

> Reaching a state does not prove that the architectural contracts required to reach
> it were satisfied. A terminal state is evidence of arrival and evidence of nothing
> else — not of which prerequisites ran, nor in what order, nor whether any of them
> succeeded.

## Why the estate does not already have it

Three neighbours state something adjacent and none states this:

- **Mistake #16, Scaffold Illusion** — *compiles is not works*. About the gap between
  a build succeeding and a system functioning. Says nothing about order.
- **Mistake #17** — *static verification does not prove runtime works*. About the gap
  between reading code and running it. Says nothing about order.
- **CLAE Part XXV** — nineteen production-reality gates at four lifecycle points. Each
  gate asks whether a required property *holds*, never whether the sequence that was
  supposed to establish it *ran*.

The residue is narrow and real: every one of those checks is an **arrival check**. A
system that skips a prerequisite, runs two out of order, or executes a prerequisite
*after* the state that depended on it will pass all three and be wrong.

## The failure shape, concretely

```
required:  mount_resources -> init_managers -> load_save_data -> hub
observed:  mount_resources -> init_managers -> hub -> load_save_data
```

The hub was reached. It renders. Every arrival check agrees the system is healthy. And
the save data was loaded *after* the screen that consumes it, so the first user action
reads an empty model — a defect that reproduces intermittently, presents as a data bug,
and is investigated in the wrong subsystem for as long as it takes someone to ask what
order things actually happened in.

`modules/osr/ordering.py` returns `AFTER_TERMINAL` on exactly this input, names
`load_save_data`, and exits non-zero. Verified end to end through
`tools/osr_audit.py --verify-order` this session.

## The counter-rule that makes it honest

**The required sequence must be DECLARED, never derived from the run under test.** A
checker that infers the required order from what it observed passes every run by
construction — it is the generator grading its own output, which CLAE Part XVI names
as the self-verification limit. The declared sequence comes from a spec, a boot
manifest, or an architectural sequence contract, and from nowhere else.

Corollary, enforced in code: **no declared sequence yields `UNMEASURED`, and
`UNMEASURED` fails the gate.** An ordering claim nobody measured is not a satisfied
one. A gate that passes on absent evidence is the quiet pass this estate has sealed as
a defect four separate times.

## Verdict vocabulary

| Verdict | Meaning |
|---|---|
| `SATISFIED` | every declared prerequisite occurred, in order, before the terminal state |
| `MISSING_PREREQUISITE` | a declared prerequisite never appears in the trace |
| `AFTER_TERMINAL` | the terminal state was reached before a prerequisite ran |
| `OUT_OF_ORDER` | every prerequisite ran, but a declared pair is inverted |
| `TERMINAL_NOT_REACHED` | the state whose arrival was in question never occurred |
| `UNMEASURED` | no declared sequence, or no observed trace — fails the gate |

## Placement request

Not placed by the agent. `rule_compiler` owns rule admission and placement
unconditionally, and `modules/osr/` is bound by
`vault/audits/usirc/BOUNDARY_CONTRACT.md` prohibition 8 to route rather than promote.
Proposed neighbour: **HR-OUTPUT-002**, which refuses a completion claim whose tests
were never observed to pass. Both refuse the same thing — a conclusion asserted from a
state rather than from the evidence that should have produced it.

## Generality check

Stated without a domain: no console, no framework, no vendor. It applies to a game
menu that reaches its hub, a web application that renders a dashboard, a daemon that
reports ready, and a deployment that returns HTTP 200. The proposal that produced it
framed it as a console-emulator concern; measured, the console instrumentation belongs
to another repo and the **law** is domain-blind — which is why it is the one element of
that category that survived.
