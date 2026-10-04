---
gsd_state_version: "1.0"
milestone: v1
current_phase: 4
current_plan: 4
status: verifying
stopped_at: Completed 04-04-PLAN.md
last_updated: "2026-10-03T23:38:29.832Z"
state_head: 622e57030ae49b99d96359fd0708554f315cab95
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 13
  completed_plans: 13
milestone_name: incremental-cognition
last_activity: 2026-10-03
workstream: incremental-cognition
created: 2026-10-03
current_phase_name: Cognitive cost regression gate
last_activity_desc: Workstream created from the approved incremental-cognition program
---

# Project State

## Mission

Incremental Cognition Program: a delta over cognitive-economy and skill-capability. Drive pillars A-N to
evidence-backed terminals. Mission terms: incremental-cognition, context-rent, institutional-memoization,
invalidation, cognitive-compiler, baseline-ratchet.

## Current Position

**Status:** Phase complete — ready for verification
**Current Phase:** 4
Current Plan: 4
Total Plans in Phase: 4

## Decisions

- [Plan / audit G1]: the CE verifier's stale V-CEP-REAL-HANDOFF is replaced in the wrapper (SC precedent); the CE
  file is never edited. The defect is handed to the CE owner.
- [Audit G3]: consuming pillars (H, I, J, M) close only through R2 against the owner ledger at a commit on HEAD.
- [Audit G4]: pillar A design = a non-blocking status for a worktree the predecessor provably worked in; the Brand
  #001 shape stays blocked.
- [Audit G6]: the gsd_mission.py repair is deployed only at >= 4 GB free RAM.
- [Plan]: arming waits for pillar A and >= 4 GB free; until then phases run in the interactive pane.
- [Phase 2 close, unattended 2026-10-03]: verification human_needed (8/8 automated, PRGs Owner-run) -> recorded verification_deferred_human, autonomous run continues at Phase 3 as with Phase 1 (phases 3-4 depend on nothing; safe, reversible, internal). Review WR-01..07 fixed before verification; WR-08 merge strategy is an Owner note in the bundle.
- [Phase 3 plan, unattended 2026-10-03]: research skipped -- 03-CONTEXT already carries the pre-research (existing kme_* instruments, measurement definitions, plane constraint); stdlib build over a known transcript format. Nyquist VALIDATION.md therefore not produced; plans carry their own V-KMEP-* gates. Reversible: `/gsd-plan-phase 3 --research` re-runs it.
- [Phase 3 close, unattended 2026-10-04]: verification human_needed (7/7 GEX44-plane, no gaps; D..I terminals need KME-L laptop runs) -> verification_deferred_human, run continues at Phase 4. Review WR-01..07 + IN-01 fixed before verification. Notable smoke fact: H clears 3 % on both GEX44 workloads (verifier subagents), contrary to its prediction -- KME-L decides.
- [Phase 4 plan, unattended 2026-10-04]: research skipped (04-CONTEXT carries the pre-research). Checker: round 1 5 warnings (W1 harness-by-type scope hole) fixed by revision; round 2 passed except R2-W1 (reference not content-pinned) -> carried as an explicit orchestrator requirement into the 04-01 / 04-03 executor dispatch (window_sha256 + window_rows in provenance, append-after-first-assistant gate, REAL re-read gate) instead of a third revision round.
- [Phase 4 execute, unattended 2026-10-04]: 4 plans run sequentially in ic-run (use_worktrees=false), each verified by the orchestrator re-running tools/test_floor_regression_gate.py (26 -> 40 -> 59 -> 60/60, drill 13/13). R2-W1 applied: window_sha256/window_rows in provenance (04-01), V-FLOOR-WINDOW-APPEND-STABLE (04-01), V-FLOOR-REAL-REFERENCE-PINNED vs transcript 34f03871 (04-03, PASS on GEX44). The 04-02 executor ended once without a report with task 2 uncommitted but green (40/40): reconciled from git log + disk and resumed the same agent (no re-dispatch). The begin-phase pointer was still phase 2: fixed in 15f70abe. IC-K addressed, not satisfied; state.K OPEN.
- [Phase 4 review, unattended 2026-10-04]: 04-REVIEW 2 critical / 3 warning / 2 info (f5be1ec6). Fix decisions (reversible, internal): CR-01 unparseable window line -> exit 2; CR-02 hook source stored as sha256 key + basename, reference-gex44.json regenerated from 34f03871 (committed copy scanned: no credential-shaped value, only 2 benign hook commands); WR-01 wholly absent large layer -> exit 2; WR-02 uncorrelated hook element -> unattributed; WR-03 unmeasured tokens axis -> exit 2 unless explicit --chars-only (WITHIN_BOUND_CHARS_ONLY), owner-bundle [K] and evidence/K.md follow.
- [Phase 4 close, unattended 2026-10-04]: verification human_needed (8/8, no gaps; review fixes re-verified 67/67, drill 18/18) -> verification_deferred_human, run continues at Phase 5 (depends on Phase 3 only; safe, reversible, internal). IC-K unticked, state.K OPEN.
- [02-03]: a renewed successor inherits the hold of its nearest predecessor that has an owner (`provider_breaker.lineage_hold`,
  bounded by a seen-set and MAX_LINEAGE_HOPS=4); a re-login after the refusal still releases it.
