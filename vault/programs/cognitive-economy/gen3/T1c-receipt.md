# cep-gen3 T1c receipt -- auto envelope from measured rate (2026-10-07)

- Worker m-3b71f5457c70 (bg 62ac7eb5): wrote `_auto_budget` + supervise hook in a hand-made worktree
  (`jobs/62ac7eb5/tmp/wt`, branch t1c-auto-budget) because the live checkout refused its edits and EnterWorktree
  failed; session guard stopped it at 17 calls (11 x 1.5); then BLOCKED until max_hours 4.0 -> HALTED. 1,752,008 processed.
- Finished in coordinator pane 0f9b771b (Owner: "finish t1c and make it more accurate"): patch applied clean, then
  headroom changed from flat 15M to the mission's OWN rate: (spent / epochs started) x epochs left, clamped to
  [min_headroom 1M, headroom 15M] from vault/config/mission-budget-defaults.json; ceiling only when spend is
  unmeasured / zero / no epoch / no cycle cap, and the basis says which. estimate = ceil((spent + headroom) / ratio).
- Tests: `python tools/test_gsd_mission_envelope.py` exit 0, ENVELOPE_PASS=55/55 (16 new V-AUTO-* gates).
- Mutation drill (isolated copy via GSD_MISSION_DRILL_DIR): operator-overwritten -> killed (V-AUTO-OPERATOR-PRESERVED);
  no-clamp -> killed (V-AUTO-CLAMP-HIGH, V-AUTO-CLAMP-LOW).
- Live preview (no write): 0 non-terminal, unheld, unbudgeted missions today -> commit changes no live record.
- Spend: worker 1,752,008 + this pane 10,075,093 / 66 calls (includes /kresume, T1b/T2 decisions, T1c arming).
  gen3 total ~37.2M vs 31M cap: CAP BREACHED by ~6.2M, driven by the coordinator pane (again).
- Finding (unverified for T1/T1b, stated by T1c's own transcript): background workers cannot edit the live
  ~/.claude/skills checkout; product tranches in other repos (T3) deliver. Belongs in the reforecast.
