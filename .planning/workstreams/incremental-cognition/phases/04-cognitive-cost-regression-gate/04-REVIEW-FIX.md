---
phase: 04-cognitive-cost-regression-gate
fixed_at: 2026-10-03T23:56:40Z
review_path: .planning/workstreams/incremental-cognition/phases/04-cognitive-cost-regression-gate/04-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Source review:** 04-REVIEW.md (CR-01, CR-02, WR-01, WR-02, WR-03, IN-01, IN-02; all seven in the requested bound)
**Iteration:** 1
**Run plane:** edits, gates and commits in the existing isolated worktree `.claude/worktrees/ic-run` (branch
`mission/incremental-cognition-run`, started at HEAD f5be1ec6); no nested worktree was created. Every gate below ran in this
same tree on GEX44 (`python3`, Linux). Each fix: RED gate first, driven through the real CLI (`run_cli`, a subprocess)
and, where a drill mutant must reach it, also in-process (`run_main`); then the fix; then green; one pathspec commit per
finding (`git commit -F <msgfile> -- <paths>`, Opus 5.5 trailer); a mutant per CR/WR in `--drill`.

Findings WR-01, WR-02 and WR-03 change a condition (logic), so they are marked `fixed: requires human verification` below:
the syntax and gate checks pass, but whether the thresholds and verdict names are what the Owner wants is a judgement the
gates cannot make. The decisions themselves were taken by the orchestrator and applied as given.

## Outcomes

### CR-01: unparseable line inside the startup window dropped silently -- FIXED

**Commit:** 19792a95
**Files:** `tools/floor_regression_gate.py` (`read_window`), `tools/test_floor_regression_gate.py`
**Fix:** `read_window` counts window lines that are not JSON objects (a truncated line, a valid JSON scalar or list); if any,
UNMEASURABLE exit 2 `window_line_unparseable` naming the count. The "no parseable line at all" case keeps its earlier
`unreadable` reason. Lines after the first assistant row are still never read.
**Gate:** `V-FLOOR-WINDOW-LINE-UNPARSEABLE` (CLI and in-process): `instructions` line cut to 50 bytes -> exit 2; a `[1, 2, 3]`
line -> exit 2; `--write-reference` from such a window -> exit 2, nothing written; positive controls: the intact check
transcript is green, and damage appended AFTER the first assistant row stays green.
**RED (fix absent):** `FAIL V-FLOOR-WINDOW-LINE-UNPARSEABLE cli cut instructions: rc=0 last='FLOOR verdict=WITHIN_BOUND exit=0 reason=within_bound'; ... cli write: rc=0 ... REFERENCE_WRITTEN ... exists=True` -> `FLOOR_PASS=60/61`
**GREEN:** `PASS V-FLOOR-WINDOW-LINE-UNPARSEABLE` -> `FLOOR_PASS=61/61`
**Mutant:** M14 (`read_window` replaced by the pre-fix function) KILLED by the gate.

### CR-02: a written reference recorded raw hook command text -- FIXED

