# S1 PARTIAL (2026-10-09, budget breaker at 61 calls; NOTHING COMMITTED, receipt not written)
Working-tree changes (uncommitted) in pp-gsdx-factory-2: modules/provider_routing/ledger.py (settle_stopped, correct),
tools/mission_spend.py (goal-settle, goal-correct, _real_console_stdin: Windows NUL reports isatty True),
tools/mission_steward.py (new: R1/R2/R3, kill switch), tools/gsd_mission.py (_steward_rows helper, called at the end of
supervise() AND in its early-return path -- terminal-only estates return early, so one end call would never run), tools/test_mission_steward.py.
Gates: STEWARD_PASS=18/18; regression GOAL_PASS=45/45, ADM_PASS=44/44.
NEXT (exact): (1) in test_mission_steward.py make V-STEWARD-DUP-PASS-ONE-EFFECT replay the STALE list `stale`
(captured; second pass currently uses run(c)) via st.steward_pass(stale, ...) in try/except; (2) run the two mutation drills
(settle_stopped closes only leases -> -SETTLE-CLOSES-ALL red; steward skips re-read -> -DUP-PASS-ONE-EFFECT red) with tools/mutation_drill.py;
(3) pathspec commits (ledger+CLI, steward+hook, test); (4) write vault/specs/gsdx-factory.RECEIPT-S1.json; (5) coordinator lands S1 live.
Decisions: R1 acts when owner verdict is not ALIVE/WAITING_HUMAN (UNKNOWN acts; settle is a watermark). R3 syntax: `successor:` line or JSON key.
(The S1 PARTIAL note above is SUPERSEDED: every step in it is done; see ACTIVE below.)

# PARKED (2026-10-10): Owner "put the rest of the mission in the backlog of claude power pack"
The programme is in the PP backlog as `vault/plans/deferred-backlog.md` D15 (PP 1a933cba): done list, forecast (12.7M
expected remaining), open debt, activation criterion. chain.json: AGMIN..PLAN-4 moved to `parked` (unarmed); the tick
reports `complete` and keeps settling leases. Spent 8,817,916, open 0. RESUME = Owner says so; in a fresh pane move the
`parked` units back into `units` in order. The ACTIVE section below is history up to 2026-10-09.

# ACTIVE (2026-10-09 ~15:00): GSD X Reconstruction Factory, Master Plan v1 APPROVED (Owner "y")

Plan: `vault/plans/gsdx-factory-master-plan.md` (68d21301). Envelope 40M, hard ceiling 55M, inside goal
gsdx-factory-2 (ledger cap 100M). Canonical factory = workstream recon-factory in `Apps\recon_work\wt_keosdtk_home`
(branch keosdtk-home, 569 dirty paths there: never touch). Full WSR out of scope. Never Set-Location into a goal root.

W0 DONE (zero model): S1 commits 55ced1e8 006c8b7b 2a3c3bd0, RECEIPT-S1 (STEWARD 18/18, GOAL 45/45, ADM 44/44, both
drills KILLED). Ledger: gsdx-factory-2 used 2,839,056 = measured, open 0. Old goal: phantom closed; 530d9700 hold
232,321 kept (liveness UNKNOWN).

Owners, do not write their files while their units run: ce-lifecycle-v3 (`Apps\pp-ce-lifecycle-v3`: gsd_mission.py,
session_budget_guard.js, ledger.py, mission_spend.py; it adopts S1 via WU-S5b/S5c then installs live via WU-INST2),
cost-collapse (route_admission.py; laptop live tree holds its uncommitted E4a edits), gen3 (recon worktree).

RUNNING WITHOUT A COORDINATOR (since ~15:30): L1 armed m-4e161ffd6420 (WU-L1.md, slim-t2, ADMISSIBLE), launched by the
5-min sweep. Successors are armed by `tools/gsdx_chain.py tick` (Task PP-GsdxChain-Tick, 15 min; decisions in
~/.claude/state/gsdx-chain.jsonl, wrapper rc in gsdx-chain-tick.log) from `vault/specs/gsdx-factory/chain.json`:
L1 -> PLAN-1 (planner epoch: compiles the next <=4 units from l1/GRAPH.md, appends them + PLAN-2). Kill switch
CPP_GSDX_CHAIN=off or disable the task.
NEXT (only if the chain row says so): `stopped_without_done` = a unit ended PARTIAL/HALTED -> read its receipt/partial,
compile a residual packet, add it to chain.json; `refuse_envelope` or a receipt with `owner_needed` -> Owner.
Open: W3 waits on ce-lifecycle-v3 WU-INST2-receipt.md; W5 GEX44 port (no admission/dossier/steward/guard there; read
DEPLOY hard rules first).
Coherence anchor: `git log --oneline -1` here at or after the RECEIPT-S1 commit.

