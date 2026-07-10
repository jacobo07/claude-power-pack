# Universal Meta-Systems — for any Power-Pack project

**Five-minute version:** the Power Pack ships a bridge to seven *universal
meta-systems* — infrastructure whose output is *more and better systems*, not
solved domain problems. They are **domain-blind**: every noun is an abstract
variable, so the same seven apply to ecommerce, SaaS, medicine, robotics,
energy, AI, manufacturing, or games. This module lets you apply them to **your**
project without touching the corpus and without inheriting any other domain's
vocabulary.

## What they are

| Meta-system | Gives your project, for free… |
|---|---|
| **MS-0 Provenance Substrate** | Every artifact is reproducible from its recorded origin. Audits become re-derivations. |
| **MS-1 Composition Fabric** | Systems assembled from published contracts; parts swap without touching consumers. |
| **MS-3 Compounding Substrate** | A knowledge frontier where each build is cheaper than the last — and it proves it. |
| **MS-4 Capital Ledger** | Non-code value (knowledge, trust, dormant capacity, debt) measured as first-class assets. |
| **MS-2 Intent Compiler** | An intent compiles into orthogonal concern planes → contracts → an assembled system. |
| **MS-5 Evolution & Integrity Fabric** | Evolve anything forever, safely, without drift — behind contracts, with drift audit + rollback. |
| **MS-6 Absence Engine** | What's missing or dormant becomes a first-class object routed to be filled. |

They form a **closed loop**: MS-6 finds the gap → MS-2 compiles it → MS-1
assembles it → MS-0 makes it reproducible → MS-3 compounds the lesson → MS-4
prices it → MS-5 keeps it coherent → MS-6 sees the next edge.

## When to use them

- **"Make this reproducible / auditable by construction"** → MS-0.
- **"Assemble this from reusable, swappable parts"** → MS-1.
- **"Why is every build as expensive as the last?"** → MS-3.
- **"What is our non-code value actually worth?"** → MS-4.
- **"Turn this intent into a real system"** → MS-2.
- **"Grow this forever without it rotting or drifting"** → MS-5.
- **"What should we even build next / what's missing?"** → MS-6.
- **"Apply a self-improving construction loop to a whole corpus"** → the loop.

Do **not** reach for them for a single-file fix or a lookup. They are for
system-shaped work — architecture, capability-building, integrity, longevity.

## Quickstart (under 5 minutes)

1. **Activate** (opt-in): mention a keyword (`meta-systems`, `MS-0`,
   `absence engine`, `closed loop`, …) or run `/cpp-meta-systems list`.
2. **Pick one** from the table above by the outcome you want.
3. **Read its dataset** (read-only) — locate the corpus via
   `corpus-reference.md`, open `datasets/MS-N_*.md`.
4. **Map your nouns.** Write down what each abstract noun is in your domain
   (the dataset's Part I names them). Example for MS-0: *artifact* = your build
   output, *transform@version* = the process that made it, *witness* = who/what
   ran it.
5. **Instantiate the laws.** The dataset's laws hold verbatim against your
   noun-map. You supply the mapping; you never rewrite the machinery.
6. **Check universality:** does the meta-system stay meaningful and non-trivial
   under your mapping? If yes, done. If it went trivial, you mapped the wrong
   noun — re-map.

Domain-agnostic worked examples: see `examples.md`.

## How this fits the Power Pack

This is a standard Power-Pack sleepy module. It obeys the four-layer pattern:
`modules/universal-meta-systems/` (this content) ← `parts/sleepy/meta-systems.md`
(tiered loader) ← the root `SKILL.md` "Sleepy Parts" trigger row ← `/cpp-meta-systems`
for explicit invocation. It is **opt-in**: silent until a keyword or the command
fires, so projects that don't want it are never touched.

## Validation / DONE gate

An instance of this integration is correct when **all** hold:

1. **Corpus untouched.** The corpus HEAD is still `45dd1f9`; no file under the
   corpus `datasets/` / `phases/` / master files was modified.
2. **No domain contamination.** No file in this module names a specific domain
   or ops ecosystem. Nouns stay abstract. (Grep this module for domain names —
   zero hits.)
3. **Opt-in verified.** Without a keyword or the command, the meta-systems do
   not appear in a session. A project that does not ask for them keeps its own
   architecture untouched.
4. **5-minute usability.** A newcomer can apply one meta-system to their domain
   using only this README + the target dataset, in under five minutes.
5. **Power Pack unchanged for non-users.** Existing tiers/triggers behave
   identically for any session that never mentions the meta-systems.

## Do not

- Do not edit the corpus.
- Do not hardcode a domain into any file here.
- Do not auto-activate in projects that didn't ask.
- Do not reimplement a meta-system inside this module — expose and hand off.
