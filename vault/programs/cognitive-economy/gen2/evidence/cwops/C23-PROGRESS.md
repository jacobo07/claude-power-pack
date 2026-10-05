# CWOPS-C23 progress (c2 mission envelope setter + c3 compiled-WU launch path)

Plan: vault/plans/cwops-compiled-execution-2026-10-05.md (Results, Next item 1).
Isolation: shared checkout refuses background edits; work in linked worktree
`.claude/worktrees/cwops-c23`, branch `cwops/c23`, from b23e94f1 (= feature/knowledge-acquisition HEAD).

## Facts confirmed (2026-10-05)
- tools/gsd_mission.py (2969 lines) reads `token_estimate` (supervise -> _cost_breaker -> mission_spend.judge, int),
  `model` (worker_argv -> --model) and `autocompact` (worker_argv -> --autocompact, default AUTOCOMPACT_SAFETY_NET "600k").
  No CLI sets any of them on an existing mission: subcommands are arm, session-start, handoff, directive, hold,
  release, supervise, status.
- Relaunch prompt is always `bind_workstream(rec["resume_command"], ...)`: launch_worker L777 and
  supervise continue path L2341. GSD-specific branches (ALL_COMPLETE completion, gsd hold) key on
  `resume_command.startswith("/gsd-autonomous")`.
- Model for setters: add_directive / set_owner_hold -> transition() CAS with an event; release_owner_hold
  states "the budget clock is not reset" (created_at untouched).
- tools/gsd_mission.py clean in the shared checkout at b23e94f1 (git status empty for it).

## Built
- Spec: vault/specs/mission-envelope-and-compiled-wu.md (covers: mission-envelope, compiled-wu-launch, ...).
- c2: `set_envelope()` + CLI `gsd_mission.py envelope --mission ID [--token-estimate 16M] [--model sonnet]
  [--autocompact 300k] [--wu-packet PATH]`. Through transition(), event `envelope_set`, reason `field old -> new`.
  Refuses: no field, non-positive / unparsable counts, model not alias or claude- id, missing/empty packet,
  unknown or terminal mission. created_at and cost_mark untouched (budget clock not reset).
- c3: `launch_prompt(rec)`: no `wu_packet` -> bound resume_command byte-identical; with one -> compiled prompt
  (packet path + CURRENT sha256, drift noted, 3 lessons, no /gsd- command). Used by launch_worker (computed
  BEFORE the epoch claim; unreadable packet -> ledger `launch_refused_packet`, ok False, no claim, no launch)
  and the same-session continuation. Card shows "Compiled work unit: <path>" instead of "Resume command".
  GSD completion/hold gates still key on resume_command (unchanged).

## Verification (commands run in the worktree, python 3.12, foreground)
- RED: `python tools/test_gsd_mission_envelope.py` before code -> AttributeError: no attribute 'set_envelope'.
- GREEN: same -> ENVELOPE_PASS=28/28.
- Regression: test_gsd_mission.py MC_PASS=225/225; test_gsd_mission_capsule_v2.py MV2_PASS=72/72;
  test_gsd_mission_legacy_characterization.py G23_PASS=32/32; test_gsd_mission_owner_hold.py 12/12;
  test_mission_spend.py MSPEND_PASS=20/20.
- Mutation drill (isolated copies under the job tmp dir, GSD_MISSION_DRILL_DIR):
  M1 launch_prompt ignores packet -> 5 gates red (NAMES-PACKET, NO-GSD, CARRIES-LESSONS, LAUNCH-SENDS-PACKET,
  MISSING-PACKET-REFUSES); M2 drop empty-field refusal -> 3 red (REFUSE-NO-FIELD, REFUSAL-WRITES-NOTHING,
  CLI-BARE-REFUSED). First drill run showed LAUNCH-SENDS-PACKET self-agreeing with the mutant; gate tightened
  to judge against the packet path, re-drilled red.
