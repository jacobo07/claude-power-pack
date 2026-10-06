---
phase: 02-kme-l-challenger
plan: 01
subsystem: kme-analytics
tags: [challenger, usage-index, kme_pillars, kme_replay, access-plan, ks-4, path-log, read-only-index]
requires:
  - phase: 01-usage-index-v5-substrate
    provides: tools/usage_index.py v5 population(select=kme, detail=True) with MEASURED / EXACT / DRIFTED / UNMEASURED verdicts
provides:
  - "kme_token_audit.scan_project(select=None): a file the select callable refuses is never opened, its session is still registered"
  - "kme_pillars access plans champion (default) / scoped / challenger / auto with the KS-4 forced behaviour, the index tier (guards index_open, kind, population), explicit --cross-project, redacted path log"
  - "kme_replay rank takes --plan / --index-db / --path-log / --cross-project through kp.add_plan_args and kp.resolve_logged"
  - "tools/test_kme_challenger.py: 8 hermetic V-KMEC-* gates, KMEC_PASS=8/8"
affects: [02-02, 02-03, 02-04, 02-05, 02-06]
plan_head_before: 23f5a7f1ee85736ceb67a2ba12b754e64a5cbcb7
actuals:
  tokens: 10154     # chars/4 over the +/- lines of wiki/tools and tools (git diff 23f5a7f1..HEAD, 40617 chars)
  tasks: 2
  commits: 2        # measured: git rev-list --count 23f5a7f1..HEAD (the docs commit of this summary comes after)
tech-stack:
  added: []
  patterns:
    - "challenger by extension: select hook in the frozen parser, tier routing in the owner, no new engine"
    - "read-only index via sqlite mode=ro URI, never usage_index.connect() (it runs the schema script)"
    - "refusals carry the guards passed so far, so the path log shows what held before the one that failed"
key-files:
  created:
    - tools/test_kme_challenger.py
  modified:
    - wiki/tools/kme_token_audit.py
    - wiki/tools/kme_pillars.py
    - wiki/tools/kme_replay.py
key-decisions:
  - "plan_taken vocabulary: champion | scoped | index | global | refused (a champion run is recorded as champion even when it carries a filter, because it is today's code path)"
  - "The index tier refuses --since (the index answers as of an instant) under guard kind, with the reason named"
  - "kme_replay reports a refusal as 'kme_replay: plan challenger refused: ...' (the tool name is the prefix); kme_pillars keeps its own prefix"
  - "A raw tier without --path-log does not walk the tree: read_files is 'unwalked' there, the walk is done only when a log is requested"
requirements-completed: [AO-07, AO-09, AOP-P]
duration: ~40min (start not timestamped; approximate)
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 01: Tracer and access plan Summary

**Pillar D (and kme_replay rank) now run from the sessions a read-only usage index selects, opening only those transcript files, with KS-4 forced plans, an explicit cross-project switch and a redacted path log; the champion path is unchanged and still pinned 89/89 plus a 20/20 mutation drill.**

## What was built

