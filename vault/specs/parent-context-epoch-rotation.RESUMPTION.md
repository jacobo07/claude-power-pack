# Parent Context Epoch Rotation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/parent-context-epoch-rotation.md`.
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Owner pane was `claude-power-pack-c2`; sibling pane `claude-power-pack-e9` owns mission-continuity
T1–T8 (`tools/gsd_mission.py` core, sweep, certification). Announce every `gsd_mission.py` edit to it.

## Thesis
A turn that ENDS is not a context that ran out. Turn end → the SAME `claude --bg` session continues
(`claude --bg --resume <sid> "<cmd>"`, no other flag: a flag makes the host start a copy). Only the
wall (flag `mission-wall-<sid>-e<N>.flag` / `handoff_*` row) or ≥ 300k resident tokens rotates to a
FRESH session. A pending background child holds everything. Kill switch `CPP_MISSION_CONTINUATION=off`.

## Sealed (commits)
`5eee90a` tools/gsd_epoch.py · `717554f` supervise wiring · `79ae1cc` spec + count correction
(10 production rotations, not 1) · `ec5eaad` command doc · `dce125b` F1 work_dir on continuation +
crash-consistency gates · `add6828` host `done`+`end_turn` = turn end, not death.
Gates: `python tools/test_gsd_epoch.py` 66/66 · `python tools/test_gsd_mission.py` 190/190.
Mutation drills (isolated copy, never the live file): scratchpad `mutate_epoch.py` 11/11 killed.

## In flight — S10 live proof
Mission `m-916e905e23d4`, cwd `C:\Users\User\Desktop\Cursor Projects\gsd-long-smoke`, work tree
`.claude\worktrees\gsd-autonomous-run` (phases 5–8 remain), wall 29/30/28 (watchdog floor, ≈300k of
1M), max 30 cycles / 10 h, armed 2026-09-28 00:44Z, launched by the real sweep 00:47Z. Worker 1
`9e89a87e`. The parent grows ~1 %/15 min (subagents do the work), so each epoch takes hours.
Target: ≥ 3 epochs whose `launch_cause` is `CONTEXT_ROTATION` trigger `wall`, each corroborated by
the predecessor's transcript ("CONTEXT WALL") and followed by commits in the work tree; ≥ 1
`turn_continued` on the same session id; never two live `m-916e905e23d4-e*` workers.
Judge out of process: `python tools/gsd_epoch.py certify --mission m-916e905e23d4` (a rotation
counts only with recorded cause + wall witness + the predecessor's own transcript + a new session +
commits). Single-owner witness: `python tools/gsd_epoch.py watch --mission <id>` writes
`~/.claude/state/gsd-epoch-owners-<id>.jsonl` (started 2026-09-28 ~02:10Z). An earlier scratch
sampler took 26 answered samples 00:46Z–02:05Z: live workers 0 (before launch) or 1, never 2.
Do NOT touch the mission.

## Next 3 actions
1. Run the judge; if `rotations_certified` ≥ 3, write the evidence into the spec §5 and a Knowledge
   Vault lesson (`vault/lessons/turn-end-is-not-context-rotation.md`); else report the exact count.
2. After e9's T8 lands, add the UKDL Traps/Process Rules (candidates for Hard Rules listed, not promoted).
3. Re-run `python tools/gsd_epoch.py census` and record the post-change counters.

## Start instruction
`python tools/gsd_mission.py status`, then the judge. Trust the ledger and git, not this file.
