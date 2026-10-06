---
phase: 02-kme-l-challenger
plan: 03
subsystem: kme-analytics
tags: [challenger, certify, shadow, deopt, invalidation-keys, source-watermark, in-04, mutation-drill, kme_pillars]
requires:
  - phase: 02-kme-l-challenger
    provides: plan 02-01 access plans and the index tier (guards index_open, kind, population), path log
  - phase: 01-usage-index-v5-substrate
    provides: tools/usage_index.py v5 population(detail=True), meta pattern_set / attr_version, files rows (size, mtime_ns, offset, first_ts)
provides:
  - "kme_pillars.py certify: writes a kmep-cert/1 certificate only on EXACT index population plus per-session shadow agreement with a champion scan of the same scope (exit 0 / 1 / 3 / 2)"
  - "selection_parser_digest, metric_digests, METRIC_DEFINITIONS, SELECTION_SOURCES / SELECTION_NAMES: invalidation keys read from source text by ast"
  - "index tier guard chain: index_open, kind, certificate, pattern, attribution, parser, metric, population, watermark, no_first_ts, then the post-scan shadow guard; every refusal is typed (guard + reason) and logged"
  - "closure-exact stale handling: only the sessions whose sources changed (or are new / vanished) join the read set; IN-04 sessions are read raw under guard no_first_ts"
  - "path record schema 2: keys, metric_changed, read_set.stale, read_set.no_first_ts"
  - "tools/test_kme_challenger.py: 21 hermetic gates (KMEC_PASS=21/21) and --drill with 15 mutants (killed=15/15)"
affects: [02-04, 02-05, 02-06]
plan_head_before: a3aed4054d0751ba38274f51c01f079670b8aafb
actuals:
  tokens: 18902     # chars/4 over the +/- lines of wiki/tools and tools (git diff a3aed405..HEAD, 75609 chars)
  tasks: 3
  commits: 3        # measured: git rev-list --count a3aed405..HEAD (the docs commit of this summary comes after)
tech-stack:
  added: []
  patterns:
    - "certificate binds code and question, never the index file identity: a refreshed index is re-queried and still covered while the digests hold"
    - "key digests are ast segments of module-level names, never imports; a vanished name reads as a change"
    - "every guard is a small module-level function so a mutant can replace exactly one mechanism"
    - "the list of names a metric key covers is checked against the names its observer actually reads (V-KMEC-METRIC-COVERAGE), not trusted"
key-files:
  created: []
  modified:
    - wiki/tools/kme_pillars.py
    - tools/test_kme_challenger.py
key-decisions:
  - "A new KME session that appears after certification, with lines before the frozen instant, is NOT served from the index: the frozen population no longer reproduces, so the shadow guard refuses (auto deopts to scoped, challenger exits 3). Only sessions that do not change the frozen answer (non-KME, lines after the freeze instant, vanished files) are served by closure."
  - "The index-root identity gap noted by 02-01 is closed as guard watermark / root_not_indexed, in the run AND in certify (a certificate is never issued for a root the index never saw)."
  - "certify requires the index guards (index_open, kind, population EXACT) and root identity, then the champion's own scoped scan; a disagreement or a non-exact champion population is exit 1, an index guard is exit 3, nothing is written in either case."
  - "The certificate's pattern_set is compared with the live champion pattern set (guard pattern); the index's own meta is left to the population guard so its own typed reason is the one quoted."
  - "Stale session ids are written as <project>/<session>; the log lists them in read_set.stale, IN-04 sessions in read_set.no_first_ts."
requirements-completed: [AO-07, AO-09, AOP-P]
duration: ~1h (start not timestamped; approximate)
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 03: Certify, keys and the guard chain Summary

**The challenger now serves an answer from the index only under a certificate (shadow-agreed selection plus code and definition digests), re-reads exactly the sessions whose sources changed, reads sessions without a first timestamp raw instead of dropping them, re-checks selection and population after the scan, and names the guard and reason of every deopt; 21 gates and a 15-mutant drill prove each guard can fail.**

## What was built

**Task 1 (tracer, commit 016bf57d).** `certify` (own parser: common question flags, `--index-db`, `--cross-project`, required `--cert`, no `--plan`): index guards, root identity, then `_measure(ctx, [], until)` with no select (the champion scan of the same scope), `compare_population` exact, and the selected `(project, session)` pairs of both sides compared (dead sessions included, so `sessions_dead` identity is checked, not only its count). Equal: the certificate is written through `redact`, atomically (temp file in the same directory + `os.replace`), refused inside any `--root`. Unequal: exit 1, counts and up to five ids per side on stderr, nothing written. Printed line `KMEP-CERT verdict=<CERTIFIED|NOT_CERTIFIED|UNMEASURED> selected=<n> uncovered=<n> cert=<path|none>`. The challenger / auto index tier gained the `certificate` guards (question equality, pattern, attribution, parser, metric) and a `--cert` flag (default `<index-db>.kmep-cert.json`, read only).

