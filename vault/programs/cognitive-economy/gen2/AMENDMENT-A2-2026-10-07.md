---
id: PLAN-CE-GEN2-AMENDMENT-A2
date: 2026-10-07
status: APPROVED 2026-10-07 Owner 'y' (pane 886d7bb9) to the inline A2 plan, decisions 1-3 at their defaults
amends: vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md (PLAN-CE-GEN2-COMPLETION) and AMENDMENT-A1-2026-10-07.md
covers: [cpp-presence-contract, baseline-negotiation, baseline-manifest, proportional-mechanism, universal-coverage, metered-over-self-reported, end-to-end-deflation, edd-phase2-selfhost]
source: Owner estate-wide /cpp-gsd-long prompt 2026-10-07 (pane 886d7bb9). Bootstrap source, cold: workers never read it.
mode: PLAN amendment to an existing owner. EXECUTION per unit. No ULTRA (falsified: >90% of the prompt is owned).
---

# Amendment A2 -- CPP presence negotiates the baseline; prove it outside CPP; meter what is real

Workers read THIS card, `gen2/ledger.json` and their own phase in `.planning/workstreams/ce-a2/ROADMAP.md`.
Not the Owner's prompt, not any transcript.

## Verified reality at approval (2026-10-07 14:26, zero-model)
- Three approved programs already own this Goal: gen2 completion (T0, T1a-T1d done; C2/C3 CHECKED), A1 (moratorium,
  U1 done 1,097,211 measured, merged into ce/a2 at f92e5db3), gen3 (T3 10.27M vs champion 16.6M/plan; T1, T1b no
  product; T2 retired; T1c m-3b71f5457c70 BLOCKED).
- `test_cognitive_economy_program.py --generation 2 --final`: FAIL 7 in the main checkout, FAIL 22 in pp-ce-gen2.
  In pp-ce-gen2 it reports `tools/test_ce_t1_state.py` and `tools/test_ce_t1_lifecycle.py` "not found" although both
  exist in that tree. Cause UNVERIFIED (resolution root or interpreter; C15/C16 checks also invoke `python3`).
- EDD Phase 1 end-to-end: canary 3.31M + WU-1R 1.96M + review 0.49M + coordinator 17.41M = ~23.2M vs the stopped
  champion 32.06M (0 obligations). The worker-only 3.31M figure is not a total. Receipt claimed 3 boundaries vs 16
  metered calls: metered wins.
- Spend vs authority: listed measured sources ~298M incl. E1 141M; ~157M without E1 vs boundary 150M. Decision 1
  removes E1 from the boundary; the remainder is still near the boundary, so every A2 unit is metered or it does not run.
- A1 families: gen3-envelopes shows `strikes: 0` in the ledger while T1 and T1b both ended with no product. Unverified
  until A2-0 checks the receipts; if both failed their own criterion the family is at the strike limit.
- Presence today: `modules/gsd_x/cli.py` (UserPromptSubmit) already injects a MEASURED ExecutionOS tier via
  `capability_runtime` in every repo, and the Tower baseline (CBR, `pp-cbr-wt` tower/constitutive-substrate) injects
  inherited lessons. That is the owner A2-2 extends. No second negotiator.
- Live writers to leave alone: pp-ce-gen2 (uncommitted rollover.py + test_ce_t1_paneloss.py, another pane), the main
  checkout (~30 dirty paths), missions m-53847a002b65, m-5128a41e0398, m-9bee7894f20f, T1c, every BLOCKED record.

## Owner decisions (ledger `a2.decisions`)
1. E1 excluded from the gen2 boundary; boundary not raised; A2 cap 20M processed INCLUDING the coordinating pane.
2. Amendment, not a program. A1 moratorium in force: T2 T4 T5 T6 T8 unfreeze only by an A1-1 amortization record
   showing break-even <= 30 days.
3. EDD Phase 2 is the A2-6 self-hosting canary, with its own envelope derived from the EDD reforecast; held if its
   forecast including coordinator exceeds 1.5x EDD Phase 1 end-to-end.

## Units (mission ce-a2 runs A2-0..A2-4 and A2-7; A2-5 and A2-6 are separate envelopes)
| unit | what | cap | done when |
|---|---|---|---|
| A2-0 | gate truth: fix why `--final` cannot see C2/C3 tools; make obligation checks interpreter-portable; verify gen3-envelopes strikes from receipts | 0.5M | pp-ce-a2 `--final` lists only genuinely OPEN items; C2/C3 green |
| A2-1 | meter: per-call attribution incl. coordinator (A1-2, `turns.py --attribute`, G3-G5); `check_receipt` judges metered calls, a self-reported boundary count below metered fails | 3M | both poles driven; a2.spent and a1.spent filled or explicitly UNKNOWN |
| A2-2 | presence: extend the gsd_x tier hook + `.pp-capabilities` into baseline negotiation (strongest certified capability per project, absent = nothing invented); shadow first; kill switch env var | 4M | C17 + C18 checks exist and pass on CPP, one mature project, one weak one; floor delta <= 0 |
| A2-3 | T3 replay (A1 cap): boundary census settle, KEEP/DEALLOCATE, concurrency, idle rebuild | A1 | measurement receipt with top-3 lifetime-cost classes |
| A2-4 | T7 prompt rent: compiler-side retirements, floor delta measured; `~/.claude/CLAUDE.md` only as Owner-applied diff | 3M | floor_regression_gate shows the delta |
| A2-5 | unfreeze at most the frozen tranche whose amortization record breaks even <= 30 days | its record | two-strike applies |
| A2-6 | EDD Phase 2 under the baseline (first BUILD-phase measurement); evidences C19/C20 | own envelope | C20 vs ~23.2M end-to-end per closed phase |
| A2-7 | T9: UKDL (dedupe first), KV causal records, CBR, independent review | 4M | C12, C14 |

## Master Done-Gate
`python tools/test_cognitive_economy_program.py --generation 2 --final` exit 0 over C1-C20 (C17-C20 added by A2,
OPEN with `check: null` until their unit lands an executable check). UNKNOWN never passes. Production Reality and
vMAX-NULL-ERROR apply to every clause.

## Laws for every A2 worker
- Write only `C:\Users\User\Apps\pp-ce-a2` (branch ce/a2). Pathspec micro-commits, `git commit -F <msgfile>`, verify
  `git log -1 --format=%s`, never push. Never touch another pane's tree, mission or hold.
- Never edit `~/.claude/` (settings, CLAUDE.md, rules, hooks): produce the PP-internal half and an OWNER STEP (HR-001).
- RED first for every guard; mutation evidence via `tools/mutation_drill.py`; a guard ships with its test (positive control).
- Measured beats self-reported. Null is never zero. A unit over 1.5x its cap: stop, write the diagnosis, change method.
- No Agent unless the phase names a positive-ROI reason; no raw planner/researcher grammar; dossier before archaeology
  (`tools/gsd_dossier.py`), page file ranges, never re-read whole modules.
- Every bug: Incident -> root cause -> CLASE 0-6 (iteration lens) -> regression -> guard -> UKDL candidate.
</content>
</invoke>
