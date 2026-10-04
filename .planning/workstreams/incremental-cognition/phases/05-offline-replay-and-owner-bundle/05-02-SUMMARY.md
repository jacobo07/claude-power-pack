---
phase: 05-offline-replay-and-owner-bundle
plan: 02
subsystem: measurement-instrument
tags: [kme, pillar-L, offline-replay, upper-bound, unmeasured-never-zero, mutation-drill, smoke]

requires:
  - phase: 05-offline-replay-and-owner-bundle
    provides: kme_replay.py rank core (05-01)
provides:
  - ranking contract hardened to the phase goal: only MEASURED candidates rank, UNMEASURED listed with reason and no number
  - seams split_ranking, bound_label, strict terminal_ok in wiki/tools/kme_replay.py
  - 16 new V-KMER-* gates (36 total) and a 13-mutant drill
  - vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md (smoke, plane gex44, never terminal)
affects: [05-03 wrapper R3 extension and laptop code sync, 05-04 bundle summary]

actuals:
  tokens: 14440
  tasks: 3
  commits: 3
plan_head_before: d9ffd1eda157d6cf1dd05b12f334db64acb6bb44
commits: 3

tech-stack:
  added: []
  patterns:
    - "the seam decides: rank_candidates receives every candidate and ranks only entries that carry a number, so a mutant that reads a missing figure as 0 is seen by the gates"
    - "terminal eligibility is one function (terminal_ok) the drill can attack"

key-files:
  created:
    - vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md
  modified:
    - wiki/tools/kme_replay.py
    - tools/test_kme_replay.py

key-decisions:
  - "rank_candidates takes entries whose upper_bound_weighted may be None (UNMEASURED) and never ranks them; split_ranking builds ranked + unranked from {candidate: measured | UNMEASURED | None}"
  - "terminal_ok is strict: a missing frozen-source record is not the committed source (None -> False)"
  - "a located-cutoff failure is reported as cutoff_not_found before population_not_reproduced (the kme_pillars _match turns it into drifted, which would otherwise hide the more specific reason)"

requirements-completed: []   # IC-L addressed, NOT satisfied: only a ledger terminal satisfies it (KME-L laptop run + Owner decision, 05-03)

coverage:
  - id: D1
    description: "ranked holds only MEASURED candidates, highest upper bound first, ties in the fixed candidate order; unranked holds each UNMEASURED candidate with a reason and no number; a measured zero ranks; drift or an unlocated cutoff makes all three UNMEASURED; exit 0 / 3 / 2"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-CONTRACT-E2E, V-KMER-RANK-ORDER, V-KMER-RANK-TIE-DETERMINISTIC, V-KMER-UNMEASURED-NEVER-ZERO, V-KMER-MEASURED-ZERO-RANKED, V-KMER-DRIFT-ALL-UNMEASURED, V-KMER-CLI-USAGE; drill M6 M7 M8 M12"
        status: pass
    human_judgment: false
  - id: D2
    description: "one weighted denominator for all three shares (selected active sessions, main and subagent calls); every ranked entry an upper bound read against 3 % on the bound; terminal only for an exact KME-L primary with the committed frozen source and nothing unranked"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-SAME-DENOMINATOR, V-KMER-SELECTED-ONLY, V-KMER-UPPER-BOUND-LABELS, V-KMER-TERMINAL-EVIDENCE; drill M10 M11 M13"
        status: pass
    human_judgment: false
  - id: D3
    description: "the ranker leaks no transcript content, is read-only on corpora, never writes into a scanned root, never overwrites, and locates the frozen cutoff"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-NO-SECRET, V-KMER-READ-ONLY, V-KMER-OUT-DIR-INSIDE-ROOT, V-KMER-NO-OVERWRITE, V-KMER-UNTIL-AUTO"
        status: pass
    human_judgment: false
  - id: D4
    description: "the ranker ran once on the real KME-G corpus; the file is committed as smoke (plane gex44, terminal_evidence false) and the a5 / a7 / b001 trees are unchanged"
    requirement: IC-L
    verification:
      - kind: integration
        ref: "L-KME-G-2026-10-04.md front matter check (KMER_SMOKE missing=[]); find snapshot diff of the three env trees empty"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-04
status: complete
---

# Phase 5 Plan 02: Ranking contract, safety gates and KME-G smoke Summary

