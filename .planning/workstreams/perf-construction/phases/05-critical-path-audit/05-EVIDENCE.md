# Phase 5: Critical-path audit, evidence

plane: GEX44 host: kobicraft-gex44
Requirement: PERF-05. Plans 05-01, 05-02, 05-03. Every figure below is a count read from a registry, a suite footer, or a recorded run, and names its instrument, its plane and its n. No wall time of any real hook chain was measured in this phase; every timing item is deferred to the laptop and marked LAPTOP-ONLY / UNJUDGED.

## 1. Scope and plane

What Phase 5 did on GEX44 (Linux, Python 3.12, node v18, stdlib only): read the live dispatcher registry structurally, classify every entry, build a guard that proves a registry change cannot silently drop a blocking-safety hook, run the boundary suite before and after under an isolated HOME, list the deferral candidates without applying any, and build a host-matched before/after judge and a sampler whose only GEX44 output is a shape check.

What it did not do: it changed nothing under `hooks/`, no dispatcher map, no `settings.json`, nothing in the live install (D5-01; `git diff --stat 4fa606d7 -- hooks/` is empty, see section 5 and `records/05-03-final-gates.txt`). The only tracked file under `vault/` that Phase 5 added is the class table `vault/config/hook-critical-path-classes.json` (05-01). Nothing here says any hook is slow or fast; criterion 3 is delivered as an executable procedure (section 7), not as a result.

## 2. Inventory and classification

Instrument: `python3 -I tools/hook_critical_path_audit.py classify` (loads `hooks/hook-dispatcher.js` through a node child with an in-memory append wrapper under an empty temp HOME; D5-02). Plane: GEX44, source at commit `ae6fd9d9`. n = 113 registry entries in 20 containers (11 chains, 9 event defaults).

| Check | Value | Instrument and n |
|-------|-------|------------------|
| Entries | 113 | classify, n=113; the planning prototype counted 113, equal |
| Containers | 20 (11 chains, 9 event defaults) | classify, n=20 |
| Stop-chain entries | 27 (15 BLOCKING-SAFETY, 4 DEFERRABLE, 8 UNKNOWN) | classify, n=27 |
| Classes | BLOCKING-SAFETY 58, DEFERRABLE 4, UNKNOWN 51 | classify, n=113 (58+4+51=113) |
| Violations | 0 | classify against the table, n=113 |
| Basis codes | FLAG_BLOCK_OR_CRITICAL 21, DEF_ACCOUNTING_DUP 4, TABLE_UNKNOWN 13, TABLE_BLOCKING 8, DENY_SHAPE_IN_SOURCE 29, NO_TABLE_ROW 24, UNRESOLVED_LIVE_ONLY 14 | classify, n=113 |

Per container (BLOCKING-SAFETY / DEFERRABLE / UNKNOWN, classify, GEX44): Stop-chain 27 (15/4/8); SessionEnd-chain 5 (0/0/5); PreToolUse-Bash-chain 15 (11/0/4); PreToolUse-Edit-chain 13 (11/0/2); PreToolUse-Read-chain 3 (1/0/2); SessionStart-chain 4 (1/0/3); UserPromptSubmit-chain 8 (1/0/7); three UserPromptSubmit deadline-drill chains 2 each (1/0/1); PostToolUse-Bash-chain 4 (0/0/4); PreToolUse-default 3 (0/0/3); PostToolUse-default 7 (3/0/4); UserPromptSubmit-default 3 (0/0/3); PreToolUse-Bash/Edit/Read-default 3 each (2/0/1); PreToolUse-Agent-default 4 (4/0/0); PreToolUse-Web-default 1 (1/0/0); PostToolUse-Web-default 1 (1/0/0).

The count of deny-shape entries in chain containers is measured as 29 here and the planner's prototype said 27; the difference is reported and was not reconciled (STATE.md, plan 05-01 line). Both counts are structural reads of source, not timings.

## 3. Floors and the named residual UNKNOWN set

UNKNOWN is never PASS and is never moved. The class rule order is (1) a `block` or `critical` flag forces BLOCKING-SAFETY, (2) a deny shape in source forces BLOCKING-SAFETY, (3) a table row decides, (4) otherwise UNKNOWN (D5-03). Conservative on purpose: OWNER DECISION NEEDED (10).

The 51 residual UNKNOWN entries (instrument: classify "RESIDUAL UNKNOWN (51, named)", GEX44, n=51), as container|script:

