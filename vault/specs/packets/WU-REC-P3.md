done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_rec_p3.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-REC-P3.json
cwd: C:\Users\User\Apps\recon_work\wt_keosdtk_home (child-process cwd only; gate/test files live in work_tree)

# WU-REC-P3 -- recon-factory Phase 3 capital promotion

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3. Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths; child-process cwd only). Pathspec commits
with a message file (one file per commit). Gate first: write the done_gate test before the work it proves, and make it
fail on the pre-state. Scripts you run for evidence must await every effect they start.

## 0. Facts (verified by the planner 2026-10-09)
- Recon worktree `C:\Users\User\Apps\recon_work\wt_keosdtk_home`; ROADMAP `### Phase 3` (lines 150-165). Prerequisite: REC-P2C receipt DONE (chain `after`). Never touch the 569 dirty paths; pathspec commits only.
- Success: SRC PROVEN in levels.jsonl rises from 5 by exactly the rows promote() accepted; each has a transaction row with both oracles AGREE; refused rows carry a named reason; swapped-object negative control refused; donors recorded as family/toolchain calibration evidence. GAP-2 (verified bundle seam, re-checked inside levels.py), GAP-6 (register donor sources in src_registry.json first), GAP-8 (admission.admit("compile") before each local promote), GAP-12 (schema /1 unchanged, ledger sha256 before/after).
- GEX44 compile jobs go through the factory's own job path (as P2b did); job share <= 2 (GAP-10); RULE-111 compute jobs; enqueue gates GAP-7/9. Wait for jobs with a bounded poll (await every effect); on exhausted share end BLOCKED.

## 1. Steps (commit after each green step)
1. Probe the P3a seam dcd9178 and what is already promoted; list the residual.
2. Gate first: `tools/test_wu_rec_p3.py` in work_tree asserts the ledger delta equals accepted promote() rows, negative controls refused (swapped object, wrong src_sha256, disagreeing oracles).
3. Register donors, run admission, promote, record calibration evidence; <=3-file pathspec commits.
4. done_gate exit 0 or PARTIAL with named remaining ids.

## 3. Budget and closeout (protected)
About 24 model calls / 39 tool calls (n estimated from: files/gates named in section 1 plus jobs to wait on). At 32 tool calls stop new work, commit green, write the receipt
(PARTIAL allowed with remaining items). End your final message with `HANDOFF NOTE:` and one line.
