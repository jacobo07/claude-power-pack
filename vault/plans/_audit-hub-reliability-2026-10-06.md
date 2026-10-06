---
id: AUDIT-HUB-RELIABILITY-2026-10-06
date: 2026-10-06
auditor: oneshot-architect-auditor (phase 4 of /ultra), persisted by parent session 9196ecb9
subject: vault/plans/pillar-k-resident-prefix-2026-10-05.md -- "Hub reliability slice"
verdict: READY WITH CONDITIONS (gaps 1-4, 6 blocking; 5, 7-9 in-commit)
verified_by_parent: gap 3 (session_start_hub.js:132 armHardExit at module load), gap 4 (hook-dispatcher.js:1545-1552 companion outputs pushed AFTER chain outputs)
---

# Phase-4 audit -- hub reliability slice

1. **C2 spawned cards step recreates the before-pool cause.** Critical lane is sequential with no deadline
   (hook-dispatcher.js:1017-1018, :1055-1073). A cards child requiring the hub is a heavier cold start than the
   floor it replaces. Fix: cards run IN-PROCESS in the dispatcher from a side-effect-free module, before runChain.
2. **Mission card is not fs-only.** session_start_hub.js:535, :561-575 -- execFileSync python, 5,000 ms timeout >
   4,000 ms deadline. Fix: bounded budget on the cards path (<=1,500 ms; ack is written before the git reads).
3. **Requiring the hub arms process.exit(0).** session_start_hub.js:132 armHardExit at load; hook-utils.js:106-110
   timer not unref'd; cleared only by the hub's own readStdin. Fix: new module with no load-time effects holding
   rollover/restart/work-state/mission functions; hub, rollover_autotype.js and the cards path require it; hub re-exports.
4. **In-process companion puts the floor warning LAST.** hook-dispatcher.js:1545-1552 pushes after chain outputs;
   mergeOutputs concatenates in order. Fix: SessionStart-only call before runChain, unshift its output; test that
   the floor context is first when CLAUDE_HOST_MEM_CRIT_MB is forced high.
5. **C1 switch/BOM/mirror.** Kill switch unnamed (existing CLAUDE_HOST_MEM_FLOOR=off disables the floor entirely);
   dispatcher :1548 parses without BOM strip; host-memory-floor.js lives only in ~/.claude/hooks; live dispatcher is a
   mirror (Copy-Item step, HR-001). Fix: CLAUDE_HOST_MEM_FLOOR_INPROC=off restores the spawned step; strip BOM once;
   fail-open require; explicit mirror step with hash compare.
6. **Recovery cache keyed on file hashes never hits or is unsound.** Inputs: power_beacon.json (epoch.py:167, rewritten
   every SessionStart by cpc_register), boot time (epoch.py:82), recovery_epoch.json (:208), pane_map.json
   (gate:86-91), pane_map_history listing. Writes: open_epoch (:270), record_reentry (gate:131-132), record_verdict
   (:290, closes the epoch). Fix: node-side predicate -- run python iff (a) beacon kind==active AND boot time > beacon.ts
   AND epoch.interrupted_at != beacon.ts, or (b) epoch open AND pane_map.json mtime > epoch.judged_at. Parity test vs
   epoch.detect_interruption, both outcomes. NOTE: while an epoch is open (today) pane_map churn keeps python running;
   the saving lands once no epoch is open.
7. **Once-per-epoch flag needs one writer.** recovery_epoch.json is written only by epoch.py durable_write_json.
   Fix: python records announced_at when it prints the full line; node reads read-only; accept up to N full lines at
   a multi-pane reboot or use an atomic wx marker keyed by interrupted_at.
8. **Double autotype arm root cause (INFERRED).** Two callers by design: rollover_autotype.js:59-63 (source=clear) and
   kresume_courier.py:191 (+3 retries, :205-217); armKresumeAutotype (hub:379-424) overwrites the flag, relaunches the
   daemon and logs every call; daemon single-flight lock is check-then-write (ps1:62-71). Fix: per-sid atomic wx
   "armed" marker; second caller gets why='already armed' and the courier records ARMED; log line tags the caller.
   Confirm with courier ledger rows at matching timestamps.
9. **"0 lost cards" has no per-session instrument.** Hub note()/DONE carry no sid (hub:97-106, :1295);
   CRITICAL-GUARD-INERT lacks session= (dispatcher:1022-1024); floor_regression_gate.py:992, :1023-1026 marks any
   SessionStart abandonment degraded. Fix: `cards DONE sid=<sid> n=<k>` line; session= on INERT; closing K probe still
   needs a session with no SessionStart abandonment at all.

## Clean / informational
- Floor in-process is safe in substance: run() is one freemem/totalmem + sync log append, exported (:122), CLI gated by
  require.main (:124); test-host-memory-floor.js requires (:25) and spawns (:93, :114) -- both stay valid.
- Ordering: index-ordered reduction keeps cards first; recovery-before-cpc holds while both stay in the hub process.
  One-shot consumers (restart marker unlink hub:200, work_state unlink :484) must leave hub main() in the same commit.
- Suites to update: ~/.claude/hooks/tests/test-sessionstart-context-routing.js:57-61; new SessionStart drill pair beside
  test-chain-deadline.js; test-host-memory-floor.js (+ in-process test); tools/test_kresume_autotype.py:199-216,
  :275-292; tools/test_kresume_courier.py:274; tools/test_hub_mission_start.js:16, test_restart_and_lag.py,
  test_hub_owner_facing.js; tools/test_session_start_cost.py:61, :163-179; tools/test_hook_stdin_liveness.py:146;
  /liveness for the new module. test_floor_regression_gate.py:1135-1169 unaffected.
- Pre-existing, out of slice: zero-command-bootstrap.js and first-time-project.js run twice per session (settings.json
  846/859 + hub :1275-1276). Doc drift: tools/gsd_mission.py:2730.
