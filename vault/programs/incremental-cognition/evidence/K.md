# Pillar K -- cognitive cost regression (startup floor ratchet): evidence

Plane: GEX44 `kobicraft-gex44` (Linux 6.8, user `kobii`), `python3` 3.12.3, branch `mission/incremental-cognition-run`,
worktree `/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run`. Measured 2026-10-04, foreground, from
the worktree root. Nothing here was run on the laptop; the laptop-plane step is the `[K]` item in
`vault/programs/incremental-cognition/owner-bundle.md` (section `## Phase 4 -- floor reference (laptop plane)`).

## Frozen rule (verbatim from ledger.json, frozen.pillars id K)

> a gate that measures the current startup floor by layer and fails on a material unexplained rise versus a committed reference; a 1K universal addition reported distinctly from project-local

The reference this rule names is a committed `floor/reference.json` written from the laptop install. It does not exist
yet, so the rule is built and smoke-proven on GEX44 and not closed.

## What the gate measures

`tools/floor_regression_gate.py` reads the startup window of a session transcript (every row before the first
`assistant` row) and classifies each model-visible component by LAYER (what it is) and SCOPE (who it applies to):

| layer | scope basis |
|---|---|
| `memory_global` (a User `CLAUDE.md`) | universal |
| `memory_project` (a Project or Local `CLAUDE.md` / `CLAUDE.local.md`) | project |
| `rules` (files under `/.claude/rules/`) | by file type |
| `skill_listing` (per entry; header lines) | by name: a file under the project `.claude` is project, under the install home universal, both or neither unattributed, a `ns:rest` plugin name universal; header unattributed |
| `other:agent_listing_delta` (per added type) | by name, same rule |
| `hook_context:<event>:<name>` and `hook_system_message:...` | by the producing hook: `${CLAUDE_PLUGIN_ROOT}` universal; else the settings file REGISTERING the command (never where the script lives); both or neither or several commands unattributed |
| `system_prompt` (per part, identified by digest) | unattributed |
| `other:environment`, `model`, `date`, `auto_mode`, `command_permissions`, `credential_org`, `remote_session_change`, `session_context` | harness (provable by type) |
| any other attachment type | unattributed |
| user rows, `file` attachments, `hook_success` rows | excluded (prompt-driven / raw stdout, counted only) |

These are stated heuristics. Scope is computed on the measuring host at measure time from the settings and skill files
present then; a `cwd` or install home that is not a directory on that host leaves everything unattributed (absent is not
zero). Scope is never guessed: an origin that cannot be proved stays `unattributed` and under the 1,000-char rule.

Materiality (a rise is a positive delta of one (layer, scope) row against the reference), constants in the gate file:
`LAYER_PCT = 0.03` (a row up by 3 % of the reference total), `TOTAL_PCT = 0.03` (the total up by 3 %),
`UNIVERSAL_MIN_CHARS = 1000` (a universal or unattributed row up by 1,000 chars; project and harness rows are exempt
from this one), `TOKENS_PCT = 0.03` (first-call tokens up by 3 %, only when both prompt digests are equal; otherwise
`TOKENS status=not_comparable`, which since the review fix WR-03 is exit 2 `tokens_unmeasured` unless `--chars-only` is
passed, giving verdict `WITHIN_BOUND_CHARS_ONLY`). A material finding is cleared only by an entry in the reference `explanations`
(layer, scope, unit, delta_bound, reason, commit) whose bound covers the delta.

Exit codes: 0 within bound, 1 material unexplained rise, 2 UNMEASURABLE (never 0 for anything not measured).
UNMEASURABLE reasons present in the gate: `reference_missing`, `reference_invalid`, `reference_exists`, `refused_path`,
`not_comparable`, `no_model_call`, `no_skill_listing`, `no_transcript`, `unreadable`, `write_failed`,
`explanation_refused`, `invalid_session_id`, `secret_firewall_unavailable`, `cwd_without_probe`, `probe_cwd_missing`,
`probe_unavailable`, `probe_fenced`, `probe_failed`, `claude_exe_not_found`.

Four mutually exclusive measurement sources: `--transcript PATH`, `--project-dir DIR` (the newest top-level `*.jsonl`),
`--session SID` (located by the owner's `listing_floor_probe.transcript`), `--probe [--cwd DIR]` (one fresh headless
session through the owner's `listing_floor_probe.main`; costs a session; proven only through stub executables, no test or
command here started a real `claude` session). The reference pins its window with `provenance.window_sha256` and
`window_rows`, computed by one function (`window_digest`).