**Commit:** 25c13924
**Files:** `tools/floor_regression_gate.py` (`hook_source_key` replaces `command_label`; `_script_basename`),
`tools/test_floor_regression_gate.py`, `vault/programs/incremental-cognition/floor/reference-gex44.json` (regenerated)
**Fix:** the component `source` of a hook is `hook:` + sha256(command)[:16] and, at most, the basename of the first
script-looking token (an allow-listed extension, `[A-Za-z0-9._-]{1,64}`; flags and `NAME=value` tokens skipped). The command
text is never stored or printed; matching between reference and check runs on that key.
**Reference regenerated:** `python3 tools/floor_regression_gate.py --write-reference vault/.../reference-gex44.json
--transcript <34f03871 jsonl> --replace`. The transcript is read-only (sha256 identical before and after); `window_sha256`
`dc6d23b90cac...` and `window_rows` 34 came out identical, `total_chars` 207245 and `tokens` unchanged; only the two hook
sources and `provenance.command` / `measured_at` / `repo_commit` changed. `grep` of the file for `node `, `CLAUDE_PLUGIN_ROOT`,
`--event` finds nothing. `V-FLOOR-REAL-REFERENCE-PINNED` still PASSes.
**Gate:** `V-FLOOR-HOOK-SOURCE-NO-COMMAND-TEXT` (CLI and in-process): hook commands carrying `DB_PASS=<value>`, a
`--password=<value>` flag and a quoted `--token '<value>'`; the written reference and the check output (text and `--json`)
hold none of them; sources equal the contract keys `hook:<16 hex>:u.js` / `hook:<16 hex>:p.py` (computed in the test from
the contract, not from the gate's helper); same floor green, +1024 in the user-registered hook red (universal, `universal_1k`);
control: a command whose hash differs is another source and reads red. Four older gates that looked a hook component up by
its raw command (`V-FLOOR-HOOK-PLUGIN`, `-SETTINGS-UNREADABLE`, `-CWD-ABSENT-UNATTRIBUTED`, `-RELABEL-NO-RISE`) now look it
up by the key (`hook_src`).
**RED (fix absent):** the reference held `DB_PASS=hunter2hunter2xx node ".../u.js" --[REDACTED:generic_secret] ...` and
`python3 .../p.py --token 'Sup3rS3cretValue12Zq'` as sources: the redactor caught only the `--password=` flag; the env
assignment and the quoted token passed it. `FLOOR_PASS=61/62`.
**GREEN:** `FLOOR_PASS=62/62`.
**Mutant:** M15 (`hook_source_key` returns the raw command) KILLED by the gate.

### WR-01: a wholly absent reference layer read as a fall -- FIXED (requires human verification)

**Commit:** b7adc31f
**Files:** `tools/floor_regression_gate.py` (`absent_layers`, `compare`; docstring), `tools/test_floor_regression_gate.py`
**Fix:** a reference layer whose components total >= 1,000 chars (`UNIVERSAL_MIN_CHARS`) with no component at all in the
checked floor -> UNMEASURABLE exit 2 `layer_absent:<first layer>`; the detail names every absent layer. A layer still present
but shrunk stays a fall (green, ratchet hint); a layer under 1,000 chars vanishing stays green.
**Gate:** `V-FLOOR-LAYER-ABSENT` (CLI and in-process): the reviewer's repro (instructions row removed, 100,000-char
`memory_global`), user `CLAUDE.md` removed alone, boundary (`rules` 1,000 chars gone -> exit 2; 999 -> green), shrunk-layer
control green; the detail names `memory_project` too in the whole-row case.
**RED:** `... want reason=layer_absent:memory_global` with `rc=0 ... WITHIN_BOUND` -> `FLOOR_PASS=62/63`
**GREEN:** `FLOOR_PASS=63/63`
**Mutant:** M16 (`absent_layers` returns nothing) KILLED by the gate.

### WR-02: an uncorrelated hook element was filed `project` on the event alone -- FIXED (requires human verification)

**Commit:** 03f845e1
**Files:** `tools/floor_regression_gate.py` (`uncorrelated_scope` replaces `_event_scope`; `correlate_hook`; docstring),
`tools/test_floor_regression_gate.py`, `vault/.../floor/reference-gex44.json` (regenerated again)
**Fix:** an element with no producing `hook_success` row is `unattributed`, basis `event_uncorrelated`, whatever the
registrations (user, project, both, neither) -- the old basis `event_fallback` is gone. `correlate_hook` also correlates a hook
that prints plain text (for `additionalContext`, stdout equal to the element).
**Pinned behaviour updated:** `V-FLOOR-HOOK-EVENT-FALLBACK` (all four registration shapes -> unattributed; the project-only +1024
case is now exit 1 instead of 0), `V-FLOOR-LAYER-TABLE` (two rows move universal -> unattributed),
`V-FLOOR-CWD-ABSENT-UNATTRIBUTED` (the "event fallback" row). The `scope_basis` text in the module docstring is rewritten.
**Gate:** `V-FLOOR-HOOK-UNCORRELATED-UNATTRIBUTED`: the reviewer's repro (project settings register `SessionStart`, user
nothing, +1,199 chars, no producer row) -> exit 1, `RISE ... scope=unattributed rules=universal_1k`, no `scope=project`
layer; the four registration shapes; plain-text stdout correlated to its project-registered command -> `project`.
**RED:** `project-only +1199: rc=0 rise=[] ... WITHIN_BOUND`; `user only: ('universal', 'event_fallback') want ('unattributed',
'event_uncorrelated')` ... -> `FLOOR_PASS=63/64`
**GREEN:** after the three pinned gates were updated, `FLOOR_PASS=64/64`.
**Reference regenerated again** (same transcript, same command, `--replace`; transcript sha256 unchanged): the
`UserPromptSubmit` element is now `unattributed` / `event_uncorrelated`; window pin, rows, tokens and total_chars unchanged.
**Mutant:** M17 (`uncorrelated_scope` restored to the pre-fix event rule) KILLED by `V-FLOOR-HOOK-UNCORRELATED-UNATTRIBUTED`
and `V-FLOOR-HOOK-EVENT-FALLBACK`.

