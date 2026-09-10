---
name: usea
description: "Universal Software Engineering Architect — verify the sealed constitution, audit which Power Pack owner discharges each of the fifteen laws, and grade a completion claim against the evidence actually collected (LAW IX)."
user-invocable: true
---

# /cpp-usea — Universal Software Engineering Architect

The constitution is sealed, read-only source material at
`vault/constitution/usea/constitution.raw.md`. This command is the activation
surface for the three mechanisms built around it. It exposes the corpus; it
never mutates it.

Read `vault/constitution/usea/PROVENANCE.md` before treating the stored copy as
byte-identical to the Owner's original — the fidelity claim is recorded as
INFERRED, and the reason is stated there.

## Subcommands

### `/cpp-usea verify`

Check the canonical corpus against its seal.

```
python tools/usea_corpus_gate.py --verify
```

Four outcomes with distinct exit codes, because a verifier that rejected its
subject and one that could not judge it are different evidence:

| Outcome | Exit | Means |
|---|---|---|
| `VALID` | 0 | corpus matches the seal |
| `SUBJECT_INVALID` | 1 | corpus is readable and has drifted |
| `UNREADABLE` | 3 | corpus or seal missing / undecodable |
| `GATE_FAILED` | 4 | the gate broke; the corpus was **not** judged |

`GATE_FAILED` outranks a subject verdict found in the same run. Do not report a
`GATE_FAILED` as corpus drift — it says nothing about the corpus.

### `/cpp-usea own`

Audit which Power Pack owner discharges each constitutional law.

```
python tools/usea_ownership_audit.py
```

Measured at seal time: **13 of 15 laws owned outright, 2 EXTEND, 0 NEW.** Run
this before proposing any new engine, fabric, runtime, registry or baseline
that claims a constitutional responsibility — LAW IV and section 9 require a new
component to earn its existence against the owners already present, and this is
the evidence that would have to be overturned first.

A cited owner that vanishes turns the run red **by name**, not by count. The
audit proves cited owners resolve on disk; it does **not** prove each one
discharges its law. Presence is not reachability.

### `/cpp-usea done <STATE>`

Grade a completion claim against collected evidence (LAW IX).

```
python tools/test_done_strength_ladder.py     # the gate for the mechanism
```

Import `modules.done_gate.strength_ladder.assess(claimed, evidence)` to grade a
real claim. Section 26's thirteen states, in order:

`IDEA · SPECIFIED · IMPLEMENTED · WIRED · REACHABLE · ACTIVATABLE · EXECUTED ·
VERIFIED · INTEGRATION-VERIFIED · ADVERSARIALLY-VERIFIED ·
PRODUCTION-LIKE-VERIFIED · PRODUCTION-REALITY-VERIFIED · REGRESSION-PROVEN`

Three outcomes. `SUPPORTED`, `OVERSTATED`, and `UNDETERMINED` — the last when
required evidence was never collected. **`UNDETERMINED` is not a pass and not a
failure of the work.** Evidence never collected and evidence collected-and-
negative are different states of the world; a gate that returns the same answer
for both is how an unknown launders itself into a green.

## The one rule this command exists to enforce

Do not claim a rung the evidence does not reach. The ladder caps the claim at
whatever the evidence actually supports and names what is missing — which is
useful precisely when the honest answer is lower than the one you wanted.
