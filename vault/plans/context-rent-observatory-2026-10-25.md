---
covers: [ctx-rent-a2-closure, ctx-rent-obs, context-rent-observatory, takeover-receipt, context-baseline-b1, ccr-independent-certification, cr-o1, cr-o2, cr-o3, cr-o4]
status: AWAITING OWNER APPROVAL (2026-10-25). Nothing armed, no goal declared, no authority moved.
mode: EXECUTION (W1-W4). PLAN only for deferred items that need a new schema. No ULTRA-PLAN.
supersedes_execution_of: vault/plans/context-rent-a2-2026-10-11.md slices C-L (ownership already moved; see section 2)
---

# Context Rent Observatory, tranche 1, plus the truthful closure of ctx-rent-a2

## 0. Verdict
- **Close ctx-rent-a2** as `DELIVERED_WITH_TRANSFERRED_OBLIGATIONS`, after booking this pane's spend.
- **Do not build a new Observatory runtime.** Most of the instruments already exist; several are CCR-authored, so
  they cannot certify CCR's own savings.
- Tranche 1 is four small units on a **new goal `ctx-rent-obs` (P80 7M)**:
  1. close the old programme truthfully;
  2. make a reproducible baseline B1;
  3. independently re-measure one CCR claim under a contract frozen before the data is read;
  4. prove the existing floor CI goes red on an injected regression.
- Everything else is deferred until tranche 1 shows leverage.

## 1. ctx-rent-a2 truth (measured 2026-10-25, `mission_spend.py goal-status`, ledger `goal-budget/ctx-rent-a2`)

### Authority lineage
| seq | when (local) | value | source |
|---|---|---|---|
| 1 | 10-11 10:27 | cap 14,000,000 | plan 6f5840a3, Owner "y go p95" |
| 33 | 10-11 14:02 | programme 30,000,000 | capital packet `owner-capital-ctx-rent-2026-10-11.json`, approval e2a5f2c6 (typed 12:01Z) |
| 44/45 | 10-23 15:29 | programme 60,000,000; lease L2 cap 30M | Owner typed `subelo 30M ctx-rent-a2` (this pane, 13:2xZ), owner-econ-raise |

- There is **no AUTHORITY_PROVENANCE_FAILURE**.
- **Weakness:** the 60M programme row is tagged `owner-econ-raise:owner-raise:goal:ctx-rent-a2:L1` without the
  approving entry's uuid. The lineage had to be recovered from the transcript text.
- **Fix (W1):** the raise row carries the approving transcript entry uuid.

### Money
- **Settled:** 19,522,634; open 0.
- **The executable remainder is not 40.5M.** The pane 36d35fab has been bound to ctx-rent-a2 since 2026-10-23T15:20:10Z.
  It holds mark 0, and it processed **38,134,713** tokens since then (`session_tokens(since)`, 199 calls), unbooked.
  - Booking that spend: settled ≈ 57.66M of 60M.
  - True residual after booking: about 2.3M (exact at closure time, because this pane keeps spending until it stops).
- **Context per call:** this pane runs at **333,752** tokens per call. It is the largest live context-rent leak on the
  estate, so it does no further work after approval.

### Units
- **A** (4de21ba8): census tool + gate.
- **B** (c6657844): see section 4.
- **Residual R1-R6** (aa97ebf8): sealed. R6 sits as a separate file (a06e4dc8), because `ukdl-universal.md` carries
  another writer's lines.

### Repo
| field | value |
|---|---|
| branch | feature/knowledge-acquisition |
| HEAD | dda4892b |
| remote | cba968bb |
| dirty paths | 1,213, other writers active |

## 2. A-L ownership map (implementation owner / evidence owner / state)
| slice | intent | impl owner | evidence owner | impl state | evidence state | transfer basis |
|---|---|---|---|---|---|---|
| A | boot census | ctx-rent-a2 | ctx-rent-obs | DELIVERED 4de21ba8 | PROVEN (method) | - |
| B | boot deflation | ctx-rent-a2 | ctx-rent-obs | DELIVERED (applied 10-11) | BOOT_REDUCTION_ESTIMATED, N=1 (section 4) | - |
| C | router + lean carrier | ccr | ctx-rent-obs | TRANSFERRED | OPEN | ccr-mods-backend-2026-10-11.md:26 "execution backend of ctx-rent-a2" |
| D | boundary rotation | ccr | ctx-rent-obs | TRANSFERRED | PARTIAL (ccr_epoch_econ.py is CCR-authored) | same + ccr-v4 E1 59babe7d |
| E | zero-model status | ccr / goal runtime | ctx-rent-obs | TRANSFERRED (programme_status.py exists) | OPEN | same |
| F | boundary metrics | ccr | ctx-rent-obs | TRANSFERRED (ccr_carry_fit, session_autopsy) | OPEN (CCR self-measured) | same |
| G | context CI | incremental-cognition (floor_regression_gate, pillar K) | ctx-rent-obs | PRODUCTION (wired in wake_check.py) | W4 drill | floor gate commits 8169092c..0f07a3d7 |
| H | first production canary | ccr (ring R2) | ctx-rent-obs | SUPERSEDED_BY_CCR | OPEN | ccr-mods-backend:146 |
| I | carrier successor canary | econ-succession | econ-succession | PARTIAL (S3 done, not via carrier) | OPEN | af7ec647 |
| J | S2-S10 | econ-succession | econ-succession | PARTIAL (S2-S4 af7ec647, 44396331) | OPEN S5-S10 | econ-succession goal: 12.86M of 20M |
| K | econ-contain-2 S9 canary | econ-succession | econ-succession | EXPIRED (packet 2026-10-14) | NOT_RUN | needs a new Owner act if wanted |
| L | KV/UKDL/CBR | ccr (R5 CBR) | ctx-rent-obs | TRANSFERRED | OPEN | ccr-mods-backend:156 |

