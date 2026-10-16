---
covers: [planning-necessity, work-class-capsule, m2-planning-incident, owner-pause-stop, p25-canary, prereg-lint]
status: APPROVED 2026-10-16 (Owner "a 1. 30.5M 2. b 3. a": tranche 30.5M hard; P25 from a PP clone on GEX44,
  live install untouched; bootstrap in the interactive pane, no Ralph mission)
progress: |
  E1 DONE: d466d977 hold --stop (owner_pause; V-OP 5/5, drill 2 red), 2f61b594 session-tree (V-STR 4/4; real M2
     tree on GEX44 = 29,947,551 exactly). PP clone on GEX44: ~/missions/pp-tbm2 (git archive of 2f61b594).
  E2 DONE: ae7c45c2 planning_gate.py + arm --work-unit/--planning-override (V-PNG 17/17; drills 9 + 1 red).
  E3 DONE: TB ac66192 capsule .planning/capsules/TB-DISC-PROBE.json + c79728f tools/prereg_lint.py
     (test_prereg_lint 15/15 laptop AND GEX44; in-memory mutants of the TIME and CLOSED checks go red; the t300
     and portrait blockers are fixtures). GEX44 ~/missions/tb-m2 main fast-forwarded to c79728f by bundle
     (worktree-m2-phase5 untouched); invalidator sha256 identical on Linux. ~/missions/pp-tbm2 got the 3 E2 files
     (LF, blob-identical to ae7c45c2; the E1 archive there is CRLF via autocrlf, content = E1): V-PNG 17/17 there,
     and planning_gate on a P25 unit (2 unknowns) -> DELTA_PLAN, 1M authority, no planner agent.
  BUDGET GATE (measured 2026-10-16 ~14:05Z, mission_spend._file_tokens deduped, since the approval message
     13:23:01Z): predecessor 56c349b4 19,956,064 (avg ctx 278k, peak 454k: context rent) + successor efadfbcc
     7,334,378 (avg 154k) = 27,290,442 of the 30.5M tranche. 25M "hard stop" (sec. 32) passed; ~3.2M left
     cannot cover E5 (P95 8M). STOPPED for the Owner: raise/second tranche, or run E5 as a fresh small-context
     Sonnet worker on GEX44 (the compiled-unit path this plan forecasts at <=70k ctx), not from an Opus pane.
  OWNER 2026-10-16 "a": +10M (tranche 40.5M); E5 runs as a fresh small-context Sonnet worker on GEX44.
  E5 DONE (economics PASS, science INCONCLUSIVE): headless Sonnet worker 17abbe26 on GEX44, watchdog 8M/10M.
     gate DELTA_PLAN -> prereg (lint CLEAN) -> PROBES cantina-camera-force -> build -> tbl-20261016-135951 (rc 0,
     59 frames) -> slot AUTHORIZED/CONSUMED -> commit. 3,648,572 processed, 12 min, 0 planner turns (old path 29.9M,
     0 executed). TB 802217e prereg, 54afccc result, 8badfae review: all three verdicts INCONCLUSIVE ("no crash"
     is met by P24's unedited disc; the Force trigger never fired, so CameraCut/CreateCreatures were not tested);
     capsule template now requires a PASS observable the unedited disc cannot produce. KSR ledger reconciled
     (121 events, 0 violations). Lesson: the gate+lint cut planning cost ~8x; neither judges whether an
     observable discriminates. That stays a reviewer's job.
  E6 DONE: reforecast below (sec. 28-29 table). Tranche measured 36.9M of 40.5M (laptop 33.25M + worker 3.65M).
  OWNER "approve both": E7 as a Sonnet unit; E6 table approved -> M2 advances one capsule-gated worker at a time
     (old /gsd-autonomous mission m-f9290d78278f STAYS held: un-holding it restarts the planner loop).
  E7 DONE: dc4bf2b4 (laptop Sonnet worker 9db680e6, 2,020,027 processed, 5 min, cap 3.2M): spawn receipt gains
     planner (gsd-planner|gsd-plan-checker) + mission (CCR_WORK_UNIT id; gsd_mission sets no mission env var);
     UKDL PR-PLANNING-NECESSITY-001 + T-OBSERVABLE-NOT-DISCRIMINATING-001. Mod tests 27/27 re-run by me. The two
     receipt fields themselves are untested (no harness drives the live handler; only isPlannerType is). Landed by
     CAS ff of the branch ref (another pane had a staged file and a dirty ukdl; both kept). Not deployed to any live
     mod copy (shadow; repo only).
  M2 P26 DONE (M2 budget): worker 23c5ea29, 5,540,073 processed, 14 min, tbl-20261016-142024. Worker said
     loose-scp PASS + spawn-route PASS; I looked at t106 vs P24's t106: the "womprat" is a two-legged minifig NPC.
     Reviewed: all INCONCLUSIVE, P5-SCP OPEN (TB 60ab421 result, d8cdab9 review). Capsule rule added: a worker's
     PASS is a candidate until a reviewer has seen the frame and its control. Lesson: Sonnet frame-reading is not
     a verdict; the 5.5M worker needs a cheap reviewer step, not an Opus pane.
  tb_local FIX DONE: TB 05c3e5f, `pgrep -x dolphin-emu-nogui` never matched (15-char comm) -> pgrep -f on the
     executable; V-TBL-DOLPHIN-REAL on GEX44: fixed 7/7, old fails (seen=[] with a live fake). Capsule sha
     refreshed; GEX44 at d8cdab9: PRL 15/15, TBL 7/7, gate DELTA_PLAN, capsule not invalidated.
  BUDGET BREACH (measured 2026-10-16 ~14:50Z, deduped since 13:23:01Z): laptop panes 46,891,601 (this pane
     26.9M: context rent ~300k/turn after images) + P25 3.65M + E7 2.02M = 52.56M vs the 40.5M tranche (+12M).
     Workers: 11.21M total for P25+P26+E7. STOPPED; no further work from this pane. Owner: next M2 unit P27
     (dense capture t35-60, named cropped evidence) needs a reviewer path that is not this pane.
  OWNER "yes" (P27 + separate reviewer). P27 chain on GEX44 (~/missions/p27_chain.sh): Sonnet worker 865d227d (same
     P26 disc, captures every 2 s t30-70, lists runs/<job>/candidates.json, NO verdicts; watchdog 8M/10M) -> fresh
     Sonnet reviewer e96aac0a (sees only claims + candidate/control frames; cap 1.5M) writes the RESULT verdicts
     and commits. Try 1 (cf54013a, 225k) stopped itself on a GEX44 "CONTEXT CRITICAL" hook advisory that a headless
     run cannot act on; the packet now says such advisories are non-binding. Laptop waiter task ba9mwie2z.
  P27 DONE (successor pane bd7ce4b7): chain_end 14:55:33Z, job tbl-20261016-144621. Spend (watch_end, processed):
     worker 3,558,793 + reviewer 363,862 + try1 ~225k = ~4.15M (P26 was 5.54M). Reviewer e96aac0a: loose-scp PASS,
     spawn-route PASS, front-camera INCONCLUSIVE (TB 07d8d65). Spot-check at full res: the t112 "tan rounded body" is a
     minifig seen from behind (alien head piece, LEGO torso, C-shaped hands); the P24 control has a DIFFERENT minifig at
     the same spot. Both PASS -> INCONCLUSIVE (TB 6d239e0). Lesson: the independent Sonnet reviewer repeated the P26
     misreading WITH the control in hand; a same-t frame from another run is not a matched control for ambient NPCs.
     The coordinator's full-res look is the only check that has caught it (2/2). Ledger: ledger_reconcile --apply
     appended P26+P27 AUTHORIZED/CONSUMED, SLOT_LEDGER PASS events=125 violations=0, re-run IN SYNC. Laptop TB at 6d239e0.
     P5-SCP and P5-FORCE stay OPEN; the CameraCut window (between t080 black and t085) is still uncaptured.
  OWNER 2026-10-16 "y": tranche P28 = 10M HARD (P5 rerun only; worker watchdog 6M pre-run / 8M hard, coordinator
     <=2M; one full-res crop look by the coordinator, no Sonnet reviewer) + remove Apps\pp-e7-ccr-shadow after a
     clean+merged check. P28 design: primary observable = CameraCut held ~60 s on Player0 from level load (~t80-85;
     P24 control t85/t112 show the normal camera), dense capture t76-100 every 1 s; womprat x3 spawn kept as secondary.
  P28 DONE (tranche 10M): worker bd6f5a09 2,400,916 processed, 12 min, tbl-20261016-155828 (disc 93a077fa..., first
     Cantina frame t084). Coordinator verdicts from a 3-row full-frame grid vs P24: loose-scp FAIL, front-camera FAIL,
     spawn-route FAIL (wide stock camera t84-100; the camera icon is stock HUD, present in P24 t085; t100 figure = the
     P27 minifig patron, which the worker itself flagged). TB d9c3362 prereg, 671078e result + RESUMPTION P27 line
     corrected (it still said P27 confirmed the loose .scp). Ledger: SLOT-TB-P28 AUTHORIZED/CONSUMED, PASS events=127
     violations=0, IN SYNC. Laptop TB at 671078e. Finding: 3 runs, 2 different Start-state actions, zero effect.
     P5-SCP narrowed to "loose level.scp not read OR Start actions not executed".
  OWNER "y": P29 from the P28 tranche remainder.
  P29 DONE: worker caa0f1c1 4,581,461 processed, tbl-20261016-162456 (disc e5737cc5...). Loose MosEisley_C level.scp
     replaced by one unparseable line -> Cantina at t085 identical to P24 (HUD, layout, patrons, pause menu at t100):
     scp-read FAIL, scp-not-read PASS (qualified). Worker errors corrected in the result: first_cantina_t is 85 not
     null; its packed-copy search was text-only (0 hits in 1561 .pak/.fpk/.AI2/.CSC/.CTR), which cannot see a compiled
     script. The worker's process hung 16 min after its run: its sha256 one-liner reopened the file each read
     (`iter(lambda: open(p).read(n), b'')`) and looped forever in a background shell; claude -p would not exit until
     the coordinator killed it. TB 63e10ab prereg, eba80ef result + RESUMPTION. Ledger SLOT-TB-P29 PASS events=129
     violations=0, IN SYNC. Laptop TB at eba80ef. P28 tranche used by workers: 2.40M + 4.58M = 6.98M of 10M, plus this pane.
  CONCLUSION P26-P29: four runs, no loose level.scp edit has any effect, so the loose .scp is a dead end for P5.
  NEXT (needs Owner, new tranche): static RE of MosEisley_C .AI2/.CSC to find the compiled level script (E6 phase-7
     class: novel RE, BOUNDED_PLAN, P50 8M / P80 12M / P95 20M), offline, no Dolphin slot.
  OWNER "y": tranche P30 = 12M HARD (worker watchdog 10M hard, coordinator <=2M). P30 = static RE, read-only on game
     data: main.dol load-path strings (which file the engine opens for a level script) + MosEisley_C .AI2/.CSC vs the
     level.scp identifiers; deliverable docs/RE_CANTINA_LEVEL_SCRIPT.md + a read-only scan tool + a proposed P5 edit route.
  P30 DONE: worker f0ae8f9c 1,500,297 processed, 6 min, TB 19ce128 (doc + tools/re/scan_level_script.py). Worker answer
     LIVE_IN_MOSEISLEY_C.AI2 ("compiled script") WITHDRAWN by the coordinator. The AI2 is locator/path data: 46-byte
     records = 16-byte name + LE f32 coordinates (Walk_0 -2.64,0.01,2.57). level.scp's type=cantinaaliens /
     MosEisleyCitizen are absent from it. Its "ai2 first" load order was inferred from string adjacency and labelled OBSERVED.
     Coordinator static checks: the P29 WBFS carries the unparseable level.scp (wit extract, 40 bytes); 203 .fpk / 22,597
     entries hold no .scp. TB 3f5ae22 + c32df0f; laptop TB at c32df0f. Answer UNKNOWN. Live readings: (a) the loose
     .scp is read and a parse failure is swallowed, or (c') an unfound source. Tranche P30: worker 1.50M + this pane.
     Lesson: a cheap worker answer arrives fast and confident. 3 of 4 worker conclusions today (P27 reviewer, P29
     first_cantina_t, P30 answer) did not survive one coordinator check.
  NEXT (needs Owner: a Dolphin slot): P31 = ONE run of the existing P29 disc with Dolphin's FileMonitor log + console
     log on; list every file opened under MosEisley_C and any "Script parse error"/"Failed to open" line. Decides
     whether the loose .scp is opened at all. Same worker shape, P50 ~3M.
  OWNER "y": P31 from the P30 tranche remainder (Dolphin slot allowed). Coordinator added opt-in TB_DOLPHIN_LOG=1 to
     tools/gex44/tb_disc_boot.sh (Logger.ini: FileMon + OSREPORT, copied to out/dolphin.log; default path unchanged,
     test_tb_disc_boot 14/14, test_tb_local 7/7) and refreshed the capsule harness sha (TB 3019f13). Worker deaea746
     launched 18:54:19Z on the existing P29 disc; log-works is an instrument claim (an empty log cannot show absence).
  P31 + P31b: BOTH INSTRUMENT FAILURE, question still open. P31 (tbl-20261016-185808, 3,537,607): no dolphin.log,
     because Dolphin does not create $U/Logs (my defect: switch never booted before spending the slot; proven afterwards
     with a homebrew DOL, fixed TB c816999). P31b (tbl-20261016-191521, 1,575,394; retry I authorised myself as
     within P31): the worker ran tb_local WITHOUT TB_DOLPHIN_LOG=1 (no "dolphin log on" in runner.log). A packet
     defect: a decisive env var was left to the worker. TB f47f6a2 result; ledger P31+P31B AUTHORIZED/CONSUMED, PASS
     events=133 violations=0; laptop TB at f47f6a2. Tranche P30 (12M): workers 1.50+3.54+1.58 = 6.62M, plus this pane.
     2-failures rule: no third attempt of the same shape.
  NEXT (needs Owner, a 3rd slot): the coordinator runs ONE literal command itself, no worker:
     TB_DOLPHIN_LOG=1 python3 tools/gex44/tb_local.py run build/TwoBuilders_P29.wbfs --capture <P29> --inputs <P29>,
     gated on runner.log "dolphin log on" + >=10 FileMon lines before any reading.
  OWNER "do it yourself". P31c DONE (coordinator, no worker; tbl-20261016-204510; ledger SLOT-TB-P31C seq 134/135,
     PASS events=135 violations=0): gate held (runner.log "dolphin log on"; 987 FileMon lines of 1073). ANSWER: the
     Cantina on this route is the HUB level Levels/Map/map. MosEisley_C is never opened. The engine opens
     Map/map/ai/MAP.AI2, ai/script.txt, then every loose ai/*.scp it lists (level, level1 16 kB, barman, band1-3, jabba,
     party, Map*). Global Scripts/SCRIPT.TXT + Scripts/*.scp are read once scripts/ai.pak is not found. P25-P29 edited a
     level this route never loads; P30's answer and reading (a) are both moot. TB b48bff9; laptop TB at b48bff9.
     Lesson: four probes and one RE unit (~25M of workers plus panes) went to a premise nobody had checked: which
     level is on screen. One instrumented run answered it.
  NEXT (needs Owner, new unit): P32 = P28's observables (CameraCut 60 s on Player0 + womprat x3) inserted into the
     HUB's Start state in Levels/Map/map/ai/ (read level.scp / level1.scp first for the owner of Start). TB-DISC-PROBE
     capsule, DELTA_PLAN, P50 ~3.6M; keep TB_DOLPHIN_LOG=1 on, so the log shows that the edited .scp is opened.
  OWNER "y". P32 DONE (coordinator, no worker; tbl-20261016-205749; disc 62a42439; ledger SLOT-TB-P32 136/137, PASS
     events=137 violations=0). The hub has no Start state: level1.scp is Base -> Update -> Enter_MainRoom (InHubArea
     MAINROOM; creates the 13 patrons). Edits anchored on the Enter_MainRoom header (the first anchor, a comment, occurs 10x:
     the build refused it, nothing spent). Gate PASS (level1.scp opened, log line 1033). hub-scp PASS with a deviation: a
     held NON-STOCK camera t84-112 (far, behind a pillar, through the mirrored timer hologram; PLUS no longer pauses),
     not the planned close-up. front-camera FAIL. spawn-route INCONCLUSIVE (4 of 21 frames looked at; womprat FileMon
     opens are stock, P31c opens them too). P5-HUB-SCP CLOSED: the loose-.scp route works on the hub. TB 74b8007 prereg,
     967f48f result; laptop TB at 967f48f.
  NEXT (needs Owner): P33 = CameraCut framing variant for a head-on shot (smaller range, roty=180) + all frames at full
     res for the womprat (or a camera aimed at MainRoomIdle). Same coordinator-run shape, one slot.
  OWNER "y". P33 DONE (coordinator; tbl-20261016-211232; disc 0bee95b6; ledger SLOT-TB-P33 138/139, PASS events=139
     violations=0; its experiment field reads "tb_p33_hub_camera_hold", a sed-rename slip, slot/job correct, left as is).
     A static survey of the stock .scp came first: Player0 is only used with campos_x/y/z; the stock close-up is
     `range=2 rotx=10 roty=90 tgt_character=player`. Using it verbatim (end_time=60) gave a HEAD-ON MEDIUM shot held
     t84-112 in 21/21 frames: front-camera PASS (medium, not a close-up). Womprat x2 (WompRat, spawned_womprat,
     nearest_player): no four-legged shape in 21/21 frames (640px sheet). FAIL in view; an off-camera spawn is not excluded.
     TB 28f9865 prereg, 1e2dd6f result; laptop TB at 1e2dd6f.
  NEXT (needs Owner): P34 = the womprat spawn on a named, camera-visible locator, with a RandomMap spawn at the same locator as
     the control (a patron appearing there proves the locator and the line work; then a missing womprat = a type/script problem).
  E-SERIES CLOSED. NEXT: M2 continues phase by phase under the E6 table (headless Sonnet worker + watchdog, never an
     Opus pane); the P5 rerun capsule needs an observable the unedited disc cannot produce (four-legged silhouette at a
     scripted spot, or a forced spawn independent of PlayerUsingForce). Old mission m-f9290d78278f stays held.
  E6 reforecast (processed tokens per phase; capsule probe cost from P25 n=1, so confidence LOW):
     | Phase | Class | Gate mode | P50 | P80 | P95 |
     | 5 rerun (unconditional trigger, then Force) | capsule | DELTA_PLAN | 3.6 | 5 | 8 |
     | 6 faces | capsule | DELTA_PLAN | 3.6 | 5 | 8 |
     | 7 CHG archaeology (womprat buffers, 350-CHG census) | novel RE, offline | BOUNDED_PLAN | 8 | 12 | 20 |
     | 8 writer | novel code | BOUNDED_PLAN | 8 | 12 | 20 |
     | 9-11 hair/kitten (x3) | capsule after 8 | DELTA_PLAN | 11 | 15 | 24 |
     | 12 Kitten Call | partial | BOUNDED_PLAN | 6 | 9 | 14 |
     | 13 extras | capsule | DELTA_PLAN | 3.6 | 5 | 8 |
     | 14 mixed | mixed | BOUNDED_PLAN | 6 | 9 | 14 |
     | Total 5-14 | | | 50 | 72 | 116 |
     vs M2 remainder ~98.5M (minus this tranche's 36.9M = ~61.6M): P50 fits, P80 does not. Every unit runs as a
     headless Sonnet worker with a watchdog, never from an Opus pane (this tranche: Opus pane 33.25M vs worker 3.65M).
created: 2026-10-16
owner_surface: chat (this file is the backup)
---

# Planning economics after the M2 incident: master plan (Reality Delta + staged tranche)

## 0. What the scan changed (read this first)
The prompt's premises came from MY numbers in chat, and two of them are false:
- **65.4M is wrong. Real M2 spend: 29,947,551 processed tokens** (deduped by message id). Claude writes one
  transcript line per content block and repeats the message `usage` on each; my sum counted those lines. Raw
  line sum = 65,398,743 (2.18x).
- **The breaker DID see the subagents.** `mission_spend.processed_tokens` walks the session dir with `rglob`,
  which includes `<sid>/subagents/agent-*.jsonl`. It read 25,377,536 at 14:26; the reviser kept running to 14:49
  and added the remaining ~4.6M. There is no descendant-invisibility bug.
- **The "1-3M per probe" prior is also mine, and unmeasured.** Measured (deduped, laptop transcripts, commit
  windows): P22 4.56M (31 turns, Opus); P24 9.09M (42 turns, Opus); P23's window is 30.9M, but the same pane
  also wrote the M2 plan inside it, so it cannot be separated (contaminated).
Consequence: the incident is real, but it is a **~30M planning loop that produced zero execution, about 3-6x the
cost of a whole precedent probe**, not 16-30x. The programme is cut to what the evidence supports.

## 1. Current M2 reality
- Goal `tb-m2` (130M, declared on the laptop install only). Mission `m-f9290d78278f`, GEX44, state RUNNING +
  owner_hold, no live worker: `claude agents` is empty; stopped with `claude stop 505ddd34`, 14:51.
- Envelope: token_estimate 60M, stall budget 15M, work_dir = the worktree (set 14:2x today).
- Laptop mission `m-0fdcc50a311b`: HALTED + hold; 1.59M spent (cost_mark).
- M2 spent so far: 29.95M (GEX44) + ~1.6M (laptop) = **~31.5M of 130M; ~98.5M remains** (the prompt's 63M
  was derived from 65.4M).
- Uncommitted: the reviser's edits to 05-01..05-05 in `worktree-m2-phase5`; committed: `e13c2d0` (plans v1).

## 2. Exact cost tree (deduped; GEX44; all Sonnet 5.5)
| Node | Type | Turns | Processed | Avg ctx/turn | Peak ctx |
|---|---|---|---|---|---|
| 505ddd34 worker (coordinator) | main | 24 | 3,194,820 | 132,814 | 161,131 |
| aa37b5f3 "Plan phase 5" | gsd-planner | 128 | 17,418,378 | 136,057 | 214,566 |
| a8cb5a88 "Check phase 5 plans" | gsd-plan-checker | 26 | 3,212,251 | 123,522 | 155,770 |
| a4319f3c "Revise phase 5 plans" | gsd-planner (replan) | 43 | 5,936,347 | 138,039 | 200,391 |
| a7c29714 "Recheck phase 5 plans" | gsd-plan-checker | 3 | 185,755 | 61,904 | 62,533 |
| **Total** | | **224** | **29,947,551** | | |
Planning 23.35M (78%), review 3.40M (11%), coordination 3.19M (11%), execution 0.

## 3. Accounting gap (actual, not assumed)
| Claimed gap | Verdict | Evidence |
|---|---|---|
| Subagents invisible to the breaker | FALSE | rglob over the session dir; 25.4M read at 14:26 included the subagents |
| My chat report double-counted | TRUE (instrument error) | raw 65.4M vs dedup 29.9M |
| Hold does not stop a live worker | TRUE on GEX44 | the GEX44 install 30fdbf0f (10-09) predates spec mission-cost-hold-stops-worker (laptop has stop_owner via `claude stop`) |
| Stall fingerprint blind to the worktree | TRUE on GEX44 | work_dir was None, so the fp read the clone root (`ef2dadc0`, frozen); the laptop has AMCR binding |
| Daemon resurrects paused work | PARTLY | I sent a raw SIGTERM; the Claude daemon treats that as a crash and resumes (correct behaviour). `claude stop` was durable. An Owner hold, by contract, does not stop the worker |
| GEX44 PP install drift | TRUE, root | no goal-declare, arm-chain, cost-hold stop, binding, calibration |

## 4. Root-cause matrix (29.9M)
1. **Topology**: `/gsd-autonomous` always runs plan-phase (planner, then checker, then replanner) for every phase. Nothing
   asks whether the work class already has a precedent. Cost 26.7M of the 29.9M.
2. **Context rent**: every turn carries ~136k of context (the GSD workflow plus PROJECT/ROADMAP/STATE/CONTEXT plus growing
   plans). 128 planner turns x 136k = 17.4M. Output was ~180 KB, about 45k tokens, so **~0.3% of processed
   tokens became plan text**.
3. **Scope inflation**: 5 plans, 4 waves, STRIDE registers, mutant validators, a 2nd reproducibility run,
   conditional follow-up discs, re-verifying the portrait (82 mentions; P24 closed it).
4. **GEX44 install drift**: the breaker tripped at ~10.6M (13:40), but the hold could not stop the worker, which spent ~19M more.
Iteration standard: CLASS 2 (the plan assumed repo/runtime state that was false: a fresh install on GEX44, no
precedent reuse) + CLASS 4 (the hold "succeeded" while the spend continued) + CLASS 5 on my side (I reported
an unverified total).

## 5-7. Boundary amplification, context rent, novelty
- Planning boundaries: 224 model turns for a unit whose irreducible decisions are about 6: which .scp hosts the
  camera, CameraCut syntax, Force condition, CreateCreatures args, capture timeline, verdict rule.
  Necessity ratio ~6/224 = 0.027.
- Context rent: avg 132-138k/turn; peak 214k. Precedent and doctrine re-read every turn.
- Novelty: the P25 delta is the .scp edits plus a new timeline. Build, tb_local, capture, judging, ledger and the prereg
  shape are identical to P22-P24. Text duplication vs precedent was not measured by tokens; qualitatively, most of the
  180 KB is harness/threat/proof boilerplate. It will be measured in P25 by the lint, not asserted.

## 8. P22-P24 precedent matrix (Work Class `TB-DISC-PROBE`)
| | P22 | P23 | P24 |
|---|---|---|---|
| Delta | main.dol name-table swap | icon files + icon= | none (route + build identity) |
| Prereg | docs/PREREG_P22 (1 page) | PREREG_P23 | PREREG_P24 |
| Build | build_two_builders RECIPE | same | same, Linux wit, byte-identical |
| Run | tb_client queue | tb_client queue | tb_local (GEX44) |
| Timeline | P22 grid | P22 grid | P22 grid |
| Judge | frames by eye | frames by eye | frames by eye + P23 comparison |
| Ledger | AUTHORIZED/CONSUMED | same | same |
| Measured | 4.56M | (contaminated) | 9.09M |
Stable across all three: the prereg shape, RECIPE+PROBES build, timeline grammar, capture/judge, ledger, commit.
Variant: the run route (queue to local; local is now the canonical one on GEX44).

## 9. P25 delta (from RESUMPTION + 05-CONTEXT, not expanded)
Cantina probe on RECIPE: CameraCut on Player0 (front camera) and `PlayerUsingForce` -> `CreateCreatures` womprat
next to Madzia, as loose `.scp` edits; one tb_local run; judge the camera and the spawn. The portrait is CLOSED (P24) and excluded.
Open unknowns (the real planning content): is a loose .scp honoured (P5-SCP), and does PlayerUsingForce fire (P5-FORCE).

## 10-24. Components: build / reuse / not build
| Section | Decision | Size |
|---|---|---|
| 10 Planning Necessity Gate | BUILD minimal: `tools/planning_gate.py`. Inputs: capsule match, novelty flags, irreversibility. Out: DIRECT_TEMPLATE / DELTA_PLAN / FULL_PLAN / OWNER. Wired at mission arm: a capsule match arms COMPILED_UNIT (`--wu-packet`) instead of `/gsd-autonomous` | ~150 lines + tests |
| 11 Planning Authority | REUSE the envelope: a FULL_PLAN unit gets its own token_estimate; no new ledger | config |
| A Mission Cost Tree | REUSE mission_spend (already counts children, deduped). ADD a `tree` report per session/subagent (it exists for sessions: `tree` flag line 581) so nobody hand-sums again | ~40 lines |
| 12-16 Plan compiler / IR / Delta compiler / CSE | NOT BUILT now. The capsule (a parameterised template) + delta fields is the IR at the size the evidence supports; a general compiler has no second consumer yet | 0 |
| 14 Work-Class Capsule | BUILD `TB-DISC-PROBE` in the TB repo from P22-P24: template prereg, PROBES entry pattern, run/judge/ledger commands, invalidators (route, wit, harness sha) | 1 file |
| 17 Plan linter | BUILD `tools/prereg_lint.py` (TB): every cited t in the capture list; claims not in `closed_obligations` (portrait to P24); probe key exists; disc sha matches | ~120 lines + tests |
| 18-19 Risk / proof compiler | NOT BUILT as a system: the capsule carries a fixed risk class (reversible personal mod, low) and "proof = one run + frames"; reproducibility only if the verdict is ambiguous | 0 |
| 20-21 Review / replan necessity | Folded into the gate: DIRECT_TEMPLATE = no semantic reviewer; lint failures are patched in place | 0 extra |
| 22 Owner pause | BUILD `gsd_mission.py hold --stop` (Owner hold that also runs stop_owner = `claude stop` + wait) + test; deploy the pause/cost-hold/binding fixes to GEX44 (see Q2) | ~30 lines |
| 23 CCR | SHADOW only: in `agent.spawn`, receipt `planner_spawn` with subagentType + mission; not enforce (no proof that middleware refusal is supported; CCR is not installed on GEX44) | ~15 lines |
| 24 Cognitive deopt | Covered by the existing stall breaker once binding/stop are deployed on GEX44 | 0 |

## 25-27. P25 canary, old vs new, learning curve
P25 runs as a COMPILED_UNIT: a fresh Sonnet worker on GEX44, wu_packet = capsule + P25 delta, small context,
no planner, no checker. Done-gates P25-DONE-1..15 from the prompt, all observable.
| | Old M2 path (measured) | Compiled P25 (forecast) |
|---|---|---|
| Planner/review turns | 197 | 0 (lint only) |
| Coordinator turns | 24 | ~25-40 (execution) |
| Avg ctx | ~136k | target <=70k (packet, not the GSD workflow) |
| Spend | 29.95M, 0 executed | P50 3M / P80 5M / P95 8M, executed + judged |
Learning curve: P22 4.56M, P23 n/a (contaminated), P24 9.09M (interactive Opus pane, ~215k ctx/turn), P25 forecast 3M.
If the worker's measured spend passes 8M before the run: STOP and report.

## 28-29. M2 6-14 reforecast, Two Builders gate
After P25: classify each phase (6 faces = capsule; 7 CHG archaeology = novel RE; 8 writer = novel; 9-11 hair/kitten =
capsule after 8; 12 Kitten Call = partial; 13 extras = capsule; 14 = mixed) and route each through the gate;
new P50/P80/P95 from P25's measured cost. M2 stays held until that table exists and is approved.

## 30. Mode by workstream
Reality Delta: done (EXECUTION). Cost tree report, lint, capsule, pause --stop: EXECUTION. Planning gate: PLAN
(this file) then EXECUTION. CCR: shadow EXECUTION. P25: EXECUTION. Reforecast: EXECUTION. No ULTRA-PLAN: no
owner conflict was found.

## 31. Micro-commits
PP: (1) this plan; (2) cost-tree report + test; (3) hold --stop + test; (4) planning_gate + test + arm wiring;
(5) CCR planner_spawn receipt; (6) UKDL/vault. TB (on GEX44 branch): (7) capsule; (8) prereg_lint + test;
(9) P25 prereg; (10) P25 result; (11) reforecast.

## 32. Staged budget (processed tokens; this pane is Opus, so routine pieces go to Sonnet subagents where they are cheaper)
| Env | Scope | Lower bound | Lower | P50 | P80 | P95 | Hard | Conf |
|---|---|---|---|---|---|---|---|---|
| E0 | Reality Delta (spent) | - | - | ~4M | | | - | measured after |
| E1 | cost-tree report + hold --stop + tests | 0.5 | 1 | 2 | 3 | 4 | 5 | med |
| E2 | planning_gate + arm wiring + tests | 0.8 | 1.5 | 2.5 | 4 | 5 | 6 | med |
| E3 | capsule + prereg_lint + tests | 0.6 | 1 | 2 | 3 | 4 | 5 | med |
| E4 | GEX44 install update (if Q2 = yes) | 0.3 | 0.5 | 1 | 2 | 3 | 3 | med |
| E5 | P25 canary (worker) | 1.5 | 2 | 3 | 5 | 8 | 10 | low |
| E6 | reforecast 6-14 | 0.5 | 1 | 1.5 | 2 | 3 | 3 | med |
| E7 | CCR shadow + UKDL/vault/CBR | 0.5 | 1 | 1.5 | 2.5 | 3.5 | 4 | med |
| **Tranche** | | | **8** | **13.5** | **21.5** | **30.5** | **25 (hard stop)** | |
Capital law check: P50 13.5M < 29.9M incident; hard stop 25M.

## 33-36. CAPEX/OPEX, amortisation, request, next tranche
- CAPEX (PP + capsule): E1-E4, E7, P50 ~9M. OPEX (P25 + reforecast): P50 ~4.5M.
- Observed savings are counted only after P25 (old-path counterfactual: ~30M per phase planned with GSD).
  Projected: phases 6, 9-11, 13 on the capsule. Not counted until measured.
- **Request: 25M hard, drawn from the M2 remainder (~98.5M); M2 stays held for anything else.**
- Second tranche only after: P25 verified at <=8M; reforecast table; hold --stop proven on GEX44.

## 37. Owner questions
Q1 approve this tranche (25M hard)? Q2 update the GEX44 live PP install to laptop HEAD (other missions there use
it, e.g. ql-lifecycle) or arm P25 from a PP clone? Q3 run the bootstrap in this pane (recommended: arming a Ralph
mission for it would repeat the planning topology being fixed) or as /cpp-gsd-long?