## Commands and observed outputs

All from the worktree root on GEX44.

`python3 tools/test_floor_regression_gate.py` (exit 0):

```
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0
```

Real-data lines of that run (none SKIPped on GEX44):

```
PASS V-FLOOR-REAL-GEX44 real GEX44 floor reproduced exactly: total=202803 tokens=107351 window_rows=34
PASS V-FLOOR-REAL-A7-NO-CALL login-expired session: tokens no_model_call, owner startup_tokens 0, no reference written (exit 2)
PASS V-FLOOR-REAL-APPENDED-PROMPT reference from the interactive session, check of the mission worker: RISE system_prompt scope=unattributed delta=+4383 unit=chars rules=universal_1k
PASS V-FLOOR-SEEDED-REAL real transcript 607795c4: +1,024 user CLAUDE.md RED (memory_global universal), same bytes in the project CLAUDE.md green (project +1024)
PASS V-FLOOR-REF-GEX44-GREEN today's interactive floor (607795c4) vs the plane-gex44 reference: tokens not comparable -> exit 2 tokens_unmeasured; --chars-only -> WITHIN_BOUND_CHARS_ONLY, universal +0, project +0
PASS V-FLOOR-REAL-REFERENCE-PINNED committed reference window pinned to 34f03871: sha256 dc6d23b90cac rows=34 re-derived from disk
PASS V-FLOOR-BUNDLE-ARGV-PARSES 7 gate lines and 2 test lines of the Phase 4 [K] item parse with their own argparse (controls: bad bundle raises 3 problems, good bundle none)
```

`python3 tools/test_floor_regression_gate.py --drill` (exit 0): `PASS DRILL-CONTROL unmutated run: 57/57 gates green
(skipped 0)`, 18 `KILLED` lines (M1 scope_key universal, M2 scope_key project, M3 `UNIVERSAL_MIN_CHARS = 10**9`, M4
validate_explanations accepts all, M5 covering ignores bound and unit, M6 exit_code maps UNMEASURABLE to 0, M7 no
layer_3pct, M8 system prompt part scope harness, M9 correlate_hook returns no producing command, M10 scope_for_name never
project, M11 host_has always true, M12 newest_transcript returns the oldest, M13 first_call_tokens accepts a
`<synthetic>` row; review-fix mutants M14 read_window drops an unparseable window line, M15 hook_source_key stores the raw
command, M16 absent_layers finds nothing, M17 uncorrelated hook element filed by its event's registrations, M18
unmeasured tokens verdict reads plain WITHIN_BOUND), `PASS DRILL-CLEAN-AFTER-MUTANTS 57/57`, `PASS DRILL-RESTORE gate file
sha256 096d71cc164eac46 before == after`, and:

```
DRILL killed=18/18
```

GEX44 check, today's interactive session against the committed plane-gex44 reference (the reference was written from
the mission worker `34f03871`). **Re-run after the review fix WR-03 (2026-10-04, code HEAD at the time: see the commit
list below); the first capture of this smoke, taken before the fix, printed `FLOOR verdict=WITHIN_BOUND exit=0` for the
same inputs and is superseded: that exit 0 was green on chars alone while the tokens axis had not been compared.** The
transcript's sha256 was identical before and after both runs.

```
$ timeout 120 python3 tools/floor_regression_gate.py --check --reference vault/programs/incremental-cognition/floor/reference-gex44.json --transcript /home/kobii/.claude/projects/-home-kobii-missions-incremental-cognition--claude-worktrees-ic-run/607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl
SOURCE transcript name=607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl
UNMEASURABLE tokens_unmeasured: the tokens axis was not compared (status=not_comparable); the chars axis is within bound; pass --chars-only to accept a chars-only comparison
FLOOR total_chars ref=207245 now=202803 delta=-4442
WINDOW ref_sha256=dc6d23b90cac now_sha256=d5e2920263a0 ref_rows=34 now_rows=34 same=no
LAYER other:session_context scope=harness ref=1180 now=1121 delta=-59
LAYER system_prompt scope=unattributed ref=13830 now=9447 delta=-4383
SCOPE universal=+0 project=+0 harness=-59 unattributed=-4383
SKILLS ref_chars=30000 now_chars=30000 ref_entries=294 now_entries=294 ref_skill_count=294 now_skill_count=294
TOKENS status=not_comparable ref=109021 now=107351 delta=na
FLOOR verdict=UNMEASURABLE exit=2 reason=tokens_unmeasured
```

