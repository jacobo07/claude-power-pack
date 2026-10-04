---
phase: 05-offline-replay-and-owner-bundle
fixed_at: 2026-10-04T01:40:00Z
review_path: .planning/workstreams/incremental-cognition/phases/05-offline-replay-and-owner-bundle/05-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Source review:** 05-REVIEW.md (CR-01, WR-01..06, IN-01..03; all ten in the requested bound)
**Iteration:** 1
**Run plane:** edits, gates and commits in the existing isolated worktree `.claude/worktrees/ic-run` (branch
`mission/incremental-cognition-run`, started at HEAD 89109cb0); no nested worktree was created. Every gate below ran in
this same tree on GEX44 (`python3`, Linux), foreground. Each fix: a RED gate first through the real entry point (the
`check_owner_decisions` / `check_measurement_scope` functions the done-gate calls, or the `kme_replay.py rank` CLI path
through `run_main` / `run_json`), then the fix, then green; one pathspec commit per finding
(`git commit -F <msgfile> -- <paths>`, Sonnet 5.5 trailer); a `--drill` mutant (kme_replay) or a selftest mutation pole
(the program wrapper) per CR/WR. Nothing was written under `~/.claude/**` and no `claude` session was started; the
accepted-shape Owner decision fixture lives in a `tempfile` scratch directory, never in the repo.

Findings CR-01, WR-01..04, WR-06 and IN-01 change a condition or an identity rule (logic), so they are marked
`fixed: requires human verification`: the syntax and the gates pass, but whether the decisions (identity rules, the
growth pin, the dense ranking) are what the Owner wants is a judgement the gates cannot make. The decisions themselves
were taken by the orchestrator and applied as given.

## Fixed Issues

### CR-01: R4 bypassed by any spelling of the bundle that `_bundle_ref` does not resolve like `ce.Resolver` -- FIXED (requires human verification)

**Commit:** 6cf619dd
**Files:** `tools/test_incremental_cognition_program.py`
**Fix:** `owner_decision_problem(ref)` replaces the string compare. `names_the_bundle` resolves the ref through
`ce.Resolver._path` (the reader L4 uses: `~` expanded, absolute accepted, raw and backslash-normalised) and compares with
`os.path.samefile` against the bundle, then by the ref's spelled tail under `vault/programs/incremental-cognition/`
(`owner-bundle.md`), which is what catches a second checkout's path (a different file, so `samefile` cannot).
**Gate:** `V-ICP-R4-IDENTITY` (selftest, `~` expanded against a patched HOME): `~/<checkout>/vault/.../owner-bundle.md`,
absolute path of this checkout, main-checkout absolute path, second checkout in scratch with different bytes, symlink to the
bundle -> refused; the accepted shapes (a scratch `evidence/L-owner-decision.md`, and the repo-relative spelling of it) ->
silent. The five original spellings of `V-ICP-R4-BUNDLE-REFUSED` still pass.
**RED (identity not judged):** `FAIL V-ICP-R4-IDENTITY ... off: ['second-checkout-abs', 'main-checkout-abs', 'tilde', 'symlink']`
**GREEN:** `ICP_SELFTEST=PASS`
**Mutant:** `V-ICP-MUT-r4-string-compare` (the pre-fix string compare) KILLED by `V-ICP-R4-IDENTITY`
(leaves open `second-checkout-abs`, `main-checkout-abs`, `tilde`).

### WR-01: R4 string-based on a POSIX-only shape; red on the Windows laptop -- FIXED (requires human verification)

**Commit:** e843107c
**Files:** `tools/test_incremental_cognition_program.py`
**Fix:** the spelled form drops a drive letter (`^[A-Za-z]:`), folds backslashes and `casefold()`s before the tail
comparison, so `C:\Users\User\repo\vault\programs\incremental-cognition\owner-bundle.md`, `c:/repo/...` and
`Vault/Programs/Incremental-Cognition/OWNER-BUNDLE.md` all name the bundle. `samefile` stays the first test on a host where
the path exists.
**Gate:** poles `windows-drive-backslash`, `windows-drive-case-variant`, `relative-case-variant`,
`windows-forward-slash-drive` refused; `unrelated-windows-path` (`C:\Users\User\Desktop\my-decision.md`) silent.
**RED:** `FAIL V-ICP-R4-IDENTITY ... off: ['windows-drive-case-variant', 'relative-case-variant']`
**GREEN:** `ICP_SELFTEST=PASS`
**Mutant:** `V-ICP-MUT-r4-case-sensitive-spelling` KILLED (leaves open the case variants).
**Limit:** the Windows forms are proven here as strings on Linux (no NTFS); on the laptop `samefile` and the case fold are
the paths that matter and were not run there.