- Stop-chain (8): session-summary.js, lazarus-snapshot.js, learning-sentinel.js, mark-live-session.js, background-verifier.js, jit_correlate_stop.js, ceps_promote_stop.py, ceps_correction_stop.js
- SessionEnd-chain (5): ads_sync.py, session_writeback.py, trace-flusher.js, session_delta_stop.js, learning-sentinel.js
- PreToolUse-Bash-chain (4): process-sandbox.js, ovo-push-gate.js, skill-heat-map-advisor.js, graph_first_gate.js
- PreToolUse-Edit-chain (2): skill-heat-map-advisor.js, uqf_pre_edit_gate.js
- PreToolUse-Read-chain (2): gatekeeper-semantic.js, graph_first_gate.js
- SessionStart-chain (3): session_start_hub.js, learning-sentinel.js, backlog_ledger_refresh.js
- UserPromptSubmit-chain (7): correction-guard.js, prd-keyword-sentinel.js, corpus-reuse-sentinel.js, gsd_x_tier.js, d2a_gate.js, jit_skill_loader.py, design_route_prompt.py
- UserPromptSubmit deadline-drill chains (3): drill-slow-straggler.js, drill-pooled-fast.js, drill-spawn-sentinel.js (test fixtures)
- PostToolUse-Bash-chain (4): tty-restore.js, bug-hunter-learning.js, osa_deploy_detector.js, bug-hunter-ceps-bridge.js
- PreToolUse-default (3): session-init.js, lazarus-heartbeat.js, intent_lock.js
- PostToolUse-default (4): turn-boundary-breadcrumb-close.js, session-logger.js, dna-flywheel.js, trace-emitter.js
- UserPromptSubmit-default (3): power-pack-reminder.js, baseline-translator.js, creative_grounding.js
- PreToolUse-Bash/Edit/Read-default (1 each, 3): turn-boundary-breadcrumb.js

Two picks held UNKNOWN on purpose (STATE.md, 05-01): `ceps_promote_stop` because `hooks/graph_first_gate.js` reads its output per tool call, and `learning-sentinel` because its source emits model context.

## 4. The guard (criterion 2)

Instrument: `python3 -I tools/hook_critical_path_audit.py guard`, compared against `records/05-01-inventory-baseline.json` (n=113 baseline entries). Plane: GEX44. Suite record `records/05-02-suite.txt`: `CRITPATH_PASS=59/59` at the 05-02 commit (the later 134/134 is section 9).

Five planted mutants, each rejected by a named code, and two controls that pass (suite, GEX44, one run each):
- M1 removes a block entry, a critical entry, and a whole container: exit 1, `MOVED_NON_DEFERRABLE`.
- M2 flips `block` or `critical` true to false: exit 1. The strengthening control (false to true) exits 0.
- M3 removes an UNKNOWN entry: exit 1.
- M4 adds a deadline to a chain that carries a BLOCKING-SAFETY entry: exit 1. Two controls (a chain with no blocking entry, a synthetic UNKNOWN-only chain) take a deadline with 0 violations.
- M5 removes a DEFERRABLE entry with no SessionEnd twin: exit 1, `DROPPED_WORK`; the control where the twin exists exits 0 with moved=1, violations=0; the no-SessionEnd-container variant exits 1.
- Refusals: an empty or a missing baseline exits 2.

Live run, `records/05-02-guard-live.txt` (GEX44, 113 baseline entries, current source = the live dispatcher at `744204da`): moved 0, added 0, violations 0, hooks clean. Boundary: the guard sees the repo registry only. It cannot see whether the laptop `settings.json` registers a chain; that is LP-09.

## 5. Boundary suite before and after

Instrument: `python3 tools/test_hook_boundary.py` under an isolated scratch HOME, run through `phases/05-critical-path-audit/compare_runs.py`. Plane: GEX44, n=2 runs of 7 gates.

- Before (`records/05-01-boundary-before.txt`): `HOOK_PASS=7/7  threshold=7/7`, exit 0.
- After (`records/05-02-boundary-after.txt`): `HOOK_PASS=7/7  threshold=7/7`, exit 0.
- Comparison (`records/05-02-boundary-compare.txt`): `VERDICT: PASS - before green and every gate line identical in the after run (isolated HOME, GEX44)`. A comparison green on both sides but with differing gate text is NOT_SHOWN, never PASS (05-02 pick).
- What the isolated HOME could not evaluate: gate V-HOOK-TRIGGER-REGISTERED reports an UNEVALUATED sub-check (no live settings under the scratch HOME), in both runs. The real-HOME run is LP-12, LAPTOP-ONLY / UNJUDGED.
- Phase 5 changed nothing under `hooks/`, so "after" is a control for the claim "no registration change", not a before/after of a move. `git diff --stat 4fa606d7 -- hooks/ vault/ tools/measure_hook_event.py tools/measure_session_start.py tools/test_hook_boundary.py` is empty in `records/05-03-final-gates.txt`.

