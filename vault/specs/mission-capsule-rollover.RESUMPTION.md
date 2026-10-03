# RESUMPTION -- mission capsule-v2 rollover (convergence of cpp-gsd-long with kclear/kresume)

**Identity.** Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree: other panes commit here; commit by pathspec, verify `git log -1`). Spec (controlling; section 8
supersedes 3-6, section 9 is the T5 seam T6 calls): `vault/specs/mission-capsule-rollover.md`. G1-G25 binding.

**Sealed (verify with `git log --oneline`):**
- `7e99f636` T0 spec. `8f43790d` T1-T3 rollover.py (v2 key, leased claim, reality-bound certify).
- T4 guard `hooks/capsule_mutation_guard.js` + dispatcher wiring (live dispatcher edited outside git;
  rollback copy `~/.claude/backups/hook-dispatcher.pre-capsule-guard-20261003.js`).
- `313416ff` G23 legacy characterization + golden (sha256 `8FF376809E5B`, captured on 1b0b929d). NEVER
  re-capture to make a red go away: a red is a migration signal.
- T5 (status IMPLEMENTED, no production caller): `87b90738` rollover.precert_arm (create never inherits a
  certification) - `1bbb9470` gsd_long_run.gsd_manager (one init.manager reader; gsd_status identical on
  7 real cases) - `5cdd7d9f` + `d99851cc` tools/mission_capsule.py (compile/seal/gate, arm/bind, CLI
  resume|certify|status --mission with G12) - `0ca149e7` UKDL - `44d95409` review fixes (pp-code-reviewer
  APPROVE, 1 MEDIUM + 2 LOW fixed: custody never unjudged, gate per G3, bind only own marker).
- Gates at `44d95409`: CAP2 36/36, ROLLOVER 55/55, CMG 18/18, G23 32/32 (golden unchanged), MCAP 49/49
  (12 source mutants, crash != kill, subject-based live sentinel).

**Active decisions.** Live missions (P3 m-13177bed4fa3 and others) have no `rollover_protocol`: legacy,
never stop/rearm them. Every gsd_mission.py edit reaches them on the next sweep: gate each new branch on
`rec.get("rollover_protocol") == "capsule-v2"`. T8 HELD by the Owner. Chain audit CLI is T7 (spec 4), not T5.

**Named debt (not T5's).** test_gsd_long_run 98/100: V-GSDLR-WD-ROLLOVER-ASKS-KCLEAR + WD-TEXT-NAMES-ROUTE
red with HEAD's module too (context-watchdog.py changed 10-01/10-02, test last 09-28). Worktree
`C:/Users/User/Apps/pp-mission-fix` holds 3 gsd_mission.py fixes NOT on this branch: merging them changes
legacy behaviour = G23 red = a deliberate migration. /liveness scans modules/ only (tools/ invisible).

**Next 3 actions.**
1. T6 entry gate: run the 5 gates above; list live missions (`~/.claude/state/gsd-mission-*.json`) and
   confirm none carries `rollover_protocol`; check `git log` and pp-mission-fix for gsd_mission.py moves.
2. T6: wire gsd_mission behind the protocol gate using spec section 9 (arm flag + G11 mode refusal,
   ROTATE -> compile/seal -> `outgoing_stop_authorized` -> gate_before_stop -> stop (G3), capsule_key (G6),
   capsule_hold (G4), G5 clock, arm before spawn / bind after, v2 card block (G22), MCP strip (G9), renew
   carries protocol (G20), file kill switch (G13)). G23 must stay green unchanged.
3. Then flip kresume.md guard status PLANNED -> LIVE; T7 fault matrix + chain audit.

**Start.** Read spec sections 8 and 9, run the gates in action 1, then do action 2.
