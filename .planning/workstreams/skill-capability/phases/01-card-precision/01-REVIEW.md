---
phase: 01-card-precision
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - hooks/doctrine_cards.js
  - hooks/capsule_mutation_guard.js
  - hooks/tests/test-doctrine-cards.js
  - hooks/tests/test-capsule-mutation-guard.js
  - tools/test_card_precision.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard (diff vs f1e80a0e)
**Files Reviewed:** 5
**Status:** issues_found

## Summary

The window rule is implemented as described and holds the properties the header claims. Fail-open holds: `main().catch` emits `continue:true`, `statSync` is wrapped, and `spawnSync` does not throw. No I/O happens before `COMMIT_RE` matches (line 414). Missing or odd timestamps give `NaN`, which `Number.isFinite` rejects in both `ownership` (line 346) and `ownShellWindowHit` (line 358), so the file stays foreign. I checked `Date.parse` on this node 18: undefined gives NaN, a numeric epoch gives NaN, an offset timestamp parses correctly, and a zone-less timestamp parses as local time. Real harness rows carry `Z` timestamps, so that last case is not reachable. The `unborn_head` fallback resolves the empty tree correctly (`git diff <oid> -- f` works on gex44). The `path.win32.basename` change in `capsule_mutation_guard.js` is identical on Windows and fixes the POSIX miss. It adds no new allow beyond the existing "any exe named git" basename policy.

Cost, measured: `ownership()` over a real 5 MB, 4.3 h transcript took 253 ms (1218 closed shell windows). That is acceptable for a call made only on commit commands.

No CRITICAL findings. Two WARNINGs and three INFOs follow.

## Warnings

### WR-01: Window rule is not tied to the file, so a peer write during any shell call reads "unknown" (false allow of exactly the case the card exists for)

**File:** `hooks/doctrine_cards.js:357-361` (rule), `hooks/doctrine_cards.js:377` (use)

**Issue:** `ownShellWindowHit` asks only whether the file's mtime falls inside any of this session's shell windows (plus 1 s slack on each side) and is later than this session's last Edit of that basename. Nothing links the window to the file. The classic concurrent-writers case is a peer that writes the shared file after this session's last Edit and before the commit. That peer write is a genuinely foreign hunk, and its mtime satisfies the second condition by construction.

The first condition then depends only on how much of the session was spent inside shell calls. I measured it on a real transcript (`/home/kobii/.claude/projects/-home-kobii-missions-cognitive-resource-os--claude-worktrees-cro-gex44/a293bedf-...jsonl`). The shell windows sum to 1.11 h of a 4.33 h span, which is 25 % direct. With the 1 s slack on both sides of 1218 windows, about 2.4 s more per window, coverage is roughly 40 %. A peer write after the last own edit has about a 25-40 % chance of landing in a window, and the hook then records `unknown` and allows the commit.

Windows can also be longer than the work. The start is the `tool_use` row timestamp and the end is the `tool_result` row timestamp, so a permission-prompt wait or a long foreground test run counts as one window. That is the period in which another session is most likely to be writing.

The header documents the peer-write aperture, so this is a stated trade-off and not a hidden defect. It is still unpinned. No test drives "peer write inside a window reads unknown", so a later tightening cannot show it changed behavior. The measured population (5 false denies, 0 true positives) gives no estimate of the false-allow rate.

**Fix:** Narrow the rule so a window counts only if the command could have written the file, then pin the aperture with a test.
```js
// ownership(): keep the command text per shell call
calls.set(b.id, { kind: 'shell', start: rowTs, end: NaN, cmd: String(i.command || '') });
// windows.push({ start, end, cmd })
// ownShellWindowHit(): require that the window's command names the file's basename or its directory, or runs
// a script/formatter. A pure read or test command (git log, pytest, sleep) never earns the exemption.
```
At minimum:
- Cap a window's length (for example 120 s), so a prompt wait or long test run does not widen the exemption.
- Record `{mtime, window_index}` in the ledger row, so false allows are measurable after the fact.
- Add a test that pins the peer-write-in-window behavior either way.

### WR-02: `git()` appends `-U0 --no-color --no-ext-diff` after `--`, so for the pathspec basis they are pathspecs, not options (pre-existing, kept by this refactor)

