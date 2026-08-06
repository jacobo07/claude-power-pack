---
title: CDICF — Phase 2 Overlap & Ownership Audit (D2A classification of 25 proposed datasets)
date: 2026-08-06
depends_on: CPP_DESIGN_REALITY_MAP.md
status: BLOCKING artifact for STOP #1
verdict: MAJORITY_OWNED — 18 of 25 resolve to an existing owner
---

# Phase 2 — Overlap & Ownership Audit

## Headline

| | |
|---|---|
| Candidate datasets evaluated | **25** |
| REJECT — owned at equal or greater maturity | **7** |
| EXTEND / MERGE / GENERALIZE an existing owner | **11** |
| **NEW** — genuine, unowned, executable residue | **5** |
| Not a dataset (artifact or ledger entry) | **2** |
| Measured duplication | **≈ 72 %** |

This is the **eighth consecutive** corpus proposal in this estate to measure as
majority-owned (prior seven: 55–85 %). The cause is known and is not carelessness:
`PR-COVERAGE-BY-CONSTRUCTION-001` — the source document could not inspect this
workspace, so its boundary column is a hypothesis.

**What makes this one different:** the residue is not prose. It is a legally
load-bearing defect plus four executables. The prior seven produced doctrine; this one
produces a gate that currently returns a wrong answer about a real repo.

## D2A classification, dataset by dataset

| # | Proposed dataset | D2A | Existing owner | Basis |
|---|---|---|---|---|
| DS00 | Constitution & Institutional Map | **REJECT** | SDD-OS · `CLAUDE.md` · `governance/README.md` · `enforcement` KB | Constitution, precedence and truth hierarchy already sealed. A compendium index is a README, not a dataset |
| DS01 | Design Authority & Governance | **EXTEND** | `DESIGN_GOVERNANCE.md` + `DESIGN.md.template` + CDIO-06 | Authority model already shipped. Real gap: the template lacks 9 decisions (density, motion budget, expressivity, dependency tolerance, Base UI/Radix/React Aria, reduced-motion policy, RSC-vs-client, onboarding style, AI-interface policy) |
| DS02 | Legal, Licensing & White-Label Boundary | **HARDEN** | `lib/license_gate.js` + `vendor/NOTICE.md` | Owner exists and is **defective** (Reality Map §2). Highest-priority work in the whole proposal |
| DS03 | Upstream Resource Intelligence & Fork Strategy | **NOT A DATASET** | `crawl_os` (generic) | Per-upstream facts are *ledger rows*, not 20 Parts of prose. 5 Mirror-Ledger entries + 1 fork-strategy decision record |
| DS04 | Canonical Component Intelligence Model | **NEW** | — | Probed: no component manifest schema anywhere. Genuine primitive |
| DS05 | Component & Composition Knowledge Graph | **EXTEND** | `modules/graphify` (1,238 coordinates, typed edges, route compiler) | A second graph is the exact anti-pattern D2A exists to stop. Add node/edge *types*, not a graph |
| DS06 | CPP Design Registry & Distribution Fabric | **NEW** | — | No `registry.json` producer exists. Highest-value executable |
| DS07 | Design Intent & Requirement Compiler | **EXTEND** | `spec_gate` · KARIMO PRD parser · CDIO-02 | Intent→requirement compilation exists generically; the design-surface vocabulary does not |
| DS08 | Component Retrieval & Discovery | **EXTEND** | `tools/design_index.py` (`design_tools_fts`) | Add `design_components_fts` / `design_compositions_fts` / `design_failures_fts` beside the existing isolated table. Small, real |
| DS09 | Selection, Ranking & Abstention Engine | **NEW** | — | No component-level ranker or abstention path exists. Genuine |
| DS10 | Reuse / Adaptation / New-Build Decision | **MERGE → DS09** | D2A fabric (system level) | Same engine as DS09 at a different granularity. Two datasets describing one decision function is proliferation |
| DS11 | Identity Adaptation, Tokens & Theme Compiler | **EXTEND** | `DESIGN.md.template` · `visual-patterns/oklch-color-mix-tokens.md` · VQ-7 | Token model + token-consumption gate already exist |
| DS12 | Marketing Surface & Tailark Intelligence | **REJECT** | CDIO-04 (conversion intelligence) + registry namespace | Marketing doctrine owned; the blocks themselves are *registry content*, not a dataset |
| DS13 | AI Interface & Generative UI | **EXTEND** | Registry namespace + adapter | Real capability, wrong container. Belongs in DS06 as a namespace + a policy section, not 20 Parts |
| DS14 | Onboarding & Progressive Disclosure | **EXTEND** | Registry namespace + `DESIGN_GOVERNANCE` §6 | Same. The one genuinely new *rule* — "a tour must not compensate for bad UX" — is one governance clause |
| DS15 | Motion & Expressivity Gateway | **EXTEND** | `visual-patterns` KB (15 patterns) | The gateway *mechanism* is new and is where the Commons Clause bites; the motion taxonomy is largely owned |
| DS16 | Activation & Product-Line Fabric | **REJECT** | `capability_runtime` (applicability · contract · derivatives · retirement) | Activation, genealogy and retirement are its declared territory. Add the 4 modes as config |
| DS17 | CLI, MCP, Commands, Hooks & DX | **EXTEND** | `cpp-design.md` · `bootstrap-new-project.md` · `first-time-project.js` | All three exist. This is command evolution, not a dataset |
| DS18 | Verification & CDIO Evaluation Fabric | **REJECT** | `modules/cdio` + 7 KB datasets + `cdio-reviewer` + VQ-1..VQ-8 | The estate's most mature owner. Gap is component-scope checks (bundle, a11y, visual-regression) → EXTEND the scorer |
| DS19 | Security, Supply Chain & Dependency Governance | **EXTEND** | `secret_firewall` (HR-SECRET-001..007) + license gate | Secrets/redaction owned. SBOM, install-script policy, lockfile pinning are a real, small gap |
| DS20 | Upstream Evolution & Semantic Diff | **NEW** | partially `crawl_os` | No upstream-diff/licence-drift watcher exists. Genuine, small |
| DS21 | Reliability, Recovery & Operational Reality | **EXTEND** | `session_resilience` KB + recovery infra | Transactional *installation* is real but belongs to DS06 |
| DS22 | Institutional Learning & Baseline Promotion | **REJECT** | UKDL · CEPS global promotion · `capability_runtime` · FD-07 flywheel | Learning→promotion→retirement is fully owned. Add component-outcome writeback as a producer |
| DS23 | Evaluation Corpus & Adversarial Scenarios | **NEW** | `testing` KB (generic) | The ~40 named scenarios (no valid component · tour hiding bad UX · licence changed upstream · partial install) are genuine and are the proposal's best falsification instrument |
| DS24 | Reference Architectures & Blueprint | **NOT A DATASET** | — | This is the build plan itself |

