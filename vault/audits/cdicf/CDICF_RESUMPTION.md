# CDICF — RESUMPTION

> Self-contained. A fresh session continues from this file with zero prior context.
> Scoped to `vault/audits/cdicf/` deliberately: the repo-root `RESUMPTION_FILE.md` is
> currently modified by a concurrent pane and is not this work's to own.

## 1. Identity, path, thesis

**CDICF — Claude Power Pack Design Intelligence & Component Fabric.**
Repo: `C:\Users\User\.claude\skills\claude-power-pack` (branch `main`).

Turn five upstream UI projects (shadcn/ui, Tailark Blocks, assistant-ui, Driver.js,
React Bits) into **legally governed, semantically described, automatically selectable**
capabilities. The valuable asset is not the visual fork — it is the machinery that
converts external code into capabilities a project can activate.

## 2. Exact state

**STOP #1 passed. Owner selected Option A (execution-first) + dual distribution
(internal AND public) with React Bits gateway-only in both paths.**

Audit verdict: **MAJORITY_OWNED ≈72%** — 25 proposed datasets resolve to 7 REJECT,
11 EXTEND, **5 NEW**, 2 not-datasets. Do not build the 25-dataset corpus.

| Work item | State |
|---|---|
| **A1** — harden `license_gate.js` + NOTICE schema | **SEALED** — commit `998d52c`, pushed, REMOTE_DELTA 0 0 |
| **A2** — Component Manifest schema + Mirror Ledger | NOT STARTED |
| **A3** — CPP Design Registry producer | NOT STARTED |
| **A4** — Selection + Abstention engine | NOT STARTED |
| **A5** — Evaluation corpus (~40 adversarial scenarios) | NOT STARTED |
| 6 extensions to existing owners | NOT STARTED |

**Coherence anchor:** `node --test tests/license_gate.test.js
tests/license_gate_restrictions.test.js` → **26/26 pass**. If that is not true, the
worktree has diverged from this file and nothing below can be trusted.

## 3. Active decisions

1. **React Bits never enters the CPP registry** — internal or public. Gateway/adapter
   that installs from upstream; zero copied component files; provenance never stripped.
2. **Build for the strictest case.** Public distribution assumed, so every artifact
   carries provenance from the first commit rather than being retrofitted.
3. **A1 gates everything.** No upstream is cloned until the legal gate is correct —
   otherwise the first absorption is performed by the component that was wrong. A1 is
   now sealed, so cloning is unblocked.
4. **Installers branch on `redistribution`, never on the SPDX id.** "MIT" is a true
   statement about React Bits and a useless one.
5. **No second graph, no second evaluation authority, no second activation authority.**
   `graphify`, `modules/cdio` and `capability_runtime` already own those.

## 4. Next 3 concrete actions

1. **A2** — write the Component Manifest schema (`vault/schemas/component_manifest.json`)
   from the source document's field list, then pin the 5 upstream commits and fill in
   the `Snapshot` / `Fingerprint` fields that currently read NOT PINNED in
   `vendor/NOTICE.md`.
2. Resolve the two blocking legal unknowns: **Tailark's copyright holder** and whether
   **`nilbuild/driver.js`** is canonical or a rename-redirect of `kamranahmedse/driver.js`.
   Neither can be attributed until resolved.
3. **A3** — `registry.json` emitter with commit-pinned deterministic install + rollback.

## 5. Start instruction

Read `CPP_DESIGN_OVERLAP_MAP.md` for what must NOT be rebuilt, then
`vault/plans/cdicf-corpus-2026-08-06.md` for the option-A work breakdown. Run the
coherence anchor first. Begin at action 1.
