---
id: PLAN-K-RESIDENT-PREFIX
date: 2026-10-05
status: APPROVED 2026-10-05 (Owner: "K-local now, rest after reset (Recommended)"; connectors "Budget as account floor (Recommended)")
covers: [ic-pillar-k, resident-prefix, startup-floor, sessionstart-attribution, deferred-tools-budget]
parents: [vault/plans/incremental-cognition-rearm-2026-10-05.md]
defers_to: vault/plans/cognitive-microkernel-brief-2026-10-04.md (steps 11-18, after the weekly quota reset)
done_gate: python tools/test_floor_regression_gate.py exit 0 AND one real K probe passing the strengthened gate for the right reason, reference 2026-10-03 preserved
---

# Pillar K -- resident prefix governance (K-local slice)

The inline ULTRA-PLAN approved in session c59ad762 is the authority; this file keeps its decisions and order.
Ledger of the programme: `vault/programs/incremental-cognition/ledger.json`. K evidence: `evidence/K-reference.md`,
`evidence/K-prg.md` (f4d0b2e7).

## Owner decisions 2026-10-05
- Do NOT reset the 2026-10-03 reference (c77535d4...) to make K green; it stays the historical champion.
- K-local (commits 0-10) now, interactively, ~1-2 probes. Steps 11-18 (host floor, capability / rule / project
  scaling, cold-start canary, discoverability, KV/UKDL/CBR at scale) merge into the deferred cognitive-microkernel
  brief and run under /cpp-gsd-long after the quota reset.
- Deferred-tools growth (+41 claude.ai Gmail 30 / Google Drive 11 names) is budgeted as host/account floor if the
  host cannot scope connectors per session.

## Measured attribution (probe fa7e93cb vs reference 8f983bc6, same cwd, same prompt digest)
- SessionStart +6,436 = one element produced by `hook-dispatcher.js` -> `hooks/session_start_hub.js` (the
  superpowers hypothesis is FALSIFIED: its 3,405-char element is in both windows, same sha). Sections:
  rule-stub re-injection 2,985 (`learning-sentinel.js:442-466`, duplicate of the rules layer), 18-rule
  "delivered by file" pointer 1,046 (`:475`; claims ~148 KB, the file is 30,431 bytes), OWNER_QUEUE 1,536
  (`modules/owner_queue`), recovery verdict 608 (`tools/recovery_epoch_gate.py`), AutoResearch digest 261 (hub ~957).
- Deferred tools +3,378: names only (~37 chars each), 72 -> 113 names; all 41 added are claude.ai connectors.
- UNRESOLVED: whether the reference's dispatcher output `{"continue":true}` was a legitimately empty hub or a
  fail-open (commit 1 decides). Why the gate's correlator left the element unattributed (commit 2).

## Order of work (micro-commits; HEAD re-read before each; pathspec only)
0. This file. 1. Reference comparability of the SessionStart component. 2. Gate: producer provenance for composite
hook output + tests. 3. Resident-rent table from transcripts on disk (per-prompt injections counted per turn).
4. Retire the duplicate rule-stub re-injection (consumer check first). 5. Scope OWNER_QUEUE / recovery / AutoResearch
to the consumer that needs them. 6. Replace or justify the 18-rule pointer (and its false size claim). 7. Deploy
live + one K probe. 8. Deferred tools: host scoping test, else account-floor budget. 9. K champion / accepted
baseline / regression-debt + per-component budgets in the gate, tests. 10. Close K-local.

## Execution log (step, commit, calls, result)
- 0 baf91b69 plan. 1 1ac31957: reference SessionStart=0 was the dispatcher abandoning the hub at its 4,000 ms
  deadline (13:34:37.839Z, 18.6 % free) -> component INCOMPARABLE, reference kept.