### WR-02: R4 identified the bundle by name only; a byte copy or any mission-written file counted as the Owner's decision -- FIXED (requires human verification)

**Commit:** f638a167
**Files:** `tools/test_incremental_cognition_program.py`
**Fix:** an `owner_decision` is also refused when a file its ref reads as has the bundle's content (raw or CRLF-folded
sha256), and when it is program-written: anything under the program's `evidence/` except a basename matching
`L-owner-decision*.md`, and anything under `measurements/` -- judged by the spelled tail (second checkout, Windows form,
case) and by `realpath` relative to the program directory (so a decision-named symlink into `evidence/` is refused).
**Gate:** poles `byte-copy-of-bundle`, `byte-copy-of-bundle-crlf`, `mission-evidence-file` (`evidence/L.md`, relative,
absolute, case variant), `mission-measurement-file` (a committed measurements file), `mission-evidence-in-second-checkout`,
`decision-named-symlink-to-evidence` -> refused; the scratch `L-owner-decision.md` -> silent. `V-ICP-R4-IDENTITY` counts 19 poles.
**RED:** the two mutants below leave `['byte-copy-of-bundle', 'byte-copy-of-bundle-crlf']` and
`['mission-evidence-file', 'mission-evidence-file-absolute', 'mission-evidence-file-case']` accepted (the pre-fix behaviour).
**GREEN:** `ICP_SELFTEST=PASS`
**Mutants:** `V-ICP-MUT-r4-no-byte-compare`, `V-ICP-MUT-r4-mission-files-accepted` KILLED.
**Judgement kept narrow:** the exemption is the literal `L-owner-decision*.md` as decided; another pillar's decision file
under `evidence/` would be refused until the exemption is widened (no other pillar's decision file is documented today).
A mission-written file that is *named* `L-owner-decision*.md` is still accepted by name; that is the residual the review's
"first commit not authored by the mission identity" idea would close, and it was not part of the decision.

### WR-03: a hand-written file closes pillar L: R3-L trusts self-asserted front matter -- FIXED (requires human verification)

**Commit:** d27e0cc6
**Files:** `tools/test_incremental_cognition_program.py`, `tools/test_kme_replay.py`
**Fix:** `kmer_ranking_problems(fm, text)` (called from `terminal_claim_problems` for pillar L; `check_measurement_scope`
now hands it the file text): `ranked_ids` / `unranked_ids` must be lists, disjoint, duplicate-free and together exactly the
three candidate ids; `weighted_denominator` a positive number; exactly one parseable `<!-- kmer-json -->` block; the block
agrees with the front matter on instrument, pillar, denominator, role, terminal flag, population match, denominator,
growth, both id lists and the full `frozen_source` record (sha included); the block's `ranked` entries are the front
matter's `ranked_ids` in order. `V-KMER-R3-TABLE-PINNED` now also pins `KMER_BODY_END` and the candidate ids across the
wrapper and the instrument.
**Gate:** `V-ICP-R3-L-RANKING-CHECKED`: 15 forged / inconsistent files refused (the reviewer's front-matter-only hand-typed
file, two-of-three ranked, a foreign id, a duplicate, a non-list, block absent / malformed / twice, five block-vs-front-matter
disagreements, ranked entries disagreeing), plus `V-ICP-R3-L-RANKING-CONSISTENT-ACCEPTED` (the consistent control is silent).
The real `V-KMER-R3-PAIR` (an instrument-written KME-L primary through the wrapper's R3) stays green.
**RED:** `FAIL V-ICP-R3-L-RANKING-CHECKED (15 ... off: [all 14 of the first set])` before the code existed.
**GREEN:** `ICP_SELFTEST=PASS`, `KMER_PASS=41/41` at that commit.
**Mutant:** `V-ICP-MUT-r3l-ranking-unchecked` (the check returns nothing) KILLED: it leaves 15 of 15 forged files accepted.

### WR-04: nothing pinned `rollover_growth`; a "terminal" ranking at any G -- FIXED (requires human verification)

**Commit:** 4d0edcce
**Files:** `wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`, `tools/test_incremental_cognition_program.py`
**Fix:** `terminal_ok(..., growth=ROLLOVER_GROWTH)` also requires `type(growth) is int and growth == 100000`, and the
terminal reason names a non-default G as sensitivity only; R3-L (`rollover_growth_problems`) requires the same value
recorded in the file. A non-default `--rollover-growth` is still accepted (smoke / sensitivity), it just is never terminal.
`KMER_ROLLOVER_GROWTH` is pinned equal across wrapper and instrument.
**Gate:** `V-KMER-ROLLOVER-GROWTH-PINNED` (truth table, CLI at the default -> terminal, at 1e9 and 2000 -> primary role but
`terminal_evidence` false with the reason naming `rollover_growth`); `V-ICP-R3-L-GROWTH-PINNED` (1e9, 50000, `"100000"`,
`100000.0`, `true`, absent -> refused).
**RED:** `FAIL V-KMER-ROLLOVER-GROWTH-PINNED TypeError: terminal_ok() got an unexpected keyword argument 'growth'`
**GREEN:** `KMER_PASS=42/42`, drill 14/14, `ICP_SELFTEST=PASS`.
**Mutants:** M14 (terminal ignores growth) KILLED by `V-KMER-ROLLOVER-GROWTH-PINNED`; `V-ICP-MUT-r3l-growth-unpinned` KILLED
(leaves 6 of 6 accepted). M13 was re-expressed for the new signature and still dies on `V-KMER-TERMINAL-EVIDENCE`.

### WR-05: ranked numerators emitted `weighted_lo` / `weighted_interval` that bound nothing, with float noise -- FIXED

**Commit:** 0fc2ed00
**Files:** `wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`,
`vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md` (regenerated)
**Fix:** `entry_figures()` replaces the observer's numerator inside each ranked entry: `upper_bound_weighted` and
`upper_bound_share` rounded to 6 decimals, numerator reduced to `name` / `kind` / `chars`; no `weighted_lo`, `weighted_hi`
or `weighted_interval`. Two retry gates that read the strict lower bound now check the strict count; share tolerances in
three gates follow the rounding.
**Gate:** `V-KMER-UPPER-ONLY` reads the result, the file's json block and the rendered text, with positive controls that the
key and float walkers do see an `upper_bound_weighted` key and floats.
**RED:** `FAIL V-KMER-UPPER-ONLY ... forbidden/noisy per source ... ['weighted_hi', 'weighted_interval', 'weighted_lo'] ... 0.5671564836298015 ...`
**GREEN:** `KMER_PASS=43/43`, drill 15/15.
**Mutant:** M15 (the pre-fix entry shape) KILLED by `V-KMER-UPPER-ONLY`.
**Smoke regenerated** with the exact command recorded in the file (`python3 wiki/tools/kme_replay.py rank --denominator KME-G
--until auto --expand --root .../a5-env/... --root .../a7-env/... --root .../b001-env/... --root ~/.claude/projects`), the old
file removed first (no-overwrite). The a5 / a7 / b001 trees are identical before and after (sha256 of every file and a
`find -printf` size + mtime listing, `cmp` clean); `~/.claude/projects` was read only. The figures did not change (late
rollover 8,773,728.0, share 0.159814; retries 2,520.633333; rereads 0.0), so `evidence/L.md`'s figures stand; its test counts
and artifact shas were refreshed (below).

### WR-06: inline-sidechain files UNMEASURED for rollover but silently MEASURED for retries and rereads -- FIXED (requires human verification)

**Commit:** e125e07b
**Files:** `wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`,
`vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md` (regenerated, caveat text only)
**Fix:** `RetryObserver` keys its state per (file, thread), a thread being `main` or one inline sidechain (`isSidechain`,
`agentId`; `thread_of`), routes a `tool_result` to the thread that issued its `tool_use`, and treats two identical tool uses
in one assistant message as not a retry (`same_message`; Agent / Task re-dispatches likewise). `identical_rereads` is a thin
`RereadObserver` over `kme_pillars.EObserver` with the same per-thread split (pillar E's instrument is NOT edited; without
inline sidechain lines it is `EObserver` exactly, `V-KMER-REREADS-EQUALS-E` green). Docstring and a caveat updated.
**Gate:** `V-KMER-THREAD-KEYED`: retries and rereads for main + sidechain (0), one sidechain pair (1), two agents (0),
main pair (1), parallel identical uses in one message (0), serial (1).
**RED:** `got={'retry main+side': 1, ..., 'retry parallel': 1, ..., 'reread main+side': 1, ...}` (every case 1)
**GREEN:** `KMER_PASS=44/44`, drill 17/17.
**Mutants:** M16 (one thread) and M17 (`same_message` never matches) KILLED by `V-KMER-THREAD-KEYED`.
**Judgement flagged:** an inline-sidechain event's residency (`resident_calls`) still counts the calls of the whole file, so
it is an upper figure; stated in the caveat. The committed corpus has 0 such sessions, so the smoke figures are unchanged.

### IN-01: equal figures got distinct ranks; stdout `share=` unlabelled -- FIXED (requires human verification)

**Commit:** 2e9efaa0
**Files:** `wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`
**Fix:** `dense_ranks()` gives equal (rounded) upper bounds the same rank (4,4,4 -> 1,1,1; 9,4,4 -> 1,2,2); the order inside
a tie stays the fixed candidate order (the existing pinned determinism, read as "stable by candidate id"); stdout prints
`upper_bound_share=`.
**Gate:** `V-KMER-RANK-TIE-DETERMINISTIC` extended (unit dense ranks on four figure sets, CLI ranks `[1, 1, 1]`, label).
**RED:** the label reverted -> `FAIL V-KMER-RANK-TIE-DETERMINISTIC`; mutant M18 (distinct ranks) KILLED by it.
**GREEN:** `KMER_PASS=44/44`, drill 18/18.
**Smoke:** unchanged (three distinct figures), not regenerated.

### IN-02: raw read paths from transcripts written to a committed file -- FIXED

**Commit:** 963525e1
**Files:** `wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`
**Fix:** `scrub_details()` turns `identical_rereads` `details.top_paths` into `{path_sha256_12, ext, count, chars}` (order
kept) before it reaches the result, the stdout json and the file.
**Gate:** `V-KMER-NO-RAW-PATHS`: reads of `/home/u/customer-acme/.env.production` and `/home/u/work/notes.md`; digests computed
in the test; `customer-acme`, `.env.production`, `/home/u`, `notes.md` appear nowhere in the file or stdout.
**RED:** `FAIL V-KMER-NO-RAW-PATHS ... top_paths=[{'path': '/home/u/customer-acme/.env.production', ...`
**GREEN:** `KMER_PASS=45/45`, drill 19/19.
**Mutant:** M19 (`scrub_details` returns the details unchanged) KILLED.
**Residual:** `unchanged_precondition_retries` `top_signatures` come from `kme_pillars.cmd_signature` (Phase 3's reviewed
sanitiser), which can keep a plain path token as the second word of a command; not changed here (outside the finding).

### IN-03: docstring said only AUTHORIZATION_BOUND needs no ranking file -- FIXED

**Commit:** a0dc6276
**Files:** `tools/test_incremental_cognition_program.py`, `wiki/tools/kme_replay.py`
**Fix:** both docstrings state exactly which L terminals need a ranking file (RESEARCH_INSUFFICIENT_EVIDENCE,
FALSIFIED_OR_REJECTED_BY_EVIDENCE) and which need none and leave R3 silent (AUTHORIZATION_BOUND, IMPLEMENTED_AND_VERIFIED,
MERGED_INTO_EXISTING_OWNER, DEFERRED_STRONGER_OWNER, EXTERNAL_BLOCKED; L4 still demands each one's own evidence kinds). The
wrapper's R4 paragraph is rewritten to the identity rule.
**Gate:** `V-ICP-R3-L-NEEDS-RANKING-TABLE` executes the claim against `ce.TERMINALS`: the five are silent with no file, the two
are loud, and every one of the seven is named in the wrapper docstring.

## Verification (after the last fix)

All foreground, in this worktree on GEX44:

```
python3 tools/test_kme_replay.py                                   KMER_PASS=45/45  threshold=45/45  skipped=0  inconclusive=0
python3 tools/test_kme_replay.py --drill                           DRILL killed=19/19 (control and clean-after 42/42)
python3 tools/test_kme_pillars.py                                  KMEP_PASS=89/89
python3 tools/test_floor_regression_gate.py                        FLOOR_PASS=67/67
python3 tools/test_incremental_cognition_program.py --selftest     ICP_SELFTEST=PASS
python3 tools/test_incremental_cognition_program.py --pillar L     exit 1 (FAIL L3 L: no terminal disposition; no terminal exists)
```

Not touched: `vault/progress.md`, the workstream `config.json` / `milestone.lock`, `docs/*kme_pillars*`, the owner bundle
(no edit needed), the ledger (`state.L` stays OPEN, IC-L unticked), `wiki/tools/kme_pillars.py`,
`tools/test_cognitive_economy_program.py`. `vault/programs/incremental-cognition/evidence/L.md` was updated (counts, artifact
shas, a short review-fix paragraph).

## Named debt (not fixed here, carried to STATE)

- **D..I terminal gate trusts self-asserted front matter** (the WR-03 weakness, outside the requested scope): for pillars
  D, E, F, G, H, I, `terminal_claim_problems` believes a `kme_pillars` file whose front matter says `terminal_evidence: true`
  and whose fields agree *with themselves* (instrument, role, population, verdict, rule table, `frozen_source` sha). It never
  parses the file's `<!-- kmep-json -->` block against the front matter, so a hand-written file with consistent front matter
  and no real measurement can close one of those pillars. The L gate now cross-checks front matter against the json block,
  the candidate id set and the growth pin; the same consistency check (and, for D..I, the measured numerator and verdict in
  the block) is not applied to D..I.
- R4's `L-owner-decision*.md` exemption is by name: a mission-written file given that name is accepted, and only `L` has a
  documented decision-file name.

---

_Fixed: 2026-10-04_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
