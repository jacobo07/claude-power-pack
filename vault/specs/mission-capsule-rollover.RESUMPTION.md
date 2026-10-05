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

**Owner T6 brief (2026-10-03, after a5debf2d).** Mode: ULTRA-PLAN entry. Run the entry gate READ-ONLY,
then present an INLINE plan for one-click approval BEFORE any gsd_mission.py edit; after approval execute
unattended. The gate must classify (CONTINUE / MIGRATE FIRST / COORDINATE FIRST / BLOCKED): d2505df6 (the
only gsd_mission.py commit since 313416ff, another pane's "follow a proven worktree when a shared cwd
diverged"; G23 stayed 32/32 after it); the G23 golden's source hash vs current gsd_mission.py -- keep
HISTORICAL WITNESS identity separate from CURRENT BEHAVIOURAL compatibility, never re-capture just to match
the hash; each of pp-mission-fix's 3 fixes (legacy bug fix / v2-only / unrelated / superseded / stale);
GSDLR 2 reds (stale test vs regression vs concurrent owner); the liveness tools/ blind spot as a capability
class (production-critical executables discoverable regardless of directory), not a "scan tools/" patch.
Verified at seal time: HEAD a5debf2d, 44 ahead of origin, 0 behind, nothing new since a5debf2d.

**T6 entry gate RESULT (2026-10-03, read-only, HEAD 6957e82e). Verdict: MIGRATE FIRST, then CONTINUE.**
- G-a d2505df6: CONTINUE. Adds non-blocking `diverged_followed` to align_cwd + `proven_ws` in supervise
  relay/replace; no field/card/argv/stop change. T6 constraint: arm_successor goes AFTER align_cwd passes.
- G-b golden: witness != current (CRLF sha d53245.. @1b0b929d vs a217654f.. now; blob 6074504D->8F9BE83D,
  100 % attributable to d2505df6; file clean, autocrlf). Behaviour 32/32. Do not re-capture.
- G-c pp-mission-fix = FOUR commits, not three. 1b27fbf6 (bare host `blocked` read as idle -> relayed 48x)
  LEGACY BUG, still live at gsd_mission.py:1161, LOAD-BEARING for T6 (owner_idle is the seal trigger).
  01567f16 (adopt pass surfaces blocked; needs host_job_needs) and 1a8dabfc (UNKNOWN != BLOCKED) LEGACY
  BUGS, merge clean. 216e39e9 SUPERSEDED by HEAD's progress_origin fingerprint refusal (the only conflict).
  G23 effect of the 3 migrations UNMEASURED (needs an isolated tree).
- G-d GSDLR 2 reds: STALE TEST. 118e5994 (09-29) made /kclear self-invoked (`rollover_kclear_asked
  route=self`, watchdog:1763); test last touched 09-28 still expects a kclear dispatch + "Delivery: MANUAL".
- G-e liveness: aperture is STATED (reachability.py:256), not hidden; a capability-class follow-up
  (entrypoint-evidenced executables, any dir, ratchet), not T6 scope.
- Missions: 89 records, 0 carry `rollover_protocol` (raw grep).

**Owner approved A-D (2026-10-03, "y").** A DONE: 95f494cd/06866df0/482469b8 (3 legacy fixes migrated
via worktree C:/Users/User/Apps/pp-t6-migrate, branch t6/migrate-legacy-fixes) + c28d5b09 backlog; MC
220/220, G23 32/32 UNCHANGED (no re-capture), 3 drills KILLED (drills need copy_dirs ["vendor"]).
B DONE: 2e4be931 GSDLR 100/100. C BUILT (uncommitted at this write): gsd_mission.py capsule-v2 wiring
(spec section 10), mission_capsule.arm_successor(capsule_key=), new tools/test_gsd_mission_capsule_v2.py
MV2 32/32, 7 source mutants KILLED (drills need copy_dirs ["vendor"]); G23 32/32 golden unchanged, MC 220,
MCA 16, EPOCH 82, MCAP 49, CAP2 36, ROLLOVER 55, CMG 18. Docs: kresume.md guard LIVE-in-code (no real
mission), cpp-gsd-long.md flag section, spec 9 status + 10. D DONE: pp-code-reviewer APPROVE (0 C/H);
M1 fixed (MV2 34/34, mutant KILLED); M2/L1/L2 named OPEN in spec 10. Committed as one T6 commit.
OWNER DECISION PENDING (M2): on a budget/no_progress halt of a v2 mission, seal before stopping the live
owner and carry capsule_key into the renewal -- or declare halt/renewal out of v2 scope?
Then: T7 fault matrix + chain audit; T8 stays HELD.

**2026-10-05 Owner brief: M2 + L1 + L2 + no-note + guard msg + T7 (ULTRA-PLAN entry; inline plan
for one-click approval BEFORE any mutation; then unattended). Owner M2 DECISION GIVEN: a resumable
halt is a continuity transition (seal before planned destruction); a hard budget/safety stop may
override but must enter explicit RECOVERY, never SAFE_TO_FORGET; renewal never silently legacy.
Reality scan (read-only) DONE at HEAD bbcb3297 (3 ahead of origin, 0 behind):**
- 100 mission records, 0 capsule-v2, 7 non-terminal. T6 gates green on HEAD: MV2 34, G23 32, MC 220, MCAP 49.
- gsd_mission.py is CO-OWNED: 4 peer commits since ba99cf77 (18b539cf quota relogin, 25a10ce5 auth park,
  308da56b mission_launch_gate pre-launch gate in supervise ~L1855 + renewals inherit quarantine,
  c0042b05). Add their suites to regressions: test_gsd_mission_quota_relogin, test_persistent_failure_park,
  test_mission_launch_gate. Fetch HEAD before every commit.
- Halt reality: budget_exhausted = iterations>=max_cycles or age>max_hours since created_at (mission-level;
  renewal = fresh budget, lineage capped MAX_RENEWALS=3). plan_next halts on budget at PREPARED/LAUNCHING/
  HANDOFF (HANDOFF even if owner busy = a forced stop), owner UNKNOWN/WAITING/dead+budget, idle(turn
  ended)+budget; a LIVE BUSY owner is let finish its turn (budget soft until turn end). no_progress halt
  (supervise ~L1897, stalls>=3) is TERMINAL today: renewal_refusal needs "budget:" in the reason.
  "3 launches never acked" halt also terminal. Renewal only for budget halts with GSD OK (renew_mission L1399).
- Draft M2 shape: in the v2 halt branch, BEFORE HALTED: idle owner -> worker_handoff seal (+fallback) ->
  clean continuity carried into renew_mission (capsule_key; renewed e1 armed with it); otherwise budget
  wins -> halt + stop -> recovery seal from durable state on the halted record -> renewal carries it as
  `recovery`; recovery refused -> renewal refused, HALTED with explicit reason (never legacy).
  no_progress stays terminal (Invariant 9) but records continuity none. Hard bound for a busy v2 owner =
  budget + wall.grace_s, then forced (v2-only; G23 must not move).
- L1 reuse provider_breaker's model (BACKOFF_BASE_S 300 * 2^(n-1), cap 3600, QUARANTINE_AFTER 4) +
  a refusal fingerprint (reasons, HEAD, dirty, obligations): re-seal only on change or backoff elapsed.
- L2: budget check BEFORE the capsule-hold "none" in plan_next; at certify deadline stop the uncertified
  worker (no authority, nothing to seal), keep capsule_key, bounded successor attempts per capsule; claim
  takeover = rollover T2 lease (30 min).
- No-note: ask once per epoch via gsd_epoch.continue_worker(prompt=handoff instruction) while owner LIVE
  idle; still no note after that turn -> immediate degraded fallback (no 30 min wait).
- Guard msg: hooks/capsule_mutation_guard.js:193 renders `python ${m.resume_cmd}` (= mission command);
  render the real tool path from one canonical source; check whether a live hooks copy exists.
- T7: tools/test_mission_capsule_faults.py does NOT exist; chain audit = `mission_capsule.py audit --mission`.
- Iteration input read (Universal vMAX: reality check, CLASE 0-6, minimal core fix, empirical gate, UKDL seed).
**NEXT: present the inline M2/T7 plan for one-click approval (no mutation before approval).**

**2026-10-05 Owner APPROVED S1-S7 ("y"), unattended. Order S1 spec -> S2 M2 -> S3 L1 -> S4 L2 -> S5 no-note ->
S6 guard text -> S7 T7; one causal change per commit; a red gate = STOP and report.** Gate runner:
scratchpad `gates.ps1` (11 suites: MV2, G23, MC, MCAP, CAP2, ROLLOVER, EPOCH, MQR, PFP, LG, MCA) + CMG via
`node hooks/tests/test-capsule-mutation-guard.js --e2e ~/.claude/hooks/hook-dispatcher.js`.
- S1 SEALED `45922af4` (spec section 11; binding for S2-S7).
- S2 SEALED `9efe5333` (MV2 56/56, 11 suites green, G23 32/32 unchanged). Drill debt: 6 KILLED; RE-RUN
  pending for 2 UNJUDGED (RENEW-KEY, card-on-launch; test line hardened) + 2 NOT RUN (renewal-before-seal,
  inherited) -- batch reaped by Claude Code under host memory pressure (2.4/31 GB free, a peer pane's
  zero-rescan runs). Do NOT re-launch drills without the Owner's go. Specs: scratchpad s2_mutants.json
  entries 3, 5, 9, 10. Sibling T6 gap for S7: continuation_failed -> replace armed with a retired key.
- S3 SEALED `22b55d3b` (L1 backoff), S4 SEALED `bc4df9dd` (L2), S5 SEALED `866f1ecc` (no-note),
  S6 SEALED `b4fc6d58` (guard text + mission_capsule.TOOL). Last gates: MV2 72/72, CMG 24/24, G23 32/32,
  all 11 suites green. Drill debt S2-S6 all deferred (Owner's go needed).
- S7 SEALED `4f150d0e` (spec 11.6 LIVE in code, T7 partial): audit CLI + C12 fix + MCF 18/18. Two audit
  defects found by the suite and fixed: key read from a ledger field transition() never writes (now from
  the row's epoch), and a blind v2 ledger read INTACT (now UNREADABLE). All 11 suites + CMG 24/24 green.
  CAP2 went 35/36 once in the full run: G24 live-state sentinel moved by a peer's concurrent seal/certify
  at 12:38:08-09 (36/36 alone, same code). Named NOT built: C1/C4/C5/C8/C9, arm->bound audit link,
  11.x source mutants. Pre-commit review was inline (pp-code-reviewer dispatch blocked by a peer's agent).
  T8 stays HELD.
- 2026-10-05 Owner "1. go 2. yes":
  - DRILLS: 16 mutants S2-S7, first pass 12 KILLED; 2 test defects found and fixed in `ab61c628` (C10
    unconfirmed-stop twin, crash-proof cap test; MCF 19/19, MV2 72/72); re-run of the 5 open ones: see
    spec 11.6 "Re-run". Specs: session e3839dd3 scratchpad s2_s7_mutants.json + redo_mutants.json.
  - BG-SPARE: `b2b28818` (stop_owner releases a daemon pooled pid after host done; V-MC-STOP-POOLED-* x5),
    merged as `876be2e4`. DEPLOYED to GEX44 install (~/.claude/skills/claude-power-pack) 339ccaa9 ->
    b2b28818 by ff; backup ~/.claude/backups/pp-predeploy-20261005T110759Z; first try auto-rolled back on
    smoke red, cause measured (below), second try DEPLOY OK; sweeps 13:13/13:18 exit 0. Peer replied.
  - E1 m-f011d7fdebc9 relayed to epoch 3 at 10:57Z BEFORE the deploy (old spare exited by itself); its
    epoch-3 pid 4168684 is itself a bg-spare, so the fix applies to its next rotation.
  - GEX44 env debt (not regressions): V-MC-PLAN-FACTS-REFUSES-OVERLAP red there at 339ccaa9 too
    (unexplained); G23 capped card is cut before <TMP> masking, so it depends on the temp-root length
    (laptop: 12 chars shorter -> +36 B; GEX44 32/32 with a 32-char TMPDIR). Fixing it changes the golden
    = re-capture = Owner decision.

**Next 3 actions.**
1. Ask the Owner: fix G23's temp-length dependence (needs a golden re-capture) or keep the matched-TMPDIR rule.
2. Optional T7 tail: fault rows C1/C4/C5/C8/C9 + an arm ledger row for the audit.
3. Investigate V-MC-PLAN-FACTS-REFUSES-OVERLAP on GEX44 (environment, pre-existing).

**Start.** `git log --oneline -8` (confirm 876be2e4 + ab61c628), then ask action 1.