**Task 2 (commit e71fd60e, gates).** `_watermark` (stale = size / mtime_ns differ, row offset short of its size, an unindexed file the certificate's `uncovered` map does not vouch for by exact (size, mtime_ns), an indexed file gone from disk), the IN-04 closure `_no_first_ts_sessions`, read set = index-selected | stale | no_first_ts, and the post-scan `_shadow_check` (in-process population exact against the frozen fields; every unchanged index-selected session selected by the champion classifier and nothing selected that the index did not select). In the `--until auto` branch the shadow guard runs right after the freeze-instant scan, before any locator probe. **These mechanics were written in the same pass as Task 1 and are in commit 016bf57d**; commit e71fd60e holds their gates (see Deviation 1).

**Task 3 (commit 1ca72e86).** `MUTANTS` M1-M15 and `run_drill()`.

## Final key definitions (for the record)

`SELECTION_SOURCES` = bytes of `tools/usage_index.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_report.py` (keyed by basename); `SELECTION_NAMES` (segments of `kme_pillars.py`) = `population`, `make_keep`, `parse_instant`, `_first_ts`, `_UNSET`.

`METRIC_DEFINITIONS` (names are module-level constants, functions or classes; a name that disappears reads as a change):
- `population`: `POP_FIELDS`, `WEIGHTS`, `weighted`.
- `D`: `DObserver`, `THRESHOLD`, `materiality`, `ESTIMATE_MODEL`, `CAVEATS`, `CPT_HI`, `CPT_LO`, `POP_FIELDS`, `WEIGHTS`, `burden`, `burden_interval`, `context_chars`, `counts_for_d`, `resident_calls`.
- `E`: `EObserver`, `THRESHOLD`, `materiality`, `ESTIMATE_MODEL`, `CAVEATS`, `CPT_HI`, `CPT_LO`, `WEIGHTS`, `E_CLASSES`, `STUB_PREFIX`, `WRITE_TOOLS`, `_blocks`, `burden`, `burden_interval`, `classify_read`, `is_stub_text`, `resident_calls`.
- `F`: `FObserver`, the same result side as E, `INIT_RE`, `SKILL_BODY_PREFIX`, `_GSD_DIRS`, `_GSD_ROOTS`, `_basename`, `_blocks`, `_user_text`, `gsd_doc_kind`, `pair_ratio`, `burden`, `burden_interval`, `resident_calls`.
- `G`: `GObserver`, `THRESHOLD`, `materiality`, `ESTIMATE_MODEL_G`, `G_CAVEATS`, `WEIGHTS`, the regexes `CITE_RE`, `DECISION_ID_RE`, `FALSIFY_RE`, `NEGATED_RE`, `RELITIGATE_RE`, `RETEST_RE`, `SEALED_RE`, `SENT_SPLIT_RE`, `MARKER_WORDS`, `STOPWORDS`, `SKILL_BODY_PREFIX`, `_EPOCH`, and the helpers it calls.
- `H`: `HObserver`, `H_DEFINITION`, `H_SENSITIVITY_LABEL`, `H_CAVEATS`, `CAVEATS`, `ESTIMATE_MODEL`, `CE_LEDGER_REL`, `VERIFY_CMD_RE`, `VERIFIER_AGENT_RE`, the signature / command-segment regexes and helpers, `ce_owner_verdicts`, `h_numerator_interval`, `WEIGHTS`, `POP_FIELDS`, and the shared burden helpers.
- `I`: `IObserver`, `ESTIMATE_MODEL_I`, `I_CAVEATS`, `CAVEATS`, `THRESHOLD`, `materiality`, `WEIGHTS`, `POP_FIELDS`, `call_weighted`, `distribution`, `is_subagent_path`, `read_subagent_meta`, `subagent_type`.
- `L`: from `kme_replay.py` the three observer classes, `rank_result` and every ranking / bound function and constant it reads (`ROLLOVER_GROWTH`, `ROLLOVER_SENSITIVITY`, `READ_ONLY_TOOLS`, `AGENT_TOOLS`, `CANDIDATES`, `DEFINITIONS`, `NAMES`, `BOUND_READINGS`, `CAVEATS`, `ROUND`, `RULE_DENOMINATORS`, ...), plus from `kme_pillars.py` what they read through `kp.`: `EObserver` (base of `RereadObserver`), `WEIGHTS`, `CPT_*`, `THRESHOLD`, `burden*`, `resident_calls`, `cmd_signature` and its helpers, `WRITE_TOOLS`, `E_CLASSES`, `STUB_PREFIX`, `classify_read`, `is_stub_text`, `compare_population`, `referenced_coverage`, `distribution`, `is_subagent_path`.

The exact lists are `kme_pillars.METRIC_DEFINITIONS`; V-KMEC-METRIC-COVERAGE regenerates the dependency closure of each observer from the source and fails if a list lacks a name (control: dropping `VERIFY_CMD_RE` from H is reported).

## Verification (observed)

```
python3 -I tools/test_kme_challenger.py
PASS V-KMEC-SCAN-PROJECT-DEFAULT ... PASS V-KMEC-REPLAY-PLAN  (the 8 gates of 02-01, now certifying their fixture first)
PASS V-KMEC-CERTIFY-SHADOW certify rc=0 selected=1 shadow={'agree': True, 'champion_selected': 1, 'index_selected': 1}; swapped selection rc=1 names k1+n1=True written=False; drifted frozen rc=3 written=False; cert inside root rc=2
PASS V-KMEC-KEYS-FOUR cert keys parser=98e1d20be43d metric keys=['D','E','F','G','H','I','L','population'] attr=1 uncovered=['p1.jsonl']; index run keys==cert=True metric_changed=[] stale=[]; after touching the preserved file stale=['-home-x-core-fixture/_preserved']
PASS V-KMEC-STALE-PARSER digest 98e1d20be43d -> 44ff46eeab8c; control taken=index; auto deopt=parser (...) taken=scoped output equals scoped=True; forced challenger rc=3 files=0
PASS V-KMEC-STALE-METRIC control metric_changed=[]; H_DEFINITION changed -> ['H'] taken=index; WEIGHTS changed -> ['D','E','F','G','H','I','L'] deopt=metric taken=scoped; forced challenger rc=3
PASS V-KMEC-ATTR-VERSION control taken=index; ATTR_VERSION+1 -> deopt attribution: attribution version differs: index 1, substrate 2, certificate 1; forced rc=3
PASS V-KMEC-PATTERN-DRIFT altered meta pattern_set -> deopt population: population: UNMEASURED: pattern set differs: ...
PASS V-KMEC-CERT-GUARDS missing: certificate cert_missing; project_filter: certificate question.project_filter; until: certificate question.until
PASS V-KMEC-METRIC-COVERAGE uncovered dependencies=none; listed names missing from source=none; selection names missing=none; control (VERIFY_CMD_RE dropped from H) -> {'wiki/tools/kme_pillars.py': ['VERIFY_CMD_RE']}
PASS V-KMEC-STALE-SOURCE control: taken=index stale=[] opened=['agent-a1.jsonl','k1.jsonl']; after appending to n1: stale=['-home-x-core-fixture/n1'] opened=[agent-a1, k1, n1] (n2 untouched, never opened) output equals champion on the modified tree=True
PASS V-KMEC-STALE-NEW-FILE (a) new non-KME file: stale=['.../n3'] equal to champion=True; (b) file vanished: stale=['.../n1','.../n3'] equal=True; (c) new KME session: auto deopt=shadow taken=scoped forced rc=3
PASS V-KMEC-IN04-NO-FIRST-TS IN-04 session z1: no_first_ts=['-home-x-core-fixture/z1'] guard='1 session(s) without a first timestamp read raw (review IN-04)...' opened z1=True; without it: [] '0 session(s) ...'
PASS V-KMEC-ROOT-NOT-INDEXED certify over a root the index never saw: rc=3 written=False; run with a forged certificate: deopt watermark: root_not_indexed ...; forced rc=3; control taken=index
PASS V-KMEC-DEOPT-LOGGED guards 10/10 [index_open/missing:ok, index_open/schema4:ok, population/DRIFTED:ok, population/UNMEASURED:ok, certificate:ok, parser:ok, attribution:ok, metric:ok, watermark/root_not_indexed:ok, shadow:ok] control (all green): taken=index deopt=None
KMEC_PASS=21/21  threshold=21/21  skipped=0  inconclusive=0

python3 -I tools/test_kme_challenger.py --drill
PASS DRILL-CONTROL unmutated run: 21/21 gates green
KILLED M1..M15 (each by the gate named in the plan: STALE-SOURCE x2, STALE-PARSER, ATTR-VERSION, STALE-METRIC x2, TRACER-D-E2E x2, DEOPT-LOGGED x2, KS4-FORCED, CROSS-PROJECT-EXPLICIT, IN04-NO-FIRST-TS, CERTIFY-SHADOW, INDEX-READ-ONLY)
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 21/21 gates green
DRILL killed=15/15

python3 -I tools/test_kme_pillars.py            -> KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
python3 -I tools/test_kme_pillars.py --drill    -> DRILL-CLEAN-AFTER-MUTANTS 84/84 green, DRILL killed=20/20
python3 -I tools/test_usage_index_v5.py         -> USAGE_INDEX_V5_PASS=74/74  threshold=74/74
python3 -I tools/test_kme_replay.py             -> KMER_PASS=45/45  threshold=45/45  skipped=1  inconclusive=0 (the skip predates this plan)
python3 -I tools/test_kme_measure_tools.py      -> KMET_PASS=14/14  threshold=14/14  skipped=0  inconclusive=0
git log --format=%H -1 -- tools/usage_index.py  -> 6674ccc0ea9a9e7506bf281f6c200c13e9a61f31 (git diff 6674ccc0 HEAD -- tools/usage_index.py is empty)
python3 -I wiki/tools/kme_pillars.py certify --denominator KME-L --root /tmp --index-db /nonexistent.sqlite --cert /var/tmp/kmec-never.json --project-filter x
  -> exit 3, "KMEP-CERT verdict=UNMEASURED selected=0 uncovered=0 cert=none", /var/tmp/kmec-never.json not created
```

Tracer gate: Task 1 `<verify>` was re-run end-to-end before expanding to Task 2 (KMEC_PASS=16/16, KMER 45/45), so expansion proceeded. The full drill kills each mutant for the intended reason (spot-checked evidence for M4, M8-M14: e.g. M4 shows `deopt None ... forced rc=0`, M12 shows `no_first_ts=[] opened z1=False`).

## Deviations from Plan

**1. [Process] Task 2 mechanics were implemented with Task 1 and are in the Task 1 commit.** `_watermark`, `_no_first_ts_sessions` and `_shadow_check` are wired into `_index_tier` / `_resolve_scan`, which Task 1 had to touch anyway (the index tier cannot exist half-built), so one pass wrote them; commit 016bf57d says so. Task 2's `tdd="true"` RED was therefore not committed separately. The substitute evidence that each Task 2 gate can go red is the drill: M1 / M2 (watermark), M12 (IN-04), M13 (shadow) each turn the Task 2 gates red. Files: `wiki/tools/kme_pillars.py`, `tools/test_kme_challenger.py`.

**2. [Rule 2 - correctness] SELECTION_NAMES carries `parse_instant`, `_first_ts` and `_UNSET` in addition to `population` and `make_keep`.** `make_keep` decides the effective timestamp of every line through those three, so a change to them changes which sessions exist at an instant; leaving them out would let that change keep a certificate valid. V-KMEC-METRIC-COVERAGE checks that everything `population` and `make_keep` read is in the selection names or the population key.

**3. [Rule 2 - correctness] Metric lists name functions and classes as well as constants.** The plan's starting lists were constants only; a change to `burden`, `classify_read`, an observer class or a helper would not have moved any digest. Lists were derived from the source closure of each observer (not hand-curated) and are checked by V-KMEC-METRIC-COVERAGE (an extra gate, 21 gates instead of the 20 the plan lists).

**4. [Rule 2 - correctness] Root identity closed (orchestrator note from 02-01).** `_scope_state` raises guard `watermark` / `root_not_indexed` when no in-scope disk path is present in the index (or no in-scope file exists), in the run and in certify. Gate V-KMEC-ROOT-NOT-INDEXED (certify refuses; a forged certificate deopts).

**5. [Design] `certify` itself also checks root identity and records `uncovered` from the same walk the watermark uses.** The plan listed only the run-side check; issuing a certificate that the run could never use would have been a silent trap.

**6. [Design] Pattern guard compares the certificate with the live champion set only.** The plan also listed the index meta; the index's own `population` refusal ("pattern set differs ...") is the typed reason the gate must quote (V-KMEC-PATTERN-DRIFT), and a meta that differs from the live set is refused there before it could differ from the certificate in a way that matters.

**7. [Design] Path record schema 2.** `keys` (live digests) and `metric_changed` are always present (null outside the index tier), and `read_set` gained `stale` and `no_first_ts` (null on raw tiers). `PATH_SCHEMA` bumped 1 to 2; the 02-01 shape gate (`PATH_KEYS`) was updated.

**8. [Design] A new KME session appearing after certification is refused, not served.** With `until` at the freeze instant, a new session whose lines fall before it changes the frozen population, so the shadow guard refuses it (V-KMEC-STALE-NEW-FILE c). The plan's text "selected if the champion classifier selects it, output equals the champion's" holds for sessions that leave the frozen answer unchanged (a new non-KME file, a vanished file, lines after the freeze instant); a population-changing session is honestly a deopt, with the champion's output reproduced by the scoped tier.

**9. [Fixture] V-KMEC-STALE-SOURCE appends an assistant text line that mentions KMEIP but carries no usage.** It changes the file's bytes and size (stale) and the classifier's input, without selecting `n1` or adding a call, so the frozen population stays exact. It is the most KME-bearing line that keeps the answer unchanged.

**10. Pre-commit assertion.** Same as 02-01 / 02-02: the worktree branch is `mission/autonomous-optimization-gen2`, outside the `agent-*` namespace; the orchestrator pinned this branch and the root-pin guard passed (exit 0) before every commit. The namespace check was not applied.

**11. Requirement status left as is.** Per the unattended instructions `requirements mark-complete` was not run; AO-07, AO-09 and AOP-P stay as they are (the phase is not done until 02-06). `requirements-completed` lists the IDs this plan advanced.

## Notes for the following plans

- **Certificate question must match the run's question exactly**: denominator, select, host, `--project-filter` text, `--cross-project`, `--expand`, the realpaths of the `--root` list and the `--until` instant (`--until auto` is the freeze instant). Run `certify` with the same flags as the measuring run; a mismatch deopts under guard `certificate` with `question.<field>` in the reason. `certify` itself costs one champion scoped scan.
- **02-04 real corpus**: `certify` needs the index population EXACT against the frozen KME-L under the scope filter (02-01's note about `--project-filter` and the other projects still applies) and the champion scan of that scope to select the same 102 sessions. The `_preserved` / `_empty_shells` files of the real corpus that fall in scope (02-01's note counts 16 pseudo-sessions; the index census over the whole corpus counts 50 skipped files) will appear in the certificate's `uncovered` map (count printed as `uncovered=<n>`); on the real index every `files` row has `offset == size` (checked), so no spurious staleness is expected. Seven indexed files have `first_ts` NULL: they surface under guard `no_first_ts` (and are read raw) whenever their session is in scope.
- **Path record fields for the evidence tables**: `plan_taken`, `deopt` (`guard`, `reason`), `read_set.{sessions,files,bytes,stale,no_first_ts}`, `keys`, `metric_changed`. Stale ids are `<project>/<session>`. For plan 02-05's delta (lines after the freeze instant on five transcripts) the five sessions are expected in `read_set.stale`, and the shadow guard must pass because the frozen population does not move.
- **Both tiers still read every file of an admitted session**: a stale session is read whole, not just its changed file (the champion's session unit).
- **kme_replay rank uses the same chain**: its `--plan challenger` runs need `--cert` (or a certificate at the default path) for the same question; L's metric key is digested from `kme_replay.py` plus the `kme_pillars.py` names it reads.
- **The watermark's project / session pair comes from the directory walk** (basename of the scanned dir, first relative path component), the pair `select` is asked about; the index's own project is the canonical store name. They are equal on the fixture and on a corpus without symlinked project dirs; a symlinked project dir would make its sessions look vanished-and-new (stale, read raw, still correct, never a wrong answer).

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-11 (stale certificate served as fresh): V-KMEC-STALE-*, V-KMEC-ATTR-VERSION, V-KMEC-PATTERN-DRIFT, V-KMEC-CERT-GUARDS plus drill M1-M6. T-02-12 (index selection that disagrees with the champion): V-KMEC-CERTIFY-SHADOW, the shadow row of V-KMEC-DEOPT-LOGGED, drill M13 / M14. T-02-13: the watermark lists only `_scope_dirs` of the run (the same rule `scan()` now calls); V-KMEC-PLAN-ORDER and V-KMEC-STALE-SOURCE (out-of-scope `c1` never opened) stay green. T-02-14: the certificate holds digests, counts, in-scope paths with (size, mtime_ns) and no text, passes `redact`, is refused inside a `--root` (V-KMEC-CERTIFY-SHADOW), and fixture certificates live in the test's scratch directory. T-02-15: V-KMEC-IN04-NO-FIRST-TS and drill M12.

## Self-Check: PASSED

- FOUND: wiki/tools/kme_pillars.py, tools/test_kme_challenger.py
- FOUND commits: 016bf57d, e71fd60e, 1ca72e86 (`git log --oneline`)
- `git show --stat` of each task commit lists only that task's files; `tools/usage_index.py` unchanged since 6674ccc0.
