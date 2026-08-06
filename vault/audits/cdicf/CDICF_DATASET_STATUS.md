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
| **A4** Selection + Abstention engine | NEW | **SEALED** | `modules/cdicf/selector.js`; 25/25 tests; relevance is a hard filter not a weighted term; six abstention codes each with a remedy; never installs (asserted structurally) |
| **A5** Adversarial evaluation corpus | NEW | **SEALED** | `tests/a5_adversarial.test.js`; 41 scenarios + a meta-gate; **6 failed on first run → 4 defects fixed** (D-016); hermetic across 3 runs |
| E1 `DESIGN.md.template` +9 decisions | EXTEND | **SEALED** | `e9d5170`; Component Provenance section — the nine decisions **are** the selector's context object. `V-DESIGN-TEMPLATE-CLEAN` still APPROVE score=100 family=F3 |
| E2 `design_index.py` + component FTS5 sidecar | EXTEND | **SEALED** | own DB file `CDICF-COMPONENT-INDEX.db`; builds **refuse** a database holding `turns*`/`design_tools*` (exit 3); provenance absent from the schema, not merely unindexed; empty results split into `NO_INDEX`/`INDEX_EMPTY`/`NO_MATCH`; `selector.js --candidates-from` consumes it. 15/15, hermetic 3× |
| E3 `graphify` +component node/edge types | EXTEND | NOT STARTED | — |
| E4 `capability_runtime` +4 activation modes | EXTEND | NOT STARTED | — |
| E5 `modules/cdio` +component-scope checks | EXTEND | NOT STARTED | — |
| E6 `DESIGN_GOVERNANCE.md` +3 clauses | EXTEND | **SEALED** | `63ccfff`; Section 8 — reuse-first, provenance-mandatory, tour-as-last-resort, each backed by an exit code |

**Progress: 11 of 15 sealed.** Absolute count, deliberately — a percentage would improve
by deleting a row. The denominator has grown three times (11 → 13 → 14 → 15) as A1b, A1c,
A2b and A3b were split out once the work turned out to be real. A denominator that only
ever shrinks is the ratio failure wearing a different hat.

**The executable spine is complete and adversarially tested.** manifest → emit → install →
select runs end to end on the real catalogue, with **174 gates** behind it — 159 JS
(`node --test "tests/**/*.test.js"`) plus 15 Python for the E2 sidecar
(`python tools/test_cdicf_index.py`). A5 found four defects the other 117 could not see
(D-016). What remains is A2b (ledger rows emitted rather than typed) and E3–E5.

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
| Selector explains and can abstain | **ENFORCED** — every ranked position explains itself in impact order (`V-SEL-13`), and abstention is an explicit code + remedy, never an empty array (`V-SEL-03`) |
| Licence change invalidates dependents | **ENFORCED** by `--expect` (exit 4) |
| One real installable vertical slice | **HELD** — manifest → emit → install → verify → rollback runs end to end on shadcn/ui Button (`V-INST-22`, through the CLI) |
| Headless operable | **HELD** — every stage is CLI, JSON, exit-code driven |

**8 of 8.** No gate is claimed on the strength of a README or a diagram; each row above
names the test that observes it.

That the last one closed is worth stating carefully: these are the gates this build set
for itself, and clearing them is not the same as the fabric being finished. A5 exists
precisely because a suite written by the same hand that wrote the code is the weakest kind
of evidence — and A4's own experience is the argument, since 23 of 23 of its tests passed
before real input found two defects.

Two of these moved for a reason worth keeping. *No restricted component redistributed* is
now enforced at **two independent points** — an entry can reach a project by a path that
never went through the emitter, and a guard that trusts an upstream guard is one guard.
*One real installable vertical slice* is HELD rather than ENFORCED because it is a
demonstration, not a constraint: it proves the pipeline runs, it does not prevent anything.
