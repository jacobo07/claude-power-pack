---
phase: 03-kme-corpus-measurements
plan: 03
subsystem: kme-measurement-instrument
tags: [pillar-G, pillar-H, IC-G, IC-H, kme, retest-interval, verification-share, ce-owner-read, gex44, smoke, mutation-drill]
requires: ["03-02"]
provides:
  - "wiki/tools/kme_pillars.py: GObserver (FALSIFY_RE, SEALED_RE, RETEST_RE, RELITIGATE_RE, NEGATED_RE, CITE_RE, DECISION_ID_RE, STOPWORDS, strip_negated, is_earlier), HObserver (VERIFY_CMD_RE, VERIFIER_AGENT_RE, verify_segment, cmd_signature, h_numerator_interval), ce_owner_verdicts, CE_LEDGER_REL; subcommands g and h; per-pillar caveats and estimate model"
  - "tools/test_kme_pillars.py: 18 new V-KMEP-G-* / V-KMEP-H-* gates (61 total), drill mutants M12-M16 (16 total)"
  - "vault/programs/incremental-cognition/measurements/G-KME-G-2026-10-03.md, H-KME-G-2026-10-03.md (smoke, plane gex44, terminal_evidence false) and H-GEX44-B001-2026-10-03.md (second workload)"
affects: ["03-05"]
tech-stack:
  added: []
  patterns: ["heuristic classifier reported as an interval with a sampled audit list", "text that only mentions a test (heredoc body, quoted string, install) blanked before command matching", "owner ledger read through argv git at HEAD, UNMEASURABLE when unreadable", "mutation seams as module-level names resolved at call time (CITE_RE, is_earlier, strip_negated, VERIFIER_AGENT_RE, h_numerator_interval)"]
key-files:
  created: [vault/programs/incremental-cognition/measurements/G-KME-G-2026-10-03.md, vault/programs/incremental-cognition/measurements/H-KME-G-2026-10-03.md, vault/programs/incremental-cognition/measurements/H-GEX44-B001-2026-10-03.md]
  modified: [wiki/tools/kme_pillars.py, tools/test_kme_pillars.py]
decisions:
  - "[Phase 3]: [03-03] G matches any candidate kind (re-test or relitigation marker) against any record kind (falsified or sealed); the plan's 'independently' wording left this open, and symmetric matching keeps 'reopen listing hiding' and 're-run D-03' countable"
  - "[Phase 3]: [03-03] sealed-decision samples show the id as the author wrote it (D-03), matching normalizes it (D-3)"
  - "[Phase 3]: [03-03] H blanks heredoc bodies and quoted strings and skips file-reading/moving programs and package installs before matching VERIFY_CMD_RE; first KME-G run matched python heredoc bodies and 'pip install pytest' as test runs"
  - "[Phase 3]: [03-03] H details carry the split weighted_tool_calls (CE P definition) / weighted_verifier_subagents so a reader sees which half drives the share"
  - "[Phase 3]: [03-03] cmd_signature shows the basename of an absolute program path and accepts '-m <module>' as the script token (python -m pytest)"
status: complete
commits: 3
plan_head_before: 849065ae7248fbaf7f9f92291aaf130fad083aad
actuals:
  tokens: 21850
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-03
requirements: [IC-G, IC-H]
requirements-completed: []
---

# Phase 3 Plan 03: pillars G and H (re-test interval, verification share + CE owner read) Summary

`python3 wiki/tools/kme_pillars.py g|h --denominator <NAME> --root <dir> ...` now measures re-tested falsified hypotheses and re-litigated sealed decisions as a strict..loose interval (G) and verification share by CE pillar P's definition plus verifier subagents, with the CE P and G owner terminals read with git at HEAD (H). **IC-G and IC-H are addressed, not satisfied**: terminals need the laptop KME-L runs (plan 03-05) and, for H, CE P and G terminals on this history, which do not exist. Ledger `state.G` and `state.H` are still `{}`; nothing was ticked and `requirements.mark-complete` was not called.

