done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_rec_p2c.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-REC-P2C.json
cwd: C:\Users\User\Apps\recon_work\wt_keosdtk_home (child-process cwd only; gate/test files live in work_tree)

# WU-REC-P2C -- recon-factory Phase 2 close (oracle parity drill + hash drift record)

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3. Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths; child-process cwd only). Pathspec commits
with a message file (one file per commit). Gate first: write the done_gate test before the work it proves, and make it
fail on the pre-state. Scripts you run for evidence must await every effect they start.

## 0. Facts (verified by the planner 2026-10-09)
- Recon worktree `C:\Users\User\Apps\recon_work\wt_keosdtk_home`; ROADMAP `.planning/workstreams/recon-factory/ROADMAP.md` `### Phase 2` (lines 133-148). A/A PASS cfedba3 is already recorded (Phase 2 is open only for its close items). 569 pre-existing dirty paths: never touch; pathspec commits only.
- Open items to close (from the Phase 2 success criteria + carried decision): `decomp/oracle_parity.py` + drill (identical verdicts on gex44match's 350+51 rows, one forced-disagreement control reported as disagreement); the five-file hash drift recorded; GAP-5 per-judge-revision tagging (runner_lib.py sha256, rows with no recoverable hash excluded with a count); carried admission drill scope fix (decomp/test_admission.py sweeps os.listdir(HERE); drill must enumerate its own population).
- GEX44 legs, if any, go through the factory's own GEX44 job path used by P2b (find it in the P2b artifacts under the recon-factory workstream; no new job path, no new dispatcher patch; GAP-7/9/10 enqueue gates apply).

## 1. Steps (commit after each green step)
1. Probe now what already exists (oracle_parity.py, drill, drift record, GAP-5 tags) by file_exists/commit; write the remaining-item list. Do not redo finished items.
2. Write `tools/test_wu_rec_p2c.py` in THIS tree (work_tree): checks each Phase 2 close artifact in the recon worktree by absolute path (exists, drill exit 0, forced-disagreement control reports disagreement). It must fail on the pre-state.
3. Implement the missing artifacts in the recon worktree (cwd), in commits of <=3 files each, pathspec only.
4. Run the done_gate to exit 0; tick Phase 2 close in the workstream STATE/ROADMAP only if the file is not in the dirty set (else record in the receipt).

## 3. Budget and closeout (protected)
About 18 model calls / 29 tool calls (n estimated from: files/gates named in section 1 plus jobs to wait on). At 22 tool calls stop new work, commit green, write the receipt
(PARTIAL allowed with remaining items). End your final message with `HANDOFF NOTE:` and one line.
