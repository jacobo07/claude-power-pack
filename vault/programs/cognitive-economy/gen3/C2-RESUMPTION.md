# RESUMPTION -- CP50 lease C2 (arm-A pilot on draw 1-5) -- rewritten 2026-10-11 for a FRESH coordinator pane

Identity. Recon C2 work tree C:\Users\User\Apps\recon_work\wt_cp50_c2 (branch cp50-c2 at 3c86ae2, cannot commit: its
`.ksr_vault` gate refuses everything; code lives in the tree + patches in PP vault/backlog). PP repo
C:\Users\User\.claude\skills\claude-power-pack (branch feature/knowledge-acquisition). Plan:
vault/plans/cp50-run-plan-2026-10-09.md C2. Goal cp50-c2, cap 14,000,000, host DESKTOP-PMT5BS8, root wt_cp50_c2.
Full history and every number: vault/backlog/2026-10-10_cp50-c2-remaining.md (rows 3, 4, 4b, 4c).

Why a fresh pane: the old coordinator pane 62e915d9 processed 37,527,020 in 207 calls (tx_tools dedupe by message.id),
4x everything its workers spent (8.6M). D22/D23 cost rule: coordinate from a fresh pane, hard-cap it (~1M per phase),
arm and end. Never Set-Location into wt_cp50_c2 (binds the pane to the goal).

State 2026-10-11 ~12:30:
- RF Phase 7 jobs: 2 of 4 SPENT, both without records.
  - Job 1 ksrmb-20261010-203003: no base types (all 50 COMPILE_FAILED) + no CURRENT_CAPSULE (judge STALE_INPUT).
    Fixed by C2b-fix (PP 16774243): M2C_TYPES prelude, set_current=True, EXISTS branch writes the pointer.
  - Job 2 ksrmb-20261011-094630: types worked (20 m2cvs units of 4 functions compiled + diffed), but the runner hit
    TOOL_FAILURE "OUT would exceed 20971520 bytes": candidate mode copies the full ~7 MB objdiff report per unit
    (runner_lib.py:1471-1472) instead of trim_objdiff_report. Tree kept in gex44\returns\.incoming\ksrmb-20261011-094630-*.
- C2c-fix RUNNING: mission m-ae80353974b4 (max-cycles 1), packet gen3/packets/C2c-fix.md (PP ad69d515), route target 1.0M
  stop 1.25M. It edits runner_lib.py + a V-CAND-DIFF-TRIMMED gate, re-prepares to recon_factory\cp50\c2c_prep_1_5.
  No send. Receipt: gen3/C2c-fix-receipt.md.
- Goal after C2b-retry settle: used 8,606,329, remaining 5,393,671 (admit later showed 5,136,824: check goal-status).

Next 3 actions:
1. Read gen3/C2c-fix-receipt.md. Meter worker transcript (newest jsonl under
   ~/.claude/projects/C--Users-User-Apps-recon-work-wt-cp50-c2, dedupe by message.id), goal-settle it, hold the mission
   if not terminal. If the commit step did not run, do it (receipt + 2026-10-11_cp50-c2c-fix.patch, pathspec).
2. If DONE: ask the Owner for "y" to C2b-retry2 = Phase 7 job 3 of 4 (1 left in reserve). Packet = copy of
   packets/C2b-retry.md with job dir + prep from the C2c-fix receipt, records to cp50\c2b_records_1_5.jsonl.
   Arm in ONE call: arm (no --supersedes if the old mission is terminal) + envelope with --estimate-basis + admit,
   id = (arm_json).mission.mission_id, hold on any non-zero rc; require wu_packet_epoch=0. Hold the mission as soon as
   its receipt lands (a 2nd cycle could resend).
3. C3: CP50 projection from the records (per-function p50/p95 x 50 x arms + GEX44 job budget). D21 (Tennis) waits on it.

Start: read this file, then the backlog file above. Never coordinate from a long-context pane.