**The ranker's contract is now pinned from both poles: only MEASURED candidates rank (highest upper bound first, ties in fixed order), an UNMEASURED candidate is listed with a reason and never a number, all shares divide by one weighted denominator, and a 13-mutant drill kills each way it could mislead; it ran once on the real KME-G corpus and the smoke ranking is committed (plane gex44, never terminal).**

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | bb5fb71a | test(incremental-cognition): L -- ranking contract end to end (UNMEASURED unranked, never 0; one denominator) |
| 2 | a08de708 | feat(incremental-cognition): L -- ranker contract and safety gates, terminal_ok seam, drill 13/13 |
| 3 | 30611813 | feat(incremental-cognition): L -- offline replay ranking smoke on KME-G (plane gex44, never terminal) |

## Gate output (final, observed after Task 3)

```
KMER_PASS=36/36  threshold=36/36  skipped=0  inconclusive=0          (python3 tools/test_kme_replay.py)
PASS DRILL-CONTROL unmutated run: 34/34 gates green
KILLED M1..M13 (each by its named gate; M6 RANK-ORDER, M7 UNMEASURED-NEVER-ZERO, M8 RANK-TIE-DETERMINISTIC,
                M10 SAME-DENOMINATOR, M11 SELECTED-ONLY, M12 DRIFT-ALL-UNMEASURED, M13 TERMINAL-EVIDENCE)
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 34/34 gates green
DRILL killed=13/13
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0          (python3 tools/test_kme_pillars.py)
ICP_SELFTEST=PASS
KMER_SMOKE file=['vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md'] missing=[]
```

`V-KMER-READ-ONLY` printed PASS (posix). The suite runs in well under 1 s. Ledger `state.L` is `{}`; IC-L unticked.

## RED / first-run record

- **Task 1: V-KMER-CONTRACT-E2E was NOT red.** It passed on its first run (the 05-01 core already met the contract at the CLI level): exit 3, W 4085.0, ranked identical_rereads 2300.0 then unchanged_precondition_retries 235.0, late_rollover UNMEASURED (observability 0.0) with no number. Its red is shown by drill M7 (an UNMEASURED candidate ranked as 0.0), which V-KMER-UNMEASURED-NEVER-ZERO catches. No fix was needed in Task 1; the commit holds only tools/test_kme_replay.py. The hand derivation matches the plan's model exactly (no recomputation needed: 05-01 recorded no change to the tracer numbers).
- **Task 2 gates RED before the build (4 of 15):** V-KMER-UNMEASURED-NEVER-ZERO (no `split_ranking`), V-KMER-UPPER-BOUND-LABELS (no `bound_label`), V-KMER-DRIFT-ALL-UNMEASURED (the reason did not name `population_not_reproduced`), V-KMER-TERMINAL-EVIDENCE (`terminal_ok(primary, exact, None, [])` returned True; the terminal reason did not name the unranked candidate or the non-default frozen source). **Passed on first run, red shown by the drill instead:** RANK-ORDER (M6), RANK-TIE-DETERMINISTIC (M8), SAME-DENOMINATOR (M10), SELECTED-ONLY (M11); MEASURED-ZERO-RANKED, NO-SECRET (canary in five places, command-signature path exercised), READ-ONLY, OUT-DIR-INSIDE-ROOT, NO-OVERWRITE, UNTIL-AUTO (bisect, late retry not counted), CLI-USAGE are inherited-safety or pole-pair gates with no 05-02 mutant (the plan lists none for them).

## Pillar L smoke on KME-G (GEX44; facts about the instrument, NOT the KME-L ranking, not a reason to spend quota)

Command (exit 0, 3.7 s): `python3 wiki/tools/kme_replay.py rank --denominator KME-G --until auto --expand --root /home/kobii/a5-env/home/.claude/projects --root /home/kobii/a7-env/home/.claude/projects --root /home/kobii/b001-env/home/.claude/projects --root /home/kobii/.claude/projects`

- population_match exact, `until_located` exact_at_freeze, 1 scan (freeze instant 2026-10-03T16:13:37Z); 13 active / 151 dead sessions, 1,322 calls, weighted 54,899,558.8 (matches the frozen population); frozen source = the committed `denominators/kme_audit_2026-10-03.json` (all_default true, sha256 38493644...c1da). 4 roots, 63 project dirs, 294 sessions scanned, 13 selected active.
- Frontmatter: denominator KME-G, evidence_role smoke, terminal_evidence false, plane gex44.
- Ranked (all upper bounds, saving_status upper_bound, displacement unknown), unranked none:

| rank | candidate | upper bound (weighted) | share of KME-G weighted | vs 3 % on the bound |
|---|---|---|---|---|
| 1 | late_rollover (G = 100,000) | 8,773,728.0 | 0.1598 | >= 3 %: could clear materiality, needs the Owner's quota decision |
| 2 | unchanged_precondition_retries | 2,520.633333 | 0.000046 | < 3 % |
| 3 | identical_rereads | 0.0 (measured zero) | 0.0 | < 3 % |