- **Root cause of the ambiguity:** the A3 transfer exists only as prose in the CCR plan. Nothing machine-readable says
  who owns an obligation, so ctx-rent-a2's RESUMPTION kept offering C+F as NEXT.
- **Fix:** `vault/programs/ctx-rent-a2/TAKEOVER.json`, one receipt per row, using the fields of the brief.
- **Check:** `cpp_fsck` stale_resumption also flags a RESUMPTION NEXT line that names a transferred obligation.
- No new ownership graph; no registry exists to extend. Nearest prior art: `vault/estate/worktree-lifecycle.json`
  (worktrees) and `tools/mission_supersede.py` (missions).

## 3. Resumption truth
- **ctx-rent-a2:** seal RESUMPTION_FILE with a closure class, no NEXT, and a fingerprint (closure commit + TAKEOVER.json sha).
- **econ-succession:** its RESUMPTION_FILE (anchor 4e9953a7) still says "do S1", although S2-S4 landed after the anchor.
  - The anchor check passes because the anchor is an ancestor of HEAD. This is UKDL Trap 1 of
    RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION, live.
  - Its last writer was 10-13.
  - W1 prepends a STALE banner that names the landed commits. Its NEXT is left to its owner.

## 4. Baseline B1: what A and B prove

### Proven
- **A:** a deterministic per-source floor census method.
- **B, controlled file component:** always-loaded file characters 139.8K -> 96.0K (-31%).

### Measured once, uncontrolled
- Provider call-1 floor 122,093 -> 106,769 (-15,324, -12.6%). It was measured on **this pane** (N=1).
- The model and the MCP set differ between the two measurements.
- The census JSON lives only in this pane's scratchpad (not durable).

### Typed claims
| claim | state |
|---|---|
| BOOT_REDUCTION | ESTIMATED (controlled chars) / MEASURED_ONCE (provider) |
| STEADY_STATE_REDUCTION | UNKNOWN |
| LIFETIME_CARRIAGE_REDUCTION | UNKNOWN |
| CONCURRENCY_SCALING | MEASURED elsewhere: CAF ≈ 1.01 (vault/plans/ccn-concurrency-neutrality-2026-10-24.md) |
| CROSS_PROJECT | UNKNOWN |
| QUALITY_PRESERVED | UNKNOWN (no proof contract was run) |

### B1 record
- Reuses the floor gate's reference schema (layer/scope components, caveats). No new format.
- Fields: Claude Code version, model, MCP set digest, skill/agent listing chars, hook context, memory/rules chars,
  prompt digest, call-1 tokens with spread over N=3 fresh probes.
- Any field the probe cannot see is UNKNOWN.
- MEMORY.md regrowth (+4.2K -> now 21.9 KB) is recorded as debt, not fixed here.

## 5. Separation of powers (architectural, by file ownership)
- **CCR actuates:** `ccr_*`, mods.
- **ctx-rent-obs measures and certifies:**
  - `vault/programs/ctx-rent-obs/` (contracts, receipts, B1);
  - instruments it did not author for CCR: `context_floor_census.py`, `floor_regression_gate.py`, `session_autopsy.py`.
- **Evidence:** a certification is valid only if its contract file was committed **before** the data it judges was
  read, so the commit order is the proof (Goodhart guard).
- **Economic kernel:** `ctx-rent-obs` gets its own goal; no ctx-rent-a2 residual is reused.
- **CBR:** promotion only after W3 evidence.

## 6. Tranche 1 work units (all EXECUTION; fresh Sonnet worker; pathspec commits only)

### W1 Closure (CR-O1/O2)
1. TAKEOVER.json (12 rows) and closure receipt `vault/programs/ctx-rent-a2/CLOSURE.md`.
2. Book pane 36d35fab: `goal-settle --goal ctx-rent-a2 --session 36d35fab --measured <session_tokens since 2026-10-23T15:20:10Z>`.
3. Lower the ctx-rent-a2 programme to settled + open (lowering needs no Owner act, V-OCA-HOLE gate). The released
   amount is not repurposed.
