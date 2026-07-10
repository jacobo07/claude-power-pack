---
name: cpp-meta-systems
description: "Apply the seven universal, domain-blind meta-systems (provenance, composition, intent-compiler, compounding, capital, evolution, absence) to any project. Explicit opt-in entry point. Exposes the read-only corpus 45dd1f9; never modifies it. Subcommands: list / show / apply / loop / audit."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# /cpp-meta-systems — Universal Meta-Systems

Explicit, opt-in entry point to the seven universal meta-systems. Domain-blind:
the same seven apply to any project (ecommerce, SaaS, medicine, robotics, energy,
AI, manufacturing, games) — you supply your domain's nouns, the machinery never
changes. Full module: `modules/universal-meta-systems/` (start at `SKILL.md`).
Corpus is **read-only** at SHA `45dd1f9` (locate via
`modules/universal-meta-systems/corpus-reference.md`).

## Invocation

```
/cpp-meta-systems list                     # the seven + the loop (LIGHT: reads index.md)
/cpp-meta-systems show MS-N                 # summarize one meta-system (STANDARD: reads its dataset)
/cpp-meta-systems apply MS-N to "<intent>"  # apply one to your domain via noun-substitution
/cpp-meta-systems loop "<intent-or-corpus>" # run the closed loop over a target (DEEP)
/cpp-meta-systems audit                     # universality + read-only integrity check (FORENSIC)
```

`MS-N` is one of `MS-0`…`MS-6`.

## What each subcommand does

- **list** — Load `modules/universal-meta-systems/index.md`; print the seven
  one-liners + the closed loop + the corpus paths. No corpus dataset read.
- **show MS-N** — Locate the corpus, read only `datasets/MS-N_*.md`, and
  summarize its doctrine, abstract nouns (Part I), and north-star metric. Quote
  the laws; do not paraphrase.
- **apply MS-N to "\<intent\>"** — Run the **domain-substitution** protocol:
  (1) restate the intent in the user's nouns; (2) map those nouns onto MS-N's
  abstract nouns; (3) instantiate MS-N's laws verbatim against the map;
  (4) universality check. Output is the applied meta-system for *their* domain —
  never another domain's vocabulary.
- **loop "\<target\>"** — Walk `MS-6 → MS-2 → MS-1 → MS-0 → MS-3 → MS-4 → MS-5`
  over the target. MS-0 applied first as the floor; MS-6 opens/closes each turn.
  Stop a turn when MS-4 shows negative net capital or MS-6 finds no absence above
  the value threshold. Loads `examples.md` + the loop-relevant datasets.
- **audit** — Verify: corpus HEAD still `45dd1f9` (or a DONE-gate-passing
  descendant); no file under the corpus modified; no domain vocabulary in this
  module (`grep` the module for domain names → expect zero); opt-in intact.

## Rules

- **Read-only corpus.** Never write to `datasets/` / `phases/` / corpus master
  files. A doctrine problem is a finding to report, not a file to edit.
- **Universality preserved.** Never inject a specific domain's vocabulary into
  output or into any module file. Nouns stay abstract until the user maps them.
- **Opt-in.** This command (and the sleepy keyword trigger) are the only entry
  points. Do not surface the meta-systems in a session that did not ask.
- **Expose, don't reimplement.** Hand over doctrine + the noun-map. Turning a
  meta-system into running code is a separate build in the consuming project.

## Output

- `list` → the seven + loop + corpus locations.
- `show` → a faithful, law-quoting summary of one meta-system.
- `apply` → the meta-system instantiated for the user's domain (noun-map + laws
  applied + universality verdict).
- `loop` → a per-stage plan over the target with stop conditions.
- `audit` → PASS/FAIL on corpus-intact + no-contamination + opt-in.