Exit 2. The same command with `--chars-only` appended, exit 0:

```
SOURCE transcript name=607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl
FLOOR total_chars ref=207245 now=202803 delta=-4442
WINDOW ref_sha256=dc6d23b90cac now_sha256=d5e2920263a0 ref_rows=34 now_rows=34 same=no
LAYER other:session_context scope=harness ref=1180 now=1121 delta=-59
LAYER system_prompt scope=unattributed ref=13830 now=9447 delta=-4383
SCOPE universal=+0 project=+0 harness=-59 unattributed=-4383
SKILLS ref_chars=30000 now_chars=30000 ref_entries=294 now_entries=294 ref_skill_count=294 now_skill_count=294
TOKENS status=not_comparable ref=109021 now=107351 delta=na
CHARS_ONLY the tokens axis was not compared (status=not_comparable); only the chars axis was checked
FLOOR verdict=WITHIN_BOUND_CHARS_ONLY exit=0 reason=within_bound_chars_only
```

Appended-prompt real red (reverse direction: a scratch reference from `607795c4`, checked against the mission worker
`34f03871`; quoted from `04-03-SUMMARY.md`, which captured it to `/tmp/ic-p4-03-reverse.txt` with `exit=1`; reproduced
every run by `V-FLOOR-REAL-APPENDED-PROMPT` above):

```
LAYER system_prompt scope=unattributed ref=9447 now=13830 delta=+4383
RISE system_prompt scope=unattributed delta=+4383 unit=chars rules=universal_1k
SCOPE universal=+0 project=+0 harness=+59 unattributed=+4383
FLOOR verdict=MATERIAL_RISE exit=1 reason=material_rise
```

Seeded real rise (`V-FLOOR-SEEDED-REAL`, line above): +1,024 chars appended to the user `CLAUDE.md` of a scratch copy of the
real transcript reads RED naming `memory_global` / `universal`; the same bytes appended to the project `CLAUDE.md` read
green and `project +1024`.

Default-reference refusal (no `--reference`, so `floor/reference.json`, which is laptop-plane and absent here), exit 2:

```
$ python3 tools/floor_regression_gate.py --check --transcript <607795c4 jsonl>
UNMEASURABLE reference_missing: no such reference file
FLOOR verdict=UNMEASURABLE exit=2 reason=reference_missing
```

Source-level scope-split drill (04-01, recorded in `04-01-SUMMARY.md`): `return "universal"` inserted as the first
statement of `scope_key` in a COPY of the gate; `--gate-path <copy>` exited 1 with `FAIL V-FLOOR-PROJECT-LOCAL` and
`FAIL V-FLOOR-SCOPE-REPORT`, and the real file's sha256 was unchanged.

Program verifier, pillar still open:

```
$ python3 tools/test_incremental_cognition_program.py --pillar K      (exit 1)
  FAIL L3 K: no terminal disposition
CEP_PILLAR_K=FAIL
ICP_PILLAR_K=FAIL
$ python3 tools/test_incremental_cognition_program.py --selftest      (exit 0)
CEP_SELFTEST=PASS
ICP_SELFTEST=PASS
```

Ledger `state.K` prints `{}`; `grep -c '\[x\] \*\*IC-K\*\*' .planning/workstreams/incremental-cognition/REQUIREMENTS.md` prints `0`.

Code commits of the gate (oldest first): `7fdef637`, `e4459393`, `8422eb2d`, `13f3bffe`, `11686c8d`, `f065ac8e`,
`17228d2f`, `09bb9142`; the `[K]` bundle item and its parse gate: `d40bd16c`. Phase 4 code-review fixes (report:
`.planning/workstreams/incremental-cognition/phases/04-cognitive-cost-regression-gate/04-REVIEW-FIX.md`): CR-01
`19792a95`, CR-02 `25c13924`, WR-01 `b7adc31f`, WR-02 `03f845e1`, WR-03 `440578c4`, IN-01 `e8fe57c5`, IN-02 `ef336ec7`.

## R2-W1 pin of the plane-gex44 reference