4. Seal RESUMPTION_FILE; add the econ-succession STALE banner.
5. Code: the econ_plane raise row carries the approval uuid, with a red-first test. The `cpp_fsck` stale_resumption
   transferred-NEXT check, with a red-first test.

### W2 Baseline B1 (CR-O3)
- Commit the census JSON.
- Run 3 fresh probes through `floor_regression_gate.py --probe` (same prompt, same model).
- Write B1 with the spread. B is then re-typed from N=1 to N=3.

### W3 Independent certification canary (CR-O8-lite)
1. Commit `ctx-rent-obs/contracts/C1.json` FIRST. It names the CCR claim, the instrument, the population, the
   denominator and the verdict rule.
   - Candidate: CCR M1 "trivial subagent 47,591 -> 15,571 (-67%) with attachments dropped".
   - Fallback: ccr-v4 E1 "Lobby BEATS_A (k=40)".
2. Re-measure with Context Rent instruments from raw transcripts or a fresh matched pair.
3. Verdict: CERTIFIED / REFUTED / UNMEASURABLE, never inferred.

### W4 Context CI drill (CR-O5)
- If `test_floor_regression_gate.py` already drives an injected resident addition to exit 1, cite the gate and stop.
- Otherwise add that one drill.

### Done-gates
- **W1:** `cpp_fsck` stale_resumption PASS on ctx-rent-a2 and FINDING on econ-succession, until its owner acts.
  goal-status shows programme == settled + open.
- **W2:** B1 file with N=3.
- **W3:** a verdict row whose contract commit precedes its data commit.
- **W4:** an exit 1 observed.

## 7. Deferred (classified)
| class | items |
|---|---|
| high ROI next | Minimum Verified CWS certificate for **mission-worker boot** (every Ralph epoch pays it; stable proof = worker reaches its first tool call with the card read; measured floor 100-215K); Projected Estate Rent (floor gate scopes x session counts) |
| PLAN first | Context ABI, consumer map, context object accounting, context debt ledger |
| speculative | lifetime flamegraph, leak detector, page-fault/locality curves, held-out workloads beyond one non-CPP repo |

Other measured state:
- The concurrency benchmark already exists in CCN (CAF ≈ 1.01); reuse it, do not rebuild.
- Status model tax is CCR's (programme_status.py); W3 may pick it as a later contract.

## 8. Budget (processed input incl. cache reads; fresh Sonnet worker, floor ~70-110K/call)
| unit | lower bound | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| W1 closure + 2 small fixes | 0.6M | 1.2M | 1.8M | 2.5M |
| W2 B1 (3 probes ≈ 0.35M) | 0.4M | 1.0M | 1.4M | 2.0M |
| W3 certification canary | 0.6M | 1.5M | 2.2M | 3.0M |
| W4 CI drill | 0.1M | 0.3M | 0.5M | 0.8M |
| recovery + meta | - | 0.8M | 0.8M | 0.8M |
| **total** | **1.7M** | **4.8M** | **6.7M** | **9.1M** |

- **HARD AUTHORITY:** 7,000,000 on new goal `ctx-rent-obs` (P80).
- **Stop-loss:** a unit over 2x its P80; 3 epochs without a commit; a W3 contract edited after data was read.
- **Confidence:** medium-low. This lineage ran 13x over on S0 and 1.4x over on ctx-rent-a2.
- **Payback:** UNKNOWN by construction. Tranche 1 measures, it does not save. Its value is refusing an unproven
  savings claim and naming the next real lever.
- **Saturation stop:** if W3 finds CCR's claim CERTIFIED and B1 shows no unexplained floor mass above 10K, the
  Observatory stops at tranche 1.

## 9. Execution, rollback, Owner boundaries
- **Execution:** this pane arms one Ralph mission and stops.
  - `gsd_mission.py arm --cwd <PP root> --command "<W1-W4 contract of this file>" --max-cycles 6 --max-hours 8`
  - then `mission_topup.py budget --authority 7M --topups 0`.
  - The worker binds goal `ctx-rent-obs` and commits by pathspec in the shared tree.
- **Rollback:** every unit is one or two commits, revert-safe. Ledger moves (pane booking, programme lowering) are
  reversible only by an Owner correction, so they are done last in W1, after the receipts are committed.
- **Owner boundaries left:** none in tranche 1. A second tranche needs a new approval.

## 10. Micro-commits
TAKEOVER.json+CLOSURE.md · ctx-rent-a2 RESUMPTION seal · econ-succession STALE banner · raise-uuid fix+test ·
fsck transferred-NEXT check+test · B1 census JSON · B1 record · C1 contract · C1 verdict · CI drill (if needed) ·
UKDL entry PROGRAMME_OWNERSHIP_AMBIGUITY (separate file while ukdl-universal.md is dirty).