## 6. Deferral candidates

Pointer: `05-DEFERRAL-CANDIDATES.md`. Count: 4 candidates, all `DEF_ACCOUNTING_DUP`, all in Stop-chain (trace-flusher, ads_sync, session_writeback, session_delta_stop), instrument classify n=113. None applied. They are one pipeline and are all-or-none; the shared precondition is that the Owner wires `SessionEnd` to the dispatcher in the laptop `settings.json` and LP-09 confirms it. This file is a list, not an instruction (OWNER DECISION NEEDED (9) still stands: leave them in Stop-chain).

## 7. Laptop procedure LP-09 to LP-12

All four are LAPTOP-ONLY / UNJUDGED until the laptop supplies the named record. Each record must begin with the output's own `host` and `os` keys. No laptop number appears in this file. Sample size rule for any timing arm: at least 7 MEASURED samples per arm (PROPOSED, uncalibrated: OWNER DECISION NEEDED (10)). The judge, not the operator, decides the verdict.

**LP-09 (enumerate the real registry), LAPTOP-ONLY / UNJUDGED.**
- Command: for each event named in the laptop `~/.claude/settings.json` run `python tools/measure_hook_event.py --event E [--tool T] --json` and save each JSON to `lp09-E.json`. Also record whether a `SessionEnd` entry calling `hook-dispatcher.js --event=SessionEnd-chain` exists, and whether the standalone `learning-sentinel.js` is also registered.
- Sample size rule: one record per registered event (n = the number of events), no timing.
- Falsifier: any record whose `os` is linux or whose `host` is kobicraft-gex44; any registered chain absent from the 113-entry registry; any chain that appears both directly and through the dispatcher (duplicate invocation).
- Record to bring back: `lp09-*.json` plus one line `SessionEnd registered: yes|no`. Until then the verdict is NOT_SHOWN.

**LP-10 (A/A then A/B Stop-chain wall), LAPTOP-ONLY / UNJUDGED.**
- Commands, from a checkout with this phase merged, on the laptop, host quiet (the sampler records the host state per sample): `python tools/hook_critical_path_audit.py collect --dispatcher <live dispatcher path> --event Stop-chain --arm A --n 7 --timeout-ms 120000 --out A.json`, then the same with `--arm A_REPLICATE --out A2.json`, and only then apply the candidate change on the laptop (Owner action) and run `--arm B --out B.json`. Never collect B first; alternate batches if the host state drifts. Judge with `python tools/hook_critical_path_audit.py ab-judge --samples A.json A2.json B.json --laptop-host <laptop host name> [--work-preserved]`.
- Sample size rule: at least 7 MEASURED samples per arm; TIMED_OUT, UNOBSERVED and FAILED samples are counted per arm and an asymmetry is INCONCLUSIVE; a non-GREEN host sample never contributes.
- Falsifier: the judge exits 2 (a GEX44 name, a mismatching host, or a SHAPE_ONLY file); both p50 and p95 of B do not beat the A to A-replicate noise (verdict NO_DIFFERENCE_DETECTED); the host bucket differs between arms (INCONCLUSIVE). A verdict of B_FASTER is the only result that supports a move, and only together with LP-11.
- Record to bring back: `A.json`, `A2.json`, `B.json` and the judge's printed VERDICT line.

**LP-11 (durability and work-preserved check), LAPTOP-ONLY / UNJUDGED.**
- Command: with the candidate applied, end one session normally and one abnormally (kill the terminal), and compare the outputs the four DEFERRABLE hooks produce (trace flush, ads_sync, session_writeback, session_delta_stop, and the `LEARNINGS_PENDING.md` the pipeline writes) against a baseline session of the same shape with the candidate not applied. Pass `--work-preserved` to the judge only when every output is present for the normal end.
- Sample size rule: one normal and one abnormal session per variant (n=2 each), at least 3 repeats before any claim.
- Falsifier: any output present in the baseline normal session and missing in the candidate normal session; an abnormal-end session that loses accounting the baseline kept per turn.
- Record to bring back: a listing of the produced output files (names and sizes only) for each of the four sessions.

**LP-12 (boundary suite with the real HOME), LAPTOP-ONLY / UNJUDGED.**
- Command: `python tools/test_hook_boundary.py` with the real HOME, once before and once after any registration change; save both outputs.
- Sample size rule: one run before, one after (n=2), full-count footers.
- Falsifier: either footer below full count; any gate line that differs between the runs; the duplicate-invocation sub-check, UNEVALUATED here, reports a duplicate.
- Record to bring back: the two outputs and a VERDICT line from `compare_runs.py`.