## HR-NOVELTY-001 disposition

The novelty gate fires on this prompt (an institutional "fabric" / mega-corpus).
Of the thirteen questions, the four that decide the outcome:

- **New primitive?** — Yes, exactly one: the **component provenance + capability
  manifest** (DS04), and the registry that distributes artifacts keyed on it (DS06).
  Everything else composes existing primitives.
- **Extension insufficiency?** — No, for 18 of 25. Yes, for the 5 NEW rows.
- **Failure class prevented?** — Yes, and it is **new to this estate**: *redistributing
  code under a licence that forbids redistribution.* No existing owner prevents it —
  `license_gate.js` currently *causes* it by returning PERMISSIVE. This is the
  strongest novelty answer any of the last eight proposals has produced.
- **Retirement condition?** — Supplied by `capability_runtime/retirement.py` for the
  activation layer; the proposal as written supplies none for the registry.

**Classification: `EXTEND_EXISTING_OWNER` + `NEW_MODULE`.** Not
`GENUINELY_NEW_DATASET_FAMILY` at the 25-dataset scale.

## Degenerative feedback loops to block by construction

The proposal names these; they are recorded here as build-time invariants, not prose:

| Loop | Structural block |
|---|---|
| Popularity self-reinforcement (used-before ⇒ ranked-higher) | Prior-adoption may enter the ranker only as a **tiebreak**, never as a scored term. `feedback_constant_factors_rank_nothing`: a factor that does not vary with the query ranks nothing |
| Visual homogenisation ("shadcn slop") | VQ-6 logo-swap already blocks it at review; the ranker additionally penalises identity-neutral candidates |
| Motion inflation | Motion budget declared in `DESIGN.md`; the gateway refuses over-budget installs |
| Upstream lock-in | Dependency Exit Plan required per Mirror-Ledger row before first install |
| Registry gate satisfied by shrinking scope | Gate on **absolute** counts, never a ratio (`feedback_never_gate_on_a_ratio`) |

## Canonical sources of truth (post-audit)

| Concern | Canonical owner | Derived views |
|---|---|---|
| Visual identity | project `DESIGN.md` (from `DESIGN.md.template`) | theme files, token exports |
| Design quality verdict | `modules/cdio/scorer.py` | review reports, DQS |
| Activation & genealogy | `modules/capability_runtime` | activation manifests |
| Legal verdict | `lib/license_gate.js` (**after hardening**) | `vendor/NOTICE.md` rows, per-component obligations |
| Component facts | **DS04 manifest** (new) | registry.json, FTS rows, graph nodes |
| Upstream state | **Upstream Mirror Ledger** (extends `vendor/NOTICE.md`) | drift alerts, exit plans |
| Rules | UKDL + `rule_compiler` | compiled digests |

Everything else the proposal lists — matrices, indices, traceability reports — is a
**regenerable derived view** and must never overwrite primary evidence.
