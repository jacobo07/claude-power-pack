# Phase 1 — S1 rotation invariant: Production Reality (GEX44 plane)

Source: `~/.claude/state/gsd-autorun-ledger.jsonl` (6052 rows, this host), 2026-10-24. Reproduce: the two scripts
described below; all numbers are counts over that file.

## Historical rotations (pre-S1 policy, GEX44 supervisor)
- 36 `launch_cause=CONTEXT_ROTATION` rows, all `mechanism=fresh`; trigger mix: wall 23, economic_ceiling 11,
  wall_enforced 1, handoff_requested 1. Acceptance condition "real rotation with trigger wall or economic_ceiling" MET (34).
- State intact: 30/36 rotations have a matching `rehydration_verified` for the new epoch; lag launch->verified 0-1 s
  (it is a marker check, NOT semantic recovery — do not read it as rehydration cost).
- Concentration: m-a6fedd2e311d 11, m-084b5ee34a78 4; the rest 1-3 each.

## Compaction baseline
- 53 `epoch_compacted` rows (12 missions), all `requested=false`, all observed `SessionStart source=compact`.
- Interval between compactions in one mission: median 13.8 min, p10 8.8, p90 39.3 (41 gaps).
- 0 rows carry `rotation_verdict`; 0 `baseline_invariant_repaired`: S1 has not run on any mission yet on this host.

## Champion/challenger: time to first commit after the event (indicative)
Rotation (fresh launch) n=35: median 3.2 min (p25 1.2, p75 6.2). Compaction n=52: median 4.8 min (p25 1.4, p75 10.8).
Method: first commit timestamp in the mission cwd repo (`log --all`) after the event, discarding > 4 h.
CAVEAT (confounded): other sessions committing in the same repo count too, so both medians are lower bounds on true
cost and are not separable below ~minutes. Reading: rotation does NOT lose economically on this data; it is not
proven to win. Token cost to next verified delta is NOT measured here (per-turn usage is not in the ledger).

## Not proven (stays open)
- S1's 0.70 x compaction-line trigger has zero live firings. This very mission (m-3d5f0a27e41d, epoch 1,
  continue_max_tokens 175k) is the live subject; Phase 1 closes LIVE only when `epoch_compacted.rotation_verdict`
  or a CONTEXT_ROTATION launch_cause with `trigger=economic_ceiling|wall` appears for it. Check:
  `python3 tools/gsd_epoch.py epochs --mission m-3d5f0a27e41d`.
- No threshold change is proposed: no evidence rotation loses.