`floor/reference-gex44.json` carries `provenance.window_sha256` `dc6d23b90cac05e665ca0eb7b9b4c57ce440a4e0bb8f9f4e8c45d91c5885fd63`
and `window_rows` 34, written from the mission worker session `34f03871` (plane gex44, `explanations` empty). The gate
`V-FLOOR-REAL-REFERENCE-PINNED` re-reads that transcript from disk with `read_window` + `window_digest`, recomputes both
values, and compares them to the committed reference; it prints SKIP (never PASS) when the transcript is absent and
FAILs when the reference is missing or the pin differs. This reference is a test and smoke input only; it is not the
frozen rule's reference (that is the laptop one, `floor/reference.json`, not produced here). It was regenerated twice by
the review fixes (CR-02: hook sources became `hook:<sha256[:16]>[:basename]` instead of raw command text; WR-02: the
`UserPromptSubmit` element became `unattributed`), each time with `--write-reference ... --replace` from the same transcript
(read only: its sha256 was identical before and after); `window_sha256` `dc6d23b90cac...`, `window_rows` 34, `total_chars`
207245 and `tokens` came out identical, and `V-FLOOR-REAL-REFERENCE-PINNED` still PASSes.

## Owners consumed

- `wiki/tools/listing_floor_probe.py` (the owner of the first-call listing probe): `--probe` imports its `transcript`,
  `main` and `analyse`, rebinds its `CLAUDE` / `OUT` globals for one call and restores them in `try/finally`; the owner
  file has zero diff (`git diff --stat -- wiki/tools/listing_floor_probe.py wiki/tools/listing_floor_probe.results.jsonl`
  prints nothing, `git log -1 --format=%h -- wiki/tools/listing_floor_probe.py` prints `4d1cfb83`), and the tests leave its
  tracked results file untouched. Reused unchanged.
- `tools/baseline_ledger.py`: consulted, not extended. Its `AXES` are `k_qa`, `k_router`, `engineering_baseline`,
  `highest_dna`: there is no floor axis, and its ledger lives at `~/.claude/vault/global_baseline_ledger.json`, an HR-001
  write. The floor reference is therefore the program's own committed JSON, and `baseline_ledger` is not written. An Owner
  who wants a floor axis there decides it.
- `modules.secret_firewall.redact` (Universal Redaction Bus): every string and the reference JSON pass it at string-leaf
  level (04-01 `V-FLOOR-NO-SECRET`).

## Liveness

The scanner's own aperture, quoted from `python3 modules/liveness/reachability.py`:

```
APERTURE: packages under `modules/` only. `tools/` is NOT scanned, so nothing below is evidence about the verification runner, the benchmarks, the commit wrapper or the hunk guard. Silence here about a tool is absence from the denominator, never health.
```

