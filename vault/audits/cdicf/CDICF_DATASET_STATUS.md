# CDICF — DATASET / WORK-ITEM STATUS

Single status surface for the 25 proposed datasets and the Option-A work items.
`CPP_DESIGN_OVERLAP_MAP.md` holds the reasoning; this holds the state.

## Option-A work items (what is actually being built)

| Item | Type | State | Evidence |
|---|---|---|---|
| **A1** Hardened license gate + NOTICE schema | HARDEN | **SEALED** | `998d52c` pushed; 26/26 tests; real react-bits input → `SOURCE_AVAILABLE_RESTRICTED` / `prohibited`, exit 5 |
| **A2** Component Manifest + Mirror Ledger | NEW | NOT STARTED | — |
| **A3** Registry producer + redistribution guard | NEW | NOT STARTED | — |
| **A4** Selection + Abstention engine | NEW | NOT STARTED | — |
| **A5** Evaluation corpus (~40 scenarios) | NEW | NOT STARTED | — |
| E1 `DESIGN.md.template` +9 decisions | EXTEND | NOT STARTED | — |
| E2 `design_index.py` +3 FTS tables | EXTEND | NOT STARTED | — |
| E3 `graphify` +component node/edge types | EXTEND | NOT STARTED | — |
| E4 `capability_runtime` +4 activation modes | EXTEND | NOT STARTED | — |
| E5 `modules/cdio` +component-scope checks | EXTEND | NOT STARTED | — |
| E6 `DESIGN_GOVERNANCE.md` +3 clauses | EXTEND | NOT STARTED | — |

**Progress: 1 of 11 sealed.** Absolute count, deliberately — a percentage would improve
by deleting a row.

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
| shadcn/ui | PERMISSIVE (MIT © 2023 shadcn) | allowed | VERIFIED | commit + fingerprint not pinned |
| assistant-ui | PERMISSIVE (MIT © 2025 AgentbaseAI Inc.) | allowed | VERIFIED | commit + fingerprint not pinned |
| Tailark Blocks | PERMISSIVE (MIT, `LICENCE.md`) | allowed | **OBSERVED** | **copyright holder unresolved** |
| driver.js | PERMISSIVE (MIT, Kamran Ahmed) | allowed | **OBSERVED** | **canonicality unresolved** |
| React Bits | **SOURCE_AVAILABLE_RESTRICTED** | **prohibited** | VERIFIED | fingerprint is of fetched text, not a pinned clone |

## Production Reality Gates — current standing

| Gate | State |
|---|---|
| No restricted component redistributed | **ENFORCED** by `--strict` (exit 5); becomes structural at A3 action 8 |
| Every artifact carries provenance | PENDING A2 |
| Installation reproducible, commit-pinned | PENDING A3 |
| Rollback + semantic recovery | PENDING A3 |
| Selector explains and can abstain | PENDING A4 |
| Licence change invalidates dependents | **ENFORCED** by `--expect` (exit 4) |
| One real installable vertical slice | PENDING A3 |
| Headless operable | **HELD** — gate is CLI, JSON, exit-code driven |

2 of 8 enforced. No gate is claimed on the strength of a README or a diagram.