**Code commits:** `10eec6dc` (tracer: GObserver + `g` + V-KMEP-G-C6-K4-POSITIVE), `4d2a25f4` (G pole gates, HObserver, `ce_owner_verdicts`, `h`), `a85752b1` (drills M12-M16, H precision fixes, the three measurement files; carries the plan's subject).

## Observed results

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=61/61  threshold=61/61  skipped=0  inconclusive=0` (43 from 03-01/02, +1 tracer, +17 expansion). `V-KMEP-G-C6-K4-POSITIVE`, both `-REAL` gates and `V-KMEP-H-CE-OWNER-READ-REAL` PASS on GEX44.
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL`, sixteen `KILLED` lines, `PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 59/59 gates green`, `DRILL killed=16/16`. New: M12 CITE_RE never matches (V-KMEP-G-CITATION-IS-REUSE), M13 matching ignores time order (V-KMEP-G-ORDER), M14 negated phrases kept (V-KMEP-G-NEGATED-RETEST), M15 VERIFIER_AGENT_RE never matches (V-KMEP-H-VERIFIER-SUBAGENT), M16 verdict computed on upper_sensitivity (V-KMEP-H-SENSITIVITY-NOT-VERDICT).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `ICP_SELFTEST=PASS` (and `CEP_SELFTEST=PASS`), unchanged. Ledger `state.G`, `state.H` print `{} {}`.
- Acceptance check: `ce_owner_verdicts()` prints `40 {'P': None, 'G': None}`.

## RED outputs

- Task 1 RED (GObserver absent): `FAIL V-KMEP-G-C6-K4-POSITIVE rc=2 ... argument PILLAR: invalid choice: 'g' (choose from 'd', 'e', 'f')`, `KMEP_PASS=43/44`.
- Task 2 RED (G pole + H gates added, HObserver absent): nine FAILs, `KMEP_PASS=52/61`: seven H gates (`V-KMEP-H-BASH-VERIFY`, `-NON-VERIFY`, `-VERIFIER-SUBAGENT`, `-NO-DOUBLE-COUNT`, `-META-ABSENT`, `-SENSITIVITY-NOT-VERDICT`, `-POSITIVE`) with `TypeError: 'NoneType' object is not subscriptable` (subcommand `h` unknown, exit 2), `V-KMEP-H-CE-OWNER-READ-REAL` (`AttributeError: ... no attribute 'CE_LEDGER_REL'`), `V-KMEP-H-CE-OWNER-UNREADABLE` (no `ce_owner_verdicts`). **The eight G pole gates passed on their first run**: Task 1 had already built the whole GObserver, so only the H side could be RED. Their ability to go red is shown by the drill (M12, M13, M14 each kill one) and by the paired poles inside the gates (negated vs un-negated sentence, wrong vs right time order, cited vs re-tested). Recorded as a deviation.
- Precision fix RED: after the first KME-G smoke the H file listed junk signatures (`for a`, `with`, `do`, `DECISION`, `pip install`); `V-KMEP-H-NON-VERIFY` was extended with a heredoc body, inline `-c` code, an install, a venv `-m pytest` run and a real run after a heredoc, and failed (`calls=6 sigs=[... '(other)', 'pip install', 'python3', '/x/venv/bin/python' ...]`) before the fix.

## Smoke measurements (GEX44, read only)

Command shape (both pillars): `timeout 600 python3 wiki/tools/kme_pillars.py {g|h} --denominator KME-G --until 2026-10-03T16:13:37Z --expand --root a5/.../projects --root a7/... --root b001/... --root ~/.claude/projects`. Both exit 0, `population_match: "exact"` (13 active / 151 dead / 1,322 calls), `plane: "gex44"`, `evidence_role: "smoke"`, `terminal_evidence: false`, observability 1.0.

- **G-KME-G-2026-10-03.md** -> strict 0, loose 0 for re-tested falsifications and for re-litigated sealed decisions; share interval [0.0, 0.0], materiality `< 3 %`, second_workload_required false. Candidates 29 re-test markers, 0 re-litigation markers; falsification records 0, sealed records 1, reuse citations 0. The whole pre-freeze assistant text of the scanned trees (11,103 sentences, all roots) holds 3 sentences matching a falsification marker (read by hand: conditional or template wording such as "G8 is only falsified when ...", none a finding of the C6 kind; none became a record in the selected sessions) and 5 matching a sealed marker. **KME-G has too few falsification statements to say anything about G**; the zero is "nothing to re-test here", not a measured absence of re-testing. G's real case (listing hiding, C6 -> K4) lives in plan documents, not in these transcripts, so the positive control is only the fixture. The interval is [0, 0] because no candidate matched; on KME-L it will not be.
- **Hand precision check of the G smoke sample: 0 samples** (no strict match), so 0 of 0 judged true; precision is unmeasured. The interval stays the output; the 20-sample audit list is empty on this corpus.
- **H-KME-G-2026-10-03.md** -> share interval [7.30 %, 7.40 %], materiality `>= 3 %`, second_workload_required true. 64 verification tool calls, 48,762 result chars. **Split: CE P definition (test/gate tool calls + output carriage) = 109,477 .. 164,216 weighted, about 0.2 - 0.3 % of 54,899,559; verifier subagents = 3,896,853 weighted, about 7.1 %**: 7 verifier-subagent files (`kme-g1-ownership-arbiter` x6, `pp-code-reviewer` x1) carry the clearance. The full-call-cost sensitivity is 11.56 %, reported beside the verdict and not used. `consumed_owner_verdicts`: commit `4d2a25f4...`, P null, G null; the file states R2 is not satisfiable at that commit and that this is recorded as open, not as a pass.
- **Second workload (required by the H file):** `python3 wiki/tools/kme_pillars.py h --denominator OTHER --label GEX44-B001 --select all --host gex44 --expand --root /home/kobii/b001-env/home/.claude/projects` -> **H-GEX44-B001-2026-10-03.md**, share [8.73 %, 9.15 %], `>= 3 %`, `population_match: not_frozen`, smoke. 161 verification tool calls; CE P part 334,048 .. 501,071 weighted; verifier subagents 3,161,538 weighted (`gsd-verifier` x4, `gsd-plan-checker` x3, `gsd-code-reviewer` x1). G needed none (`< 3 %`): "second workload not required: < 3 %".
- **Reading of H on these two GEX44 corpora (not a terminal, not the frozen denominator):** both clear 3 % and in both the clearance is almost entirely verifier subagents, not test/gate tool calls. H's predicted direction (below materiality) is NOT supported on the GEX44 workloads, but KME-L decides; the KME-L run should keep the split visible.
- **No-write proof:** `find ... -type f -printf '%p %s %T@\n' | sort` over the a5, a7 and b001 project trees (736 files) before and after each smoke run: `diff /tmp/ic-p3-03-snap.before /tmp/ic-p3-03-snap.after` printed nothing, and the same for the B001 second-workload run (`/tmp/ic-p3-03-snap2.*`). `~/.claude/projects` is read by the scan but excluded from the snapshot (live sessions append there). The first smoke pair (before the H precision fix) was deleted unrun-for-commit and rerun; only the final files are committed.
- `grep -c 'sk-ant-'` on the three measurement files -> 0; assistant text and commands enter outputs only as two-word alphabetic subjects, decision ids, program/script tokens and agent type names.

## Deviations from Plan

**1. [Process] No RED run for the eight G pole gates** (see "RED outputs"): Task 1's GObserver already carried every path. Gate strength is shown by drills M12-M14 and the paired poles.

**2. [Rule 1 - bug] H matched text that only mentions a test.** The plan's literal rule (a Bash command that matches VERIFY_CMD_RE) counted python heredoc bodies, `-c` code, `pip install pytest` and `git diff -- test_x.py` as verification. Added `_code_only` (heredoc bodies and quoted strings blanked), `NON_RUN_PROGRAMS` (cat, grep, git, sed ...), `INSTALL_RE`, and wrapper/env-assignment skipping; `VERIFY_CMD_RE` itself is as in the plan. Cost, written into the file caveats: a real run hidden inside `bash -c "..."` is not seen. This moves H toward under-counting the tool-call half (0.2 - 0.3 % on KME-G), which does not change the verdict because the verifier-subagent half decides it.

**3. [Rule 2 - correctness] H details split** (`weighted_tool_calls`, `weighted_verifier_subagents`) so a reader can tell the CE P definition part from the subagent part; without it the 7 % looked like a test-running finding.

**4. [Rule 3 - blocking] Per-pillar caveats and estimate model.** The shared `CAVEATS` / `ESTIMATE_MODEL` constants describe hook rent and chars-per-token; G has no char estimate and H needs extra caveats. `CAVEATS_BY_PILLAR` / `ESTIMATE_MODELS` added; D, E, F output is unchanged (default constants).

**5. [Plan wording] Matching kinds.** The plan's "independently" left open which candidate kind matches which record kind; implemented symmetric (any candidate against any record), see decisions.

**6. [Attribution]** Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the attribution in force in this session's system reminder), not the Opus 5.5 line named in the dispatch; same choice as 03-01 and 03-02.

**7. [Process]** The agent-branch-namespace pre-commit check was not applied: this is a sequential run on the dispatched `mission/incremental-cognition-run` branch; HEAD was never on a protected branch.

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None. The tool reads transcripts and `meta.json` files and runs read-only argv git (`rev-parse`, `show`, 15 s timeout); it writes only markdown under the measurements directory.

## Debts / notes for the owner bundle

- KME-L laptop commands for plan 03-05: `python wiki/tools/kme_pillars.py g --denominator KME-L --expand --root <laptop projects roots>` and the same with `h` (default `--until` is the freeze instant; the population must match the frozen KME-L entry or the verdict is UNMEASURED). The G file's sample list must be read by a human in the named sessions before any number from it is cited.
- G blind spots, written into the files: English markers only; subjects are two words so unrelated findings can collide; a first-time "was falsified" statement is read as a citation; recall unknown; only assistant text of selected active sessions is read.
- H blind spots: runs hidden in `bash -c "..."`, hooks or wrappers are not seen; a subagent without `meta.json` is never a verifier (`meta_absent` counts them, 0 on both GEX44 workloads); `arbiter` and `review` agents count as verifiers per the plan's regex.
- R2 for H cannot be satisfied until CE P and G carry terminals on this history (Phase 6 already notes this for J/M).
- Untracked `docs/{arch,changelog,constitution,prd}/*kme_pillars*` files (hook-generated) were left alone, as were `vault/progress.md`, the workstream `config.json` and `milestone.lock`.

## Self-Check: PASSED

Verified after writing: wiki/tools/kme_pillars.py, tools/test_kme_pillars.py and the three measurement files present; commits 10eec6dc, 4d2a25f4, a85752b1 in the log; `population_match: "exact"`, `evidence_role: "smoke"`, `terminal_evidence: false` each count 1 in the G and H KME-G files; `consumed_owner_verdicts` present in the H file; `sk-ant-` count 0; ledger `state.G` and `state.H` are `{}`.
