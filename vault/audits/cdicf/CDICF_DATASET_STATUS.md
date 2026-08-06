# CDICF — DATASET / WORK-ITEM STATUS

Single status surface for the 25 proposed datasets and the Option-A work items.
`CPP_DESIGN_OVERLAP_MAP.md` holds the reasoning; this holds the state.

## Option-A work items (what is actually being built)

| Item | Type | State | Evidence |
|---|---|---|---|
| **A1** Hardened license gate + NOTICE schema | HARDEN | **SEALED** | `998d52c` + `e5aff74` (filename discovery by pattern); 31/31 tests; real react-bits input → `SOURCE_AVAILABLE_RESTRICTED` / `prohibited`, exit 5 |
| **A1b** Legal debt closed — holders, canonicality, commit pins | HARDEN | **SEALED** | `1748670`; all 5 commits pinned; Tailark holder = Irung; driver.js confirmed a rename redirect |
| **A2** Component Manifest schema + validator | NEW | **SEALED** | `modules/cdicf/`; 21/21 tests; CLI verified both directions; 6 invariants enforced, INV-02 blocks forking a prohibited component |
| **A1c** License fingerprints measured from pinned commits | HARDEN | **SEALED** | All 5 measured from raw blobs; D-008 proved — the superseded react-bits value fires a false `--expect` drift on an unchanged licence |
| **A2b** Mirror Ledger emitted from the gate rather than hand-written | NEW | NOT STARTED | — |
| **A3** Registry producer + redistribution guard | NEW | **SEALED** | `modules/cdicf/registry_emitter.js`; 16/16 tests; PROHIBITED refused at exit 5 with zero bytes written; posture derived from the tier, never read from the manifest |
| **A3b** Transactional installer — atomic, idempotent, recoverable, reversible | NEW | **SEALED** | `modules/cdicf/installer.js`; 24/24 tests; a real `exit 137` inside the rename sweep recovers to the exact pre-state; licence re-derived at install as defence in depth |
| **A4** Selection + Abstention engine | NEW | NOT STARTED | — |
| **A5** Evaluation corpus (~40 scenarios) | NEW | NOT STARTED | — |
| E1 `DESIGN.md.template` +9 decisions | EXTEND | NOT STARTED | — |
| E2 `design_index.py` +3 FTS tables | EXTEND | NOT STARTED | — |
| E3 `graphify` +component node/edge types | EXTEND | NOT STARTED | — |
| E4 `capability_runtime` +4 activation modes | EXTEND | NOT STARTED | — |
| E5 `modules/cdio` +component-scope checks | EXTEND | NOT STARTED | — |
| E6 `DESIGN_GOVERNANCE.md` +3 clauses | EXTEND | NOT STARTED | — |

**Progress: 6 of 15 sealed.** Absolute count, deliberately — a percentage would improve
by deleting a row. The denominator has grown three times (11 → 13 → 14 → 15) as A1b, A1c,
A2b and A3b were split out once the work turned out to be real. A denominator that only
ever shrinks is the ratio failure wearing a different hat.

**Ratified 2026-08-06 (D-011):** `--reference-only` stands. Redistribution is the movement
of code; a URL is not code. The Motion Gateway namespace is in scope with the pointer path
as its emission mode, and A3b installs such an entry as a record with zero component bytes
on disk (`V-INST-14`).

## The 25 proposed datasets — disposition

| Verdict | Count | Datasets |
|---|---|---|
| **REJECT** — owned at equal or greater maturity | 7 | DS00, DS05, DS12, DS16, DS18, DS22, DS10 (merged into DS09) |
| **EXTEND / HARDEN** an existing owner | 11 | DS01, DS02→A1, DS07, DS08, DS11, DS13, DS14, DS15, DS17, DS19, DS21 |
| **NEW** — genuine unowned residue | 5 | DS04→A2, DS06→A3, DS09→A4, DS20, DS23→A5 |
| **NOT A DATASET** | 2 | DS03 (ledger rows), DS24 (the build plan itself) |

Note DS20 (upstream semantic diff / license drift) is classified NEW but is **partially
delivered**: `--expect <fingerprint>` in A1 detects license drift today. The remaining
residue is API/component/visual diff.

## Legal status per upstream

| Upstream | Verdict | Redistribution | Confidence | Blocking gap |
|---|---|---|---|---|
| shadcn/ui | PERMISSIVE (MIT © 2023 shadcn) | allowed | VERIFIED | fingerprint PENDING_CLONE |
| assistant-ui | PERMISSIVE (MIT © 2025 AgentbaseAI Inc.) | allowed | VERIFIED | fingerprint PENDING_CLONE |
| Tailark Blocks | PERMISSIVE (MIT © 2025 **Irung**, `LICENCE.md`) | allowed | **VERIFIED** | fingerprint PENDING_CLONE |
| driver.js | PERMISSIVE (MIT © **Kamran Ahmed**, no year, file `license`) | allowed | **VERIFIED** | fingerprint PENDING_CLONE |
| React Bits | **SOURCE_AVAILABLE_RESTRICTED** | **prohibited** | VERIFIED | fingerprint is of fetched text, not a pinned clone |

All five commits are **pinned** (GitHub API, 2026-08-06). Fingerprints are withheld by
decision D-008, not by omission: the license bodies reaching this session pass through a
markdown conversion that can reflow whitespace, so a hash of them would not match the
repository bytes and would false-positive on the first real drift check.

Filename traps encountered, all now handled by `findLicenseFiles`:
`react-bits` → `LICENSE.md` (plain `LICENSE` 404s) · `tailark/blocks` → `LICENCE.md`
(British spelling) · `driver.js` → `license` (lowercase, branch `master`).

## Production Reality Gates — current standing

| Gate | State |
|---|---|
| No restricted component redistributed | **ENFORCED** — structurally, twice: the emitter refuses to emit (exit 5, `V-EMIT-01`) and the installer refuses to land it (exit 5, `V-INST-13`) |
| Every artifact carries provenance | **ENFORCED** — required by the schema, and the installer refuses an entry whose manifest carries no `provenance.license_tier` |
| Installation reproducible, commit-pinned | **ENFORCED** — per-artifact sha256 + a recomputed roll-up; a tampered artifact is refused by name (`V-INST-15`) |
| Rollback + semantic recovery | **ENFORCED** — `rollback` (`V-INST-08`) and `recover` after a real `exit 137` (`V-INST-03`/`V-INST-04`) |
| Selector explains and can abstain | PENDING A4 |
| Licence change invalidates dependents | **ENFORCED** by `--expect` (exit 4) |
| One real installable vertical slice | **HELD** — manifest → emit → install → verify → rollback runs end to end on shadcn/ui Button (`V-INST-22`, through the CLI) |
| Headless operable | **HELD** — every stage is CLI, JSON, exit-code driven |

**7 of 8.** Only the selector remains, and it is A4. No gate is claimed on the strength of
a README or a diagram; each row above names the test that observes it.

Two of these moved for a reason worth keeping. *No restricted component redistributed* is
now enforced at **two independent points** — an entry can reach a project by a path that
never went through the emitter, and a guard that trusts an upstream guard is one guard.
*One real installable vertical slice* is HELD rather than ENFORCED because it is a
demonstration, not a constraint: it proves the pipeline runs, it does not prevent anything.