- 2 5d82174c: gate read 59/65 exec-form hooks as no_registration; fixed (V-FLOOR-EXEC-FORM-REGISTRATION).
- 3 bf8a7630: rent scan, 40 sessions: 23,249 hook chars/session, 3,131/prompt; per-prompt classes = named debt.
- 4+6 6063b55f: learning-sentinel no longer re-emits rules the harness already loads (-4,031 chars; its emission
  was 4,119 B > its own 4,096 B budget); inheritance test now judges the model boundary. Deployed live.
- 5 b526915a: OWNER_QUEUE / recovery / AutoResearch lines omitted for entrypoint sdk-cli; zero-signal digest dropped.
- 7 b7170420: probe 6eba7a1f ($0.24): rule de-dup CONFIRMED at the model boundary; hub INCONCLUSIVE (abandoned).
- 8 e336e06a: deferred +3,378 = 41 claude.ai connector names; `--strict-mcp-config` measured -> 15 names (38e32976).
- 9 969b39b2 dispatcher names the session in deadline lines (live; confirmed in real lines from 22:09:33Z);
  8169092c + 1cbdaa10 gate: evidenced budgets print as DEBT, degraded windows refused, unattributable = unknown,
  unknown never green nor a champion (60/60); f25d05e3 deferred-tools budget in reference.json (measured fields
  unchanged).
- 10 OPEN: K-local closes on ONE probe whose window is `WINDOW_HEALTH settled` and verdict WITHIN_BOUND with the
  deferred-tools DEBT line. Not run: host at ~15 % free RAM abandons the hub several times per hour, and the slice's
  ~1-2 probe allowance is spent (6eba7a1f, 38e32976). The hub's 4 s abandonment is itself the dominant reliability
  defect (it also drops mission / rollover cards) -> Owner decision.

## Hub critical-path delta (read-only, session 9196ecb9, 2026-10-06, 7-day window)
Sources: `%TEMP%\pp-session-hub.log`, `~/.claude/logs/hook-dispatcher-errors.log`.
- Hub's OWN work never exceeds the budget: 859 DONE runs, elapsed p50 1,161 / p90 1,867 / p99 2,659 / max 3,092 ms, 0 > 4,000.
- Yet the dispatcher lost it 326x: 254 reaped mid-run ("after 4000ms") + 72 never spawned ("before pool", critical
  lane alone 4,013..19,110 ms). The 4 s budget is spent BEFORE the hub's t0: serial `host-memory-floor.js` (critical,
  zero-spawn logic = one `os.freemem()`, but paid as a whole node spawn) + the hub's own node cold start.
- Inside the hub, time up to the `recovery epoch` line p50 967 / p90 1,550 ms vs after it p50 125 / p90 423 ms.
  The comment's "~176 ms" for the recovery gate is stale. 42 runs logged the recovery line and were reaped before DONE.
  The line it re-prints every session is a 3-day-old FAILED verdict (epoch 2026-10-03T01:35:59Z).
- Side defect: kresume autotype armed >1x for 127 of 196 sessions (same sid, seconds apart).

## Hub reliability slice -- Owner decisions 2026-10-06 (all four recommended options)
- Recovery verdict: full line ONCE per interruption epoch, then a one-line reminder until /lazarus or dismiss;
  python runs only when the gate's inputs change (cache keyed on them).
- host-memory-floor: in-process in the dispatcher, SessionStart only, env kill switch.
- kresume double-arm fix is IN this slice (C4).
- SessionStart CHAIN_DEADLINE_MS stays 4000.
Phase-4 audit: `_audit-hub-reliability-2026-10-06.md` (READY WITH CONDITIONS, 9 gaps). Revised commit order (phase 5):
- C0 extract `hooks/session_cards.js`: rollover/restart/work-state/mission functions, NO load-time effects (no
  armHardExit, no stdin); hub + rollover_autotype.js require it; hub re-exports for its tests (gap 3).
