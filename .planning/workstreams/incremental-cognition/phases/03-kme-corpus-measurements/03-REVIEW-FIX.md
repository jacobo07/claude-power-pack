---
phase: 03-kme-corpus-measurements
fixed_at: 2026-10-03T22:40:00Z
review_path: .planning/workstreams/incremental-cognition/phases/03-kme-corpus-measurements/03-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 3: Code Review Fix Report

**Source review:** 03-REVIEW.md (WR-01..WR-07 + IN-01 in scope; IN-02 out of scope)
**Iteration:** 1
**Run plane:** edits and commits in the existing isolated worktree `.claude/worktrees/ic-run` (branch
`mission/incremental-cognition-run`); no nested worktree was created. Gates were run in this same tree.

## Outcomes

### WR-01: --out-dir inside a scanned root -- FIXED

**Commit:** d241bb5e
**Files:** `wiki/tools/kme_pillars.py` (`_prepare`), `tools/test_kme_pillars.py`, `vault/.../evidence/phase3.md` (sha rows)
**Fix:** a measuring run resolves `os.path.realpath` of the out-dir (default included) and of every `--root`; equal or
contained (symlinks followed) -> `_fail`, exit 2, nothing written. `population` writes nothing and is not checked.
**Gate:** `V-KMEP-OUT-DIR-INSIDE-ROOT` (inside, via symlink, `--expand` root, out-dir == project dir: all rc 2, the root
tree byte-identical via `tree_state`; positive control out-dir outside the root writes exactly one file).
**RED (fix reverted):** `FAIL V-KMEP-OUT-DIR-INSIDE-ROOT inside=0 symlink=0 expand=0 equal=0 tree_unchanged=False control_rc=0 control_files=1` -> `KMEP_PASS=83/84`
**GREEN:** `PASS V-KMEP-OUT-DIR-INSIDE-ROOT inside=2 symlink=2 expand=2 equal=2 tree_unchanged=True control_rc=0 control_files=1` -> `KMEP_PASS=84/84  threshold=84/84`

### WR-02: cmd_signature wrote URL / path arguments verbatim -- FIXED

**Commit:** 8f835ed6
**Files:** `wiki/tools/kme_pillars.py` (`cmd_signature` plus helpers `_opaque_run`, `_sig_redact`), `tools/test_kme_pillars.py`, phase3.md sha rows
**Fix:** program token must be a bare name or plain path without a long opaque run, else `(other)`. Second token: flags dropped;
a URL-ish token (`://`, leading `//`, `?`, `@`, `#`, `=`, `%xx`) becomes the placeholder `<url>`; a token with a 20+
letter/digit run that mixes both (or any 32+ run) becomes `<opaque>`; otherwise kept only as a short lowercase word or a plain path
(`python3 tools/test_x.py` and the gsd-tools path keep their old signatures, so every committed signature is unchanged and
no measurement file needed regeneration). The final signature goes through the Secret Firewall `redact()`; if that is unavailable the
signature is `(other)` (fail closed). A `::` pytest id is no longer kept (dropped to the program name).
**Gate:** `V-KMEP-SIGNATURE-NO-URL-TOKEN` (four secret-bearing curl shapes written end to end through the real CLI; the token and the host
must be absent from file, stdout, stderr; positive control `python3 tools/test_x.py` still recorded).
**RED (fix reverted):** `FAIL V-KMEP-SIGNATURE-NO-URL-TOKEN rc=0 leaked=True ... sigs=['curl', 'curl api.example.com/verify/ghp1234...', 'curl https://api.example.com/verify/ghp1234...', ...]` -> `KMEP_PASS=84/85`
**GREEN:** `PASS V-KMEP-SIGNATURE-NO-URL-TOKEN rc=0 leaked=False unit={'url': 'curl <url>', 'query': 'curl <url>', 'userinfo': 'curl <url>', 'bare-path': 'curl <opaque>'}` -> `KMEP_PASS=85/85  threshold=85/85`

### WR-03: R3 fails open on absent / unparsable kme_pillars front matter -- FIXED