## 8. Decisions D5-01 to D5-12

| Decision | Content | Commits | Records |
|----------|---------|---------|---------|
| D5-01 | zero registration change | all Phase 5 commits leave `hooks/` untouched | `05-03-final-gates.txt` (empty diff) |
| D5-02 | inventory loaded structurally from the dispatcher | a522485e, 69e27e19 | `05-01-tracer.txt`, `05-01-suite.txt` |
| D5-03 | three closed classes with basis codes | 69e27e19 | `05-01-suite.txt` (41/41) |
| D5-04 | one thin tool and its suite | a522485e, 69e27e19 | `05-01-suite.txt` |
| D5-05 | Stop-chain classified entry by entry | 69e27e19 | section 2 |
| D5-06 | guard semantics with planted mutants | f7ce4a98 | `05-02-suite.txt` (59/59), `05-02-guard-live.txt` |
| D5-07 | boundary suite before and after under an isolated HOME | f18ff762, 7451bd0f | `05-01-boundary-before.txt`, `05-02-boundary-after.txt`, `05-02-boundary-compare.txt` |
| D5-08 | pure judge that refuses a non-laptop plane | afff74cb, aa124969, ae6fd9d9 | `05-03-suite.txt` (134/134), `05-03-collector-smoke.txt` |
| D5-09 | laptop items LP-09 to LP-12 | this commit | section 7 |
| D5-10 | privacy: repo-relative paths, no ids or user paths | all | the check below |
| D5-11 | liveness: offender set unchanged by name | f18ff762, 37129b7a | `05-01-reach-pre.txt`, `05-02-reach-post.txt`, `05-03-reach-final.txt` |
| D5-12 | historical timings are claims | this file | section 9 |

Privacy check (T-05-15): a grep for an absolute home prefix over every committed record, header lines removed, printed 0 after the final-gates script was made to rewrite its own home prefix; the committed records contain no user path outside `#` header lines. Collector files carry a unique session id per sample that is generated and never stored.

## 9. Unknowns and final gates

Final gate run, `records/05-03-final-gates.txt` (GEX44, one run, HEAD `ae6fd9d9`): a5_u6 13/13, arm preflight 23/23, bench integrity 53/53, bench gate 24/24, resource pressure 17/17, gsd_mission resources 17/17, gsd_mission baseline 21 passed 0 failed, hook critical path `CRITPATH_PASS=134/134`, `tools/test_git_invocation.py` exit 1 at 6/7. The 6/7 is the Phase 4 state (`04-03-final-gates.txt`: same 6/7, 14 NEW offenders and 2 frozen sites), unrelated to hooks and not edited. The bench_all blob `611681e6bec23f65bab05dee9d8dc87ec778ebb7`, the floors blob `8522b474e7264c2c8a9c2bfea3daf1e0d03970e0`, the ledger sha256 `cef10a59...32f4` and the floors sha256 `54a5f2af...dfdc09` equal the Phase 4 values. Reachability: 56 offenders before (`05-01-reach-pre.txt`), 56 now (`05-03-reach-final.txt`), 0 new, 0 gone, names unchanged by name (comparison printed in the gates record); no registry edit was needed. `tools/test_s9_redteam.py` was not re-run (814 s in Phase 4); its caveat stands as recorded in STATE.md.

What the Owner still does not know:
- No wall time of any real hook chain was measured in this phase, on any plane. VERDICT: NOT_SHOWN for every statement about waiting time.
- The 54.9 s Stop-chain figure and similar numbers in dispatcher comments are claims in a comment from the laptop era, unmeasured here (D5-12). They are not evidence in this file.
- Which events the laptop `settings.json` registers, and whether `SessionEnd` calls the dispatcher, were never seen by this phase (LP-09).
- The 51 UNKNOWN entries stay UNKNOWN; naming them is the output, classifying them needs evidence the repo does not hold.
- The minimum of 7 samples per arm and the J5 noise rule are proposed, not calibrated on any host.
- The only GEX44 result about the sampler is a shape smoke: with a decoy dispatcher `collect` produced 3 MEASURED samples with schema-2 host state, scope `SHAPE_ONLY`, and no timing figure, and the judge refuses such a file (`records/05-03-collector-smoke.txt`, n=3, decoy not a hook).
- The sampler under load: the first final-gate run showed a load near 118 on this shared host, which is why the timeout-kill gate was hardened in `ae6fd9d9`; it is a statement about the gate, not a measurement of a hook.
