---
title: CDICF — Claude Power Pack Design Intelligence & Component Fabric
date: 2026-08-06
covers: [cdicf, design-intelligence, component-fabric, license-gate, design-registry, upstream-absorption, shadcn, tailark, assistant-ui, driver-js, react-bits]
status: STOP #1 — blocking. No dataset or module content is written until the Owner selects an option.
phase_0: vault/audits/cdicf/CPP_DESIGN_REALITY_MAP.md
phase_2: vault/audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md
verdict: MAJORITY_OWNED (≈72%) — apply D2A. Do not build the 25-dataset corpus.
---

# CDICF — STOP #1 Plan

## Phase 1 — Upstream legal verdicts (licence text inspected this session)

Every row below rests on the **licence file actually fetched**, not on a README, a
badge alone, or the source document's assertion. Untrusted-data doctrine applied: no
fetched content was treated as instruction.

| Upstream | Licence file | Verdict | Holder | Confidence | Integration mode |
|---|---|---|---|---|---|
| `shadcn-ui/ui` | `LICENSE.md` | **MIT**, no appended clause | shadcn, 2023 | **VERIFIED** (full text) | **Fork canónico** — registry protocol + primitives |
| `assistant-ui/assistant-ui` | `LICENSE` | **MIT**, no appended clause | **AgentbaseAI Inc.**, 2025 | **VERIFIED** (full text) | **Fork especializado** — AI-interface namespace |
| `tailark/blocks` | `LICENCE.md` (British spelling) | **MIT**, no appended clause | not stated in fetched content | **OBSERVED** — holder unresolved | **Fork canónico** — marketing namespace |
| `nilbuild/driver.js` | `LICENSE` | **MIT** | Kamran Ahmed | **OBSERVED** | **Fork especializado** — onboarding namespace |
| `DavidHDev/react-bits` | **`LICENSE.md`** (plain `LICENSE` 404s) | **MIT + Commons Clause Restriction v1.0** | **David Haz, 2026** | **VERIFIED** (full text + GitHub badge string "MIT + Commons Clause") | **Gateway / adapter upstream — NO redistribution** |

### Material findings

1. **React Bits confirms the proposal's decisive claim.** The Commons Clause forbids
   selling, sublicensing or redistributing the components "whether alone, in a bundle,
   or as a ported version." Placing them in a CPP-distributed registry **is**
   redistribution as a bundle. Renaming or porting is explicitly covered. Permitted:
   installing from the original registry into a consuming application, applying tokens
   in the final application, indexing and recommending. Prohibited: shipping them in
   the CPP registry, stripping provenance.
2. **`LICENSE` 404s; `LICENSE.md` carries the terms.** Any absorption tool that probes
   only `LICENSE` reports UNKNOWN on the single most restricted upstream in the set.
   `license_gate.js` does check `LICENSE.md` — but then misclassifies it (Reality Map §2).
3. **Two holder fields are unresolved** — Tailark's copyright holder, and confirmation
   that `nilbuild/driver.js` is canonical rather than a rename-redirect. Both are
   **blocking for a NOTICE row**, not for this decision. Resolve at commit-pin time.
4. **Licence facts are commit-scoped.** React Bits' text is dated 2026 — its terms have
   moved before. Every ledger row pins a commit; a licence change at a later commit is
   a **material invalidator** of every artifact derived from it.
5. No legal advice is asserted here. These are inspected-text readings with stated
   confidence. Redistribution decisions on the React Bits boundary warrant human
   review before any public registry ships.

## Options for the Owner

### Option A — Execution-first (RECOMMENDED)

Build the irreducible remainder as **running code**, not prose. 5 work items:

| # | Item | Type | Why it is real |
|---|---|---|---|
| **A1** | Harden `license_gate.js`: composite-licence detection (scan the **whole** file, not `slice(0,4000)`; collect **all** signals, not first-hit), new tier `SOURCE_AVAILABLE_RESTRICTED`, explicit `redistribution: allowed\|prohibited` field, drift detection between snapshots. Extend `vendor/NOTICE.md` schema with `redistribution` + `commit` + `exit_plan`. | HARDEN | The gate returns a **wrong, confident, legally load-bearing verdict** on React Bits today |
| **A2** | Component Manifest schema (DS04) + Upstream Mirror Ledger rows for the 5 upstreams | NEW | No component manifest exists anywhere in 78 modules |
| **A3** | CPP Design Registry producer (DS06): `registry.json` emitter, namespaces, commit-pinned deterministic install, rollback | NEW | No `registry.json` producer exists |
| **A4** | Selection + Abstention engine (DS09 ∪ DS10): hard filters → soft scoring → explanation → **abstention path** | NEW | No component ranker exists; abstention is a first-class outcome |
| **A5** | Evaluation corpus (DS23): the ~40 adversarial scenarios as executable cases | NEW | The only instrument that can falsify A1–A4 |

Plus 6 extensions to existing owners: `DESIGN.md.template` (+9 decisions),
`design_index.py` (+3 FTS tables), `graphify` (+component node/edge types),
`capability_runtime` (+4 activation modes), `modules/cdio` (+component-scope checks),
`DESIGN_GOVERNANCE.md` (+reuse-first, +provenance-mandatory, +tour-as-last-resort).

**Not built:** a second knowledge graph, a second evaluation authority, a second
activation authority, a second institutional-learning loop, 25 datasets of prose.

**Gate A1 first.** Nothing touches an upstream until the legal gate is correct —
otherwise the first absorption is performed by the component that is currently wrong.

### Option B — Legal spine only

A1 alone, sealed and tested, then re-decide. Smallest defensible unit; leaves the
registry unbuilt.

### Option C — Full 25-dataset corpus as specified

Rejected by the audit but available on explicit Owner override. Expect ≈72% of the
output to restate owners that already exist at equal or greater maturity, and to
create the second-source-of-truth condition D2A exists to prevent.

### Option D — Reduced corpus: 5 NEW datasets as prose, no executables

Consistent with the letter of the request, but FIOS's own STOP #1 set the precedent
against prose describing engines that do not run — and the residue here is
specifically executable.

## Done-gate for whichever option is selected

Production Reality Gates (from the source, retained verbatim in intent):
no restricted component redistributed · every artifact carries provenance · notices
correct · installation reproducible and commit-pinned · rollback and semantic recovery
exist · the selector can explain its decision and can abstain · no generic-by-default
aesthetics · `DESIGN.md` preserved · accessibility and reduced-motion honoured ·
bundle within budget · one real installable vertical slice · upstream update simulable
· licence change invalidates dependent artifacts · interrupted install recoverable ·
headless operable · activation undoable. A README, a mock, a diagram or a screenshot
does **not** satisfy any of these.

Additional gates from this estate's standing lessons:
- **Liveness** (`python modules/liveness/reachability.py`): every new module is wired,
  declared, or deleted. A shipped-but-unreachable registry is the exact failure the
  Liveness Standard exists to stop.
- **Absolute counts, never ratios** (`feedback_never_gate_on_a_ratio`).
- **Discovered denominators, never curated** (`PR-COVERAGE-BY-CONSTRUCTION-001`).

## Blocking condition

No dataset content, no module code, no upstream clone until the Owner selects
A / B / C / D. Phase 3 (Compendium Skeleton) does not begin before that selection.

## Owner actions outside this repository

1. Confirm intended distribution model: **internal-only** (PP consumed by your own
   projects) vs **public registry**. The React Bits boundary and the shadcn/Tailark
   NOTICE obligations change materially between the two.
2. Resolve the two unverified holder fields (Tailark copyright holder; `nilbuild`
   canonicality) before the first NOTICE row is written.