- [02-03]: the env preflight gates launches only on a declared plane (CPP_ENV_PREFLIGHT=on, or CPP_MISSION_PLANE set and
  CPP_ENV_PREFLIGHT not off). Only a MEASURED NOT_READY refuses; UNMEASURABLE, a raising preflight and an unknown verdict
  launch and are ledgered `launch_preflight_unmeasurable` (never READY). Kill switches CPP_LAUNCH_GATE=off / CPP_ENV_PREFLIGHT=off.
  `gsd_mission.py arm` stays ungated (named debt, 02-04 records it).
- [Phase 2]: [02-04] Hook scripts are restored by the deploy itself (registered-but-missing only, own hooks dir, never overwrite): install_global_core.py does not copy hooks
- [Phase 2]: [02-04] A dirty install or non-ancestor env head is a refusal result; real a5 (1024 modified) and a7 (1 modified) both refuse exit 4, the Owner decides; ledger state.B/state.C and IC-B/IC-C stay open (PRGs Owner-run)
- [Phase 3]: [03-01] --until defaults to the freeze instant (16:13:37Z) for frozen denominators KME-L/KME-G; live corpora grow, so only the window reproduces the frozen population (unwindowed GEX44 scan already reads 14 active / 1679 calls vs frozen 13 / 1322)
- [Phase 3]: [03-01] terminal_evidence requires primary role AND exact population AND a measured (non-UNMEASURED) verdict; KME-G smoke is evidence_role smoke, never terminal. D on KME-G STRADDLES 2.6-4.0 %, B001 sample < 3 %; IC-D stays open pending the laptop KME-L run
- [Phase 3]: [03-02] E adds an eighth class 'unhashable' for image Read results (text_of renders every image as '[image]', hashing it would equate different images); in neither bound
- [Phase 3]: [03-02] F pairs a doc delivery with an init.* result only within the same (transcript file, human-prompt turn); ratio is null (never 0) when no turn holds both; KME-G smoke: E 140 first/0 identical (< 3 %), F 0.69-1.03 % (< 3 %), init 2 calls, 1 paired turn ratio 6.29; no second workload required; IC-E/IC-F stay open pending laptop KME-L
- [Phase 3]: [03-03] G matches any candidate kind (re-test or relitigation) against any record kind (falsified or sealed); sealed samples show the id as written (D-03), matching normalizes it (D-3)
- [Phase 3]: [03-03] H blanks heredoc bodies and quoted strings and skips file-reading programs and package installs before matching VERIFY_CMD_RE; H details split the CE P definition part from the verifier-subagent part
- [Phase 3]: [03-03] KME-G smoke: G strict 0 / loose 0 (corpus has no falsification statements, 0 samples for the hand precision check); H share 7.3-7.4 percent, driven by verifier subagents (CE P definition part 0.2-0.3 percent); second workload GEX44-B001 H 8.7-9.1 percent; neither is a terminal
- [Phase 3]: [03-04] total scans of a run never exceed 24: locator 23 (the freeze scan counts as one) plus one reserved for the final measuring scan at a located cutoff; exact-at-freeze reuses the first scan (one scan in total)
- [Phase 3]: [03-04] the locator tries two candidates at the smallest call instant reaching the frozen call count: the instant itself, then the instant just before the next call (a later prompt-only session changes sessions_dead without adding a call); both only on an every-field match
- [Phase 3]: [03-04] a located cutoff keeps sub-second precision (fmt_instant); truncating to whole seconds would drop the lines of the located second
- [Phase 3]: [03-04] CPP-D-W7 is referenced: share judged against the CE ledger weighted figure, observability = min(1, coverage) x the pillar's own, primary file terminal only at coverage >= 1 and a measured verdict; its window and selection are fixed (--select/--since/--until/--freeze-instant/--label refused)
- [Phase 3]: [03-04] population exits 0 when the frozen population is reproduced, a referenced one is fully covered, or the workload is unfrozen; 3 otherwise; per_project rows come from the KME-selected sessions only; it writes nothing
- [Phase 3]: [03-04] I on KME-G (smoke, plane gex44, not terminal): 8.26 % of the weighted denominator, second workload B001 17.25 %; ledger state.I stays empty, IC-I/IC-D/IC-E not ticked, requirements.mark-complete not called
- [Phase 3]: [03-05] R3 lives only in the program-owned wrapper: a kme_pillars file supports a terminal only as primary with terminal_evidence true, or second_workload (valid) beside such a primary; smoke and cross-pillar files never; another instrument's files are skipped; ICP_PILLAR_<P> printed by --pillar
- [Phase 3]: [03-05] second workloads accepted for E (advisory 2): any instrument-written second_workload file with second_workload_valid true beside a terminal KME-L primary -- CPP-D-W7 at coverage >= 1 (named in the bundle), a KME-G run with an exact population, or a named OTHER workload; the claim stays in the KME-L primary and KME-G cannot stand in for it (R3 refuses a second workload without a terminal primary); independence is argued at close time in evidence/E.md
- [Phase 3]: [03-05] bundle [D]-[I]: population proof UNFILTERED first (P0 dir list never recorded), fourteen-commit cherry-pick list preceded by the conditional FROZEN_AT pick d4d35059, replayed in a scratch clone from 18e928af (KMEP 82/82); commands NOT RUNNABLE HERE, proven only to parse (11 parsed)
- [Phase 3]: [03-05] phase 3 closes on GEX44 with every pillar D-I OPEN: ledger state.D..I empty, IC-D..IC-I unticked, requirements.mark-complete not called; terminals wait for the six laptop KME-L files; evidence/phase3.md Status OPEN
- [Phase 4]: [04-01] R2-W1 items 1-2 applied (window_sha256/window_rows via one window_digest, V-FLOOR-WINDOW-APPEND-STABLE); floor gate core built, drill 8/8; IC-K addressed not satisfied
- [Phase 4]: [04-02] hook/skill/agent scope attributed by registration or file under <cwd>/.claude vs <install_home>/.claude; unreadable settings and a cwd absent on this host stay unattributed; plugin ns:name with no project file is filed universal (stricter side); deltas per source so relabels are cost-neutral
- [Phase 4]: [Phase 04-03]: R2-W1 item 3 applied: committed reference-gex44.json pins window_sha256/window_rows from window_digest; V-FLOOR-REAL-REFERENCE-PINNED re-reads transcript 34f03871 from disk (SKIP, never PASS, when absent); --probe is stub-only behind a test fence; IC-K still not satisfied (laptop reference in 04-04)
- [Phase 4]: 04-04: pillar K stays OPEN (state.K {}, IC-K unticked); [K] bundle item carries laptop reference + PRG; R2-W1 pin of reference-gex44.json named in evidence/K.md