### WR-03: unmeasured / non-comparable tokens axis ended WITHIN_BOUND exit 0 -- FIXED (requires human verification)

**Commit:** 440578c4
**Files:** `tools/floor_regression_gate.py` (`unmeasured_tokens_verdict`, `compare(..., chars_only)`, `exit_code`, `render`,
`--chars-only`, docstring), `tools/test_floor_regression_gate.py`, `vault/programs/incremental-cognition/owner-bundle.md`,
`vault/programs/incremental-cognition/evidence/K.md`
**Fix:** a floor within bound on chars whose tokens axis is `no_model_call` or `not_comparable` is UNMEASURABLE exit 2
`tokens_unmeasured` (the char comparison is still printed, the detail names the status); with the new `--chars-only`
(`--check` only; with `--write-reference` it is refused, `chars_only_without_check`) the verdict is `WITHIN_BOUND_CHARS_ONLY`,
exit 0, reason `within_bound_chars_only`, with a `CHARS_ONLY ... the tokens axis was not compared (status=...)` line. Design
choice recorded: a tokens axis that CAN be compared is still enforced with the flag (a +3.3 % rise stays exit 1); a material
chars rise stays exit 1 either way; the flag authorizes only the non-comparison.
**Pinned behaviour updated:** `V-FLOOR-TOKENS-RULE` (different prompt), `V-FLOOR-NO-MODEL-CALL` (check and no assistant row),
`V-FLOOR-REF-GEX44-GREEN` (real transcripts: now exit 2 without the flag, `WITHIN_BOUND_CHARS_ONLY` with it).
**Callers updated:** `owner-bundle.md` [K] item -- option A self-check and PRG lines take `--chars-only` (an ordinary session
vs a probe-written reference is not tokens-comparable by construction) and the verdict to record is
`WITHIN_BOUND_CHARS_ONLY`; option B's same-session sanity parse stays exit 0 (same prompt digest); option B's PRG gets a
second line with `--chars-only`, run only if the first prints exit 2 `tokens_unmeasured`; `V-FLOOR-BUNDLE-ARGV-PARSES` green
(7 gate lines). `evidence/K.md`: rule text and the real smoke re-run, with the pre-fix capture marked superseded.
**Real GEX44 smoke re-run** (committed `reference-gex44.json` vs interactive session 607795c4; transcript sha256 identical
before and after): without the flag `FLOOR verdict=UNMEASURABLE exit=2 reason=tokens_unmeasured` (`TOKENS status=not_comparable
ref=109021 now=107351`); with `--chars-only` `FLOOR verdict=WITHIN_BOUND_CHARS_ONLY exit=0 reason=within_bound_chars_only`.
The pre-fix run printed `WITHIN_BOUND exit=0` for the same inputs.
**Gate:** `V-FLOOR-TOKENS-UNMEASURED` (CLI and in-process): both statuses default -> exit 2, no plain `WITHIN_BOUND` line;
`--chars-only` -> verdict/exit/`CHARS_ONLY` note; `--json` verdict; a chars rise with tokens unmeasured is exit 1 with and
without the flag; measured and comparable tokens is plain `WITHIN_BOUND` with and without the flag; measured +3.3 % with
`--chars-only` is exit 1; `--write-reference --chars-only` refused.
**RED:** the flag was rejected by argparse and the default printed `WITHIN_BOUND exit 0` -> `FLOOR_PASS=64/65`
**GREEN:** after the three pinned gates were updated, `FLOOR_PASS=65/65`.
**Mutant:** M18 (`unmeasured_tokens_verdict` returns plain `WITHIN_BOUND`) KILLED by `V-FLOOR-TOKENS-UNMEASURED`,
`V-FLOOR-NO-MODEL-CALL`, `V-FLOOR-TOKENS-RULE`.

### IN-01: a failed `--replace` write left a stray temp file -- FIXED

