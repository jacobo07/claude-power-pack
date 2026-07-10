---
title: Universal Meta-Systems — Quick Reference Index
tier: reference
purpose: One-scan map of the seven universal meta-systems, the closed loop, the corpus paths, and how each maps into a domain. Loaded at STANDARD depth by the sleepy part.
---

# Universal Meta-Systems — Index

> Seven **universal meta-systems**: infrastructure whose output is *more and
> better systems*, not solved domain problems. Domain-blind: every noun is an
> abstract variable, so they work for ecommerce, SaaS, medicine, robotics,
> energy, AI, manufacturing, and games alike. Source corpus: `45dd1f9`
> (read-only; see `corpus-reference.md`).

## The seven meta-systems (build order)

| ID | Name | One-line capability | Layer | Corpus dataset |
|----|------|---------------------|-------|----------------|
| **MS-0** | Provenance Substrate | Reproducibility-and-lineage by construction — every artifact carries its origin; audit becomes re-derivation. | 0 (floor) | `datasets/MS-0_PROVENANCE_SUBSTRATE.md` |
| **MS-1** | Composition Fabric | Assemble any system from published contracts — `provides(X)` composes with `requires(X)`. | 1 | `datasets/MS-1_COMPOSITION_FABRIC.md` |
| **MS-3** | Compounding Substrate | A cross-system knowledge frontier + falling-marginal-cost law — each build cheaper than the last. | 1 | `datasets/MS-3_COMPOUNDING_SUBSTRATE.md` |
| **MS-4** | Capital Ledger | Account non-code capital (knowledge, trust, dormant capacity, liabilities) as first-class assets. | 1 | `datasets/MS-4_CAPITAL_LEDGER.md` |
| **MS-2** | Intent Compiler | Compile an intent → orthogonal concern planes → contracts → an assembled system. The machine that builds machines. | 2 | `datasets/MS-2_INTENT_COMPILER.md` |
| **MS-5** | Evolution & Integrity Fabric | Evolve anything forever, safely, without drift — evolve behind contracts + drift audit + rollback. | 2 | `datasets/MS-5_EVOLUTION_INTEGRITY_FABRIC.md` |
| **MS-6** | Absence Engine | Model what is missing or dormant as a first-class object and route it to be filled. | 2 | `datasets/MS-6_ABSENCE_ENGINE.md` |

## The closed loop (how the seven coexist)

```
MS-6 finds what's missing
   → MS-2 compiles it (from the frontier)
      → MS-1 assembles it (from contracts)
         → MS-0 makes it reproducible
            → MS-3 compounds the lesson (frontier grows, next build cheaper)
               → MS-4 prices the result (net capital)
                  → MS-5 keeps it all coherent, forever, safely
                     → MS-6 sees the new, deeper edge …
```

**Order of exposition matters.** MS-0 is the floor — everything embeds it, so it
is applied first. MS-6 closes the loop — it points at the next edge, so it is
often applied last (or first, when the task is "what should we even build?").

## How to apply one (domain-substitution)

Every meta-system is applied the same way — the machinery never changes, only
the noun-map:

1. **Name your domain's nouns.** For MS-0: what is your `artifact`? your
   `transform@version`? your `witness`? (For a data pipeline: a checkpoint, a
   training job @ code+data-version, the compute job.)
2. **Read the dataset** for that meta-system (read-only, from the corpus).
3. **Instantiate the abstract laws** against your nouns. The dataset's laws hold
   verbatim; you only supply the mapping.
4. **Check universality:** if the meta-system stays meaningful and non-trivial
   under your mapping, you have applied it correctly.

Worked mappings for five reference domains live in the corpus at
`UNIVERSALITY_PROOF.md`. Domain-agnostic worked examples live in `examples.md`.

## Corpus master files (for navigation)

| File | Use |
|------|-----|
| `MASTER_INDEX.md` | Full corpus navigation |
| `META_SYSTEM_REGISTRY.md` | The 7 with filter scorecards; the 2 killed + why |
| `CAPABILITY_GRAPH.md` | The capability graph with connection strengths |
| `GAP_MATRIX.md` | Each gap ↔ the meta-system that fills it ↔ evidence |
| `COMPOUND_EFFECT_MAP.md` | How each dataset makes the others cheaper |
| `UNIVERSALITY_PROOF.md` | ≥5 distinct-domain instantiations per meta-system |
| `DONE_GATE.md` | Corpus verification incl. contamination scan |

## Activation

- **Sleepy (automatic on keyword):** any of `meta-systems`, `meta-sistemas`,
  `provenance substrate`, `composition fabric`, `intent compiler`,
  `compounding substrate`, `capital ledger`, `absence engine`,
  `closed loop`, `MS-0`…`MS-6`, `apply the meta-systems`.
- **Explicit:** `/cpp-meta-systems <list|show MS-N|apply MS-N to "<intent>"|loop "<intent>">`.