- Rollover sensitivity (upper / rollovers): G 50,000 -> 11,643,331.2 / 41; 100,000 -> 8,773,728.0 / 16; 200,000 -> 3,024,745.1 / 5 (200,000 gives share about 0.0551, still >= 3 %; none of these decides the rank). 24 threads, 9 cross G = 100,000, floor median 173,427.5 (min 124,905, max 194,591). The figure is gross: a rollover's own re-read cost and any summary are not subtracted (caveat in the file).
- Retries: 3 loose, 0 strict (the loose upper is the ranked number); by tool Bash 2, ExitWorktree 1; 1 after an error; 0 Agent re-dispatches; 0 unobserved results. Signatures only (`git show`, `git log`, `ExitWorktree`).
- Rereads class split: 142 reads, 140 first, 2 unhashable, 0 identical_same_segment, 0 identical_after_compaction (matches the E smoke's zero identical rereads).
- Reading: on this GEX44 corpus only late_rollover could matter, as an optimistic ceiling. This says nothing about KME-L (laptop plane); the KME-L run and the quota decision are the Owner's (05-03 `[L]` item). Pillar L stays open.

## No-write proof

`find` over the three env trees (a5-env, a7-env, b001-env `.claude/projects`, `-printf '%p %s %T@\n'`) before and after the run, sorted: **736 files, `diff before after` printed nothing (DIFF_EMPTY)**. `~/.claude/projects` was scanned but left out of the snapshot (live sessions append there); the instrument opens transcripts read-only, proven by V-KMER-READ-ONLY. Nothing was written under `~/.claude/**` and no `claude` session was started.

## Deviations from Plan

### Judgement calls (no rule trigger)

1. **`rank_candidates` signature widened (kept backward-compatible).** To let the M7 mutant be a mutant of the seam the plan names, `rank_candidates(entries)` now receives all three candidates (an UNMEASURED one carries `upper_bound_weighted: None`) and ranks only entries with a number; a new `split_ranking` builds `(ranked, unranked)`, including the "input missing: no observer result" reason for a missing result. `rank_result` calls it. The 05-01 gates pass unchanged.
2. **`terminal_ok` made strict** (`frozen_source` None -> False); the plan's seam text names "frozen_source all_default". The old code treated None as default; only smoke runs have None, so no behaviour change for any real run.
3. **Reason text.** A drift now reads `population_not_reproduced: population_match=drifted ...` and an unlocated cutoff `cutoff_not_found: ...` is checked first (kme_pillars `_match` turns not_found into drifted, so the specific reason was unreachable before). The terminal reason names the frozen source ("NOT the committed frozen source ...") and the unranked candidates.
4. **`bound_label(upper, weighted)` seam added** (the plan's UPPER-BOUND-LABELS unit needed one); the stdout `vs_threshold=` token still prints without spaces.
5. **`tracer_fixture(root, project=...)`** gained a backward-compatible `project` keyword (SELECTED-ONLY needs the same fixture under a non-KME project).
6. **Commit trailer.** The attribution reminder in force for this run (`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`) was used, as in 05-01, not the Opus line in the execution prompt.
7. **Smoke file date.** The file is named for the UTC run date, `L-KME-G-2026-10-04.md` (the population is the 2026-10-03 freeze, reproduced at that instant).

No Rule 1-4 deviations. No auth gates, no package installs.

## Known Stubs

None.

## Threat Flags

None. Every emitted text passes `redact()`; commands appear only as `kp.cmd_signature` output (V-KMER-NO-SECRET, canary in a Bash command, a Read path, a tool_result, an assistant text and a hook context element); no new endpoint or write path.

## Notes for the next plans

- 05-03 can import `terminal_ok`, `split_ranking`, `bound_label`, `FRONT_KEYS`, `KMER_BODY_MARKER`, `RULE_DENOMINATORS` from `kme_replay`.
- The committed smoke file is plane gex44 and role smoke; the bundle must cite it as such and never as the KME-L ranking.

## Self-Check: PASSED

- FOUND: wiki/tools/kme_replay.py, tools/test_kme_replay.py, vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md
- FOUND commits: bb5fb71a, a08de708, 30611813 (`git rev-list --count d9ffd1ed..HEAD` = 3 before this SUMMARY commit)
- Gates re-run after the last task commit: KMER_PASS=36/36, DRILL killed=13/13, KMEP_PASS=89/89, ICP_SELFTEST=PASS
