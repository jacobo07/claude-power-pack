# STOP Disposition Ledger

**Derived — do not hand-edit.** Regenerate with `python -m modules.owner_queue.stop_ledger --write`.

The plan files are sealed records of what was believed when, and are never rewritten to match a later verdict. This ledger carries the transition their `status:` field has no producer for.

**23 STOP-bearing plans** — OPEN 8 · CONTRADICTED 11 · RESOLVED 4 · UNKNOWN 0

By checkpoint: STOP 1 · STOP #1 19 · STOP #2 3. A STOP #2 is a different question from a STOP #1 and is counted separately rather than folded into it.

| plan | checkpoint | family | disposition | status as written | witness |
|---|---|---|---|---|---|
| `claude-md-compaction-2026-07-26.md` | STOP #1 | claude-md-compaction | **OPEN** | STOP #1 delivered inline; awaiting Owner approval before execution | - |
| `efaif-expansion-2026-08-06.md` | STOP #2 | efaif-expansion | **OPEN** | STOP #2 — BLOCKING, presented inline, no dataset written | - |
| `gap-discovery-2026-07-30.md` | STOP #1 | gap-discovery | **OPEN** | STOP #1 — presented inline, awaiting Owner approval before any constru | - |
| `iig-compendium-2026-07-30.md` | STOP #1 | iig | **OPEN** | STOP #1 — presented inline, awaiting Owner approval before any constru | - |
| `re-baseline-compendium-2026-07-26.md` | STOP #1 | re-baseline | **OPEN** | STOP-1 (Phase 0 complete; awaiting Owner approval of the revised archi | - |
| `sdd-os-activation-2026-07-26.md` | STOP #1 | sdd-os-activation | **OPEN** | STOP #1 delivered inline; awaiting Owner approval before any execution | - |
| `seip-sprint2-2026-08-06.md` | STOP #1 | seip-sprint2 | **OPEN** | STOP #1 -- BLOCKING, presented inline, awaiting Owner selection | - |
| `uceimr-expansion-2026-08-04.md` | STOP #2 | uceimr-expansion | **OPEN** | STOP #2 — BLOCKING, presented inline, no dataset written | - |
| `apir-corpus-2026-08-03.md` | STOP #1 | apir | **CONTRADICTED** | STOP #1 — BLOCKING, awaiting Owner selection of A / B / C / D | vault/plans/seip-corpus-2026-08-04.md: \| 10 \| CPP-APIR \| ≈80 % owned \| corpus refused; `capability_runtime |
| `cdicf-corpus-2026-08-06.md` | STOP #1 | cdicf | **CONTRADICTED** | STOP #1 — blocking. No dataset or module content is written until the  | vault/audits/cdicf/CDICF_DATASET_STATUS.md: \| **A3** Registry producer + redistribution guard \| NEW \| **SEA |
| `crpf-2026-07-27.md` | STOP #1 | crpf | **CONTRADICTED** | STOP #1 (verdicts delivered inline to the Owner; no Part authored) | vault/plans/crpf-overlap-audit-2026-07-27.md: Charter impact: CRPF is struck as a NEW family; construction ord |
| `crpf-overlap-audit-2026-07-27.md` | STOP #2 | crpf-overlap | **CONTRADICTED** | STOP_2_PENDING_OWNER — no CRPF architecture designed, per instruction | vault/plans/STOP_LEDGER.md: \| `crpf-2026-07-27.md` \| STOP #1 \| crpf \| **CONTRADICTED** \| STOP #1 (verdict |
| `e-passes-audit-2026-07-29.md` | STOP | e-passes | **CONTRADICTED** | STOP — verdicts delivered inline. No E-pass Part authored. No E-pass a | vault/plans/STOP_LEDGER.md: \| `igef-2026-07-29.md` \| STOP #1 \| igef \| **CONTRADICTED** \| STOP #1 — verdic |
| `efaif-corpus-2026-08-04.md` | STOP #1 | efaif | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/efaif-expansion-2026-08-06.md: \| EFAIF STOP #1 open \| reads **CONTRADICTED** — a documented fals |
| `egcc-corpus-2026-08-06.md` | STOP #1 | egcc | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/STOP_LEDGER.md: \| `uceimr-corpus-2026-08-04.md` \| STOP #1 \| uceimr \| **CONTRADICTED** \| STOP  |
| `igef-2026-07-29.md` | STOP #1 | igef | **CONTRADICTED** | STOP #1 — verdicts delivered inline. No IGEF Part authored. No IGEF ar | vault/plans/e-passes-audit-2026-07-29.md: precedent: CRPF struck (vault/plans/crpf-2026-07-27.md) · IGEF struc |
| `seip-corpus-2026-08-04.md` | STOP #1 | seip | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/efaif-expansion-2026-08-06.md: \| EFAIF STOP #1 open \| reads **CONTRADICTED** — a documented fals |
| `uceimr-corpus-2026-08-04.md` | STOP #1 | uceimr | **CONTRADICTED** | STOP #1 — BLOCKING, presented inline, no dataset written | vault/plans/egcc-corpus-2026-08-06.md: \| F1 \| Governance Benchmarks \| **DO-NOT-BUILD** \| SQI: 4 sealed dat |
| `ukr-runtime-2026-07-30.md` | STOP #1 | ukr | **CONTRADICTED** | STOP #1 — presented inline, awaiting Owner approval before any constru | vault/plans/seip-corpus-2026-08-04.md: \| Universal Knowledge Runtime \| **0** \| Does not exist. `ukr-runtime |
| `ccfl-pdpf-corpus-2026-07-31.md` | STOP #1 | ccfl-pdpf | **RESOLVED** | STOP #1 CLOSED — verdict MAJORITY_OWNED. Awaiting Owner selection befo | - |
| `pane-map-versioning-2026-07-06.md` | STOP #1 | pane-map-versioning | **RESOLVED** | **SHIPPED 2026-07-06** (SCS C80). ULTRA-PLAN, Reality Scan STOP #1 app | - |
| `process-hibernation-fase-a.md` | STOP #1 | process-hibernation-fase-a | **RESOLVED** | **built + tested 2026-07-03** \| Owner-approved scope (STOP #1): Shell | - |
| `usirc-corpus-2026-07-31.md` | STOP #1 | usirc | **RESOLVED** | STOP #1 RESOLVED — Owner selected Option B (build the residue as one m | - |

