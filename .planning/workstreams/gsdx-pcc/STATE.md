---
gsd_state_version: "1.0"
current_phase: 6
status: planning
last_updated: "2026-10-13T00:00:00.000Z"
last_activity: 2026-10-13
progress:
  total_phases: 10
  completed_phases: 5
  total_plans: 17
  completed_plans: 17
  percent: 50
workstream: gsdx-pcc
created: 2026-10-07
current_phase_name: W5 Mutant farm
current_plan: Not started
stopped_at: Phase 5 CLOSED (Windows + Linux planes, 05-CROSS-PLATFORM.md); wave 5.2 (trust core) packet WU-P52 is the next compile (WU-P51 Part C)
---

# Project State

## Current Position

**Status:** Phase 5 CLOSED 2026-10-14 (planes: Windows laptop py3.12.10 for all claims; Linux GEX44 py3.12.3 for d3 + the 58-mutant verdicts; PORTABILITY only for those two, see `phases/05-*/05-CROSS-PLATFORM.md`). Next: wave 5.2 trust core (`packets/WU-P52.md`, compiled by WU-P51 Part C), then Phase 6.
**Current Phase:** 5.2 -- trust core (continuation plan row 5.2); Phase 6 W5 Mutant farm follows

**Old position line:** 5 -- W4 Judge VALIDATE vs REPLAY (Phase 4 complete 2026-10-13, see `phases/04-w3-candidate-snapshots-invalidation-proof-inheritance/04-VERIFICATION.md`)
**Last Activity:** 2026-10-13

## RESOLVED 2026-10-13 (coordinator, option a): WU-P4 mutation-suite decision

- **Result (Linux plane, GEX44, dc590090):** first run `GSDX_GOAL_MUTATIONS_CAUGHT=56/58`. Two drills were INVALID (`ANCHOR NOT FOUND`), not survivors: `closure-tree-ignored` and `proof-elsewhere-is-not-open-work`. Their anchors no longer matched, because Phase 4 edited `convergence.py:363` and `reconcile.py:210` for inheritance. Both were re-anchored to the current predicate, with the same mutant. Re-run `58/58`, rc=0, 68 s; the two drills were CAUGHT by `V-CONV-CLOSE-AT-OTHER-TREE` and `V-RC-REGATE-AFTER-TREE-MOVES`. Log: `phases/04-*/logs/04-mutation-gex44.log`.
- Original entry, kept for the record:

- **Question:** where and when is `tools/test_gsd_x_goal_mutation.py` run for Phase 4? It mutates LIVE files, hit a 270 s timeout on the laptop, and its kill left `judge.py` mutated (restored by `git checkout`, diff empty).
  **Options:** (a) coordinator runs it on the Linux plane (GEX44) at the Phase 4 head and labels the result "Linux plane"; (b) defer it to Phase 6's entry obligation (R11, isolated-copy incumbent measurement); (c) run it on the laptop in an isolated copy with a longer timeout.
  **Pick:** (a). Phase 4 added no judge or mutation-suite change, so the risk is low; the gate stays honest as UNRUN until then.

## RESOLVED 2026-10-14 (WU-P51, option a executed): Phase 5 Linux-plane runs

**Result:** coordinator ran d3 (KILLED) and the 58-mutant suite (58/58, 70 s) on GEX44 at 46d470e1 (`d057770f`). WU-P51 then made the suite mutate a disposable copy (`fdc0c18b`, hermetic gate 5/5, RED was 3/5), re-ran d3 on the laptop (KILLED), and ran 58/58 in a copy on Windows. Original entry kept below.

## (original) OWNER DECISION NEEDED 2026-10-13 (WU-P5): Linux-plane runs

- **Question:** who runs d3 and `tools/test_gsd_x_goal_mutation.py` for Phase 5, and when? Both were UNRUN on the laptop (d3 reaped for memory; the suite mutates live files).
  **Options:** (a) coordinator runs both on GEX44 at the Phase 5 head and labels them "Linux plane"; (b) defer to Phase 6's entry obligation (isolated-copy incumbent measurement).
  **Pick:** (a). Phase 5 kept every anchor line intact, so the risk is low, but a changed judge.py may move an anchor; re-anchor and record if so.

## Session Continuity

