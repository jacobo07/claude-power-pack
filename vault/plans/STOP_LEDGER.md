# STOP #1 Disposition Ledger

**Derived — do not hand-edit.** Regenerate with `python -m modules.owner_queue.stop_ledger --write`.

The plan files are sealed records of what was believed when, and are never rewritten to match a later verdict. This ledger carries the transition their `status:` field has no producer for.

**18 STOP-bearing plans** — OPEN 8 · CONTRADICTED 6 · RESOLVED 4 · UNKNOWN 0

| plan | family | disposition | status as written | witness |
|---|---|---|---|---|
| `claude-md-compaction-2026-07-26.md` | claude-md-compaction | **OPEN** | STOP #1 delivered inline; awaiting Owner approval before execution | - |
| `e-passes-audit-2026-07-29.md` | e-passes | **OPEN** | STOP — verdicts delivered inline. No E-pass Part authored. No E-pass a | - |
| `gap-discovery-2026-07-30.md` | gap-discovery | **OPEN** | STOP #1 — presented inline, awaiting Owner approval before any constru | - |
| `iig-compendium-2026-07-30.md` | iig | **OPEN** | STOP #1 — presented inline, awaiting Owner approval before any constru | - |
| `re-baseline-compendium-2026-07-26.md` | re-baseline | **OPEN** | STOP-1 (Phase 0 complete; awaiting Owner approval of the revised archi | - |
| `sdd-os-activation-2026-07-26.md` | sdd-os-activation | **OPEN** | STOP #1 delivered inline; awaiting Owner approval before any execution | - |
| `uceimr-corpus-2026-08-04.md` | uceimr | **OPEN** | STOP #1 — BLOCKING, presented inline, no dataset written | - |
| `uceimr-expansion-2026-08-04.md` | uceimr-expansion | **OPEN** | STOP #2 — BLOCKING, presented inline, no dataset written | - |
| `apir-corpus-2026-08-03.md` | apir | **CONTRADICTED** | STOP #1 — BLOCKING, awaiting Owner selection of A / B / C / D | vault/plans/seip-corpus-2026-08-04.md: \| 10 \| CPP-APIR \| ≈80 % owned \| corpus refused; `capability_runtime |
| `crpf-2026-07-27.md` | crpf | **CONTRADICTED** | STOP #1 (verdicts delivered inline to the Owner; no Part authored) | vault/plans/crpf-overlap-audit-2026-07-27.md: Charter impact: CRPF is struck as a NEW family; construction ord |
| `efaif-corpus-2026-08-04.md` | efaif | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/seip-corpus-2026-08-04.md: \| G1 Benchmark Genome \| REJECT \| SQI `BenchmarkScenario` + 4 sealed  |
| `igef-2026-07-29.md` | igef | **CONTRADICTED** | STOP #1 — verdicts delivered inline. No IGEF Part authored. No IGEF ar | vault/plans/e-passes-audit-2026-07-29.md: precedent: CRPF struck (vault/plans/crpf-2026-07-27.md) · IGEF struc |
| `seip-corpus-2026-08-04.md` | seip | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/uceimr-corpus-2026-08-04.md: \| 13 \| Evaluation & Benchmarks \| DO-NOT-BUILD \| SQI: 4 sealed dat |
| `ukr-runtime-2026-07-30.md` | ukr | **CONTRADICTED** | STOP #1 — presented inline, awaiting Owner approval before any constru | vault/plans/seip-corpus-2026-08-04.md: \| Universal Knowledge Runtime \| **0** \| Does not exist. `ukr-runtime |
| `ccfl-pdpf-corpus-2026-07-31.md` | ccfl-pdpf | **RESOLVED** | STOP #1 CLOSED — verdict MAJORITY_OWNED. Awaiting Owner selection befo | - |
| `pane-map-versioning-2026-07-06.md` | pane-map-versioning | **RESOLVED** | **SHIPPED 2026-07-06** (SCS C80). ULTRA-PLAN, Reality Scan STOP #1 app | - |
| `process-hibernation-fase-a.md` | process-hibernation-fase-a | **RESOLVED** | **built + tested 2026-07-03** \| Owner-approved scope (STOP #1): Shell | - |
| `usirc-corpus-2026-07-31.md` | usirc | **RESOLVED** | STOP #1 RESOLVED — Owner selected Option B (build the residue as one m | - |

## Reading

- **OPEN** — open-shaped status and no artifact anywhere witnesses an outcome. Genuinely outstanding; these are the ones to act on.
- **CONTRADICTED** — the plan still reads as awaiting, but another artifact states what became of it. The work is done; only the record disagrees.
- **RESOLVED** — the plan's own status states its outcome.

A disposition is never asserted, only witnessed, and a plan may not witness itself. Absent evidence the verdict is OPEN — this producer can create work, never silently close it. CONTRADICTED means *a contradiction exists*, never *this is resolved*; verify the witness before acting on it.

### Known limits of the witness test

**False positives — precedent citation.** An audit that cites another family's verdict as prior art (an `| EFAIF | DO-NOT-BUILD |` row inside a base-rate table) produces a line carrying both the family token and a disposition verb, indistinguishable by line-level matching from a statement about that family's own STOP. This is exactly why the verdict is CONTRADICTED rather than RESOLVED: the tool surfaces the disagreement and a human adjudicates it.

**False negatives — family-token drift.** A disposition recorded under a name other than the filename is missed. `e-passes-audit` is the live instance: it was struck on 2026-07-29, but the closure report records that outcome as `E1-E5`, so no line carries the token `e-passes` and the plan reads OPEN here. Misses fall toward OPEN, which is the safe direction — this producer over-reports outstanding work, never under-reports it.