# PRIOR (2026-10-09 morning): gsdx-factory steward recovery (worktree pp-gsdx-factory-2, goal gsdx-factory-2)

Plan (binding, Owner "y"): live tree `vault/plans/gsdx-steward-recovery-plan.md`; handoff `vault/plans/gsdx-r0-handoff.md`.
Goal ledger: `gsdx-factory-2`, cap 100M, root = this worktree. Old goal `gsdx-factory` is over cap by LEDGER_MISATTRIBUTION
(coordinator Set-Location into its root booked a whole session); a ledger correction op is S1's job.
Rule: a coordinator NEVER Set-Locations into a goal root; use `git -C`, absolute paths, child-process cwd only.

State: R0 / A-G1 DONE. Tool+test 0573e610; obligations+dispositions f923c24a; receipt
`vault/specs/gsdx-factory.RECEIPT-AG1.json`. dispose --check rc=0 (22 disposed, 0 undisposed, 5 UNKNOWN), DISPOSE_PASS=17/17,
canary A1/B1 PASS. Coordinator steps done: sid 6305f97c settled at 3,276,310 on old goal (leaked 839,065 lease closed);
m-fa18e2b8b44d under OWNER HOLD pointing at the receipt (gsd_mission has no terminal verb). Side effect for S1: `goal-renew
--per-call 0` falls back to the 150,000 default, so the refused renew booked a phantom `final` hold for the dead sid
(gsdx-factory:6305f97c...:6). No release op exists; old goal reads used 14,020,691 of which ~10.4M is misattributed.

S4 DONE (PASS, `vault/specs/gsdx-factory.RECEIPT-S4.json`): slim-t2 ran Read->Write->PowerShell commit (bfb4c8b3) with the
guard live, and the guard denied the Write at stop 5,000. Floor 17.5K vs 121K top-level; whole unit 73,648 tokens. Its two
probe sids hold 838,615 of open lease on this goal (real 130,061) until S1 can settle a finished sid without a new lease.
S1 ARMED 2026-10-09 ~09:10Z (Owner option "b": new tools/mission_steward.py, one guarded call in supervise()):
mission m-ffb75e73f813, slim-t2/sonnet, packet vault/specs/packets/WU-S1.md (4e34c258), route-S1.json ADMISSIBLE
(need 763,246 flat-floor; target 2.5M, stop 4M). It superseded AG1 (m-fa18e2b8b44d now HALTED). Launched by the live
5-min sweep; result = vault/specs/gsdx-factory.RECEIPT-S1.json. Check `gsd_mission.py status`, never poll with a model.
After S1: coordinator lands it on live, then goal-settle the open probe/phantom holds; then S2 (slim-t2) / S3 -> L1.
A-G2..A-G5 are recompiled from L1 + S4, never re-armed from stale packets. Coherence anchor: `git log` here at or after f923c24a.

# PRIOR (2026-10-08): cost-collapse + expected-completion admission (worktree pp-cost-collapse)

Specs (binding): `vault/specs/cost-collapse.md` (T1-T7) and `vault/specs/expected-completion-admission.md`
(APPROVED, Owner "y": D1 program cap 85M, D2 land live at E4, D3 growth term authoritative after canaries 1-4).
Goal ledger: goal `cost-collapse`, cap 69,774,423 (85M - metered T1 11,135,030 - T2 4,090,547), root = this tree.

State: T1 done (f3b503e6, GRAMMAR 56/56; 11.14M vs 8M). T2 done (2b5b0ea5, AUTOPSY 42/42; 4.09M vs 5M). Their
mission records are superseded (m-1a51d97b4a15 HALTED, m-b76843b319af superseded by E1). E1 armed + admitted as
m-66e1c23cae19 (WU-E1.md, route-E1.json, need 4,446,486 <= 5M); the 5-min live sweep launches it. T3 FROZEN until
E3's dependent admission or E4 landing; WU-CC3.md is committed (540ace84) but must be re-admitted under E1's model.
gsdx-pcc m-53847a002b65 stays held until T7.