Fresh context: read, in order, `vault/specs/gsdx-proof-conserving-convergence.md`, this workstream's `ROADMAP.md`
(operating constraints first), `DENOMINATOR.md`, then the latest phase `EVIDENCE.md`. Do not reread the
2111-line dataset end to end: open only the § numbers a denominator row cites.

Position (worker epoch 3, 2026-10-07): Phase 1 complete (61f67459). Phase 2 context committed (d7168944). Phase 2
plan-phase is running: the researcher writes `phases/02-.../02-RESEARCH.md`; the planner and checker follow. If a
fresh worker finds 02-RESEARCH.md present and no 02-*-PLAN.md, resume with `/gsd-plan-phase 2 --ws gsdx-pcc`
(it reuses existing research).

## Decisions

- D-O1..D-O4 recorded in the spec (worktree, software_construction family, io-chatgpt-plugin pilot, PROBATION ceiling).
- 2026-10-07 (worker epoch 2): Phase 1 plans run inline in the main session with PowerShell. Reason: subagents have no PowerShell tool, and the Windows Bash guard blocks git and python there. Safe: execution order only; the artifacts are unchanged.
- 2026-10-07: V-RB is 16 gates, not the plan's 15. The added gate is V-RB-GUARD-EXCLUDES-ONLY-NAMED, for the sweep_heartbeat.json confound measured in 01-01. Safe: one more gate, and its control still trips.
- 2026-10-07: The 01-04 liveness freeze was re-applied as an order-preserving known_orphans-only rewrite. Reason: `--baseline` re-sorts the whole registry (sort_keys), which puts hunks outside known_orphans, and the plan forbids those. Safe: the list is identical to the tool's own output, every other key is checked equal, and it is reversible by git.
- 2026-10-07: The 01-05 suites were measured by one background driver script (one guarded `suites` call per suite, `--runs 3`). Reason: it stays serial and avoids the 600 s cap per tool call. Safe: same instrument, same rows; a guard trip stops the driver.

- 2026-10-07: `.gsd/`, the workstream `config.json` and `milestone.lock` (gsd-tools runtime state) are excluded through the common `.git/info/exclude` and are neither committed nor added to `.gitignore`. Safe: local only, reversible, and names only gsdx-pcc paths.
- 2026-10-07: The in-copy run of the mutation suite was killed by the memory-pressure reaper and NOT restarted (harness policy). It is recorded UNKNOWN in 01-INCUMBENT.md. Re-run when RAM allows (command in 01-05-SUMMARY.md).
- 2026-10-07 (Owner, 20:05): the mutation-suite timing stays UNKNOWN in Phase 1. It becomes the ENTRY OBLIGATION of Phase 6 (DENOMINATOR R11; ROADMAP Phase 6 "Entry obligation"). Phase 6 measures the incumbent in an isolated copy before any speedup claim. Worker epoch 3 added the tool's required `--out`/`--log-dir` to the recorded command, because the short form exits with an argparse error (`tools/gsdx_reality_baseline.py:370-371`).
- 2026-10-07 INCIDENT (worker epoch 2): verification returned `human_needed` (7efe5322, 16:24 +0200), and the worker ended its turn on a question to the Owner inside an UNATTENDED mission. The mission parked BLOCKED until the Owner answered at 20:05 (about 3h41m, next commit baf27b86 at 20:12). Every human_verification item except the mutation decision was a command the worker could run itself (01-verify-*.log). RULE from now on: when verification returns human_needed, run the checks yourself, or record the decision per the mission card's DECISION GATE (OWNER DECISION NEEDED with options and a pick), then continue. Never end a turn on a question. UKDL candidate T-UNATTENDED-HUMAN-NEEDED-ENDS-TURN-ON-QUESTION-PARKS-MISSION-001.
- 2026-10-07 (worker epoch 3): Phase 1 verification set to `passed` after the four UNCERTAIN rows were verified from committed logs (01-verify-{vrb,vtl,gate-provider,git}.log at baf27b86). The registry hunks were re-read and all fall inside `known_orphans`.
- 2026-10-07 (worker epoch 3, Phase 2 research open questions; 02-RESEARCH.md:506-512). The worker takes the researcher's recommendations. Each is internal and reversible by git:
  - (1) Land only `obligation.contract` + `proof.*` event types as code now. The Phase 3-8 event types are frozen as a spec table plus a discovered collision gate, because the Reality Contract bars constants with no projection. This narrows the CONTEXT wording "land their event types".
  - (2) Commit a byte copy of the g-002/g-001 logs (~163 KB, private repo) behind a secret/PII grep gate. A synthetic generator covers the 9 legacy type strings the corpus lacks.
  - (3) The `unknown:` tree-equality defect (G2) is NOT fixed in the zero-change seam. It becomes DENOMINATOR R12 with a Phase 4 RED fix.
  - (4) Kill switches are env-only in Phase 2. Any value other than unset/on/1/true/yes means OFF, so a typo falls back to legacy. Flag files are decided with Phase 3's first consumer.
  - (5) `test_gsd_x_goal_mutation.py` stays out of the Phase 2 gates (R11).