## Reading

- **OPEN** — open-shaped status and no artifact anywhere witnesses an outcome. Genuinely outstanding; these are the ones to act on.
- **CONTRADICTED** — the plan still reads as awaiting, but another artifact states what became of it. The work is done; only the record disagrees.
- **RESOLVED** — the plan's own status states its outcome.

A disposition is never asserted, only witnessed, and a plan may not witness itself. Absent evidence the verdict is OPEN — this producer can create work, never silently close it. CONTRADICTED means *a contradiction exists*, never *this is resolved*; verify the witness before acting on it.

### Known limits of the witness test

**False positives — precedent citation.** An audit that cites another family's verdict as prior art (an `| EFAIF | DO-NOT-BUILD |` row inside a base-rate table) produces a line carrying both the family token and a disposition verb, indistinguishable by line-level matching from a statement about that family's own STOP. This is exactly why the verdict is CONTRADICTED rather than RESOLVED: the tool surfaces the disagreement and a human adjudicates it.

**False negatives — family-token drift.** A disposition recorded under a name other than the filename is missed. `e-passes-audit` is the live instance: it was struck on 2026-07-29, but the closure report records that outcome as `E1-E5`, so no line carries the token `e-passes` and the plan reads OPEN here. Misses fall toward OPEN, which is the safe direction — this producer over-reports outstanding work, never under-reports it.

## Two producers, one boundary

`modules/backlog_autopilot/stop1_queue.py` is the other half. It is the **Owner-authored writer**: `resolve()` records a terminal status on the plan itself. This module is the **derived read model**: it infers from evidence and never writes. A read model may not write and a writer may not infer, so neither replaces the other.

Their counts disagreed (22 here, 15 there) and the reconciliation of 2026-08-06 found four distinct causes — not one bug:

| cause | count | whose |
|---|---|---|
| witness test vs. self-reported `status:` | 9 | by design, both correct |
| `STOP #2` counted under a STOP #1 heading | 2 | **this module's defect**, fixed — the checkpoint is now labelled |
| `status: STOP-1` (hyphen) missed by a literal `STOP #1` marker | 1 | `stop1_queue` — reported, not patched; it belongs to another pane |
| `STOP #1 CLOSED … Awaiting Owner selection` | 1 | genuine source ambiguity; the line asserts a closure and a wait at once |

Neither number was right. They mismeasured in opposite directions for different reasons, which is what two independent instruments are for — and is why the disagreement was worth reconciling rather than averaging.