**Task 1 (tracer, commit 596d8460).** `scan_project(select=None)` skips `scan_file` for a refused file but still registers the session, so `corpus.sessions_scanned` does not depend on the selection (2 on the fixture, 568 on KME-L per RESEARCH). `kme_pillars` gained `--plan/--index-db/--path-log/--cross-project`, `_usage_index()` (lazy path load), `_open_index_ro()` (`mode=ro` URI), `PlanRefused`, and `_index_tier()` with guards `index_open`, `kind`, `population` (the index's own reasons are quoted on refusal). `_resolve` computes the index tier before the first measuring scan and, under `--until auto`, refuses with guard `shadow` instead of letting the locator bisect on a selected-only scan. `main` turns a refusal into exit 3 with nothing written.

**Task 2 (routing, commit aa961615).** `_prepare` validates the KS-4 combinations (exit 2). `_resolve` routes champion/scoped through today's code untouched, challenger through the index tier (refusal propagates), auto through the index tier with deopt to scoped raw (filter given) or global raw (`--cross-project` only), recording `ctx["deopt"]`. `report_path` writes one redacted JSON line per run to `--path-log` and prints `KMEP-PATH plan=... taken=... deopt=... read_files=...` for every non-champion run; `resolve_logged` is the single wrapper both producers call.

## Verification (observed)

```
python3 -I tools/test_kme_challenger.py
PASS V-KMEC-SCAN-PROJECT-DEFAULT default==None==all-admit: True; sessions base=2 refused=2; opens refused=0 control=3; select saw 3 files
PASS V-KMEC-TRACER-D-E2E masked front equal=True masked json equal=True; challenger opened ['agent-a1.jsonl', 'k1.jsonl']; champion opened [... 'n1.jsonl']; sessions_scanned=2
PASS V-KMEC-INDEX-READ-ONLY db unchanged=True connect() calls=0 rc=0/0 write refused on the ro connection=True 0444 copy opened 2 files
PASS V-KMEC-PLAN-ORDER ... ('auto','index','none','2') ... ('auto','scoped','index_open','unwalked') ... ('auto','global','index_open','unwalked') ... ('auto','index','none','3')
PASS V-KMEC-CROSS-PROJECT-EXPLICIT rows ... [('auto', 2, 0, 0, True), ('challenger', 2, 0, 0, True)]
PASS V-KMEC-KS4-FORCED no-flag==champion=True scoped==champion=True champion clean subprocess ... index opens by champion=0
PASS V-KMEC-PATH-LOG lines=3 shapes=[True, True, True] stderr_ok=True champion quiet=True canary in log=False redacted marker=True; taken=['index', 'scoped', 'refused']
PASS V-KMEC-REPLAY-PLAN L file equal (masked)=True; challenger opened ['agent-a1.jsonl', 'k1.jsonl']; ... path records=[('kme_replay', 'index')]; forced refusal rc=3 files=0
KMEC_PASS=8/8  threshold=8/8  skipped=0  inconclusive=0

python3 -I tools/test_kme_pillars.py            -> KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
python3 -I tools/test_kme_pillars.py --drill    -> DRILL-CONTROL 84/84 green, DRILL-CLEAN-AFTER-MUTANTS 84/84 green, DRILL killed=20/20
python3 -I tools/test_kme_replay.py             -> KMER_PASS=45/45  threshold=45/45  skipped=1  inconclusive=0 (the skip is V-KMER-BUNDLE-SUMMARY-UAT, no UAT file for phases 01-06 on this checkout; it skipped before this plan too)
python3 -I wiki/tools/kme_pillars.py d --denominator KME-L --plan bogus --root /tmp   -> exit 2
python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --plan auto --root /tmp  -> exit 2
```

Gate sensitivity (one-off monkeypatch mutants run from `/home/kobii/ao-scratch/p2/mut1.py`, `mut2.py`, not committed): select admits everything, read-write index open, scan_project ignoring select, path log without redaction, deopt that drops the filter, forced challenger silently served by raw, kme_replay ignoring the plan. Each went FAIL on exactly the gate meant to catch it. These are spot checks of the new gates, not a drill added to `test_kme_pillars.py --drill`.

## Deviations from Plan

**1. [Rule 2 - correctness] `--since` refused by the index tier.** The index answers as of an instant and cannot honour a lower bound; silently ignoring `--since` would make the challenger measure a different window than the champion. Added under guard `kind` with a named reason. Files: `wiki/tools/kme_pillars.py`. Commit 596d8460.

**2. [Rule 2 - correctness] `PlanRefused` carries the guards passed so far.** The path record must show which guards held before the failing one; the plan's `PlanRefused(guard, reason)` signature gained an optional third argument. Commits 596d8460 / aa961615.

**3. [Rule 3 - fixture] The fixture's KME session carries a `hook_additional_context` attachment.** Pillar D is UNMEASURED (exit 3) on a fixture with no such attachment, which would have made every happy-path gate exit 3. Fixture-only; the instrument is untouched.

**4. Transient state between the two commits.** The Task 1 commit refuses `--plan auto` (exit 2, "not routed yet") instead of running it as champion; Task 2 replaces that refusal with the routing. It never reached a state where `auto` silently ran as champion.

**5. Pre-commit assertion.** The worktree branch is `mission/autonomous-optimization-gen2`, outside the `agent-*` namespace the generic allow-list expects; the orchestrator pinned this branch and the root-pin guard passed (exit 0) before every commit, and `git.base-branch --is-protected` returned `false`. The namespace check was not applied.

**6. Requirement status left as is.** `requirements mark-complete AO-07 AO-09 AOP-P` flipped the AOP-P row to Complete; this plan is 1 of 6 and the pillar is not closed (equivalence, cross-project exposure table, stale-cache control and the beat-or-narrow decision belong to 02-03 .. 02-06), so the row was restored to Pending. `requirements-completed` in the frontmatter lists the IDs this plan advanced, not IDs it closed.

## Notes for the following plans

- **The index guard does not yet check that the index was built over the same tree as `--root`.** `population` is answered from the index alone; if the index covers a different projects directory than `--root`, selected `(project, session)` keys that are absent from the scanned tree simply open nothing, and the shadow check (auto + `--until auto` only) is the sole backstop. The watermark / root-identity guards listed for plan 02-03 are the place to close this.
- **With `--project-filter`, the index population is the scoped one and is compared with the global frozen KME-L.** It is EXACT only when the filter covers every project that holds a KME-L session; otherwise the guard `population: DRIFTED` fires (auto deopts, challenger refuses). That is the designed behaviour, but plan 02-04's real-corpus runs should choose the filter (or `--cross-project` without one) with this in mind.
- The index tier uses the `files.project` / `session_key` columns, matched against `os.path.basename(project dir)` and the first relative path component; this equals the key the champion uses on the fixture, including subagent files. Real-corpus equality (the 16 `_preserved` / `_empty_shells` pseudo-sessions) is plan 02-04's measurement.
- `KMEP-PATH` goes to stderr for every non-champion run; any consumer of kme_pillars stderr that treats extra lines as errors would need to skip that prefix (none found in the repo).

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. The new persisted record (`--path-log`) is T-02-03 and is covered by V-KMEC-PATH-LOG (canary absent, redaction marker present on a secret-shaped reason).

## Self-Check: PASSED

- FOUND: tools/test_kme_challenger.py, wiki/tools/kme_token_audit.py, wiki/tools/kme_pillars.py, wiki/tools/kme_replay.py
- FOUND commits: 596d8460, aa961615 (`git log --oneline`)
- `git show --stat` of each task commit lists only that task's files; no file outside `files_modified` was changed by the tasks.