**File:** `hooks/doctrine_cards.js:241-243` (`git`); the argv comes from `plan()` at line 227, `['diff','HEAD','--',...rp]`.

**Issue:** For `basis: only-paths` (every `git commit -- file`, the commonest agent form) the argv is `diff HEAD -- <paths> -U0 --no-color --no-ext-diff`. After `--`, git reads those three as pathspecs. I confirmed on gex44: `git -c color.diff=always diff HEAD -- f.txt -U0 --no-color --no-ext-diff` prints ANSI-colored output with 3 lines of context, where `-U0` should give zero context.

The failure mode is a user or global config of `color.diff=always`, or an external diff driver. `parseDiff` matches `line.startsWith('diff --git ')`, and the colored line begins with `ESC[1m`. No file is ever parsed, so `foreign` is empty and the row says `no_opportunity`. The card is silently disarmed and the ledger records a clean verdict. The same applies to the unborn-head re-run (line 427, which reuses `p.args.slice(2)`).

The new test probe `V-DC-GIT-CLASSES` replicates the same wrong order (`tail` after `--`), so the tests share the defect and cannot see it. A further effect is the default 3-line context. Hunk headers and the dedupe key at line 456 depend on context size, so two nearby edits merge into one hunk.

**Fix:** Put the options before the revision and before `--`.
```js
function git(repo, args) {
  const [sub, ...rest] = args;   // args[0] is always 'diff'
  return spawnGit(['--no-optional-locks', '-C', repo, sub, '-U0', '--no-color', '--no-ext-diff', ...rest]);
}
```
The empty-tree re-run and the test's `tail` need the same ordering. Add a test that runs the card under `-c color.diff=always` (via `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` in the child env) and expects the same verdict as without it.

## Info

### IN-01: First-commit empty-tree fallback judges only already-indexed files, and the comment overclaims

**File:** `hooks/doctrine_cards.js:420-422`, `hooks/doctrine_cards.js:451-453`

**Issue:** The comment says "every line it adds is a hunk". I verified that `git diff <empty-tree>` shows only paths present in the index. An untracked file does not appear. For `git add -A && git commit` as one command in an unborn repo (basis `add-then-commit`), nothing is staged yet, so the diff is empty. The row then reads `decision: no_opportunity, base: empty-tree`, where it previously read `unknown` (git exit 128). The `aperture: 'untracked not checked'` field is carried, but the decision is a clean "no opportunity" for a check that inspected nothing. This is the same blindness `add-then-commit` has in every repo, but in an unborn repo it covers 100 % of files.

**Fix:** Only set `base: empty-tree` and allow the clean verdict for `only-paths` and `index` bases. For `add-then-commit` in an unborn repo, record `unknown` with reason `unborn-head-untracked-unseen`. Correct the comment.

### IN-02: stderr classification depends on English git messages

**File:** `hooks/doctrine_cards.js:272-280` (`classifyGitError`), called at 425 and 433

**Issue:** Every class except the `usage: git diff --no-index` banner is matched on English text. This hook ships to a Windows laptop whose owner works in Spanish. If a localized git prints translated `fatal:` lines, `unborn_head` never matches, so the empty-tree fallback silently never engages, and the rows say `other`. It degrades safely to the old `unknown`, but it does so without any signal.

**Fix:** Pin the locale on the git spawns whose stderr is classified: `env: { ...process.env, LC_ALL: 'C', LANGUAGE: 'C' }` in `spawnGit`.

### IN-03: Worst-case spawn chain can exceed the dispatcher's hook timeout

**File:** `hooks/doctrine_cards.js:60` (`GIT_TIMEOUT_MS`), 419-428, 444; `hooks/hook-dispatcher.js:433` (`timeoutMs: 5000`)

**Issue:** Up to four bounded 2.5 s spawns can now run in one invocation: diff, `hash-object`, the re-run, and `rev-parse --show-toplevel`. The dispatcher kills the hook at 5 s. This only matters when git is slow, such as a hung network filesystem. The kill fails open, but it leaves no ledger row for that commit. The doctrine header lists "one bounded git spawn (2.5 s)" plus one extra, and the second extra is not listed.

**Fix:** Share one deadline across the spawns, for example `Math.max(300, 4500 - (Date.now() - t0))` per call, and record `timeout` when it is exhausted.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