- C1 dispatcher, SessionStart only, BEFORE runChain and in-process: BOM-stripped payload once; floor `run()` then
  cards; both outputs UNSHIFTED (floor first, then cards) (gaps 1, 4). Floor + cards leave CHAIN_MAP; one-shot
  consumers (restart unlink, work_state unlink) leave hub main() in the same commit. Switches:
  `CLAUDE_HOST_MEM_FLOOR_INPROC=off` / `CLAUDE_SESSION_CARDS_INPROC=off` restore the spawned path; fail-open require.
  Mission python on the cards path bounded at 1,500 ms (gap 2). `cards DONE sid= n=` line; `session=` on
  CRITICAL-GUARD-INERT (gap 9). Mirror to ~/.claude/hooks with hash compare (gap 5).
- C3 recovery: node predicate decides whether python runs (beacon/boot/epoch facts, pane_map mtime vs judged_at),
  parity test vs epoch.detect_interruption both poles (gap 6); python records `announced_at`, node reads only;
  full line once, one-line reminder until RECOVERED or dismiss (gap 7). Saving lands only once no epoch is open.
- C4 autotype: per-sid atomic wx armed marker, second caller -> why='already armed' (courier reads ARMED), log tags
  caller (gap 8); confirm cause against courier ledger first.
- C5 SessionStart drill pair (starved advisory -> cards arrive; control in budget) + suites listed in the audit.
DONE: suites green, drill both poles, >=20 real SessionStarts with 0 before-pool and 0 lost cards (counted from
`cards DONE`), then the closing K probe in a session with no SessionStart abandonment at all.
Out of slice (named debt): zero-command-bootstrap / first-time-project double run; gsd_mission.py:2730 doc drift.
- C0 4bbf6796: cards in `hooks/session_cards.js` (load: 11 ms, 0 active handles); hub imports + re-exports, behaviour
  unchanged; live on the next SessionStart (hub is served from this checkout). Suites: mission 8/8, owner-facing 8/8,
  rollover-cwd 13/13, session-start-cost 9/9, restart-kclear 13/14 (baseline-identical), kresume-autotype 32/33
  (V-KRA-D-FOCUS-TYPED daemon 6 s window, unpaired with baseline). Another session's uncommitted hub hunk
  (stdin ceiling 12 s -> 50 s) left in the tree, not committed by C0.
- C1 (repo; live mirror pending Owner): dispatcher `sessionStartInProcess` runs floor + `composeCards` before the pool,
  outputs prepended, its time counted against the 4 s deadline (runChain opts.startedAt); hub skips cards when
  PP_SESSION_CARDS_DONE=1 (`hubCards`), so a hub deployed before the dispatcher still emits them. Switches
  CLAUDE_HOST_MEM_FLOOR_INPROC / CLAUDE_SESSION_CARDS_INPROC; INERT lines carry session=. New suite
  `tools/test_session_start_inproc.js` 19/19 (hermetic tmp HOME/TEMP; e2e via a stand-in hub), 3/3 mutants killed.
  Observed in the e2e: at 1.9 % free a NO-OP stand-in hub was reaped by the 4 s deadline in 3/3 attempts while floor +
  card arrived (V-SSINPROC-E2E-CARDS-SURVIVE-ABANDON) -- the residual cliff is one node spawn, not hub work.
  restart-and-lag 16/17 (V-HUB-REGISTERED stale since the 2026-09-22 fold), session-start-cost 9/9.
- C1 committed 755de1f6; LIVE ~2026-10-06T12:37Z (Owner "y"): ~/.claude/hooks/hook-dispatcher.js == repo
  (B74D5B483555CDA4). Backup of the previous live file (6A00D9B6E6AC7E75):
  ~/.claude/backups/dispatcher-c1-20261006/hook-dispatcher.js -- rollback = Copy-Item it back.
  DONE count (>=20 real SessionStarts after 12:37Z): `%TEMP%\pp-session-hub.log` lines `cards DONE via=inproc sid=`
  (one per start; `via=hub` means the lane did not run) vs `~/.claude/logs/hook-dispatcher-errors.log`
  `[SessionStart-chain] CHAIN-DEADLINE-ABANDONED before pool` (target 0) and `INPROC-*-FAILED` (target 0).
