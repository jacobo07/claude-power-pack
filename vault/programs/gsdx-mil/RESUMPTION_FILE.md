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

**UPDATE — 2026-11-10 ~13:10Z: Owner "go ahead and rec on all".**
1. Canary G3 DEPLOYED to the GEX44 live clone: commit **3f6577d9** on feature/knowledge-acquisition (on top of
   aba6356c), not pushed.
   - Patch: `evidence/gsdx-mil/p6/canary-g3.patch` (branch db70afa6). It is the P6 patch minus the P4 immunity
     hunk: immunity is default-on and writes into the recall-indexed vault, which is outside "G3 only".
   - G1/G2/G4/G5 are present but opt-in.
   - Smoke in the live clone, before == after: MC 242/242, self_heal 19/19, goal_control 27/27.
     G3_LIVE_SMOKE_PASS (`smoke_g3_live.py`).
   - Kill: CPP_MIL_G3=off. Rollback: `git revert 3f6577d9`.
2. Lesson backfill: option B, keep the gap. One shared condition, of low value, against breaking the frozen
   GSDX-CI W5 harness.
3. Next mission NOT launched. The miner miscounts (see memory feedback_mission_waste_miner_counts_planned_spend):
   - 390M of the 583M is authority reached, not waste.
   - 1,940 h of the 2,276 h are designed Owner gates.
   - The fixable part (875 h of host prompts) belongs to mission-self-heal v2.

**UPDATE — 2026-11-10 ~14:00Z: Owner "go ahead". Miner corrected inline, with no mission (P8).**
- `mission_waste.by_cause()` + `--by-cause` (76f91dd7). The P1 classes stay frozen.
- Gate `--wave p8`: 3 checks, 10 mutants. Result `evidence/gsdx-mil/p8/result.json`, a post-hoc correction with no
  prediction.
- Train:
  - Waste: stall 57.2M tokens (it used to show 583M), host prompts 875 h, breaker holds 840 h.
  - Not waste: authority spent 383M, designed gates 1,084 h.
  - Unjudged: over-estimate 76.5M.
  - waste_tokens_eq 274.6M.
- Holdout: 1.7M eq (13.6 h of breaker holds; 0 host prompts).
- The P6 gate is updated to reality (01a8a616): the live copy is valid only with OWNER-GO.json and a byte-identical
  file, with 2 new mutants. guards.patch regenerated (7698f828).
- All gates green: MIL p0-p8 and CI w0-w8.

**NEXT.**
- The fixable hours in train do not reappear in the holdout (0 h and 13.6 h). There is no measured class today that
  justifies a new mission.
- Measure G3 prospectively with the next K>=5 missions that autocompact (`directive_redelivered` in the ledger).