## Session Continuity

**Last session:** 2026-10-03T23:38:29.750Z

**Stopped At:** Completed 04-04-PLAN.md
`tools/test_gsd_mission_cwd_align.py` has 4 NEW uncommitted cases (V-MCA-DIVERGED-FOLLOWED / -UNPROVEN /
-STALE-ROADMAP / -THREE-RELAYS) calling `gm.align_cwd(cwd, wt, proven_workstream="ws")`; the
`threshold=9/9` line still needs 13/13. Not yet run (expected RED: align_cwd has no proven_workstream).
**Next exact action:** run `python tools/test_gsd_mission_cwd_align.py` -> confirm RED; then in a SCRATCH copy
of tools/gsd_mission.py add `proven_workstream=None` to align_cwd: in the diverged branch return
`diverged_followed` (NOT in CWD_ALIGN_BLOCKING) iff proven_workstream and work_dir is a worktree top of the
same repo and `_worktree_carries_workstream(work_dir, cwd, proven_workstream)`; at supervise ~1481 split
`ew = effective_workdir(...)`, `work_dir = ew or rec.get("work_dir")`, pass
`proven_workstream=rec.get("workstream") if ew and ew != rec["cwd"] else None`, ledger event
`cwd_diverged_followed`. Run cwd_align + test_gsd_mission + test_gsd_epoch + legacy golden; mutation drill;
deploy into the live file only at >= 4 GB free RAM (audit G6).
**Update 2026-10-03 (session c47b1f78):** RED confirmed (TypeError on proven_workstream). Fix written in a
SCRATCH copy only (`%TEMP%\claude\...\c47b1f78-...\scratchpad\droot\tools\gsd_mission.py`; live file sha256
D5324568... untouched): align_cwd(proven_workstream) -> `diverged_followed`; supervise splits `ew`, sets
`proven_ws` only when `ew and ew != rec["cwd"]`, ledgers `cwd_diverged_followed`. Gap found: nothing tested the
supervise wiring -> 3 new gates V-MCA-SUP-PROVEN-PASSED / -RECORDED-NOT-PROOF / -BASE-NOT-PROOF (repo test file
now 16/16 threshold; RED against the live module until deploy). Against scratch: cwd_align 16/16,
test_gsd_mission 213/213, test_gsd_epoch 82/82, legacy golden 32/32; mutation drills m1-m7 all KILLED (controls valid; specs in scratchpad\drills).
**DEPLOYED + committed d2505df6** (Owner go; 8.1 GB free; live sha A217654F..., pre-deploy backup in the session
scratchpad). Live tree: cwd_align 16/16, test_gsd_mission 213/213, test_gsd_epoch 82/82, golden 32/32.
Note: m-fdefb0fca0c0 (cognitive-economy) and m-876f8b5a904a (ucep) were already RUNNING epoch 2 before the
deploy (relaunched 16:10 / 17:01 UTC on "owner dead"); the fix applies from their next relay on.
**Next:** obligation 5 -- arm `gsd_mission.py arm --workstream incremental-cognition` (12/24h), needs Owner go
on WHERE (local RAM swings 0.6-8 GB; GEX44 own clone is the alternative).
**Resume File:** None