**Commit:** e8fe57c5
**Files:** `tools/floor_regression_gate.py` (`write_reference`), `tools/test_floor_regression_gate.py`
**Fix:** the temp write and `os.replace` run in a `try`; a `finally` unlinks `<target>.tmp<pid>` if it still exists.
**Gate:** `V-FLOOR-REPLACE-FAILURE-NO-STRAY-TMP` (CLI and in-process): `os.replace` onto an existing directory fails for real ->
exit 2 `write_failed`, no stray file, target intact; control: a successful `--replace` leaves only the target.
**RED:** `stray=['ref.json.tmp3741843']` -> `FLOOR_PASS=65/66`; **GREEN:** `FLOOR_PASS=66/66`.
(No mutant: only CR and WR findings were required to have one.)

### IN-02: `--probe` appends to a tracked file undocumented; `--json` dropped `detail` -- FIXED

**Commit:** ef336ec7
**Files:** `tools/floor_regression_gate.py` (docstring, `--probe` help, `JSON_KEYS`), `tools/test_floor_regression_gate.py`
**Fix:** the module docstring and the `--probe` help state that `--probe` appends one row to the tracked
`wiki/tools/listing_floor_probe.results.jsonl` unless `CPP_FLOOR_PROBE_RESULTS` names another file; `JSON_KEYS` gains `detail`
and `probe_error` (null/empty on success).
**Gate:** `V-FLOOR-JSON-DETAIL-AND-PROBE-NOTE`: `--json` of a `reference_missing` exit 2 carries `detail` equal to the text-mode
detail; of a stub-proven `probe_failed` (mode 0644 stub) carries `probe_error: "PermissionError"` and a detail; `--help` and the
docstring name the file; `V-FLOOR-JSON` key set is now 14.
**RED:** `FLOOR_PASS=65/67` (keys differ: `detail`, `probe_error`; docs lack the file name); **GREEN:** `FLOOR_PASS=67/67`.

## Final verification (run in this worktree, after the last code commit ef336ec7 and the docs commit 7de23688)

- `python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0` (60 before
  this run; +7 gates: WINDOW-LINE-UNPARSEABLE, HOOK-SOURCE-NO-COMMAND-TEXT, LAYER-ABSENT, HOOK-UNCORRELATED-UNATTRIBUTED,
  TOKENS-UNMEASURED, REPLACE-FAILURE-NO-STRAY-TMP, JSON-DETAIL-AND-PROBE-NOTE). The real-transcript gates PASS (none SKIPped):
  REAL-GEX44, REAL-A7-NO-CALL, REAL-APPENDED-PROMPT, SEEDED-REAL, REF-GEX44-GREEN, REAL-REFERENCE-PINNED
  (`dc6d23b90cac` rows=34 re-derived from disk).
- `python3 tools/test_floor_regression_gate.py --drill` -> `PASS DRILL-CONTROL 57/57`, `PASS DRILL-CLEAN-AFTER-MUTANTS 57/57`,
  `PASS DRILL-RESTORE` (gate sha256 `096d71cc164eac46` before == after), `DRILL killed=18/18` (M1-M13 as before; new M14-M18).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`.
- `python3 tools/test_incremental_cognition_program.py --pillar K` -> `FAIL L3 K: no terminal disposition`, `CEP_PILLAR_K=FAIL`,
  `ICP_PILLAR_K=FAIL` (expected: pillar K stays OPEN).
- Real transcripts 34f03871 and 607795c4 were read only (sha256 recorded before and after every regeneration / smoke run:
  identical). No real `claude` session was started (`--probe` only through scratch stubs under the test fence). Nothing was
  written under `~/.claude/**`.
- Not touched: `vault/progress.md` (it carries an uncommitted modification that predates this run and is not part of any
  commit here), the workstream `config.json` / `milestone.lock`, `docs/*kme_pillars*`, ledger `state.K` (still `{}`), any IC-K
  tick.

## Scope notes

- The laptop path: the bundle now takes the fixed tool files and the regenerated reference as a tree state of `ef336ec7`
  (commit 440578c4 also edits the bundle and evidence, which the laptop does not need, so a plain cherry-pick of it would
  conflict there). Unproven on the laptop, like the rest of the [K] item.
- The committed `reference-gex44.json` is a GEX44 test and smoke input; the frozen rule's laptop reference is still pending.
- Commits (all pathspec-only, hooks on): 19792a95 CR-01, 25c13924 CR-02, b7adc31f WR-01, 03f845e1 WR-02, 440578c4 WR-03,
  e8fe57c5 IN-01, ef336ec7 IN-02, 7de23688 docs (bundle + evidence). REVIEW-FIX.md is committed separately, after this write.

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
