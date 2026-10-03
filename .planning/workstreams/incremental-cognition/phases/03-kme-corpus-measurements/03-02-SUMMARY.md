---
phase: 03-kme-corpus-measurements
plan: 02
subsystem: kme-measurement-instrument
tags: [pillar-E, pillar-F, IC-E, IC-F, kme, read-reread, gsd-doc-residency, gex44, smoke, mutation-drill]
requires: ["03-01"]
provides:
  - "wiki/tools/kme_pillars.py: EObserver, classify_read, is_stub_text, FObserver, gsd_doc_kind, INIT_RE, pair_ratio; subcommands e and f (same flags as d); pillar-neutral measurement renderer"
  - "tools/test_kme_pillars.py: 19 new V-KMEP-E-* / V-KMEP-F-* gates (43 total), drill mutants M7-M11 (11 total)"
  - "vault/programs/incremental-cognition/measurements/E-KME-G-2026-10-03.md and F-KME-G-2026-10-03.md (smoke, plane gex44, terminal_evidence false)"
affects: ["03-05"]
tech-stack:
  added: []
  patterns: ["per-transcript-file observer state (a thread is one context)", "content hashed with sha256 and never emitted", "mutation seams as module-level functions resolved at call time (classify_read, is_stub_text, gsd_doc_kind, pair_ratio)"]
key-files:
  created: [vault/programs/incremental-cognition/measurements/E-KME-G-2026-10-03.md, vault/programs/incremental-cognition/measurements/F-KME-G-2026-10-03.md]
  modified: [wiki/tools/kme_pillars.py, tools/test_kme_pillars.py]
decisions:
  - "E adds an eighth class, unhashable, for Read results that carry an image block: text_of renders every image as the same '[image]', so hashing it would call two different images identical. It sits in neither bound"
  - "F's human-prompt turn counter advances on every user line that is not isMeta, not a tool_result and not a 'Base directory for this skill:' body; a non-meta line carrying <command-name> therefore starts a turn (it is the human's slash command), its isMeta body does not"
  - "a paired turn is a (transcript file, turn) holding at least one gsd-tools init result AND at least one GSD doc delivery; ratio = doc chars / init chars over paired turns, null when there is none (pair_ratio is a module-level seam so the null-never-0 rule is mutation-tested)"
  - "skill_body is recognised from the 'Base directory for this skill:' prefix whether or not isMeta is set; an errored Read / init result is ignored in both pillars"
status: complete
commits: 3
plan_head_before: c46f295e7ee764b9626983c9f8cdf06b6f3fea9e
actuals:
  tokens: 11460
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-03
requirements: [IC-E, IC-F]
requirements-completed: []
---

# Phase 3 Plan 02: pillars E and F (identical rereads, GSD doc residency) Summary

`python3 wiki/tools/kme_pillars.py e|f --denominator <NAME> --root <dir> ...` now measures identical-version file rereads (E) and GSD workflow-doc residency beside the `gsd-tools init.*` JSON (F) with the 03-01 core and measurement contract. **IC-E and IC-F are addressed, not satisfied**: their terminals need the laptop KME-L runs (plan 03-05); ledger `state.E` and `state.F` are still `{}`; nothing was ticked and `requirements.mark-complete` was not called.

