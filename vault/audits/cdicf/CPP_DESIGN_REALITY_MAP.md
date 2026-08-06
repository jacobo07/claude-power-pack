---
title: CDICF — Phase 0 Reality Map (PP repo vs. the proposal's asserted inventory)
date: 2026-08-06
source: "Dataset Claude Power Pack Design Intelligence & Component Fabric 1.txt" (19,357 B, read to EOF)
method: discovered denominator — filesystem enumeration this session, not recall
status: BLOCKING artifact for STOP #1
---

# Phase 0 — Reality Map

## Method

Every row below was produced by opening a file or enumerating a directory **this
session**. Nothing is carried from memory. Per `PR-COVERAGE-BY-CONSTRUCTION-001`, a
boundary column filled from recall measures memory, not reality.

**Discovered denominator:** 78 modules · 67 commands · 39 hooks · 12 agents ·
26 knowledge families · 1,238 graph coordinates (+478 cross-repo).

## 1. The proposal's asserted inventory, probed

The source document names nine PP artifacts. Eight exist; one does not exist the way
the document implies.

| Asserted artifact | Reality | State | Evidence |
|---|---|---|---|
| `lib/license_gate.js` | Exists, 9,551 B / 235 lines | **VERIFIED** | Read in full |
| `tools/design_index.py` | Exists, 15,997 B | **VERIFIED** | Stat + `/cpp-design` contract |
| `commands/cpp-design.md` | Exists, 1,771 B | **VERIFIED** | Read in full |
| `commands/bootstrap-new-project.md` | Exists, 7,884 B | **OBSERVED** | Stat only |
| `hooks/first-time-project.js` | Exists, 2,277 B | **OBSERVED** | Stat only |
| `governance/DESIGN_GOVERNANCE.md` | Exists, 8,779 B | **VERIFIED** | Read in full |
| `vendor/NOTICE.md` | Exists, 5,078 B, 7 entries | **VERIFIED** | Read in full |
| CDIO | Exists: `modules/cdio` + 7 KB datasets (~97 KB) | **VERIFIED** | Directory listing |
| Capability Runtime | Exists: `modules/capability_runtime`, 6 files (~74 KB) | **VERIFIED** | Directory listing |
| `DESIGN.md` **at PP repo root** | **Does not exist** | **REJECTED** | Recursive filename probe returned MISSING |

### The DESIGN.md correction

The proposal reads as though `DESIGN.md` is a PP-repo artifact to be extended. It is
not. `DESIGN.md` is a **per-consuming-project** artifact generated from
`modules/design-md/DESIGN.md.template` (7,397 B) and governed by
`DESIGN_GOVERNANCE.md` §1, which states it lives "at the repo root" of the project
being built. PP ships the template, the family picker, the brand→DESIGN.md workflow,
the live-site audit and a 3-designer-debate workflow — not a DESIGN.md of its own.

This does not weaken the proposal's architecture; it **confirms** it. "DESIGN.md as
authority" is already the shipped design. It changes where the extension work lands:
in the template and the governance file, not in a root document that must first be
created.

## 2. Verified defect — `license_gate.js` misclassifies MIT + Commons Clause

This is the proposal's single most consequential technical claim. It is **correct**,
and it is worse than the document states.

**Snippet** — `lib/license_gate.js:69-93`:

```js
function detectFromText(text) {
  const head = text.slice(0, 4000);          // L71 — window
  ...
  const tests = [
    ...
    [/Permission is hereby granted, free of charge, to any person obtaining a copy/i, 'MIT'],  // L85
  ];
  for (const [rx, id] of tests) {
    if (rx.test(head)) return { spdx: id, source: 'heuristic' };   // L91-93 — first hit wins, returns
  }
```

**Scenario** — run the gate against a React Bits clone. `LICENSE.md` is in
`LICENSE_FILES` (L37), so it is read. Its text opens with the standard MIT grant, so
L85 matches, L92 returns immediately, and the appended **Commons Clause Restriction
v1.0** is never examined. `classify()` sets `canonical: 'MIT'`, `tier: 'PERMISSIVE'`,
and emits the obligation string *"Preserve copyright + license text on
redistribution. Otherwise unrestricted."* — on a component set whose license forbids
redistribution "alone, in a bundle, or as a ported version."

**Why existing guards fail:**
1. `TIER` (L41-45) has no restricted category. Even a correct detection has no tier to
   land in — the vocabulary cannot express the outcome (`feedback_zero_cannot_fall`:
   a gate is bounded by its vocabulary).
2. The proprietary-smell check (L95-99) is unreachable — it sits after the loop that
   already returned.
3. The 4,000-char window (L71) may not even contain the appended clause.
4. The module is documented "Advisory only — does not block execution" (L7).

**Severity: CRITICAL.** Not because the code crashes, but because it returns a
confident, wrong, legally load-bearing verdict on a repo this very proposal intends to
consume. `vendor/NOTICE.md` inherits the same vocabulary — its `Gate verdict` field
offers PERMISSIVE / WEAK_COPYLEFT / STRONG_COPYLEFT / PROPRIETARY / UNKNOWN and one
ad-hoc `UPSTREAM_LICENSE`. There is no value in that set that means
"usable in-application, prohibited to redistribute."

## 3. Owners discovered in the design/UI territory

| Owner | Path | Territory held | Maturity |
|---|---|---|---|
| Design constitution | `governance/DESIGN_GOVERNANCE.md` | Authority, VQ-1..VQ-8, colour discipline, material physics, logo-swap identity, 6 prohibited anti-patterns, render-not-curl | **High** — imperative, incident-cited |
| DESIGN.md system | `modules/design-md/` | Template, family picker, brand→DESIGN.md, live-site audit, remix, debate | **High** |
| CDIO | `modules/cdio/` + `vault/knowledge_base/cdio/` (7 datasets) | Design-quality scoring, 6-lens review pipeline, aesthetic families, visual/UX/trust/conversion intelligence | **High** — ~97 KB, mechanical scorer |
| Capability Runtime | `modules/capability_runtime/` | applicability · contract · corpus_adapter · derivatives · retirement | **High** — ~74 KB |
| Visual patterns | `vault/knowledge_base/visual-patterns/` (15 patterns) | Glassmorphism, gradient/metallic/holographic text, grain, scroll-driven reveal, OKLCH token mixing | **Medium-High** |
| Pattern retrieval | `tools/design_index.py` + `/cpp-design` | FTS5 BM25 over isolated `design_tools_fts`, 10 systems × 15 patterns | **Medium** — patterns, not components |
| Legal | `lib/license_gate.js` + `vendor/NOTICE.md` | SPDX tiering + attribution ledger | **Low** — defective (§2) |
| Project activation | `commands/bootstrap-new-project.md`, `hooks/first-time-project.js` | New-project bootstrap, first-time detection | **Medium** |
| Creative | `modules/ccf/` | Brief→spec→generate→select→package brand pipeline, trademark scan | **High** |
| Knowledge graph | `modules/graphify/` | 1,238 coordinates, typed edges, route compiler | **High** |
| Upstream intelligence | `vault/knowledge_base/crawl_os/` (5 datasets, ~117k words) | Web/repo acquisition intelligence | **High** |
| Governance spine | SDD-OS, `hard_rules`, `rule_compiler`, `spec_gate`, `liveness` | Spec-first, 156 compiled rules, novelty gate, reachability | **High** |

## 4. Claims the proposal makes that this scan did **not** confirm

| Claim | State | Note |
|---|---|---|
| `design_index.py` holds "only 15 unique snippets repeated across 10 systems" | **UNKNOWN** | Not decisively measured; non-decisive for STOP #1 either way. The retrieval-layer verdict (EXTEND) does not depend on it |
| "The audited ZIP is ~52 MB / 2,000+ files" | **UNKNOWN** | Refers to an artifact outside this workspace; not re-measurable here |
| Absorbing 5 upstreams would cause dependency conflicts | **INFERRED** | Reasonable, unmeasured |

## 5. Contamination check

Swept for CommonWealth Ops concepts (brandshipping, ecommerce, operators, PCIOS,
AEIS, ACMF, Profit Recovery, revenue, fulfillment, commercial missions). **Zero
present** in the source document and zero introduced by this audit. CW Ops appears in
this estate only as a depth benchmark, which is the authorized use.
