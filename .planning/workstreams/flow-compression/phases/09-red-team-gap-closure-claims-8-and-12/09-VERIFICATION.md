---
phase: 09-red-team-gap-closure-claims-8-and-12
verified: 2026-10-26T08:40:00Z
status: passed
score: 3/3
---
# Phase 9 verification (GEX44, worktree fc-p9-exec, CPP_RESOURCE_ADMISSION=off, node 24 on PATH)

| Gate | Result |
|---|---|
| tools/redteam_s9.py run --claims all (07-PIN) | claims 8 and 12 BREACH -> HELD; the other 13 verdicts unchanged |
| test_s9_redteam | S9RT_PASS=114/114 (V-S9RT-C8-SUBJECT gamed=[] blind=[]; C12 pin-ended control breach=True) |
| test_progress_fingerprint_planning | PFP_PASS=25/25 |
| test_gsd_mission | MC_PASS=234/234 |
| test_mission_spend | MSPEND_PASS=46/46 |
| test_s7_replay | S7_PASS=164/164 |
| test_s9_done_gate | S9_PASS=43/43 |

Before the 08-REDTEAM regeneration test_s9_redteam was 111/114: the three failures were the stale committed report
(claims 8 and 12 differed), not the repairs.
