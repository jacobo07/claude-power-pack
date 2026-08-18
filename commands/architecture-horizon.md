---
description: Which part of the architecture stops being valid first? Ranks units by what their invalidation carries, and names the mutually-dependent core where nothing invalidates first.
---

# /architecture-horizon

UPAC residue R2 (`vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`). A sweep of all
402 module files found exactly one counterfactual symbol in the estate
(`rule_compiler/effect_harness._counterfactual_ids`), and it is governance-scoped — it
replays a *rule* against the incident that produced it. Nothing answered the same
question about *architecture*.

## Run it

```
python -m modules.architecture_horizon.horizon                    # ranked view
python -m modules.architecture_horizon.horizon --invalidate <unit>
python -m modules.architecture_horizon.horizon --json
python -m modules.architecture_horizon.horizon --root <path>      # any repo
```

Standing rows:

```
python tools/verify_spp.py --row architecture-horizon
python tools/verify_spp.py --row architecture-horizon-gates
```

## What it answers

If this unit's contract changes, what else must change with it? That is the transitive
dependent closure of the real Python import graph, computed over package directories —
the granularity a person owns, a commit touches, and a contract is negotiated over.

A unit with a wide closure is one the architecture cannot cheaply revise. That is the
brief's "what stops being valid first" at the granularity the evidence supports.

## The finding you should read first

Measured 2026-08-19 on this estate: **83 units, 81 intra-estate edges, and an
eleven-unit mutually-dependent core** —

```
cdio · cognitive_os · dataset_first · decision_review · duplicate_to_advantage
fable_distillation · frontier_intelligence · liveness · parallel_mesh · spec_gate · wrapper
```

Every member transitively reaches every other, which is why a dozen units tie at 27–29
transitive dependents. **Inside that group there is no unit that invalidates first** —
they move together. The ranking orders the groups' reach, never a sequence within one.
A ranking printed without the group would be a false hierarchy, so the group is printed
above the ranking, not in a footnote.

## What it deliberately does not do

It does not simulate. Scale, latency inflation, multi-region, adversarial traffic, data
growth and team growth are printed as **declared unmodelled**, each with the reason. All
of them need a running system, a load model or a topology that a repository does not
contain, and numbers produced from those would carry the authority of measurement and the
content of a guess.

It also does not duplicate existing owners: `decision_review.compute_blast_radius` matches
keyword surfaces over a decision's *prose*, `graphify` holds knowledge coordinates rather
than import edges, `liveness/reachability` maps surface→module rather than module→module,
and `refcheck` covers documentation references.

## The gate

`--gate` compares the load-bearing set against `LOAD_BEARING_BASELINE` — a **named set**,
never a count or a ratio, because a ratio falls when the estate grows and a count falls
when a module is deleted. Only names force the number down for the right reason. The
baseline currently ships **unsealed**, so the gate reports and never fails; sealing it is
a deliberate act, and inventing one on the fly would pin whatever today happens to be and
call it intent.