- 2026-10-07 (worker, W1 ULTRA phase 1-3): spec S2 proof states resolved -- precedence changed > unknown > all-equal-with-event; SUPERSEDED derived by strength; legacy mapping = _needs_a_gate_here. Reason: 02-RESEARCH G3-G5; internal and reversible by git.
- 2026-10-07 (worker, ULTRA Q&A Q1 auth): none. No credentials are involved; authority is the producer code path (S3: proof.produced only from the gate receipt, proof.inherited only by the reconciler). Reason: spec S3, 02-RESEARCH G16.
- 2026-10-07 (worker, ULTRA Q&A Q2 env vars): `GSDX_FRONTIER` and `GSDX_PROOF_INHERITANCE`, read at call time, off for any value but unset/on/1/true/yes (S10); tests redirect `GSDX_GOALS_ROOT`, HOME and USERPROFILE. Reason: spec S10, 02-RESEARCH section 5.
- 2026-10-07 (worker, ULTRA Q&A Q3 file paths): the paths in 02-01-PLAN.md Artifacts (`modules/gsd_x/goal/proof.py`, the two `tools/test_gsd_x_goal_pcc_*.py` suites, `tools/fixtures/gsdx_legacy_goals/**`, the golden). Reason: 02-01 plan, spec S7 and S11.
- 2026-10-07 (worker, ULTRA Q&A Q4 edge cases): empty premise set = UNKNOWN, adjacent equal certificates = later supersedes, unknown: bindings never equal, ordering by log seq (S2, S4, S13), plus `v` greater than 1 = UNKNOWN not raise, re-accept changes claim_id, interleaved seq-valued fields, CRLF fixtures. Reason: 02-RESEARCH pitfalls 3-4, G6, G12.
- 2026-10-07 (worker, ULTRA Q&A Q5 success criteria): ROADMAP Phase 2 criteria 1-3 plus the S-item gates named in the spec. Reason: ROADMAP Phase 2.
- 2026-10-07 (worker, ULTRA Q&A Q6 scope): Phase 3-8 event types are frozen in the S7 table only, no legacy file is edited, R12 (unknown: tree equality) is deferred to Phase 4. Reason: STATE decisions 1 and 3.
- 2026-10-11 (worker, W1 ULTRA phase 4-5): audit 6 gaps -- 6 injected, 0 deferred, 0 rejected (02-AUDIT.md).
- 2026-10-12 (Owner, option b on OWNER DECISION NEEDED): `V-PCC-ADDITIVE-ONLY` is scoped to the Phase 2 commit range by git history (`98609c4f..0fca7111`: no legacy goal file changed, `proof.py` the only added module), with a control over a range that did edit them. No hash is re-pinned. Phase 3 edits `epoch.py`, `reconcile.py`, `sweep.py` and adds `frontier.py` on purpose. Suite 48/48. Reason: the gate proves the Phase 2 seam was additive; later phases are judged by their own gates.

## Owner steps

- OWNER STEP (not done by the mission; it is a global file under `~/.claude`, which the mission must not edit): change the routing of `human_needed` in the global `gsd-autonomous` skill and workflow (`~/.claude/gsd-core/workflows/autonomous.md`). In an UNATTENDED run it should run the human_verification commands itself, or record OWNER DECISION NEEDED and continue, never end the turn on a question. Source: the epoch-2 incident above.

## Blockers

None open for Phase 3. Carry to Phase 4: executed speculation and racing (D25/D26 report-only today); the frontier suite at 298ba2c6 was verified on the Linux plane only (laptop runs were killed for low memory).

Open measurement gap carried to Phase 6 as R11: incumbent `test_gsd_x_goal_mutation.py` is UNKNOWN (memory-pressure reaper; see 01-05-SUMMARY.md).
</content>
</invoke>