Chain defect (audit A1): the live gsd_mission.py has no packet gate, so every finished packet worker gets a "COPY"
continuation and a stuck LAUNCHING record; each E-worker therefore supersedes its own mission when arming the next.

Next: (1) if E1 has no receipt `vault/specs/expected-completion.RECEIPT-E1.json`, check `gsd_mission.py status` for
m-66e1c23cae19 and the sweep log `~/.claude/state/gsd-long-run-sweep.log` -- do not poll with a model;
(2) E2 -> E3 -> E4 run as a packet chain; (3) after E4: reconcile T2, re-admit T3 (expected split T3a/T3b).
Coherence anchor: `git log --oneline -1` in this tree is at or after 2e2047c2.

# POST-INCIDENT STATE (2026-09-20) — /cpp-gsd-long: what is settled, what blocks C7

Commits this wave, all pushed: `15bcdbe` `ba540f2` `27a7094` `d92bcc9`.

**DO NOT RE-LITIGATE WITHOUT NEW EVIDENCE — three premises measured FALSE:**
1. **The host DOES write `compact_boundary`.** Three rows in session 37cfb187's
   transcript, newest `2026-09-20T12:43:08Z`. F2 as written is retracted; the one
   `compaction_unobserved` was a compaction that never happened. Do not weaken C4.
2. **There is no rearm deadlock.** The advisory flag cleared on its own and the
   next Stop resumed at `used_pct=24.0`.
3. **The overlay does not fire every Stop.** It is once-per-session AND 180 s
   throttled. A `used_pct=?` heartbeat line is the overlay branch; every other
   line is the normal path.

**CLOSED (`15bcdbe`).** `_run_inner` returned the auto-reset advisory before the
whole continuation path (used_pct stamp, endpoint refresh, resume confirmation,
rearm, post-compaction resume, snapshot, crossing, `/compact`). Once-per-session,
so one Stop — but it fires on context pressure, the same condition that produces
a crossing. Armed runs now keep the path; unarmed behaviour unchanged.
`tools/test_watchdog_overlay_precedence.py` 4/4, mutation 3/4 on its own
assertion, SHA-256 restore verified.

**THE BLOCKER IS F5, NOT THE WALL.** The run re-entered itself with zero human
input (`resume_requested` → `resume_dispatched` → inbox ack `status:"sent"`,
`terminal:"claude"`, correct `window_cwd`) and `/gsd-autonomous` executed — but
**no user row records the submission**, so `user_issued_command_since` reads
False and `resume_confirmed` cannot fire. On 2026-09-19 the same flow left
`type=user, isMeta=True` at `09:08:06.552Z` and confirmed. Already excluded by
measurement: late flush, the 8 MB window, the time bound. Control: the Owner's
typed messages ARE recorded. **Do not weaken the C6 oracle to close this.** The
discriminating observation is the next watchdog-initiated crossing, watched live
end to end.

**Also true and easy to misread:** the 2026-09-20 12:43 compaction was run by the
Owner. Every rung after it behaved, but an Owner-triggered crossing cannot count
toward C7.