## Deferred Verification

| Phase | State | Resume |
|-------|-------|--------|
| 1 | verification_deferred_human | owner bundle [A] (laptop PRG), then /gsd-verify-work 1 |
| 2 | verification_deferred_human | owner bundle [B]/[C] (a7 re-login, env deploys, laptop PRG), then /gsd-verify-work 2 |
| 3 | verification_deferred_human | owner bundle [D]..[I] (KME-L laptop runs, population proof first), then /gsd-verify-work 3 |
| 4 | verification_deferred_human | owner bundle [K] (laptop reference + PRG; WR-01..03 policy judgement), then /gsd-verify-work 4 |

## Performance Metrics

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 2 P01 | 35min | 3 tasks | 3 files |
| Phase 02 P03 | 40min | 3 tasks | 4 files |
| Phase 02 P04 | 1h | 3 tasks | 7 files |
| Phase 3 P01 | n/m (session interrupted) | 3 tasks | 5 files |
| Phase 03 P02 | 40min | 3 tasks | 4 files |
| Phase 03 P03 | 40min | 3 tasks | 5 files |
| Phase 3 P04 | 10min | 3 tasks | 4 files |
| Phase 03 P05 | 11min | 3 tasks | 6 files |
| Phase 04 P01 | ~1h | 3 tasks | 2 files |
| Phase 04 P02 | 40min | 2 tasks | 2 files |
| Phase 04 P03 | 50min | 3 tasks | 3 files |
| Phase 04 P04-04 | 20m | 2 tasks | 3 files |

## Session Continuity (GEX44 run, 2026-10-03 ~19:00Z, session 607795c4)

Run branch `mission/incremental-cognition-run` in worktree `.claude/worktrees/ic-run` (never pushed; the
clone root stays on `mission/incremental-cognition`). `.planning/config.json` has `workflow.use_worktrees=false`
(single-plan sequential waves run in this worktree; harness worktrees would fork from origin default).

- Phase 1: deferred human verification (PRG laptop-plane, owner bundle [A]).
- Phases 3-6: CONTEXT.md written and committed (discuss skipped). Phase 6 J/M R2 externally blocked (CE/SC
  ledgers have no terminals on this history; CE 21671d6c absent from this clone).
- Phase 2: 4 plans, checker PASSED after one revision. Wave 1 (02-01, code 5962571c), wave 2 (02-02, code
  4c31bb0a) and wave 3 (02-03, code 60e7947d: LG 19/19, drill 6/6, six-suite FAIL lists identical to baseline, one
  gsd_mission.py hunk at old-start 1544) DONE. IC-B / IC-C deliberately left unticked (requirement = ledger terminal).
**Next exact action:** `/gsd-execute-phase 2 --no-transition --ws incremental-cognition` resumes at wave 4
(02-04 repeatable deploy + evidence C.md/B.md + [B]/[C] owner-bundle lines, incl. the `arm` ungated DEBT line),
then phase verification; then `/gsd-autonomous --ws
incremental-cognition` continues at Phase 3 (plan from its CONTEXT). Note for 02-03: every deployed a5/a7 install
reports `interpreters` UNMEASURABLE (no vendored engine range) -- must not churn launches.