The gate and its test live in `tools/`, outside the aperture, so the scanner can neither reach nor miss them. No registry
entry was written: registry keys under `modules` are module units (`pkg/mod`), and a `tools/` key would never be read.
Proof this phase changed none of the scanner's inputs: with BASE = `73d546152cc6edc7e9fe223ec49acf70de08c734` (the parent of
the oldest gate commit `7fdef637`), `git diff --name-only BASE..HEAD -- modules hooks commands agents SKILL.md CLAUDE.md vault/liveness`
prints nothing (0 lines), so the scanner's verdict is unchanged by this phase. Today's run, plane gex44:
`modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 64`, exit 1 -- 64 pre-existing offenders (the
live install on GEX44 differs from the laptop's), none introduced here.

How the gate is reached today: its test (`tools/test_floor_regression_gate.py`), the `[K]` owner-bundle item (parse-proven
by `V-FLOOR-BUNDLE-ARGV-PARSES`), and, once K closes, the ledger `gate` evidence argv
`["python","tools/test_floor_regression_gate.py"]` that `--final` executes. That last surface runs the fixture suite, not a
`--check` against `reference.json` (see the named debt below).

## Artifacts (LF sha256)

```
096d71cc164eac46c03061d0a3940be2562223fc900abaec14d986a9379f9359  tools/floor_regression_gate.py
3bec0f7b62fb273a4fb15565992abac563e2e11635332c846c0b89b33dc462bf  tools/test_floor_regression_gate.py
0d59e0dcf57837aa386e31e5259c8c6855d54f76c71e671bc9d604f82bce49c6  vault/programs/incremental-cognition/floor/reference-gex44.json
```

(`hashlib.sha256` over the file bytes with CRLF folded to LF, the CE verifier's `lf_sha256`.)

## Product Delta

A reviewer can now see the startup floor move, by layer and by scope, in one command. A 1,024-char addition to a
universal layer (2.05 % of a 50,000-char floor, under every percentage rule) goes red and is named as
`memory_global` / `universal`; the same bytes added to a project-local file are reported as `project +1024` and stay
green. A new system prompt part is a named `RISE system_prompt scope=unattributed delta=+4383`, not a silent total. An
unexplained rise exits 1 and is cleared only by an explanation that names layer, scope, unit, a delta bound and a reason;
a comparison that could not be made exits 2 and never reads green.

## Intelligence Delta

Measured facts learned while building it:

- The skill listing reads 30,000 chars in both GEX44 sessions (294 entries each) and in the laptop champion-startup probe
  row (30,000 chars, 216 entries). The same figure at different entry counts is consistent with a harness cap on the
  listing, so a new skill would displace descriptions rather than add cost; this is an inference from three rows, not a
  documented limit.
- Two same-day sessions of this repo (the interactive `607795c4` and the mission worker `34f03871`) differ by ONE appended
  4,383-char system prompt part (a mission worker's launcher prompt). That is why system prompt parts are identified by
  digest and left `unattributed` under the 1,000-char rule rather than classed as harness by type: the gate reads a mission
  worker against an interactive reference as a material rise, so a reference and its checks must be the same session kind.
- The owner probe's `startup_tokens` reads a synthetic first call (a login-expired session) as 0; the gate reports that
  as `no_model_call` and refuses to write a reference from it (`V-FLOOR-REAL-A7-NO-CALL`).
- Hook context and `UserPromptSubmit` attribution needs the producing `hook_success` row or the settings registrations,
  never the script path, because the laptop checkout lives under `~/.claude` and a path rule would call every project hook
  universal.

## Named debts

- LAPTOP REFERENCE PENDING: the frozen rule's committed reference must come from the laptop install; the `[K]` bundle item
  carries the exact commands (option A one headless session, spends quota, an Owner decision; option B no quota, the
  champion-startup probe session already on the laptop, a sanity parse only). Until it lands K is OPEN.
- LIVENESS / SURFACE DEBT: `tools/` is outside `modules/liveness/reachability.py`'s aperture and, after closure, no hook,
  CI job or `--final` run executes `--check` against `reference.json` -- the closing gate argv is the fixture suite -- so
  the `[K]` PRG's one real `--check` is the only proof until a surface is wired, and later silence is not health.
- LAPTOP-RUN DEBT: the closing gate `tools/test_floor_regression_gate.py` has never been run on the laptop. There its GEX44
  `-REAL` gates SKIP and the gates that need POSIX file modes or a script as the owner's argv[0] SKIP on Windows (expected,
  not measured), so the laptop's own evidence is `V-FLOOR-SEEDED-REAL` via `--real-session` plus the PRG `--check`.
- Tokens are comparable only on equal prompt digests (otherwise `not_comparable`). Since WR-03 that is exit 2
  `tokens_unmeasured`, and only an explicit `--chars-only` gives exit 0 (`WITHIN_BOUND_CHARS_ONLY`, tokens axis not
  compared); in practice an ordinary session checked against a probe-written reference is chars-only by construction.
- Since CR-01 / WR-01 the gate also refuses (exit 2) an unparseable startup-window line and a reference layer of >= 1,000
  chars that is wholly absent from the check; since WR-02 a hook element with no producing `hook_success` row is
  `unattributed`; since CR-02 no hook command text is stored.
- Scopes are computed on the measuring host at measure time; a check run on another host re-attributes from that host.
- `hook_success` raw stdout is excluded from the floor (counted only).
- A resumed session's startup window is its original start.
- The 64 pre-existing liveness offenders on GEX44 are not this phase's.
- The cherry-pick list in the bundle is the eight code commits by full sha, taken from `git log --reverse` on the three
  K artifacts before the bundle commit; it is proven to resolve (`git cat-file -t` prints `commit` for each) on GEX44 and
  to apply on the laptop only by the Owner's run. The seven review-fix commits are taken as the tree state of `ef336ec7`
  for the three tool / reference paths (one of them also edits the bundle and this file); likewise unproven on the laptop.

## Status: OPEN

Ledger `state.K` is not written (`{}`), IC-K is not ticked, `python3 tools/test_incremental_cognition_program.py --pillar K`
still reports `FAIL L3 K: no terminal disposition`. The pillar closes only through the `[K]` item: the laptop reference,
the committed `floor/reference.json`, and one real `--check` PRG saved as `evidence/K-prg.md`, after which K takes
IMPLEMENTED_AND_VERIFIED with gate `["python","tools/test_floor_regression_gate.py"]` + `K-prg.md`.
