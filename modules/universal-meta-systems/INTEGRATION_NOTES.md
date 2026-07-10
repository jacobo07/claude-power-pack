---
title: Universal Meta-Systems — Integration Notes (Phase 0 Reality Scan + ULTRA-PLAN)
tier: reference
purpose: Records the Power Pack reality scan and the four ULTRA-PLAN decisions that shaped this integration. Not loaded at runtime — audit trail only.
---

# Universal Meta-Systems → Power Pack — Integration Notes

> Audit artifact for the integration. Explains **why** the integration has the
> shape it has, so a future maintainer does not have to re-derive it.

## FASE 0 — Power Pack Reality Scan (findings)

The Power Pack exposes capabilities through a **four-layer pattern**, observed
consistently across `distiller`, `executionos-lite`, and `knowledge-graph`:

1. **`modules/<name>/`** — the content (a `core.md` / `SKILL.md` + supporting
   docs). This is where a capability's substance lives.
2. **`parts/sleepy/<name>.md`** — a small, tiered *loader* that points into the
   module. Loaded **only** when a trigger keyword matches (see the root
   `SKILL.md` "Sleepy Parts" table). This is the opt-in gate.
3. **Root `SKILL.md` "Sleepy Parts" table** — the router. A trigger→part row
   here is what makes a capability discoverable without contaminating every
   session.
4. **`SKILLBANK.md`** — the human-readable index (documentation, not routing).

Slash commands (`commands/*.md`) are an optional fifth surface, hot-loaded, for
explicit user invocation (`/cpp-*`). No `settings.json` edit is required to add
one — command markdown is registered by presence.

**Consequence for this integration:** the meta-systems must follow this pattern
exactly. Imposing a new architecture on top of the Power Pack would violate the
POWER-PACK-FIRST hard rule. So the integration is: one module + one sleepy part
+ one router row + one SKILLBANK entry + one command. Nothing more.

## The corpus (read-only source of truth)

- **Location:** local repo `universal-meta-systems-corpus`, HEAD **`45dd1f9`**
  ("corpus complete, all gates PASS"). No git remote is configured — the corpus
  is a local artifact, referenced by SHA + discovery, never by a public URL.
- **Shape:** 7 doctrine datasets (`datasets/MS-*.md`), 4 discovery phases
  (`phases/`), and cross-reference master files. **No code** — the corpus is
  domain-blind doctrine. Each dataset has an identical 18-Part structure.
- **Contract:** this integration NEVER modifies the corpus. It exposes it. See
  `corpus-reference.md` for the discovery order and the read-only contract.

## The four ULTRA-PLAN decisions

**D1 — Mechanism = (e) combination.** Module + sleepy part + router row +
SKILLBANK entry + `/cpp-meta-systems` command. Mirrors the existing pattern;
adds no new architecture.

**D2 — Activation = keyword trigger, opt-in.** The sleepy part loads only on a
meta-systems keyword. A project that never mentions the meta-systems never sees
them. Explicit invocation via `/cpp-meta-systems`. Never auto-active.

**D3 — Mapping = domain-substitution.** The corpus already proves its
universality via the **domain-substitution test** (`UNIVERSALITY_PROOF.md`): the
machinery is domain-blind; only the mapping of abstract nouns onto a domain
changes. That test *is* the application protocol. The module does not
reimplement any meta-system — it hands the reader the dataset and the noun-map.

**D4 — Docs = README + examples.** `README.md` answers what/when/how in under 5
minutes. `examples.md` gives domain-agnostic worked applications (apply MS-0 to
a new project; use MS-6 to find gaps; run the closed loop over any corpus).

## Universality guard (contamination scan)

Every file in this module is checked against the same rule the corpus uses: no
vocabulary from any specific domain or ops ecosystem. Nouns stay abstract
(`artifact`, `contract`, `intent`, `frontier`, `capital`, `absence`). A reader
in ecommerce, SaaS, medicine, robotics, energy, or games maps the nouns onto
their world without ever seeing someone else's.