**Code commits:** `7e6d46e1` (tracer: EObserver + `e` + V-KMEP-E-E2E), `35a58f87` (17 expansion gates + FObserver + `f`), `9d9795dd` (drills M7-M11, `pair_ratio` seam, the two KME-G smoke files; carries the plan's subject). `git show --stat 9d9795dd` lists kme_pillars.py, test_kme_pillars.py and the two files under measurements/ only.

## Observed results

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=43/43  threshold=43/43  skipped=0  inconclusive=0` (24 from 03-01, +1 tracer, +18 expansion). Both `-REAL` gates still PASS on GEX44 (byte-identical frozen pipeline, KME-G frozen population exact).
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL 41/41`, eleven `KILLED` lines, `PASS DRILL-CLEAN-AFTER-MUTANTS 41/41`, `DRILL killed=11/11`. New: M7 E ignores compaction boundaries (killed by V-KMEP-E-AFTER-COMPACTION), M8 stub test never matches (V-KMEP-E-STUB), M9 writes never mark a path (V-KMEP-E-INTERVENING-EDIT), M10 `gsd_doc_kind` always None (V-KMEP-F-READ-WORKFLOW + V-KMEP-F-POSITIVE), M11 paired ratio reads 0 with no init (V-KMEP-F-INIT-ABSENT).
- Acceptance check: `gsd_doc_kind` prints `workflow skill None` for the three plan paths.

## RED outputs

- Task 1 RED (EObserver absent): `FAIL V-KMEP-E-E2E rc=2 ... argument PILLAR: invalid choice: 'e' (choose from 'd')`, `KMEP_PASS=24/25`.
- Task 2 RED: nine F gates FAILed (`V-KMEP-F-READ-WORKFLOW` AttributeError no `gsd_doc_kind`; the other eight `TypeError: 'NoneType' object is not subscriptable` because `f` was an unknown subcommand, exit 2), `KMEP_PASS=34/43`. **The nine E expansion gates passed on their first run**: Task 1 had already built every E class, so only the F side could be RED. Their ability to go red is shown by the drill (M7, M8, M9 kill three of them) and by the pole pairs inside the gates (INTERVENING-EDIT runs an edit of the same path and an edit of another path; E-POSITIVE runs identical rereads and a file that changes every read; E-ABSENT runs a session with no Read). Recorded as a deviation.

## Smoke measurements (GEX44, read only)

Command shape (both pillars): `timeout 600 python3 wiki/tools/kme_pillars.py {e|f} --denominator KME-G --until 2026-10-03T16:13:37Z --expand --root a5/.../projects --root a7/... --root b001/... --root ~/.claude/projects`. Both exit 0, `population_match: "exact"` (13 active / 151 dead / 1,322 calls), `plane: "gex44"`, `evidence_role: "smoke"`, `terminal_evidence: false`, observability 1.0.

- **E-KME-G-2026-10-03.md** -> share [0.0, 0.0], materiality `< 3 %`, second_workload_required false. 142 Read results: **first 140, unhashable 2 (images), stub 0, identical_same_segment 0, identical_after_compaction 0, rewritten_identical 0, changed_after_write 0, changed_outside_tools 0**. No identical reread exists in the KME-G corpus (the two Reads of `autonomous.md` are in different transcript files, i.e. different contexts). The zero stubs agrees with the planning measurement. E's predicted RESEARCH_INSUFFICIENT_EVIDENCE direction is consistent; the KME-L run decides.
- **F-KME-G-2026-10-03.md** -> share [0.69 %, 1.03 %], materiality `< 3 %`, second_workload_required false. 24 GSD doc deliveries, 175,494 chars: workflow 2 (83,116 chars), reference 11 (65,631), skill_body 10 (24,332), invoked_skill 1 (2,415). `gsd-tools init` calls: 2, 1,261 chars total (mean 630.5), `init_json_present: true`; paired turns 1, doc_chars 7,933, init_chars 1,261, **ratio 6.29**. The compact init state exists and is about 6x smaller than the docs delivered beside it in the one paired turn; F's predicted MERGED_INTO_EXISTING_OWNER direction is consistent but rests on one paired turn, so it is a sample, not a finding.
- **Second workload:** not required for either pillar (E: `< 3 %`; F: `< 3 %`). Per the plan no `--denominator OTHER --label GEX44-B001` run was made and no extra file committed.
- **No-write proof:** `find ... -type f -printf '%p %s %T@\n' | sort` over the a5, a7 and b001 project trees (736 files) before and after the two runs: `diff /tmp/ic-p3-02-snap.before /tmp/ic-p3-02-snap.after` printed nothing. `~/.claude/projects` is read by the scan but excluded from the snapshot (live sessions append there).
- `grep -c 'UNIQUE-CONTENT-MARKER\|sk-ant-'` on both files -> 0; Read results and GSD doc text enter outputs only as sha256 (never emitted), char counts, E file paths and F basenames.

## Deviations from Plan

**1. [Process] No RED run for the nine E expansion gates** (see "RED outputs"): the tracer's EObserver already carried every class. Gate strength is shown by drill M7/M8/M9 and the paired poles.

**2. [Rule 2 - correctness] Eighth E class `unhashable`.** A Read result with an image block extracts to `[image]` for every image; hashing it would classify two different images as an identical reread. Such results are kept in their own class and in neither bound. Two such results exist in KME-G (14 chars).

**3. [Rule 3 - blocking] Pillar-neutral renderer.** `render_measurement` printed D-only lines (`attachments`, `by_hook`). It now branches on pillar (D output unchanged); E and F use `name` / `definition` and a `_pillar_details` helper. `numerator` also carries `weighted_lo` / `weighted_hi` as the plan's interface states, beside the `weighted_interval` list the shared `main()` reads.

**4. [Process] Commits.** Three commits (one per task) instead of one; the Task-3 commit carries the plan's subject.

**5. [Attribution]** Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the attribution in force in this session's system reminder), not the Opus 5.5 line named in the dispatch; same choice as 03-01.

**6. [Process]** The agent-branch-namespace pre-commit check was not applied: this is a sequential run on the dispatched `mission/incremental-cognition-run` branch; HEAD was never on a protected branch.

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None. The tool reads transcripts and writes only markdown under the measurements directory.

## Debts / notes for the owner bundle

- KME-L laptop commands for plan 03-05: `python wiki/tools/kme_pillars.py e --denominator KME-L --expand --root <laptop projects roots>` and the same with `f` (default `--until` is the freeze instant; the population must match the frozen KME-L entry or the verdict is UNMEASURED). E and F stay `smoke`/unticked until those run.
- Known blind spots, written into the measurement files: E does not see rereads through Bash/Grep/cat; a file changed and changed back with no tool write counts as identical; paths are compared as written (two spellings of one path read as two files); F's turn pairing is per human prompt, so one long autonomous run is a single turn.
- Untracked `docs/{arch,changelog,constitution,prd}/*kme_pillars*` files (hook-generated) were left alone, as were `vault/progress.md`, the workstream `config.json` and `milestone.lock`.

## Self-Check: PASSED

Verified after writing: wiki/tools/kme_pillars.py, tools/test_kme_pillars.py, E-KME-G-2026-10-03.md and F-KME-G-2026-10-03.md present; commits 7e6d46e1, 35a58f87, 9d9795dd in the log; `population_match: "exact"`, `evidence_role: "smoke"`, `terminal_evidence: false` each count 1 in both files; marker / `sk-ant-` count 0; ledger `state.E` and `state.F` are `{}`.