**Commit:** 42800120
**Files:** `tools/test_incremental_cognition_program.py` (`front_matter_fields`, new `is_kmep_file`, `check_measurement_scope`, selftest), phase3.md sha row
**Fix:** `front_matter_fields` strips a leading U+FEFF. A measurement is a kme_pillars file when its front matter `instrument` is
`wiki/tools/kme_pillars.py` (the instrument already writes this line in every file, so no new marker or regeneration was needed), or the
`<!-- kmep-json -->` block marker / `"instrument": "wiki/tools/kme_pillars.py"` appears anywhere in the text, or either role field is present. Such a file
with `evidence_role` not a string or `terminal_evidence` not a bool (absent, damaged, hand-edited) is refused with
`R3 <P>: <ref> is a kme_pillars measurement without readable evidence_role / terminal_evidence front matter`. Only a file with no mark at all is
still left to the CE clauses.
**Gates (selftest):** `V-ICP-R3-BOM-READ`, `V-ICP-R3-KMEP-NO-ROLE-REFUSED`, `V-ICP-R3-KMEP-MARKER-ONLY-REFUSED`, `V-ICP-R3-KMEP-UNPARSABLE-REFUSED`;
the pre-existing `V-ICP-R3-NON-KMEP` / `-QUOTED-NOT-FIELD` (another instrument's file, body words are not fields) stay green.
**RED (guard reverted):** `FAIL V-ICP-R3-BOM-READ`, `FAIL V-ICP-R3-KMEP-NO-ROLE-REFUSED`, `FAIL V-ICP-R3-KMEP-MARKER-ONLY-REFUSED` -> `ICP_SELFTEST=FAIL`
(the `-UNPARSABLE` gate stays ok under that partial revert only because the pre-existing code refuses it with a different message)
**GREEN:** all four `ok`, `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`

### WR-04: R3 never required a primary file for a D..I terminal and trusted the file's own claim -- FIXED

**Commit:** 6d329c4f
**Files:** `tools/test_incremental_cognition_program.py` (`terminal_claim_problems`, `FROZEN_RULE_DENOMINATORS`, `check_measurement_scope`, selftest), `tools/test_kme_pillars.py`, phase3.md sha rows
**Fix:** (1) a pillar in D..I whose ledger state has a terminal must cite at least one kme_pillars primary file with `terminal_evidence: true` that passes the
cross-check, else `R3 <P>: terminal <T> cites no kme_pillars primary measurement file ...` (a hand-written KME-G md with `command:` no longer slips through
by being uncited by R3). (2) every kme_pillars file claiming `terminal_evidence: true` on D..I is checked against its own fields:
`instrument == wiki/tools/kme_pillars.py`, `evidence_role == primary`, `population_match == exact` (a `referenced` CPP-D-W7 file only at `coverage == 1.0`,
which is the one reading of "exact" that keeps D's CPP-D-W7 leg closable; WR-06 below makes the instrument emit that only at an exact reproduction),
`materiality` in {">= 3 %", "< 3 %", "STRADDLES"} (never UNMEASURED/absent), `rule_denominators` equal to the wrapper's own copy of the frozen rule table (not
just trusted from the file), and `denominator` inside it. A contradiction yields `R3 <P>: <ref> claims terminal_evidence true but <why>`; an inconsistent primary no longer
counts as `has_primary` for a second workload. Deviation from the review text: it listed `population_match in (exact, referenced)`; this requires exact, or referenced
only for CPP-D-W7 at coverage exactly 1.
**Gates:** wrapper selftest `V-ICP-R3-TERMINAL-CLEAN`, `-TERMINAL-HAND-WRITTEN-REFUSED`, `-TERMINAL-NO-EVIDENCE-REFUSED`, seven `V-ICP-R3-MUT-*` contradictions
(denominator-KME-G, population-drifted, verdict-UNMEASURED, no-verdict, rule-widened, foreign-instrument, referenced-on-E), `-TERMINAL-DW7-REFERENCED-ACCEPTED`, `-TERMINAL-DW7-COVERAGE-REFUSED`;
instrument-driven `V-KMEP-R3-TERMINAL-REQUIRES-PRIMARY` (the real E KME-L primary file accepted with a terminal set, a hand-written KME-G file and a doctored copy refused,
wrapper table == `kme_pillars.RULE_DENOMINATORS`).
**RED (guard disabled):** nine selftest FAIL lines (`V-ICP-R3-TERMINAL-HAND-WRITTEN-REFUSED`, `-NO-EVIDENCE-REFUSED`, the seven `-MUT-*` ..., `-DW7-COVERAGE-REFUSED`) -> `ICP_SELFTEST=FAIL`, and
`FAIL V-KMEP-R3-TERMINAL-REQUIRES-PRIMARY primary_terminal=True good=[] hand=[] forged=[]` -> `KMEP_PASS=85/86`
**GREEN:** `ICP_SELFTEST=PASS`, `PASS V-KMEP-R3-TERMINAL-REQUIRES-PRIMARY ... table_eq=True` -> `KMEP_PASS=86/86  threshold=86/86`

### WR-05: second_workload_valid ignored the verdict -- FIXED

**Commit:** 0dbd46dc
**Files:** `wiki/tools/kme_pillars.py` (`_result`, `FRONT_OPTIONAL`), `tools/test_incremental_cognition_program.py` (R3 second_workload branch + selftest), `tools/test_kme_pillars.py`, phase3.md sha rows
**Reading of the frozen rule (as asked):** ledger rule E is "build a query path ... only at >= 3 % weighted on KME-L AND confirmed on a second workload". "Confirmed" means the
second workload shows the effect, so a `< 3 %` second workload does NOT confirm; it is a legitimate measurement that disconfirms, and `STRADDLES` is undecided. So two separate claims:
- `second_workload_valid` (usable as a measurement beside a primary) = population reproduced or workload not frozen AND verdict is measured (not UNMEASURED). R3 keeps accepting a valid second workload whatever its measured verdict.
- new optional front-matter field `second_workload_confirms` (written only for second_workload files) = valid AND verdict `>= 3 %`. R3 does not read it (R3 does not know whether a terminal is a build); whoever closes E reads it, and `terminal_evidence_reason` now prints `valid=..., confirms=..., materiality=...`.
R3 also refuses a second_workload file whose own `materiality` is UNMEASURED (guards a hand-edited `second_workload_valid: true`).
**Gates:** `V-KMEP-SECOND-WORKLOAD-NEEDS-VERDICT` (unmeasured -> valid False/confirms False; `< 3 %` -> True/False; `>= 3 %` -> True/True), wrapper `V-ICP-R3-SECOND-UNMEASURED-REFUSED`, `V-ICP-R3-SECOND-BELOW-3-ACCEPTED`.
**RED (validity line reverted):** `FAIL V-KMEP-SECOND-WORKLOAD-NEEDS-VERDICT rows={'unmeasured': ('UNMEASURED', True, False), ...}` -> `KMEP_PASS=86/87`; wrapper guard off: `FAIL V-ICP-R3-SECOND-UNMEASURED-REFUSED` -> `ICP_SELFTEST=FAIL`
**GREEN:** `PASS V-KMEP-SECOND-WORKLOAD-NEEDS-VERDICT rows={'unmeasured': ('UNMEASURED', False, False), 'below': ('< 3 %', True, False), 'above': ('>= 3 %', True, True)}` -> `KMEP_PASS=87/87  threshold=87/87`; `ICP_SELFTEST=PASS`
**Note:** committed measurement files were not regenerated: no committed file is a second_workload with a changed value for these fields (the two GEX44-B001 files are smoke), their content is untouched and the sha rows in phase3.md for them are unchanged.

### WR-06: referenced CPP-D-W7 share divided a measured numerator by the frozen denominator at coverage > 1 -- FIXED

**Commit:** 1bc24317
**Files:** `wiki/tools/kme_pillars.py` (`_result`, `_population_report`, D-W7 caveat), `tools/test_kme_pillars.py`, phase3.md sha rows
**Conservative option chosen and why:**
- coverage == 1.0 AND all five `DW7_FIELDS` equal -> reproduced: judged share = numerator / frozen weighted, `terminal_evidence` possible.
- coverage > 1, or coverage == 1 with any differing usage field -> a different population: the judged share is withheld (`share_interval: null`), verdict UNMEASURED with reason
  `referenced_population_not_reproduced (coverage ..., fields differing: [...])`, `terminal_evidence: false`. `share_measured_population` still reports the share over the MEASURED denominator, so the figure is not lost.
- coverage < 1 (partial) is unchanged: numerator / FROZEN weighted is a conservative lower bound (the unseen calls can only add numerator), UNMEASURED unless that lower bound alone clears 3 %, never terminal. Dividing a partial numerator by the measured denominator would overstate the share, so it is deliberately not used here (this differs from the literal "use the measured denominator when coverage is not exactly 1"; for coverage > 1 that figure is reported in `share_measured_population` but not judged).
`_population_report` (the `population` subcommand) now exits 0 for a referenced denominator only at coverage exactly 1 with no deltas. The old `coverage >= 1` terminal condition is gone.
Three existing gates built ledgers whose usage fields differed from the fixture's measured population while claiming coverage 1 (`V-KMEP-DW7-COVERAGE`, `-DW7-ROLES`, `V-KMEP-R3-E-PAIR`); they now build the ledger from the measured population (`ce_ledger_exact`) because that is what a reproduced population is.
**Gate:** `V-KMEP-DW7-COVERAGE` extended (equal -> measured + terminal true; calls above -> UNMEASURED/no share/not terminal; same calls other usage -> UNMEASURED; partial unchanged).
**RED (HEAD source):** `FAIL V-KMEP-DW7-COVERAGE ... above: cov=1.33 < 3 % terminal=True; same calls other usage: < 3 % terminal=True ...` -> `KMEP_PASS=86/87`
**GREEN:** `PASS V-KMEP-DW7-COVERAGE ... above: cov=1.33 UNMEASURED terminal=False; same calls other usage: UNMEASURED terminal=False` -> `KMEP_PASS=87/87  threshold=87/87`

### WR-07: --frozen-file / --frozen-ce-ledger could make a terminal file against an uncommitted denominator -- FIXED

**Commit:** a4d09a24
**Files:** `wiki/tools/kme_pillars.py` (`frozen_source_entry`, `_prepare`, `_result`, `FRONT_OPTIONAL`), `tools/test_incremental_cognition_program.py` (`FROZEN_SOURCE_DEFAULTS`, `terminal_claim_problems`), `tools/test_kme_pillars.py`, phase3.md sha rows
**Fix (instrument):** every KME-L / KME-G / CPP-D-W7 run records optional front-matter field `frozen_source` = `{frozen_file?: {path, sha256, default}, ce_ledger?: {...}, all_default}`
(LF-normalised sha256 of the bytes actually read; path repo-relative or absolute; `default` = resolves to the committed `DENOMS_REL` / `CE_LEDGER_REL`). A KME run records `frozen_file` (and `ce_ledger` if that flag
was passed); a CPP-D-W7 run records `ce_ledger` (and `frozen_file` if passed). `terminal_evidence` requires `all_default`; otherwise `terminal_evidence_reason` says "frozen source is not the repo default". OTHER runs have no frozen source (field absent).
**Fix (R3):** a terminal claim is only believed when `frozen_source` says all_default, the entry for the denominator (frozen_file for KME-L/G, ce_ledger for CPP-D-W7) has `default: true`, `path` equal to the committed path
(`FROZEN_SOURCE_DEFAULTS`, pinned equal to the instrument's constants by a gate) and `sha256` equal to the committed file's current LF sha256.
**Test-harness note:** in-process fixtures pass scratch frozen files; `run_main` points `kp.DENOMS_REL` / `kp.CE_LEDGER_REL` at the scratch file named on the command line (module constants, no production back door), and the two R3-driving gates point
`icp.FROZEN_SOURCE_DEFAULTS` at the same scratch files via `icp_sources`. `V-KMEP-TRACER-D-E2E` (a real subprocess with a scratch file) now asserts the new, correct outcome `terminal_evidence: false`.
**Gates:** `V-KMEP-FROZEN-SOURCE-RECORDED` (scratch file: sha recorded, not terminal; off-default CE flag: not terminal; D-W7 scratch ledger: not terminal; default file: terminal; default file + off-default CE flag: not terminal; OTHER: no source), wrapper `V-ICP-R3-MUT-no-frozen-source / non-default-source / source-sha-stale / source-path-elsewhere / wrong-source-kind`.
**RED (instrument reverted, tests kept):** `FAIL V-KMEP-FROZEN-SOURCE-RECORDED KeyError: 'frozen_source'`, `FAIL V-KMEP-TRACER-D-E2E ... terminal=True (scratch frozen file is not the committed default)`, `FAIL V-KMEP-R3-E-PAIR ... frozen_source is absent ...`, `FAIL V-KMEP-R3-TERMINAL-REQUIRES-PRIMARY` -> `KMEP_PASS=84/88`
**GREEN:** `PASS V-KMEP-FROZEN-SOURCE-RECORDED scratch file: terminal=False default=False sha_ok=True; ... default file: True; default file + off-default ce flag: False; OTHER source=None` -> `KMEP_PASS=88/88  threshold=88/88`; `ICP_SELFTEST=PASS`; drill `DRILL killed=20/20`

### IN-01: pillar D observability was "any attachment line seen" -- FIXED

**Commit:** 326da74c
**Files:** `wiki/tools/kme_pillars.py` (`DObserver`), `tools/test_kme_pillars.py`, regenerated `measurements/D-KME-G-2026-10-03.md` and `measurements/D-GEX44-B001-2026-10-03.md`, phase3.md (sha rows, D table row, D Intelligence Delta bullet)
**Fix:** a session counts as observed for D only when a `hook_*` attachment of any type (hook_success, hook_additional_context, hook_system_message, ...) was seen in it (`hook_sessions`). A transcript with only `file` / `todo_reminder` attachments is unobserved, so observability is 0 and the verdict UNMEASURED, never `< 3 %`. The "explicit attachment-capable marker" alternative was not added: the transcript format has no such marker, and a hook-attachment sighting is the positive evidence the fix intent asked for. `details.sessions_with_attachment_lines` is kept; new `details.sessions_with_hook_attachments` shows the basis.
**Gate:** `V-KMEP-D-NEEDS-HOOK-ATTACHMENT` (file+todo_reminder only -> obs 0.0 UNMEASURED rc 3; the same plus one hook_success -> obs 1.0 `< 3 %`; mixed two sessions -> obs 0.5 UNMEASURED).
**RED (HEAD source):** `FAIL V-KMEP-D-NEEDS-HOOK-ATTACHMENT non-hook attachments only: obs=1.0 < 3 % rc=0; plus hook_success: obs=1.0 < 3 %; mixed: obs=1.0 < 3 %` -> `KMEP_PASS=88/89`
**GREEN:** `PASS V-KMEP-D-NEEDS-HOOK-ATTACHMENT non-hook attachments only: obs=0.0 UNMEASURED rc=3; plus hook_success: obs=1.0 < 3 %; mixed: obs=0.5 UNMEASURED` -> `KMEP_PASS=89/89  threshold=89/89`
**Committed measurement files changed -- regeneration:** replaying the recorded `command:` of both D files changed content, so both were regenerated by that exact command (old file moved aside, same name rewritten, one scan each):
- `D-GEX44-B001-2026-10-03.md`: a REAL wrong reading was corrected. Old: `materiality: "< 3 %"`, `observability: 1.0`. New: `materiality: "UNMEASURED"`, `materiality_reason: "signal not recorded for part of the population"`, `observability: 0.8552` (7 of its 10 sessions have a hook attachment; the other 3 had attachment lines but none was a hook). The share interval [0.0015 %, 0.0022 %] is unchanged. sha256 `7f9da08d...` -> `22527425a4f53ae9...e56`.
- `D-KME-G-2026-10-03.md`: numerator, share, verdict (STRADDLES), observability unchanged; only added keys (`frozen_source` default-true with the committed file sha, `second_workload_confirms`, `sessions_with_hook_attachments`, `project_filter`, `since`...) and `measured_at`. sha256 `b1ad9164...` -> `e8d7c24d005217d6...fc88fc3`.
- The other seven committed files (E, F, G, H x2, I x2) were NOT regenerated: their numerators, shares, verdicts and observability do not depend on any changed code path (WR-01, WR-02 signatures verified unchanged for H, WR-05/06/07 and IN-01 add only optional keys to new runs); their content is untouched and their sha rows in phase3.md are unchanged. They predate `frozen_source`, so R3 would refuse them as terminal on that ground too (they are smoke files and refused anyway).
- a5 / a7 / b001 snapshot diff: `find -printf '%p %s %T@'` of the three env trees, sha256 before and after the two replays: `cb3de1bed50b6db51b805072822fdeb43d28dbd1a4dcee239d3fcc6bba22c769` both -> empty diff.

## Final verification (run in this worktree `.claude/worktrees/ic-run`, after the last code commit 326da74c)

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` (83/83 before; +6 gates: OUT-DIR-INSIDE-ROOT, SIGNATURE-NO-URL-TOKEN, R3-TERMINAL-REQUIRES-PRIMARY, SECOND-WORKLOAD-NEEDS-VERDICT, FROZEN-SOURCE-RECORDED, D-NEEDS-HOOK-ATTACHMENT). `V-KMEP-AUDIT-BYTE-IDENTICAL` and `-REAL` PASS (frozen audit output byte-identical).
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL 84/84`, `PASS DRILL-CLEAN-AFTER-MUTANTS 84/84`, `DRILL killed=20/20` (no new mutants were added; the new gates were each driven RED by reverting their fix, recorded above).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS` (V-ICP-REAL-OWNER-READ is the pre-existing INCONCLUSIVE: commits fa9ae2ed / 21671d6c not in this clone).
- `--pillar D` .. `--pillar I` -> each `FAIL L3 <P>: no terminal disposition`, `CEP_PILLAR_<P>=FAIL`, `ICP_PILLAR_<P>=FAIL` (expected: state D..I is empty; no R3 line added).
- a5 / a7 / b001 read-only: the instrument only reads them (its sole writer is `write_measurement` to the out-dir, which WR-01 now refuses to place inside a root). Around the two D regenerations the `find -printf '%p %s %T@'` hash of the three env trees was `cb3de1be...` before and after (empty diff). A later whole-env hash differed because the live `gsd-mission-sweep.log` under `a5-env/home/.claude/state/` and `a7-env/home/.claude/state/` was rewritten by its sweeper (outside the `.claude/projects` read set, not by this run). The seven committed measurement files not regenerated were re-run to a scratch directory and compared: numerators, shares, verdicts and observability identical; differing only in `command` (the scratch `--out-dir`), `measured_at`, optional keys, `corpus.project_filter`, and for H the HEAD commit recorded in `consumed_owner_verdicts`.
- Not touched: `tools/test_cognitive_economy_program.py`, `vault/progress.md`, the workstream `config.json` / `milestone.lock`, the untracked `docs/*/*kme_pillars*` files, ledger `state.D..I`, any IC-* tick.

## Scope notes

- IN-02 (BOM literal, span-less G hits, two `_utcnow()` calls) was outside the requested bound and is unchanged.
- Commits (all pathspec-only, hooks on): d241bb5e WR-01, 8f835ed6 WR-02, 42800120 WR-03, 6d329c4f WR-04, 0dbd46dc WR-05, 1bc24317 WR-06, a4d09a24 WR-07, 326da74c IN-01, ed59fcfe docs (phase3 evidence). REVIEW-FIX.md itself is not committed.

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
