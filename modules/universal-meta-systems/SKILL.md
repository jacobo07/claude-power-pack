---
name: universal-meta-systems
description: "Apply seven universal, domain-blind meta-systems (provenance, composition, intent-compilation, compounding, capital, evolution, absence) to any project. Opt-in via keyword or /cpp-meta-systems. Exposes the read-only corpus 45dd1f9; never reimplements it."
---

# Universal Meta-Systems

> **What this is.** A read-only bridge from the Power Pack to a corpus of seven
> *universal meta-systems* — infrastructure whose output is **more and better
> systems**, not solved domain problems. Every noun in them is an abstract
> variable, so the same seven work for ecommerce, SaaS, medicine, robotics,
> energy, AI, manufacturing, and games. This module lets any Power-Pack project
> apply them to its own domain **without ever seeing another domain's
> vocabulary**.

**This module does not reimplement the meta-systems.** It exposes the corpus
(`45dd1f9`, read-only) and gives you the protocol to apply a meta-system to your
domain. The doctrine lives in the datasets; this file is the on-ramp.

## Activation (opt-in — never automatic)

The meta-systems are silent until you ask for them:

- **Keyword (loads the sleepy part):** `meta-systems` / `meta-sistemas` /
  `provenance substrate` / `composition fabric` / `intent compiler` /
  `compounding substrate` / `capital ledger` / `absence engine` /
  `closed loop` / `MS-0`…`MS-6` / `apply the meta-systems`.
- **Explicit command:** `/cpp-meta-systems …` (see `commands/meta-systems.md`).

A project that never mentions them never inherits them. This is the opt-in
contract — the meta-systems compose *with* a project's own cognitive
architecture, they do not overwrite it.

## Tiered loading

| Depth | When | Load |
|-------|------|------|
| LIGHT | "what are the meta-systems?" / pick one | `index.md` (this module's map) |
| STANDARD | apply ONE meta-system to a domain | `index.md` + the one target `datasets/MS-N_*.md` from the corpus |
| DEEP | run the closed loop / compose several | `index.md` + `examples.md` + the relevant datasets + `COMPOUND_EFFECT_MAP.md` |
| FORENSIC | integrity / universality audit | + `UNIVERSALITY_PROOF.md` + `DONE_GATE.md` + `META_SYSTEM_REGISTRY.md` |

Never load all seven datasets at once. Match the task to a tier, then read only
the datasets that tier names. Locate the corpus via `corpus-reference.md`.

## The seven (one line each)

- **MS-0 Provenance Substrate** — reproducibility-and-lineage by construction.
  The floor; everything embeds it.
- **MS-1 Composition Fabric** — assemble systems from published contracts
  (`provides(X)` ↔ `requires(X)`).
- **MS-3 Compounding Substrate** — a shared knowledge frontier; each build
  cheaper than the last, and it proves it.
- **MS-4 Capital Ledger** — book non-code capital (knowledge, trust, dormant
  capacity, liabilities) as first-class assets.
- **MS-2 Intent Compiler** — compile intent → orthogonal concern planes →
  contracts → an assembled system.
- **MS-5 Evolution & Integrity Fabric** — evolve anything forever, safely,
  without drift (evolve-behind-contracts + drift audit + rollback).
- **MS-6 Absence Engine** — model what is missing or dormant as a first-class
  object and route it to be filled.

## The application protocol (domain-substitution)

The corpus proves its universality with one test, and that test *is* how you
apply any meta-system:

> The meta-system's machinery is domain-blind; only the mapping of its abstract
> nouns onto your domain changes.

**Steps (identical for every meta-system):**

1. **State your intent or artifact** in your own domain's words.
2. **Pick the meta-system** whose capability matches (use `index.md`; if the
   task is "what's even missing?", start at MS-6; if "make this reproducible",
   MS-0; etc.).
3. **Map the nouns.** Write down, for that dataset, what each abstract noun is
   in your world (e.g. for MS-0: `artifact`, `transform@version`, `witness`).
4. **Instantiate the laws.** The dataset's laws hold verbatim; you only supply
   the mapping. Do not translate the machinery — translate the nouns.
5. **Universality check.** If the meta-system stays meaningful and non-trivial
   under your mapping, the application is correct. If it collapses to a triviality,
   you mapped the wrong noun — re-map, do not modify the meta-system.

## The closed loop (compose all seven)

```
MS-6 finds what's missing → MS-2 compiles it → MS-1 assembles it
   → MS-0 makes it reproducible → MS-3 compounds the lesson
      → MS-4 prices the result → MS-5 keeps it coherent forever → (MS-6 again)
```

Apply MS-0 first (it is the floor every other one trusts). Apply MS-6 to decide
what to build next. The loop is self-directed, self-improving construction — and
it can be run over *any* corpus, including a project's own architecture.

## Hard rules for this module

1. **Corpus is read-only.** Never edit `datasets/`, `phases/`, or the corpus
   master files. The integration exposes; it never mutates. (Corpus HEAD stays
   at `45dd1f9`.)
2. **Universality preserved.** No file here names a specific domain or ops
   ecosystem. Nouns stay abstract. A contamination check is part of the DONE
   gate (`README.md` §Validation).
3. **Opt-in only.** Do not inject the meta-systems into a project that did not
   ask for them. The sleepy trigger and the command are the only entry points.
4. **Expose, don't reimplement.** If a project wants a meta-system as running
   code, that is a *separate* build in that project — this module hands over the
   doctrine and the noun-map, not an implementation.

## Files in this module

- `index.md` — quick-reference map of the seven + the loop + corpus paths.
- `README.md` — what they are, when to use, 5-minute quickstart, validation.
- `examples.md` — domain-agnostic worked applications.
- `corpus-reference.md` — how to locate the read-only corpus + the contract.
- `INTEGRATION_NOTES.md` — the Phase-0 reality scan + the four ULTRA-PLAN
  decisions (audit trail).

## Return-to-dormant

After a meta-systems task completes, this module returns to dormant. It
re-loads only on the next keyword match or `/cpp-meta-systems` invocation.
