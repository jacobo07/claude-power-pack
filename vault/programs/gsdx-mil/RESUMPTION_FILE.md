# RESUMPTION — GSDX-MIL (Mission Intelligence Loop; successor of GSDX-CI)

**Identity.**
- Plan: laptop `vault/plans/gsdx-mil-20261109.md` (a046102c).
- GEX44 product: worktree `/home/kobii/missions/gsdx-ci`, branch **gsdx-mil**, which branches from 2459f6ac.
  b0b38e83 holds the packet, PLAN, BRIEF-VERBATIM (sha d7b79d5f…), the GSDX-INLINE-WAVE capsule and unit.json.
- Authority comes from the Owner's typed 'y', 2026-11-09T19:34:23Z (turn f7b0e9d2).

**CURRENT — 2026-11-09 19:36Z.** Mission **m-03c1c2298ac8** is RUNNING, epoch 1, worker eb68dd62.
- Planning gate verdict: DELTA_PLAN, `planner_agent_admitted=false`.
- 9-phase milestone. 28M authority, no top-ups. 24 cycles / 48 h.
- The launch command is a plain prompt; the gate refuses `/gsd-*` under DELTA.
- `worker_marker_refused` ("must start with '/'") is benign. It comes from the retired v2 marker and fires for
  every non-`/` mission in the estate (76, 30, 23, …). The P1 miner must class it as noise.
- Concurrent spec on the laptop: `vault/specs/mission-self-heal.md` (another pane; edits `align_cwd` and
  `launch_worker` in tools/gsd_mission.py). The MIL guards also edit gsd_mission.py, on the gsdx-mil branch, so a
  merge conflict is possible at deploy time.
- Reach GEX44 with an LF, no-BOM temp script: `cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`. Use scp,
  never `>`, onto .jsonl paths. Run MC with `PATH=/opt/node-v24.14.0/bin:$PATH`.

**NEXT.**
1. Watch that P0 and P1 commit product before ~7M, and that no Agent-tool call appears in the worker transcript.
2. At P6, the Owner decides the canary deploy of G1-G4 to the GEX44 live clone. It is not pre-approved.
3. The coordinator independently re-runs the gates plus MC/AMCR/GOAL_CONTROL at every checkpoint.
