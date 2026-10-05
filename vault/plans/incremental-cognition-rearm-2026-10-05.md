---
id: PLAN-IC-REARM
date: 2026-10-05
status: APPROVED 2026-10-05 (Owner "Approve (Recommended)" to the inline ULTRA-PLAN; this file mirrors it)
covers: [incremental-cognition-rearm, ic-closeout, ic-pillar-k, ic-invalidation-drill]
parents: [vault/plans/incremental-cognition-program-2026-10-03.md]
mode: EXECUTION in a fresh interactive epoch (/kclear -> /kresume); no new goal, no new ledger
done_gate: python tools/test_incremental_cognition_program.py --final exit 0 AND python tools/test_ic_closeout.py exit 0 AND the invalidation drill reports 0 false negatives
---

# Incremental Cognition -- rearm and closeout (same programme, same ledger)

Authority: `vault/programs/incremental-cognition/ledger.json` (frozen rules, immutable), `owner-bundle.md` rows,
`OWNER-DECISIONS-2026-10-04.md`. This file adds only the order of work and the Owner decisions of 2026-10-05.

## Owner decisions 2026-10-05
- Plan approved; execute in a fresh epoch (this file + the ledger are the whole state; no transcript).
- Realized-saving experiment: Autonomous Optimization P4 runs the live late-rollover champion/challenger ONCE after the
  quota reset; IC consumes the result. Until then IC effectiveness = NOT CERTIFIED (never fabricated).
- Pillar H: keep RESEARCH_INSUFFICIENT_EVIDENCE (answers owner-bundle row 21).
- Push of the local commits: ask the Owner once at the end, with the final count. Never push without it.

## Verified state at approval (HEAD 646c6c86, branch feature/knowledge-acquisition)
- Closed: D E F G H L (`d2e4edef`, --pillar PASS each). Open: A B C I J K M N.
- "CE clauses failed (rc 1)" = `test_incremental_cognition_program.py:1295-1300` reporting `ce.main(["--final"])`'s rc,
  i.e. the 8 open pillars (L3) + 4 missing closeout artifacts (L8). Not a separate defect.
- 99 commits ahead of `origin/feature/knowledge-acquisition`; 865 dirty paths, mostly other writers; a concurrent
  session commits in this tree (autonomous-optimization, cognitive-economy). Pathspec-scoped commits only; re-read HEAD.
- `.planning/workstreams/incremental-cognition/STATE.md` is STALE ("phase 1, 0 completed").

## Order of work (each one micro-commit, record calls + context per step in the log below)
1. Correct STATE.md to the ledger (STALE -> current), with this plan as the resume pointer. (~5 calls)
2. **K** (row 12, Option B AUTHORIZED, no quota): write `vault/programs/incremental-cognition/floor/reference.json`
   with the row-12 command, one real `--check` (row-12 command) as PRG -> `evidence/K-prg.md`, plus a deliberately
   injected floor rise on an isolated copy must go red; gate `python tools/test_floor_regression_gate.py`.
   Do not weaken the threshold. K measures the startup floor, not equivalent-change cost: say so. (~15)
3. **Invalidation drill** on the ledger's pinned-proof graph via `tools/mutation_drill.py` (isolated copy, never the
   live file): positive = 1 byte in one cited measurement -> exactly that pillar red; negative = 1 byte in an uncited
   file -> all 14 verdicts unchanged. Report TP / FN / FP and re-judged / affected. Scope: proof invalidation in this
   ledger only. Evidence -> `evidence/invalidation-drill.md`. (~12)
4. **J** (row 29) and **M** (row 30): `python tools/ic_r2_evidence.py --pillar J|M --commit HEAD`, handoffs J.md / M.md
   under `vault/programs/incremental-cognition/handoffs/`, owner + owner_ledger evidence, `--pillar J|M` PASS.
   CE D E I are MERGED; CE Q N O MERGED + CE M DEFERRED_STRONGER_OWNER. gen2 M belongs to autonomous-optimization:
   M's handoff points there for the residue. (~15)
5. **B** (rows 13, 15 AUTHORIZED conditional): a7 deploy dry-run, apply only if clean and no unexpected diff; a5 same;
   save each record. Then STOP for the Owner's a7 `/login` (row 14, Owner action). (~20)
6. After the login: B preflight JSON -> `evidence/B-prg.md`; **C** PRG (row 2: suites already PASS and pinned, do not
   rerun) -> `evidence/C-prg.md`. (~10)
7. **N** (row 31 APPROVED): `ukdl-candidates.md`; promote IC-U-01/04/06 -> `ukdl-universal.md`, IC-D-01 ->
   `ukdl-cognitive-resource-os.md`, IC-U-02 as instance; NOTHING to CBR; review entry + `## Promotions recorded` in ONE
   commit; ledger reviews/deltas filled only with evidenced items; `python tools/test_ic_closeout.py` exit 0. (~25)
- **A**: wakes on the next real held mission (both named subjects are gone: m-fdefb0fca0c0 COMPLETED, m-876f8b5a904a
  HALTED). One observation records hold reason, peer SHA, relay, preserved worktree commits, unrelated missions not woken.
- **I**: sleeps on `vault/programs/skill-capability/ledger.json` state.B (None at approval); re-read once per epoch start.

## Budget and breakers
LOW ~70 calls / ~12M, CENTRAL ~100 / ~20M, HIGH ~150 / ~35M processed tokens. Warning 30M; hard stop 45M or 180 calls.
A step past 2x its planned calls with no new evidence stops and is re-planned. Rotate the epoch when context exceeds
~2.5x its first-call context. Expected end state if the experiment has not run: COMPLETE, effectiveness NOT CERTIFIED.

## Execution log (append per step: step, commit, calls, peak context, result)
