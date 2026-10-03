# RESUMPTION -- mission capsule-v2 rollover (convergence of cpp-gsd-long with kclear/kresume)

**Identity.** Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Spec (controlling, read section 8 first -- it supersedes 3-6): `vault/specs/mission-capsule-rollover.md`.
Audit gaps G1-G25 are binding. Owner answers Q1-Q6 are in the spec front matter / section 3.

**Sealed (verify with `git log --oneline -5`):**
- `7e99f636` T0 spec.
- `8f43790d` T1-T3 rollover.py: v2 key + `mission-capsules/` dir, kind-aware completeness, leased claim
  with generation/takeover under `_ClaimLock`, `resume_flow`/`certify_flow` (snapshot-bound exam, exit 8
  checked BEFORE judging), precert helpers `precert_write/_read`, `_flip_precert`. Gates CAP2 33/33,
  ROLLOVER 55/55, 7 mutants killed. Interactive /kresume runs this exam LIVE now (Owner Q3).
- T4 commit (this one): `hooks/capsule_mutation_guard.js` + `hooks/tests/test-capsule-mutation-guard.js`
  (22/22 incl. --e2e through the LIVE dispatcher) + canonical `hooks/hook-dispatcher.js` wiring.
  LIVE `~/.claude/hooks/hook-dispatcher.js` was edited with the same two lines (not in git);
  rollback copy `~/.claude/backups/hook-dispatcher.pre-capsule-guard-20261003.js` (sha 9B4D7B1C...).
  The guard is inert until a marker exists: nothing writes markers yet (T6).
- G23 commit: `tools/test_gsd_mission_legacy_characterization.py` + golden
  `tools/fixtures/gsd_mission_legacy_golden.json` (captured on 1b0b929d, gsd_mission sha d5324568...,
  no rollover_protocol in source). 23 scenarios = every supervise branch (launch/ack/adopt/replace/
  halt/continue/rotate x3/turn-done/dead/gsd complete/hold->block->unblock/unavailable/quota/auth/
  child/handoff/wall/budget renew+complete/no-progress/waiting-human) + record keys + worker_argv +
  9 card byte-shapes. G23 32/32 incl. 4 mutants (route legacy->v2, card block, stop-auth event,
  argv MCP) all red, clean after. T6 must keep it green WITHOUT `--capture --force`.

**Active decisions.** Live missions (P3 = m-13177bed4fa3, m-876f8b5a904a, m-f9ad30f21e85, BLOCKED
m-162e867ec4e7) have no `rollover_protocol` -> legacy; never stop/rearm them. Every gsd_mission.py edit
reaches them on the next sweep: gate every new branch on `rec.get("rollover_protocol") == "capsule-v2"`.
T8 (real quota) is HELD by the Owner.

**Next 3 actions.**
1. (DONE, G23 sealed -- see above.)
2. T5: `tools/mission_capsule.py` adapter -- compile mission capsule (GSD init.manager actions rendered
   as strings, partial phase -> "continue phase N", G1/G2), seal + gate, fallback/recovery (G5, G21),
   precert marker via rollover.precert_write (worker name, cwd, created_at, capsule_key, resume_cmd),
   CLI `resume|certify --mission` requiring CLAUDE_CODE_SESSION_ID == mission worker (G12),
   `audit --mission` (T8 chain). Tests `tools/test_mission_capsule.py`, isolated state (G24).
3. T6: gsd_mission wiring behind the protocol gate (arm flag + mode refusal G11, ROTATE seal ->
   `outgoing_stop_authorized` -> stop (G3), capsule_key on record (G6), capsule_hold in plan_next (G4),
   v2 card block before GSD facts (G22), MCP stripped (G9), renew carries protocol (G20), file kill
   switch (G13)); then flip kresume.md guard status PLANNED -> LIVE.

**Start.** Read the spec section 8, run `python tools/test_rollover_capsule_v2.py` and
`node hooks/tests/test-capsule-mutation-guard.js` and
`python tools/test_gsd_mission_legacy_characterization.py` (all must be green), then do action 2 (T5).
