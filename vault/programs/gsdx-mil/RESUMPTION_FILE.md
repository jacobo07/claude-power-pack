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

**UPDATE — 2026-11-10 ~10:20Z: PROGRAMME CLOSED PARTIAL.**
- Owner 'y' 09:34:32Z (turn 32665051) raised authority to 34M; D1 woke the epoch-5 worker. P6 716e20b0 and P7
  b9dc3dd8 landed; the mission then HALTED no_progress (expected: nothing left to do).
- CLOSEOUT `.planning/CLOSEOUT-gsdx-mil.md`: PARTIAL. Only G3 was confirmed (1.4 h); G1 and G5 FALSIFIED; G2 near
  zero; G4 unmeasured. The lesson backfill is a gap. The P6 prospective measurement waits on the Owner canary.
- Coordinator re-run: MIL p0-p5 and p7 PASS. **p6 FAILED** (V-MIL-P6-PATCH-CURRENT): P7's mil_immunity fix (+2 lines)
  left guards.patch stale. I regenerated the patch and sha (77548b8c); after that p6 PASSES and the patch
  reverse-applies at HEAD.
- Other gates: CI w0-w8 PASS; MC 242/242 (node 24); GOAL_CONTROL 27/27; test_mission_recovery 69/69. judge.py
  untouched.
- Child calls 106/150, ~132k tokens. Paid USD 0. Nothing deployed, merged or pushed.

**NEXT (Owner).**
1. Canary: (a) G3 only [recommended], (b) G3+G4, (c) none. Packet: `evidence/gsdx-mil/p6/CANARY-REQUEST.md`.
2. Lesson backfill: allow the one-line W5 harness edit, or leave it as a gap.
3. Next mission: the largest waste class (idle while BLOCKED with authority remaining, 2,276 h) has no guard.