**Gate state at this tree:** GSDLR 93/93 · GSDAC 26/26 · OVLY 4/4 · OVERLAY_GUARD
4/4 · REARM 8/8 (names this run's wall `(35,40,30)` as accepted). ACPS is
**non-attributable**, not green and not a regression: with and without the change
the failure SETS differ in both directions, 6 fail in both, and two runs of
identical code gave 31/38 and 32/38 — measured at 610 processes / 20 concurrent
claude sessions / 1.9 GB free. A valid ACPS verdict on a quiet host is owed.

**Marker:** armed `2026-09-20T11:23:29Z`, `cycles 1/12`, `max_hours 24`, wall
`{35,40,30}` stamped in the marker, mission FRESH (5/5 terms).

**Two-pane positive leg, negative half: DONE and live.** 33 other live panes
examined with the product's own predicate at a real delivery; zero touched. No
window opened, no Owner action. Pane A's half is blocked on F5, not on a pane.

# POST-INCIDENT STATE (2026-09-18, read before the router below)

**Hook substrate restored.** All six dispatcher chains were dark 2026-09-16 20:02 → 2026-09-18
13:55 (an agent's exec-form rewrite of `~/.claude/settings.json` dropped every `--event=`).
Full report: `vault/incidents/2026-09-16-hook-registration-identity-loss.md`. Commits
`9b536df` `e58b6af` `5dfbda4` `098f564` `f939aef` `a8b5f0a`, pushed.

- Canonical settings generation: sha16 `49402DC084DCC5F7` (repaired 13:55:50). Pre-repair
  evidence kept: `settings.json.bak-20260918-135550-pre-incident-repair`.
- Check it any time: `python tools/test_hook_registration_integrity.py --live` (must be 15/15);
  the launcher also checks at every start and logs `state/session-config-generations.jsonl`.
- `state/dispatcher-no-event.jsonl` non-empty = a registration lost its identity again.
- Hooks reload LIVE in running sessions on this build; no stale-session restart program needed.

Do NOT re-litigate without new evidence: the writer (session `2174d82b`, ad-hoc script; not
fix_conhost, not settings_merger, not Orca); exec form stays; launcher check is detect-only
by decision (GSDX-I05) — no auto-restore.

**GSD X resumes at the Context Watchdog hot-path slice.** Baseline is GSDX-I11 (real
sessions only: median 3,132 ms / p90 4,974 ms per Stop). Never use synthetic rows
(`gsdac-*`, `gsdlr-*`) or the dark window (GSDX-I09).

**Action 1 partly answered without timing (2026-09-19, `3c49f86`).** The host sat at 4% free
memory, where this estate has measured 17x drift, so nothing was timed. Two load-independent
instruments were used instead and both hold on any host:
- Static profile of `CHAIN_MAP['Stop-chain']`: 25 members, 0 missing, 327 s of serial budget;
  **6** are both unconditional and transcript-scaling (`lazarus-snapshot`, `mark-live-session`,
  `research-intent-detector`, `session_snapshot_stop`, `output_contract_stop`,
  `ceps_promote_stop`). That is a LOWER BOUND: "a gate exists" is not "the gate fires", and
  `closer-guard` is marked gated while measuring 644-1245 ms.
- `logs/context-watchdog.log`, which real Stops write themselves — 256 real rows / 106 sessions
  after excluding 663 synthetic `gsdac-`/`gsdlr-` rows and the dark window. **`pass` median
  1,555 ms vs `block` 233 ms** (p90 4,930 / max 15,007 on a pass at 45% usage). 92 of 256 are
  multi-second passes with no crossing. The comment at `hook-dispatcher.js:173` claiming 844 ms
  for an ordinary Stop is wrong against real sessions.

**Fixed:** `_orchestrator_overlay` imported `auto_reset_orchestrator` ABOVE its throttle and
no-nag flag, so every Stop paid the import chain forever. Guards hoisted; pinned by
`tools/test_context_watchdog_overlay_guard.py` 4/4 (counts imports, never a clock — valid on a
starved host), mutation 2/4, `test_gsd_autocompact.py` 26/26.

# POST-INCIDENT STATE (2026-09-19 evening) — THE LONG-RUN CAUSAL MODEL CHANGED

**The 7-hour KobiiCraft stall was NOT a hung Stop hook, and not a hung job.** Session
`de7f3c91` (KobiiCraft Core Files, Phase 13). Measured, not inferred:

- 12:38:58 the mission backgrounds a STATE.md blocker read at the harness 120 s timeout.
- **12:41:58 the job COMPLETES** — `tasks/b4haxctvm.output`, 3,095 bytes, exit 0. Its content:
  all four blocker sections **absent**, i.e. "nothing is blocking you, proceed."
- 12:41:58 and 12:44:45 two `<task-notification>` rows are **enqueued**.
- The turn ends. Nothing re-invokes the model. **The queue does not pump itself.**
- 19:50:02 (7 h 08 m later) the notifications are delivered, when the Owner returns and types.
- 20:06:59 the reply is `No response requested.` — a relapse of CLAUDE.md rule (L).

Stop `4/5` is `gsd-context-monitor.js` (timeout 10 s, and it carries its OWN 10 s stdin guard),
so it is a poor 7-hour suspect; `4/5` was the last-rendered frame of a turn that had already
ended. **Do not go looking for a wedged hook without new process evidence.**

**H1 IS REFUTED AS EVIDENCED — and this corrects a claim made in chat on 2026-09-19.**
It was reported that KME "survived 11 compactions unattended, AUTO=11 / HUMAN=0". That was an
instrument failure: the classifier listed `<command-name>` as *synthetic*, so every `/compact`
the Owner typed scored as AUTO. Measured properly across the whole store:

    439 compact boundaries in 131 transcripts -> 419 confirmed MANUAL /compact, 20 window
    artifacts. 3 of 3 hand-checked candidates (including one inside KME's own bb4e529f,
    whose /compact row sits at +9 rows) were MANUAL.

**Zero native auto-compactions have ever been observed in this estate.** But note the selection
effect before concluding the host cannot do it: the watchdog fires at 60/70% and a human
compacts first, so **nothing has ever been allowed to reach the native wall.** H1 is therefore
UNTESTED as a host capability, not disproven. The experiment is cheap and decisive and is the
next big unknown — a disposable session with the watchdog off, run to the real wall.

**H2 IS SUPPORTED.** `closer-guard` measured 867 runs / 385 blocks, live. Stop `decision:block`
re-invokes the model in the same session. That primitive is proven in production here.

**H3 is supported but did NOT cause this stall.** Three `auto-compact-refused-*.flag` files,
zero deliveries; `8915b3d5` (KobiiCraft, 71%) went dead 23 h after its refusal. (That session id
is real — it had been flagged in chat as possibly invented. It is not.)

**LANDED (`4d45b7a`).** `hooks/gsd_stop_continuation.js` — bounded autonomous TURN continuation.
Second on Stop-chain, critical lane, after `closer-guard`. 17/17 both poles, 2 mutations caught
on their own assertions, SHA-256 restore verified, and driven END-TO-END through the real
dispatcher (`runnable=20/26`, reason survives the merge, negative control clean).
**It is OPT-IN and currently inert:** it does nothing unless the autorun marker carries
`continuation: "stop-block"`. 11 markers existed when it landed; none opt in. Kill switch
`CPP_GSD_STOP_CONTINUATION=off`. Anti-loop = A SECOND BLOCK REQUIRES A CAUSAL DELTA.

**LANDED (`1df113f5`, KobiiCraft repo).** `agents_installed:false` with all 35 agents present was
Orca exporting `CODEX_HOME` into Claude Code panes, so GSD's host-detection rung reported
`codex` and checked a directory that does not exist. Fixed at `config.runtime`, never in
`gsd-core` (MANAGED tree — edits are re-staged away). Same file finished the long-run threshold
restore (12/8 -> defaults) that `_pp_long_run_backup` proved was owed.

Next actions for the long-run track, highest value first:
1. **The native-wall experiment.** Disposable session, watchdog off, run to the real context
   wall. This single measurement decides whether the whole compact-delivery apparatus lives or
   dies. Until it runs, do not retire the legacy path and do not flip the default.
2. **A/B**, then flip `continuation: "stop-block"` on by default only if it wins.
3. `Stop-chain` still has **no `CHAIN_DEADLINE_MS` entry**. Adding one needs its own wall-clock
   measurement AND an argument about what failing open costs — the dispatcher states that bar
   itself. Note the Stop-chain blockers are `closer-guard` and `zero-issue-gate`, i.e.
   ACCOUNTING and dead-screen, not the HR-SECRET-001 boundary, so the argument differs from
   PreToolUse. Blocked on host headroom (6.4% free at time of writing).
4. Four GSD projects still lack `runtime` in `.planning/config.json` and misreport agents the
   same way: `gsd-long-smoke`, `Orca X`, `ABSW2-Wii`, `KobiiSports Resort`. Deliberately NOT
   patched — the Owner does run Codex sessions, so a blind `claude` would create the mirror bug.
   Apply per project when next active.

Older actions from the watchdog hot-path slice (still open):
1. **Explain the pass/block asymmetry — still open.** The overlay runs FIRST for both outcomes
   (`context-watchdog.py:963`), so the import defect does not by itself explain why the cheap
   path costs 6.7x the expensive one. Do not assume the fix closed it. Suspect next: what
   `block` short-circuits that `pass` does not.
2. **Time it once the host has headroom** (>8 GB free, medians not single readings, bracket the
   headroom on BOTH sides of the sweep — a pre-flight reading cannot see contention the sweep
   creates). Quantify what the hoisted import actually cost; no timing claim exists yet. Then
   take the 6 suspects above in order.
3. Make the synthetic drivers stop writing the production watchdog log (override HOME and
   USERPROFILE, see `tools/test_hook_replay_isolation.py`) — `tools/test_gsd_autocompact*.py`
   has been quiet since 09-18 17:57, so that pane is done and this is now unblocked. Note the
   synthetic rows already outnumber real ones 2.6:1 in the log.

# ACTIVE-TASK ROUTER (read first)

**GSD X — Invocation Independence is LIVE (2026-09-16). Do not re-litigate this without new evidence.**
GSD X computes the ExecutionOS Lite tier from a prompt's measured evidence, ambiently, on the real
`UserPromptSubmit-chain`. Live-served branch `feature/knowledge-acquisition` @ `ee54540` (pushed).
Integration branch `integrate/gsd-x-landing` @ `42dd006` (pushed).

Settled by measurement — do NOT rebuild these conclusions:
- There is **no installer** from repo to live. `~/.claude/skills/claude-power-pack` IS the main git
  worktree, and the live dispatcher resolves `path.join(__dirname, '../skills/claude-power-pack/...')`.
  A committed file is live-served. 31 other repo-owned hooks already arrive this way.
- `~/.claude/hooks` is **not under git** (79 hooks; only 15 also exist in the repo). It is the executing
  authority. `hooks/hook-dispatcher.js` in the repo is a **snapshot**, not an authority; its only
  consumer is `tools/test_dispatcher_drift.js`. Do not try to make the repo copy execute — the
  dispatcher's relative paths are resolved from `~/.claude/hooks`, so running it from the repo would
  break all 31 registrations plus the 64 live-only hooks.

Proven at the production invocation (`node hook-dispatcher.js --event=UserPromptSubmit-chain`):
heavy prompt → FORENSIC (secret_containment, cascade_prevention), 9000 ms of a 15 s timeout ·
trivial prompt → silent, heartbeat still advanced (judgements 43→45, LIGHT 10→11) so VALID_SILENCE is
distinguishable from a dead hook · `CLAUDE_GSDX=off` → 0 emissions, judgements unchanged, chain
unharmed. Drift gate `DISPATCHER_DRIFT=3/3` byte-identical. `test_gsd_x.py` 14/14,
`test_gsd_x_timeout_visibility.js` 9/9.

**OPEN, in ROI order:** (1) U05 is only half-measured — per-hook timings inside the chain were not
broken out, only chain wall time; (2) F06 contract-corpus coverage never started; (3) U01 not
re-evaluated against the now-live architecture; (4) informative rate is recorded by the heartbeat
(29/45) but was not analysed for false escalations; (5) concurrency 4 on this chain is still
**inherited, not proven** — shared stdout/heartbeat surfaces unvalidated.

**ACTIVE line (2026-09-13): USEA — Universal Software Engineering Architect.** Phases I–VI
are sealed and green; the one thing the programme still has no evidence for is whether the
constitution changes engineering OUTCOMES. Resume it from
`vault/knowledge_base/usea/USEA_RESUMPTION.md`. Read its §1 before acting on any brief that
asks you to reconcile `UASE` with `USEA` — they are two different systems and one of them
was rejected.

**ACTIVE build (2026-07-12): DAIF — Duplicate-to-Advantage Institutional Fabric.**
Resume it from `vault/knowledge_base/d2a_fabric/DAIF_RESUMPTION.md` → then `DAIF_INDEX.md` →
`DAIF_CANONICAL_MAP.md`. Owner re-spec approved; 22 candidates → 8 sovereign datasets; building DAIF-00.

**PARALLEL build (2026-07-19): Crawl OS.** Separately tracked, not a replacement for the DAIF
ACTIVE line above. Resume it from `vault/knowledge_base/crawl_os/CRAWLOS_RESUMPTION.md` →
`CONSUMER_DECLARATIONS.md`. STOP #1 and Fase 0 (invocation model, consumer declarations) are
Owner-approved; dataset 01 (Constitutional Architecture) is in progress.

**PRIOR task below — SQI — is SEALED (SCS C90/C91/C94) and pushed.** Its content is preserved verbatim;
its backlog (threshold inventory §15.7, pointing `run_sqi` at the estate, surfacing the 4 PP findings) is
unstarted but lower priority than the active DAIF build. Do not delete the SQI section.

---

# RESUMPTION — SQI / UQIOS

You are continuing work on the **Sovereign Quality Intelligence (SQI)** axis in
`C:\Users\User\.claude\skills\claude-power-pack`. Read this file, then the index, then execute
Block 4. Do not re-plan. The architecture is approved and sealed.

---

## 1. What this is

SQI is the **Verification axis** of Claude Power Pack: it governs whether the executable reality
is actually verified, and what evidence licenses that claim. It is the ex-post counterpart to DRK
(decisions, ex-ante) and ACIS (epistemic status of claims).

It is now **two layers**: a corpus (doctrine) and engines (enforcement).

- Corpus: `vault/knowledge_base/sqi/` — 4 datasets, 80 Parts, 108,598 words.
- Engines: `modules/sqi/` — scanner, qualifier, reconciler. `tools/run_sqi.py` runs all three.
- Architecture: `vault/plans/sqi-uqios-architecture-2026-07-12.md`
- Engine contract: `vault/plans/sqi-reconciliation-engine-2026-07-12.md`
- **Binding ontology — read before authoring any Part:** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`
- Honest gaps: `vault/knowledge_base/sqi/SQI_COMPLETION_REPORT.md`
- Latest seal: `vault/knowledge_base/sqi/sqi_scs_c91.md`

---

## 2. Exact state

**SPEARHEAD CORPUS (SCS C90) AND EXECUTABLE LAYER (SCS C91) ARE BOTH COMPLETE AND PUSHED.**
Do not rewrite either.

- `sqi_00_constitution_v1.txt` · `sqi_01_repository_reality_v1.txt` ·
  `sqi_02_test_reach_v1.txt` ★ · `sqi_03_environment_qualification_v1.txt` — 20/20 Parts each.
- `modules/sqi/repo_reality_scanner.py` · `environment_qualifier.py` · `reconcile.py` ·
  `baseline_guardian.py` · `weakening_detectors.py` · `weakening_baseline.py` ·
  `discovery_rules.json` (**governed artifact** — widening its `exclusions` is the census trap;
  **narrowing its `assertion_vocabulary` is the inverse trap**, and blinds the weakening gate).
- `vault/audits/sqi_weakening_baseline.json` — per-file `{assertions, mocks, cases, sha256}`,
  NOT environment-keyed (the counts are static; keying them would let a host change erase them).
  Currently: **101 files, 2,158 assertions, 23 exit-code-gate (UNKNOWN), 9 verifying nothing.**
- `tools/run_sqi.py` → `vault/audits/sqi_report_<date>.md` + JSON sidecar + the guardian verdict.
  **It exits non-zero on an unexplained decrease.** `--accept-baseline --reason … --author …`
  is the only path that may LOWER a baseline.
- `vault/audits/sqi_baseline.json` — per-root, env-keyed, identity-carrying. Currently: **76**
  executed in root `pytest tests/`, 101 authored, reach 3.0%, env `b5ec3ed51c2f23b1`.
- `tests/test_sqi_engine.py` — 33 tests, **inside** `tests/` so the engine and the guardian are
  reached. It is there because the engine reported SELF-REACH ZERO about itself.
- `sqi-runner` in the D1 Liveness Ledger. CO-12 signal kind `sqi_reconcile`.
- UKDL: `T-SQI-PARALLEL-SYSTEM-001`, `PR-SQI-COMPOUND-INTELLIGENCE-001`,
  `T-SQI-SELF-EVOLUTION-UNCONTROLLED-001`, `PR-SQI-EXECUTABLE-GOVERNANCE-001`,
  `T-SQI-FINDING-FABRICATION-001`, `T-SQI-DIRECTORY-NOT-MANIFEST-001`,
  `PR-SQI-SIGNAL-MUST-GATE-001`, `T-SQI-RATIO-GATE-REWARDS-DELETION-001`,
  `T-SQI-SCOPE-LAUNDERING-001`.

**Coherence anchor — these must agree or something has drifted:**
`python tools/test_sqi.py` reports `SQI_PASS=53/53` and `datasets=4` · `pytest tests/` reports
**86 passed** · `SQI_INDEX.md` marks 4 datasets `COMPLETE` ·
`vault/knowledge_base/sqi/sqi_*_v1.txt` is exactly 4 files · `modules/sqi/*.py` is exactly 7 files
(6 engines + `__init__`).

**What the engine measures about this repository right now** (do not re-derive; re-run it):
Test File Reach **3.0%** (3 of 100) · Orphaned **97** · Executed Protection Ratio **1.6%** ·
authoritative invocation **BROKEN** (`pytest` exits 3, collects nothing) · reach under it
**UNKNOWN, not zero** · verdict `PARTIAL_GREEN`.

**NOT BUILT (backlog, verdicts already fixed in `SQI_INDEX.md` — do not re-litigate):**
SQI-04…SQI-13. Ten datasets.

---

## 3. Active decisions (binding — do not revisit)

1. **14 datasets, not 17.** Every overlapping capability is a cross-reference to the system that
   already owns it (`T-SQI-PARALLEL-SYSTEM-001`). **Never fork:** the evidence ladder (ACIS), the
   knowledge graph (graphify), the insight router (**FD-03 — DO NOT BUILD; it already *is* the
   "Failure-to-Data Compiler"**), decision verdicts/blast radius (DRK), bug→invariant
   (`modules/hard_rules`), the premise verifier (`modules/error_prevention`), done-gate scoring
   (`output_contracts`), telemetry (CO-12 `record_signal` — extend the kind, never fork the bus),
   liveness (D1 `default_registry` — add an entry, never a second ledger).
2. **Fabrication contract.** One `.txt` per dataset. `PART I`…`PART XX`, each closed by
   `PART N FINAL LAW`. Dense prose, numbered subsections, arrow flows. **No** markdown headings,
   bullets, tables, or code fences. **≥1,200 words per Part.**
3. **Vocabulary.** Use *transmutation* / *institutionalization*. The quarantined literals live
   fragment-assembled in `tools/test_sqi.py` `_BANNED` and are **never spelled out in any vault
   prose — including prose that is describing the rule.** A document about forbidden words cannot
   contain the forbidden words.
4. **Never move a criterion to fit a draft.** If a Part lands under the floor, raise the Part.
   The only gate ever loosened here was loosened because the *detector* was broken, never because
   a real finding was inconvenient — that is Part XIII's Gate Mutation Firewall.
5. **The producer never certifies its own claim.** Delegated work is verified by running the gate
   yourself, not by trusting the agent's self-report.
6. **Never adjust the engine so the number confirms the hypothesis** (`T-SQI-FINDING-FABRICATION-001`).
   Every number the engine produced disagreed with the plan's prediction, and every disagreement
   was a real fact about the repository. Report what the instrument says.
7. **The engine surfaces; the Owner remediates.** Widening the canonical invocation is a
   governance event (SQI-02 §9.10). Do not silently fix `testpaths` or the `_logs/` crash.

---

## 4. Next actions (imperative — highest value first)

1. ~~Build SQI-02 Part XV weakening detection.~~ **DONE — SCS C94.** `weakening_detectors.py` +
   `weakening_baseline.py`; four gates (assertions fell → FAIL; mocks rose ∧ assertions did not →
   FAIL; hash moved ∧ arithmetic held → REVIEW; broad handlers rose → REVIEW) + the §15.8 mutation
   probe (`--mutation-probe`, opt-in). **Do NOT gate the mocks/assertions ratio** — a ratio falls
   when its denominator rises, and the cheapest way to raise an assertion count is a tautological
   assertion, which IS weakening §15.8. The assertion vocabulary is a governed artifact:
   **narrowing it hides removals, because zero cannot fall.**
2. **Build the threshold inventory (§15.7)** — the one weakening still undetected. Every numeric
   threshold in the repository, versioned, each change a governance event with a reason. Each
   individual relaxation is defensible; the sum, over a year, is a set of gates that constrain
   nothing. It is invisible without a ledger and lethal with one.
3. **Point `run_sqi.py` at the rest of the estate.** It takes a path argument and has never been
   run outside PP. TUA-X's 390 orphaned tests are one `testpaths` line; CostaLuz's scanner is
   declared and never invoked; the two Elixir repos cannot compile. The engine detects all three
   classes already. Nothing has pointed it at them.
3. **Surface the four PP findings to the Owner** (governance decisions, not agent work): the
   broken zero-argument default, the absent root pytest config, the canonical invocation, and the
   63 unprotected module packages including `secret_firewall` and `cascade_prevention`.
4. **Only then** consider SQI-04…13 from the backlog.

---

## 5. Start instruction

Read this file, then `SQI_INDEX.md`, then `SQI_COMPLETION_REPORT.md` §4 (honest gaps), then
execute Block 4 action 1. Do not ask for approval. Do not explain the plan. Build.

**Update this file after every sealed unit of work — never only at the end.**

---

## Parallel workstream: exact-target continuation (2026-09-18)

The false "COMPACTION LANDED" and the foreground `/d1-continue` injection are fixed in
`5d17c1e`, `01211b5`, `fd87e39`. Its own resumption contract, with what is and is not
proven, lives in `vault/specs/exact-target-continuation.RESUMPTION.md`; read that file
before touching the watchdog resume path, the SendKeys daemon or `continuation_transport`.
